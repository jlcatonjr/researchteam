#!/usr/bin/env python3
"""Check the pinned copy of the agentteams term-index core against its manifest, and load it.

Purpose: scripts/term-index-core/ holds two files of agentteams' term-index core, byte for byte as the
    signed agentteams tag named in scripts/term-index-core/PINNED.json has them, with their sha256 values.
    This script is both the offline check (run as a command) and the loader term_index_engine.py imports,
    so the check and the load share one hash routine. The term index never imports an installed agentteams.
Lifecycle: UTILITY
Created: 2026-11-24

What a pass proves, and what it does not: every listed file is a regular file whose bytes have the sha256
the manifest records, and no unlisted code file sits in the directory. It does not prove that the manifest
matches upstream; that is the network comparison against the signed tag
(`python -m researchteam._term_core_upstream`), required when the pin moves and at release.

Usage:
  python3 scripts/check_term_core.py
Exit codes: 0 every file matches | 1 a file is mismatched, missing, a symbolic link or not a regular file, or
  a code file in the directory is not listed | 2 the manifest is unreadable or malformed, or the directory is
  a symbolic link. Standard library only; no network, no child process, nothing written.

Loading (load()): each listed file is read once, through a descriptor opened without following links, and
hashed; the bytes that were hashed are the bytes compiled. The files become submodules of a private package,
`_researchteam_term_core`, whose `__path__` is empty, so nothing is ever found on disk. They are registered in
sys.modules before they run (the core's dataclasses need that) and run in manifest order. Their imports go
through a restricted `__import__` in their own builtins: `agentteams.<name>` resolves to the pinned module of
that upstream path (the import shim, design note option (b)), any other agentteams import is refused, and so
is anything outside the standard library. No process-wide import state is swapped.
"""
from __future__ import annotations

import builtins
import errno
import hashlib
import importlib.machinery
import json
import linecache
import os
import re
import stat
import sys
import threading
import types
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parent / "term-index-core"
MANIFEST = "PINNED.json"
FORMAT = "researchteam-pinned-copy/1"
LOCAL_PREFIX = "scripts/term-index-core/"
PACKAGE = "_researchteam_term_core"
UPSTREAM_PACKAGE = "agentteams"
MAX_FILE_BYTES = 1_000_000
CODE_SUFFIXES = (".py", ".pyc", ".pyo", ".pyw", ".pyd", ".so", ".pth")
MODULE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\.py$")
DATA_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
UPSTREAM_PATH = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9._-]*(/[A-Za-z0-9_][A-Za-z0-9._-]*)*$")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
TAG = re.compile(r"^v\d+\.\d+\.\d+(-rc\.\d+)?$")
SHA1, SHA256 = re.compile(r"^[0-9a-f]{40}$"), re.compile(r"^[0-9a-f]{64}$")
_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
_DIR_FD = os.open in os.supports_dir_fd and bool(_NOFOLLOW) and hasattr(os, "O_DIRECTORY")
_LINK_ERRNOS = {errno.ELOOP, getattr(errno, "EMLINK", -1)}  # O_NOFOLLOW on a link (EMLINK on FreeBSD)


class CoreCheckFailed(Exception):
    """The copy did not verify, or did not load. `lines` are the report; `code` is the command's exit code."""

    def __init__(self, code: int, lines: list[str]):
        super().__init__("\n".join(lines))
        self.code, self.lines = code, lines


# ----------------------------------------------------------------------------- the repair message
def installed_researchteam() -> str:
    """The researchteam version installed for this interpreter, for the repair message."""
    try:
        from importlib.metadata import PackageNotFoundError, version
        try:
            return f"researchteam {version('researchteam')} (this interpreter)"
        except PackageNotFoundError:
            return "no researchteam in this interpreter"
    except Exception:  # noqa: BLE001  (only a message depends on it)
        return "researchteam version unknown"


def repair_lines() -> list[str]:
    """Upgrade first: an older researchteam syncs its own file list, which does not include this directory."""
    return [
        "[term-core] The term index will not run until the copy verifies. There is no override.",
        "[term-core] Repair: restore the files from git (git checkout -- scripts/term-index-core/ "
        "scripts/check_term_core.py), or receive them with researchteam update.",
        f"[term-core] Before researchteam update, upgrade researchteam ({installed_researchteam()}): "
        "bash scripts/bootstrap_toolchain.sh, or pip install researchteam at the tag toolchain.lock names. "
        "An older researchteam does not sync this directory, so re-running its update changes nothing.",
    ]


