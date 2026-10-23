# `_notes` — ResearchTeam

Upstream-authored Project-Specific Notes, synced into every agent surface. agentteams treats an agent's `## Project-Specific Notes` section as repo-owned and preserves it verbatim, so rules researchteam itself writes there (history, literature-library, news-perspective and so on) used to reach derived repos only by hand-copying. researchteam now keeps them in a fenced block at the top of each listed agent's Notes. The source of truth is the block in upstream researchteam's `.github/agents/<agent>.agent.md`; `researchteam update` writes it into the agent's file on every surface the repo carries: `.github/agents` (markdown), `.claude/agents` (markdown) and `.goose/recipes` (inside the recipe's indented `instructions:` block). Codex is projected from `.github` and follows automatically. Text outside the block is never touched, except that on first adoption hand-copied duplicates of the block's content are folded in. Expert blocks go only to experts whose component the repo's `brief.json` still defines, or to all experts when `brief.json` has no readable `components` list, and an agent can be excluded entirely through `brief.json`.

> *Source: `researchteam/_notes.py`*

> **Stability.** This module is underscore-prefixed. The supported interface is the `researchteam` CLI ([CLI reference](../cli-reference.md)); the functions below are documented for contributors and may change between releases.

All functions expect LF line endings (`Path.read_text` already translates CRLF). Files reached through a symlink that resolves outside the repository are refused.

---

## Constants

| Name | Value | Meaning |
|------|-------|---------|
| `NOTES_AGENTS` | `("interpretation-advisor", "topic-scoping-expert", "literature-review-expert", "main-analysis-expert")` | Agents that carry an upstream Notes block. |
| `BEGIN` | `` <!-- >>> researchteam:notes — upstream-authored; synced by `researchteam update`. Edit upstream. --> `` | Begin marker line written into files. |
| `END` | `<!-- <<< researchteam:notes -->` | End marker line written into files. |
| `BEGIN_CORE` | `">>> researchteam:notes"` | Substring that identifies a begin marker when reading. |
| `END_CORE` | `"<<< researchteam:notes"` | Substring that identifies an end marker when reading. |
| `NOTES_HEADING` | `"## Project-Specific Notes"` | The section heading the block lives under. |
| `EXPERT_SUFFIX` | `"-expert"` | agentteams names a component's expert `<component slug>-expert`. |

---

## File formats

### Notes block in an agent file

```markdown
## Project-Specific Notes

> ⚙️ **USER-EDITABLE** — ...

<!-- >>> researchteam:notes — upstream-authored; synced by `researchteam update`. Edit upstream. -->
### Historical setting (...)
...
<!-- <<< researchteam:notes -->

### A repo's own rule            <- outside the block: never touched
```

In a Goose recipe the same lines appear indented by two spaces inside `instructions:`.

### `brief.json` exclusion

A listed agent gets no block on any surface; its files are left exactly as they are:

```json
{
  "researchteam_notes": {"exclude": ["interpretation-advisor"]}
}
```

---

## Classes

### `NotesError`

Subclass of `ValueError`. A file or block that cannot be reconciled safely; the caller keeps the file as it is.

---

## Functions

### `component_slugs(root)`

The `components[].slug` set of the repo's `brief.json`. Components that are not objects or have no string `slug` are skipped.

**Args:**

- `root` (`Path`) — Repository root.

**Returns:** `set[str] | None` — `None` when `brief.json` cannot be read or parsed, or `components` is not a list.

---

### `agents_for(root)`

The `NOTES_AGENTS` whose block belongs in this repo: every non-expert, and each expert whose component slug (the agent name minus `-expert`) the brief defines. Without a readable brief or a `components` list, all of `NOTES_AGENTS` (`surfaces` still limits the sync to files that exist).

**Args:**

- `root` (`Path`) — Repository root.

**Returns:** `tuple[str, ...]`

---

### `excluded(root)`

Read `brief.json`'s `"researchteam_notes": {"exclude": [...]}`.

**Args:**

- `root` (`Path`) — Repository root.

**Returns:** `tuple[set[str] | None, list[str]]` — `(slugs, notes)`.

- An absent or unreadable brief, or no `researchteam_notes` key: `(set(), [])`.
- `researchteam_notes` present, non-null and not an object, or `exclude` not a list of strings: `(None, [message])`, so the caller can refuse to guess.
- Otherwise the listed slugs that are in `NOTES_AGENTS`; each other slug is dropped and produces a note `brief.json researchteam_notes.exclude: '<slug>' is not a researchteam notes agent; ignored`.

---

### `source_path(agent)`

Where the upstream block lives, and where a derived repo's copilot surface keeps it.

**Args:**

- `agent` (`str`) — Agent slug.

**Returns:** `str` — `".github/agents/<agent>.agent.md"`.

---

### `surfaces(root, agent)`

Every surface file of `agent` present in the repo, with the indent the block uses there. Candidates are `.github/agents/<agent>.agent.md` (indent `""`), `.claude/agents/<agent>.md` (indent `""`) and `.goose/recipes/<agent>.yaml` (indent `"  "`). A file is included only if it exists and `inside(root, path)` is true.

**Args:**

- `root` (`Path`) — Repository root.
- `agent` (`str`) — Agent slug.

**Returns:** `list[tuple[Path, str]]` — `(file, indent)` pairs.

---

### `inside(root, path)`

Whether `path`, with symlinks resolved, stays inside `root`. Used so nothing is written through a link that points out of the repository.

**Args:**

- `root` (`Path`) — Repository root.
- `path` (`Path`) — Candidate file.

**Returns:** `bool`

---

### `extract_block(text)`

The block's inner text, unindented, from an upstream `.github` agent file.

**Args:**

- `text` (`str`) — Agent file content.

**Returns:** `str | None` — The text between the markers with surrounding blank lines stripped and one trailing newline; `None` if the file has no Notes section or no block in it.

**Raises:**

- `NotesError` — If the block has no end marker before the next level-2 heading, or the block's content contains a level-2 heading (`## `, up to three leading spaces).

---

### `apply_block(text, inner, indent="")`

Put `inner` into `text`'s Notes block at `indent`. If a block already exists it is replaced. Otherwise (first adoption) the function removes outside-block units the block now carries — a `###` subsection whose heading matches one in `inner`, or a top-level bullet item (with its continuation lines) identical to one in `inner` — and then inserts the block after a blockquote that opens the section (such as the USER-EDITABLE note), else directly under the heading, adding blank lines around it as needed. Blank lines inside `inner` are written without indent. A missing final newline on `text` is added.

**Args:**

- `text` (`str`) — Target file content.
- `inner` (`str`) — Block content, as returned by `extract_block`.
- `indent` (`str`) — Indent of the Notes section in the file (`"  "` for Goose recipes).

**Returns:** `tuple[str, list[str]]` — `(new text, folded unit labels)`. Labels are the subsection heading text or the normalised bullet text; the list is empty when an existing block was replaced.

**Raises:**

- `NotesError` — If the file has no `## Project-Specific Notes` heading at `indent`, or an existing block has no end marker.

---

### Private helpers

| Name | Purpose |
|------|---------|
| `_notes_region(lines, indent)` | `(heading index, end index)` of the Notes section at `indent`. The section ends at the next level-2 heading or, in a Goose block scalar, at the first non-blank line that leaves the indent. Raises `NotesError` if there is no heading. |
| `_block_span(lines, start, end)` | Inclusive `(begin, end)` marker indices within the range, or `None`; raises `NotesError` when the end marker is missing. |
| `_units(lines, indent)` | Top-level units for duplicate folding: `("h:<heading>", start, end)` for `###` subsections and `("b:<normalised text>", start, end)` for bullet items. |

---

## See Also

- [`index`](index.md) — API reference overview.
- [`update`](update.md) — runs the Notes sync and decides when a customised file is skipped.
- [`drift`](drift.md) — `NOTES_HEADING_RE` and the comparable body above the Notes heading.
- [`frozen`](frozen.md) — frozen surfaces are not Notes-synced.
- [`manifest`](manifest.md) — which files researchteam syncs.
- [CLI reference](../cli-reference.md)
