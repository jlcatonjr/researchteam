# `_doctor_cmd` — ResearchTeam

Implementation of `researchteam doctor`, a health check for the researchteam ↔ agentteams toolchain. It checks that `agentteams` resolves, runs, and is not installed from a temporary path; reports the `toolchain.lock` pin and SessionStart wiring; reports frozen surfaces and frozen fences; optionally checks seeded files and bridges; and checks that `brief.json` and `_build-description.json` together give `update` a complete descriptor. It was written to catch, before it causes an outage, a stale editable `agentteams` install whose finder points at a deleted temporary path.

> *Source: `researchteam/_doctor_cmd.py`*

> **Stability.** This module is underscore-prefixed. The supported interface is the `researchteam` CLI ([CLI reference](../cli-reference.md)); the functions below are documented for contributors and may change between releases.

---

## Constants

| Name | Value | Purpose |
|------|-------|---------|
| `_EPHEMERAL_MARKERS` | `("/tmp/", "/private/tmp/", "-worktree", "scratchpad", "/var/folders/")` | Substrings that mark an `agentteams` source path as ephemeral. |

---

## Functions

### `run_doctor(root: Path, drift: bool = False) -> None`

> *Source: `researchteam/_doctor_cmd.py`*

Run every check and print a report. The CLI calls it as `run_doctor(root, drift=args.drift)`, where `root` is found without requiring a `.researchteam` marker.

**Args:**

- `root` (`Path`) — Repository root.
- `drift` (`bool`) — Also run the checks that need the network or agentteams (seeded files, bridges). The bridge check deletes and rewrites the gitignored `bridge-check.report.md` files.

**Report levels:**

| Level | Printed as | Meaning |
|-------|------------|---------|
| OK | `  [ok]   …` on stdout | The check passed. |
| WARN | `  [warn] …` on stdout | Advisory. Does not count as a problem and does not change the exit status. |
| FAIL | `  [FAIL] …` on stderr | A problem. Increments the problem count. |

**Returns:** `None` when there are no FAIL results; it prints `[researchteam] doctor: all critical checks passed.`

**Exit behaviour:** if any FAIL was reported, prints `[researchteam] doctor: N problem(s) found (see [FAIL] above).` to stderr and calls `sys.exit(1)`.

#### Checks, in order

**0. Layer-1 switch.** If `.researchteam` declares `layer1 = off` (also `false`, `no`, `0`), reports OK and skips checks 1–4. Otherwise:

**1. agentteams resolves.** Looks for an `agentteams` executable beside the current interpreter, then on `PATH`.
- OK: prints the path and where it was found.
- FAIL: found in neither place; layer-1 `researchteam update` will fail. Checks 2–4 are skipped.

**2. agentteams runs.** Runs `agentteams --version`.
- OK: exit 0; prints the version output.
- FAIL: non-zero exit, typically a stale editable install pointing at a deleted path. Prints the last output line (up to 200 characters). Checks 3–4 are skipped.

**3. Source path is not ephemeral.** Reads the console script's shebang to find its interpreter (falls back to `sys.executable`), then asks that interpreter for the directory of `build_team.__file__`.
- OK: the path contains none of `_EPHEMERAL_MARKERS`.
- WARN: the source path could not be determined.
- FAIL: the path contains an ephemeral marker.

**4. Code & API index available.** Runs `agentteams --help` and looks for `--query-code`.
- OK: present; retrieval surface #2 is available.
- WARN: absent; `--query-code`, `/code-recall` and the bridge `code-query` command are unavailable.

**5. Toolchain pin** (`_check_toolchain`, always runs).
- WARN: `scripts/check_toolchain.py` is missing (run `researchteam update` to receive it); nothing else in this check runs.
- Otherwise runs `check_toolchain.py --python <sys.executable>` with a 60-second timeout. Each non-blank stdout line is reported (stderr and the exit status are ignored; empty stdout gives one WARN `(no output)`) with its `[toolchain] ` prefix removed: OK if the line starts with `[toolchain] OK`, WARN for every other line (including "no toolchain.lock yet", `BEHIND`, `MISMATCH` and `note` lines, and a failure to run the script).
- OK / WARN: whether `.claude/settings.json` or `.claude/settings.local.json` has a SessionStart hook whose command contains `scripts/check_toolchain.py`. WARN asks the operator to merge `.claude/settings.toolchain.example.json`.

**6. Frozen surfaces** (`_check_frozen_surfaces`, always runs). Reads `frozen_surfaces` from `brief.json` and the set recorded in `.researchteam`.
- FAIL: `brief.json` is unreadable, or `frozen_surfaces` is invalid; `researchteam update` refuses to run until it is fixed. The rest of this check is skipped.
- OK: lists the frozen surfaces and the paths researchteam never writes for them; or `none` when nothing is frozen now or recorded.
- WARN (`unfreeze pending`): surfaces recorded as frozen but no longer in `brief.json`. `update` will not render into them without an operator-signed `unfreeze-<surface>` row verified by agentteams' gate.

