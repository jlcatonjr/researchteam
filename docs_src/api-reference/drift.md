# `_drift` — ResearchTeam

Drift reporting: what `researchteam update` would otherwise leave behind without saying so. The module covers three kinds of drift. **Frozen fences:** `update` pins `--shrink-policy preserve`, so when a template rewords text the shrink guard reads the change as lost enrichment and keeps the old body. agentteams writes a review report of every section it kept when `AGENTTEAMS_SHRINK_REPORT` is set; `update` sets it on every non-dry-run render (under the gitignored `tmp/`), prints the count, and `doctor` lists the sections with how long each has been frozen. **Seeded files behind upstream** (`doctor --drift`): files `init` seeds but `update` never syncs, compared with upstream at the pinned researchteam commit. **Stale bridges** (`doctor --drift`): `agentteams --bridge-check` per bridge. This module holds the shared helpers; the commands themselves live in `update` and `doctor`.

> *Source: `researchteam/_drift.py`*

> **Stability.** This module is underscore-prefixed. The supported interface is the `researchteam` CLI ([CLI reference](../cli-reference.md)); the functions below are documented for contributors and may change between releases.

---

## Constants

| Name | Value | Meaning |
|------|-------|---------|
| `REPORT_STEM` | `"agentteams-shrink-report"` | File stem of the shrink review report agentteams writes. |
| `STATE_FILE` | `"tmp/frozen-fences.state.json"` | Gitignored first-seen state for frozen sections. |
| `INTENTIONAL_FILE` | `".github/agents/references/intentional-pins.json"` | Repo-owned list of deliberate pins; never synced. |
| `BRIDGES_DIR` | `"references/bridges"` | Where copilot-vscode bridges are recorded. |
| `NOTES_HEADING_RE` | `^## Project-Specific Notes[ \t]*\r?$` (multiline) | The single Notes-heading rule used by drift and above-notes checks; tolerates trailing blanks and CRLF. |
| `SAFE_REF` | compiled regex (below) | A ref that may be placed in a GitHub URL: a commit, or a plain branch/tag name. Every ref check goes through `is_safe_ref`, which also rejects `.`/`..` segments and `refs/pull/` heads. |

`SAFE_REF`:

```text
^(?:[0-9a-f]{7,40}|[A-Za-z0-9][A-Za-z0-9._/-]{0,99})$
```

---

## File formats

### Shrink review report

`tmp/agentteams-shrink-report.json` (copilot-vscode) or `tmp/agentteams-shrink-report.<framework>.json` (other surfaces), written by agentteams, with a companion `.md`. The JSON is a list of objects; `load_frozen` reads these keys and skips items without `file` and `fence`:

```json
[{"file": "ref-bibtex-reference.md", "fence": "content", "entry": "...", "lost": ["..."], "all_retired": false}]
```

### Intentional pins

`.github/agents/references/intentional-pins.json`. `section` is `<file>:<fence>` exactly as the report prints it:

```json
{"pins": [{"section": "ref-bibtex-reference.md:content",
           "reason": "holds filled tool docs the template would reset to placeholders"}]}
```

### First-seen state

`tmp/frozen-fences.state.json`, written with `indent=2` and sorted keys. Keys are `<surface>|<section>`, values ISO dates:

```json
{
  "copilot-vscode|ref-bibtex-reference.md:content": "2026-10-01"
}
```

---

## Functions

### `is_safe_ref(ref)`

Whether `ref` may go into a GitHub URL. `init` checks `--ref` with it, and the CLI's `update` dispatch checks the resolved upstream ref.

**Args:**

- `ref` (`object`) — The ref to check; any non-`str` value fails.

**Returns:** `bool` — True when `ref` is a `str`, matches `SAFE_REF`, has no `/`-separated part equal to `.` or `..`, and does not start with `refs/pull/` (a pull-request head is unreviewed code served from the upstream repository).

```python
is_safe_ref("v1.0.2")       # True
is_safe_ref("feature/x")    # True
is_safe_ref("a/../b")       # False
is_safe_ref("refs/pull/1/head")  # False
is_safe_ref("-main")        # False
```

---

### `clean(text)`

