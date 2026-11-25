# Metaplan: the high-benefit items after researchteam 1.3.0 (2026-11-25)

Asked for by the operator on 2026-11-25: a plan for each item rated "high net benefit" in the session's list of
what remains after `v1.3.0`, coordinated here, audited, revised, then carried out, in parallel where that is safe.

**This metaplan approves nothing.** Every merge into `main` needs the operator's live answer naming the pull
request and its head (PS-2). Every signature is the operator's, in their own terminal. A `@security` HALT stops
the work it names (C-2).

## 1. The six target plans

| Id | Plan file | What | Kind |
|---|---|---|---|
| H1 | `post-1.3.0-h1-local-toolchain` | Bring the local toolchain to the commits `toolchain.lock` pins | remediation |
| H2 | `post-1.3.0-h2-release-policy-text` | `docs/release-policy.md`: the lock step of a line move; the autosync section | remediation |
| H3 | `post-1.3.0-h3-retire-op-2026` | Retire the old decision key `op-2026` (target 2026-12-05) | remediation |
| H4 | `post-1.3.0-h4-app-authorization` | The App authorization row (fleet agent, Tier 1) | remediation |
| H5 | `post-1.3.0-h5-survey-tools-a-d` | Survey tools, steps A to D of `survey-tools-2026-11-23` | development |
| H6 | `post-1.3.0-h6-survey-sign-off` | Survey tools, step F: sign-off verification and stage refusal | development |

H5 and H6 carry out steps of the existing plan `survey-tools-2026-11-23.plan.md`, which stays the authority on
what the tools are. The contract `docs/survey-toolkit.md` (version 1) is the specification.

## 2. What depends on what

- H1 first and alone, before wave 1 starts: the bootstrap changes the main checkout's `.venv` in place, so no
  other local check may run against it while it is half done. Every later local check then runs the pinned code.
  Worktrees have no `.venv` of their own; a step that needs the toolchain says which interpreter it uses.
- H2 touches one document and nothing else depends on it.
- H3 runs on its own track and is not held to the waves: it has a date (2026-12-05) and touches no file the
  survey work touches. It depends on H4 in one respect. The key-rotation plan (2026-11-22) lets `fleet-agent-pilot-2026-11` lapse and
  says a new authorization "is drafted and reviewed before `op-2026` is retired". So before the retirement the
  operator either signs the H4 row or rules that the old key is retired without it.
- H4 waits for the operator's word (picker, 2026-11-25: "Regenerate when I ask"). No session work before that.
- H5 is a chain: A, then B, then C, then D, each its own reviewed pull request.
- H6 needs only H5 step A. Step A ships the gate states and the one function that turns a state into a refusal;
  until H6, verification answers `UNAVAILABLE`, and a blocking gate in that state refuses (contract rule 1.7).
  H6 adds the verification and nothing a later step must be rewritten for. H5 step D's post-steps call the
  refusal function (contract 4.5), so in a study with a blocking S6 they refuse until H6 is merged: D can be
  built and tested before H6, and is only useful to such a study after it.
- H3 shares no path with H5 and H6: H3 changes the decisions logs, two key stores and the registry. H5 and H6
  share the survey core, the fixtures, `researchteam/_manifest.py` and the bridge script with each other, so
  they are never built at the same time on the same files without a rule: whichever of H5-B and H6 merges second
  merges `main` first and resolves there, and H5-C (which writes gate state into provenance) starts from a
  `main` that has H6, or records that it does not.
- Step E of the 2026-11-23 plan (the explorer projection) was rated medium-high, not high, with issue #243. It
  is not in these plans and stays `pending` in that plan. The 2026-11-23 plan calls A to E the smallest useful
  set; these plans deliver A to D and F and say so wherever a release is discussed (decision P7).

## 3. Waves

