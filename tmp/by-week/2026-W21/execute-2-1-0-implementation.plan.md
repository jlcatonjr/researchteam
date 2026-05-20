# Plan: Execute Ordered Steps 2-1-0

Trigger: User request to proceed with execution of the prepared plan.
Date: 2026-05-20

Goal:
- Execute ordered implementation sequence:
  1) Step 2 JS/runtime hardening
  2) Step 1 agent-infra authority normalization (non-destructive)
  3) Step 0 CI automation scaffolding for AgentTeams update/merge

Agent sequence:
1. Orchestrator: implement Step 2 JS fixes.
2. Orchestrator: implement Step 1 infra normalization artifacts.
3. Orchestrator: implement Step 0 workflow/script/policy files.
4. Orchestrator: validate edits and summarize outcomes.

Success criteria:
- Runtime hardening is in place with no new file errors.
- Infrastructure has an explicit authoritative path policy and legacy mirror quarantine guidance.
- CI workflow, validator script, and policy docs are present and internally consistent.

Rollback notes:
- Revert changed files if behavior diverges from expected runtime or CI policy.
- Keep operations non-destructive for duplicate-tree handling in this pass.

Completion: 2026-05-20
