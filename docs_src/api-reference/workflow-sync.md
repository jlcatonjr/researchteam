# `_workflow_sync` — ResearchTeam

Implementation of `researchteam workflow-sync` (#186). It brings a derived repository's `.github/workflows/agentteams-sync.yml` up to the installed scaffold and keeps the repository's own top-level `on:` block, so its schedule stays exactly as the repository has it.

> *Source: `researchteam/_workflow_sync.py`*

> **Stability.** This module is underscore-prefixed. The supported interface is the `researchteam` CLI ([CLI reference](../cli-reference.md)); the functions below are documented for contributors and may change between releases.

**Behaviour:**

- The workflow is written at `init` and otherwise only by this command; `researchteam update` and the autosync gate never touch `.github/workflows/`.
- Everything except the top-level `on:` block comes from the scaffold. The `on:` block is kept: schedule present, absent or commented out.
- With no workflow present, the scaffold is written as shipped. Its weekly schedule is commented out, so autosync runs only when dispatched until the repository turns it on.
- A unified diff is shown first; the command asks before writing unless `--yes` is given, and `--dry-run` writes nothing.
- It refuses a symlinked workflow or parent directory, a non-regular file, a non-UTF-8 file, and a file without exactly one block-style top-level `on:` key (for example `on: [push]`). The write goes through a new temporary file (`O_EXCL | O_NOFOLLOW`) and `os.replace`, so it never follows a link.

---

## Constants

| Name | Value | Purpose |
|------|-------|---------|
| `WORKFLOW` | `".github/workflows/agentteams-sync.yml"` | The derived repository's autosync workflow. |
| `SCAFFOLD` | `"agentteams-sync-derived.yml"` | The packaged scaffold under `researchteam/scaffold/`. |

---

## Classes

### `WorkflowSyncError`

A condition under which `workflow-sync` refuses before writing anything.

---

## Functions

### `on_block(text)`

Returns the `(start, end)` line indexes of the top-level `on:` block: from the `on:` line to the next top-level key, leaving out the blank lines and column-0 comments just before that key. Raises `WorkflowSyncError` unless there is exactly one block-style `on:` key (`on:`, `"on":` or `'on':`).

### `merge(scaffold, existing)`

The scaffold with its `on:` block replaced by the existing workflow's `on:` block. Idempotent.

### `load_scaffold()`

The packaged scaffold text, read through `importlib.resources`, so it matches the installed researchteam.

### `plan(root, scaffold=None)`

Returns `(current, proposed)` for the repository at `root`; `current` is `None` when no workflow exists. Raises `WorkflowSyncError` for a symlinked path, a non-regular file, a non-UTF-8 file or an unusable `on:` block.

### `run_workflow_sync(root, yes=False, dry_run=False)`

The command: plan, print the diff, confirm (unless `yes`), write. Returns `0` on success or when there is nothing to do, `1` when it refuses, the operator declines, or the write fails.
