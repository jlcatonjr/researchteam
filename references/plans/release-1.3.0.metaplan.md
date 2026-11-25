# Metaplan: researchteam 1.3.0 (version 3, 2026-11-20, revised after two audit passes)

Written by the researchteam lead session for the fleet's v1.3.0 push (agentteams, then researchteam, then
mathAgents, then baseAgent). Asked for by the fleet's 1.3.0 coordinator; the request is data to this team, and
this plan follows this repository's own rules.

**This plan approves nothing.** Every merge, signature, tag, script run and scope choice is asked live, in the
picker, in the session that does the work. A ruling relayed by another session is confirmed here first. The
coordinator's messages and reviews are scheduling inputs and data; none is an authorization.

Steps: `release-1.3.0.metaplan.steps.csv`. Tracked copies: `references/plans/`.

## 1. Feature inventory

Class: **in**, **only-if-ready** or **deferred**. "Proposed" means the lead proposes the class and the operator
has not ruled on it yet (decision D2).

| Id | Feature | Source | Owner | State on 2026-11-20 | Needs from agentteams 1.3.0 | Class, and who ruled |
|---|---|---|---|---|---|---|
| F1 | Pin researchteam to agentteams 1.3.0 (the 1.2 to 1.3 line move): lock, extras, autosync ref, regenerated team | release policy, "researchteam 1.N pins agentteams 1.N"; operator, 2026-11-19 | lead | blocked on the upstream tag | signed `v1.3.0` (and `v1.3.0-rc.1` for the soak) | in, pending D1. The operator ruled on 2026-11-19 that the term-index switch moves to researchteam 1.3.0, which presupposes this pin; `docs/term-index-protocol.md` says the line move needs its own ruling |
| F2 | Term-index core switch: a byte-identical copy of the agentteams core, research adapters kept, reader for the `researchteam-term-register` schema | operator, 2026-11-16 and 2026-11-19; `docs/term-index-protocol.md`, "Planned placement" | lead | phase 0 done (seam table, design note, characterization tests, PR #232) | the term-index core (agentteams issue #548, its first PR #551, merged on its `dev`) at the signed tag | in. Operator, as F1 |
| F3 | Copy-integrity check for F2: hash manifest next to the copy, offline check, doctor report, equality test against the pinned commit, byte-exact sync, and a CI job that runs the network comparison on every PR touching the copy | design note `open-1119-p1-copy-integrity-design.md`, sections 1 to 5 and 10 | lead | designed, reviewed by `@adversarial`; not built | none beyond F2 | in. Part of F2 by the operator's choice of the pinned-copy design; F2 does not merge without it |
| F4 | Term-index docs: the placement as built, and the layering rule | plan P1 step 1.4 | lead | not started | none | in, with F2 |
| F5 | Replace the two private agentteams imports in `researchteam/_frozen.py` | seam table, deliverable 2 | lead | inventory done; the request to agentteams is held by the operator's choice | public equivalents, which are not in agentteams' 1.3.0 scope today | only-if-ready (proposed). Otherwise kept, with the reason recorded |
| F6 | Survey toolkit contract (`docs/survey-toolkit.md`) | operator, 2026-11-19, the survey session's picker ("researchteam 1.3; the contract first") | the survey-toolkit session | merged on `main` (PRs #223 to #226) and **frozen as version 1 on 2026-11-23** (PR #251, `9538596`), after the first project's first stage that writes evidence; the plan record is reconciled | none | in. Operator, 2026-11-19 |
| F7 | Survey contract, open point 1: the per-study sign-off log, written against the gates-only pattern as agentteams releases it | `docs/survey-toolkit.md`, section 11 | the survey-toolkit session | waits for upstream | agentteams #578 (its PR #588): the gates-only team directory, documented and tested, and whether a main-team HALT binds it | in, as documentation only (proposed) |
| F8 | Survey: explorer contract 1.1 (`basis`, `reporter`, `note`) | `docs/survey-toolkit.md`, section 10 step 2 | the survey-toolkit session | **done**: contract 1.1 merged on 2026-11-20 (PR #238, `5b59aa5`) | none | in (done) |
| F9 | Survey tools: validator, manifest builder, row checks, sign-off verification, enumeration, agents, CI gate | `docs/survey-toolkit.md`, section 10 steps 4 to 8 | the survey-toolkit session | not started, by ruling | #578 for sign-off verification | deferred to 1.3.x or 1.4. Operator, 2026-11-19: no tool before the first project has run a stage |
| F10 | Derived autosync workflow: fetch a release tag without the repository's history | issue #228 | lead | not started | none | in (proposed) |
| F11 | Derived autosync workflow: `persist-credentials: false` on checkout | issue #176 | lead | already on `main`: both checkouts set it and tests assert it; the issue is still open | none | done. T4 verifies it against the issue and closes the issue |
| F12 | Layer-1 compatibility with agentteams 1.3.0's behaviour changes: the routing-loss refusal on overwrite renders, the frozen-fences state, the pin check in a workspace without decision signing | agentteams' cut plan (its #583, finding #16, #555), read as data | lead | to be found in the soak | those changes as released | in. Required for F1 to work |
| F13 | Interim pin of `main` to agentteams `v1.2.2` (its notes label one change as security) | work summary 2026-11-20, Open Obligations | lead | not started | none (a 1.2.x tag) | proposed: do it now, as its own reviewed PR, before F1. Whether a researchteam 1.2.2 is cut from it is a separate operator question (D2) |
| F14 | Release files: the 1.3 line in `docs/release-policy.md`, install instructions naming the new release, changelog, release notes, cut scripts | release policy; PR #156 (stale, names v1.1.2) | lead | not started | none | in. PR #156 is superseded by this and closed with the operator's agreement |
| F15 | One scan rule for every surface (consistent rosters) | issue #61 | none | open since 1.0.1, no plan | unknown | deferred (proposed) |
| F16 | Briefing records for the literature library | PR #135 | another lane; last updated 2026-10-31 | open, not reviewed here | none | deferred (proposed) |

Not release features, but they share files with F1 and are carried here so they are not lost:
- Draft PR #234 (the dated PS-2 exception for automatic head-branch deletion). It waits for the operator to run
  its script. Lane rule in section 3. After it merges: a changelog entry for the retired exemption and the
  exception (the lead writes it), and the next deletion script for merged remote branches (plan P3 step 4).
- `brief.json` still lists agentteams under `s10_cooldown_exempt_repos`; checked at the next render (T5 step 3,
  or T1 B4 if T5 is dropped).
- If D4 adds `scripts/term-index-core/` to PS-2's path list, that is its own PR on `.claude/CLAUDE.md` and its
  projected copies, with `@security` naming them (T2 step 5).

## 2. Target plans

| Id | Plan (in this folder; tracked in `references/plans/`) | Covers | Status |
|---|---|---|---|
| T1 | `release-1.3.0-t1-pin-agentteams-1.3` | F1, F12 | blocked on upstream; the soak part starts at agentteams rc.1 |
| T2 | `release-1.3.0-t2-term-index-switch`. It replaces phases 1 and 2 of `open-1119-p1-term-index-core-switch`, whose phase 0 is done and whose design note and seam table still bind | F2, F3, F4, F5 | the build can be rehearsed against agentteams `dev` after D2 and a `@security` clearance |
| T3 | `release-1.3.0-t3-survey-contract` | F6, F7, F8 | F8 can start once D2 is answered; F7 waits for upstream |
| T4 | `release-1.3.0-t4-derived-workflow` | F10; closes F11's issue | can start once D2 is answered |
| T5 | `release-1.3.0-t5-interim-pin-1.2.2` | F13 | can start once D2 is answered |
| T6 | `release-1.3.0-t6-release` | F14, the candidate, the downstream check, the final | waits for T1 to T4 |

Version and sha256 of each file are in the audit record (section 6) and in the message that hands this plan to
the coordinator. A plan file cannot hold its own hash.

## 3. Lanes

Nothing below starts on a proposed class: all four lanes wait for D2. Then they run in parallel (different
files):
- **Lane A, T5:** `toolchain.lock`, the extras in `pyproject.toml`, `.github/agentteams-autosync-ref`,
  regenerated agent files.
- **Lane B, T4:** `researchteam/scaffold/agentteams-sync-derived.yml` and its tests.
- **Lane C, T3 (F8):** `templates/bibliography-explorer/` (its contract, tests, component and file hashes).
- **Lane D, T2 rehearsal:** the swap is built on a branch against agentteams `dev`, with a manifest marked
  provisional, as a draft PR that is never marked ready and never merged. It needs a recorded `@security`
  clearance naming the `dev` commit first. Nothing from it carries into the real swap unchecked: T2 rebuilds
  the manifest from the signed tag.

What serializes them:
- T5, PR #234, a PS-2 path-list PR (if D4 asks for one) and T1 all touch the lock, the regenerated team or the
  projected Project-Specific Rules. They merge one at a time, T5 before T1; #234 and the PS-2 PR merge whenever
  they are ready. Whichever merges later rebases and repeats its `@security` review at the new head.
- T2 merges only after T1: the equality test compares the copy with the file at the pinned commit.
- F7 is written only after agentteams releases #578. It does not wait for T1, and F8 does not wait for F7.
- T6 starts when T1 to T4 are merged or explicitly dropped from scope by the operator.
- Rule 9: every row starts `pending` (the notes say what it waits for). After each step, the remaining steps
  pass through `@adversarial` and `@conflict-auditor` before the next one starts.
- Tracks never edit `CHANGELOG.md`, `workSummaries/` or plan files; the lead integrates those. A track that
  writes files works in its own worktree. Test runs and API-heavy work do not overlap in time.
- Every merge into `main` needs the operator's live answer naming the PR and head, so each track is its own PR.

## 4. Release procedure

Form: a candidate, then the final, as for 1.2 (proposed; D6). researchteam 1.3.0 is not pin-only.

1. **Soak of agentteams rc.1 (before any pin merges).** A branch pinned to the signed `v1.3.0-rc.1`, with
   the T2 rehearsal on top. Conditions, all required:
   - a recorded `@security` clearance naming the candidate tag, before the branch is made (S-10 applies to a
     candidate even when nothing merges);
   - the PR stays a draft, is never marked ready and is never merged (`main` pins stable tags only);
   - the lock on `main` is untouched, no autosync is dispatched for the branch, and no workflow runs on it with
     write credentials;
   - the branch name is outside every ref a sync reads;
   - renders run in the branch's own worktree and nowhere else;
   - a provisional manifest never reaches `main`.
   Run: the test suite on both Python versions, `validate`, `doctor`, `agentteams --verify-toolchain-pin`, an
   update render and a materialize render on every surface, the term-index tests and `term-check` on every
   project. The frozen-fences state file is cleared before an overwrite render only if upstream's fix is not in
   the candidate, and then only after the operator's confirmation in the picker (S-4) and a recorded
   `@security` clearance. The report goes to a tracked record in this repository (PS-1) and, by message, to the
   coordinator. After the final, the soak and rehearsal branches go to `archive/`.
2. **Pin and build**, after agentteams `v1.3.0` is signed. First re-check what changed upstream between the
   soaked candidate and the final. Then T1, then T2, with T3 and T4 as they are ready.
3. **Freeze.** Declared by the operator (D11), because it also stops other sessions' merges. It needs all of:
   - every "in" feature is merged, and each only-if-ready feature is merged or recorded as moved to 1.3.x;
   - PR #234 is merged or recorded as outside the release; D4 is answered, and any PS-2 edit is merged;
   - `tests (3.10)` and `tests (3.13)` are green on `main`, the characterization tests among them;
   - the lock names the stable tag `v1.3.0` (not a candidate, not a branch commit);
     `check_toolchain.py --verify-tag agentteams v1.3.0` and `agentteams --verify-toolchain-pin` pass;
   - the copy manifest names the lock's agentteams commit; the copy check passes offline and in its network
     form against the signed tag;
   - the recorded `@security` clearance for adopting the beta upstream module exists (S-10), and the
     vulnerability scan status is current and complete;
   - `validate` is clean; `doctor` shows no failure (whether a failed core check is a failure or a warning is
     D4); `term-check` passes on every project;
   - PS-1 to PS-3 are present in every projected copy, and every rendered Claude agent declares `tools:`;
   - an older installed researchteam syncing the 1.3 ref gives the upgrade-first message (design note,
     section 10 point 1), shown by a test;
   - no `@security` HALT or unmet condition stands, and the S-8 search of the regenerated team is clean.
   After the freeze, `main` takes only fixes found by the candidate, release files and records, each by PR with
   the operator's live answer. The autosync is paused or left running from
   the freeze to the final by the operator's choice (D10): an upstream patch release in that window would move
   the lock but not the copy.
4. **Candidate.** Release-prep PR (changelog, notes, policy text, the cut script's tracked copy), reviewed and
   merged. The operator runs the cut script: it creates `release/1.3` at the named commit of `main`, signs
   `v1.3.0-rc.1` and publishes a pre-release. The script carries the 1.2.1 checks (fixed tagger identity,
   registered signing key, the newest 1.2.N release pinned by tag object and required as an ancestor, allowlist
   of changed paths, verification report) and refuses unless all of these hold:
   - the named commit is the reviewed head of `main` with both test checks green;
   - the lock pins the stable `v1.3.0`;
   - the copy manifest names the lock's commit, and the network comparison with the signed tag passes;
   - `agentteams --verify-toolchain-pin` passes;
   - the decisions log holds no unretracted HALT and no `pending` condition.
5. **Downstream check of the candidate.** The next repository in the order makes a dry-run pin to
   `v1.3.0-rc.1`; the coordinator reports the result. A defect is fixed on `main` by PR (with release files and records, the
   only merges `main` takes in this window). `release/1.3` then moves only by fast-forward to that commit of `main`, inside
   the operator's next cut script, after the operator's live answer naming the commit (PS-2). No cherry-pick
   is needed while `main` is frozen.
6. **Final.** The operator's go, then the cut script for `v1.3.0` on `release/1.3` (the candidate plus fixes and
   release files only), with the same refusals. The script marks the release Latest.
7. **After each tag.** Check that `main` contains the tagged commit, as the policy requires. With the
   fast-forward model it does; if it ever does not, `release/1.3` is merged forward by a PR with the operator's
   live answer.
8. **After the final.** `release/1.2` stays open for 1.2.N fixes and does not move to agentteams 1.3. Read back
   the tag object, the peeled commit and GitHub's verification; tell the coordinator; work summary; close with
   `@conflict-auditor`.

### Operator decisions, in order
- **D1.** Confirm in this session the line move: researchteam 1.3 pins agentteams 1.3 (the relayed "v1.3.0
  push" ruling).
- **D2.** Scope: F5, F7, F8, F10, F13, F15 and F16 as proposed, or changed. For F13 also: cut a
  researchteam 1.2.2 from it, or not.
- **D3.** The held request to agentteams (seam table, deliverable 3): send it now, or keep it held.
- **D4.** Two open questions of the design note: a failed core check in doctor is a failure or a warning;
  `scripts/term-index-core/` joins PS-2's list of paths that need a `@security` PASS. The note's third question
  is settled by this plan with the stricter answer: at every release the core pin equals the lock's commit
  (freeze criteria, cut-script refusals, T2). The operator sees that choice when this plan is reviewed.
- **D5.** The signed decision row for the line move (`release-line-agentteams-1.3`).
- **D6.** The release form: candidate then final.
- **D7.** Each merge into `main`: live answer naming the PR and head.
- **D8.** The commit for `release/1.3` and the candidate; the go for the final.
- **D9.** Closing PR #156 as superseded.
- **D10.** The autosync from the freeze to the final: paused, or left running.
- **D11.** Declaring the freeze.
- Each clearing of the frozen-fences state file (S-4), if one is needed.

### Operator scripts that will be needed
Each is a `.sh` file with one location-independent command, reviewed by `@security` before it is handed over.
Numbers follow the existing series and are fixed when written.
- Sign and register the line-move decision row (T1).
- Only if D2 asks for a researchteam 1.2.2: its cut script (T5).
- Cut `v1.3.0-rc.1`, creating `release/1.3` (T6). One more per further candidate.
- Cut `v1.3.0` (T6).
No script changes repository settings, rulesets or keys: `release/**` and tags are already covered.

## 5. What researchteam 1.3.0 needs from agentteams

- **Releases:** the signed `v1.3.0-rc.1` for the soak, and the signed `v1.3.0` for the pin. The tag object and
  peeled commit are read and verified at pin time (`check_toolchain.py --write-lock --tag`), not copied from a
  message. The release key is unchanged, and agentteams stays in the signed first-party toolchain group.
- **Features relied on:**
  - the term-index core (its issue #548, PR #551): `term_index.py` and its helper at the tag, with the configuration fields
    and functions the design note's section 8 lists, and a reader for the `researchteam-term-register` schema;
  - the gates-only team directory and the HALT ruling (its #578), for F7's text only;
  - the pin check in a workspace without decision signing (its #555);
  - release notes that state the routing-loss refusal and its migration (its #583);
  - every rendered Claude agent declares `tools:` (its #511, re-checked at the pin).
- **Not relied on:** the WASM items, the term-index follow-ups (its #584), and public equivalents of the two
  private symbols (F5 falls back).

## 6. Audit record

Version 1 was reviewed on 2026-11-20 by this team's `@adversarial`, `@conflict-auditor` and `@security`. These
are records of reviews, not signed decision rows. Version 2 adopted their findings; version 3 adopted the
second pass.

- **`@security`: CONDITIONAL PASS, seven conditions, all adopted.** A clearance and a list of limits for the
  candidate soak and the `dev` rehearsal; the operator's confirmation before the frozen-fences file is
  cleared; complete path lists for the T1 and T5 reviews; fail-closed fetch in T4; refusals in the cut
  scripts; added freeze criteria; `release/1.3` moves by fast-forward only. Nothing forbidden by S-1 or S-8
  was found in the files. Cleared for: nothing; a plan review only.
- **`@adversarial`: metaplan, T1, T2, T5 and T6 CONDITIONAL; T3 and T4 SOUND. Seven blocking, five advisory,
  all adopted.** The changelog criterion moved from the freeze to the candidate gate; the CI job and the PS-2
  path-list change got a home in T2; "manifest commit equals lock commit" and the autosync decision were added;
  a 1.2.2 path and "newest 1.2.N as ancestor" were added; the forward-merge rule was matched to the policy;
  rehearsal output is provisional; F1 reads "pending D1"; dependency columns were corrected; open obligations
  are carried; the freeze names real commands; the coordinator's assignment is a scheduling input; the freeze
  is the operator's decision.
- **Second pass on version 2 (`@conflict-auditor`): one blocking and three advisory, all adopted in version 3.**
  The third design question is settled by the plan instead of being asked again; release files and records
  may merge during the freeze; cross-plan waits are written into the step notes; four agent assignments were
  corrected.
- **`@conflict-auditor`, first pass: 15 findings, 5 blocking, all adopted.** F11 was already done (verified in the scaffold,
  lines 84 and 242); renders moved off a read-only agent; a new T2 file replaces P1's phases 1 and 2, which are
  marked superseded there; "only candidate fixes" replaces "nothing else merges"; the cut-time copy check was
  added; merges go to `@git-operations`; T3 names the explorer's real files; statuses start `pending`; the
  `--verify-tag NAME TAG` form and an install step before `--write-lock`; the issue and PR numbers of the
  upstream core are both named.
- Sha256 of each file at each version: in the hand-over message and in the pull request that tracks these
  plans.

## 7. Not in 1.3.0, and why

- **Survey tools (F9):** the operator ruled that no tool is written before the first project has run a stage.
- **Consistent rosters (F15):** no owner and no plan; needs fresh analysis against agentteams 1.3.
- **Briefing records (F16):** another lane's PR, not reviewed for this line.
- **A single-file upstream core and the three small upstream gaps:** the request is held; the design loads the
  two-file core without them.
- **The agentteams governance-vocabulary register and `--term-check` gate:** upstream deferred them past its
  1.3.0 (only its first term-index PR is in scope), so researchteam adopts nothing from them.
- **Any change to the term index's behaviour:** the switch must be invisible; the freeze on term-index scope
  holds until it has shipped.

## Update, 2026-11-23 (the lead changed hands on 2026-11-22; facts only, no decision D1 to D9 is answered here)

- **F6:** the survey contract is frozen as version 1 (PR #251). T3's step 4 ("the specification stays labelled
  v0-unstable in 1.3.0") no longer holds: 1.3.0 ships the frozen contract. Its open points were renumbered at the
  freeze; open point 1 (the per-study ledger, F7) keeps its number.
- **F8:** done on 2026-11-20 (PR #238). Nothing of it is left for 1.3.0.
- **F9:** operator ruling, 2026-11-23 (picker): the survey tools are planned for the minor release after 1.3.0.
  Plan: `references/plans/survey-tools-2026-11-23.plan.md`. They are out of 1.3.0's scope.
- **New on `main` since version 3, all of which 1.3.0 will carry:** the concept-map template, exporter and
  protocol (PR #247; `docs/concept-map-protocol.md` is a scholarly managed file); CI installs Graphviz and checks
  for Node (PR #250); this repository's own toolchain-group file, sequence 5, signed with `opr-2026-11` (PR #248);
  the verify key `opr-2026-11` beside `op-2026` and seven re-signed decision rows (PRs #244, #245).
- **Soak order** as the fleet's coordinator gave it on 2026-11-23: the first soak repository, then researchteam,
  then the third. The agentteams freeze is clear and its release branch is next.
- **Still open for the operator:** D1 to D4, D6 and D9.

## Update, 2026-11-24 (rulings answered in this session's picker, and T1 done)

- **D1 answered: yes.** researchteam 1.3 pins agentteams v1.3.0.
- **D2 answered: the interim pin is dropped.** No pin to agentteams 1.2.2 and no researchteam 1.2.2 (T5 is
  recorded as dropped). The rest of the scope stands as proposed.
- **D4 answered.** A failed term-index core check is a doctor failure, not a warning, and
  `scripts/term-index-core/` joins PS-2's list of paths that need a `@security` PASS (its own PR on
  `.claude/CLAUDE.md`, in T2).
- **D5 done.** The operator signed `release-line-agentteams-1.3` with `opr-2026-11` (script 27).
- **D6 answered: candidate, then final.**
- **T1 is done.** agentteams v1.3.0 was already final, so part A's candidate soak on a draft branch was not run;
  the final was soaked in a separate checkout instead. Part B merged as PR #254 (`c92fc56`): the lock, both extras
  and the autosync ref name `536306d2502e3db338846677f2d37489531ac8e7`, and the team is regenerated on four
  surfaces. The review record is `docs/release/pin-agentteams-v1.3.0.decision-spec.json`.
- **The one test that failed in the first soak run is not a 1.3.0 change.** It targets an agentteams 1.0.0
  interpreter and runs only when `RT_TEST_AGENTTEAMS_PYTHON` is set; the session had pointed it at 1.3.0. The
  triage record (`open-1119-p4-test-triage.md`) already says to unset it.
- **For agentteams:** the generated `operator-decision.reference.md` uses `@pr-manager` as an example in a team
  without that agent. Reported to the release coordinator; not hand-edited.
- **Next:** T2 (term-index core switch), then T3 open point 1, T4, the freeze (D11, D10), the release-prep PR and
  the operator's cut (D8).
- **Still open for the operator:** D3, D8, D9, D10 and D11; D7 at each merge.
- **T2 is done (same day).** The swap merged as PR #256 (`e15b3fb`): `scripts/term-index-core/` holds the two core
  files of the signed agentteams `v1.3.0` as exact bytes, the engine is adapters, and `term-core.yml` compares the
  copy with the signed tag on pull requests. PS-2 now names `scripts/term-index-core/` (PR #255),
  `scripts/check_term_core.py` and `scripts/term_index_engine.py` (PR #257; operator's answer "Add both"). No
  rehearsal against `dev` was run, because the signed tag was already out. Two edge cases changed, as the design
  note accepts (a linked or oversized register's message; a symlinked index directory reads as stale).
- **Consequence to keep in mind at the freeze:** a move of the lock's agentteams pin now runs `term-core.yml`, and
  it fails unless the core moves with it.
- **Next:** T3 open point 1, then T4.
- **T3 is done (same day).** Open point 1 of the survey contract is closed by PR #258 (`41d76d9`): section 6.2
  gives the per-study sign-off log's folder and the HALT rule, from agentteams 1.3.0's released pattern. Operator
  ruling in the picker: the folder may be the only home of the verify keys and approver list, with the limit
  stated; a trust root outside the repository is the contract's new open point 7. The contract stays version 1.
- **Next:** T4, then the freeze.
- **T4 is done (same day).** PR #259 (`440b526`): the derived workflow scaffold's release-locked check fetches the
  tag shallowly, with one retry, and fails closed. Issue #228 is closed by the merge and #176 with the evidence
  that it was already fixed.
- **All four target plans T1 to T4 are done; T5 was dropped.** What remains is T6: the freeze (D11, D10), the
  release-prep PR, the operator's cut of `release/1.3` and `v1.3.0-rc.1` (D8), the downstream dry run, and the
  final. D3 and D9 are still to be asked.
- **D11 answered: the freeze is declared** on `main` at `440b5269145fb3334526c4929db3110f991866d3` (operator's
  picker answer, 2026-11-24). Checked there before the question: `tests (3.10)` and `tests (3.13)` green; the lock
  at the signed agentteams `v1.3.0`; `--verify-tag`, `--verify-toolchain-pin` and the group pass; the core check
  offline and against the signed tag; `validate`; `doctor` with no failure; `term-check` on every project; PS-1 to
  PS-3 in every projected copy; all 33 rendered Claude agents declare `tools:`; the upgrade-first message has
  tests; no HALT; security intelligence fresh. From here `main` takes only fixes the candidate shows, release
  files and records, each by PR with the operator's live answer.
- **F12:** the update render on all four surfaces and the pin check pass under agentteams 1.3.0. An overwrite
  (`materialize`) render does not apply to this upstream repository, which refuses it; the downstream dry run on
  the candidate covers it.
- **D10 answered: the autosync is paused** from the freeze to the final. Enabling or disabling a workflow is a
  repository setting, so the operator runs script 28 (`archive/2026-W48/operator/28-pause-autosync.sh`). The stale
  autosync PR #246 is closed as superseded.
- **Pending conditions, operator ruling:** the candidate cut script refuses on a `pending` condition in any
  decision row added since `v1.2.1` and reports older ones without refusing. One older row is pending (2026-10-22,
  a documentation fix merged in the agentteams repository); it shipped under three earlier releases.
- **D3 answered: the held request to agentteams is sent** (to the release coordinator's session, 2026-11-24), for
  a later agentteams release. It does not affect 1.3.0.
- **Still open for the operator:** D8 (the commit for `release/1.3` and the candidate; the go for the final), D9
  (closing PR #156, after the release-prep PR), and D7 at each merge.
- **Release-prep PR merged.** PR #260 (`26ee061108b95229ad74060f4456442c19dff214`, merged at the reviewed head
  `cdfa940`): the 1.3.0rc1 changelog section with the upgrade steps, the release notes, and the tracked copy of
  the candidate cut script (29) with its `common.sh` and script 28. `@security` PASS at `cdfa940` after three
  reads; the release coordinator's review, read as data, found nothing blocking at that head. Both test checks
  are green on the merge commit. The script's freeze allowlist is `CHANGELOG.md`, `docs/release/`, `docs_src/`,
  `references/plans/` and `workSummaries/`: documents under `docs/` are synced into derived repositories.
- **With the operator:** script 29 (cut `release/1.3` and sign `v1.3.0-rc.1` at `26ee061`; D8) and script 28
  (pause the autosync).
- **Owed at the final's release files** (outside the candidate's allowlist): install instructions naming
  `v1.3.0` (README, CLAUDE.md and its scaffold template, the framework and getting-started pages; closes PR #156,
  D9); "older than 1.3.0" becoming "older than 1.3.0rc1" in `docs/term-index-protocol.md` and the bridge message;
  the release lines listed in `docs/CONTRIBUTING.md`. The final's cut script needs an allowlist that admits them.
- **Another session** (researchteam-80) asked whether to work on the release after the operator asked it to
  proceed; it is holding, and was told this session leads T6.
- **The autosync is paused.** The operator ran script 28 on 2026-11-24; the workflow reads back as
  `disabled_manually`. It is resumed with the same script (`resume`) after `v1.3.0` is final.
- **The final's release files are drafted (2026-11-24), while the candidate cut is with the operator.** Draft PR
  #261 (`release/final-1.3.0`): the `1.3.0` changelog section and release notes, install instructions naming
  `v1.3.0` with a guard test (supersedes #156), `docs/CONTRIBUTING.md` brought up to date, "older than 1.3.0rc1"
  in `docs/term-index-protocol.md`, and the tracked copy of the final cut script (30). The bridge script's comment
  keeps "older than 1.3.0", so that no synced script differs between the candidate and the final.
  `@security` gave CONDITIONAL PASS and `@conflict-auditor` two blocking findings at `7d48b81`; both sets are
  addressed in `4bbeeb8`, and `@security`'s second read is running. The PR stays a draft until the candidate is
  cut and the downstream dry run has reported. Script 30 needs the candidate's tag object before hand-over.
- **The candidate is cut (operator, script 29, 2026-11-24 local time).** `v1.3.0-rc.1` is tag object
  `22359c747fd2bd86e8af826e31fd84ca476181ab`, peeling to `26ee061108b95229ad74060f4456442c19dff214`; `release/1.3`
  and `main` are at that commit. Read back by the session from the remote: the signature is good and by the
  release key, GitHub reports the tag verified, and the GitHub release is a pre-release (Latest is still
  `v1.2.1`). The script reported one older pending condition and refused nothing. The tag's creation used the
  operator's admin bypass of the tag ruleset, as the ruleset intends. The tag object and peel were sent to the
  release coordinator for the downstream dry run. Script 30's tracked copy names the tag object (`662fa69` on
  PR #261); `@security` is reading that change.
- **Next:** the dry run's report; then the operator's answer on merging #261 and closing #156, script 30, and
  the resume of the autosync.
