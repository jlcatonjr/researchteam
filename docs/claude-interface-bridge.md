# Claude Interface Bridge

This document explains how Claude users can operate the ResearchTeam repository consistently.

## Bridge Components

1. Root guidance: `CLAUDE.md`
2. Command bridge: `scripts/claude_researchteam_bridge.sh`
3. Claude support folder: `.claude/`
4. Existing validator: `scripts/validate_agentteams_update.sh`

## Prerequisites

- Bash shell
- Local clone of this repository
- Optional: git initialized and authenticated for push workflows

## Usage

From repository root:

```bash
bash scripts/claude_researchteam_bridge.sh help
```

### Status

```bash
bash scripts/claude_researchteam_bridge.sh status
```

Shows branch, short HEAD hash, and concise working-tree status.

### Validation

```bash
bash scripts/claude_researchteam_bridge.sh validate
```

Runs `scripts/validate_agentteams_update.sh`.

### Reader and Summary Paths

```bash
bash scripts/claude_researchteam_bridge.sh open-reader
bash scripts/claude_researchteam_bridge.sh open-summary
bash scripts/claude_researchteam_bridge.sh open-claude-dir
```

### Claude Support Folder

The `.claude/` folder contains:

- `README.md` with usage notes
- `prompts/research-report.prompt.md` starter prompt template
- `checklists/research-task-preflight.md` checklist for multi-step work

### Weekly Plan Directory

```bash
bash scripts/claude_researchteam_bridge.sh plan-path
```

Returns the current `tmp/by-week/YYYY-Www/` path.

## Recommended Claude Workflow

1. Run `status`.
2. For multi-step tasks, create plan artifacts in current weekly directory.
3. Perform edits.
4. Run `validate`.
5. Commit/push if requested.

## Notes

- Active source-of-truth agent files are in `.github/agents/`.
- Backup snapshots in `.github/agents/.agentteams-backups/` are archival.
- The main Zelda human-facing guide is:
  - `Projects/ZeldaTimeline/ZeldaTimelineResearchGuide.html`
- Keep `CLAUDE.md` as the top-level entry point and `.claude/` as structured support content.
