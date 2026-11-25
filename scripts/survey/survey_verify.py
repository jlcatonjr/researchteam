"""Signature verification through ``agentteams`` (contract 6.2), reached only as a child process.

Rule 1.7: the tools import nothing outside the standard library, and verifying a signature needs ``agentteams``, which
is optional. This module imports no ``agentteams`` code. It starts ``sys.executable -B -I -c CHILD`` (one fixed snippet,
below) in the interpreter the tools run under, so the ``agentteams`` found is the one installed for that interpreter
and never another one on ``PATH``. The child calls agentteams' public file-clearance check
(``agentteams.cli.clearance_binding.check_file_clearance``, documented in agentteams 1.3.0's API reference, section
"Gates-only team dirs for sign-off rows") and prints one JSON line.

**The child's environment is an allowlist** (``child_env``): a minimal ``PATH``, ``LC_ALL``, and ``HOME`` and
``TMPDIR`` set to a fresh, empty temporary folder that is removed afterwards. No ``AGENTTEAMS_*``, ``XDG_*`` or
``GIT_*`` variable reaches it. Why each matters, read from agentteams 1.3.0:

- ``AGENTTEAMS_DECISION_SIGNING_KEY`` makes every decisions log the process touches signing-active, and supplies a
  shared secret that would let a shared-secret row or retraction verify (6.2, lines 864-865 and 884-886).
- agentteams reads a shared-secret (HMAC) key file from ``~/.config/agentteams/keys/decision-hmac.key``
  (``signed_ledger.HMAC_KEY_DIR``, expanded with ``HOME``) when the variable is unset. The empty ``HOME`` defeats
  that, so **a HALT retraction signed with a shared secret never counts in this check** (a stricter default the session adopted, Q11). Its
  Ed25519 verify keys are read only from the team directory's ``references/authorized-verify-keys/``, never from
  ``HOME``.

**What clears** (``interpret``): exit status 0; exactly one JSON object on stdout; ``cleared`` true; the action the
child checked equal to the one the tools computed; ``agentteams`` 1.3.0 or later; its module file exactly
``<purelib>/agentteams/__init__.py`` of the child; the child's ``sys.prefix`` equal to the parent's. Anything else is not ``CLEARED``. No message text is
ever parsed to decide.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path

#: The oldest agentteams whose clearance check reads HALTs in the repository's team logs (6.2, lines 915-917).
MIN_VERSION = (1, 3, 0)
#: How long the child may run, and how many bytes of stdout are read.
TIMEOUT_SECONDS = 120
MAX_STDOUT = 64 * 1024
#: The ``PATH`` the child gets: enough for agentteams to run ``git`` if it needs to, nothing from the caller.
CHILD_PATH = "/usr/bin:/bin"
#: The child's interpreter flags: ``-B`` writes no ``__pycache__`` (``-I`` does not imply it), so a check never writes
#: into an environment kept inside the work tree; ``-I`` ignores ``PYTHON*`` variables, the user site and the current
#: directory.
CHILD_FLAGS = ("-B", "-I")

#: The one snippet the child runs: ``python -B -I -c CHILD <team dir> <scope> <manifest file>``. It computes the action
#: from the file's bytes first, then asks agentteams whether that action is cleared, and prints one JSON line.
CHILD = r"""
import json, sys, sysconfig
from pathlib import Path
import agentteams
from agentteams.cli.clearance_binding import check_file_clearance, clearance_action
team, scope, path = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
action = clearance_action(scope, path)
cleared, _reason = check_file_clearance(team, scope, path)
print(json.dumps({"version": str(agentteams.__version__), "file": str(agentteams.__file__),
                  "purelib": str(sysconfig.get_paths()["purelib"]), "prefix": str(sys.prefix),
                  "cleared": cleared is True, "action": str(action)}, sort_keys=True))
