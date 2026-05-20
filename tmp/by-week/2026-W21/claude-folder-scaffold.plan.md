# Plan: Claude Folder Scaffold

Trigger: User requested planning and development for creating a structured .claude folder alongside CLAUDE.md.

Goal:
- Add a minimal .claude scaffold for reusable Claude-facing project assets.
- Keep CLAUDE.md as top-level entry point and wire cross-links.
- Update bridge script/docs to expose the new location.

Agent Sequence:
1. orchestrator: define scaffold files and create plan artifacts
2. orchestrator: create .claude folder content
3. orchestrator: update existing bridge docs/script to reference .claude assets
4. orchestrator: validate syntax and links
5. orchestrator: summarize deliverables and usage

Success Criteria:
- .claude/ directory exists with practical starter files.
- CLAUDE.md and docs/claude-interface-bridge.md reference .claude content.
- Bridge script includes a simple .claude path helper command.
- Validation checks pass.

Rollback Notes:
- Remove .claude files and revert bridge doc/script references.

Completion: 2026-05-20
