# Stale-fact documentation audit (2026-10-20)

Goal: enumerate every evaluable statement of fact in researchteam-owned documentation, verify each
against the repo state (code, scripts, tags, toolchain.lock, CHANGELOG, git history), and revise the
stale ones.

Scope (edited): researchteam-owned docs.
- A: layer-2 framework managed docs (CLAUDE.md managed block, docs/claude-interface-bridge.md,
  docs/agentteams-update-policy.md, docs/agent-infrastructure-authority.md,
  docs/researchteam-framework.md, docs/retrieval-surfaces.md, docs/on-the-fly-retrieval-profile.md,
  .claude/README.md, .claude/checklists/, .claude/prompts/).
- B: scholarly managed protocols (citation-claim-audit, literature-library, news-perspective,
  historical-context).
- C: upstream-only docs (README.md, docs/CONTRIBUTING.md, docs/release-policy.md, .codex/README.md,
  researchteam/scaffold/*.md, CHANGELOG.md verify-only).
- D: dated records (plans, handoffs, open-items, docs/release/*.md, reports/): status lines only;
  superseded state is annotated, history is not rewritten.

Out of scope (agentteams-generated, overwritten on sync): .github/agents, .claude/agents,
.codex/agents, .goose/, .agents/, .claude/skills, AGENTS.md, .claude/CLAUDE.md,
.github/copilot-instructions.md, references/bridges, SETUP-REQUIRED.md,
references/architecture-graph.md. Projects/, tmp/, workSummaries/ are not documentation.

Method: four parallel read-only audits enumerate claims with verdicts; orchestrator applies fixes;
validate; conflict-auditor close.