"""
CHILD_KEYS = {"version", "file", "purelib", "prefix", "cleared", "action"}

#: Outcomes of one check.
CLEARED, NOT_CLEARED, UNAVAILABLE = "cleared", "not-cleared", "unavailable"


def parse_version(text: str):
    """``(major, minor, patch)`` from a version that is exactly ``X.Y.Z``; None for anything else (a pre-release, a
    local or development version), so an unusual version fails closed."""
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(text))
    return tuple(int(g) for g in match.groups()) if match else None


@dataclass
class ChildResult:
    """What one check found. ``outcome`` is CLEARED, NOT_CLEARED or UNAVAILABLE; ``why`` says why it is not
    CLEARED, in the tools' own words; ``info`` is the child's JSON object when it was well-formed."""

    outcome: str
    why: str = ""
    info: dict = field(default_factory=dict)


def installed_version():
    """The installed agentteams version string, read with the standard library (no agentteams import), or None."""
    try:
        from importlib import metadata
        return metadata.version("agentteams")
    except Exception:  # noqa: BLE001 (any failure means: not usable here)
        return None


def probe() -> str:
    """Why verification cannot run in this interpreter, or ``""`` when it can be tried. Standard library only."""
    if importlib.util.find_spec("agentteams") is None:
        return (f"agentteams is not installed for this interpreter (Python {sys.version_info[0]}."
                f"{sys.version_info[1]}; agentteams needs 3.11 or later), so no signature can be verified here")
    version = installed_version()
    parsed = parse_version(version) if version else None
    if parsed is None:
        return f"the installed agentteams version {version!r} cannot be read as X.Y.Z"
    if parsed < MIN_VERSION:
        return (f"agentteams {version} is older than 1.3.0, which is the first to read HALTs in the repository's "
                "team logs (6.2)")
    if importlib.util.find_spec("cryptography") is None:
        return "the cryptography package (agentteams' signing extra) is not installed, so Ed25519 cannot be verified"
    return ""


def child_env(home: str) -> dict:
    """The child's whole environment (an allowlist; see the module docstring)."""
    return {"PATH": CHILD_PATH, "LC_ALL": "C", "HOME": home, "TMPDIR": home}


def _read_bounded(stream, cap: int, out: list) -> None:
    """Read *stream* until end of file or until more than *cap* bytes have been read, whichever comes first."""
    total = 0
    while total <= cap:
        chunk = stream.read(min(65536, cap + 1 - total))
        if not chunk:
            break
        out.append(chunk)
        total += len(chunk)


