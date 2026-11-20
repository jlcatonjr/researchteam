# Execution architecture for the open-items metaplan (2026-11-20)

How this session carries out `references/plans/open-items-metaplan-2026-11-19.plan.md` and its target plans
P1 to P4. The metaplan stays the authority on what is done; this file says how, in what order, and what
changed since it was written. **It approves nothing.** Every merge, script run and deletion is still asked
live in the picker.

## State checked on 2026-11-20 (start-here step, done)
- `main` = `origin/main` = `fec2e30`, clean. Open PRs: #156 and #135 only (other work). The plans' PR is
  merged. Working copies in `tmp/by-week/2026-W47/` equal the tracked copies.
- `v1.2.1` is Latest; the lock pins agentteams `v1.2.1`; agentteams `v1.2.2` is Latest upstream.
- No signed agentteams 1.3.x tag exists, so P1 phases 1 and 2 stay blocked.
- Repository setting `delete_branch_on_merge` is `false`. Rulesets read back: `main`, `release/**` and
  `archive/**` forbid deletion with no bypass; tags restricted.
- Merged remote branches now waiting: `plans/open-items-2026-11-19`, `records/post-1.2-housekeeping`,
  `records/v1.2.1-cut`, `release-prep/v1.2.1`, `fix/verify-tag-shallow-fetch`, and four
  `docs/survey-toolkit-*` branches that belong to another session's work.

