# PS-2: the agent manages the GitHub repository (2026-11-14)

Operator ruling, given in session on 2026-11-14: "You monitor the merge and handle all github repo management. I
don't want to be involved in that. Monitor and manage all of this yourself."

1. Add PS-2 to `.claude/CLAUDE.md` and delegate merges in `docs/release-policy.md`, whose section is renamed
   "Operator-only and delegated actions".
   Signing stays with the operator.
2. `@security` review: CLEARED-WITH-CONDITIONS. The conditions are written into PS-2: no force-push, history
   rewrite, `--admin` merge, or settings change; no merge of executor-opened remediation PRs (S-VM); no merge while
   a HALT or a pending condition stands; deletions follow S-4; remote branch deletion needs the signed grant;
   fixing forward goes through a PR.
3. Publish `2026-W42/operator/state.env` as `state.vars.txt`, after a separate recorded `@security` clearance
   (step 3a). The `*.env` ignore rule had kept it out of PR #162. `@security`'s S-1 finding assumed it was
   tracked on `main`, and it never was. Correct the published count from 110 to 109+1.
4. Keep the unscrubbed `tmp/` originals. Deleting them needs per-deletion operator confirmation (S-4), and they
   are the only copies made before scrubbing.
5. `@conflict-auditor` (7 items, all fixed). `@adversarial`: CONDITIONAL on items 1, 3, 4 and 7, all met:
   - (1) The operator did not review PS-2's wording; the agent wrote it. It was shown to the operator in the
     session's closing report, and the operator can amend it at any time.
   - (3) PS-2 names the required checks, and changes to the gate paths need a `@security` PASS that names them.
   - (4) Branch protection was checked: none on `main` or `release/*`. Delegated merges are marked in the
     commit body.
   - (7) The step-3a row has been added.
   Then commit, PR, merge under PS-2 (this PR touches `.claude/CLAUDE.md` Project-Specific Rules and
   `docs/release-policy.md`, which `@security` cleared), and check CI on `main`.
