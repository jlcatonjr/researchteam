# Release prep: researchteam v1.1.5 (2026-11-15)

Operator rulings through the interactive selection interface in session researchteam-59: "Prepare v1.1.5" and
"Fixes only, on v1.1.3". IM-40 asked whether the #172 and #173 fixes go in a release (relayed, C-4).

Scope: `main` at the release-prep merge. Since v1.1.4 that adds #172 (autosync stranded branch, PR #174), #173
(unfenced `CLAUDE.md` append, PR #175), #165 (`python -m researchteam`) and #161 (build requirements re-vet), plus
rules, plans and work summaries. The agentteams pin stays v1.1.3 (`cbd41a74`, tag object `1f1ffe6b`); agentteams
v1.1.4 (`b82d78e7`) is a separate pin move.

As for v1.1.4, `release/1.1` (`5fd8ec3b`) is an ancestor of `main`, so the release is a fast-forward of
`release/1.1` to the merge commit of this PR, and no merge-forward is needed afterwards.

1. Branch `release-prep/v1.1.5` from `main`: CHANGELOG `## 1.1.5`, `docs/release/release-notes-v1.1.5.md`, this plan.
2. Operator script `05-cut-v1.1.5.sh` (tracked copy, paths scrubbed, in `references/plans/archive/2026-W46/operator/`).
   It checks the pin, the group file and the CHANGELOG at the given commit, requires a fast-forward, asks twice,
   fast-forwards `release/1.1`, signs and pushes the tag, verifies it as consumers do, and offers the GitHub release.
3. `@security` and `@conflict-auditor` on the PR; merge under PS-2; CI green on `main`.
4. The operator runs the script with the merge commit. The agent session does not fast-forward `release/1.1` or tag.
5. Verify the tag independently (`check_toolchain.py --verify-tag researchteam v1.1.5`), tell IM-40, work summary.

Noticed while preparing: researchteam's own `chore/agentteams-autosync` branch holds a commit from 2026-11-13
(`5ed37f5`) with no open PR, which is the #172 situation in this repository itself. The next autosync run (with the
fix) will detect agentteams v1.1.4 and open a PR; that PR is the separate pin move.
