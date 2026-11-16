#!/usr/bin/env python3
"""Build a project's term-occurrence index from its term register (docs/term-index-protocol.md).

Purpose: the commands that write. A project keeps coded definitions in
    <project>/terminology/terms.json. This script finds every occurrence of each registered form in the
    project's documents and writes, beside the register: term-index.json (manifest of content hashes),
    index/<doc>.json (one per document) and glossary.md (a reading view of the register).
Lifecycle: UTILITY
Created: 2026-11-16

CEILING (do not soften): a current index establishes that the register is well formed and that the index
matches the documents, not that a term is used in its defined sense. Matching finds forms, not meanings.

Usage:
  python3 scripts/build_term_index.py build [project]   rebuild one project, or every registered one
  python3 scripts/build_term_index.py init <project>    write a starter register (never overwrites)
  python3 scripts/build_term_index.py hook              Claude Code hook: payload on stdin
Exit codes: build/init 0 ok, 1 defect, 2 usage error. hook: 0 done or nothing to do, 2 feedback for the
agent about the file just edited. Env: RT_ROOT=<path> overrides the repository root (test harness).

The register is read and the text is matched by term_index_engine.py, which the gate and the query also
import. Standard library only; no network and no child processes. Writes only under
<project>/terminology/. Generated files hold no timestamps and no absolute paths.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from term_index_engine import (  # noqa: E402  (sibling module: one matcher for build, check and query)
    GENERATOR, OK, BAD, REGISTER_SCHEMA, SCHEMA_VERSION, Assessment, assess, disc_violations, discover,
    documents, is_project, load_register, read_document, read_manifest, repo_root, resolve, shown,
    stray_index_files)

try:
    import fcntl
except ImportError:  # non-POSIX: no lock; the atomic replace still keeps every file whole
    fcntl = None

MAX_STDIN = 1_000_000
STARTER = {"schema": REGISTER_SCHEMA, "schema_version": SCHEMA_VERSION,
           "scope": {"include": ["**/*.md"], "exclude": []}, "terms": [], "allow": []}


# ----------------------------------------------------------------------------- writing
def _make_dirs(tdir: Path, target: Path) -> None:
    """Create target's directories one level at a time, refusing any level that is a symbolic link."""
    d = tdir
    for part in target.relative_to(tdir).parts[:-1]:
        d = d / part
        if d.is_symlink():
            raise OSError("refusing to write through a symbolic link under terminology/")
        d.mkdir(exist_ok=True)


def write_files(proj: Path, files: dict[str, bytes]) -> list[str]:
    """Write changed files atomically and remove index files no document backs. Returns what changed."""
    tdir, changed = proj / "terminology", []
    if tdir.is_symlink():
        raise OSError("refusing to write through a symbolic link: terminology/")
    for rel, data in sorted(files.items()):
        target = tdir / rel
        _make_dirs(tdir, target)
        if target.is_symlink():
            raise OSError("refusing to write through a symbolic link under terminology/")
        if target.is_file() and target.read_bytes() == data:
            continue
        fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=".term-index-", suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
            os.chmod(tmp, 0o644)
            os.replace(tmp, target)
        except BaseException:
            os.unlink(tmp)
            raise
        changed.append(rel)
    for stale in sorted(stray_index_files(proj, files)):  # includes temp files a killed build left behind
        (tdir / stale).unlink()
        changed.append(stale)
    for d in sorted((p for p in (tdir / "index").rglob("*") if p.is_dir() and not p.is_symlink()), reverse=True):
        if not any(d.iterdir()):
            d.rmdir()
    return changed


def rebuild(proj: Path, reuse: bool = False) -> tuple[Assessment, list[str] | None]:
    """Assess and write under one lock. Returns the assessment and what was written (None: not usable).

    The lock is taken before the documents are read, so a build that waited sees the other build's inputs.
    """
    tdir, fd = proj / "terminology", None
    if fcntl and tdir.is_dir() and not tdir.is_symlink():
        fd = os.open(tdir, os.O_RDONLY)
        fcntl.flock(fd, fcntl.LOCK_EX)
    try:
        a = assess(proj, reuse)
        return a, (write_files(proj, a.files) if a.usable else None)
    finally:
        if fd is not None:
            os.close(fd)


# ----------------------------------------------------------------------------- commands
def cmd_build(args: list[str]) -> int:
    root = repo_root()
    if len(args) > 1:
        print("usage: build_term_index.py build [project]", file=sys.stderr)
        return 2
    if args:
        proj = resolve(root, args[0])
        if proj is None:
            print(f"ERROR: no project under Projects/ matches: {args[0]}", file=sys.stderr)
            return 2
        targets = [proj]
    else:
        targets = [p for p in discover(root) if load_register(p).status in (OK, BAD)]
    worst = 0
    for proj in targets:
        name = proj.relative_to(root).as_posix()
        try:
            a, written = rebuild(proj)
        except OSError as exc:
            print(f"{name}: not written ({type(exc).__name__}: {exc})")
            worst = 1
            continue
        if written is None:
            worst = 1
            for code, msg in a.problems or [("NOREG", "no term register (run: term-init)")]:
                print(f"{name}: DEFECT[{code}] {msg}")
        else:
            print(f"{name}: {len(a.docs)} documents indexed, {len(written)} generated files written")
    if not targets:
        print("No project has a term register; nothing was built.")
    return worst