Make text from reports and repo files safe to print by removing control characters: C0 except tab and newline (`\x00-\x08`, `\x0b-\x1f`), DEL and C1 (`\x7f-\x9f`). Removing the ESC byte stops ANSI escape sequences from acting; their printable remainder (for example `[31m`) stays in the text.

**Args:**

- `text` (`object`) — Any value; it is converted with `str()`.

**Returns:** `str` — The text with control characters removed.

---

### `report_path(root, framework=None)`

Where one surface's shrink review report goes.

**Args:**

- `root` (`Path`) — Repository root.
- `framework` (`str | None`) — Surface name; `None` for the default (copilot-vscode) report.

**Returns:** `Path` — `root/tmp/agentteams-shrink-report.json`, or `root/tmp/agentteams-shrink-report.<framework>.json`.

---

### `prepare_report(root, framework=None)`

Move this surface's previous report aside and return the path for the next one. agentteams writes the report only when it froze something, so a stale report from an earlier run would otherwise survive a run that froze nothing. Both the `.json` and `.md` reports are moved to a hidden `.<name>.prev` file (which `load_frozen` never reads); if no current report exists, any old `.prev` file is removed. Creates `tmp/` if needed.

**Args:**

- `root` (`Path`) — Repository root.
- `framework` (`str | None`) — Surface name, as for `report_path`.

**Returns:** `Path` — The report path to pass to agentteams.

---

### `finish_report(root, framework, succeeded)`

Resolve the reports moved aside by `prepare_report`. After a successful run the kept copies are deleted. After a failed run (for example, agentteams refusing a shrink grant) the kept copies are restored; where there was no earlier report, any partial new report is deleted.

**Args:**

- `root` (`Path`) — Repository root.
- `framework` (`str | None`) — Surface name.
- `succeeded` (`bool`) — Whether the render succeeded.

**Returns:** `None`

---

### `load_frozen(root)`

Every frozen section from the latest reports, across all surfaces (`tmp/agentteams-shrink-report*.json`). The surface is taken from the file name; the unsuffixed report is `copilot-vscode`. Unreadable or non-list reports are skipped.

**Args:**

- `root` (`Path`) — Repository root.

**Returns:** `list[dict]` — One dict per frozen section with keys `surface`, `section` (`"<file>:<fence>"`), `entry` (default `""`), `lost` (default `[]`) and `all_retired` (`bool`).

---

### `load_intentional(root)`

The repo's deliberate pins from `INTENTIONAL_FILE`.

**Args:**

- `root` (`Path`) — Repository root.

**Returns:** `dict[str, str]` — `{section: reason}`; `{}` if the file is absent or unreadable. Entries without a string `section` are ignored.

---

### `record_first_seen(root, items, today=None)`

Update the first-seen state for the current frozen set and return it. A section keeps its first-seen date while it stays frozen; one that thawed is dropped, so a later re-freeze starts a new age. The state file is always rewritten, including when `items` is empty.

**Args:**

- `root` (`Path`) — Repository root.
- `items` (`list[dict]`) — Frozen sections, as returned by `load_frozen`.
- `today` (`datetime.date | None`) — Date to record for newly seen sections; defaults to today.

**Returns:** `dict[str, str]` — The new state, `{"<surface>|<section>": ISO date}`.

---

### `first_seen(root)`

Read the first-seen state.

**Args:**

- `root` (`Path`) — Repository root.

**Returns:** `dict[str, str]` — `{"<surface>|<section>": ISO date}`; `{}` if the file is absent, unreadable or not a JSON object.

---

### `frozen_summary(root)`

One line for `update`'s summary, built from the latest report of every surface (not only the surfaces this run rendered). Records first-seen dates as a side effect.

**Args:**

- `root` (`Path`) — Repository root.

**Returns:** `str` — Either `"[researchteam] Frozen fences: none (the shrink guard kept no stale section)."` or a line giving the count, how many are marked intentional, how many are to review, and the `.md` report paths (or `tmp/`).

---

### `age_days(since, today=None)`

Days between an ISO date and today.

**Args:**

- `since` (`str`) — ISO date (`YYYY-MM-DD`).
- `today` (`datetime.date | None`) — Reference date; defaults to today.

