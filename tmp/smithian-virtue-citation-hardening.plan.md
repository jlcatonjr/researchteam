# Plan Summary: Smithian Virtue Citation Hardening

- Plan slug: smithian-virtue-citation-hardening
- Trigger: Proceed with implementation; enforce constitutional citation rules
- Date: 2026-04-30
- Goal: Fail-closed citation verification for the Smithian Virtue project by identifying in-text references, matching them to bibliography records, resolving what can be verified locally, and documenting unresolved items as blocking defects.
- Agent sequence: orchestrator -> citation verification -> bibliography refinement -> adversarial/conflict audit artifact
- Success criteria:
  - Citation audit file exists with explicit statuses (`VERIFIED`, `UNVERIFIED`, `NOT-FOUND`, `CONTRADICTED`).
  - `references/bibliography.bib` includes locally verifiable records for cited works.
  - Known citation typos are corrected in analysis artifacts where appropriate.
  - Blocking citation defects are surfaced clearly.
- Rollback notes:
  - Revert modified project markdown and bibliography files.
  - Remove the new citation audit file if necessary.

Completion date: 2026-04-30

Blocking defects remaining: NONE — all cleared 2026-04-30
- RESOLVED: Hirschfeld 2018 — BibTeX + HTML reference entry added
- RESOLVED: Heath 1995 — BibTeX with DOI + HTML reference entry added
- RESOLVED: Hankins and Thrasher 2022 — *Philosophy and Phenomenological Research* 105(3): 638–656; DOI 10.1111/phpr.12833
- RESOLVED: Caton 2020 — *Erasmus Journal for Philosophy and Economics* 13(2): 1–29; DOI 10.23941/ejpe.v13i2.443
- RESOLVED: Wagner 2024 — SSRN Working Paper; DOI 10.2139/ssrn.4769642
