"""Check which agentteams code a layer-1 render is about to run, and refuse unreviewed code.

Adapted from mathAgents ``scripts/lib/agentteams_provenance.py`` (PR #24, f6205a7), the guard written
after mathAgents' v0.2.6 renders dropped every adopted routing row (CA-033): the agentteams that ran was
an unrecorded local snapshot taken before the fix. The check classifies the install that the resolved
``agentteams`` launcher imports, by its PEP 610 ``direct_url.json``:

  editable          refused unless the checkout's HEAD is on its origin/main and the imported package
                    directory has no uncommitted or untracked sources (bytecode caches excepted). The
                    shared checkout is switched between branches by other sessions.
  vcs               passes when the source is github.com/jlcatonjr/agentteams, naming the commit.
  local snapshot    refused (a frozen copy of a folder; its commit cannot be verified, and a stale one is
                    what caused CA-033/034), unless RESEARCHTEAM_ALLOW_AGENTTEAMS_SNAPSHOT=1, which runs
                    it with a WARNING. Matches mathAgents PR #25 (MATHAGENTS_ALLOW_AGENTTEAMS_SNAPSHOT).
  unverified        refused unless RESEARCHTEAM_ALLOW_UNVERIFIED_AGENTTEAMS=1 (then a WARNING): a VCS install
                    from any other repository (a fork or mirror at an unreviewed commit), a remote archive
                    install (no commit recorded), or an index install with no install record (agentteams
                    is not published on PyPI, so a package of that name from an index is someone else's).

"The code" is both modules the launcher runs: its entry module ``build_team`` (a top-level py-module
beside the package) and the ``agentteams`` package. A non-editable install whose modules Python does not
actually import (a checkout earlier on ``sys.path`` shadows them) is refused, since the code that runs is
not the code the record describes.

Two stages: ``check(exe)`` runs under researchteam's interpreter, finds the interpreter the launcher
uses (direct shebang, ``#!/usr/bin/env python3``, or pip's ``#!/bin/sh`` trampoline for long paths), and
re-runs this file there with ``--inner`` so the install it inspects is the one the launcher imports.
This file is stdlib-only for that reason. Exit 0 = OK to render; 1 = refused.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from urllib.parse import unquote, urlparse

try:  # imported as researchteam._agentteams_provenance
    from . import _fetch
except ImportError:  # run as a script (--inner) under the launcher's interpreter: _fetch.py sits beside it
    import _fetch  # type: ignore[no-redef]

TAG = "[researchteam] agentteams provenance"
ALLOW_SNAPSHOT_ENV = "RESEARCHTEAM_ALLOW_AGENTTEAMS_SNAPSHOT"
ALLOW_UNVERIFIED_ENV = "RESEARCHTEAM_ALLOW_UNVERIFIED_AGENTTEAMS"
# The one reviewed source: a VCS install must come from here (any scheme, case, `.git` or trailing slash).
CANONICAL_REPO = ("github.com", "/jlcatonjr/agentteams")
CANONICAL_SLUG = "jlcatonjr/agentteams"
# What the `agentteams` launcher runs: its console-script entry point is build_team:main.
ENTRY_MODULES = ("build_team", "agentteams")


def launcher_interpreter(exe: str) -> str | None:
    """The interpreter ``exe`` runs under, from its shebang (direct, env-style) or pip's /bin/sh trampoline."""
    try:
        head = Path(exe).read_text(encoding="utf-8", errors="replace").splitlines()[:3]
    except OSError:
        return None
    if not head or not head[0].startswith("#!"):
        return None
    parts = head[0][2:].strip().split()
    if not parts:
        return None
    if Path(parts[0]).name == "env":
        args = [a for a in parts[1:] if not a.startswith("-")]
        return shutil.which(args[0]) if args else None
    if Path(parts[0]).name in ("sh", "bash") and len(head) > 1:  # pip: '''exec' "/long/path/python" "$0" "$@"
        # A quoted interpreter path may contain spaces; an unquoted one stops at the first space (and then
        # fails the os.access check in check(): a refusal, never a wrong interpreter).
        m = re.search(r"exec'?\s+(?:\"([^\"]+)\"|(\S+))\s+\"\$0\"", head[1])
        return (m.group(1) or m.group(2)) if m else None
    return parts[0]


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    except OSError as exc:  # git missing: a failure the caller refuses on, never a pass
        return subprocess.CompletedProcess(["git", *args], 127, "", str(exc))


