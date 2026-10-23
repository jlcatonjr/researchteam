# `_update_cmd` — ResearchTeam

Implementation of `researchteam update` and `researchteam materialize`. `update` syncs the layer-2 managed files from the upstream researchteam repository, using the merge strategy recorded for each file. It then syncs the upstream `researchteam:notes` blocks and runs the layer-1 `agentteams --update --merge` pass on every agent surface the repository has, followed by Codex and bridge refreshes. `materialize` is the separate, destructive path: an `agentteams --update --overwrite` re-render from `brief.json`, then a re-personalization of `README.md` / `CLAUDE.md`. Both run inside a frozen-surfaces guard. The guard refuses an unverified unfreeze, and it fails closed if anything under a frozen surface changed.

> *Source: `researchteam/_update_cmd.py`*

> **Stability.** The supported interface is the `researchteam` CLI. The functions on this page are documented for contributors and may change between releases.

---

## Constants

| Name | Value / meaning |
|------|-----------------|
| `NATIVE_SURFACES` | `(("claude", ".claude/agents"), ("goose", ".goose/recipes"))`: native agent surfaces besides copilot-vscode (`.github/agents`) that a repo may carry. Each is a separate agentteams render target. |
| `TOOLCHAIN_HOOK_SCRIPT` | `"scripts/check_toolchain.py"`: the toolchain check looked for in `.claude/settings(.local).json` SessionStart hooks. |
| `TOOLCHAIN_HOOK_EXAMPLE` | `".claude/settings.toolchain.example.json"`: the file the operator is told to merge from. |
| `_P5A_FLAG` | `"--discard-user-regions"`: the agentteams flag that opts out of carrying user-editable regions across `--overwrite`. Its presence in `agentteams --help` is also the capability check for P5a. |
| `_LAYER1_OFF` | `{"off", "false", "no", "0"}`: values of `layer1 =` in `.researchteam` that disable layer 1. |
| `_GRANT_KEYS` | `("tools", "agents")`: front-matter list keys read as capability grants (plus `handoffs`). |
| `_SCANNED_MANIFESTS` | `("pyproject.toml", "requirements.txt", "package.json", "Cargo.toml", "go.mod", "Gemfile")`: dependency manifests agentteams' project scan turns into tool agents. |
| `_CODEX_REFUSED` | Message printed (dry run) or used as the exit message (real run) when `.codex/agents` exists but `write_policy` does not put codex under orchestrator-only. |
| `_BACKUP_STAMP` | Per-run backup folder name (UTC `%Y%m%dT%H%M%S%fZ`). Set at import and reset at the start of every `update` run. |
| `_FROZEN` | `frozenset[str]`: the validated frozen-surface set of the current run; set by `_frozen_begin`, cleared by `_frozen_end`. |
| `_VERIFIED_LAUNCHERS` | `set[str]`: agentteams launchers that already passed `_preflight_agentteams` in this process, so several renders do not re-probe the same one. |

Merge strategies come from `_manifest.MERGE_STRATEGIES` (see [`manifest`](manifest.md)): `"fenced-preserve"` (`.gitignore`, `CLAUDE.md`), `"above-notes"` (`.github/agents/interpretation-advisor.agent.md`), and `"overwrite"` for any file not listed.

---

## Entry points

### `run_update(root, ref, yes, dry_run, layer2_only, layer1_only=False, accept_upstream=(), codex=True)`

> *Source: `researchteam/_update_cmd.py`*

`researchteam update`. Runs `_run_update_body` inside `_guarded` (the frozen-surfaces guard). Before the body runs, `codex` goes through `_codex_allowed`, which forces it to `False` (and says so) when `frozen_surfaces` lists `codex`.

**Args:**

