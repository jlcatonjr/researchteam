# Claude Workspace Folder

This folder contains Claude-specific support assets for the ResearchTeam repository.

Design intent:
- Keep `CLAUDE.md` as the root entry point.
- Store reusable Claude templates and checklists here.
- Keep these files lightweight and repository-specific.

## Contents

- `prompts/research-report.prompt.md`: Prompt template for creating a new report draft.
- `checklists/research-task-preflight.md`: Preflight checklist before editing deliverables.

## Usage

1. Start with `CLAUDE.md` at repository root.
2. Use the bridge script for status, validation, and navigation:
   ```bash
   bash scripts/claude_researchteam_bridge.sh help
   ```
3. Copy relevant template sections from this folder.
4. Follow validation and planning requirements before major edits.
