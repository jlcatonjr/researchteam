# `_adopt` — ResearchTeam

Implementation of `researchteam init --adopt` (#59). [`run_init`](init.md) calls it to scaffold the framework into an existing, non-empty directory. It never overwrites a file and never stages or commits.

> *Source: `researchteam/_adopt.py`*

> **Stability.** This module is underscore-prefixed. The supported interface is the `researchteam` CLI ([CLI reference](../cli-reference.md)); the functions below are documented for contributors and may change between releases.

**Invariants:**

- **No existing file is modified**, with one exception. An existing `.gitignore` or `CLAUDE.md` with no `researchteam:managed` fence gets the managed block appended below its unchanged content.
- **No write follows a link.** New files are created with `O_CREAT | O_EXCL | O_NOFOLLOW`, so a path that exists in any form, including a dangling symlink, is refused at the moment of the write. Appends open with `O_NOFOLLOW`. A path under a symlinked or non-directory parent is a conflict and is skipped.
- **Fail before writing.** `preflight` refuses, with nothing written, every input that would otherwise fail part-way. The `.researchteam` marker is written last, so a run that fails anyway can be retried.
- **Git is never staged or committed.** `git init` runs only when the target is not already inside a git work tree. `README.md` and `CLAUDE.md` are rendered only when absent, so `personalize` never rewrites a file that was already there, even one that carries a valid generation marker.

---

## Constants

| Name | Value | Purpose |
|------|-------|---------|
| `ADOPT_APPEND_FENCED` | `(".gitignore", "CLAUDE.md")` | The `fenced-preserve` files (`_manifest.MERGE_STRATEGIES`) that adopt may append the managed block to. Every other existing file is kept as is. |
| `_AGENT_TREES` | `(".github/agents/", ".claude/agents/", ".codex/", ".goose/", ".agentteams/")` | Agent-infrastructure trees that `materialize` / `update` regenerate. A kept or conflicting path under them is reported as at risk. |
| `_KEY_FILES` | `(".researchteam", "brief.json", "README.md", "CLAUDE.md", ".gitignore")` | Files adopt writes or reads outside the archive. Each must be absent or a regular file (`preflight`). |

---

## Classes

### `AdoptError`

> *Source: `researchteam/_adopt.py`*

Subclass of `Exception`. A condition under which adopt refuses before writing anything. `run_adopt` prints `Error: <message>` and `Nothing was written.` to stderr, then exits 1.

### `AdoptReport`

> *Source: `researchteam/_adopt.py`*

What adopt did, recorded in these attributes:
- `added`, `kept`, `appended`, `conflicts`: lists of relative paths. A conflict is a path that adopt left alone: a directory, a symlink, or anything under a non-directory parent.
- `notes`: messages, such as an ignored `--vulnscan-level` or `--remote`, or a skipped nested `git init`.
- `profile`: the brief's `layer2_profile`.

Methods:
- `at_risk()` returns the kept or conflicting paths that a later sync will replace wholesale. These are managed files whose strategy is not `fenced-preserve` (`managed_files_for(profile)`), plus anything under `_AGENT_TREES`.
- `print()` writes the report to stdout. It lists appended files and conflicts first, then a WARNING with the at-risk paths, then the other kept paths and the notes.

---

## Functions

### `run_adopt(target: Path, tarball: bytes, members: set[str], links: list[str], ref: str, remote_url: str | None, vulnscan_level: str | None) -> None`

> *Source: `researchteam/_adopt.py`*

`run_init`'s adopt branch. It calls `populate_adopt` with a new `AdoptReport`, then prints the report.

- On `AdoptError`, it prints the error and `Nothing was written.`, then exits 1.
- On `OSError` or `subprocess.CalledProcessError`, it prints the files added or appended so far, says the marker was not written so a retry is safe, and exits 1.

### `populate_adopt(target: Path, tarball: bytes, members: set[str], links: list[str], ref: str, remote_url: str | None, vulnscan_level: str | None, report: AdoptReport) -> None`

> *Source: `researchteam/_adopt.py`*

1. Run `preflight`.
2. Extract with `_init_cmd._extract(..., adopt=report)`, so each file goes through `adopt_write`. Then write each `INIT_SCAFFOLD_REPLACEMENTS` file the same way.
3. Seed `brief.json` (`_init_cmd._seed_brief`) only if the file is absent; even an existing `{}` is kept. An existing brief is kept, and `vulnscan_level` is then ignored with a note.
4. For each `INIT_RENDER_TEMPLATES` file, render it from `brief.json` if it is absent. If it exists, keep it, or, for an unfenced `CLAUDE.md`, append the rendered managed block.
5. Run `git init` unless the target is inside a git work tree. Inside an enclosing repository (no `.git` of its own), `remote_url` is ignored with a note, so the enclosing repository's remotes are never changed. Otherwise add `remote_url` as `origin` only when there is no `origin` yet.
6. Write the `.researchteam` marker last. If it cannot be created, raise `OSError`, so `run_adopt` exits 1 and does not report success.

### `preflight(target: Path) -> dict`

> *Source: `researchteam/_adopt.py`*

Return the existing `brief.json` as a dict, or `{}` when there is none. It raises `AdoptError` in four cases:
- a `_KEY_FILES` path is a symlink, or exists but is not a regular file;
- `CLAUDE.md` or `.gitignore` is not UTF-8;
- `brief.json` is not valid JSON;
- `brief.json` is not a JSON object.

### `adopt_write(target: Path, rel: str, content: bytes, report: AdoptReport, mode: int = 0) -> None`

> *Source: `researchteam/_adopt.py`*

Write one scaffold file in adopt mode. The first matching case applies:
1. A conflict if `_blocked`.
2. An append for an existing unfenced `ADOPT_APPEND_FENCED` file.
3. Kept if the file exists.
4. Otherwise, created with `O_EXCL | O_NOFOLLOW`, mode `0o755` when `mode` has an execute bit, else `0o644`. A `FileExistsError` there, from a path that appeared or is a dangling link, is recorded as a conflict.

### Private helpers

| Function | Behaviour |
|----------|-----------|
| `_blocked(target: Path, dest: Path) -> bool` | True when `dest` is a directory or symlink, a parent inside `target` is a file or symlink, or `dest` resolves outside `target`. |
| `_append_fenced(dest: Path, rel: str, managed_block: str, report: AdoptReport) -> None` | Opens `dest` with `O_NOFOLLOW` (a link is recorded as a conflict). Appends `managed_block` below the content unless a `researchteam:managed` fence is already present, in which case it is recorded as kept. |

---

## See Also

- [`init.md`](init.md) — `run_init`, `_extract`, `_seed_brief`, `warn_links`.
- [`personalize.md`](personalize.md) — the templates and fence helpers adopt renders with.
- [`manifest.md`](manifest.md) — `MERGE_STRATEGIES`, `managed_files_for`, `INIT_RENDER_TEMPLATES`.
- [`../cli-reference.md`](../cli-reference.md) — `init --adopt`.