- `root` (`Path`) — Repository root (holds `.researchteam`).
- `ref` (`str`) — Upstream git ref to fetch layer-2 files and Notes blocks from (resolved by `cli.main`).
- `yes` (`bool`) — Apply without interactive prompts.
- `dry_run` (`bool`) — Report what would change; write nothing.
- `layer2_only` (`bool`) — Sync layer 2 and Notes, skip everything from the agentteams pass on.
- `layer1_only` (`bool`) — Skip the layer-2 sync; run only the agent-side passes.
- `accept_upstream` (`list[str] | tuple[str, ...]`) — `above-notes` paths whose upstream head should replace a customised local one.
- `codex` (`bool`) — `False` skips the Codex step (`--no-codex`).

**Returns:** `None`.

**Sequence.** `_guarded` first calls `_frozen_begin` (see [Frozen-surface guard](#frozen-surface-guard)). `_run_update_body` then does the following, in order:

1. Starts a new backup stamp. Exits if both `layer1_only` and `layer2_only` are set.
2. Reads `layer1_enabled(root)`. With `layer1_only` and layer 1 off, prints that there is nothing to do and returns. With layer 1 off otherwise, prints that only layer 2 is synced.
3. **`layer1_only` path** (then returns):
   1. `_run_agentteams(root, yes, dry_run)` — copilot-vscode merge pass.
   2. `_render_native_surfaces(..., overwrite=False)` — claude/goose merge passes.
   3. `_refresh_codex_unless_frozen(root, dry_run, codex)`.
   4. `_merge_bridges(root, dry_run)`.
   5. On the upstream repository only (`_personalize.is_upstream`), `_sync_notes(root, None, yes=True, dry_run)`, which copies its own `.github` Notes blocks into its other surfaces.
   6. `_print_frozen_summary(root, dry_run)`.
4. **Layer-2 sync.** Gets the profile from `brief.json` (`_read_brief_profile`) and the file list from `managed_files_for(profile)`. `--accept-upstream` paths that are not `above-notes` files are reported and ignored. For each managed file:
   - Under a frozen surface: reported as `[frozen]`, skipped.
   - Fetched with `fetch_raw(UPSTREAM_REPO, ref, rel_path)`. A `RuntimeError` is recorded as a fetch error and the loop continues.
   - **Local file missing:** created (`[dry-run] Would create` under dry run).
   - **`above-notes`:** `_reconcile_above_notes` builds upstream's head plus the local Notes tail. If the upstream copy has no Notes heading, the file is kept and counted as skipped. Unless the path is in `accept_upstream`, `_above_notes_pristine` checks whether the local head still equals upstream at the pinned commit. A customised or unverifiable file is kept under `--yes` or `--dry-run`, with an `--accept-upstream` hint. Interactively it goes to the prompt, whose default (No) keeps it. If upstream's front matter widens `tools`/`agents`/handoffs (`_grant_widening`), the widening is printed, and under `--yes` (not dry run) the file is kept. Before writing, the previous file is backed up to `tmp/researchteam-backups/<stamp>/<rel_path>`, and under `--yes` the first 50 diff lines are printed.
   - **`fenced-preserve`:** `_reconcile_fenced` replaces only the managed block (details below). Any warning is printed, and a kept file counts as skipped.
   - **`overwrite`:** replaced wholesale when it differs.
   - With a change pending: under dry run prints `Would update`. Interactively it shows up to 50 diff lines and asks `Apply? [y/N]`. Otherwise it writes the file and adds the execute bits to `.sh` files.
5. **Notes sync.** Unless the profile is `generic`, runs `_sync_notes(root, ref, yes, dry_run)`.
6. Prints fetch errors (to stderr), a summary (`N updated, N skipped, N errors`), and `_toolchain_hook_note` when the toolchain check exists but is not wired to SessionStart.
7. Returns here if `layer2_only` or layer 1 is off.
8. **Layer 1:** `_run_agentteams` (copilot-vscode merge), `_render_native_surfaces(overwrite=False)`, `_refresh_codex_unless_frozen`, `_merge_bridges`, `_print_frozen_summary`.

Finally `_frozen_end` runs from a `finally`, whether the body succeeded or not.

**Exit behaviour:** exits non-zero on mutually exclusive flags, an invalid `frozen_surfaces`, a refused unfreeze, a missing/unrunnable/unreviewed agentteams, a placeholder brief (real run), a non-zero agentteams exit, a Codex refusal (real run), or a changed frozen path.

**Example:**

```bash
researchteam update --dry-run
researchteam update --yes --accept-upstream .github/agents/interpretation-advisor.agent.md
researchteam update --layer1-only --no-codex
```

---

### `run_materialize(root, yes, dry_run, copilot_only=False, adopt_orphans=False, codex=True, discard_user_regions=False)`

> *Source: `researchteam/_update_cmd.py`*

`researchteam materialize`. Runs `_run_materialize_body` inside `_guarded`, with `codex` filtered through `_codex_allowed`.

**Args:**

- `root` (`Path`) — Repository root.
- `yes` (`bool`) — Skip the overwrite confirmation and pass `--yes` to agentteams.
- `dry_run` (`bool`) — Pass `--dry-run` to agentteams; skip the prompt and the re-personalization.
- `copilot_only` (`bool`) — Re-render only `.github/agents`; skip native surfaces.
- `adopt_orphans` (`bool`) — Pass `--adopt-orphans` to every render.
- `codex` (`bool`) — `False` skips the Codex refresh.
- `discard_user_regions` (`bool`) — Pass `--discard-user-regions` to every render.

**Returns:** `None`.

**Sequence** (`_run_materialize_body`, after `_frozen_begin`):

1. Exits if `layer1 = off`, if the repo is the upstream repository (`is_upstream = true`), or if `brief.json` still contains `BRIEF_PLACEHOLDER`.
2. `_require_p5a(_preflight_agentteams())`. Before any prompt, this checks that agentteams is reviewed code and supports `--discard-user-regions`.
3. Prints that the run replaces generated agent bodies. Unless `dry_run` or `yes`, asks `Proceed with the overwrite re-render? [y/N]`. Any answer but `y` prints `Aborted; nothing changed.` and returns.
4. `_run_agentteams(..., overwrite=True, adopt_orphans, discard_user_regions)` on copilot-vscode. On success (not dry run) this includes the `_reconcile_manifest_back` write-back.
5. Unless `copilot_only`: `_render_native_surfaces(..., overwrite=True, label="materialize")`.
6. If `codex`: `_refresh_codex(root, dry_run)`. Unlike `update`, nothing is printed when `codex` is `False`.
7. If not dry run: `_personalize.run_personalize(root, force=False, quiet=False)`. Otherwise prints what it would re-personalize.

`_frozen_end` then runs from a `finally`.

**Exit behaviour:** as for `run_update`, plus the three refusals in step 1 and the P5a check.

**Example:**

```bash
researchteam materialize --dry-run
researchteam materialize --adopt-orphans --yes
```

---

## Frozen-surface guard

### `_guarded(root, dry_run, body)`

Calls `_frozen_begin(root)`, runs `body(frozen)`, and always calls `_frozen_end(..., succeeded=<body returned normally>)` from a `finally`.

### `_frozen_begin(root)`

Validates `brief.json` `frozen_surfaces` via `_frozen.load`. A `FrozenSurfacesError` exits with `Nothing was changed.` A surface counts as dropped when it is in `_frozen.recorded(root) | _frozen.at_head(root)` but no longer frozen. For each dropped surface it calls `_frozen.verify_unfreeze(root, surface, launcher)`, which needs an operator-signed `unfreeze-<surface>` decision row. If that fails it exits. It prints the frozen set and the paths researchteam will not write. If `AGENTS.md` is frozen and present, it saves the file's bytes, then takes `_frozen.snapshot` and sets `_FROZEN`.

**Returns:** `tuple[frozenset[str], dict[str, str], bytes | None]` — frozen set, snapshot, saved `AGENTS.md` bytes.

### `_frozen_end(root, state, *, dry_run, succeeded)`

Clears `_FROZEN` and computes `_frozen.changed_since`. If a frozen `AGENTS.md` changed, for example because an unfrozen Goose or Codex render wrote it, the saved bytes are written back and it re-checks. If any frozen path still differs it exits with `FAILED CLOSED` and lists up to 20 paths. On a successful, non-dry run it records the frozen set in `.researchteam` (`_frozen.record`).

### `_codex_allowed(frozen, codex)`

Returns `False`, printing `frozen_surfaces lists codex: same as --no-codex.`, when `"codex"` is frozen and `codex` is `True`. Otherwise returns `codex`.

### `_is_frozen(rel)`

`True` when `_FROZEN` is non-empty and `_frozen.is_frozen_path(rel, _FROZEN)`.

---

## Layer-2 reconciliation

### `_reconcile_fenced(rel_path, local_content, remote_content, yes)`

Reconcile a `fenced-preserve` file without deleting lines that exist only in the derived repo.

**Args:**

- `rel_path` (`str`) — Path used in diff labels.
- `local_content` (`str`), `remote_content` (`str`) — Local and upstream text.
- `yes` (`bool`) — Non-interactive mode.

**Returns:** `tuple[str | None, list[str], str]` — `(write_content, preview_diff, warn)`:

| Case | Result |
|------|--------|
| Upstream has no `researchteam:managed` fence | `None`, keep local, warn (never a wholesale overwrite). |
| Both fenced, managed blocks equal | `None`, no warning (no-op). |
| Both fenced, blocks differ | local pre + upstream managed block + local post. The diff covers only the managed block. |
| Local unfenced, equal (after `strip()`) to upstream's fence body | Upstream file as-is (first-time wrap). |
| Local unfenced and divergent, `yes=True` | `None`, keep local, warn to add the fence markers. |
| Local unfenced and divergent, `yes=False` | Upstream file, full diff, and a warning that approval replaces the file wholesale. |

### `_split_fence(text)`

Split `text` around the first `FENCE_CORE_BEGIN` line and the next `FENCE_CORE_END` line. A marker line is matched when the stripped line contains the core string, so both `# >>> …` and `<!-- >>> … -->` work.

**Returns:** `tuple[str, str, str] | None` — `(pre, managed, post)`, where `managed` includes both marker lines. Returns `None` when there is no well-formed BEGIN-then-END pair.

### `_reconcile_above_notes(rel_path, local, remote)`

Build upstream's part above the Notes heading (`_drift.NOTES_HEADING_RE`) plus the local heading and tail. If the local file has no Notes heading, upstream's tail is adopted.

**Returns:** `tuple[str | None, list[str]]`:

- `(None, [warning])` when upstream has no Notes heading. The warning is also printed.
- `(None, [])` when nothing changes.
- Otherwise `(new_content, diff)`, where the diff covers only the part above Notes.

### `_above_notes_pristine(root, rel_path, local, ref, remote)`

Check whether the local file still equals the upstream copy at the repo's pinned researchteam commit (`_drift.pinned_ref`: the `toolchain.lock` pin, else the marker ref, else `main`). It compares with `_drift.comparable_body`. When the pin equals `ref` it reuses `remote`; otherwise it fetches that commit.

**Returns:** `tuple[bool | None, str]` — `True` means un-customised, `False` means customised, and `None` means it cannot tell (a pin that fails `is_safe_ref`, or a failed fetch). The second element is a detail string.

### `_grant_widening(local, remote)`

Compare the front-matter grants (`_front_matter_grants`) and list each key where upstream adds names, formatted `"tools: +a, b"`. A non-empty result means upstream widens a declared capability grant (C-3), which `--yes` will not apply.

**Returns:** `list[str]`.

### `_sync_notes(root, ref, yes, dry_run)`

Write each upstream `researchteam:notes` block into every surface file its agent has in this repo (`_notes.agents_for`, `_notes.surfaces`). With `ref=None` it reads this repo's own `.github` copies; otherwise it fetches from upstream at `ref`.

The run stops before touching any agent when `brief.json` `researchteam_notes.exclude` is malformed. An agent is skipped when any of these holds:

- It is listed in `exclude`.
- Its block is unavailable (`OSError`, `RuntimeError`, `NotesError`) or absent.
- Its canonical file is an `above-notes` file the repo customised (`_notes_customised`). This check runs only when `ref` is set and the repo is not upstream.

Each surface path under a frozen surface is skipped. Before each write the previous file is backed up to `tmp/researchteam-backups/<stamp>/`. Interactively, each file shows a diff and asks `Apply? [y/N]`. Repo-owned Notes outside the block are not touched.

### `_notes_customised(root, rel, ref, source)`

Return why the Notes block for `rel` must not be synced, or `None`. Only `above-notes` files inside `root` are judged. A file matching `source` is un-customised. Otherwise `_above_notes_pristine` decides, and an unverifiable file counts as customised.

---

## Layer-1 (agentteams)

### `_run_agentteams(root, yes, dry_run, overwrite=False, framework=None, adopt_orphans=False, discard_user_regions=False)`

Run one agentteams render.

**Args:**

- `root` (`Path`) — Repository root (agentteams runs with `cwd=root`).
- `yes` (`bool`), `dry_run` (`bool`) — Appended as `--yes` / `--dry-run`.
- `overwrite` (`bool`) — `False` runs a merge render, `True` an overwrite render (materialize).
- `framework` (`str | None`) — `None` means copilot-vscode. Otherwise `"claude"`, `"goose"` or `"codex"`.
- `adopt_orphans` (`bool`), `discard_user_regions` (`bool`) — Overwrite mode only.

**Behaviour:**

1. Returns without rendering when the surface is frozen. For `framework=None` the surface counts as frozen when `copilot-vscode` or `copilot-cli` is.
2. If `brief.json` holds `BRIEF_PLACEHOLDER`, a dry run prints the message and returns, and a real run exits.
3. `_preflight_agentteams()`, then `_resolve_descriptor(root)`.
4. Builds the command:
   - merge: `agentteams --description <d> --update --merge --shrink-policy preserve`
   - overwrite: `agentteams --description <d> --update --overwrite`, plus `--adopt-orphans` and/or `--discard-user-regions`
   - with `framework`, both modes add `--framework <fw> --project . --materialize-native`
   - then `--yes` / `--dry-run` as set.
5. When not a dry run, calls `_drift.prepare_report(root, framework)`. In merge mode it also sets `AGENTTEAMS_SHRINK_REPORT` to that report path in the child environment.
6. Runs the command. Any exception (for example a missing executable or Ctrl-C) calls `finish_report(succeeded=False)` when not a dry run and re-raises. The temporary descriptor is always deleted.
7. Calls `finish_report(succeeded=<returncode == 0>)` when not a dry run. A non-zero return prints `agentteams update exited non-zero.` and exits with that code.
8. On success, when not a dry run and `framework is None`, calls `_reconcile_manifest_back(root)`.

### `_preflight_agentteams()`

Resolve the agentteams launcher (`_resolve_agentteams`) and check it before use. A launcher already in `_VERIFIED_LAUNCHERS` is returned at once. It exits with an actionable message in three cases:

- No launcher is found.
- `agentteams --version` returns non-zero. This is usually a stale editable install.
- `_agentteams_provenance.check(exe)` is non-zero: an unmerged or dirty checkout (CA-033), an unallowed local snapshot, or an unverified install (another repository's VCS install, an archive or an index install) without `RESEARCHTEAM_ALLOW_UNVERIFIED_AGENTTEAMS=1`.

**Returns:** `str` — the launcher path, which is also added to `_VERIFIED_LAUNCHERS`.

### `_resolve_agentteams()`

**Returns:** `tuple[str | None, str]` — the `agentteams` file beside `sys.executable` when it exists and is executable, else `shutil.which("agentteams")`, together with a "where" label. `sys.executable` is not resolved through symlinks, so a venv's `bin/` is used.

### `_resolve_descriptor(root)`

Build the descriptor passed to agentteams as a union of the two descriptor files, so neither loses data.

- No `brief.json`: uses `.github/agents/_build-description.json` if present, else exits with guidance (`layer1 = off` or `--layer2-only`).
- No manifest, a parse error (a warning goes to stderr), or nothing to inject: uses `"brief.json"`.
- Otherwise: copies `selected_archetypes` / `governance_agents` from the manifest into the brief's data where they are non-empty and different. The result is written to a temp file `.rt-descriptor-*.json` in `root`.

**Returns:** `tuple[str, Path | None]` — the descriptor argument relative to `root`, and the temp file to delete (or `None`).

### `_reconcile_manifest_back(root)`

RT-5 write-back: copy every `brief.json` key except `selected_archetypes` / `governance_agents` onto `_build-description.json`, and write it (indent 2) only when something changed. It does nothing when either file is missing or unreadable. A write error is printed to stderr.

### `_render_native_surfaces(root, *, yes, dry_run, overwrite, adopt_orphans=False, discard_user_regions=False, label="update")`

Render each non-frozen surface returned by `_native_surfaces` with `_run_agentteams(framework=fw)`. When there are any, it first prints `_warn_scan_divergence`. On a `SystemExit` it prints which surfaces were rendered and which were not attempted, then re-raises. With no surfaces it prints `no native claude/goose surfaces present.`

### `_native_surfaces(root)`

**Returns:** `list[tuple[str, str]]` — each `NATIVE_SURFACES` entry whose `<dir>/references/build-log.json` is a readable JSON object without `origin: "interop"`. An unreadable log is reported to stderr and skipped. A bare bridge directory, or an interop projection marker, is never treated as a native team.

### `_require_p5a(exe)`

Exits unless `agentteams --help` output contains `--discard-user-regions` (agentteams P5a, f113f5d or later). An older agentteams would drop user-editable regions on `--overwrite`.

### `_merge_bridges(root, dry_run)`

Refresh each recorded copilot-vscode bridge (`_drift.bridge_frameworks`) with `agentteams --bridge-from .github/agents --framework <fw> --output . --bridge-merge`. It skips frameworks in these cases:

- If `AGENTS.md` is frozen, no bridge is refreshed, because every bridge merge writes it.
- A frozen framework is skipped.
- A framework covered by `write_policy: orchestrator-only` (`_drift.write_policy_frameworks`) is skipped, and its remaining bridge outputs are listed for removal through `@cleanup`. Nothing is deleted.

It warns (stderr) for each covered framework other than codex that has no native team. A failed merge is reported to stderr and is not fatal. A dry run only lists what it would refresh.

### Codex

| Function | Behaviour |
|----------|-----------|
| `_refresh_codex_unless_frozen(root, dry_run, codex)` | With `codex=False`, prints that the Codex surface was left unchanged. Otherwise calls `_refresh_codex`. |
| `_refresh_codex(root, dry_run)` | Does nothing without `.codex/agents/`. If `write_policy_frameworks` lacks `codex`, a dry run prints `_CODEX_REFUSED` and returns, and a real run exits with it. Otherwise runs `_run_agentteams(yes=True, overwrite=False, framework="codex")`, then `_project_codex_skills`, then `_warn_codex_leftovers` (not on a dry run). |
| `_project_codex_skills(root, dry_run)` | If `.claude/skills/` exists, runs `agentteams --interop-from .claude/agents --interop-source-framework claude --framework codex --interop-skills-only --output . --overwrite --yes [--dry-run]`. A failure is reported to stderr, not raised. |
| `_warn_codex_leftovers(root)` | Returns, and warns about, the `.codex/agents/*.toml` files that are neither in the native build-log's `file_hashes` nor named by `agent_slug_list`. Deletes nothing. Returns `[]` for a missing, unreadable or interop log. |

---

## Minor helpers

| Function | Purpose |
|----------|---------|
| `layer1_enabled(root)` | `False` when the marker's `layer1` value, as parsed by [`_personalize.read_marker`](personalize.md#read_markerroot-path-dictstr-str) (first occurrence wins, trailing ` #comment` dropped, one pair of quotes stripped), is `off`, `false`, `no` or `0` (case-insensitive). `True` otherwise, including when the key is absent, the marker is missing, or it is unreadable (`OSError`). |
| `_fence_body(managed_block)` | The managed block without its first and last (marker) lines. |
| `_split_above_notes(text)` | `(head, tail)` split at the Notes heading, or `None`. |
| `_front_matter_grants(text)` | `{"tools", "agents", "handoffs"}` to sets of names, read from `key: [..]` lines and indented `agent: x` lines in the leading `---` block. Front matter it cannot parse yields empty sets. |
| `_new_backup_stamp()` | UTC timestamp with microseconds, used as the backup folder name. |
| `_backup(root, rel_path, content)` | Writes `content` to `tmp/researchteam-backups/<_BACKUP_STAMP>/<rel_path>` and returns that path. |
| `_read_brief_profile(root)` | `brief.json` `layer2_profile` if it is a string, else `None` (missing or unreadable brief). |
| `_brief_has_placeholder(root)` | `True` when `brief.json` contains `BRIEF_PLACEHOLDER` (`"<YOUR PROJECT NAME>"`). |
| `_toolchain_hook_installed(root)` | `True` when a SessionStart hook command in `.claude/settings.json` or `settings.local.json` mentions `TOOLCHAIN_HOOK_SCRIPT`. |
| `_toolchain_hook_note(root)` | A note to merge `TOOLCHAIN_HOOK_EXAMPLE` when the script exists but the hook is not installed; otherwise `""`. researchteam never edits `settings.json`. |
| `_scan_divergence(root)` / `_warn_scan_divergence(root)` | Lists (and warns on stderr about) brief fields whose absence lets native surfaces' repo scan give a different roster from copilot-vscode: `retrieval_integration` when it is missing, and `tools` when it is missing and a `_SCANNED_MANIFESTS` file exists. |
| `_print_frozen_summary(root, dry_run)` | Prints `_drift.frozen_summary(root)`, the sections agentteams' shrink guard kept unchanged, per surface report. Skipped on a dry run. This is unrelated to frozen surfaces. |

---

## See Also

- [`index`](index.md) — API reference overview.
- [`cli`](cli.md) — parses the flags and resolves `ref` before calling `run_update` / `run_materialize`.
- [`manifest`](manifest.md) — `managed_files_for`, `MERGE_STRATEGIES`, fence cores, `BRIEF_PLACEHOLDER`.
- [`fetch`](fetch.md) — `fetch_raw`.
- [`drift`](drift.md) — `pinned_ref`, `comparable_body`, shrink reports, bridge and write-policy helpers.
- [`frozen`](frozen.md) — the frozen-surfaces contract used by the guard.
- [`notes`](notes.md) — `researchteam:notes` block extraction and application.
- [`personalize`](personalize.md) — `run_personalize`, `is_upstream`.
- [`agentteams-provenance`](agentteams-provenance.md) — the provenance check in `_preflight_agentteams`.
- [`release`](release.md) — release-locked refs.
- [`init`](init.md), [`doctor`](doctor.md) — sibling commands.
- [CLI reference](../cli-reference.md) — user-facing flags for `update` and `materialize`.
