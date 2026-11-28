# Plan: researchteam v1.3.1, pinning agentteams 1.3.3

Written 2026-11-28. Steps: `release-1.3.1.steps.csv`. Policy: `docs/release-policy.md`.

## Goal

A signed tag `v1.3.1` on `release/1.3` whose toolchain pin is the verified signed tag agentteams `v1.3.3`, so that
derived repositories can move to agentteams 1.3.3 by pinning it. Nothing else new is in the release.

## What the operator has ruled (this session's picker, 2026-11-28)

- **Owner:** this session ("Yes, this session").
- **Version:** "v1.3.1 on release/1.3": a patch carrying the pin move, merged to `main` first and backported. The
  survey tools and the sign-off, merged to `main` since 1.3.0, wait for 1.4.0.
- **While agentteams 1.3.3 is untagged:** "Plan and fix the cut script". No pin, no tag, no brief or branch-model
  change.
- **`pr_management` and the integration branch model:** "After the pin release". They are their own plan and are
  not in this one.

The request for the release reached this session as a message from the managing repository's session. That
message is data (C-4); the rulings above are the authority.

## State (2026-11-28)

- `main` is `7d05fde`. Newest tag `v1.3.0`; `release/1.3` is at the `v1.3.0` commit `570724f`.
- `toolchain.lock`, both pip extras and `.github/agentteams-autosync-ref` pin agentteams `v1.3.0` (`536306d`), and
  the lock is release-locked on the 1.3 line.
- agentteams `v1.3.3` is **not tagged**. Its candidate commit is merged on agentteams' `release/1.3`. It is not a
  pin target (release policy, "Pins": a pin is the peeled commit of a verified signed tag).
