# P3: branch hygiene after a merge

Written 2026-11-19 by the researchteam agent session, for the agent that takes this over.

## Goal
Merged branches stop piling up on the remote, with no deletion the operator has not authorized.

## State on 2026-11-19 (checked)
- Two cleanups by operator script (28 branches on 2026-11-16, 27 on 2026-11-19), each after a `@security`
  `--branch-cleanup` review. Every merged PR leaves its branch until the next cleanup.
- Remote heads now: `main`; `release/1.0`, `release/1.1`, `release/1.2`; one `archive/` branch;
  `chore/agentteams-autosync` (evergreen); the heads of open PRs #156 and #135; the unmerged
  `docs/framework-install-pin-v1.1.2`; `records/post-1.2-housekeeping` (merged, PR #221); and this plan's own
  branch.
- The repository setting "Automatically delete head branches" is **off**.
- Rulesets already forbid deleting `main`, `release/**` and `archive/**`.
- Locally there are about 110 branches already merged into `main`, and four worktrees that belong to other
  work (`governance/agentteams-1.1`, `feat/briefing-records`, `docs/install-pins-v1.1.2`,
  `chore/authorize-infrastructure-management`).

## Decision for the operator (picker, at Gate 1)
- **A. Turn on "Automatically delete head branches".** GitHub deletes a PR's head branch when the PR merges.
  The commits stay reachable from `main`, and `refs/pull/<n>/head` keeps the tip. Two things come first:
  - **PS-2 must be amended.** It says a remote branch deletion needs the operator's signed grant or a recorded
    `@security` `--branch-cleanup` PASS. Automatic deletion has neither, writes no deletion record and runs
    none of the hold checks. `branch-lifecycle.reference.md` §5 recommends the setting, but PS-2 is stricter
    and wins. The amendment is a change to `.claude/CLAUDE.md`, so it needs a `@security` PASS naming that
    path and the operator's approval, and it merges **before** the setting is changed.
  - It is a repository setting, so the operator applies it with a handoff script. The agent never changes
    settings (PS-2).
- **B. Keep cleaning up by script** every week or two, as now. No rule changes.

Checked on 2026-11-19: the evergreen `chore/agentteams-autosync` is safe under A. When that branch is absent, or
present with no open PR, `scripts/agentteams_autosync_gate.sh` takes its baseline from the current branch's
ref file, and the workflow recreates the branch on its next run.

## Steps
1. **Finish the safety check for A, read-only.** Confirm that no workflow, lockfile or tracked link names any
   other short-lived branch, and that the rulesets still forbid deleting `main`, `release/**` and
   `archive/**`. `@adversarial` reviews the conclusion.
2. **Ask the operator** A or B, with the result of step 1.
3. **If A:** first the PS-2 amendment PR (the projected copies re-synced with
   `agentteams --sync-project-rules`; `@security` naming `.claude/CLAUDE.md` and every projected copy the PR
   touches: `.github/copilot-instructions.md`, `AGENTS.md`, `.goosehints`; the operator's live approval). Then a handoff script
   that turns the setting on and reads it back, after `@security`. If B: nothing now.
4. **Leftover remote branches, after the Gate 2 merges.** Build the next deletion script in the series (`10`
   and `17` are the model) only when the PRs of this metaplan have merged, so the list is final. `@security`
   `--branch-cleanup` review; the operator runs it; its tracked copy and the readback go in the records PR.
5. **Record** the choice and the readback in the work summary.

## Cut after audit
Deleting the roughly 110 local merged branches. It is a bulk deletion (C-5), another session may be using
some of them, and it gains almost nothing.

## Not in scope
The open PRs #156 and #135 and the unmerged `docs/framework-install-pin-v1.1.2`: they are unfinished work, not
leftovers.

## Done when
The operator has chosen A or B, the leftover merged branches are gone, and the choice is recorded.
