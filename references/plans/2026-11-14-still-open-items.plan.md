# Still-open items after v1.1.2 and the agentteams v1.1.1 pin (2026-11-14)

Session researchteam-47. The operator asked for these items to be completed.

| Step | Agent | Action | Status | Notes |
|---|---|---|---|---|
| 1 | orchestrator | Record the decision on `effect_targets` coverage for the signed `pin-agentteams-v1.1.1` row | done | `docs/release/pin-agentteams-v1.1.1.effect-targets.md`; no new row |
| 2 | orchestrator | Check the agentteams issue draft about the discarded `_unbound_reason` | done | Already filed as agentteams#476 (2026-11-13) and fixed by agentteams #481 (in v1.1.2 and v1.1.3). Nothing to file. |
| 3 | cleanup | Remove the merged worktrees `researchteam-wt-pr152` and `researchteam-wt-v112`, and the session scratch copies | done | Both were clean and contained in `origin/main`; the operator confirmed removal |
| 4 | conflict-auditor | Consistency check of the record | done | No BLOCKING. 3 NOTEs: step status fixed; 65f5604 verified with git; "non-relaxing" is the signer's classification (the row's effect_class field is empty) |
| 5 | git-operations | Pull request, green CI, merge under PS-2 | done | |
