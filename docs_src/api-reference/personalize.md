# `_personalize` — ResearchTeam

Renders the project-specific `README.md` and `CLAUDE.md` from `brief.json`, using the bundled scaffold templates `scaffold/README.template.md` and `scaffold/CLAUDE.template.md`. These two files are project identity, not framework infrastructure, so they are generated at `init` and re-rendered on demand by `researchteam personalize` rather than synced from upstream.

Two safety rules apply:

- **The upstream repository is never personalized.** If the `.researchteam` marker declares `is_upstream = true`, `run_personalize` exits.
- **Hand-edited files are not overwritten silently.** Each generated file (for `CLAUDE.md`, its project header above the managed fence) ends with a `researchteam:generated` marker line holding a SHA-256 of the generated body. On re-render, a region whose body still matches its marker is refreshed; a region that diverged, or has no marker, is skipped unless `force` is set.

> *Source: `researchteam/_personalize.py`*

> **Stability.** This module is underscore-prefixed. The supported interface is the `researchteam` CLI ([CLI reference](../cli-reference.md)); the functions below are documented for contributors and may change between releases.

---

## Constants

| Name | Value | Purpose |
|------|-------|---------|
| `GEN_MARKER_PREFIX` | `"<!-- researchteam:generated sha256="` | Prefix of the generation marker line. |
| `_SHA_RE` | `re.compile(r"sha256=([0-9a-f]{64})")` | Extracts the digest from a marker line. |

The module also imports `FENCE_CORE_BEGIN`, `FENCE_CORE_END` and `INIT_RENDER_TEMPLATES` from [`_manifest`](manifest.md).

### Template tokens

`_render` substitutes these tokens from `brief.json`. Scalar fields are converted with `str()` and stripped; a missing field or an empty (or whitespace-only) string uses the fallback (a JSON `null` renders as `None`). `deliverables` uses its fallback unless it is a non-empty list, and its items are not stripped.

| Token | `brief.json` field | Fallback |
|-------|--------------------|----------|
| `{{PROJECT_NAME}}` | `project_name` | `Untitled Project` |
| `{{PROJECT_GOAL}}` | `project_goal` | `_(describe this project's goal in brief.json)_` |
| `{{OUTPUT_FORMAT}}` | `output_format` | `Markdown` |
| `{{PRIMARY_OUTPUT_DIR}}` | `primary_output_dir` | `reports/` |
| `{{DELIVERABLES}}` | `deliverables` (non-empty list, one `- item` line each) | `` - _(define `deliverables` in brief.json)_ `` |

---

## Functions

### `run_personalize(root: Path, force: bool = False, quiet: bool = False) -> list[str]`

> *Source: `researchteam/_personalize.py`*

Render every entry of `INIT_RENDER_TEMPLATES` (`README.md` from `README.template.md`, `CLAUDE.md` from `CLAUDE.template.md`) into `root`. The CLI calls it as `run_personalize(root, force=args.force, quiet=False)`; `init` calls it with `force=True`.

**Args:**

- `root` (`Path`) — Repository root.
- `force` (`bool`) — Overwrite generated regions even when they diverged from their marker or have no marker.
- `quiet` (`bool`) — Suppress the "Personalized …" and "Skipped …" messages.

**Returns:** `list[str]` — Repository-relative paths that were written (a subset of `["README.md", "CLAUDE.md"]`).

**Exit behaviour (`sys.exit` with a message):**

- `.researchteam` declares `is_upstream = true`.
- `brief.json` does not exist.
- `brief.json` cannot be read or is not valid JSON.

**Write rules (from `_write_generated`):**

| File kind | Existing file | Result |
|-----------|---------------|--------|
| Unfenced (`README.md`) | absent | Written: rendered body plus marker. |
| Unfenced | marker matches | Rewritten. |
| Unfenced | diverged or no marker | Skipped, unless `force`. |
| Fenced (`CLAUDE.md`) | absent | Written: header plus marker, then the template's managed block and trailing text. |
| Fenced | has fence, header marker matches | Header regenerated; the existing managed block and everything after it are kept (owned by `researchteam update`). |
| Fenced | has fence, header diverged or no marker | Skipped, unless `force`; with `force`, the header is regenerated and the existing managed block is still kept. |
| Fenced | fence missing | Treated as hand-authored: skipped, unless `force`; with `force`, the whole file is rewritten from the template. |

