# Plan: full-agent-docs-scripts-audit-revision

- Trigger: Pass all agent documents and scripts through adversarial and conflict audits; revise according to findings.
- Goal: Resolve active documentation/script contradictions, stale paths, and safety gaps across agent infrastructure and bridge docs.
- Agent sequence: orchestrator -> adversarial/conflict audit -> implementation edits -> verification audit.
- Success criteria:
  - Broken paths corrected.
  - Governance path/policy contradictions reduced.
  - Orchestrator/bootstrap workflow clarified.
  - Safety warnings and validation semantics improved.
  - Follow-up audit reports no unresolved critical issues.
- Rollback notes:
  - Revert only touched files if regressions are detected.
  - Preserve existing user-authored content and avoid backup tree edits.

- Completion: 2026-05-20