def _fail(code: int, lines: list[str]) -> CoreCheckFailed:
    return CoreCheckFailed(code, lines + repair_lines())


# ----------------------------------------------------------------------------- reading without links
def _open_dir(path: Path) -> int | None:
    """A descriptor for the core directory, opened without following a link; None where dir_fd is missing."""
    if not _DIR_FD:
        if path.is_symlink():
            raise _fail(2, [f"[term-core] LINK {LOCAL_PREFIX}: the directory is a symbolic link (refused)"])
        return None
    try:
        return os.open(path, os.O_RDONLY | os.O_DIRECTORY | _NOFOLLOW)
    except FileNotFoundError:
        raise _fail(2, [f"[term-core] MISSING {LOCAL_PREFIX}: the pinned core directory is not here"]) from None
    except OSError as exc:
        what = "is a symbolic link" if exc.errno in _LINK_ERRNOS or path.is_symlink() else "cannot be opened"
        raise _fail(2, [f"[term-core] LINK {LOCAL_PREFIX}: the directory {what} (refused)"]) from None


def _read(dfd: int | None, name: str) -> tuple[str, bytes | None]:
    """("ok", bytes), ("missing"|"link"|"refused", None). One descriptor: opened, checked with fstat, read."""
    flags = os.O_RDONLY | _NOFOLLOW | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0)
    try:
        if dfd is not None:
            fd = os.open(name, flags, dir_fd=dfd)
        else:
            if (CORE_DIR / name).is_symlink():
                return "link", None
            fd = os.open(CORE_DIR / name, flags)
    except FileNotFoundError:
        return "missing", None
    except OSError as exc:
        return ("link" if exc.errno in _LINK_ERRNOS else "refused"), None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE_BYTES:
            return "refused", None
        chunks, left = [], MAX_FILE_BYTES + 1
        while left > 0:
            chunk = os.read(fd, min(left, 1 << 20))
            if not chunk:
                break
            chunks.append(chunk)
            left -= len(chunk)
        data = b"".join(chunks)
        return ("refused", None) if len(data) > MAX_FILE_BYTES else ("ok", data)
    finally:
        os.close(fd)


# ----------------------------------------------------------------------------- the manifest
def _entries(value, kind: str, problems: list[str]) -> list[dict]:
    if not isinstance(value, list) or (kind == "files" and not value):
        problems.append(f"'{kind}' must be a list" + (" with at least one entry" if kind == "files" else ""))
        return []
    out = []
    for n, item in enumerate(value, 1):
        if not (isinstance(item, dict) and set(item) == {"upstream_path", "local_path", "sha256"}
                and all(isinstance(v, str) for v in item.values())):
            problems.append(f"{kind} entry {n}: needs exactly upstream_path, local_path and sha256 (strings)")
            continue
        name = item["local_path"][len(LOCAL_PREFIX):] if item["local_path"].startswith(LOCAL_PREFIX) else ""
        pattern = MODULE_NAME if kind == "files" else DATA_NAME
        if not pattern.match(name) or name == MANIFEST or (kind != "files" and name.endswith(CODE_SUFFIXES)):
            problems.append(f"{kind} entry {n}: local_path must be a plain file name directly under {LOCAL_PREFIX}"
                            + (" ending in .py" if kind == "files" else " that is not a code file"))
        if not UPSTREAM_PATH.match(item["upstream_path"]) or ".." in item["upstream_path"].split("/") or (
                kind == "files" and not item["upstream_path"].endswith(".py")):
            problems.append(f"{kind} entry {n}: upstream_path must be a relative path inside the repository")
        if not SHA256.match(item["sha256"]):
            problems.append(f"{kind} entry {n}: sha256 must be 64 lower-case hexadecimal digits")
        out.append({**item, "name": name})
    return out