## What changed since the metaplan was written
1. **The upstream module exists.** `agentteams/term_index.py` is on agentteams `dev` (read at `b4b732f`,
   707 lines, from the merged PR for issue #548). It imports ten names from `agentteams/_term_text.py`
   (348 lines, standard library only). So the core is **two files, not one**, and P1's copy design cannot
   assume a single file. P1 0.1 compares the engine with the real module, not with the issue's parameter
   list. P1 0.3 must design for a file set (or for a single file, if upstream agrees to fold them).
2. **P2 is nearly done** (v1.2.1). Left: step 2 (confirm "fix forward only") and step 5 (the policy
   sentence). Wave 1 track B is empty.
3. **Who the coordinator is today is not known to this session.** The session names in the work summaries
   are no longer in the peer list. The upstream message is drafted and tracked; which session receives it is
   asked at Gate 1. No message goes to a guessed session.

## Order of work

### Wave 1: read-only, in parallel
| Track | Step | Who | Output |
|---|---|---|---|
| A | P1 0.1 and 0.4 | `technical-validator` subagent, given the two upstream files in scratch | seam table (function by function, core or adapter, upstream parameter or gap); private-symbol list; draft message |
| C | P3 1 | this session gathers the evidence (done above: workflows, rulesets, tracked links); `adversarial` subagent reviews the conclusion | safe or unsafe, with reasons |
| D1 | P4 1 | `technical-validator` subagent | risk table for the test files that touch network, clock, environment or home |
| D2 | P4 2 | this session, in the background, after D1 | 20 runs, then 5 in reverse file order, junit per run |

(Superseded in part by "Deviation recorded: the 25 runs" below: the repository's `.venv` has no pytest, so
the runs used two other interpreters.)

D2 runs from a `git archive` extract of `main` in the session scratchpad, one run at a time, as
`PYTHONPATH=<extract> .venv/bin/python -m pytest -p no:cacheprovider --junitxml=...` from the extract root,
with a scratch `HOME`. `.venv` holds an installed, non-editable researchteam from an older commit, and only
some test files put the repository root on `sys.path` themselves, so without `PYTHONPATH` a run could test
the installed copy, and which copy wins could depend on file order. Each run records
`researchteam.__file__` as seen under that same command and environment, next to its junit file. D2 is the
only thing using `.venv` while it runs. A1's runs use the same command form.

### Gate 1: one picker visit, after tracks A and C report and after the Rule 9 pass
1. P2: confirm "fix forward only: the existing tags stay".
2. P3: A (automatic head-branch deletion, with the PS-2 amendment first) or B (scripts as now).
3. P1: which session receives the upstream message, shown in full (or: hold it). Sent or held, the draft
   goes in the records PR.
4. P3: whether the four merged `docs/survey-toolkit-*` branches of another session go on the next deletion
   list. Asked here, before the deletion script is built, so the `--branch-cleanup` review covers the final list.
No answer means "keep as it is" for each, and for question 1 it is recorded as "fix forward unconfirmed",
not as a confirmation. PR-docs is not put up for merge before question 1 is answered.

### Wave 2: build (does not wait for Gate 1, except track C)
Gate 1 decides only P3 step 3 and the destination of one message. Tracks A1, A2 and B depend on neither,
so they start when their inputs exist.

| Track | Step | Branch (own worktree, from `origin/main`) | Who writes | Review |
|---|---|---|---|---|
| A1 | P1 0.2 | `tests/term-index-characterization` | `primary-producer` writes the file; this session makes the worktree, runs the tests, pushes and opens the PR | `code-hygiene` |
| A2 | P1 0.3 | no branch: the note is a records file | `primary-producer`; lands in the records PR | `adversarial` |
| B | P2 5 | `docs/release-policy-tag-checks` | this session (one sentence) | `Security` naming `docs/release-policy.md` |
| C | P3 3 | `governance/ps2-auto-branch-delete` (only if A) | this session; `agentteams --sync-project-rules` for the copies | `Security` naming `.claude/CLAUDE.md` and each projected copy |
| D3 | P4 3 | `fix/<name>` (only if a failure is captured or an unguarded test is found) | `primary-producer` writes; this session runs, pushes and opens the PR | `code-hygiene`; `Security` if a gate test |

Test discipline: A1's test file is run only after D2 has finished, so the 25 runs are not disturbed and the
single `.venv` is never used by two tracks at once. A1 runs its new file, then the whole suite once.
Tracks do not touch `CHANGELOG.md`, `workSummaries/` or plan files. If D3 has to edit
`tests/test_term_index.py`, D3 merges first and A1 rebases.

A1 tests the engine as it is today, so changes on agentteams `dev` do not affect it. A2 is different: it
treats `b4b732f` as provisional (no hash of it is pinned anywhere), states how `term_index.py`'s import of
`agentteams._term_text` resolves in a copy that must load with no agentteams installed (a byte-identical
copy cannot rewrite the import), and hashes a manifest of N files. `_term_text` goes on the 0.4 list.

Track C, if chosen, first reads the agentteams `v1.2.2` security-labelled note to check that it does not
concern `--sync-project-rules`, which would run here under `v1.2.1`.

Rule 9 pass (`adversarial`, `conflict-auditor`) on the remaining steps after Wave 1 and again before Gate 2.

### Gate 2: one PR at a time
For each PR: pushed with the session's token, both checks `tests (3.10)` and `tests (3.13)` present and
green on the head, the reviews recorded as PR comments, then one picker question naming the PR number and
the full head SHA. Merge with `gh pr merge <n> --merge --match-head-commit <sha>`, the body saying "Merged
under PS-2 by the agent session" and naming the approval. Order: PR-fix (if any), PR-tests, PR-docs, PR-ps2
(if A). If the operator does not answer, the PR stays open and is recorded as waiting.

After each merge, content is compared, not file names: if `main` had not moved since the branch point, the
merge commit's tree must equal the reviewed head's (the metaplan's check); if it had (these PRs merge one
after another), the patch of the merge against its first parent must be identical to the patch of the head
against its merge base. Then tests must be green on `main`. If `main` is red: a revert PR first, and after
one failed fix-forward the session stops and tells the operator (PS-2).

Reviews: any new head of a PR that needs `Security` gets a new PASS that names every path in the PR's file
list (for PR-ps2 that includes any agent file the projection touches). A multi-file PR gets
`conflict-auditor` before its merge is asked.

Operator script for P3 (only if A): the setting script is reviewed by `Security` and handed over (PS-3)
only after PR-ps2 has merged; its readback goes in the records PR.

### Wave 3: records and leftovers
Numbers 20 to 22 went to the option-A operator scripts on PR #234; the deletion script takes the next free
number.
- The next deletion script, built from script 17 with the final list, only after the
  Gate 2 merges. `Security` `--branch-cleanup` review, then handed over as a `.sh` plus one command (PS-3).
  The list follows Gate 1 question 4. At run time the script re-checks that each branch is an ancestor of
  `main` and is not the head of an open PR, which also covers a Gate 2 PR left unmerged.
- Records PR: plan statuses, this file and its CSV, the seam table, the upstream message (sent or held), the
  design note, the risk table and run results, tracked script copies, the work summary (`work-summarizer`). `conflict-auditor` runs on it before
  its merge is asked.
- Scratch is deleted; worktrees made by this session are removed (their branches stay for the cleanup).

## Not done by this session
- P1 phases 1 and 2 (blocked: no signed agentteams 1.3.x tag, no cross-line ruling).
- The agentteams `v1.2.2` pin move and issue #228: the metaplan lists them as outside the four plans. They
  are reported as open, not started here.
- Any write to another repository; any change to settings, rulesets, keys or `.claude/settings.json`.

## Failure handling
- A subagent's finding is checked against the files before it is used (a table row that names a function
  must match the source).
- A red check on a PR: fix on the branch, re-review if the fix is more than the review covered, ask again
  with the new head.
- A captured P4 failure stops D2's remaining runs only if it makes later runs meaningless; otherwise the
  runs finish, to measure how often it fails.
- A `Security` HALT stops that track (C-2). The other tracks continue.

## Closing P4
If nothing fails, the record says "not reproduced under isolation". Clean isolated runs cannot test the
first two hypotheses (a race with the regeneration; the old environment), so it does not say "does not
recur".

