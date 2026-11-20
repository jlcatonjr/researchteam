# P3 step 1: is automatic head-branch deletion safe? (`adversarial`, 2026-11-20)

Evidence gathered by the orchestrator the same day: setting `delete_branch_on_merge` is `false`; rulesets forbid deleting `main`, `release/**` and `archive/**` with no bypass; no workflow, lock or tracked link names a short-lived branch other than the evergreen autosync branch.

**Verdict: SAFE WITH CONDITIONS.** The setting is technically safe. The governance case is not: amending PS-2 is necessary but does not by itself satisfy C-5 or the fenced text.

**1. Autosync. The plan's claim is true.**
- After a merge, the `evergreen_pr` job finds no open PR (`agentteams-sync.yml:47-50`). The `git show origin/chore/agentteams-autosync:…` probe fails, so the evergreen branch is never consulted (`agentteams_autosync_gate.sh:173`). The baseline then comes from main's own `.github/agentteams-autosync-ref` (`:185-187`), which the merge just updated.
- A sync that is still needed is not skipped and nothing loops. Equal SHAs exit with no writes (`:190-192`). A new SHA makes create-pull-request recreate the branch (`yml:284`).
- `delete-branch: false` (`yml:285`) is the action's own option and has nothing to do with the repository setting.
- Closing and reopening a PR under PS-2 never triggers deletion, and nothing here needs the autosync branch to survive a merge.

**2. Other dependencies on a merged branch surviving.** None are live.
- Release cuts fast-forward `release/*` from the merge commit on main (`references/plans/archive/2026-W47/operator/19-cut-v1.2.1.sh:92-123`).
- `PIN_BRANCH` is `main` (`archive/2026-W42/operator/common.sh:28`).
- Rulesets already protect `archive/**`, so PS-1 is not affected.
- Two residual risks remain:
  - **Stacked PRs.** They have been used here (`archive/2026-W42/operator/04-merge-prs.sh:54`). GitHub would retarget a dependent PR's base on its own, and PS-2 approval names only the head SHA, not the base.
- **Session and worktree holds** (`branch-lifecycle.reference.md:62-68`). These are never checked. If a session pushes again to a branch whose PR has merged, the branch comes back with no PR, which strands that work.

**3. Governance.**
- PS-2 text that A contradicts (`.claude/CLAUDE.md:391-393`): "Deletions still follow S-4 and need the operator's explicit confirmation. Remote branch deletion needs the operator's signed `branch-delete` grant or a recorded `@security` `--branch-cleanup` PASS. PS-2 replaces neither."
- **There is fenced text the amendment cannot reach.**
  - `branch-lifecycle.reference.md` §3 guard 8 (`:88`) says every deletion is recorded in the ledger. §5 (`:172-174`) recommends the setting as a "complement". So the generated framework tolerates the setting, but S-4 (`security.agent.md:70`) still requires explicit confirmation.
  - `instruction-authority.reference.md:120-124`: forbidding a safeguard step (a confirmation, clearance or log entry) "is a relaxation, however it is worded."
  - `.claude/CLAUDE.md:301-302` (fenced): the toolchain group and the integration-branch merge authorization are "the only such authorizations" with no sunset and no cap slot. A standing authorization for automatic deletion therefore needs a sunset and a cap slot. A PS-2 amendment cannot exempt it.
- **C-5.** GitHub performs the deletion, but each agent merge under PS-2 now causes a remote ref deletion. Judged by effect, as the framework requires, that is a destructive action. A is compatible with C-5 only on the reading that a standing clearance, recorded before the setting is enabled, counts as "a recorded clearance before execution". The framework already accepts standing clearances (grants with expiry and use counts). The other reading, that each merge needs its own deletion clearance, makes A incompatible. Amending PS-2 does not satisfy either reading, because a Tier-3 rule is not a recorded clearance.

**Conditions for A:**
1. Before the setting changes, `@security` records a decision row such as `repo-setting:delete_branch_on_merge`. It is scoped to PR head refs in this repository, carries a sunset and a cap slot, and ends on a HALT on `branch-delete`.
2. The PS-2 amendment states honestly that:
   - GitHub deletes the head of any merged PR, whatever its base;
   - no ledger row is written;
   - no hold checks run (owner, link, worktree, session, retargeting of dependent PRs);
   - restore is through `refs/pull/<n>/head`;
   - every other deletion, including local branches and branches never opened as PRs, still needs a grant or a `--branch-cleanup` PASS.
3. The merge checklist adds a manual session and worktree hold check, and the operator's merge approval acknowledges that the head will be deleted.
4. The operator turns the setting on through a handoff script, and it is read back afterwards.

**For the operator:** A is technically safe, autosync included. But it means permanently giving up the deletion record and the hold checks, and to stay inside C-5 it needs a recorded `@security` clearance that expires and takes a cap slot, not just a PS-2 edit. B costs a reviewed script every week or two and changes no rule. Choose A only if that periodic review no longer earns its cost.
