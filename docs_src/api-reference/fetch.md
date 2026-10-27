# `_fetch` — ResearchTeam

GitHub fetching utilities, using only the standard library (`urllib.request`). `fetch_raw` reads one file from `raw.githubusercontent.com`; `fetch_tarball` downloads a branch, tag or commit archive from `github.com`. `update` uses `fetch_raw` for every layer-2 managed file, and `init` uses `fetch_tarball` for the template. `doctor --drift` would use `fetch_raw` for seeded-file comparison, but `SEEDED_FILES` is currently empty, so it makes no request.

> *Source: `researchteam/_fetch.py`*

> **Stability.** This module is underscore-prefixed. The supported interface is the `researchteam` CLI ([CLI reference](../cli-reference.md)); the functions below are documented for contributors and may change between releases.

---

## Constants

| Name | Value | Purpose |
|------|-------|---------|
| `GITHUB_RAW_BASE` | `"https://raw.githubusercontent.com"` | Base URL for single-file fetches. |
| `GITHUB_ARCHIVE_BASE` | `"https://github.com"` | Base URL for archive tarballs. |
| `_HEX_REF` | compiled regex `^[0-9a-f]{7,40}$` | A ref that may be a commit (short or full SHA); only such a ref gets the commit-archive candidate in `fetch_tarball`. |
| `GITHUB_API_BASE` | `"https://api.github.com"` | Base URL for `commit_is_reviewed`; the `RESEARCHTEAM_GITHUB_API` environment variable overrides it (the tests point it at a local fake). |
| `REVIEWED_BRANCH_PREFIX` | `"release/"` | Branches whose history counts as reviewed, besides `main`. |
| `FETCH_ATTEMPTS` | `2` | Attempts per URL in `fetch_raw` and `fetch_tarball`: a `URLError` (other than `HTTPError`) or a timeout is retried once. |
| `FETCH_BACKOFF_SECONDS` | `1.5` | Pause before that retry. An HTTP answer (4xx or 5xx) is final and never retried. |

---

## Functions

### `fetch_raw(repo: str, ref: str, path: str) -> str`

> *Source: `researchteam/_fetch.py`*

Fetch one file from `{GITHUB_RAW_BASE}/{repo}/{ref}/{path}` with a 20-second timeout and decode it as UTF-8. A `URLError` or timeout is retried once after `FETCH_BACKOFF_SECONDS`; an HTTP error is not.

**Args:**

- `repo` (`str`) — `owner/name`, for example `UPSTREAM_REPO` (`"jlcatonjr/researchteam"`).
- `ref` (`str`) — Branch, tag, or commit.
- `path` (`str`) — Repository-relative file path.

**Returns:** `str` — The file contents.

**Raises:**

- `RuntimeError` — `"Failed to fetch '<path>' from <repo>@<ref>: HTTP <code>"` on an HTTP error, or `"Network error fetching '<path>' from <repo>@<ref>: <exc>"` on any other `OSError` (including `URLError` and timeouts). The original exception is chained.

**Example:**

```python
from researchteam._fetch import fetch_raw
from researchteam._manifest import UPSTREAM_REPO

text = fetch_raw(UPSTREAM_REPO, "main", "docs/researchteam-framework.md")
```

---

### `fetch_tarball(repo: str, ref: str) -> bytes`

> *Source: `researchteam/_fetch.py`*

Download a gzip archive of `ref`, trying these URLs in order, each with a 60-second timeout:

1. `{GITHUB_ARCHIVE_BASE}/{repo}/archive/refs/heads/{ref}.tar.gz` (branch)
2. `{GITHUB_ARCHIVE_BASE}/{repo}/archive/refs/tags/{ref}.tar.gz` (tag)
3. `{GITHUB_ARCHIVE_BASE}/{repo}/archive/{ref}.tar.gz` (commit) — only when `ref` matches `_HEX_REF` (7–40 lower-case hex characters).

An HTTP 404 moves on to the next candidate. Any other HTTP error, or a network error that persists after one retry (`URLError` or timeout only, after `FETCH_BACKOFF_SECONDS`), stops at once without trying the remaining candidates.

**Args:**

- `repo` (`str`) — `owner/name`.
- `ref` (`str`) — Branch name, tag name, or commit SHA (short or full).

**Returns:** `bytes` — The raw `.tar.gz` content.

**Raises:**

- `RuntimeError` — every failure, as in `fetch_raw`, with the original exception chained:
    - `"Failed to fetch the <repo>@<ref> archive: HTTP <code>"` on a non-404 HTTP error;
    - `"Network error fetching the <repo>@<ref> archive: <exc>"` on any other `OSError` (including `URLError` and timeouts);
    - `"No branch, tag or commit '<ref>' in <repo> (HTTP 404)"` (or `"No branch or tag ..."` for a non-hex `ref`) when every candidate returns 404.

---

### `commit_is_reviewed(repo: str, sha: str) -> bool | None`

Whether `sha` is in the history of `repo`'s `main` or a `release/*` branch. GitHub serves every commit in a
repository's fork network under the parent's URLs, so a commit fetched as `github.com/<repo>/archive/<sha>` or
installed as `git+https://github.com/<repo>@<sha>` may exist only in a fork. `init`, `update` and the agentteams
provenance guard use this to tell reviewed commits from fork commits.

It asks the compare API for `main...<sha>`. A status of `identical` or `behind` means the commit is on that branch.
Only when `main` says no does it list the repository's branches and ask the same of each `release/*` branch, where a
release tag's commit lives. A `GITHUB_TOKEN` or `GH_TOKEN` in the environment is sent, which raises GitHub's limit of
60 unauthenticated requests an hour.

**Args:**

- `repo` (`str`) — `owner/name`.
- `sha` (`str`) — A 7–40 hex commit; anything else returns `False`.

**Returns:** `True` when the commit is on `main` or a `release/*` branch; `False` when GitHub answered for every
branch and it is on none (including a commit unknown to the network: HTTP 404/422); `None` when that cannot be
determined (offline, rate-limited, an unexpected reply).

Callers treat `None` differently: `init` refuses, while `update` and the provenance guard warn and continue.

---

## See Also

- [`index.md`](index.md) — API reference overview.
- [`init.md`](init.md) — uses `fetch_tarball`.
- [`update.md`](update.md) — uses `fetch_raw` for layer-2 sync.
- [`doctor.md`](doctor.md) — uses `fetch_raw` under `--drift`.
- [`manifest.md`](manifest.md) — `UPSTREAM_REPO` and the managed-file sets that are fetched.
- [`release.md`](release.md) — release-locked refs.
- [`../cli-reference.md`](../cli-reference.md) — command-line reference.
