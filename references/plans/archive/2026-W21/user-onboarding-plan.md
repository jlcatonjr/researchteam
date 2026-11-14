# ResearchTeam Repository — User Onboarding Plan

## 1. Entry Point and Documentation
- Add a top-level README.md with:
  - Project purpose and outputs
  - Quick start instructions (clone, bridge script, agent workflow)
  - Directory structure summary
  - How to update agent infrastructure safely
  - Where to find further docs (CLAUDE.md, .claude/README.md, docs/)

## 2. Installability and Usage
- No pip/npm install needed; this is a research workflow repo, not a library.
- Users operate via scripts (e.g., scripts/claude_researchteam_bridge.sh) and agent workflows.
- Document how to update agent infrastructure using agentteams (with CI/CD safety).

## 3. Update Safety and Customization
- User research and agent customizations are preserved outside AGENTTEAMS fenced regions.
- CI/CD and validation scripts prevent accidental overwrites.
- Document how to safely merge upstream agentteams updates.

## 4. Support for Claude and Copilot Users
- Entry docs for both Claude (CLAUDE.md, .claude/) and Copilot (copilot-instructions.md).
- Bridge script and checklists for Claude users.

## 5. Next Steps
- Draft README.md as a clear, actionable entry point.
- Reference all key docs and scripts for onboarding.
- Encourage users to read docs/agentteams-update-policy.md and docs/agent-infrastructure-authority.md before updating agents.