def parse_manifest(raw: bytes) -> dict:
    """The validated manifest; raises CoreCheckFailed (exit 2) naming every problem found."""
    try:
        data = json.loads(raw.decode("utf-8"))
    except (ValueError, RecursionError) as exc:
        raise _fail(2, [f"[term-core] MANIFEST {LOCAL_PREFIX}{MANIFEST}: not valid JSON ({type(exc).__name__})"]) from None
    problems: list[str] = []
    if not isinstance(data, dict) or set(data) != {"format", "upstream", "entry", "files", "data_files"}:
        raise _fail(2, [f"[term-core] MANIFEST {LOCAL_PREFIX}{MANIFEST}: needs exactly the keys format, upstream, "
                        "entry, files and data_files"])
    if data["format"] != FORMAT:
        problems.append(f"format must be {FORMAT}")
    up = data["upstream"]
    if not (isinstance(up, dict) and set(up) == {"repository", "tag", "commit"} and all(isinstance(v, str) for v in up.values())
            and REPOSITORY.match(up["repository"]) and TAG.match(up["tag"]) and SHA1.match(up["commit"])):
        problems.append("upstream must be {repository: owner/name, tag: vX.Y.Z, commit: 40 lower-case hex}")
    files, data_files = _entries(data["files"], "files", problems), _entries(data["data_files"], "data_files", problems)
    names = [f["name"] for f in files + data_files]
    if len(set(names)) != len(names) or len({f["upstream_path"] for f in files + data_files}) != len(names):
        problems.append("a local_path or an upstream_path is listed twice")
    if data["entry"] not in [f["name"][:-3] for f in files]:
        problems.append("entry must name one of the listed .py files, without .py")
    if problems:
        raise _fail(2, [f"[term-core] MANIFEST {LOCAL_PREFIX}{MANIFEST}: {p}" for p in problems])
    return {"upstream": up, "entry": data["entry"], "files": files, "data_files": data_files}


# ----------------------------------------------------------------------------- the check
def _unlisted(listed: set[str]) -> list[str]:
    """Code files anywhere under the directory that the manifest does not list (links included)."""
    found = []
    for base, dirs, files in os.walk(CORE_DIR, followlinks=False):
        rel_base = Path(base).relative_to(CORE_DIR).as_posix()
        for name in sorted(files + [d for d in dirs if (Path(base) / d).is_symlink()]):
            rel = name if rel_base == "." else f"{rel_base}/{name}"
            if name.endswith(CODE_SUFFIXES) and rel not in listed:
                found.append(rel)
        dirs.sort()
    return sorted(found)


def verify() -> tuple[dict, str, dict[str, bytes], list[str]]:
    """(manifest, manifest sha256, {name: verified bytes}, report lines). Raises CoreCheckFailed on any failure."""
    dfd = _open_dir(CORE_DIR)
    try:
        state, raw = _read(dfd, MANIFEST)
        if raw is None:
            raise _fail(2, [f"[term-core] MANIFEST {LOCAL_PREFIX}{MANIFEST}: "
                            + {"missing": "missing", "link": "a symbolic link (refused)"}.get(state, "not a regular file, or too large (refused)")])
        manifest = parse_manifest(raw)
        up = manifest["upstream"]
        lines, verified, bad = [], {}, {"mismatched": 0, "missing or refused": 0, "unlisted": 0}
        for f in manifest["files"] + manifest["data_files"]:
            path, origin = f["local_path"], f"agentteams {up['tag']} {f['upstream_path']}"
            state, data = _read(dfd, f["name"])
            if data is None:
                bad["missing or refused"] += 1
                why = {"missing": "missing", "link": "a symbolic link (refused)"}.get(state, "not a regular file, or too large (refused)")
                lines.append(f"[term-core] {state.upper()} {path}: {why} (expected sha256 {f['sha256'][:12]}, {origin})")
                continue
            digest = hashlib.sha256(data).hexdigest()
            if digest != f["sha256"]:
                bad["mismatched"] += 1
                lines.append(f"[term-core] MISMATCH {path}: sha256 {digest[:12]}, expected {f['sha256'][:12]} ({origin})")
                continue
            verified[f["name"]] = data
            lines.append(f"[term-core] OK {path}")
    finally:
        if dfd is not None:
            os.close(dfd)
    for rel in _unlisted({f["name"] for f in manifest["files"] + manifest["data_files"]}):
        bad["unlisted"] += 1
        lines.append(f"[term-core] UNLISTED {LOCAL_PREFIX}{rel}: a code file the manifest does not list")
    total = len(manifest["files"]) + len(manifest["data_files"])
    lines.append(f"[term-core] agentteams {up['tag']} ({up['commit'][:12]}): {len(verified)} of {total} files match; "
                 + ", ".join(f"{n} {k}" for k, n in bad.items()))
    if any(bad.values()):
        raise _fail(1, lines + ["[term-core] FAILED: the copied core is not the one the manifest names."])
    return manifest, hashlib.sha256(raw).hexdigest(), verified, lines


# ----------------------------------------------------------------------------- loading
class _CheckedSource:
    """The loader of a pinned module: it serves only the source that was checked, so a traceback shows what ran."""

    def __init__(self, data: bytes):
        self._data = data

    def get_source(self, fullname: str) -> str:
        return self._data.decode("utf-8")

    def is_package(self, fullname: str) -> bool:
        return False


