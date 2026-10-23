"""GitHub fetching utilities — stdlib only, no third-party dependencies."""

import re
import urllib.error
import urllib.request

GITHUB_RAW_BASE = "https://raw.githubusercontent.com"
GITHUB_ARCHIVE_BASE = "https://github.com"
_HEX_REF = re.compile(r"^[0-9a-f]{7,40}$")


def fetch_raw(repo: str, ref: str, path: str) -> str:
    """Fetch a single file from GitHub raw content delivery."""
    url = f"{GITHUB_RAW_BASE}/{repo}/{ref}/{path}"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"Failed to fetch '{path}' from {repo}@{ref}: HTTP {exc.code}"
        ) from exc
    except OSError as exc:
        raise RuntimeError(
            f"Network error fetching '{path}' from {repo}@{ref}: {exc}"
        ) from exc


def fetch_tarball(repo: str, ref: str) -> bytes:
    """Download a branch, tag or commit tarball from GitHub.

    Tries ``refs/heads/<ref>``, then ``refs/tags/<ref>``, then (only for a 7-40 hex ``ref``) the commit archive
    ``archive/<ref>.tar.gz``. A 404 moves to the next candidate; any other HTTP error or a network error stops at
    once. Every failure is a ``RuntimeError``, as in :func:`fetch_raw`.
    """
    candidates = [
        f"{GITHUB_ARCHIVE_BASE}/{repo}/archive/refs/heads/{ref}.tar.gz",
        f"{GITHUB_ARCHIVE_BASE}/{repo}/archive/refs/tags/{ref}.tar.gz",
    ]
    if _HEX_REF.match(ref):
        candidates.append(f"{GITHUB_ARCHIVE_BASE}/{repo}/archive/{ref}.tar.gz")
    for url in candidates:
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise RuntimeError(f"Failed to fetch the {repo}@{ref} archive: HTTP {exc.code}") from exc
        except OSError as exc:
            raise RuntimeError(f"Network error fetching the {repo}@{ref} archive: {exc}") from exc
    kinds = "branch, tag or commit" if _HEX_REF.match(ref) else "branch or tag"
    raise RuntimeError(f"No {kinds} '{ref}' in {repo} (HTTP 404)")