A skip prints `[researchteam] Skipped <file>: its <project header|file> <was hand-authored (no generation marker)|has been edited since it was generated>. Re-run with --force …` to stderr.

**Example:**

```python
from pathlib import Path
from researchteam._personalize import run_personalize

written = run_personalize(Path("."), force=False)
```

---

### `read_marker(root: Path) -> dict[str, str]`

> *Source: `researchteam/_personalize.py`*

Parse `root/.researchteam` into a flat `key → value` dict. It is the one reader of the marker's `ref`, `layer1` and `is_upstream` keys (used by `cli`, `_update_cmd` and `_drift` as well as this module). Each line is stripped; lines containing `=` that do not start with `[` or `#` are split at the first `=`. Then, for the value:

1. a trailing comment — whitespace followed by `#` and everything after it — is dropped;
2. the value is stripped;
3. one pair of matching surrounding quotes (`"…"` or `'…'`) is removed.

Keys are stripped. The first occurrence of a key wins; later duplicates are ignored. Section headers are ignored, so keys from all sections share one namespace.

```ini
[researchteam]
ref = "v1.0.2"   # read as v1.0.2
is_upstream = 'true'
```

**Returns:** `dict[str, str]` — Empty when the marker does not exist.

**Raises:** `OSError` — when the marker exists but cannot be read.

---

### `is_upstream(root: Path) -> bool`

> *Source: `researchteam/_personalize.py`*

True when `read_marker(root)["is_upstream"]`, lower-cased, equals `"true"`. Because `read_marker` strips quotes and trailing comments, `is_upstream = "true"` and `is_upstream = true  # framework repo` both count as true. A missing key or any other value returns `False`.

---

### `_generation_status(region: str) -> bool | None`

> *Source: `researchteam/_personalize.py`*

Classify a file or header region. Finds the first line containing `GEN_MARKER_PREFIX`, removes every marker line from the region, and compares the SHA-256 of the remainder with the digest in the marker.

**Returns:** `True` — untouched generated region; `False` — edited since generation; `None` — no marker line, or a marker without a 64-hex digest (treated as hand-authored).

---

### Private helpers

| Function | Behaviour |
|----------|-----------|
| `_render(template: str, brief: dict) -> str` | Replaces the template tokens listed above. |
| `_marker_line(body: str) -> str` | Returns `` <!-- researchteam:generated sha256=<digest> — regenerate with `researchteam personalize`; edits to generated regions are overwritten --> `` plus newline, where `<digest>` is SHA-256 of `body`. |
| `_wrap(body: str) -> str` | Ensures `body` ends with a newline, then appends `_marker_line(body)`. |
| `_split_fence(text: str) -> Optional[tuple[str, str, str]]` | Splits into `(before, fenced block including both marker lines, after)` using the first line containing `FENCE_CORE_BEGIN` and the next line containing `FENCE_CORE_END`; `None` if either is missing. |
| `_load_template(name: str) -> str` | Reads `researchteam/scaffold/<name>` from the installed package. |
| `_write_generated(dest, dest_rel, rendered, *, force, quiet) -> bool` | Applies the write rules above; returns `True` if the file was written. |
| `_skip(dest_rel, status, quiet, *, header_only) -> None` | Prints the skip message to stderr unless `quiet`. |

---

## See Also

- [`index.md`](index.md) — API reference overview.
- [`cli.md`](cli.md) — dispatches `researchteam personalize`.
- [`init.md`](init.md) — calls `run_personalize(..., force=True)`.
- [`update.md`](update.md) — owns the `CLAUDE.md` managed block.
- [`manifest.md`](manifest.md) — `INIT_RENDER_TEMPLATES` and the fence markers.
- [`notes.md`](notes.md) — upstream-authored Project-Specific Notes.
- [`../cli-reference.md`](../cli-reference.md) — command-line reference.