**7. Frozen fences** (`_check_frozen_fences`, always runs, offline). Reads the shrink-guard reports `tmp/agentteams-shrink-report*.json` from the last `researchteam update`, intentional pins from `.github/agents/references/intentional-pins.json`, and first-seen dates from `tmp/frozen-fences.state.json`.
- OK: no frozen fences recorded.
- Summary line: OK when every frozen section is listed as intentional, WARN when any needs review.
- Per section: OK for an intentional pin (with its reason and age); WARN for each section to review, with its age, a note when every lost token is retired upstream, and the `AGENTTEAMS_SHRINK_ALLOW=<entry>` release setting. Entries starting with `../` note that agentteams 5f8503e or later is needed.

**8. Seeded files** (`_check_seeded_files`, only with `drift=True`). Compares each `SEEDED_FILES` entry outside `## Project-Specific Notes` with upstream at the pinned ref (the `toolchain.lock` researchteam pin, else the marker `ref`, else `main`).
- OK: `SEEDED_FILES` is empty (the current state, so no network request is made), or every file matches.
- WARN: the ref is not a plain commit or name; a file could not be fetched; a file is missing locally; or a file differs from upstream.

**9. Bridges** (`_check_bridges`, only with `drift=True`). Looks for `references/bridges/copilot-vscode-to-<framework>/` directories.
- OK: none recorded.
- For frameworks covered by `write_policy: orchestrator-only`: FAIL if bridge agents that keep dispatch tools are still present (lists up to 8); otherwise OK.
- For other frameworks: runs the agentteams pre-flight (WARN and stop if it fails), deletes any previous `bridge-check.report.md`, then runs `agentteams --bridge-from .github/agents --framework <fw> --output . --bridge-check` in `root` with a 300-second timeout. OK when it exits 0 and the report says `PASS`; otherwise WARN with the result, up to 5 changed files, agentteams' last output line when the result is unknown, and the `--bridge-merge` refresh command.

**10. Descriptor health** (always runs). Loads `brief.json` and `.github/agents/_build-description.json` (unreadable JSON is treated as `{}`).
- `brief.json`: WARN if missing; WARN if `authority_sources` or `style_rules` is missing or empty, because the corresponding managed fences may render as placeholders; otherwise OK.
- `_build-description.json`: WARN if missing (an update from `brief.json` alone may orphan registered archetypes); WARN if `selected_archetypes` is empty; otherwise OK with the archetype count.
- When both files exist: OK either way, saying that `brief.json` already carries the roster, or that `update` will merge `brief.json` (content) and `_build-description.json` (roster).

**Example:**

```python
from pathlib import Path
from researchteam._doctor_cmd import run_doctor

run_doctor(Path("."), drift=False)   # exits 1 if any [FAIL]
```

---

### `_check_toolchain(root: Path, ok, warn) -> None`

> *Source: `researchteam/_doctor_cmd.py`*

Check 5 above. Advisory only: it never reports FAIL, so a missing or stale pin does not fail `doctor`. See [`scripts.md`](scripts.md#check_toolchainpy) for the script's output.

---

### `_check_bridges(root: Path, ok, warn, fail=None) -> None`

> *Source: `researchteam/_doctor_cmd.py`*

Check 9 above. When `fail` is `None`, the leftover-bridge-agent finding is reported through `warn` instead.

---

### Private helpers

| Function | Behaviour |
|----------|-----------|
| `_load(path: Path) -> dict` | JSON-decodes `path`; returns `{}` on `OSError` or `JSONDecodeError`. |
| `_script_interpreter(exe: str) -> str` | First token after `#!` on the script's first line; `sys.executable` if there is no shebang or the file cannot be read. |
| `_agentteams_source(interp: str) -> Optional[str]` | Runs `interp -c` to print the directory of `build_team.__file__`; `None` on failure or empty output. |
| `_check_frozen_surfaces(root, ok, warn, fail) -> None` | Check 6. |
| `_check_frozen_fences(root, ok, warn) -> None` | Check 7. |
| `_check_seeded_files(root, ok, warn) -> None` | Check 8. |

---

## See Also

- [`index.md`](index.md) — API reference overview.
- [`cli.md`](cli.md) — dispatches `researchteam doctor`.
- [`update.md`](update.md) — agentteams resolution, pre-flight and the layer-1 switch.
- [`drift.md`](drift.md) — shrink reports, intentional pins, seeded-file and bridge helpers.
- [`frozen.md`](frozen.md) — `frozen_surfaces` validation.
- [`agentteams-provenance.md`](agentteams-provenance.md) — the provenance part of the pre-flight.
- [`release.md`](release.md) — release-locked pins.
- [`manifest.md`](manifest.md) — `SEEDED_FILES`.
- [`scripts.md`](scripts.md) — `check_toolchain.py`.
- [`../cli-reference.md`](../cli-reference.md) — command-line reference.
