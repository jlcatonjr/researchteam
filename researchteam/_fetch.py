"""GitHub fetching utilities — stdlib only, no third-party dependencies."""

import urllib.request
import urllib.error

GITHUB_RAW_BASE = "https://raw.githubusercontent.com"
GITHUB_ARCHIVE_BASE = "https://github.com"


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
    """Download a branch/tag tarball from GitHub."""
    url = f"{GITHUB_ARCHIVE_BASE}/{repo}/archive/refs/heads/{ref}.tar.gz"
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            return resp.read()
    except urllib.error.HTTPError:
        # Fall back to tags archive if heads fails (e.g. when ref is a tag).
        url = f"{GITHUB_ARCHIVE_BASE}/{repo}/archive/refs/tags/{ref}.tar.gz"
        with urllib.request.urlopen(url, timeout=60) as resp:
            return resp.read()