_CACHE: dict[tuple[str, str], types.ModuleType] = {}
_LOCK = threading.Lock()


def _restricted_import(pinned: dict[str, types.ModuleType]):
    """An __import__ for the core's own builtins: agentteams.<x> is the pinned module, nothing else of agentteams."""
    real = builtins.__import__

    def __import__(name, globals=None, locals=None, fromlist=(), level=0):  # noqa: A002 (the builtin's signature)
        if level == 0 and (name == UPSTREAM_PACKAGE or name.startswith(UPSTREAM_PACKAGE + ".")):
            if name in pinned and fromlist:
                return pinned[name]
            raise ImportError(f"the pinned term-index core may not import {name} (only `from <pinned module> "
                              "import ...` of a file the manifest lists)")
        if level == 0 and name.partition(".")[0] not in sys.stdlib_module_names:
            raise ImportError(f"the pinned term-index core may import only the standard library, not {name}")
        return real(name, globals, locals, fromlist, level)
    return __import__


def _exec_all(manifest: dict, verified: dict[str, bytes]) -> types.ModuleType:
    had_agentteams = UPSTREAM_PACKAGE in sys.modules
    package = types.ModuleType(PACKAGE, "The pinned agentteams term-index core (scripts/term-index-core/).")
    package.__path__ = []  # a package that finds nothing on disk
    package.__package__ = PACKAGE
    package.__spec__ = importlib.machinery.ModuleSpec(PACKAGE, None, is_package=True)
    sys.modules[PACKAGE] = package
    pinned: dict[str, types.ModuleType] = {}       # upstream dotted name -> module
    own_builtins = dict(builtins.__dict__)
    own_builtins["__import__"] = _restricted_import(pinned)
    modules = {}
    for f in manifest["files"]:
        stem, path = f["name"][:-3], str(CORE_DIR / f["name"])
        fullname, data = f"{PACKAGE}.{stem}", verified[f["name"]]
        try:
            code = compile(data, path, "exec", dont_inherit=True)
        except (SyntaxError, ValueError) as exc:
            raise _fail(2, [f"[term-core] LOAD {f['local_path']}: does not compile here ({type(exc).__name__}: {exc})"]) from None
        loader = _CheckedSource(data)
        module = types.ModuleType(fullname)
        module.__dict__.update(__file__=path, __loader__=loader, __package__=PACKAGE, __builtins__=own_builtins,
                               __spec__=importlib.machinery.ModuleSpec(fullname, loader, origin=path))
        source = data.decode("utf-8")
        linecache.cache[path] = (len(source), None, source.splitlines(True), path)  # mtime None: never re-read
        sys.modules[fullname] = module
        try:
            exec(code, module.__dict__)
        except Exception as exc:
            sys.modules.pop(fullname, None)
            raise _fail(2, [f"[term-core] LOAD {f['local_path']}: failed to run ({type(exc).__name__}: {exc})"]) from None
        setattr(package, stem, module)
        modules[stem] = module
        pinned[f["upstream_path"][:-3].replace("/", ".")] = module
    entry = modules[manifest["entry"]]
    leaked = [n for n in dir(entry) if str(getattr(getattr(entry, n), "__module__", "")).partition(".")[0] == UPSTREAM_PACKAGE]
    if leaked or (UPSTREAM_PACKAGE in sys.modules and not had_agentteams):
        raise _fail(2, ["[term-core] LOAD: the core reached an installed agentteams instead of the pinned copy"])
    if "_term_text" in modules and getattr(entry, "Matcher", None) is not getattr(modules["_term_text"], "Matcher", None):
        raise _fail(2, ["[term-core] LOAD: term_index.Matcher is not the pinned _term_text.Matcher"])
    return entry


def load() -> types.ModuleType:
    """The verified, pinned entry module (term_index). Every call re-checks the bytes; a verified copy loads once."""
    with _LOCK:
        manifest, manifest_sha, verified, _ = verify()
        key = (os.path.realpath(CORE_DIR), manifest_sha)
        if key not in _CACHE:
            _CACHE[key] = _exec_all(manifest, verified)
        return _CACHE[key]


def main(argv: list[str]) -> int:
    if argv:
        print("usage: check_term_core.py", file=sys.stderr)
        return 2
    try:
        lines = verify()[3]
    except CoreCheckFailed as exc:
        print("\n".join(exc.lines))
        return exc.code
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
