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
- `survey-manifest` is in A because `survey-status` needs the manifest builder. As section 7 says, it writes the
  gate's manifest file and prints what the operator signs; it signs nothing and writes no ledger row.
- **Two recorded widenings of step A** against the 2026-11-23 plan and the contract's section 10, which name
  the validator, the manifest builder, `survey-validate` and `survey-status` for this step, and put "stage
  refusal" with verification in step 6: the `survey-manifest` command, and the refusal function. Both are
  standard-library code with no signing. The reason is the audit's finding that step D's post-steps must refuse
  on a blocking gate (4.5) whether or not verification has landed.
- The waiver-file error of 6.2 is a structural check, so it is in A.

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

## Step B is split in two (2026-11-25)

The builder stopped after a coherent first part, as this plan allows where a step is too large to review as one
pull request.

- **B part 1 (built, in review):** the evidence row checks with the contract's 18 rule ids and the legacy
  exceptions (4.1), the attribution checks (4.3), bucket tables, the two bucketers and the year and period rule
  (4.8), the form-and-presence check of a fetch-receipt citation (5.4; fetching and re-finding stay in step G), and
  `survey-validate`'s row-file checks. It adds no command and writes no file. Branch `feat/survey-tools-b`.
- **B part 2 (next):** the overrides file, the registry build with names and candidates, proposed override rows,
  the batch merge, writing a first exceptions file, and the commands `survey-rows` and `survey-registry`.
- **A dependency the plan had not seen.** The batch merge renews the registry's provenance record (4.4), and that
  record's shape is defined in 4.6, which this plan gave to step C. Part 2 therefore brings forward the part of
  4.6 it needs: the provenance record itself (the shape, and writing it for the registry). Step C keeps agreement,
  finalising, the rollup, and applying the record to its own outputs. The record is written once, in shared code,
  so step C adds callers and no second definition.
- The metaplan's waves change accordingly: wave 2 is B part 1 and step F; B part 2 follows B part 1's merge and
  runs beside step F if F is still open; step C waits for B part 2.

## Step C: what the contract leaves open, and what the reference tool does (2026-11-25; data)

