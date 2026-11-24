"""Compare the pinned term-index core with the signed agentteams tag its manifest names (network; opt-in).

The offline check (``scripts/check_term_core.py``) proves only that the copied files match
``scripts/term-index-core/PINNED.json``. Anyone who can merge can change a copy and its manifest together, so
this is the proof that the manifest matches upstream (design note ``open-1119-p1-copy-integrity-design``,
sections 5 and 10, point 8). It requires the signed tag; an installed agentteams proves nothing here, because a
copy taken from that install would match it by construction.

Steps, each failing closed:

1. the offline check passes;
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
import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

from . import _release


def _load_offline_check(root: Path):
    """The repository's own scripts/check_term_core.py, loaded by path (it is not part of this package)."""
    path = root / "scripts" / "check_term_core.py"
    spec = importlib.util.spec_from_file_location("_rt_check_term_core_for_upstream", path)
    if spec is None or spec.loader is None or not path.is_file():
        raise _release.ReleaseError(f"no offline check at {path.relative_to(root)}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    check = _load_offline_check(root)
    try:
        manifest, _, _, lines = check.verify()
    except check.CoreCheckFailed as exc:
        return exc.code, exc.lines
    up = manifest["upstream"]
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
