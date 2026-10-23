# `cli` — ResearchTeam

The `researchteam` console-script entry point. `main()` builds the argparse parser for the six subcommands (`init`, `update`, `personalize`, `materialize`, `status`, `doctor`), locates the repository root, resolves the upstream ref for `update`, and hands off to the implementing module. Each implementation module is imported lazily inside its branch, so a subcommand only loads what it uses.

> *Source: `researchteam/cli.py`*

> **Stability.** The supported interface is the `researchteam` CLI. The functions on this page (and the underscore-prefixed modules they call) are documented for contributors and may change between releases.

---

## Constants

| Name | Value / meaning |
|------|-----------------|
| `UPSTREAM_BRANCH` | Imported from `_manifest`: `"main"`. Default for `init --ref` and the fallback ref when `.researchteam` records none. |
| `__version__` | Imported from the `researchteam` package; printed by `--version` and `status`. |

---

## Functions

### `main()`

> *Source: `researchteam/cli.py`*

Parse `sys.argv` and dispatch one subcommand. Before parsing, it calls `sys.stdout.reconfigure(line_buffering=True)` (ignoring `AttributeError`/`ValueError`) so stdout and stderr interleave in order in CI logs.

A subcommand is required (`sub.required = True`); the top-level parser also accepts `--version`, which prints `researchteam <version>`.

**Subcommands and their dispatch:**

| Subcommand | Arguments | Root lookup | Calls |
|------------|-----------|-------------|-------|
| `init` | `name` (optional positional, default `None`), `--ref REF` (default `UPSTREAM_BRANCH`), `--remote URL` (default `None`) | none | `_init_cmd.run_init(name, ref, remote)` |
| `update` | `--yes`/`-y`, `--dry-run`, `--layer2-only`, `--layer1-only`, `--ref REF` (default `None`), `--accept-upstream PATH` (repeatable, default `[]`), `--no-codex` | `_find_repo_root(require_marker=True)` | `_update_cmd.run_update(root, ref=..., yes=..., dry_run=..., layer2_only=..., layer1_only=..., accept_upstream=..., codex=not no_codex)` |
| `personalize` | `--force` | `_find_repo_root(require_marker=True)` | `_personalize.run_personalize(root, force=..., quiet=False)` |
| `materialize` | `--copilot-only`, `--adopt-orphans`, `--discard-user-regions`, `--no-codex`, `--yes`/`-y`, `--dry-run` | `_find_repo_root(require_marker=True)` | `_update_cmd.run_materialize(root, yes=..., dry_run=..., copilot_only=..., adopt_orphans=..., codex=not no_codex, discard_user_regions=...)` |
| `status` | none | `_find_repo_root(require_marker=False)` (inside `_cmd_status`) | `_cmd_status()` |
| `doctor` | `--drift` | `_find_repo_root(require_marker=False)` | `_doctor_cmd.run_doctor(root, drift=...)` |

**`update` ref resolution.** The ref passed to `run_update` is the first non-empty of:

1. `--ref`, when given;
2. `_release_locked_ref(root)`, unless `--layer1-only` is set (the lock is not consulted for a layer-1-only run);
3. `_read_marker_ref(root)`.

The resolved ref must pass [`_drift.is_safe_ref`](drift.md#is_safe_refref); otherwise `main()` exits 1 with `[researchteam] refusing the upstream ref '<ref>': not a plain branch, tag or commit name (check --ref and the .researchteam marker's ref).` before `run_update` is called.

**Returns:** `None`.

**Exit behaviour:** argparse exits 2 on a usage error. The root lookup, `_release_locked_ref` and the `update` ref check can exit 1 with a message (see above and below). Otherwise the exit status is whatever the dispatched function produces.

**Example:**

```bash
researchteam update --dry-run
researchteam update --layer2-only --ref v1.0.2
researchteam materialize --adopt-orphans --yes
```

---

### `_find_repo_root(require_marker=False)`

> *Source: `researchteam/cli.py`*

Walk up from the current working directory (the directory itself, then each parent) and record the first directory holding a `.researchteam` marker and the first holding a `.git` entry. The walk stops once both are found.

**Args:**

- `require_marker` (`bool`) — When `True`, a missing `.researchteam` marker is an error.

**Returns:** `Path` — the marker directory when one was found, else the git root.

**Exit behaviour:**

- `require_marker=True` and no marker: prints an error explaining that the command runs inside a derived repo (suggesting `researchteam init <name>`) to stderr and exits 1.
- Neither a marker nor a `.git` found: prints `Error: not inside a git repository.` to stderr and exits 1.

---

### `_release_locked_ref(root)`

> *Source: `researchteam/cli.py`*

Return the commit of the verified researchteam tag when `toolchain.lock` release-locks researchteam, so layer 2 syncs from that tag instead of `main`. Delegates to `_release.locked_layer2_ref(root, UPSTREAM_REPO)`.

**Args:**

- `root` (`Path`) — Repository root.

**Returns:** `str | None` — the tag's commit SHA, or `None` when the lock does not release-lock researchteam. On success it prints `[researchteam] release-locked: syncing layer 2 from researchteam <tag> (<sha[:12]>).`

**Exit behaviour:** a `ReleaseError` (the lock names a tag that does not verify) exits with a message saying layer-2 sync is refused. It fails closed and never falls back to `main`; `--ref` is the documented way past it.

---

### `_read_marker_ref(root)`

> *Source: `researchteam/cli.py`*

Read the upstream ref recorded in `.researchteam`.

**Args:**

- `root` (`Path`) — Repository root.

**Returns:** `str` — the marker's `ref` value as parsed by [`_personalize.read_marker`](personalize.md#read_markerroot-path-dictstr-str) (first occurrence wins, trailing ` #comment` dropped, one pair of surrounding quotes stripped). Returns `UPSTREAM_BRANCH` (`"main"`) when the marker is missing, has no `ref` key or an empty one, or cannot be read (`OSError`).

---

### `_cmd_status()`

> *Source: `researchteam/cli.py`*

Implementation of `researchteam status`. Finds the root with `_find_repo_root(require_marker=False)`, prints `researchteam <version>`, then either the marker path and its full (stripped) contents, or `No .researchteam marker found (upstream repo or uninitialized).`

**Returns:** `None`.

---

## See Also

- [`index`](index.md) — API reference overview.
- [`update`](update.md) — `run_update` / `run_materialize`, called by `update` and `materialize`.
- [`init`](init.md) — `run_init`, called by `init`.
- [`personalize`](personalize.md) — `run_personalize`, called by `personalize` and `materialize`.
- [`doctor`](doctor.md) — `run_doctor`, called by `doctor`.
- [`release`](release.md) — `locked_layer2_ref`, used by `_release_locked_ref`.
- [`manifest`](manifest.md) — `UPSTREAM_BRANCH`, `UPSTREAM_REPO`.
- [`drift`](drift.md), [`frozen`](frozen.md), [`notes`](notes.md), [`agentteams-provenance`](agentteams-provenance.md), [`fetch`](fetch.md) — modules the subcommands use.
- [CLI reference](../cli-reference.md) — user-facing command and flag documentation.
