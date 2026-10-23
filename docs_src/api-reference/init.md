# `_init_cmd` — ResearchTeam

Implementation of `researchteam init`. `run_init` scaffolds a new derived repository from the upstream researchteam template: it checks the requested ref, downloads and validates a GitHub archive tarball of it before creating anything, extracts it while skipping the paths that a derived repo must not inherit, replaces the CI workflow with the bundled derived-repo version, seeds a placeholder `brief.json`, writes the `.researchteam` marker, renders the project-specific `README.md` and `CLAUDE.md` through [`personalize`](personalize.md), and makes an initial git commit.

> *Source: `researchteam/_init_cmd.py`*

> **Stability.** This module is underscore-prefixed. The supported interface is the `researchteam` CLI ([CLI reference](../cli-reference.md)); the functions below are documented for contributors and may change between releases.

---

## Constants

| Name | Value | Purpose |
|------|-------|---------|
| `_MARKER_TEMPLATE` | `"[researchteam]\nupstream = https://github.com/{repo}\nref = {ref}\nis_upstream = false\n"` | Contents of the `.researchteam` marker written by `init`. `is_upstream = false` is always written explicitly; the personalize and materialize guards refuse only when `is_upstream` reads as `true` (see [`is_upstream`](personalize.md#is_upstreamroot-path-bool)), which `init` never writes. |
| `_HEX` | compiled regex `^[0-9a-f]{7,40}$` | A `ref` that may be a commit (short or full SHA). |
| `_FULL_SHA` | compiled regex `^[0-9a-f]{40}$` | A full commit SHA, as found at the end of the archive's top directory name. |

`run_init` also uses `UPSTREAM_REPO`, `INIT_SKIP_PREFIXES` and `INIT_SCAFFOLD_REPLACEMENTS` from [`_manifest`](manifest.md).

---

## Classes

### `ArchiveError`

> *Source: `researchteam/_init_cmd.py`*

Subclass of `Exception`. An upstream archive `init` will not extract: unreadable, a member path that could escape the target, or not exactly one top-level directory. Raised by `_validate_archive`; `run_init` turns it into exit 1 before anything is created.

---

## Functions

### `run_init(name: str | None, ref: str, remote_url: str | None) -> None`

> *Source: `researchteam/_init_cmd.py`*

Scaffold a new project. The CLI calls it as `run_init(args.name, args.ref, args.remote)`; the CLI default for `ref` is `UPSTREAM_BRANCH` (`"main"`).

**Args:**

- `name` (`str | None`) — Directory to create the project in. When given, it is resolved to an absolute path; it must either not exist or be an empty directory, and is created with `mkdir(parents=True, exist_ok=True)` only after the archive has been downloaded and validated. When `None`, the current working directory is used and must be empty.
- `ref` (`str`) — Upstream git ref to scaffold from: a branch, tag, or commit (short or full SHA). It must pass [`_drift.is_safe_ref`](drift.md#is_safe_refref). It is passed to [`fetch_tarball`](fetch.md), which tries the branch archive, then the tag archive, then (for a hex `ref`) the commit archive. It is recorded as `ref = …` in the marker; a hex `ref` is recorded as the full commit SHA when the archive's top directory (`<repo>-<sha>`) ends in a 40-character SHA that starts with `ref`.
- `remote_url` (`str | None`) — When set, added as the `origin` remote after the initial commit.

**Steps, in order:**

1. Check `ref` with `is_safe_ref`.
2. Validate the target directory (see Args). Nothing is created yet.
3. Download `UPSTREAM_REPO` at `ref` with `fetch_tarball`, and check the whole archive with `_validate_archive`.
4. For a hex `ref`, replace it with the full commit SHA taken from the archive's top directory (see Args), then
   require [`_fetch.commit_is_reviewed`](fetch.md#commit_is_reviewedrepo-str-sha-str-bool-none) to return `True`.
   GitHub serves a fork's commits under this repository's URL, so a commit must be on `main` or a `release/*`
   branch. Branch and tag names skip this step.
5. Create the `name` directory, if given, and print where the project is being initialized.
6. Call `_populate`, which runs the remaining steps:
    1. Warn on stderr if the archive held link members (`skipped N link member(s) in the archive: …`, at most five named); they are not extracted.
    2. Extract the accepted members with `_extract`.
    3. Overwrite paths listed in `INIT_SCAFFOLD_REPLACEMENTS` with bundled scaffold files (`_apply_scaffold_replacements`).
    4. Write `brief.json` from `scaffold/brief.template.json` (`_seed_brief`).
    5. Write `.researchteam` from `_MARKER_TEMPLATE`. This happens before personalize because the `is_upstream` guard reads it.
    6. Call `run_personalize(target, force=True, quiet=False)` to render `README.md` and `CLAUDE.md`.
    7. Run `git init`, `git add -A`, and `git commit -m "chore: initialize from researchteam template"` in the target (each with `check=True`, output captured).
    8. If `remote_url` is set, run `git remote add origin <remote_url>`.
7. Print next steps: edit `brief.json`, `researchteam personalize`, `researchteam materialize`, plus a note that strict decision signing is on and `materialize` needs one operator-signed clearance first (via [`scripts/sign_security_decision.py`](scripts.md#sign_security_decisionpy)).

**Returns:** `None`.

**Exit behaviour:**

- Prints `Error: --ref '<ref>' is not a plain branch, tag or commit name.` to stderr and calls `sys.exit(1)` when `ref` fails `is_safe_ref`.
- Prints an error to stderr and calls `sys.exit(1)` if `name` exists and is not an empty directory, or if `name` is `None` and the current directory is not empty.
- Prints `Error: commit <sha> is not on main or a release branch of …` (or `could not be confirmed to be on …`
  when GitHub cannot answer) and calls `sys.exit(1)` for a commit `ref` that is not reviewed history. Nothing
  has been created.
- Prints `Error: <message>` to stderr and calls `sys.exit(1)` when `fetch_tarball` raises `RuntimeError` or `_validate_archive` raises `ArchiveError`. No directory has been created at that point.
- After the directory is created, an `OSError` or `subprocess.CalledProcessError` from `_populate` is printed as `[researchteam] init failed: <exc>` followed by a line saying the project at the target is incomplete and to remove it (when `init` created the directory) or the files written there (when it already existed) before retrying; then `sys.exit(1)`. Nothing is deleted.
- A `SystemExit` raised by `run_personalize` is re-raised unchanged. Any other exception from personalize is printed as `[researchteam] init failed while personalizing: …` and ends with `sys.exit(1)`.

---

### `_populate(target: Path, tarball: bytes, members: set[str], links: list[str], ref: str, remote_url: str | None) -> None`

> *Source: `researchteam/_init_cmd.py`*

Write the checked archive into `target`, then the scaffold files, `brief.json`, the marker, the identity files and the git repository: sub-steps 6.1–6.8 of `run_init` above. `members` and `links` are the first two values returned by `_validate_archive`; `ref` is the value recorded in the marker.

**Raises:** `OSError` (including from `_extract`) and `subprocess.CalledProcessError` (a git command failed); `run_init` reports both.

---

### `_validate_archive(tarball: bytes) -> tuple[set[str], list[str], str]`

> *Source: `researchteam/_init_cmd.py`*

Check the whole archive before anything is written.

**Returns:** `(members, links, top)` — the member names (full archive paths) of the regular files and directories to write; the paths (top directory stripped) of the symlink and hard-link members that will be skipped; and the archive's single top-level directory name (for example `researchteam-main` or `researchteam-<sha>`). The top directory itself, paths for which `_should_skip` is true, and other member types are left out of both lists.

**Raises:** `ArchiveError` —

- `"the template archive cannot be read (<exc>)"` when `tarfile` cannot open or list it (`TarError`, `OSError`, `EOFError`);
- `"the template archive has an unsafe member path '<name>'; refusing it"` when any member is absolute, has a `..` segment, or starts with `\`. The whole archive is refused: the upstream archive never contains such a member, so it indicates tampering;
- `"the template archive has <n> top-level directories, expected 1"`.

It does not rely on `tarfile`'s `filter=` argument (absent before Python 3.10.12).

---

### `_extract(tarball: bytes, target: Path, members: set[str]) -> None`

> *Source: `researchteam/_init_cmd.py`*

Write the members `_validate_archive` accepted into `target`. Members whose name is not in `members` are not written. Each destination is `target / _rel(name)`, resolved; it must lie inside the resolved `target`, or `OSError("archive member '<name>' resolves outside <root>")` is raised. Directories are created; regular files are written byte-for-byte, and if any execute bit is set on the member, execute bits are added to the written file.

---

### Private helpers

| Function | Behaviour |
|----------|-----------|
| <code>_rel(name: str) -&gt; str &#124; None</code> | A member's path with the archive's top directory stripped (POSIX `/`-joined); `None` for the top directory itself. |
| `_should_skip(rel_path: str) -> bool` | True when `rel_path` equals an `INIT_SKIP_PREFIXES` entry (trailing `/` stripped) or starts with that entry followed by `/`. |
| `_seed_brief(target: Path) -> None` | Copies the bundled `researchteam/scaffold/brief.template.json` to `target/brief.json`. The framework's own `brief.json` is excluded on extract. |
| `_apply_scaffold_replacements(target: Path) -> None` | For each `dest → scaffold_name` in `INIT_SCAFFOLD_REPLACEMENTS`, creates the parent directory and writes the bundled `researchteam/scaffold/<scaffold_name>` to `target/<dest>`. |

---

## See Also

- [`index.md`](index.md) — API reference overview.
- [`cli.md`](cli.md) — CLI entry point that dispatches `init`.
- [`personalize.md`](personalize.md) — renders `README.md` / `CLAUDE.md` during `init`.
- [`manifest.md`](manifest.md) — `INIT_SKIP_PREFIXES`, `INIT_SCAFFOLD_REPLACEMENTS`, `UPSTREAM_REPO`.
- [`fetch.md`](fetch.md) — `fetch_tarball`.
- [`update.md`](update.md) — keeping a scaffolded repo current.
- [`doctor.md`](doctor.md) — toolchain health check.
- [`scripts.md`](scripts.md) — `sign_security_decision.py`, referenced in the next-steps output.
- [`../cli-reference.md`](../cli-reference.md) — command-line reference.
