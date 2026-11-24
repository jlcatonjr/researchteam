"""Compare the pinned term-index core with the signed agentteams tag its manifest names (network; opt-in).

The offline check (``scripts/check_term_core.py``) proves only that the copied files match
``scripts/term-index-core/PINNED.json``. Anyone who can merge can change a copy and its manifest together, so
this is the proof that the manifest matches upstream (design note ``open-1119-p1-copy-integrity-design``,
sections 5 and 10, point 8). It requires the signed tag; an installed agentteams proves nothing here, because a
copy taken from that install would match it by construction.

Steps, each failing closed:

1. the copy matches PINNED.json, checked by this module itself (not by the repository's
   ``scripts/check_term_core.py``, whose own bytes this cannot vouch for);
2. the manifest's tag verifies as a signed release tag (``_release.verify_tag``) and peels to the manifest's commit;
3. the tag, fetched again with its tree, is the same tag object and peels to the same commit;
4. every listed file, read from that commit with ``git cat-file blob``, has the manifest's sha256;
5. the manifest's commit is the agentteams commit ``toolchain.lock`` pins (the rule at every researchteam
   release, section 10, point 3); ``--allow-lock-difference`` reports a difference instead of failing.

Usage: ``python -m researchteam._term_core_upstream [--root PATH] [--allow-lock-difference]``.
Exit codes: 0 every check passed | 1 a hash, commit or lock mismatch | 2 cannot verify (network, no
allowed_signers, malformed manifest). Not a CI gate on its own: a workflow job runs it on every pull request
that touches ``scripts/term-index-core/`` (a separate change under ``.github/workflows/``).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

from . import _release


CORE_PREFIX = "scripts/term-index-core/"
MANIFEST_REL = CORE_PREFIX + "PINNED.json"
FORMAT = "researchteam-pinned-copy/1"
CODE_SUFFIXES = (".py", ".pyc", ".pyo", ".pyw", ".pyd", ".so", ".pth")
_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9._-]*$")
_UPSTREAM_PATH = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9._-]*(/[A-Za-z0-9_][A-Za-z0-9._-]*)*$")
_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_TAG = re.compile(r"^v\d+\.\d+\.\d+(-rc\.\d+)?$")
_SHA1, _SHA256 = re.compile(r"^[0-9a-f]{40}$"), re.compile(r"^[0-9a-f]{64}$")

# Independence: this module (the network comparison) and the update's post-sync check parse PINNED.json and hash
# the copied files here, in the installed researchteam package. They never call the repository's own
# scripts/check_term_core.py, so a changed check script cannot hand them a genuine manifest while other bytes sit
# in the directory. The few lines that compare a sha256 with a manifest entry are therefore duplicated from
# check_term_core.digest_mismatch on purpose.


def sha256_mismatch(entry: dict, data: bytes) -> str | None:
    """None when ``data`` has the sha256 the manifest entry records; otherwise the sha256 it has."""
    digest = hashlib.sha256(data).hexdigest()
    return None if digest == entry["sha256"] else digest


def parse_pinned(raw: bytes) -> dict:
    """The validated PINNED.json; raises ValueError naming the first problem found."""
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict) or set(data) != {"format", "upstream", "entry", "files", "data_files"}:
        raise ValueError("needs exactly the keys format, upstream, entry, files and data_files")
    if data["format"] != FORMAT:
        raise ValueError(f"format must be {FORMAT}")
    up = data["upstream"]
    if not (isinstance(up, dict) and set(up) == {"repository", "tag", "commit"} and all(isinstance(v, str) for v in up.values())
            and _REPOSITORY.match(up["repository"]) and _TAG.match(up["tag"]) and _SHA1.match(up["commit"])):
        raise ValueError("upstream must be {repository: owner/name, tag: vX.Y.Z, commit: 40 lower-case hex}")
    seen = set()
    for kind in ("files", "data_files"):
        if not isinstance(data[kind], list) or (kind == "files" and not data[kind]):
            raise ValueError(f"'{kind}' must be a list")
        for item in data[kind]:
            if not (isinstance(item, dict) and set(item) == {"upstream_path", "local_path", "sha256"}
                    and all(isinstance(v, str) for v in item.values())):
                raise ValueError(f"a {kind} entry needs exactly upstream_path, local_path and sha256 (strings)")
            name = item["local_path"].removeprefix(CORE_PREFIX)
            right_kind = name.endswith(".py") if kind == "files" else not name.endswith(CODE_SUFFIXES)
            if (not item["local_path"].startswith(CORE_PREFIX) or not _NAME.match(name) or name == "PINNED.json"
                    or not right_kind):
                raise ValueError(f"{item['local_path']!r} is not a plain file name directly under {CORE_PREFIX}")
            if not _UPSTREAM_PATH.match(item["upstream_path"]) or ".." in item["upstream_path"].split("/"):
                raise ValueError(f"{item['upstream_path']!r} is not a relative path inside the repository")
            if not _SHA256.match(item["sha256"]):
                raise ValueError(f"{item['local_path']}: sha256 must be 64 lower-case hexadecimal digits")
            if name in seen:
                raise ValueError(f"{item['local_path']} is listed twice")
            seen.add(name)
    if data["entry"] not in [f["local_path"].removeprefix(CORE_PREFIX)[:-3] for f in data["files"]]:
        raise ValueError("entry must name one of the listed .py files, without .py")
    return data


#: The only repository the copied core may come from (compared case-insensitively, as GitHub does).
UPSTREAM_REPOSITORY = "jlcatonjr/agentteams"


def link_on_path(root: Path, rel: str) -> bool:
    """Whether any component of ``root/rel`` below ``root`` is a symbolic link, or its parent resolves outside ``root``."""
    here = root
    for part in Path(rel).parts:
        here = here / part
        if here.is_symlink():
            return True
    real_root = os.path.realpath(root)
    return os.path.commonpath([real_root, os.path.realpath(here.parent)]) != real_root


def _read_regular(root: Path, rel: str) -> bytes | None:
    """The bytes of ``root/rel`` when it exists and no component is a link; None otherwise."""
    if link_on_path(root, rel) or not (root / rel).is_file():
        return None
    return (root / rel).read_bytes()


def local_mismatches(root: Path) -> tuple[dict | None, list[str]]:
    """(manifest or None, problem lines) for the copy at ``root``, checked without the repository's check script.

    A problem is an unreadable or malformed PINNED.json, a listed file that is missing, reached through a link
    or hashes differently, or a code file in the directory that the manifest does not list.
    """
    raw = _read_regular(root, MANIFEST_REL)
    if raw is None:
        return None, [f"[term-core-upstream] MANIFEST {MANIFEST_REL}: missing, or reached through a link"]
    try:
        manifest = parse_pinned(raw)
    except (ValueError, RecursionError) as exc:
        return None, [f"[term-core-upstream] MANIFEST {MANIFEST_REL}: {exc}"]
    out, listed = [], set()
    for f in manifest["files"] + manifest["data_files"]:
        listed.add(f["local_path"])
        data = _read_regular(root, f["local_path"])
        if data is None:
            out.append(f"[term-core-upstream] MISSING {f['local_path']} (or reached through a link)")
        elif (digest := sha256_mismatch(f, data)) is not None:
            out.append(f"[term-core-upstream] MISMATCH {f['local_path']}: sha256 {digest[:12]}, manifest {f['sha256'][:12]}")
    core = root / CORE_PREFIX
    for path in sorted(core.rglob("*")) if core.is_dir() and not link_on_path(root, CORE_PREFIX.rstrip("/")) else []:
        rel = path.relative_to(root).as_posix()
        if path.name.endswith(CODE_SUFFIXES) and rel not in listed:
            out.append(f"[term-core-upstream] UNLISTED {rel}: a code file the manifest does not list")
    return manifest, out


def blob_mismatches(manifest: dict, read_blob: Callable[[str], bytes | None]) -> list[str]:
    """Report lines for every listed file whose upstream blob is absent or hashes differently.

    ``read_blob(upstream_path)`` returns the file's bytes at the pinned commit, or None when it is absent.
    """
    out = []
    for f in manifest["files"] + manifest["data_files"]:
        data = read_blob(f["upstream_path"])
        if data is None:
            out.append(f"[term-core-upstream] ABSENT {f['upstream_path']} at {manifest['upstream']['commit'][:12]}")
            continue
        digest = hashlib.sha256(data).hexdigest()
        if digest != f["sha256"]:
            out.append(f"[term-core-upstream] MISMATCH {f['upstream_path']}: upstream sha256 {digest[:12]}, "
                       f"manifest {f['sha256'][:12]}")
    return out


def _git_bytes(args: list[str], cwd: str, timeout: int = 300) -> subprocess.CompletedProcess:
    """git with the neutral configuration ``_release`` uses, returning raw bytes (blobs are not text)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_TERMINAL_PROMPT="0", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    try:
        return subprocess.run(["git", *_release._NEUTRAL, *args], cwd=cwd, capture_output=True, timeout=timeout,
                              env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise _release.ReleaseError(f"git {args[0]} failed: {exc}") from exc


def _fetch_tree_reader(repo: str, tag: str, tag_object: str, commit: str, tmp: str) -> Callable[[str], bytes | None]:
    """Fetch ``tag`` with its tree into ``tmp`` and return a reader of blobs at ``commit``."""
    for args in (["init", "--bare", "-q", tmp],
                 ["-C", tmp, "fetch", "--no-tags", "-q", "--depth=1", f"https://github.com/{repo}",
                  f"refs/tags/{tag}:refs/tags/{tag}"]):
        r = _git_bytes(args, cwd=tmp)
        if r.returncode != 0:
            raise _release.ReleaseError(f"git {args[0] if args[0] != '-C' else args[2]} failed for {repo} {tag}: "
                                        f"{r.stderr.decode('utf-8', 'replace').strip() or r.returncode}")
    obj = _git_bytes(["-C", tmp, "rev-parse", f"refs/tags/{tag}"], cwd=tmp).stdout.decode().strip()
    peeled = _git_bytes(["-C", tmp, "rev-parse", f"refs/tags/{tag}^{{commit}}"], cwd=tmp).stdout.decode().strip()
    if obj != tag_object or peeled != commit:
        raise _release.ReleaseError(f"{tag} fetched with its tree is {obj[:12]} -> {peeled[:12]}, not the verified "
                                    f"{tag_object[:12]} -> {commit[:12]}")

    def read(upstream_path: str) -> bytes | None:
        r = _git_bytes(["-C", tmp, "cat-file", "blob", f"{commit}:{upstream_path}"], cwd=tmp, timeout=60)
        return r.stdout if r.returncode == 0 else None
    return read


def compare(root: Path, *, allow_lock_difference: bool = False) -> tuple[int, list[str]]:
    """(exit code, report lines) for the comparison of the copy at ``root`` with its signed upstream tag."""
    manifest, problems = local_mismatches(root)
    if manifest is None:
        return 2, problems
    if problems:
        return 1, problems
    up = manifest["upstream"]
    lines = [f"[term-core-upstream] the copy matches {MANIFEST_REL} (checked here, not by scripts/check_term_core.py)"]
    # The release key signs tags in more than one repository. The core may only come from agentteams' own, and
    # from the repository the lock pins: a manifest and a lock repointed together must not verify.
    if up["repository"].lower() != UPSTREAM_REPOSITORY:
        return 1, lines + [f"[term-core-upstream] REPOSITORY the manifest names {up['repository']}; the core may only "
                           f"come from {UPSTREAM_REPOSITORY}"]
    lock_now = _release.read_lock_pin(root, "agentteams")
    if lock_now is not None and lock_now[0].lower() != UPSTREAM_REPOSITORY:
        return 1, lines + [f"[term-core-upstream] REPOSITORY toolchain.lock pins agentteams from {lock_now[0]}, not "
                           f"{UPSTREAM_REPOSITORY}"]
    try:
        tag_object, peeled = _release.verify_tag(up["repository"], up["tag"])
    except _release.ReleaseError as exc:
        return 2, lines + [f"[term-core-upstream] CANNOT VERIFY {up['repository']} {up['tag']}: {exc}"]
    if peeled != up["commit"]:
        return 1, lines + [f"[term-core-upstream] COMMIT {up['tag']} peels to {peeled[:12]}, the manifest names "
                           f"{up['commit'][:12]}"]
    lines.append(f"[term-core-upstream] {up['repository']} {up['tag']} verifies (tag object {tag_object[:12]}) "
                 f"and peels to {peeled[:12]}")
    with tempfile.TemporaryDirectory(prefix="rt-term-core-") as tmp:
        try:
            reader = _fetch_tree_reader(up["repository"], up["tag"], tag_object, peeled, tmp)
        except _release.ReleaseError as exc:
            return 2, lines + [f"[term-core-upstream] CANNOT VERIFY: {exc}"]
        bad = blob_mismatches(manifest, reader)
    if bad:
        return 1, lines + bad
    lines.append(f"[term-core-upstream] every listed file equals agentteams {up['tag']} at {peeled[:12]}")
    lock = _release.read_lock_pin(root, "agentteams")
    if lock is None or lock[1] != up["commit"]:
        named = f"{lock[1][:12]}" if lock else "no agentteams pin"
        line = (f"[term-core-upstream] LOCK toolchain.lock pins {named}; the core is pinned to {up['commit'][:12]} "
                "(at a researchteam release they must be equal)")
        if not allow_lock_difference:
            return 1, lines + [line]
        lines.append(line + " (reported, not failed: --allow-lock-difference)")
    else:
        lines.append("[term-core-upstream] the core's commit is the agentteams commit toolchain.lock pins")
    return 0, lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m researchteam._term_core_upstream", description=__doc__.split("\n")[0])
    parser.add_argument("--root", default=".", help="the repository root (default: the current directory)")
    parser.add_argument("--allow-lock-difference", action="store_true",
                        help="report, without failing, a core commit that differs from toolchain.lock's agentteams pin")
    args = parser.parse_args(argv)
    code, lines = compare(Path(args.root).resolve(), allow_lock_difference=args.allow_lock_difference)
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main())
