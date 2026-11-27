# Handoff: the high-benefit items after 1.3.0

Written 2026-11-26, at the close of the session that carried out
`references/plans/post-1.3.0-high-items.metaplan.md`. It lists what is done, what is still open and who holds
each open item. The target plans, their step lists and the check tables beside this file are the detailed
record; this file points to them and does not replace them.

`main` when this was written: `13fcf5c` (PR #280), CI green. Everything the session did is merged there, in pull
requests #262 to #280. Apart from the run logs of the two 1.3.0 cuts
(see the last section), nothing is kept in a stash or only in an untracked file.

## Done

| Item | What | State |
|------|------|-------|
| H1 | The local toolchain equals the lock | done 2026-11-25 |
| H2 | Release-policy text for a line move | merged (PR #262) |
| H3 | The decision key `op-2026` retired | merged (PRs #275 to #278); steps 16 and 17 and a few smaller points open, below |
| H5 | Survey tools, steps A to D | merged (PRs #263, #264, #267, #269, #270, #272, #273); running post-steps deferred |
| H6 | Survey sign-off (step F) and its CI job | merged (PRs #265, #266, #268, #271) |
| Records | Plans, check tables, work summaries | merged (PRs #274, #278 to #280; #278 is also counted under H3) |

H4 has not started, by the operator's choice.

## The trust state on `main`

- The `.github` and `.codex` key stores hold one decision key, `opr-2026-11`.
- The clearance row `key-retire:op-2026` and the seven decisions carried forward under `opr-2026-11` verify.
  Rows signed only with `op-2026` no longer verify, as the operator ruled.
- The branch-deletion exception is bound to its `opr-2026-11` row and expires on 2027-02-18.
- `release/1.0`, `1.1` and `1.2` still depend on `op-2026` and are left alone (ruling P4). A pull request that
  brings `op-2026` back onto `main` is a HALT.
- The AgentTeams Autosync is active again. `toolchain.lock` pins researchteam at `535c7ca`, behind `main`, so
  the next autosync pull request moves the pin.

## Open, with the operator

1. **H4, the App authorization.** Left waiting on 2026-11-26 ("Leave H4 waiting"). The prepared work is on the
   branch `governance/fleet-agent-tier1` (head `25b77f2`, not merged). When the operator names a signing day, the
   steps are 2 to 10 of `post-1.3.0-h4-app-authorization.steps.csv`: the script is regenerated and re-dated, not
   reused as it stands. Whether the authorization is still wanted is part of that decision. Step 9 comes with
   it: the exception cap returns to one by 2027-02-18, or when either exception ends, by an operator script.
2. **The old private key of `op-2026`** (H3 step 17). Its disposition is the operator's. It is retained by the operator
   while an older release line might need a patch, and signs no row on `main` again. No agent session reads, moves or
   deletes it.
3. **The App installation on GitHub** still lists this repository. Removing it there is optional and is the
   operator's to do.
4. **The release that carries H5 and H6** (metaplan P7): the next minor, or a split. Not decided.
5. **The next contract version of the survey toolkit** (metaplan P8). The contract `docs/survey-toolkit.md` is
   frozen at version 1. The proposals gathered while building are in the check tables
   (`post-1.3.0-h5-step-*-check-table.md`, `post-1.3.0-h6-step-f-check-table.md`). Each needs a ruling.
6. **Running post-steps in `survey-frame`** (H5 step D part 2). Deferred on 2026-11-26 ("Defer; keep refusing").
   The tool checks post-steps and refuses to run them. To be decided with the plug-in questions and the next
   contract version.
7. **Python 3.14.** CI tests 3.10 and 3.13. The reference comparison ran on 3.14 in the first integrating
   project's session and agreed, but 3.14 is not a tested version here. Whether to add it is a workflow change
   (a PS-2 path).
8. **An earlier wording in the H3 plan** has been replaced. Any change to `main`'s history is the operator's to
   order; the session's advice is to leave it.
9. **The merge of the next autosync pull request.** It needs the operator's live answer, like any merge. The
   agent session's part is in the next list.
10. **The plug-in questions of the survey tools:** the vantage module, and the evidence reader, which needs its
    own plan. To be decided with items 5 and 6.
11. **Step E of the 2026-11-23 survey plan** (the explorer projection, issue #243) was rated medium-high and is
    in none of these plans. It bears on item 4.
12. **Three merged work branches under `release/`** (metaplan finding F1): `release/pin-agentteams-1.3`,
    `release/prep-1.3.0` and `release/final-1.3.0`. The `release/**` ruleset forbids their deletion, so removing
    them needs a ruleset change, which is the operator's choice. They are ancestors of `main` and harmless.

## Open, with the next agent session

1. **The next cut script** (H3 step 16). It must not require the row `s10-release-cooldown-restored` as a line of
   text; it checks signatures instead, or drops the requirement. It also names the agentteams version it
   expects. `@security` marked this as blocking for the next release cut.
2. **The close-out audit of the metaplan** (step M13, `@conflict-auditor`, read-only). It waits for H4. If H4 is
   withdrawn or stays waiting for long, run it on H1 to H3, H5 and H6 and say so.
3. **The first integrating project runs each merged step on its own study** (H5 step X1). The step D comparison
   was done on the invented study. Runs on the real study are that project's to report, as data.
4. **The release coordinator.** The note that `op-2026` is retired was sent on 2026-11-26 to the session the
   operator named. Delivery is confirmed and reading is not. Condition C6 asked for a note before and after the
   removal; only the after-note exists.
5. **The generated memory indexes** mention `op-2026` until they are next rebuilt.
6. **The family-HALT scan in the sign-off tools** (H6, decision P9, "Strict interim scan"). Until agentteams
   offers its public listing of open HALTs, expected in 1.3.1, any HALT row on the two family names blocks every
   gate, retracted or not. When that release is adopted, the scan uses the listing to tell a retracted HALT from
   an open one, and keeps its own scan of the family names. See `post-1.3.0-h6-survey-sign-off.plan.md`.
7. **The next autosync pull request** is opened with the workflow's token and gets no checks. The session closes
   and reopens it with the session's `gh` token so the tests run on its head (PS-2), then asks the operator for
   the merge.
8. **The first integrating project's adoption:** besides X1, it moves its manifests and adds the chain column to
   its log when it adopts the tools. That work is the project's own.
9. **A request to the upstream agentteams team** (H3 plan, phase 1) is recorded as sent, as information. This
   session did not confirm that it was received. It is not described here.
10. **One observation for the upstream agentteams team,** about how its tool labels one kind of decision row, is
   not yet passed on. It is information for that team and is not described here.

## Left on the operator's machine

Nothing here is the only copy of merged work. Deleting any of it needs the operator's confirmation, and a branch
deletion needs the signed grant or a `--branch-cleanup` PASS.

- **Worktrees.** Sixteen finished ones were removed on 2026-11-26. Those kept: the one holding the H4 branch; the
  one holding the test interpreter; one that holds regeneration backup folders; three whose branches are not
  merged; two with uncommitted files; and one that another session uses.
- **Local branches** of merged pull requests, whose remote branches GitHub deleted at the merge.
- **Remote branches that are not merged:** `governance/fleet-agent-tier1` (H4) and
  `chore/root-owned-agentteams-1.3.0` (script 32, drafted here and then withdrawn; the H3 plan keeps the branch as
  the record of the draft and its reviews). The other unmerged remote branches are not this session's.
- **The ignored working folder** `tmp/by-week/2026-W48/operator/` still holds the runnable copies of the
  autosync pause script and the two 1.3.0 cut scripts, with the run logs of the two cuts. The cuts' outcome
  is in `docs/release/release-notes-v1.3.0-rc.1.md` and `release-notes-v1.3.0.md`. The two logs exist only in
  that ignored folder. Under PS-1 they are either published after the operator has reviewed each file, since
  they may carry machine detail, or deleted with the operator's confirmation. That choice is the operator's. The copies of scripts 31, 33 and 34 were
  deleted after `@security`'s review; their tracked copies are in `references/plans/archive/2026-W48/operator/`.
- **The session's scratch folders** hold only invented or public content and are cleared by the system.

## Where to start

1. Read `post-1.3.0-high-items.metaplan.md` and its step list, then the target plan of the item in hand.
2. `workSummaries/daily/2026-11-25.md` and `2026-11-26.md` give the order of events and the operator's answers.
3. Before any release work, do item 1 of "Open, with the next agent session".