def _refuse(msg: str) -> int:
    print(f"{TAG}: REFUSED: {msg}", file=sys.stderr)
    return 1


def inner(exe: str) -> int:
    """Run under the launcher's interpreter: classify the install and check an editable checkout."""
    try:
        dist = metadata.distribution("agentteams")
        direct = json.loads(dist.read_text("direct_url.json") or "{}")
    except metadata.PackageNotFoundError:
        dist, direct = None, {}  # a bare source tree on sys.path: checked as a checkout
    except (OSError, ValueError) as exc:
        return _refuse(f"cannot read the agentteams install record ({exc})")
    if not isinstance(direct, dict):
        return _refuse("the agentteams install record (direct_url.json) is not an object")
    url = direct.get("url", "")
    dir_info, vcs_info = direct.get("dir_info", {}), direct.get("vcs_info", {})
    if not isinstance(url, str) or not isinstance(dir_info, dict) or not isinstance(vcs_info, dict):
        return _refuse("the agentteams install record (direct_url.json) is malformed")
    # The code that runs: the launcher's entry module (build_team, a top-level py-module beside the package)
    # and the agentteams package. Located without importing, so no agentteams code executes here.
    modules: dict[str, Path] = {}
    for name in ENTRY_MODULES:
        spec = importlib.util.find_spec(name)
        if spec is None or not spec.origin:
            return _refuse(f"{name} cannot be found by the launcher's interpreter")
        modules[name] = Path(spec.origin).resolve()
    pkg = modules["agentteams"].parent  # the directory actually imported (handles a src/ layout)
    if dir_info.get("editable") or dist is None:
        return _check_checkout(exe, url, pkg, modules)
    owned = {Path(str(dist.locate_file(f))).resolve() for f in (dist.files or [])}
    for name, origin in modules.items():  # the code that runs must be the install judged, not a shadowing copy
        if origin not in owned:
            return _refuse(f"the {name} that Python imports ({origin}) is not the installed copy the record "
                           "describes (a checkout earlier on sys.path shadows it)")
    if vcs_info.get("commit_id"):
        print(f"{TAG}: {exe} is a VCS install of {url} @ {str(vcs_info['commit_id'])[:12]}")
        if not is_canonical_repo(url):
            return _unverified(f"the VCS install comes from {url}, not github.com/jlcatonjr/agentteams (a fork "
                               "or mirror at a commit that was not reviewed there)")
        # GitHub serves a fork's commits under the parent's URL too, so the URL alone does not prove the commit
        # was reviewed: it must be on agentteams' main or a release/* branch.
        reviewed = _fetch.commit_is_reviewed(CANONICAL_SLUG, str(vcs_info["commit_id"]))
        if reviewed is False:
            return _unverified(f"commit {str(vcs_info['commit_id'])[:12]} is not on main or a release branch of "
                               "jlcatonjr/agentteams (GitHub serves fork commits under the upstream URL)")
        if reviewed is None:
            print(f"{TAG}: WARNING: could not confirm that commit {str(vcs_info['commit_id'])[:12]} is on "
                  "jlcatonjr/agentteams main or a release branch (offline or rate-limited; set GITHUB_TOKEN to "
                  "raise the limit); running it", file=sys.stderr)
    elif url.startswith("file:"):
        print(f"{TAG}: {exe} is a non-editable snapshot of {unquote(urlparse(url).path)}")
        if os.environ.get(ALLOW_SNAPSHOT_ENV) != "1":
            return _refuse("a local-folder snapshot records no commit and may be stale or from an unmerged branch; "
                           "install a VCS commit on main (pip install \"agentteams @ git+https://github.com/"
                           f"jlcatonjr/agentteams@<sha>\"), or set {ALLOW_SNAPSHOT_ENV}=1 to run it anyway")
        print(f"{TAG}: WARNING: running a local-folder snapshot ({ALLOW_SNAPSHOT_ENV}=1); its commit cannot be "
              "verified", file=sys.stderr)
    elif url:
        print(f"{TAG}: {exe} is an archive install of {url}")
        return _unverified("an archive install records no commit, so the code cannot be matched to a reviewed one")
    else:
        print(f"{TAG}: {exe} is an index install of agentteams {dist.version} (no install record)")
        return _unverified("agentteams is not published on PyPI, so a package of that name installed from an "
                           "index is not the reviewed source")
    return 0


