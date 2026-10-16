"""Release-line pins: verify a signed release tag and find the newest one on a release line.

A repository is *release-locked* when its ``toolchain.lock`` records a tag beside a pin::

    agentteams=jlcatonjr/agentteams@<peeled 40-hex sha>
    agentteams.tag=v1.0.0-rc.10

The ``name=owner/repo@sha`` lines keep their old format, so older readers still parse the lock. A
release-locked pin only moves to a newer tag on the same ``vX.Y`` line, and only after that tag
verifies (shared release policy §2-§4):

1. it is an annotated tag;
2. ``git tag -v`` passes against the operator's ``allowed_signers`` under neutralised repository
   config;
3. the signing key's fingerprint is a release key named here, not just any "Good signature";
4. the verified tag object equals the one the remote advertises.

The pin is then the tag's peeled commit. Stdlib only; ``scripts/check_toolchain.py`` imports it.
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile

# Operator release keys (agentteams SECURITY.md "Release signers"), from v1.0.0-rc.9 onward.
RELEASE_KEY_FINGERPRINTS = frozenset({"SHA256:IPdnLwlFdHNhr7QGKVWU40BOKyYzv2u8qxP/qxnzTNM"})
# Lives outside every write root; agents may read it, never write it. An operator-run CI job may point
# AGENTTEAMS_ALLOWED_SIGNERS at a copy it provisions from a repository secret.
DEFAULT_ALLOWED_SIGNERS = os.path.join("~", ".config", "agentteams", "allowed_signers")
TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)(?:-rc\.(\d+))?$")
_SHA = re.compile(r"^[0-9a-f]{40}$")
# Never let a checkout-configured hook, monitor or signing program run while verifying.
_NEUTRAL = ["-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", "-c", "gpg.format=ssh",
            "-c", "gpg.ssh.program=ssh-keygen"]


class ReleaseError(RuntimeError):
    """A tag that is not a verified release, or a release line that cannot be read."""


def tag_key(tag: str) -> tuple[int, int, int, int, int]:
    """Sort key: patch order, and a final release after every RC of the same version."""
    m = TAG_RE.match(tag)
    if not m:
        raise ReleaseError(f"{tag!r} is not a release tag (vX.Y.Z or vX.Y.Z-rc.N)")
    major, minor, patch, rc = m.groups()
    return int(major), int(minor), int(patch), 0 if rc else 1, int(rc or 0)


def release_line(tag: str) -> str:
    """``v1.0`` for ``v1.0.3`` or ``v1.0.0-rc.10``."""
    major, minor = tag_key(tag)[:2]
    return f"v{major}.{minor}"


def allowed_signers_path() -> str:
    return os.path.expanduser(os.environ.get("AGENTTEAMS_ALLOWED_SIGNERS") or DEFAULT_ALLOWED_SIGNERS)


def _git(args: list[str], cwd: str | None = None, timeout: int = 60) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        return subprocess.run(["git", *_NEUTRAL, *args], cwd=cwd, capture_output=True, text=True,
                              timeout=timeout, env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReleaseError(f"git {args[0]} failed: {exc}") from exc


def remote_tags(repo: str) -> dict[str, str]:
    """{tag name: advertised tag object} for the release tags on ``https://github.com/<repo>``."""
    r = _git(["ls-remote", "--tags", f"https://github.com/{repo}", "refs/tags/v*"])
    if r.returncode != 0:
        raise ReleaseError(f"cannot list tags of {repo}: {r.stderr.strip() or r.returncode}")
    tags = {}
    for line in r.stdout.splitlines():
        obj, _, ref = line.partition("\t")
        name = ref.removeprefix("refs/tags/")
        if not name.endswith("^{}") and TAG_RE.match(name):
            tags[name] = obj
    return tags


def newest_on_line(repo: str, current: str) -> str | None:
    """The newest release tag on ``current``'s line that is newer than ``current``, else None."""
    line, floor = release_line(current), tag_key(current)
    newer = [t for t in remote_tags(repo) if release_line(t) == line and tag_key(t) > floor]
    return max(newer, key=tag_key) if newer else None


