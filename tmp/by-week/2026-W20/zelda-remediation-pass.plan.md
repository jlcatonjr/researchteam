# Plan: Zelda Remediation Pass

- Plan slug: zelda-remediation-pass
- Trigger: User instruction to proceed with remediation.
- Goal: Resolve medium/high findings from the adversarial and conflict audit.
- Agent sequence: orchestrator -> document edits -> consistency recheck.
- Success criteria:
  - BOTW/TOTK hypothesis matrix added in analysis.
  - Verification and release-gate language aligned across 00-03.
  - Character claims in analysis include support/confidence tagging including Tingle.
  - Reader has top-level completeness warning for partial load.
  - Bibliography undated web entry is parser-safe.
- Rollback notes:
  - Revert only remediation edits if user requests rollback.
  - Keep previously produced audit artifacts intact.
