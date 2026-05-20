# Plan: Seizure Transition Literature Project

- Trigger: User request to build a new project in Projects/SiezureTransition summarizing 25-year literature (emphasis on last 5 years) on levetiracetam (Keppra), methylene blue, and transition strategy.
- Goal: Deliver a structured research package with literature review, analysis, conclusion, and bibliography grounded in verifiable scholarly sources.
- Agent sequence: @orchestrator -> @adversarial (plan assumptions) -> @conflict-auditor (consistency) -> @primary-producer (draft files) -> @technical-validator (fact/citation pass) -> @conflict-auditor (closeout).
- Success criteria:
  - Files created under Projects/SiezureTransition:
    - 00-research-plan.md
    - 01-literature-review.md
    - 02-analysis.md
    - 03-conclusion.md
    - references/bibliography.bib
  - Claims and recommendations framed as evidence synthesis, not patient-specific medical advice.
  - Literature window covers 2001-2026 with explicit 2021-2026 emphasis.
  - Explicitly labels evidence gaps and uncertainty.
- Rollback notes:
  - Delete newly created files if user rejects scope.
  - Preserve pre-existing repository files unchanged.