def verify_tag(repo: str, tag: str) -> tuple[str, str]:
    """(tag object, peeled commit) of a verified signed release tag; raises ReleaseError otherwise."""
    tag_key(tag)  # a release tag name, or raise
    signers = allowed_signers_path()
    if not os.path.isfile(signers):
        raise ReleaseError(f"no allowed_signers file at {signers}; the operator installs it "
                           "(see agentteams SECURITY.md \"Release signers\")")
    advertised = remote_tags(repo).get(tag)
    if not advertised:
        raise ReleaseError(f"{repo} does not advertise tag {tag}")
    with tempfile.TemporaryDirectory(prefix="rt-release-") as tmp:
        for args in (["init", "--bare", "-q", tmp],
                     ["-C", tmp, "fetch", "--no-tags", "-q", f"https://github.com/{repo}",
                      f"refs/tags/{tag}:refs/tags/{tag}"]):
            r = _git(args, timeout=300)
            if r.returncode != 0:
                raise ReleaseError(f"cannot fetch {repo} {tag}: {r.stderr.strip() or r.returncode}")
        obj = _git(["-C", tmp, "rev-parse", f"refs/tags/{tag}"]).stdout.strip()
        if _git(["-C", tmp, "cat-file", "-t", obj]).stdout.strip() != "tag":
            raise ReleaseError(f"{tag} is a lightweight tag; a release tag is annotated and signed")
        if obj != advertised:
            raise ReleaseError(f"{tag}: fetched tag object {obj[:12]} differs from advertised {advertised[:12]}")
        r = _git(["-c", f"gpg.ssh.allowedSignersFile={signers}", "-C", tmp, "tag", "-v", tag])
        out = r.stdout + r.stderr
        if r.returncode != 0 or 'Good "git" signature' not in out:
            raise ReleaseError(f"{tag}: signature does not verify against {signers}")
        if not any(fp in out for fp in RELEASE_KEY_FINGERPRINTS):
            raise ReleaseError(f"{tag}: signed by a key that is not a release key")
        peeled = _git(["-C", tmp, "rev-parse", f"refs/tags/{tag}^{{commit}}"]).stdout.strip()
    if not _SHA.match(peeled):
        raise ReleaseError(f"{tag}: cannot peel to a commit")
    return obj, peeled


def read_lock_pin(root, name: str) -> tuple[str, str, str | None] | None:
    """(owner/repo, sha, tag or None) for ``name`` in ``<root>/toolchain.lock``, or None."""
    path = os.path.join(str(root), "toolchain.lock")
    try:
        with open(path, encoding="utf-8") as f:
            lines = [ln.strip() for ln in f]
    except OSError:
        return None
    pin = tag = None
    for line in lines:
        if line.startswith(f"{name}=") and "@" in line:
            repo, _, sha = line.split("=", 1)[1].partition("@")
            pin = (repo.strip(), sha.strip())
        elif line.startswith(f"{name}.tag="):
            tag = line.split("=", 1)[1].strip()
    return (*pin, tag) if pin else None


def locked_layer2_ref(root, upstream_repo: str) -> tuple[str, str] | None:
    """(peeled sha, tag) to sync Layer 2 from when the lock release-locks researchteam, else None.

    Raises ReleaseError when the lock names a tag that does not verify, names another repository, or
    names a commit that is not the tag's peeled commit. The caller fails closed.
    """
    pin = read_lock_pin(root, "researchteam")
    if not pin or pin[2] is None:
        return None
    repo, sha, tag = pin
    if repo != upstream_repo:
        raise ReleaseError(f"toolchain.lock pins researchteam to {repo}, not {upstream_repo}")
    _, peeled = verify_tag(repo, tag)
    if peeled != sha:
        raise ReleaseError(f"toolchain.lock pins researchteam {sha[:7]}, but {tag} is {peeled[:7]}")
    return peeled, tag
