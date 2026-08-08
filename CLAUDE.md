# Claude Interface Bridge for ResearchTeam

This file is the operating bridge for Claude users working in this repository.

## Project Purpose

ResearchTeam produces structured, source-grounded research deliverables in markdown with Chicago-style citations.

Primary outputs:
- Research reports in `Projects/` and/or `reports/`
- Bibliography data in project-local `Projects/*/references/bibliography.bib` files (with optional non-bibliography registries under `references/`)
- Governance and execution plans in `tmp/by-week/`

## Working Rules

1. Keep claims traceable to explicit sources.
2. Do not fabricate references.
3. Preserve existing file structure and naming conventions.
4. For multi-step work, create a plan and step CSV in `tmp/by-week/YYYY-Www/`.
5. Prefer non-destructive changes unless explicitly requested.
6. When a project is initiated or developed, run the 2-fold citation & claim audit before
   compiling — `bash scripts/claude_researchteam_bridge.sh citation-audit <project>` (mechanical
   layer), then the doubled semantic audit in `docs/citation-claim-audit-protocol.md`. Unresolved
   citation/claim findings block compilation (fail-closed). A clean run means WELL-FORMED, not
   proof of non-fabrication.

## Quick Start

Run the bridge helper:

```bash
bash scripts/claude_researchteam_bridge.sh help
```

Common commands:

```bash
bash scripts/claude_researchteam_bridge.sh status
bash scripts/claude_researchteam_bridge.sh validate
bash scripts/claude_researchteam_bridge.sh open-reader
bash scripts/claude_researchteam_bridge.sh open-summary
bash scripts/claude_researchteam_bridge.sh open-claude-dir
```

## Standard Workflow

1. Inspect current repo state with `status`.
2. Create/update plan artifacts in `tmp/by-week/` for multi-step edits.
3. Edit target files.
4. Run `validate`.
5. Commit and push when requested.

## Key Paths

- Active projects: `Projects/`
- Agent infrastructure: `.github/agents/`
- CI workflow: `.github/workflows/agentteams-sync.yml`
- Bridge docs: `docs/claude-interface-bridge.md`
- Authority map: `docs/agent-infrastructure-authority.md`
- Claude support folder: `.claude/`

## Keeping Infrastructure Current

This repository is pip-installable. If you are working in a derived project (not the upstream repo), keep layer-2 infrastructure files current with:

```bash
researchteam update          # interactive — shows diffs before applying
researchteam update --yes    # non-interactive (CI-safe)
researchteam update --dry-run  # preview only
```

`researchteam update` syncs `docs/`, `scripts/`, `.claude/`, `CLAUDE.md`, and `README.md` from the upstream template, then runs `agentteams --update --merge` for agent infrastructure. It never touches `brief.json`, `Projects/`, or `references/`.

### Installing the toolchain (agents: verify this before relying on either tool)

`researchteam` is the entry point. `agentteams` is **installed through it as an extra**, never on
its own — it is not published to PyPI, so the base install deliberately declares
`dependencies = []` and a bare `pip install researchteam` leaves layer-1 agent regeneration
unavailable.

```bash
# base CLI only — layer-2 file sync, no agent regeneration
pip install "git+https://github.com/jlcatonjr/researchteam.git"

# recommended — pulls agentteams in, enabling `researchteam update`'s layer-1 pass
pip install "researchteam[update] @ git+https://github.com/jlcatonjr/researchteam.git"

# adds agentteams' research extra (web search, curated-source rating, claim verification)
pip install "researchteam[research] @ git+https://github.com/jlcatonjr/researchteam.git"
```

Agents must not assume the toolchain is present, and must not assume that an `agentteams` found on
`PATH` belongs to the interpreter they are running under. Check both:

```bash
python -m pip show researchteam agentteams   # both must resolve in the ACTIVE interpreter
which researchteam agentteams                # both should sit in that same environment
python -c "import sys; print(sys.prefix)"    # the environment those two must belong to
```

Act on the result as follows:

- **`researchteam` missing** — ask the user to install it with a command above. Do not hand-edit
  generated agent infrastructure as a workaround.
- **`researchteam` present, `agentteams` missing** — ask the user to install the `update` extra.
  Do **not** `pip install agentteams` standalone; routing it through the extra is what keeps the
  two pinned to a compatible pair in one environment.
- **`agentteams` resolves from a different environment than `sys.prefix`** — treat the toolchain
  as unavailable and say so. This is the failure mode worth naming explicitly: `researchteam
  update` shells out to whatever `agentteams` `PATH` resolves, so a binary belonging to an
  unrelated interpreter will happily regenerate agent files at the wrong version, and nothing in
  the output announces the mismatch.
- **Neither available** — report the drift and stop. Editing `.github/agents/**` by hand is not a
  substitute; those files are generated and the next sync discards the edit.

## Notes for Claude Users

- If running outside a git worktree context, some validation checks may be reduced.
- The repository includes archived agent backup trees under `.github/agents/.agentteams-backups/`; do not treat backups as active source-of-truth.
- Do not manually edit AGENTTEAMS fenced sections in agent docs. Route multi-file agent changes through orchestrated workflows.
- Back up research and agent files before update or merge runs.
- Use `.claude/README.md` for reusable templates and preflight checklists.
