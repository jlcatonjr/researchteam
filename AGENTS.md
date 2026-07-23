<!-- AGENTTEAMS:BEGIN content v=1 -->
# Agent Team (Goose bridge)

<!-- AGENTTEAMS-BRIDGE:BEGIN goose-bridge-entry v=1 -->
Use source framework `copilot-vscode` as canonical agent infrastructure.
Read `references/bridges/copilot-vscode-to-goose/agent-inventory.md` and `references/bridges/copilot-vscode-to-goose/quickstart-snippet.md`.
Start with orchestrator routing.

These two apply to every request in this session, not just project-coordination
work routed through the orchestrator above:
- Before claiming you lack real-time or internet access, try a read-only fetch
  first (`web_scrape` if the `computercontroller` extension is active, otherwise
  a plain `curl`/`wget` via the shell) — don't default to refusal without
  attempting it.
- When a name in the request doesn't exactly match a known entity, resolve to the
  single closest well-known match and proceed confidently — but only when one
  candidate is clearly the best fit (an obvious misspelling or variant). If
  multiple entities are genuinely comparably plausible, say so and ask instead of
  forcing a guess between real alternatives.
<!-- AGENTTEAMS-BRIDGE:END goose-bridge-entry -->
<!-- AGENTTEAMS:END content -->

<!-- AGENTTEAMS:BEGIN project_overview v=1 -->
## Project Overview

**Name:** ResearchTeam
**Goal:** Conduct rigorous scholarly research on any user-specified topic, producing well-structured research reports with verified citations drawn exclusively from established academic repositories (JSTOR, PubMed, SSRN, arXiv, Google Scholar, CrossRef, Semantic Scholar). All claims must be grounded in peer-reviewed or reputable scholarly sources and presented with Chicago bibliography/citation formatting.
**Deliverable type:** Markdown research reports, BibTeX bibliography and Executive summary
**Output format:** Markdown with Chicago citations
<!-- AGENTTEAMS:END project_overview -->

<!-- AGENTTEAMS:BEGIN directory_structure v=1 -->
## Directory Structure

| Path | Purpose |
|------|---------|
| `Projects/` | Primary authored deliverables |
| `output/` | Compiled/converted output artifacts |
| `figures/` | Diagrams and figures |
| `Projects/*/references/bibliography.bib` | Reference/bibliography database |
| `.github/agents/` | Agent definition files |
| `.github/agents/references/` | Shared reference data |
<!-- AGENTTEAMS:END directory_structure -->

<!-- AGENTTEAMS:BEGIN output_conventions v=1 -->
## Output Conventions

- All primary deliverables are authored in `Projects/` as `Markdown research reports, BibTeX bibliography and Executive summary`
- Compiled output lives in `output/` and is **never edited directly**
- Figures are generated from source files in `figures/` — source files are authoritative
- Every deliverable must correspond to a Component Spec defined by a workstream expert
- Work summaries are authored in `workSummaries/` from canonical `tmp/by-week/` plan artifacts, legacy `tmp/` fallbacks, and git history
<!-- AGENTTEAMS:END output_conventions -->

<!-- AGENTTEAMS:BEGIN agent_team v=1 -->
## Agent Team

### Orchestrator
- `@orchestrator` — coordinates all agents; entry point for all user requests

### Governance Agents
- `@navigator` — project structure and file location
- `@security` — destructive operation clearance
- `@code-hygiene` — architecture enforcement and anti-sprawl auditor
- `@adversarial` — presupposition critic
- `@conflict-auditor` — consistency enforcement
- `@conflict-resolution` — ACCEPT/REJECT/REVISE decisions on flagged conflicts
- `@cleanup` — artifact removal
- `@agent-updater` — documentation synchronization
- `@agent-refactor` — spec compliance and reference extraction
- `@repo-liaison` — cross-repository impact tracking and coordination
- `@git-operations` — git/github operations and merge strategy workflow

### Domain Agents
- `@work-summarizer` — synthesizes daily/weekly/monthly work summaries from plan artifacts and git history
- `@primary-producer` — drafts and revises primary deliverables
- `@quality-auditor` — read-only structural and prose quality audit
- `@cohesion-repairer` — repairs within-section cohesion failures
- `@technical-validator` — verifies technical accuracy against authority sources
- `@format-converter` — converts deliverables to final output format
- `@reference-manager` — manages the reference/bibliography database
- `@output-compiler` — assembles components into the final deliverable package
- `@visual-designer` — creates and revises diagrams and figures
- `@interpretation-advisor` — specialized domain agent
- `@retrieval-integrator` — validates retrieval query, maintenance, and trigger contracts
- `@tool-doc-researcher` — specialized domain agent

### Workstream Experts
- `@topic-scoping-expert` — Topic Scoping and Research Plan
- `@literature-review-expert` — Literature Review
- `@main-analysis-expert` — Main Analysis
- `@conclusion-expert` — Conclusion and Executive Summary
<!-- AGENTTEAMS:END agent_team -->

<!-- AGENTTEAMS:BEGIN tone_and_style v=1 -->
## Tone and Style

Default to terse output for read-only auditor and governance roles
(`@security`, `@adversarial`, `@code-hygiene`, `@conflict-auditor`,
`@navigator`, `@quality-auditor`, `@technical-validator`,
`@post-production-auditor`, `@module-doc-validator`,
`@reference-manager` in read mode): respond in ≤200 words unless
the task requires longer output. Producing roles
(`@primary-producer`, `@module-doc-author`, `@content-enricher`,
`@output-compiler`, `@orchestrator` when summarizing a multi-step
session) emit the deliverable in full and are exempt from this
default.

Terse mode reduces consumer-harness token consumption on the
common case of audit-and-route turns. Producing roles override the
default explicitly by saying so in their first line.
<!-- AGENTTEAMS:END tone_and_style -->

<!-- AGENTTEAMS:BEGIN authority_hierarchy v=1 -->
## Authority Hierarchy

1. **Project source files** — ground truth for all technical claims
<!-- AGENTTEAMS:END authority_hierarchy -->

<!-- AGENTTEAMS:BEGIN source_repositories v=1 -->
## Source Repositories

- Project source files (read-only)
<!-- AGENTTEAMS:END source_repositories -->
