# ResearchTeam

Conduct rigorous, source-grounded scholarly research with agent-based workflows and robust update safety.

## What is ResearchTeam?
ResearchTeam is a framework for producing well-structured research reports with verified citations, using agent-based workflows. All claims are grounded in peer-reviewed or reputable scholarly sources, with Chicago-style citations. The repository is designed for safe updates and user customization.

## Quick Start
1. **Clone the repository:**
   ```bash
   git clone https://github.com/jlcatonjr/researchteam.git
   cd researchteam
   ```
2. **For Claude users:**
   - See `CLAUDE.md` and run:
     ```bash
     bash scripts/claude_researchteam_bridge.sh help
     ```
   - Use `.claude/README.md` for templates and checklists.
3. **For Copilot/agentteams users:**
   - See `.github/copilot-instructions.md` for agent governance and workflow details.
   - All agent files are in `.github/agents/`.

## Directory Structure
| Path                          | Purpose                                    |
|-------------------------------|--------------------------------------------|
| `Projects/`                   | Primary research deliverables (active)     |
| `reports/`                    | Optional deliverables path (create if needed) |
| `references/`                 | Registry, plans, and shared references      |
| `tmp/by-week/`                | Weekly plan and steps artifacts             |
| `.github/agents/`             | Agent infrastructure and governance        |
| `.github/agents/references/`  | Shared reference data for agents           |
| `.claude/`                    | Claude-specific templates and checklists   |
| `scripts/`                    | Helper scripts (bridge, validation)        |
| `docs/`                       | Policy and bridge documentation            |


## Agent Workflows and Orchestrator

### Orchestrator Agent
The orchestrator agent is the entry point for all agent-based workflows. It coordinates requests, enforces constitutional rules, and ensures every multi-file session closes with a consistency check. All agent operations (writing, updating, auditing) are routed through the orchestrator for safety and traceability. **Do not bypass the orchestrator or invoke agents directly, except for the Team Builder bootstrap flow used to generate/regenerate an agent team.**

### Agent Roles
- **Orchestrator:** Coordinates all agent operations and workflow routing.
- **Domain Agents:** Specialized for research, writing, validation, reference management, and more. See `.github/copilot-instructions.md` for the full agent team list and roles.
- **Note on topology:** `.github/agents/references/pipeline-graph.md` is auto-generated from `build_team.py`. Agents declared in `copilot-instructions.md` but not yet wired into `build_team.py` (e.g., `@work-summarizer`, `@git-operations`) will not appear in the graph until the build system is updated.
- **Claude vs. Copilot/agentteams:**
  - *Claude users* use the bridge in `CLAUDE.md` and `.claude/README.md`.
  - *Copilot/agentteams users* follow `.github/copilot-instructions.md` and use `.github/agents/`.
  - Choose the workflow that matches your platform and follow the onboarding steps below.

### Fenced Regions
Fenced regions are special code or text blocks in files that are managed by agents. **Do not edit inside fenced regions manually.** User-authored content outside these regions is preserved during updates. Editing inside fenced regions or agent files can cause data loss or workflow errors.

## Onboarding and Safety Checklist
1. **Choose your workflow:** Claude or Copilot/agentteams (see above).
2. **Read the relevant onboarding docs:** `CLAUDE.md`, `.claude/README.md`, or `.github/copilot-instructions.md`.
3. **Run validation scripts:** Use `scripts/validate_agentteams_update.sh` before and after agent-infrastructure update/merge changes.
4. **Backup your work:** Regularly copy your research and agent files outside the repo for safety.
5. **Avoid editing agent files or fenced regions manually.**
6. **If a session is interrupted or a consistency check fails:**
   - Review the logs and validation output.
   - Restore from backup if needed.
   - See `docs/agent-infrastructure-authority.md` for escalation and recovery steps.

## Updating Agent Infrastructure
- Use the provided CI/CD workflow and validation scripts for safe updates.
- See `docs/agentteams-update-policy.md` and `scripts/validate_agentteams_update.sh` for update/merge safety.
- User-authored research and customizations **outside AGENTTEAMS fenced regions** are preserved. **Editing inside fenced regions or agent files is risky and may cause data loss.**

## Key Docs
- `CLAUDE.md` — Claude user bridge and workflow
- `.claude/README.md` — Claude templates/checklists
- `.github/copilot-instructions.md` — Copilot/agent governance
- `.github/agents/references/pipeline-graph.md` — Agent team topology (auto-generated)
- `docs/agentteams-update-policy.md` — Update/merge policy
- `docs/agent-infrastructure-authority.md` — Path authority map


## FAQ
- **Is this a pip/npm package?**
  - No. This is a research workflow repo, not a library. No install step is needed, but you may need to install dependencies for scripts or agent execution (see onboarding docs).
- **How do I keep my research safe during updates?**
  - All user-authored content outside fenced regions is preserved. CI/CD and validation scripts help prevent accidental overwrites, but always keep backups and avoid editing inside fenced regions.
- **What are fenced regions?**
  - Fenced regions are agent-managed blocks in files. Do not edit inside them. See above for details.
- **Where do I start?**
  - Read this README, then see `CLAUDE.md` or `.github/copilot-instructions.md` depending on your workflow.
- **What if something goes wrong?**
  - Review logs and validation output, restore from backup if needed, and see `docs/agent-infrastructure-authority.md` for recovery steps.

---

For more, see the `docs/` folder and in-repo help scripts.