def run_child(repo_root: Path, team_dir: Path, scope: str, manifest: Path):
    """Run the fixed snippet. Returns ``(returncode, stdout bytes)``, or ``(None, why)`` when it could not run.
    Stdout is read through a bounded read that stops at ``MAX_STDOUT + 1`` bytes (@security S5); a child that prints
    more is stopped, and the extra byte makes ``interpret`` refuse it."""
    home = tempfile.mkdtemp(prefix="survey-verify-")
    try:
        try:
            proc = subprocess.Popen(
                [sys.executable, *CHILD_FLAGS, "-c", CHILD, str(team_dir), scope, str(manifest)],
                cwd=str(repo_root), env=child_env(home), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL)
        except OSError as exc:
            return None, f"the agentteams check could not be started: {exc.strerror or type(exc).__name__}"
        chunks: list = []
        reader = threading.Thread(target=_read_bounded, args=(proc.stdout, MAX_STDOUT, chunks), daemon=True)
        reader.start()
        reader.join(TIMEOUT_SECONDS)
        timed_out = reader.is_alive()
        if timed_out or sum(map(len, chunks)) > MAX_STDOUT:
            proc.kill()
        try:
            returncode = proc.wait(timeout=TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            proc.kill()
            returncode = proc.wait()
        reader.join(1)
        proc.stdout.close()
        if timed_out:
            return None, f"the agentteams check did not finish within {TIMEOUT_SECONDS} s"
        return returncode, b"".join(chunks)
    finally:
        shutil.rmtree(home, ignore_errors=True)


def _inside(path: str, root: str) -> bool:
    try:
        path, root = os.path.realpath(path), os.path.realpath(root)
        return os.path.commonpath([path, root]) == root
    except ValueError:
        return False


def interpret(returncode, stdout, expected_action: str) -> ChildResult:
    """Decide from the child's exit status and stdout alone (never from message text)."""
    if returncode is None:
        return ChildResult(UNAVAILABLE, str(stdout))
    if returncode != 0:
        return ChildResult(UNAVAILABLE, f"the agentteams check exited with status {returncode}")
    if len(stdout) > MAX_STDOUT:
        return ChildResult(UNAVAILABLE, "the agentteams check printed more than expected")
    try:
        lines = stdout.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return ChildResult(UNAVAILABLE, "the agentteams check printed text that is not UTF-8")
    if len(lines) != 1:
        return ChildResult(UNAVAILABLE, "the agentteams check did not print exactly one line")
    try:
        info = json.loads(lines[0])
    except ValueError:
        return ChildResult(UNAVAILABLE, "the agentteams check did not print a JSON object")
    if not isinstance(info, dict) or set(info) != CHILD_KEYS or not isinstance(info["cleared"], bool) or \
            not all(isinstance(info[k], str) for k in CHILD_KEYS - {"cleared"}):
        return ChildResult(UNAVAILABLE, "the agentteams check printed an object of the wrong shape")
    version = parse_version(info["version"])
    if version is None or version < MIN_VERSION:
        return ChildResult(UNAVAILABLE, "the agentteams the check ran is not 1.3.0 or later", info)
    expected_file = os.path.join(info["purelib"], "agentteams", "__init__.py")
    if os.path.realpath(info["file"]) != os.path.realpath(expected_file):
        return ChildResult(UNAVAILABLE, "the agentteams the check ran is not the package installed in its "
                           "interpreter's site-packages", info)
    if os.path.realpath(info["prefix"]) != os.path.realpath(sys.prefix):
        return ChildResult(UNAVAILABLE, "the agentteams check ran in another environment", info)
    if info["action"] != expected_action:
        return ChildResult(UNAVAILABLE, "the agentteams check hashed different manifest bytes than the tools", info)
    if not info["cleared"]:
        return ChildResult(NOT_CLEARED, "agentteams found no clearance it accepts", info)
    return ChildResult(CLEARED, "", info)


class Verifier:
    """The verifier the gates use. Tests replace ``probe`` and ``run`` to exercise the paths without agentteams."""

    def probe(self) -> str:
        return probe()

    def run(self, repo_root: Path, team_dir: Path, scope: str, manifest: Path):
        return run_child(repo_root, team_dir, scope, manifest)

    def check(self, repo_root: Path, team_dir: Path, scope: str, manifest: Path, action: str) -> ChildResult:
        returncode, out = self.run(repo_root, team_dir, scope, manifest)
        return interpret(returncode, out, action)


class NotRun(Verifier):
    """For ``survey-validate``, which reports no gate state: verification is not attempted."""

    def probe(self) -> str:
        return "survey-validate does not verify signatures; survey-status reports gate state"


def location(info: dict, repo_root: Path) -> str:
    """Where the verifying agentteams and its interpreter are, without a home-directory path (N1, @security S6): the
    package relative to the repository root when inside its work tree, else from ``site-packages`` on; and whether
    the interpreter's prefix (``sys.prefix``) is inside the work tree, where a ``.pth`` file or ``sitecustomize``
    could change what the child reports."""
    file = info.get("file", "")
    if not file:
        return "unknown"
    real, root = os.path.realpath(file), os.path.realpath(repo_root)
    if _inside(real, root):
        where = "inside the work tree: " + os.path.relpath(real, root).replace(os.sep, "/")
    else:
        parts = Path(real).parts
        tail = parts[parts.index("site-packages"):] if "site-packages" in parts else parts[-2:]
        where = "outside the work tree: " + "/".join(tail)
    prefix = info.get("prefix", "")
    inside = bool(prefix) and _inside(prefix, root)
    return where + ("; its interpreter is inside the work tree" if inside else
                    "; its interpreter is outside the work tree")