def is_canonical_repo(url: str) -> bool:
    """Whether a VCS URL names github.com/jlcatonjr/agentteams (https or ssh, any case, ``.git``/``/`` optional)."""
    if re.match(r"^[\w.-]+@[\w.-]+:", url):  # scp-like git@github.com:owner/repo
        user_host, _, path = url.partition(":")
        host, path = user_host.split("@", 1)[1], "/" + path
    else:
        parsed = urlparse(url)
        try:
            if parsed.port not in (None, 443, 22):
                return False
        except ValueError:  # a malformed port
            return False
        host, path = parsed.hostname or "", parsed.path
    path = path.lower().rstrip("/").removesuffix(".git").rstrip("/")
    return (host.lower(), path) == CANONICAL_REPO


def _unverified(reason: str) -> int:
    if os.environ.get(ALLOW_UNVERIFIED_ENV) == "1":
        print(f"{TAG}: WARNING: running an unverified agentteams install ({ALLOW_UNVERIFIED_ENV}=1): {reason}",
              file=sys.stderr)
        return 0
    return _refuse(f"{reason}; install a reviewed commit (pip install \"agentteams @ git+https://github.com/"
                   f"jlcatonjr/agentteams@<sha>\"), or set {ALLOW_UNVERIFIED_ENV}=1 to run it anyway")


def _check_checkout(exe: str, url: str, pkg: Path, modules: dict[str, Path]) -> int:
    """An editable install (or a bare source tree on sys.path): its checkout must be on origin/main and clean."""
    if url.startswith("file:"):
        src = Path(unquote(urlparse(url).path)).resolve()
        for name, origin in modules.items():
            if src not in origin.parents:
                return _refuse(f"the {name} that Python imports ({origin}) is outside the editable checkout {src}")
    top = _git(pkg, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        return _refuse(f"the editable agentteams at {pkg} is not in a git checkout")
    repo = Path(top.stdout.strip()).resolve()
    for name, origin in modules.items():
        if repo not in origin.parents:
            return _refuse(f"the {name} that Python imports ({origin}) is outside the checkout {repo}")
    head, branch = _git(repo, "rev-parse", "HEAD"), _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    if head.returncode != 0:
        return _refuse(f"cannot read HEAD of {repo}")
    sha, name = head.stdout.strip(), branch.stdout.strip() or "?"
    print(f"{TAG}: {exe} is an editable checkout {repo}, branch {name}, commit {sha[:12]}")
    anc = _git(repo, "merge-base", "--is-ancestor", sha, "origin/main")
    if anc.returncode != 0:
        return _refuse(f"commit {sha[:12]} (branch {name}) is not on origin/main (or origin/main is missing); "
                       "render only merged agentteams: check out main there, fetch if origin/main is stale, or "
                       "install a pinned commit (pip install \"agentteams @ git+https://github.com/jlcatonjr/"
                       "agentteams@<sha>\")")
    status = _git(repo, "status", "--porcelain", "--", str(pkg), str(modules["build_team"]))
    if status.returncode != 0:
        return _refuse(f"git status failed in {repo}: {status.stderr.strip()[:200]}")
    dirty = [ln for ln in status.stdout.splitlines() if not re.search(r"(__pycache__/|\.pyc$)", ln)]
    if dirty:
        return _refuse(f"uncommitted or untracked agentteams sources in {repo}: "
                       f"{', '.join(d[3:] for d in dirty[:5])}")
    return 0


def check(exe: str) -> int:
    """Classify the install behind the ``agentteams`` launcher ``exe``; 0 = OK to render, 1 = refused."""
    py = launcher_interpreter(exe)
    if not py or not os.access(py, os.X_OK):
        return _refuse(f"cannot determine the interpreter of {exe} (shebang not understood)")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    # Not -I: a real launcher run honours PYTHONPATH (a shadowing source), and like the launcher, script
    # mode puts the script's own directory (not cwd) at sys.path[0].
    return subprocess.run([py, str(Path(__file__).resolve()), "--inner", exe], env=env).returncode


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--inner":
        sys.exit(inner(sys.argv[2]))
    sys.exit("usage: _agentteams_provenance.py --inner <agentteams-launcher>")
