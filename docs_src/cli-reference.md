# CLI Reference

The `researchteam` console script (`researchteam.cli:main`). Every subcommand and flag below is defined in
[`researchteam/cli.py`](https://github.com/jlcatonjr/researchteam/blob/main/researchteam/cli.py); the test
suite fails if this page and the parser drift apart.

```
researchteam [--version] <command> [options]
```

| Command | Description |
|---|---|
| [`init`](#init) | Scaffold a new project from the researchteam template |
| [`update`](#update) | Sync layer-2 managed files from upstream, then run agentteams update |
| [`personalize`](#personalize) | Regenerate project-specific `README.md` and `CLAUDE.md`'s header from `brief.json` |
| [`materialize`](#materialize) | Re-render the agent team from `brief.json` on every agent surface, then re-personalize |
| [`status`](#status) | Show marker info and CLI version |
| [`doctor`](#doctor) | Diagnose researchteam ↔ agentteams toolchain health |

`update`, `personalize` and `materialize` run only inside a derived repo (they walk up from the current directory
for a `.researchteam` marker and exit 1 without one). `status` and `doctor` also work in the upstream repo.

---

## `init`

```
researchteam init [name] [--ref REF] [--remote URL] [--vulnscan-level off|scan]
```

| Option | Default | Meaning |
|---|---|---|
| `name` | current directory | Directory name for the new project |
| `--ref REF` | `main` | Upstream branch, tag or commit (short or full SHA) to scaffold from. A commit must be on `main` or a `release/*` branch (checked with the GitHub API; refused when it cannot be confirmed) and is recorded in full in `.researchteam` |
| `--remote URL` | none | Git remote URL to set as `origin` after init |
| `--vulnscan-level` | `scan` (the scaffold's) | `vulnerability_scanning.level` written into the seeded `brief.json`: `off` or `scan`. `remediate` is an operator choice, made later with `agentteams --set-vulnscan` |

Implementation: [`init`](api-reference/init.md).

---

## `update`

```
researchteam update [--yes] [--dry-run] [--layer2-only | --layer1-only] [--ref REF]
                    [--accept-upstream PATH]... [--no-codex]
```

| Option | Meaning |
|---|---|
| `--yes`, `-y` | Apply all file changes without interactive confirmation (required in CI) |
| `--dry-run` | Show what would change without writing any files |
| `--layer2-only` | Only sync layer-2 files; skip `agentteams --update --merge` |
| `--layer1-only` | Only run the agentteams merge (union descriptor); skip layer-2 file sync. Safe on the upstream repo; used by the auto-integration git hook |
| `--ref REF` | Upstream git ref to fetch from. Default: a release-locked `toolchain.lock`'s verified researchteam tag, else the `.researchteam` marker's `ref`, else `main`. With `--layer1-only` the lock is not consulted (marker ref, else `main`) |
| `--accept-upstream PATH` | Replace this `above-notes` file's part above `## Project-Specific Notes` with upstream's even though the repo customised it (Notes kept, previous file backed up). Repeatable. Without it a customised file is kept, also under `--yes` |
| `--no-codex` | Skip refreshing the Codex surface (`.codex/agents`, `.agents/skills`); for repositories that keep Codex frozen for 1.0 |

When `toolchain.lock` release-locks researchteam but its tag does not verify, `update` refuses (fail closed; it
never falls back to `main`). Pass `--ref` to choose a ref deliberately.

The resolved ref must be a plain branch, tag or commit name; otherwise `update` exits 1 with a message
naming the ref, before fetching anything. A commit ref (other than the verified release-locked one) must be on
researchteam's `main` or a `release/*` branch, because GitHub serves a fork's commits under this repository's URL
too: `update` refuses a commit GitHub says is on neither, and warns and continues when GitHub cannot answer
(offline or rate-limited; a `GITHUB_TOKEN` raises the limit).

Implementation: [`update`](api-reference/update.md).

---

## `personalize`

```
researchteam personalize [--force]
```

| Option | Meaning |
|---|---|
| `--force` | Overwrite generated regions even if they were hand-edited since generation |

Refuses in the upstream repository (`is_upstream = true` in `.researchteam`). Implementation:
[`personalize`](api-reference/personalize.md).

---

## `materialize`

```
researchteam materialize [--yes] [--dry-run] [--copilot-only] [--adopt-orphans]
                         [--discard-user-regions] [--no-codex]
```

| Option | Meaning |
|---|---|
| `--yes`, `-y` | Skip the destructive-overwrite confirmation prompt |
| `--dry-run` | Show what would change without writing any files |
| `--copilot-only` | Re-render only the copilot-vscode surface (`.github/agents`); skip native surfaces |
| `--adopt-orphans` | Keep bespoke agents (no agentteams template) in every surface's roster (passes `agentteams --adopt-orphans`) |
| `--discard-user-regions` | Drop the user-editable `## Project-Specific Notes` / `## Project-Specific Rules` regions instead of carrying them into the re-rendered files (passes `agentteams --discard-user-regions`) |
| `--no-codex` | Skip refreshing the Codex surface after rendering |

Plain `update` merges with `--shrink-policy preserve` and will not re-brand enriched agent bodies; use
`materialize` after a domain or identity change in `brief.json`. Implementation:
[`update`](api-reference/update.md) (`run_materialize`).

---

## `status`

```
researchteam status
```

Prints the CLI version and the contents of the `.researchteam` marker, or a note that none was found.

---

## `doctor`

```
researchteam doctor [--drift]
```

| Option | Meaning |
|---|---|
| `--drift` | Also check drift that needs the network or agentteams: seeded files vs upstream at the pinned commit, and `--bridge-check` per bridge (rewrites the gitignored bridge-check reports) |

Implementation: [`doctor`](api-reference/doctor.md).

---

## `--version`

```
researchteam --version
```

Prints `researchteam <version>`. The version comes from git tags via setuptools-scm.
