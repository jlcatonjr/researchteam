#!/usr/bin/env python3
"""check_toolchain.py — is this checkout's researchteam / agentteams the pinned one?

Compares the installed commits against ``toolchain.lock`` and (optionally) against upstream main,
and prints a short notice when anything is behind. Used by the SessionStart hook in
``.claude/settings.toolchain.example.json`` (its stdout becomes session context), by
``scripts/bootstrap_toolchain.sh`` and by ``researchteam doctor``. ``--write-lock`` is used by the
autosync gate to record what a green sync was verified with.

Managed by researchteam (layer 2); adapted from OrthodoxLLM a291cf2.

Which interpreter is inspected, first match wins:
  --python PATH  >  <repo>/.venv/bin/python  >  the interpreter behind `researchteam` on PATH.

Lock format (one pin per line, ``#`` comments allowed)::

    researchteam=jlcatonjr/researchteam@<40-hex sha>
    agentteams=jlcatonjr/agentteams@<40-hex sha>
    agentteams.tag=v1.0.0-rc.14          # optional: release-locked (see researchteam/_release.py)

A pin with a ``<name>.tag`` line is RELEASE-LOCKED: its commit is that verified signed tag's peeled
commit, and ``--write-lock`` moves it only to a newer verified tag on the same ``vX.Y`` line
(``--tag name=vX.Y.Z``), never to an untagged commit such as agentteams ``main``.

When the repository's own ``pyproject.toml`` installs agentteams from git (researchteam's ``update`` /
``research`` extras), each such ref must name the same commit as the agentteams pin (release policy §3);
a bare or different ref is a problem like a mismatched install.

Exit 0 always (advisory), unless --strict, which exits 1 when a pin does not match.
``--write-lock`` exits 1 if either package has no recorded commit or comes from a dirty checkout.
Stdlib only.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK = os.path.join(ROOT, "toolchain.lock")
PACKAGES = ("researchteam", "agentteams")
# The ONLY repositories a pin may name. bootstrap_toolchain.sh installs (and so runs the build code
# of) whatever the lock names, so an edited lock must not be able to point it anywhere else.
DEFAULT_REPOS = {"researchteam": "jlcatonjr/researchteam", "agentteams": "jlcatonjr/agentteams"}
HOOK_SCRIPT = "scripts/check_toolchain.py"
_SHA = re.compile(r"^[0-9a-f]{40}$")

LOCK_HEADER = """\
# Toolchain pin: the researchteam / agentteams commits this repository was last synced and verified
# against (researchteam update + validate + gates). Written by the AgentTeams Autosync after a green
# sync (scripts/check_toolchain.py --write-lock); read by scripts/bootstrap_toolchain.sh (builds .venv)
# and scripts/check_toolchain.py (SessionStart hook, researchteam doctor). Bump only after a green sync.
"""


def read_lock(path=None):
    """{name: (owner/repo, sha)} from the lock; {} when it does not exist."""
    path = path or LOCK
    pins = {}
    if not os.path.exists(path):
        return pins
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                name, spec = line.split("=", 1)
                if "." in name:  # a <name>.tag line, read by read_tags
                    continue
                repo, _, sha = spec.partition("@")
                pins[name.strip()] = (repo.strip(), sha.strip())
    return pins


def read_tags(path=None):
    """{name: release tag} for the release-locked pins in the lock."""
    path = path or LOCK
    tags = {}
    if not os.path.exists(path):
        return tags
    with open(path, encoding="utf-8") as f:
        for line in f:
            name, sep, tag = line.strip().partition(".tag=")
            if sep and name in PACKAGES:
                tags[name] = tag.strip()
    return tags


def pin_problem(name, repo, sha):
    """Why a pin is unacceptable, or "" when it names the allowed repo at a full commit SHA."""
    if repo != DEFAULT_REPOS.get(name):
        return f"toolchain.lock pins {name} to {repo or '(none)'}; only {DEFAULT_REPOS.get(name)} is allowed"
    if not _SHA.match(sha):
        return f"toolchain.lock pins {name} to {sha or '(none)'!r}, not a 40-hex commit"
    return ""


_EXTRA_DEP = re.compile(r'"agentteams(?:\[[^\]]*\])?\s*@\s*git\+https://github\.com/([^/"\s]+/[^@"\s]+?)'
                        r'(?:\.git)?(?:@([^"#\s]+))?"')


def extras_problems(pins, pyproject=None):
    """Each git-installed agentteams requirement in pyproject.toml that does not name the lock's commit."""
    pyproject = pyproject or os.path.join(os.path.dirname(LOCK), "pyproject.toml")  # the lock's own repo
    try:
        with open(pyproject, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return []
    repo, pin = pins.get("agentteams", ("", ""))
    out = []
    for m in _EXTRA_DEP.finditer(text):
        dep_repo, ref = m.group(1), m.group(2) or ""
        if dep_repo != repo or ref != pin:
            out.append(f"pyproject.toml installs agentteams from {dep_repo}@{ref or '(no ref: main)'}, "
                       f"but toolchain.lock pins {repo}@{pin[:7]}; pin the extra to the same commit")
    return out


def write_lock(commits, path=None, tags=None):
    """Write the lock from {name: (owner/repo, sha)} and {name: release tag}, keeping the fixed header."""
    path = path or LOCK
    tags = tags or {}
    body = "".join(f"{name}={commits[name][0]}@{commits[name][1]}\n"
                   + (f"{name}.tag={tags[name]}\n" if name in tags else "") for name in PACKAGES)
    with open(path, "w", encoding="utf-8") as f:
        f.write(LOCK_HEADER + body)


def launcher_interpreter(exe):
    """The interpreter a console script runs under (direct, env-style or pip-trampoline shebang)."""
    try:
        with open(exe, encoding="utf-8", errors="replace") as f:
            head = [f.readline() for _ in range(2)]
    except OSError:
        return None
    if not head[0].startswith("#!"):
        return None
    parts = head[0][2:].strip().split()
    if not parts:
        return None
    if os.path.basename(parts[0]) == "env":
        args = [a for a in parts[1:] if not a.startswith("-")]
        return shutil.which(args[0]) if args else None
    if os.path.basename(parts[0]) in ("sh", "bash"):
        m = re.search(r"exec'?\s+(?:\"([^\"]+)\"|(\S+))\s+\"\$0\"", head[1])
        return (m.group(1) or m.group(2)) if m else None
    return parts[0]


def pick_python(explicit):
    if explicit:
        return explicit
    venv = os.path.join(ROOT, ".venv", "bin", "python")
    if os.path.exists(venv):
        return venv
    exe = shutil.which("researchteam")
    return launcher_interpreter(exe) if exe else None


_PROBE = r"""
import importlib.metadata as m, json, sys
out = {}
for name in sys.argv[1:]:
    try:
        d = m.distribution(name)
    except m.PackageNotFoundError:
        out[name] = None
        continue
    try:
        du = json.loads(d.read_text("direct_url.json") or "null")
    except ValueError:
        du = None
    out[name] = {"version": d.version, "direct_url": du}
print(json.dumps(out))
"""


def installed(py):
    try:
        # -I: isolated mode, so the probe never sees the current directory. A repo root with a
        # researchteam.egg-info from an editable build would otherwise shadow the real install record.
        r = subprocess.run([py, "-I", "-c", _PROBE, *PACKAGES], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


def commit_of(info):
    """(sha or None, how) for one package's install record."""
    du = info.get("direct_url") if isinstance(info, dict) else None
    if not isinstance(du, dict):
        return None, "installed from an index (no commit recorded)"
    vcs = du.get("vcs_info")
    if isinstance(vcs, dict) and vcs.get("commit_id"):
        return vcs["commit_id"], "git pin"
    dir_info = du.get("dir_info") if isinstance(du.get("dir_info"), dict) else {}
    url = du.get("url", "") or ""
    if dir_info.get("editable") and url.startswith("file://"):
        path = unquote(url[len("file://"):])
        try:
            # core.fsmonitor=false: never run a checkout-configured monitor from a session hook
            r = subprocess.run(["git", "-C", path, "rev-parse", "HEAD"], capture_output=True, text=True,
                               timeout=5)
            dirty = subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", path, "status", "--porcelain",
                                    "--untracked-files=no"], capture_output=True, text=True, timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            return None, f"editable {path} (git unavailable)"
        if r.returncode == 0:
            return r.stdout.strip(), f"editable {path}" + (" (dirty)" if dirty.stdout.strip() else "")
        return None, f"editable {path}"
    if url:
        return None, f"local folder {url} (no commit recorded)"
    return None, "installed from an index (no commit recorded)"


def repo_of(info, name):
    """owner/repo for a git-pinned install (from its URL), else the default upstream."""
    du = info.get("direct_url") if isinstance(info, dict) else None
    url = (du or {}).get("url", "") if isinstance(du, dict) else ""
    m = re.search(r"github\.com[:/]([^/]+/[^/@]+?)(?:\.git)?/?$", url)
    return m.group(1) if m else DEFAULT_REPOS[name]


def remote_main(repo):
    try:
        r = subprocess.run(["git", "ls-remote", f"https://github.com/{repo}", "refs/heads/main"],
                           capture_output=True, text=True, timeout=5)
    except (subprocess.TimeoutExpired, OSError):
        return None
    return r.stdout.split()[0] if r.returncode == 0 and r.stdout.strip() else None


def hook_installed(root=None):
    """Whether .claude/settings.json (or settings.local.json) runs this check at SessionStart."""
    root = root or ROOT
    for name in ("settings.json", "settings.local.json"):
        try:
            with open(os.path.join(root, ".claude", name), encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        hooks = data.get("hooks") if isinstance(data, dict) else None
        entries = hooks.get("SessionStart") if isinstance(hooks, dict) else None
        for entry in entries if isinstance(entries, list) else []:
            inner = entry.get("hooks") if isinstance(entry, dict) else None
            for hook in inner if isinstance(inner, list) else []:
                if isinstance(hook, dict) and HOOK_SCRIPT in str(hook.get("command", "")):
                    return True
    return False


def _release():
    """researchteam._release, or None when the installed researchteam predates release-line pins."""
    try:
        from researchteam import _release
    except ImportError:
        return None
    return _release


def parse_tag_args(values):
    """{name: tag} from repeated --tag name=vX.Y.Z; raises ValueError on a malformed one."""
    out = {}
    for v in values or []:
        name, sep, tag = v.partition("=")
        if not sep or name not in PACKAGES or not tag:
            raise ValueError(f"--tag {v!r}: expected one of {', '.join(PACKAGES)}=vX.Y.Z[-rc.N]")
        out[name] = tag
    return out


def lock_tags(commits, old_pins, old_tags, new_tags, verify):
    """The tags to write, or (None, why) when the move would break a release lock.

    A release-locked pin keeps its tag while its commit is unchanged. It moves only to a ``--tag`` that is
    newer on the same release line and whose verified peeled commit is the installed one. A ``--tag``
    on an unlocked pin starts a release lock under the same verification.
    """
    tags = {}
    for name in PACKAGES:
        sha, old_tag, new_tag = commits[name][1], old_tags.get(name), new_tags.get(name)
        if new_tag is None:
            if old_tag is None:
                continue
            if old_pins.get(name, ("", ""))[1] != sha:
                return None, (f"{name} is release-locked at {old_tag}; refusing to move it to the untagged "
                              f"commit {sha[:7]} (pass --tag {name}=<newer verified tag> to move it)")
            tags[name] = old_tag
            continue
        rel = verify()
        if rel is None:
            return None, "researchteam._release is unavailable; cannot verify --tag (install researchteam >= 1.0)"
        try:
            if old_tag is not None and (rel.release_line(new_tag) != rel.release_line(old_tag)
                                        or rel.tag_key(new_tag) < rel.tag_key(old_tag)):
                return None, f"{name}: {new_tag} is not on {old_tag}'s release line, or is older"
            _, peeled = rel.verify_tag(commits[name][0], new_tag)
        except rel.ReleaseError as exc:
            return None, f"{name}: {exc}"
        if peeled != sha:
            return None, f"{name}: installed {sha[:7]} is not {new_tag}'s peeled commit {peeled[:7]}"
        tags[name] = new_tag
    return tags, ""


def cmd_write_lock(py, new_tags=None):
    info = installed(py) if py else None
    if not info:
        print(f"[toolchain] cannot inspect {py or 'any interpreter'}; toolchain.lock not written")
        return 1
    commits = {}
    for name in PACKAGES:
        if info.get(name) is None:
            print(f"[toolchain] {name} is not installed in {py}; toolchain.lock not written")
            return 1
        sha, how = commit_of(info[name])
        if sha is None or not _SHA.match(sha) or "dirty" in how:
            print(f"[toolchain] {name}: {how}; a lock needs a clean recorded commit, not written")
            return 1
        repo = repo_of(info[name], name)
        why = pin_problem(name, repo, sha)
        if why:
            print(f"[toolchain] {why}; not written")
            return 1
        commits[name] = (repo, sha)
    old = read_lock()
    tags, why = lock_tags(commits, old, read_tags(), new_tags or {}, _release)
    if tags is None:
        print(f"[toolchain] {why}; toolchain.lock not written")
        return 1
    write_lock(commits, tags=tags)
    changed = {n for n in PACKAGES if old.get(n, ("", ""))[1] != commits[n][1]}
    summary = ", ".join(f"{n} {commits[n][1][:7]}" + (f" ({tags[n]})" if n in tags else "") for n in PACKAGES)
    print(f"[toolchain] toolchain.lock {'updated' if changed else 'unchanged'}: {summary}")
    return 0


def cmd_release(candidate_of, verify):
    """--release-candidate / --verify-tag for the autosync gate. Exit 1 when the answer cannot be trusted."""
    rel = _release()
    if rel is None:
        print("[toolchain] researchteam._release is unavailable (install researchteam >= 1.0)", file=sys.stderr)
        return 1
    pins, tags = read_lock(), read_tags()
    name = candidate_of or verify[0]
    if name not in PACKAGES or pin_problem(name, *pins.get(name, ("", ""))):
        print(f"[toolchain] {name}: no valid pin in toolchain.lock", file=sys.stderr)
        return 1
    try:
        if candidate_of:
            if name not in tags:
                return 0  # not release-locked: no candidate
            newer = rel.newest_on_line(pins[name][0], tags[name])
            if newer:
                print(newer)
            return 0
        print(rel.verify_tag(pins[name][0], verify[1])[1])
        return 0
    except rel.ReleaseError as exc:
        print(f"[toolchain] {name}: {exc}", file=sys.stderr)
        return 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--python")
    ap.add_argument("--no-remote", action="store_true", help="skip the upstream-main comparison")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--write-lock", action="store_true",
                    help="record the installed commits in toolchain.lock (autosync, after a green sync)")
    ap.add_argument("--tag", action="append", metavar="NAME=TAG",
                    help="with --write-lock: the verified release tag the installed NAME commit is (repeatable)")
    ap.add_argument("--release-candidate", metavar="NAME",
                    help="print the newest verified-able tag on NAME's locked release line, if newer; exit 0")
    ap.add_argument("--verify-tag", nargs=2, metavar=("NAME", "TAG"),
                    help="verify TAG of NAME's pinned repository and print its peeled commit")
    a = ap.parse_args(argv)

    if a.release_candidate or a.verify_tag:
        return cmd_release(a.release_candidate, a.verify_tag)
    py = pick_python(a.python)
    if a.write_lock:
        try:
            new_tags = parse_tag_args(a.tag)
        except ValueError as exc:
            print(f"[toolchain] {exc}")
            return 2
        return cmd_write_lock(py, new_tags)

    pins = read_lock()
    fix = "run: bash scripts/bootstrap_toolchain.sh"
    if not pins:
        print("[toolchain] no toolchain.lock yet; the next AgentTeams Autosync writes one "
              "(nothing to compare against)")
        return 0
    extras = extras_problems(pins)
    for e in extras:
        print(f"[toolchain] MISMATCH: {e}")
    if not py:
        print(f"[toolchain] researchteam/agentteams not installed for this repo — {fix}")
        return 1 if a.strict else 0
    info = installed(py)
    if info is None:
        print(f"[toolchain] could not inspect {py} — {fix}")
        return 1 if a.strict else 0

    problems, notes, tags = [], [], read_tags()
    for name in PACKAGES:
        repo, pin = pins.get(name, ("", ""))
        why = pin_problem(name, repo, pin)
        if why:
            problems.append(why)
            continue
        if info.get(name) is None:
            problems.append(f"{name} is not installed in {py}")
            continue
        sha, how = commit_of(info[name])
        if sha is None:
            problems.append(f"{name}: {how}; cannot confirm it matches the pin {pin[:7]}")
        elif sha != pin:
            problems.append(f"{name}: installed {sha[:7]} ({how}) but toolchain.lock pins {pin[:7]}")
        elif "dirty" in how:
            notes.append(f"{name}: matches the pin, but the editable checkout has uncommitted changes")
        if name in tags:
            continue  # release-locked: upstream main is irrelevant; the gate follows the release line
        if not a.no_remote and repo:
            head = remote_main(repo)
            if head and head != pin:
                notes.append(f"{name}: upstream main is {head[:7]}, newer than the pin {pin[:7]} — "
                             "the next AgentTeams Autosync PR moves the pin")

    problems += extras
    if not problems and not notes:
        print(f"[toolchain] OK: researchteam and agentteams match toolchain.lock ({py})")
        return 0
    for p in problems:
        if p not in extras:
            print(f"[toolchain] BEHIND: {p}")
    for n in notes:
        print(f"[toolchain] note: {n}")
    if problems:
        print(f"[toolchain] {fix}   (or `--local` for editable checkouts)")
    return 1 if (a.strict and problems) else 0


if __name__ == "__main__":
    sys.exit(main())