| Wave | In parallel | The next wave starts when |
|---|---|---|
| 0 | H1, alone | H1's checks pass, or its failure is recorded and the old state restored |
| 1 | H2 (pull request); H5 step A (build, review, pull request) | the H5-A pull request is merged (H2's merge is not waited for) |
| 2 | H5 step B; H6 (step F) | B is merged |
| 3 | H5 step C | C is merged |
| 4 | H5 step D, with the comparison against the reference tool run on the pull request's head | D is merged |

Beside the waves, on their own tracks: H3 (phase 1 starts with wave 1; each later phase starts when the one
before it ends), and H4 (starts when the operator asks). The two meet only at the decisions log and the
registry; the H3 and H4 plans say who goes first.

Parallel work runs in separate worktrees, one branch per pull request. New work branches use the prefixes
`docs/CONTRIBUTING.md` names (`feat/`, `fix/`, `docs/`, `chore/`), never `release/` (finding F1 below). This
plans branch and the existing `governance/fleet-agent-tier1` keep the names they already have.

## 4. Reviews that every target plan uses

- `@adversarial` and `@conflict-auditor` on this metaplan and the target plans before the first step, and on the
  steps that remain after each step that changes what a later step assumes (Rule 9). A step that ends as planned
  is recorded without a new round.
- `@code-hygiene` on every code pull request; `@technical-validator` compares each tool with the contract's text.
- `@security` on H3 (all of it), H4, H6, H5 step A's path handling and file reads, and on any pull request that
  touches a PS-2 path.
- `@conflict-auditor` closes each multi-file change.
- Both test checks green on the head before a merge is put to the operator.

## 5. Decisions that are the operator's

- **P1.** Each merge (PS-2), one question per pull request, naming its head.
- **P2.** H3: whether the two cooldown rows lapse (the session's recommendation) or are signed again as a new
  decision (section "Rows" of the H3 plan).
- **P3.** H3: retire `op-2026` before H4 is signed, or after.
- **P4.** H3: the `release/1.x` branches' key stores: left alone, or carried in the next tagged release on each
  line. PS-2 allows no other change to a `release/*` branch.
- **P5.** H3: the retirement itself, by running its script; the date if 2026-12-05 cannot hold; and, if the
  branch-deletion exception cannot be re-registered cleanly, whether to turn the repository setting off instead.
- **P6.** H4: when.
- **P7.** H5 and H6: the release that carries them (the next minor, as ruled on 2026-11-23, or a split), given
  that step E is not in these plans.
- **P8.** H5 and H6: each proposed contract change, where the contract's text is silent.
- **P9.** H6: if verification needs a private agentteams name, whether to wait for the agentteams release that
  makes it public or to pin the private call under a test.
- **P10.** H6: whether a CI job that installs agentteams is added (a workflow change, PS-2), so that the
  `CLEARED` path runs in CI. Until then it runs only locally and the pull request records that run.
- **P11.** H2: whether "the operator pauses the autosync while a release is cut" is written as standing
  procedure or as what was done for 1.3.0.

## 6. Findings recorded while planning

- **F1. Three merged work branches cannot be deleted.** `release/pin-agentteams-1.3`, `release/prep-1.3.0` and
  `release/final-1.3.0` were this session's work branches for the 1.3.0 pull requests. Their names match the
  `release/**` ruleset, which forbids deletion with no bypass, so GitHub did not delete them at the merge and
  nobody can without a ruleset change. `docs/CONTRIBUTING.md` already says never to create a `release/*`
  branch; the session broke that rule. They are harmless (each is an ancestor of `main`) but they sit beside
  the real release lines. Removing them is the operator's choice and a ruleset change, so it is not in these
  plans; work branches are named otherwise from now on.
- **F2. The key-rotation plan's last step is done in fact.** The seven re-signed rows are on `main`; its step 7
  is closed in H3 phase 1 with the evidence.

## 6a. Audit of this metaplan and the target plans (2026-11-25)

- **`@adversarial`: CONDITIONAL.** Six blocking, twelve advisory. H2 sound; H3 phase 1 may proceed and its later
  phases were unsound as first written; the others conditional.
- **`@conflict-auditor`: three blocking, thirteen advisory.** No private detail in the plan files.
- **Adopted, all blocking findings and the advisory ones named here:**
  - H1: the bootstrap installs in place and keeps no backup; H1 now copies `.venv` aside first and runs alone.
  - H3: the recommendation on `s10-release-cooldown-restored` is reversed (its lineage includes another
    `op-2026` row, so it cannot be re-signed field for field); two key stores hold the old key, not four; the
    one script became two steps, each with its own pull request and clearance; `release/*` branches are not
    changed by pull request; the `.codex` log's rows, the registry's keying, the autosync and the private key's
    disposition are named.
  - H5 and H6: step A ships the gate states and the refusal function, so D depends on nothing in H6 that is
    not there; a gate whose files changed since its request is `UNCLEARED` whatever can be verified; step A
    takes every structural ledger check of 6.2 and H6 takes signatures, the HALT scan and verification; the
    false claim about CI coverage is removed (P10); fixtures live in temporary git repositories; the Unicode
    database version is recorded; the schema is tested without a new dependency.
  - Metaplan: H1 before the waves; H3 on its own track; the paths H5 and H6 share; step E named; decisions P8
    to P11 added; branch prefixes; the wave table's gating.
- **Not adopted:** none of the blocking findings. Advisory A12 (H2's autosync wording) is made a decision (P11)
  rather than settled by the session.

## 7. Stop conditions

- A `@security` HALT on a step stops that target plan; the others continue if they do not depend on it.
- A failed check on `main` after a merge: a revert pull request first (PS-2).
- H3 stops, with nothing retired, if the rehearsal shows any row or file that is still needed and verifies only
  with `op-2026`.
- H5 or H6 stop and propose a contract change where the contract's text is silent; they do not invent behaviour.

Steps: `post-1.3.0-high-items.metaplan.steps.csv`.
