# Claude Interface Bridge for ResearchTeam

This file is the operating bridge for Claude users working in this repository.

## Project Purpose

ResearchTeam produces structured, source-grounded research deliverables in markdown with Chicago-style citations.

Primary outputs:
- Research reports in `Projects/` and/or `reports/`
- Bibliography data in `references/` (and project-local `references/` subfolders)
- Governance and execution plans in `tmp/by-week/`

## Working Rules

1. Keep claims traceable to explicit sources.
2. Do not fabricate references.
3. Preserve existing file structure and naming conventions.
4. For multi-step work, create a plan and step CSV in `tmp/by-week/YYYY-Www/`.
5. Prefer non-destructive changes unless explicitly requested.

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
```

## Standard Workflow

1. Inspect current repo state with `status`.
2. Create/update plan artifacts in `tmp/by-week/` for multi-step edits.
3. Edit target files.
4. Run `validate`.
5. Commit and push when requested.

## Key Paths

- Main Zelda guide: `Projects/ZeldaTimeline/ZeldaTimelineResearchGuide.html`
- Zelda summary: `Projects/ZeldaTimeline/ZeldaTimelineSummary.html`
- Agent infrastructure: `.github/agents/`
- CI workflow: `.github/workflows/agentteams-sync.yml`
- Bridge docs: `docs/claude-interface-bridge.md`

## Notes for Claude Users

- If running outside a git worktree context, some validation checks may be reduced.
- The repository includes archived agent backup trees under `.github/agents/.agentteams-backups/`; do not treat backups as active source-of-truth.