`@technical-validator` on step C part 1 (pull request #270): the code and adjudication checks match 4.2 as written,
but line 400 plainly requires raw agreement, Cohen's κ and Gwet's AC1, and the text does not define the last two
well enough to compute; and 4.2 does not say where final rows go or what the rollup's output is. The first
integrating project's session described how its reference tool behaves (behaviour only):

- **Agreement.** NA codes and the missing value count as ordinary categories. A unit enters only when it has both
  passes. AC1's number of categories is the number of codes that occur in the outcome's pairs, not the number
  the codebook allows. κ is unweighted, also for ordered levels. With no pairs all three are not-a-number; where
  chance agreement is 1, κ and AC1 are reported as 1.0 by convention. Output is one plain line per outcome with
  three decimals. Its users warn that counting NA and missing as categories with the category count taken from
  the data makes AC1 look much better than κ on sparse outcomes, and that 1.0 for the undefined case is a
  convention.
- **Final codes.** Written to a separate file named on the command line; the file with passes A and B is never
  rewritten. An agreed unit's final row is pass A's row with the coder given as "agreed" and a note that says so,
  and says when the two passes cited different evidence. A disagreement or a missing pass needs an adjudication,
  whose coder, basis, reporter, evidence and note the final row carries. A unit with no pass rows is silently
  absent.
- **Rollup.** Written to a file named on the command line: the person, the study's rollup keys, the author kind
  where the study has attributions, one column per coded outcome that has a rollup rule, and the `__types` column
  where the study asks for it. NA codes and the missing value are skipped before the rule is applied; a cell with
  nothing left gets the missing value. It refuses an input without the finalising step's record.
- **Records.** Both outputs carry a provenance record that lists gate S5 only.
- **A problem from use, for a later contract version.** When a later ruling recodes a pass so that the passes
  agree, the earlier adjudication becomes an error and must be removed for finalising to run, and the final row
  shows "agreed" with no pointer to the ruling.

These go to the operator as decisions; where the operator follows the reference, the tools match it, and where
not, the difference is recorded for the step D comparison.

**Operator's decisions for step C (picker, 2026-11-25).**
- **Agreement: "Standard definitions".** As the reference tool, with two changes: AC1's number of categories is
  every code the codebook allows for the outcome, and an undefined statistic is reported as `undefined`, not 1.0.
  So: NA codes and the missing value are categories; a unit enters only with both passes; κ is unweighted; three
  decimals; one plain line per outcome. Numbers will differ from the reference tool's on some outcomes, and the
  difference is recorded for the step D comparison.
- **Final codes: "Separate file, as the reference".** The output path is an argument, inside the study's folder and
  not a file the study declares; the file with passes A and B is only read. A field for it is proposed for a
  later contract version.
- **Agreed rows: "As the reference".** Pass A's row, the coder given as `agreed`, the note `agreed` or
  `agreed; evidence differed`.
- **A unit with no pass: "Refuse to finalise".** Stricter than the reference: finalising stops and lists every
  unit that has neither pass.
- **Rollup: "As the reference".** The same columns and rules, the output path an argument inside the study's
  folder, and an input without the finalising step's record refused.
- **Gates listed: "S5 only, as the reference".** Neither command refuses on a gate; the records carry S5's state.

**Operator's further decisions for step C part 2 (picker, 2026-11-25).**
- **The `__types` column: "Distinct, in declared order".** Each distinct value once, joined with `;`, in the order
  the study declares that attribute's levels. Which units are behind a cell is the contract's own definition
  (4.7).
- **A codes file that already holds `final` rows: "Accept if they match".** The tools compare each such row with
  the row they derive from the passes and adjudications and refuse only where one differs or is extra; the
  separate final-codes file is still what they write.
- **A final-codes file that differs from the derived one: "Refuse in every status".** A tightening. The contract's
  leniency for a draft study still applies to a record whose inputs changed while the final codes themselves
  still match.
- **What the record's `gates` entry stands for: "Gates entry covers them".** `inputs` lists the files the output
  is computed from. The reads made to check gate S5 (the codebook it covers and the study's sign-off folder) are
  stood for by the record's `gates` entry, not listed in `inputs`. No code changed. A proposal for a later contract
  version, with one consequence to state there: a record's gate state is fixed when the record is written and
  `check_current` does not check it again; each gated stage checks its gate when it runs.

**Step C part 2 merged (2026-11-25).** Pull request #272 (`survey-finalize`, `survey-rollup`) merged as `599dc90`
after the operator's answer "Merge #272 at 77c6572"; the merge's tree equals that head. `@security` PASS at
`e294f35` (one check-table sentence changed after it); `@technical-validator` confirmed every code fix. Finalising
and the rollup read no fetch receipt, so a record's `inputs` are exactly the files opened apart from the gate's
reads. Suite at the head: 2127 passed, 2 skipped. Step C is complete. Step D is being built on
`feat/survey-tools-d` in two parts: the frame, its lists and the frame-change-log check first, with post-steps
refused as not yet available; then running post-steps, after the operator and `@security` decide the design.

**Step D part 1 (pull request #273, 2026-11-25 and 26).** `survey-frame` builds the frame of a passage or work
study, the passage list and the dropped list, checks the frame-change log, and checks post-steps without running
them. The check table is `references/plans/post-1.3.0-h5-step-d-check-table.md` on the feature branch. The
operator's decisions (picker):
- **The dropped list's name: "Replace .csv".** The frame's path with `.csv` replaced by `.dropped.csv`; a frame
  path that does not end in `.csv` is refused.
- **Who writes a frame-change-log entry: "The tool, from arguments".** The author gives the id, the date, the
  reason and whether results were seen; the tool computes the rest from the frame. Without the arguments the tool
  refuses and prints the entry.
- **How the log is recorded: "No record for the log".** The entry and the frame are written in one guarded write.
  The log has no record of its own; the outputs' records list it as it stands after the append.
- **Replacing a changed frame: "Replace when the log names it".** Only `survey-frame`, only its own recorded
  outputs, and only when the log's last entry holds the new frame's hash. Every other command keeps refusing to
  overwrite.
- **Merged person ids: "Read through the registry".** A merged id counts as the surviving person, by the recorded
  merge override. Applied to the rollup too, through one shared function, so the two agree (the session's choice,
  told to the operator).
- **Which cells the frame has: "Cells with a counted passage".**
- The command's arguments and the passage list's record gates stay as built (the session's choice, told to the
  operator).

Reviews: `@security` PASS at `a413cf1`; `@technical-validator` PASS at `1a8caec`, its four small points then
fixed. Suite at the head: 2209 passed, 2 skipped. The comparison with the reference tool was requested from the
first project's session on 2026-11-26 at that head; the merge waits for it.

**Step D part 2, not started: running post-steps.** `@security` would accept it only under conditions, which the
check table records as not yet decided by the operator: a blocking gate the operator has signed and cleared, pinned
to the step file's hash; never in CI, a hook or `survey-validate`, nor under a standing grant, directive or waiver;
a child process with the step's bytes and the frame over standard input; the result parsed and checked again; and
user documentation that says it is not a sandbox.

**Step D part 1 merged (2026-11-26).** The comparison came back at `a413cf1`: the frame and the passage list are
byte-equal with the reference tool in three runs on the invented study. The differences are in the dropped list
(its name, by ruling; no list without the rule, by the contract's text; the `reason` cell, a proposal) and in the
final-codes file's quoting (a proposal). They are set out in the step D check table. Pull request #273 merged as
`40c9902` after the operator's answer "Merge #273 at 89dbb42"; the merge's tree equals that head. Steps A to D of
H5 are merged. What remains of H5: running post-steps (part 2), which waits for the operator's decision, and the
contract proposals gathered in the check tables, for a later contract version.
