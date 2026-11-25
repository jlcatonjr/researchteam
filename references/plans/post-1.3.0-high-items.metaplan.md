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

- H1 first, alone and short: every later local check should run the pinned code.
- H2 touches one document and nothing else depends on it.
- H3 depends on H4 in one respect. The key-rotation plan (2026-11-22) lets `fleet-agent-pilot-2026-11` lapse and
  says a new authorization "is drafted and reviewed before `op-2026` is retired". So before the retirement the
  operator either signs the H4 row or rules that the old key is retired without it.
- H4 waits for the operator's word (picker, 2026-11-25: "Regenerate when I ask"). No session work before that.
- H5 is a chain: A, then B, then C, then D, each its own reviewed pull request.
- H6 needs only H5 step A (the specification loader and the gate list).
- H3, H5 and H6 touch disjoint paths: H3 the decisions logs, key stores and registry; H5 and H6
  `scripts/survey/`, `tests/`, the manifest and the bridge script. H5 B and H6 both add commands to the bridge
  script and entries to the manifest, so whichever merges second merges `main` first and resolves it there.

## 3. Waves

| Wave | In parallel | Ends when |
|---|---|---|
| 1 | H1; H2 (pull request); H3 phase 1 (read-only audit and rehearsal); H5 step A (build, review) | H2 and H5-A pull requests are reviewed and put to the operator |
| 2 | H5 step B; H6 (step F); H3 phase 2 (specs and scripts for the operator) | B and F reviewed and put to the operator |
| 3 | H5 step C; H3 phase 3 (the operator signs; the retirement pull request) | C reviewed; the key retired or its date moved by the operator |
| 4 | H5 step D, ending with the comparison against the reference tool | D reviewed and put to the operator |

H4 joins whichever wave is running when the operator asks for it.

Parallel work runs in separate worktrees, one branch per pull request. Work branches are named `feat/…`,
`docs/…`, `governance/…` or `plans/…`, never `release/…` (finding F1 below).

## 4. Reviews that every target plan uses

- `@adversarial` and `@conflict-auditor` on this metaplan and the target plans before the first step (Rule 9).
- `@code-hygiene` on every code pull request; `@technical-validator` compares each tool with the contract's text.
- `@security` on H3 (all of it), H4, H6, and on any pull request that touches a PS-2 path.
- `@conflict-auditor` closes each multi-file change.
- Both test checks green on the head before a merge is put to the operator.

## 5. Decisions that are the operator's

- **P1.** Each merge (PS-2), one question per pull request, naming its head.
- **P2.** H3: whether `s10-release-cooldown-restored` is re-signed with the new key or left to lapse (section
  "Rows" of the H3 plan gives the session's recommendation and why).
- **P3.** H3: retire `op-2026` before H4 is signed, or after.
- **P4.** H3: whether the key stores on the `release/1.x` branches are touched.
- **P5.** H3: the retirement itself, by running its script; and the date if 2026-12-05 cannot hold.
- **P6.** H4: when.
- **P7.** H5 and H6: the release that carries them (the next minor, as ruled on 2026-11-23, or a split).

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

## 7. Stop conditions

- A `@security` HALT on a step stops that target plan; the others continue if they do not depend on it.
- A failed check on `main` after a merge: a revert pull request first (PS-2).
- H3 stops, with nothing retired, if the rehearsal shows any row or file that is still needed and verifies only
  with `op-2026`.
- H5 or H6 stop and propose a contract change where the contract's text is silent; they do not invent behaviour.

Steps: `post-1.3.0-high-items.metaplan.steps.csv`.