**Returns:** `int | None` — The number of days, or `None` when `since` is not a valid ISO date.

---

### `comparable_body(text)`

A seeded file's upstream-owned part: everything before its `## Project-Specific Notes` heading (matched with `NOTES_HEADING_RE`), with trailing whitespace stripped. Without the heading, the whole text with trailing whitespace stripped.

**Args:**

- `text` (`str`) — File content.

**Returns:** `str`

---

### `pinned_ref(root)`

The researchteam commit to compare seeded files against: the `researchteam` pin in `toolchain.lock`, else the `ref` key in the `.researchteam` marker (read with [`_personalize.read_marker`](personalize.md#read_markerroot-path-dictstr-str)), else `main`. An unreadable marker (`OSError`) or an empty `ref` value counts as no marker ref. The value is not validated here; callers check it with `is_safe_ref`.

**Args:**

- `root` (`Path`) — Repository root.

**Returns:** `tuple[str, str]` — `(ref, source)`, where `source` is `"toolchain.lock pin"`, `"marker ref"` or `"main"`.

The marker line it reads (a trailing ` #comment` and one pair of surrounding quotes are stripped; the first `ref` line wins):

```ini
ref = main
```

---

### `bridge_frameworks(root)`

Frameworks with a copilot-vscode bridge recorded under `references/bridges/`, from directory names of the form `copilot-vscode-to-<framework>`.

**Args:**

- `root` (`Path`) — Repository root.

**Returns:** `list[str]` — Sorted framework names; `[]` if the directory is absent.

---

### `parse_bridge_report(text)`

Parse a `bridge-check.report.md`: the value after `Result:` and the `- ` items under `## Changed Source Files`.

**Args:**

- `text` (`str`) — Report content.

**Returns:** `tuple[str, list[str]]` — `(result, changed source files)`; `result` is `"UNKNOWN"` when no `Result:` line is found.

---

### `write_policy_frameworks(root)`

Frameworks under `write_policy: orchestrator-only`. A copilot-vscode bridge or Codex projection into one of these would re-create agents that keep dispatch/write tools and undo the narrowing on every update, so neither may run there. Reads `brief.json`, falling back to `.github/agents/_build-description.json` when the brief is missing, unreadable or lacks `write_policy`.

**Args:**

- `root` (`Path`) — Repository root.

**Returns:** `set[str]` — Lower-cased framework names. Empty when the switch is off or absent. When the switch is on and `write_policy_frameworks` is a non-empty list, that list; otherwise `{"claude", "goose", "codex"}`.

---

### `bridge_outputs(root, framework)`

The agent files a copilot-vscode-to-`framework` bridge wrote. For `claude`: `.claude/agents/*.md` files containing a line `bridge: copilot-vscode-to-claude`. For `goose`: `.goose/recipes/*.yaml` files carrying the matching line, or named `bridge-*`. Shared bridge infrastructure (team docs, settings examples, `references/`) is never listed.

**Args:**

- `root` (`Path`) — Repository root.
- `framework` (`str`) — `"claude"` or `"goose"`; any other value returns `[]`.

**Returns:** `list[str]` — Repository-relative paths, sorted.

---

### Private helpers

| Name | Purpose |
|------|---------|
| `_kept(path)` | Hidden `.<name>.prev` path where a previous report waits during a run. |
| `_WRITE_POLICY_TARGETS` | `("claude", "goose", "codex")`: the default frameworks for `write_policy_frameworks`. |

---

## See Also

- [`index`](index.md) — API reference overview.
- [`update`](update.md) — sets `AGENTTEAMS_SHRINK_REPORT` and prints `frozen_summary`.
- [`doctor`](doctor.md) — lists frozen sections and runs `--drift`.
- [`release`](release.md) — `read_lock_pin`, used by `pinned_ref`.
- [`manifest`](manifest.md) — which files `init` seeds and `update` syncs.
- [`notes`](notes.md) — the Notes block below the comparable body.
- [`fetch`](fetch.md) — fetches upstream files at the ref `pinned_ref` returns.
- [CLI reference](../cli-reference.md)
