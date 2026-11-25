# Bridge Reference

`scripts/claude_researchteam_bridge.sh` is the in-repo command surface for research checks. It is a layer-2
file, so every derived repo carries the same commands.

```
bash scripts/claude_researchteam_bridge.sh <command> [args]
```

An unknown command prints the help and exits 2.

## Repository commands

| Command | What it does |
|---|---|
| `help` | Show the command list |
| `status` | Show git status and the current branch |
| `validate` | Run `scripts/validate_agentteams_update.sh` (with `VALIDATION_SKIP_SCOPE=1`, so general edits outside the update allowlist pass), then every executable file directly in `scripts/validate.d/` in name order, then, when the term-index scripts are present, the term-index core check (`scripts/check_term_core.py`) and the term-index check. `scripts/check_term_index.py`, `scripts/term_index_engine.py`, `scripts/check_term_core.py` and `scripts/term-index-core/PINNED.json` are present together or not at all; a partial set is an error whose message says to upgrade researchteam before `researchteam update`. Fails if any of them fails. `scripts/validate.d/` is repo-owned and never synced |
| `plan-path` | Print the absolute path of the current ISO-week plan directory, `<repo>/tmp/by-week/YYYY-Www` |
| `open-claude-dir` | Print the path to `.claude/` |

## Research checks

These gate compilation of cited deliverables (see [Guides](guides.md)). A clean run means **well-formed**, not
proof of non-fabrication.

| Command | What it does |
|---|---|
| `citation-audit [project] [--bib PATH]` | The 2-fold citation & claim integrity detector (`scripts/check_citation_integrity.sh`): bibliography / URL structural integrity plus an in-text citation-backing signal. A DEFECT (duplicate key, missing title or author/editor, no link, reference without URL, no `.bib`) blocks; NEEDS-REVIEW is advisory. No argument scans all projects |
| `history-check [project]` | The historical-context detector (`scripts/check_historical_context.sh`): every interpretive map needs a `## Historical setting` register whose rows give a date and a basis. Structural only |
| `methodology-check [project]` | The interpretation-advisor methodology-coverage detector (`scripts/check_methodology_coverage.sh`). Exits 1 when a project lacks an interpretive map or a guide it references (warn-only with `METHODOLOGY_COVERAGE_ADVISORY=1`) |

## Term register and index

Coded term definitions per project under `Projects/<project>/terminology/`, with a generated index of
every occurrence. A clean check means **well-formed and current**, not that terms are used in their defined
sense. Codes and the ceiling: the [Term Index protocol](https://github.com/jlcatonjr/researchteam/blob/main/docs/term-index-protocol.md).

| Command | What it does |
|---|---|
| `term-init <project>` | Write a starter register (`scripts/build_term_index.py init`). Never overwrites one |
| `term-build [project]` | (Re)build the index and glossary (`scripts/build_term_index.py build`). No argument rebuilds every project that has a register |
| `term-check [project]` | The gate (`scripts/check_term_index.py`): a DEFECT exits 1. Read-only |
| `term-query <project> "<label, variant or id>"` | List where a registered term occurs (`scripts/query_term_index.py`) |
| `term-core-check` | Check the pinned agentteams term-index core (`scripts/check_term_core.py`) against `scripts/term-index-core/PINNED.json`, offline. `term-build`, `term-check` and `term-query` run the same check before they do anything |

## Position survey

The survey toolkit's first commands (`scripts/survey/`), against the frozen contract
[`docs/survey-toolkit.md`](https://github.com/jlcatonjr/researchteam/blob/main/docs/survey-toolkit.md), version 1.
Each takes a project whose specification is `Projects/<project>/study.json`. They are synced to scholarly-profile
repositories only; without `scripts/survey/` each exits 1 and says to upgrade researchteam. No command verifies a
signature yet: a gate reads `UNCLEARED` (its files changed since its manifest file was written) or `UNAVAILABLE`,
never `CLEARED`. The commands work on the repository the bridge is in; a `--root` argument is refused (exit 2).

| Command | What it does |
|---|---|
| `survey-validate <project>` | Check the specification (every check of section 3, and the path rule), the ledger folder's structure (6.2) and the gates' manifest files. Writes nothing. Exit 1 on any error |
| `survey-status <project>` | Print each gate's manifest hash, state, `enforce` and `mode`, and any reason the gates read `UNAVAILABLE`. A gate reads `CLEARED` only where agentteams 1.3.0 or later verifies its sign-off, and `UNAVAILABLE` without a usable agentteams. Exit 0 whatever the states; 1 only when the specification, a manifest file or the ledger is malformed |
| `survey-manifest <project> <gate>` | Write the gate's manifest into the ledger folder's `references/`, beside the log, and print the scope and action the operator signs. Signs nothing and writes no ledger row |

## Literature library

A per-project, stdlib TF-IDF index over the agents' relevance summaries, under
`Projects/<project>/references/library/`. Records ship UNVERIFIED; similarity is **navigation, not evidence**.

| Command | What it does |
|---|---|
| `library-build <project>` | (Re)build the library (`scripts/build_literature_library.py`) |
| `library-query <project> "<terms>"` | Lexical-similarity candidates (`scripts/query_literature_library.py`) |
| `library-check <project>` | Integrity gate (`scripts/check_literature_library_integrity.sh`): a DEFECT exits 1; no library yet (NEEDS-BUILD) exits 0 |

Script arguments are documented in [`scripts`](api-reference/scripts.md).

## Code & API index

| Command | What it does |
|---|---|
| `code-query "<terms>" [--code-kind K] [--code-query-k N]` | K is `local`, `api`, `doc` or `all`. Ranked candidates for "where is this function / which API does this script call", via `agentteams --query-code … --description brief.json --output .github/agents`. Needs the optional `agentteams` extra on `PATH` (exits 1 without it; exits 2 without a query). Navigation only |
