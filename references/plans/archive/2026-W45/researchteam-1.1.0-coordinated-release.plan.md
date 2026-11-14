# researchteam 1.1.0 — coordinated release (pin agentteams v1.1.0)

Source: coordination request from infrastructureManagement (session infrastructuremanagement-40), plan of
record `infrastructureManagement tmp/by-week/2026-W45/coordinated-release.metaplan.md` rev 3.1, target
`cr-researchteam-release.plan.md`, delivery clearance SEC-IM-CR-2026-11-06. This is a request, not a
directive. Steps marked (operator) are operator-only; this team prepares them.

## Verified state (2026-11-06)
- origin/main 50725af; release/1.1 = v1.1.0-rc.5 = f4be2d9, contained in main.
- release/1.0 = v1.0.4 = f3396f0, NOT in main (release-policy.md requires the merge-forward).

## Steps
- RT-1 (operator): merge #142, #134, #130; defer #135 (CONFLICTING) to 1.2.
- RT-2: merge-forward v1.0.4 into main on `merge-forward/v1.0.4` (merge a6ce263). Resolved toward main's
  1.1 lock, extras, brief and rendered surfaces; net change is the ## 1.0.4 CHANGELOG section, the signed
  pin-agentteams-v1.0.7 row (verified) and its decision spec. validate passes; pytest 524 passed / 1 skipped.
  (operator) merges.
- RT-5 (operator): confirm #59 deferred to 1.2.
- RT-4: rehearse the agentteams Track-A candidate in a worktree, no pin move; report to agentteams. Waits on
  the candidate.
- RT-6: on v1.1.0 publication, branch chore/agentteams-v1.1.0: check_toolchain.py --write-lock --tag
  agentteams=v1.1.0 --sync-extras; re-render; pin spec with OSV and dependency delta; CHANGELOG ## 1.1.0.
  (operator) signs the row and merges.
- RT-7: draft cut-1.1.0 from 11-cut-rc5.sh (v1.1.0, Latest, not prerelease). Precondition: the manager-roster
  enrollment (researchteam-wt-mgr-roster) is merged, or (operator) records a deferral. (operator) cuts.
- RT-8: after (operator) publishes, send release notices to derived repos (--researchteam-tag v1.1.0) under
  this team's @security.

## 2026-11-09 operator rulings
- Operator Decision Query (agentteams 95561f88) deferred to 1.2; RT-6 pin spec states the dropped @security deletion-rule pointer.
- Local .git/hooks/pre-commit agentteams-integrate block skipped in agent sessions (CLAUDECODE/CLAUDE_CODE_ENTRYPOINT); backup in session scratchpad.
- RT-4 ran on v1.1.0-rc.17 (8d0a4bc): gates green, pytest 507/7; only rule-text delta is the ODQ pointer.