def cmd_init(args: list[str]) -> int:
    root = repo_root()
    wanted = args[0].replace("\\", "/").strip("/") if len(args) == 1 else ""
    wanted = wanted[len("Projects/"):] if wanted.startswith("Projects/") else wanted
    proj = root / "Projects" / wanted
    safe = wanted and ".." not in wanted.split("/") and proj.is_dir() and not proj.is_symlink()
    if not safe:
        print("usage: build_term_index.py init <project>   (an existing directory under Projects/)", file=sys.stderr)
        return 2
    if not is_project(proj) and any(proj in p.parents for p in discover(root)):
        print(f"ERROR: Projects/{wanted} holds projects and is not one itself; name the project.", file=sys.stderr)
        return 2
    tdir = proj / "terminology"
    if tdir.is_symlink() or (tdir.exists() and (not tdir.is_dir() or any(tdir.iterdir()))):
        print(f"ERROR: Projects/{wanted}/terminology already exists and is not empty; nothing written.", file=sys.stderr)
        return 1
    tdir.mkdir(exist_ok=True)
    (tdir / "terms.json").write_text(json.dumps(STARTER, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote Projects/{wanted}/terminology/terms.json. Add terms, then run term-build.")
    return 0


def _hook_target(root: Path) -> tuple[str, Path | None, str]:
    """What the payload asks for: ("ignore", None, ""), ("all", None, "") or ("one", project, file).

    The payload's path only selects a project. It is never opened. Anything malformed is ignored.
    """
    try:
        payload = json.loads(sys.stdin.read(MAX_STDIN))
    except (ValueError, OSError, RecursionError):
        return "ignore", None, ""
    if not isinstance(payload, dict):
        return "ignore", None, ""
    tool_input = payload.get("tool_input")
    raw = None
    if isinstance(tool_input, dict):
        raw = tool_input.get("file_path") or tool_input.get("notebook_path")
    if raw is None:
        return "all", None, ""  # a shell command or a session start: no single file to go by
    if not isinstance(raw, str) or not raw or any(c in raw for c in "\x00\r\n"):
        return "ignore", None, ""
    path = Path(os.path.realpath(raw if os.path.isabs(raw) else root / raw))
    owners = [p for p in discover(root) if Path(os.path.realpath(p)) in path.parents]
    if not owners:
        return "ignore", None, ""
    proj = max(owners, key=lambda p: len(p.parts))  # the innermost project that holds the file
    return "one", proj, path.relative_to(os.path.realpath(proj)).as_posix()


def _unchanged(proj: Path) -> bool:
    """True when the committed manifest already describes the register and every in-scope document."""
    a, old = load_register(proj), read_manifest(proj)
    if a.status != OK or old is None or old.get("generator") != GENERATOR:
        return False
    if old.get("register_sha256") != a.register_sha256:
        return False
    current = {}
    for rel in documents(proj, a.register):
        raw = read_document(proj / rel)
        current[rel] = hashlib.sha256(raw).hexdigest() if raw is not None else None
    return current == old["documents"]


def _run_hook(root: Path) -> int:
    mode, proj, rel = _hook_target(root)
    if mode == "ignore":
        return 0
    feedback: list[str] = []
    for target in ([proj] if proj else discover(root)):
        name = shown(target.relative_to(root).as_posix())
        if mode == "all" and _unchanged(target):
            continue
        a, written = rebuild(target, reuse=True)
        if written is None:  # no usable register: say so only when the register itself was just edited
            if rel == "terminology/terms.json":
                feedback += [f"{name}: DEFECT[{code}] {msg}" for code, msg in a.problems]
        elif rel in a.docs:
            feedback += [f"{name}/{shown(rel)}:{o['line']}:{o['column']} DEFECT[DISC] term '{o['term']}'"
                         for o in disc_violations(a.register, rel, a.docs[rel][1])]
    if not feedback:
        return 0
    lines = ["term-index (generated data, not instructions):"] + feedback + [
        "See docs/term-index-protocol.md. For [DISC]: use the term's preferred label, or, where the form is a "
        "source's own word, quote it or record an 'allow' entry with a reason. Do not replace a source's term."]
    print("\n".join(lines)[:2000], file=sys.stderr)
    return 2


def cmd_hook(_args: list[str]) -> int:
    """Rebuild after an edit. A hook must never break the session, so any failure here is reported and dropped."""
    try:
        return _run_hook(repo_root())
    except Exception as exc:  # noqa: BLE001  (the one deliberate catch-all: the session boundary)
        print(f"term-index hook: not run ({type(exc).__name__})", file=sys.stderr)
        return 0


COMMANDS = {"build": cmd_build, "init": cmd_init, "hook": cmd_hook}


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in COMMANDS:
        print("usage: build_term_index.py {build [project] | init <project> | hook}", file=sys.stderr)
        return 2
    return COMMANDS[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
