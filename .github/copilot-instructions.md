<!--
SECTION MANIFEST — copilot-instructions.template.md
| section_id            | designation   | notes                                    |
|-----------------------|---------------|------------------------------------------|
| project_overview      | FENCED        | Name, goal, deliverable type, output fmt |
| directory_structure   | FENCED        | Path/purpose table                       |
| output_conventions    | FENCED        | Authoring and build conventions          |
| agent_team            | FENCED        | Full agent team list                     |
| authority_hierarchy   | FENCED        | Source hierarchy list                    |
| source_repositories   | FENCED        | Authority source entries                 |
| constitutional_rules  | USER-EDITABLE | Project may extend or customise          |
| style_rules           | USER-EDITABLE | Project may extend or customise          |
-->

# ResearchTeam — Copilot Instructions

> This file defines the conventions, authority hierarchy, and agent team structure for all GitHub Copilot agents in ResearchTeam.

---

<!-- AGENTTEAMS:BEGIN project_overview v=1 -->
## Project Overview

**Name:** ResearchTeam
**Goal:** Conduct rigorous scholarly research on any user-specified topic, producing well-structured research reports with verified citations drawn exclusively from established academic repositories (JSTOR, PubMed, SSRN, arXiv, Google Scholar, CrossRef, Semantic Scholar). All claims must be grounded in peer-reviewed or reputable scholarly sources and presented with Chicago bibliography/citation formatting.
**Deliverable type:** Markdown research reports, BibTeX bibliography and Executive summary
**Output format:** Markdown with Chicago citations
<!-- AGENTTEAMS:END project_overview -->

---

<!-- AGENTTEAMS:BEGIN directory_structure v=1 -->
## Directory Structure

| Path | Purpose |
|------|---------|
| `reports/` | Primary authored deliverables |
| `output/` | Compiled/converted output artifacts |
| `figures/` | Diagrams and figures |
| `references/bibliography.bib` | Reference/bibliography database |
| `.github/agents/` | Agent definition files |
| `.github/agents/references/` | Shared reference data |
<!-- AGENTTEAMS:END directory_structure -->

---

<!-- AGENTTEAMS:BEGIN output_conventions v=1 -->
## Output Conventions

- All primary deliverables are authored in `reports/` as `Markdown research reports, BibTeX bibliography and Executive summary`
- Compiled output lives in `output/` and is **never edited directly**
- Figures are generated from source files in `figures/` — source files are authoritative
- Every deliverable must correspond to a Component Spec defined by a workstream expert
- Work summaries are authored in `workSummaries/` from canonical `tmp/by-week/` plan artifacts, legacy `tmp/` fallbacks, and git history
<!-- AGENTTEAMS:END output_conventions -->

---

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
- `@tool-doc-researcher` — specialized domain agent

### Workstream Experts
- `@topic-scoping-expert` — Topic Scoping and Research Plan
- `@literature-review-expert` — Literature Review
- `@main-analysis-expert` — Main Analysis
- `@conclusion-expert` — Conclusion and Executive Summary
<!-- AGENTTEAMS:END agent_team -->

---

<!-- AGENTTEAMS:BEGIN authority_hierarchy v=1 -->
## Authority Hierarchy

1. **JSTOR** (`https://www.jstor.org`) — humanities and social science peer-reviewed articles
1. **PubMed / MEDLINE** (`https://pubmed.ncbi.nlm.nih.gov`) — biomedical and life-science literature
2. **arXiv** (`https://arxiv.org`) — preprints in STEM fields
2. **SSRN** (`https://ssrn.com`) — economics, law, and social science working papers
2. **Semantic Scholar** (`https://www.semanticscholar.org`) — cross-disciplinary scholarly literature discovery and metadata
3. **CrossRef** (`https://www.crossref.org`) — DOI resolution and bibliographic metadata verification
3. **Google Scholar** (`https://scholar.google.com`) — broad academic literature discovery and citation counts
<!-- AGENTTEAMS:END authority_hierarchy -->

---

## Constitutional Rules

1. **Security first** — destructive operations require `@security` clearance
2. **Code hygiene second** — code changes require `@code-hygiene` audit before merge
3. **Authority hierarchy is ground truth** — no agent may contradict a higher-authority source
4. **Primary deliverables are the canonical output** — build artifacts are derived, never primary
5. **No fabricated references** — every citation must be verifiable in a project bibliography source (for example `Projects/*/references/bibliography.bib`)
6. **Voice fidelity** — style governance rulings are authoritative when a style-governance agent is present
7. **Living documentation** — agent docs must not accumulate stale content
8. **Always close with `@conflict-auditor`** — required after any multi-file change session
9. **Every request must generate a plan** — any request involving two or more implementation steps (steps that write, create, rename, delete, or make agent decisions) must produce: (a) a summary saved to `tmp/by-week/YYYY-Www/<plan-slug>.plan.md` and (b) a step-by-step CSV saved to `tmp/by-week/YYYY-Www/<plan-slug>.steps.csv` before the first step executes; the CSV must include columns: `step`, `agent`, `action`, `inputs`, `outputs`, `status`, `notes`; initial `status` for all rows is `pending`; after each step completes, pass remaining steps through `@adversarial` and `@conflict-auditor` before proceeding; create `tmp/by-week/YYYY-Www/` if it does not exist; legacy undated `tmp/` plans are read-only fallback inputs.
10. **Fail-closed verification** — unresolved factual or citation verification findings must block final acceptance and output compilation

---

<!-- AGENTTEAMS:BEGIN source_repositories v=1 -->
## Source Repositories

- `https://www.jstor.org` — humanities and social science peer-reviewed articles
- `https://pubmed.ncbi.nlm.nih.gov` — biomedical and life-science literature
- `https://arxiv.org` — preprints in STEM fields
- `https://ssrn.com` — economics, law, and social science working papers
- `https://www.semanticscholar.org` — cross-disciplinary scholarly literature discovery and metadata
- `https://www.crossref.org` — DOI resolution and bibliographic metadata verification
- `https://scholar.google.com` — broad academic literature discovery and citation counts
<!-- AGENTTEAMS:END source_repositories -->

---

## Style Rules

- All citations must follow Chicago Author-Date style (17th edition)
- Include a full Chicago-formatted bibliography at the end of every report
- Inline citations use the form (Author Year, page) or (Author Year) for general references
- Never fabricate or hallucinate sources; every citation must be verifiable via DOI, URL, or repository record
- Flag any source that cannot be verified as UNVERIFIED and exclude it from the final report
- Prefer peer-reviewed journal articles and books over grey literature
- Distinguish clearly between empirical findings, theoretical arguments, and author opinion
- Summarise conflicting scholarly positions fairly before offering a synthesis
- Use clear section headings: Introduction, Literature Review, Analysis, Conclusion, References
- Every factual claim must be traceable to explicit evidence from an approved authority source or a verifiable local artifact
- Treat citation or fact statuses `UNVERIFIED`, `NOT-FOUND`, and `CONTRADICTED` as blocking defects until resolved

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
