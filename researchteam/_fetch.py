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


GITHUB_API_BASE = "https://api.github.com"
# Branches whose history is reviewed code: main and the maintained release lines.
REVIEWED_BRANCH_PREFIX = "release/"


def _api_get(path: str, timeout: int = 20):
    """GET ``{GITHUB_API_BASE}{path}`` as JSON; a ``GITHUB_TOKEN`` / ``GH_TOKEN`` in the environment is sent."""
    import json
    import os
    base = os.environ.get("RESEARCHTEAM_GITHUB_API") or GITHUB_API_BASE  # tests point this at a local fake
    req = urllib.request.Request(f"{base}{path}", headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def commit_is_reviewed(repo: str, sha: str) -> bool | None:
    """Whether ``sha`` is in the history of ``repo``'s ``main`` or a ``release/*`` branch.

    GitHub serves every commit in a repository's fork network under the parent's URLs, so a commit
    fetched as ``github.com/<repo>/archive/<sha>`` (or installed as ``git+https://github.com/<repo>@<sha>``)
    may exist only in a fork. Asks the compare API, ``<branch>...<sha>``: ``identical`` or ``behind`` means the
    commit is on that branch. Returns True when it is on one, False when GitHub answered for every branch
    and it is on none, and None when that cannot be determined (offline, rate-limited, unexpected reply).
    """
    if not _HEX_REF.match(sha):
        return False
    unknown = False

    def on(branch: str) -> bool:
        nonlocal unknown
        try:
            status = _api_get(f"/repos/{repo}/compare/{branch}...{sha}").get("status")
        except urllib.error.HTTPError as exc:
            unknown = unknown or exc.code not in (404, 422)  # 404/422: not in this network: a definite "no"
            return False
        except (OSError, ValueError, AttributeError):
            unknown = True
            return False
        if status not in ("identical", "behind", "ahead", "diverged"):
            unknown = True
        return status in ("identical", "behind")

    if on("main"):
        return True
    try:  # only when main says no: the release lines (a release tag's commit lives on release/X.Y)
        names = sorted(b["name"] for b in _api_get(f"/repos/{repo}/branches?per_page=100")
                       if isinstance(b, dict) and str(b.get("name", "")).startswith(REVIEWED_BRANCH_PREFIX))
    except (OSError, ValueError, TypeError, KeyError):
        return None
    if any(on(name) for name in names):
        return True
    return None if unknown else False