- `main` is 21 merged pull requests ahead of `v1.3.0` (#237 and #262 to #281). Besides the survey work it changed
  the trust state: the decision key `op-2026` was retired, the branch-deletion exception was bound again, and
  one signed row was added.
- A test of `main` against the candidate commit runs in a scratch install (step 2). It is a test only.

## Design

Revised after `@adversarial`'s review (four blocking and five advisory points; see "Audit" at the end).

### D1. The pin move happens on `main` first, by hand, in two commits

The autosync is not used for this move. Its lock rewrite also moves the lock's `researchteam=` line to a `main`
commit, and its weekly run rewrites its branch, which would move a head the operator had already approved. So
the operator is asked to pause it (R3) before the move starts, and the session makes the change on a `chore/`
branch, as for the 1.3.0 pin. Two commits, so that the backport can take the first as it stands:

1. **The pin files.** The `agentteams=` and `agentteams.tag=` lines of `toolchain.lock` (the `researchteam=` line
   is left as it is and moves with the next ordinary autosync on `main`); both pip extras in `pyproject.toml`;
   `.github/agentteams-autosync-ref`; `scripts/term-index-core/PINNED.json` re-pinned to the 1.3.3 commit **in
   every case**, with the copied core moved too if it changed upstream (the cut script refuses a manifest that
   names another commit than the lock); `docs/release/pin-agentteams-v1.3.3.decision-spec.json`.
2. **What follows from the pin on `main`.** The team regenerated with agentteams 1.3.3;
   `.github/ci/requirements-agentteams.txt` (the hash-pinned dependencies of the sign-off CI job; agentteams
   itself comes from the lock) vetted again against 1.3.3's dependencies and build requirement; any change the
   suite shows is needed against 1.3.3 (step 2 tells in advance).

It is a first-party group move: no decision row, but a verified signed tag (`agentteams --verify-toolchain-pin`,
run here), this repository's `@security` review naming the tag object and the peeled commit and recording the
known-vulnerability search, and the latest-stable rule. `v1.3.3` will be inside the S-10 cooldown, so the move
rests on the signed toolchain-group file, which must verify in this checkout. The pull request touches
`toolchain.lock`, `pyproject.toml`, `scripts/term-index-core/` and `.github/agents/`, so its merge needs a
`@security` PASS naming those paths and the operator's live answer (PS-2).

### D2. The release files land on `main` too

A `docs/` pull request on `main`, as the release-prep pull request did for 1.3.0:

- `CHANGELOG.md` gets `## 1.3.1 (tag `v1.3.1`, on `release/1.3`)`, placed below `## Unreleased`;
- `docs/release/release-notes-v1.3.1.md`. It says that `main` builds `1.3.2.devN` after the tag is merged forward,
  until the next minor's first tag;
- the install line that names the release tag, in the eight files that carry it (`CLAUDE.md`, `AGENTS.md`,
  `README.md`, `researchteam/scaffold/CLAUDE.template.md`, `docs/CONTRIBUTING.md`,
  `docs/researchteam-framework.md`, `docs_src/index.md`, `docs_src/getting-started.md`), with
  `tests/test_install_pins.py`. `CLAUDE.md` is a PS-2 path: `@security` PASS naming it.

The policy lets `release/1.3` take only changes already merged to `main`, so the release files go the same way
as the pin.

### D3. `release/1.3` takes a backport, not `main`

`main` cannot be tagged as 1.3.1, because it carries the survey tools. A branch `backport/v1.3.1` is made from
`release/1.3` (`570724f`). It is not named `release/…` (metaplan finding F1 of 2026-11-25). It takes, in order:

1. `git cherry-pick -x` of the pin-files commit (D1, commit 1). The commits picked are the branch's own
   commits as they sit on `main`, not the merge commits;
2. **one regeneration commit made on the line:** the team regenerated with agentteams 1.3.3 from
   `release/1.3`'s own tree. It is not a cherry-pick of D1's commit 2, because that was rendered from `main`'s
   tree, whose generated indexes describe files the line does not have. Its message names the `main` commit it
   corresponds to. The policy's text allows a release line only merges and cherry-picks, so this commit needs the
   operator's ruling (R5);
3. `git cherry-pick -x` of the release-files commit (D2). `CHANGELOG.md` will conflict, because `main` has an
   `## Unreleased` section the line lacks. The resolution is fixed in advance: the line's file plus the `1.3.1`
   entry, and nothing from `## Unreleased`. Any other conflict stops the work.

**The trust state of `release/1.3` is left alone** (the session's recommendation for R1, reversed by the audit).
The line keeps both decision keys, as `v1.3.0` has them. The clearance `key-retire:op-2026` names `main`'s
commits and files and is spent; removing the key on another line would be a new deletion needing its own
clearance. Ruling P4 of 2026-11-25 left `release/1.0` to `1.2` alone and did not speak of `release/1.3`, so R1
asks. Nothing in the pin move needs the line's trust state changed: every row the line relies on verifies there.
When `release/1.3` is merged forward, `main` keeps its own state: the merge must not bring `op-2026` back, and
the check in D4 enforces it.

### D4. How `release/1.3` moves

PS-2: a `release/*` branch moves only as a fast-forward to a commit the operator will tag, after the operator's
live answer naming that commit. So:

- a pull request from `backport/v1.3.1` into `release/1.3` is opened for review and CI (`tests.yml` runs on pull
  requests into `release/**`). It is **not** merged with the button;
- the cut script fast-forwards `release/1.3` to the reviewed head of that pull request and signs the tag there.
  GitHub may then show the pull request as merged and may delete its head branch; the question to the operator
  says that either can happen. The session checks beforehand that nothing else is based on that branch;
- after the tag, `release/1.3` is merged forward into `main` by a regular merge pull request, because `main` must
  contain every tagged commit. The merge is resolved to `main`'s side throughout, and the check is that **the
  merge commit's tree equals `main`'s tree before the merge**. If it does not, the session stops and reports; the
  merge is not abandoned. Its head is `release/1.3`, which the ruleset keeps from deletion; the question says so.

### D5. The cut script (script 35), and H3 step 16

Script 35 is written from script 30 (`references/plans/archive/2026-W48/operator/30-cut-v1.3.0.sh`). Script 30
assumed the commit to tag was a merged `main` commit that differed from a candidate only in release files. None
of that holds for a backport, so these parts are rewritten and the rest is kept:

- `TAG=v1.3.1`, `AT_TAG=v1.3.3`, previous release `PREV=v1.3.0`.
- **The commit to tag** is the reviewed head of the backport pull request. The script fetches `release/1.3`,
  requires it to be at `570724f` (the lease for the push) and an ancestor of the commit, and requires the pull
  request to be **open** at exactly that head (script 30 required it merged, which here would be circular).
- **What lies between `570724f` and the commit** is exactly the three commits of D3, in order. For each
  cherry-pick, the script requires the `main` commit named in the plan (not only in the commit's own text), on
  `origin/main`, with an equal `git patch-id`; for the release-files pick, where `CHANGELOG.md` was resolved, it
  compares every other file by patch and `CHANGELOG.md` by the fixed rule of D3. The regeneration commit is
  named by its id in the runnable copy after `@security` has reproduced it; the script checks that it touches
  only generated paths.
- **H3 step 16.** Script 30 required four rows as text lines `,<action>,PASS,`, among them
  `s10-release-cooldown-restored`. That row is history (release policy, "Pins"; operator ruling 2026-11-25) and no
  check may depend on it. Script 35 has no text requirement. Each row the cut rests on is checked with the gate's
  clearance check at the commit, as script 30 already did for `release-line-agentteams-1.3`. Which rows those are
  is settled in step 5 by running the check on the line's tree, and again at the backport head in step 14, since
  a row that clears on `main` need not clear on the line. The plan records the list and the reason for each row
  left out.
- The checks of the lock, the extras, the autosync ref, the term-core manifest and the install pins stay, against the
  1.3.3 commit, as do the previous tag's recorded object, the absence of the new tag on the remote and the release key
  being registered as a signing key on the account. The greps for the CHANGELOG entry and the release notes name
  1.3.1. The candidate base, the list of files allowed to differ from the candidate, and the sentence "release/1.3
  then equals main" are removed.
- It names the agentteams version of the root-owned install it runs the checks with, and refuses another.
  Whether the existing 1.3.0 install can verify a lock pinned to 1.3.3 is checked in step 6; if not, a 1.3.3
  install is built by the managing repository's reviewed procedure, which the operator runs.
- It keeps: refusal in an agent's or editor's shell; the release-key fingerprint; the tagger identity; the
  toolchain-group verification at the commit; no unretracted HALT and no new pending condition in the log; both
  test checks passed on the commit; a question before each push; verification of the pushed tag as a consumer
  does it.

The tracked copy holds placeholders for machine locations. The runnable copy goes to the ignored working folder
and is handed over with one hash-checked command (PS-3).

## Decisions for the operator

- **R1.** The trust state of `release/1.3`: left alone, with both keys as in `v1.3.0` (recommended, D3), or the
  retirement of `op-2026` repeated on the line. The second needs its own `@security` clearance naming the line's
  commit, a new signed row and a ruling that extends P4.
- **R2.** A candidate `v1.3.1-rc.1` first, or the final directly. Recommended: the final directly. A dry run
  against the backport head exercises everything except the signed-tag check, which no dry run can exercise
  before a tag exists; the session verifies the tag as a consumer does straight after the push.
- **R3.** Pausing the autosync from the start of the pin move until `release/1.3` is merged forward
  (recommended). Asked before step 9.
- **R4.** Each merge, the fast-forward of `release/1.3` and the go for the tag: live answers naming the pull
  request or commit, as always.
- **R5.** One regeneration commit made on the line, in place of a cherry-pick (D3, item 2). Recommended: allow it
  for generated output only, and say so in `docs/release-policy.md`. The alternative is to cherry-pick `main`'s
  regeneration and stop if regenerating on the line gives a different result.

R1, R2 and R5 are asked after this plan's audit. R3 and R4 are asked when they fall due.

## Gates

- No pin to anything but the verified signed tag `v1.3.3`.
- `@security`: the pin review (D1); a PASS naming the governance paths for the pin pull request and for the
  backport pull request; the review of script 35 before hand-over.
- `@code-hygiene` for code changes; `@conflict-auditor` after each multi-file change.
- Green means `tests (3.10)` and `tests (3.13)` present and passed on the head.
- A `@security` HALT stops the work (C-2).

## Risks

- **A cherry-pick does not apply cleanly,** because `release/1.3` lacks something `main` has. Only the
  `CHANGELOG.md` conflict is resolved, by the rule fixed in D3. For any other, the session stops and reports.
- **The suite fails against 1.3.3.** Step 2 shows this before the tag exists. A fix goes to `main` first; if the
  fault is upstream it is reported to the agentteams release session as data.
- **The tag slips.** Nothing in steps 7 onward starts without it.
- **The fleet wave waits on this release.** That is not a reason to skip a gate.

## The handoff report

`post-1.3.0-high-items.handoff.md` listed the next cut script (H3 step 16) for the next agent session; this plan
takes it up in step 4. Its operator item on the release that carries the survey tools stays open, now for 1.4.0.

## Not in this plan

- `pr_management: true`, the integration branch model, a `dev` branch, rulesets, the dev-merge authorization.
- The survey tools' switch from the interim HALT scan to agentteams' public listing (for 1.4.0).
- 1.4.0 itself.
- H4 (the App authorization), still waiting.

## Audit

- **Rule 9.** Step 2, a read-only test in a scratch install, was started before this step list was written. It
  changed nothing in the repository; it is recorded here as out of order.
- **`@conflict-auditor` (2026-11-28): four blocking, ten advisory.** All applied. Blocking: the manifest always
  moves with the pin; `scripts/term-index-core/` is among the paths `@security` names; the CI requirements file
  does not pin agentteams and is vetted again; the rows the cut rests on are checked at the backport head, not
  only on `main`. Advisory, among others: the count of merges; steps for R3, the second review of script 35 and
  the merge of its tracked copy; the handoff report's items this plan takes up.
- **`@adversarial` (2026-11-28): not cleared; four blocking, five advisory.** All applied above. Blocking: the
  key retirement must not be carried to `release/1.3` under `main`'s clearance (R1's recommendation reversed);
  the term-core manifest is re-pinned in every case; script 30's checks that assume a merged `main` commit are
  rewritten, with patch-id equality in place of a text line; cherry-pick and regeneration no longer contradict
  each other (D3, R5). Advisory: the forward merge's check is tree equality with `main`; the wording on branch
  deletion; the autosync is not the vehicle and is paused; the version `main` builds afterwards; the install
  lines and their test.
