# H5: survey tools, steps A to D (2026-11-25)

Metaplan: `post-1.3.0-high-items.metaplan.md`. This plan carries out steps A to D of
`survey-tools-2026-11-23.plan.md`, which stays the authority on scope, and whose waiting condition (researchteam
1.3.0 released) was met on 2026-11-25. The specification is `docs/survey-toolkit.md`, version 1. Where this plan
and the contract differ, the contract is right.

## Rules for every step (from the contract and the 2026-11-23 plan)

- Code in `scripts/survey/`, a shared core and one module per tool. Python standard library only (rule 1.7).
- Fail closed: a violation exits non-zero and writes nothing (1.2). Deterministic output, no clock (1.5). Paths
  stay in the repository (1.6). Nothing is inferred (1.3). No tool writes a sign-off (1.4).
- Tests on an invented study under `tests/fixtures/`; no project's data, names or topic (1.8). Every contract
  error and every rule id has a test that triggers it.
- Where the contract's text is silent, the step stops on that point and records a proposed contract change; it
  does not invent behaviour. The proposal goes to the operator, not into the code.
- Supported Python: 3.10 to 3.13, as the two test checks run. Folded text (rule 1.10) depends on the Unicode
  database, which differs between Python versions, so the provenance record carries
  `unicodedata.unidata_version`, a test pins the folding of a fixed sample, and a byte comparison between two
  runs (step D's included) is made on the same Python version and says which.
- Fixtures that need team folders, key stores or logs are built by the tests in temporary git repositories. No
  test reads researchteam's own team folders, so a change to those (H3) cannot break a survey test.
- The JSON Schema is generated from the validator's own rule table and tested without a new dependency: it is
  well-formed, every rule's field appears in it, and the shared valid and invalid specifications give the same
  verdict from the validator. A run against a schema library is local and recorded in the pull request.
- Delivery: the new files are added to the scholarly managed files in `researchteam/_manifest.py` and the
  commands to `scripts/claude_researchteam_bridge.sh`, each in the step that makes the command work. The managed
  block of `CLAUDE.md` and the agents are step H, not here.
- Each step is one pull request with `@code-hygiene`, `@technical-validator` (tool against contract text, section
  by section) and `@conflict-auditor`; `@security` reads step A's path handling (rule 1.6) and anything that
  reads a file a specification names. Both test checks green; the operator's live answer for the merge.

## Steps

| Step | Contract | Delivers | Commands |
|---|---|---|---|
| A | 3, 6.1, the structural part of 6.2, 7 | The specification loader and validator with every section 3 check; the published JSON Schema; the gate list, the manifest builder and the three gate states (6.1); the function that turns a gate's state and `enforce` into "runs" or "refuses"; every check of the ledger folder that needs no signature (6.2); the invented example study and the shared valid and invalid specifications of section 3 as fixtures | `survey-validate`, `survey-status`, `survey-manifest` |
| B | 4.1, 4.3, 4.4, 4.8 | Evidence and attribution row checks with rule ids and legacy exceptions; the batch merge; the identity registry (candidates, overrides, build, the record a merge renews); the table bucketer and the year rule | `survey-rows`, `survey-registry` |
| C | 4.2, 4.6 | Agreement between the two passes; fail-closed finalising; the rollup; the provenance record every output carries | `survey-agreement`, `survey-finalize`, `survey-rollup` |
| D | 4.4, 4.5, 4.7 | The frame of a passage or work study, its dropped list and passage list; the frame-change log and post-steps; refusal in an author study | `survey-frame` |

**Step A before verification exists.** The line between A and F is: A does everything that needs only the
standard library, F does signatures. So in A:
- `survey-status` reports each gate's manifest hash, `enforce`, `mode` and state. The state follows 6.1: a gate
  whose files have changed since a request was made is `UNCLEARED`, whatever can be verified; otherwise, with no
  verification in this version, it is `UNAVAILABLE` ("signatures cannot be verified here"), with that reason.
  Step A never reports `CLEARED`.
- `survey-validate` makes every structural check of the ledger folder that 6.2 lists.
- The refusal function exists and is tested: a blocking gate that is `UNCLEARED` or `UNAVAILABLE` refuses (6.1,
  rule 1.7). No command of steps A to C is a gated stage under 6.1. Step D's post-steps are (4.5), and call it:
  in a study with a blocking S6 they refuse until H6 is merged and agentteams 1.3.0 or later is installed.
- `survey-manifest` is in A because `survey-status` needs the manifest builder and the command only prints what
  it builds. The 2026-11-23 plan and the contract's section 10 name only `survey-validate` and `survey-status`
  for this step; this is a recorded widening of step A by one command, with no signing.

**Step D ends with the comparison, before its merge.** The first project's session is asked to run its reference
tool and researchteam's, at the pull request's head, on the invented study and on the same Python version, and
report differences in the frame's bytes. A difference is settled by the
contract's text; where the text is silent it becomes a proposal. researchteam's session does not read that
project's repository.

## How each step is built

1. Read the contract sections the step names, and section 12 (where the reference differs). List every check,
   rule id, error and output shape as a table in the pull request description: that table is the test list.
2. Fixtures first, then tests that fail, then the code.
3. `@technical-validator` compares the table with the contract; anything in the contract and not in the table is
   a finding.
4. The reviews above; fixes; the full suite; `validate`; the docs-site test (public names in `docs_src/`).

## Parallelism

A is the base and is built alone. After A is merged: B (this plan) and F (H6) run in parallel. C waits for B, D
for C. C writes the gate's state into provenance records (4.6), so it starts from a `main` that has H6, or its
pull request says that states are still unverified. Inside a step, the build is one worktree and one author; the
reviews run in parallel.

## Risks

- **Size.** The contract is over a thousand lines; step A alone covers about three hundred. Each step is cut so
  that a reviewer can hold it; if A's check table exceeds what one pull request can be reviewed for, it is split
  into "loader and validator" and "manifest and commands", and the metaplan's wave table is updated.
- **Two implementations** until the first project moves; guarded by the byte-level comparison at D.
- **A check that is too strict breaks the first project's real study** when it adopts the tools. The first
  project's session is asked to run each merged step on its own study and report; a report is data.
- **The synced bridge script grows.** Each new command follows the existing pattern of the term-index commands
  and refuses clearly when `scripts/survey/` is absent (a repository synced by an older researchteam).

Steps: `post-1.3.0-h5-survey-tools-a-d.steps.csv`.
