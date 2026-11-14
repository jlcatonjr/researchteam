# Plan: Integrate the 2-Fold Citation & Claim Audit Trigger

- Week: 2026-W28
- Trigger: User asked that initiating/developing a project auto-trigger a 2-fold audit of the
  bibliography + URL links AND all facts/interpretations vs their cited justification, run twice,
  for high confidence no citation or claim was fabricated.
- Full design + audit resolutions: `docs/citation-claim-audit-integration-plan.md`
- Standing procedure (single source): `docs/citation-claim-audit-protocol.md`

- Goal: A reliable, layered trigger — a deterministic detector (mechanical spine) + a doubled
  agent protocol (Round 1 baseline, Round 2 adversarial re-audit) anchored at pre-compile closeout,
  surfaced via CI (advisory) + bridge command + Claude workflow surfaces — honoring the
  anti-fabrication ceiling (WELL-FORMED ≠ RESOLVED) and advisory-by-design.

- Method: plan → adversarial + conflict audit (parallel) → revise (binding R1–R12) → implement →
  gates green.

- Success criteria:
  - Detector discovers all 3 project roots (nested + hidden), blocks only on unambiguous DEFECT
    (duplicate key / missing title or author-editor), advisory on everything heuristic, never
    false-blocks a valid parenthesized DOI, and prints the WELL-FORMED-not-RESOLVED banner.
  - bash-3.2 unit tests pass (upstream-CI blocking); catches the live `(Shi 1995)` in-text miss.
  - Derived CI runs advisory scan only (guarded); upstream runs blocking test + advisory scan.
  - Orchestrator routing added in USER-EDITABLE notes only (no fence touched); agent-doc pointers
    deliberately cut (sprawl).
  - `researchteam update --dry-run` recognizes the two new MANAGED_FILES; no unrelated changes.

- Rollback: additive and independent (see plan §5). No existing file destructively rewritten.
- Status: Implemented 2026-07-07; verification pending final gate run.
