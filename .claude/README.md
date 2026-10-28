# Claude Workspace Folder

This folder contains Claude-specific support assets for the ResearchTeam repository.

Design intent:
- Keep `CLAUDE.md` as the root entry point.
- Store reusable Claude templates and checklists here.
- Keep these files lightweight and repository-specific.

## Contents

- `prompts/research-report.prompt.md`: Prompt template for creating a new report draft.
- `checklists/research-task-preflight.md`: Preflight checklist before editing deliverables.
- `settings.toolchain.example.json`: SessionStart toolchain check; merge it into `settings.json` by hand.

agentteams generates the rest of this folder (`agents/`, `skills/`, `hooks/`, `hook-guard.sh`,
`agent-team.md`, `quickstart-snippet.md`, `CLAUDE.md`, `schedules.agentteams.json`, and the other
`settings.*.example.json` files). Do not hand-edit those; the next sync overwrites them.

## Usage

1. Start with `CLAUDE.md` at repository root.
2. Use the bridge script for status, validation, and navigation:
   ```bash
   bash scripts/claude_researchteam_bridge.sh help
   ```
3. Copy relevant template sections from this folder.
4. Follow validation and planning requirements before major edits.
