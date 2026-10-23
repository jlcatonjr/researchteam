# `_fetch` — ResearchTeam

GitHub fetching utilities, using only the standard library (`urllib.request`). `fetch_raw` reads one file from `raw.githubusercontent.com`; `fetch_tarball` downloads a branch, tag or commit archive from `github.com`. `update` uses `fetch_raw` for every layer-2 managed file, `doctor --drift` uses it for seeded-file comparison, and `init` uses `fetch_tarball` for the template.

> *Source: `researchteam/_fetch.py`*

> **Stability.** This module is underscore-prefixed. The supported interface is the `researchteam` CLI; these functions are documented for contributors and may change between releases.

---

## Constants

| Name | Value | Purpose |
|------|-------|---------|
| `GITHUB_RAW_BASE` | `"https://raw.githubusercontent.com"` | Base URL for single-file fetches. |
| `GITHUB_ARCHIVE_BASE` | `"https://github.com"` | Base URL for archive tarballs. |
| `_HEX_REF` | compiled regex `^[0-9a-f]{7,40}$` | A ref that may be a commit (short or full SHA); only such a ref gets the commit-archive candidate in `fetch_tarball`. |

---

## Functions

### `fetch_raw(repo: str, ref: str, path: str) -> str`

> *Source: `researchteam/_fetch.py`*

Fetch one file from `{GITHUB_RAW_BASE}/{repo}/{ref}/{path}` with a 20-second timeout and decode it as UTF-8.

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

An HTTP 404 moves on to the next candidate. Any other HTTP error, or a network error, stops at once without trying the remaining candidates.

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

## See Also

- [`index.md`](index.md) — API reference overview.
- [`init.md`](init.md) — uses `fetch_tarball`.
- [`update.md`](update.md) — uses `fetch_raw` for layer-2 sync.
- [`doctor.md`](doctor.md) — uses `fetch_raw` under `--drift`.
- [`manifest.md`](manifest.md) — `UPSTREAM_REPO` and the managed-file sets that are fetched.
- [`release.md`](release.md) — release-locked refs.
- [`../cli-reference.md`](../cli-reference.md) — command-line reference.
