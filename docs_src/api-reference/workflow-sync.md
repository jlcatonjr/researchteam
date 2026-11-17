# `_workflow_sync` — ResearchTeam

Implementation of `researchteam workflow-sync` (#186). It brings one of a derived repository's workflows up to the installed scaffold and keeps the repository's own top-level `on:` block. The default is the autosync workflow, `.github/workflows/agentteams-sync.yml`, whose schedule stays exactly as the repository has it. `--workflow validate` selects `.github/workflows/researchteam-validate.yml`, an opt-in, read-only workflow that runs the bridge validator on pull requests and on pushes to `main`.

> *Source: `researchteam/_workflow_sync.py`*

> **Stability.** This module is underscore-prefixed. The supported interface is the `researchteam` CLI ([CLI reference](../cli-reference.md)); the functions below are documented for contributors and may change between releases.

**Behaviour:**

- The autosync workflow is written at `init` and otherwise only by this command. The validate workflow is written only by this command, when asked for. `researchteam update` and the autosync gate never touch `.github/workflows/`.
- Everything except the top-level `on:` block comes from the scaffold. The `on:` block is kept: schedule present, absent or commented out.
- With no workflow present, the scaffold is written as shipped. For autosync, its weekly schedule is commented out, so autosync runs only when dispatched until the repository turns it on.
- A unified diff is shown first; the command asks before writing unless `--yes` is given, and `--dry-run` writes nothing.
- It refuses a symlinked workflow or parent directory, a non-regular file, a non-UTF-8 file, a file without exactly one block-style top-level `on:` key (for example `on: [push]`), and any column-0 content inside the `on:` block other than comments (a `---` marker, a `- ` item, a `?` key), which would otherwise be carried into the merged file.
- The write goes through a new temporary file (`O_EXCL | O_NOFOLLOW`) and `os.replace`, so it never follows a link. A regular temp file left by an interrupted run is removed first; a temp path that is a link or directory is refused. An existing workflow's permission bits are kept.

---

## Constants

| Name | Value | Purpose |
|------|-------|---------|
| `WORKFLOW` | `".github/workflows/agentteams-sync.yml"` | The derived repository's autosync workflow. |
| `SCAFFOLD` | `"agentteams-sync-derived.yml"` | The packaged scaffold under `researchteam/scaffold/`. |
| `WORKFLOWS` | `{"autosync": Workflow(WORKFLOW, SCAFFOLD, …), "validate": Workflow(".github/workflows/researchteam-validate.yml", "researchteam-validate-derived.yml", …)}` | Each known workflow. `plan` and `run_workflow_sync` take `which`, one of these names, default `"autosync"`. |
| `PRIVILEGED_TRIGGERS` | `("pull_request_target", "workflow_run")` | Triggers the validate workflow may not have: either would run the scripts of an untrusted commit with more than a read-only token. |

---

## Classes

### `Workflow`

A `NamedTuple` for one known workflow: `path` (in the repository), `scaffold` (the packaged file) and `when_absent` (the sentence printed when the workflow does not exist yet).

### `WorkflowSyncError`

A condition under which `workflow-sync` refuses before writing anything.

---

## Functions

### `on_block(text)`

Returns the `(start, end)` line indexes of the top-level `on:` block: from the `on:` line to the next top-level key, leaving out the blank lines and column-0 comments just before that key. Raises `WorkflowSyncError` unless there is exactly one block-style `on:` key (`on:`, `"on":` or `'on':`), or when non-comment column-0 content sits inside the block.

### `merge(scaffold, existing)`

The scaffold with its `on:` block replaced by the existing workflow's `on:` block. Idempotent.

### `load_scaffold(name=SCAFFOLD)`

The packaged scaffold text for `name`, read through `importlib.resources`, so it matches the installed researchteam.

### `plan(root, scaffold=None, which="autosync")`

Returns `(current, proposed)` for the workflow `which` in the repository at `root`; `current` is `None` when no workflow exists. Raises `WorkflowSyncError` for a symlinked path, a non-regular file, a non-UTF-8 file or an unusable `on:` block, and, for `validate`, for an `on:` block that mentions one of `PRIVILEGED_TRIGGERS` outside a comment (as a key, a list item or inside a flow collection). Raises `ValueError` for a name that is not in `WORKFLOWS`.

### `run_workflow_sync(root, yes=False, dry_run=False, which="autosync")`

The command: plan, print the diff, confirm (unless `yes`), write. Returns `0` on success or when there is nothing to do, `1` when it refuses, the operator declines, or the write fails.