## Audit record (2026-11-20, before any work)
- `conflict-auditor`: 2 blocking, 5 advisory. `adversarial`: CONDITIONAL, 5 blocking. All adopted:
  - the test runs set `PYTHONPATH` to the extract and record which copy was imported, per run;
  - Gate 1 waits for tracks A and C and the Rule 9 pass; the survey-toolkit branch question moved to Gate 1;
  - writing agents without a shell only write; this session branches, tests, pushes and opens PRs;
  - the post-merge check compares content; PS-2's rule for a red `main` is stated;
  - a new head needs a new path-naming `Security` PASS; multi-file PRs get `conflict-auditor`;
  - the P3 setting script has its own review and hand-over after PR-ps2, with a readback;
  - the design note deals with import resolution and treats the upstream commit as provisional;
  - the records branch is assembled before the close-out audit, and merged after it.
- Not checked by either audit: Rule 9's "after each step" wording against the batched passes the metaplan
  accepted on 2026-11-19. This session follows the metaplan's batching.

## Rule 9 pass before Gate 1 (2026-11-20)
`adversarial`: CONDITIONAL, four blocking, all adopted: the Wave 1 findings were pushed to the records branch
at once (PS-1); `main`'s ruleset was read (`strict_required_status_checks_policy` is false, so one merge does
not move another PR's head); the P4 fetch stub raises, as the offline path does; the cost of option A in
signing and a cap slot was stated at Gate 1. Also adopted: #231 and #232 are not held for the P4 PR; this
session's worktrees are removed before the deletion script is built; unmerged PRs stay off its list.

## Gate 1 answers (operator, session picker, 2026-11-20)
1. **P2: confirmed.** "Fix forward only": `v1.1.9`, `v1.2.0-rc.1` and `v1.2.0` stay as they are and are not
   re-signed. P2 step 2 is closed.
2. **P3: option A**, automatic head-branch deletion. The recommendation shown was B.
3. **P1: the upstream request is held in the records.** It was not sent. The draft is Deliverable 3 of
   `references/plans/open-1119-p1-seam-table.md`.
4. **P3: the four `docs/survey-toolkit-*` branches stay off the next deletion list.**

## Found after Gate 1: the exception cap
Option A was offered as needing "a cap slot". The registry
(`.github/agents/references/exception-registry.json`) sets no cap, so the default of one active relaxing
exception applies, and one is active: `s10-cooldown-exempt:jlcatonjr/agentteams`, until 2027-02-01. A second
would breach the cap. The operator did not have this fact when choosing A. `Security` is asked what A
lawfully requires; the result goes back to the operator in the picker before anything is built for A.

## Found while building the P4 hardening change: two test files fail when run alone
`tests/test_update_native_surfaces.py` (4 of 10) and `tests/test_materialize_surfaces.py` (13 of 20) fail on
`main` when run alone. `researchteam._frozen` binds `subprocess.run` at import and is imported lazily, after
those files' fixtures have faked `subprocess.run`. A full run hides it, because another file imports
`_frozen` at collection. PR #233 fixes it in `tests/conftest.py`. It cannot be the single failure of
2026-11-19, which happened in a full run.

## Deviation recorded: the 25 runs
- The repository's `.venv` has no pytest, so the runs do not use it. They use two interpreters, to cover the
  leading explanation of the 2026-11-19 failure: one with no agentteams (as in CI), one in which agentteams
  is importable from a local checkout (as the session's default `python3` is). Ten forward runs each, then
  three and two with the files in reverse order.
- While the series ran, this session also ran single test files a few times and, once, every test file on
  its own. A failure of a timing test in the series during that window would not count as evidence.

## Gate 2 (operator, session picker, 2026-11-20)
One question per PR, each naming the PR and its full head. All three approved, then merged with
`--match-head-commit`, with the content check and green tests on `main` after each:
- #233 at `8542e2b` as `89bda42` (merge tree equal to the head's tree);
- #232 at `ff8ab84` as `dabf348` (merge patch equal to the head's patch);
- #231 at `45003ce` as `53ed42e` (merge patch equal to the head's patch).
Before the question: `conflict-auditor` on the three PRs together, no blocking finding. `adversarial` was not run
again here: its pass before Gate 1 had examined the Gate 2 procedure, and each PR had its own review.

## Option A after the cap finding (operator, session picker, 2026-11-20)
`Security` found that A is a relaxation by effect and needs the registry's one slot, and that
`s10-cooldown-exempt:jlcatonjr/agentteams` is redundant with the signed first-party toolchain group. Offered:
retire that exemption; a signed `branch-delete` grant with no rule change; B; or raise the cap. **The operator
chose: A, retiring the s10 exemption.**
- Draft PR #234: the PS-2 amendment and its projected copies, the decision spec, operator scripts 20 (retire,
  sign, register), 21 (setting on) and 22 (setting off), one clause and one merge condition in the release
  policy.
- `Security`: conditional at `670ad62` (four required changes), PASS at `e2b441f` as the basis for the
  operator to run script 20. `conflict-auditor`: one blocking finding, fixed at `e2b441f`.
- Next, in order: the operator runs script 20; the session commits the log and registry; `Security` reviews
  that head; the operator approves the merge; `Security` clears script 21; the operator runs it; read-back.

## P4 closed
25 isolated full runs, no failure: `references/plans/open-1119-p4-runs.md`.
