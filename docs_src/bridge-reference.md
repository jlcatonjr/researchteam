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
| `validate` | Run `scripts/validate_agentteams_update.sh` (with `VALIDATION_SKIP_SCOPE=1`, so general edits outside the update allowlist pass), then every executable file directly in `scripts/validate.d/` in name order. Fails if any of them fails. `scripts/validate.d/` is repo-owned and never synced |
| `plan-path` | Print the current ISO-week plan directory, `tmp/by-week/YYYY-Www` |
| `open-claude-dir` | Print the path to `.claude/` |

## Research checks

These gate compilation of cited deliverables (see [Guides](guides.md)). A clean run means **well-formed**, not
proof of non-fabrication.

| Command | What it does |
|---|---|
| `citation-audit [project] [--bib PATH]` | The 2-fold citation & claim integrity detector (`scripts/check_citation_integrity.sh`): bibliography / URL structural integrity plus an in-text citation-backing signal. A DEFECT (duplicate key, missing title or author, no link, reference without URL, no `.bib`) blocks; NEEDS-REVIEW is advisory. No argument scans all projects |
| `history-check [project]` | The historical-context detector (`scripts/check_historical_context.sh`): every interpretive map needs a `## Historical setting` register whose rows give a date and a basis. Structural only |
| `methodology-check [project]` | The interpretation-advisor methodology-coverage detector (`scripts/check_methodology_coverage.sh`). Advisory: surfaces projects missing an interpretive map or guide |

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
| `code-query "<terms>" [--code-kind local\|api\|doc\|all] [--code-query-k N]` | Ranked candidates for "where is this function / which API does this script call", via `agentteams --query-code … --description brief.json --output .github/agents`. Needs the optional `agentteams` extra on `PATH` (exits 1 without it; exits 2 without a query). Navigation only |
