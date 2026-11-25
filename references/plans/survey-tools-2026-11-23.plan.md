# Survey toolkit: the tools (plan, 2026-11-23)

The contract `docs/survey-toolkit.md` is frozen as version 1 (PR #251). This plan covers its section 10,
steps 4 to 8: the tools, the agents and the commands. No tool code exists in researchteam yet.

## Rulings this plan rests on

- Operator, 2026-11-19: the contract first; tools and agents after the first project has run a stage.
- Operator, 2026-11-21: that stage is one that writes evidence rows or codes. Met on 2026-11-23.
- Operator, 2026-11-23 (picker): "After 1.3.0, next minor". researchteam 1.3.0 ships the frozen contract only.
  The tools are planned for the minor release after it and are not added to 1.3.0's scope.

## What is built

The contract is the specification. Where this plan and the contract differ, the contract is right and this plan
is corrected. A behaviour the contract does not fix is not invented here: it becomes a proposal for a new contract
version.

- **Where the code lives.** `scripts/survey/`, one module per tool, with a shared core, in the pattern of the term
  index (`scripts/term_index_engine.py` and its three commands). Python standard library only (contract rule 1.7).
- **How it reaches a derived repository.** As scholarly managed files in `researchteam/_manifest.py`, synced by
  `researchteam update`. The tools never touch a project's `study.json`, rows, codebooks, tables or plug-ins.
- **Commands.** The bridge commands of contract section 7, in `scripts/claude_researchteam_bridge.sh`.
- **Tests.** An invented example study under `tests/fixtures/`, never a project's data (rule 1.8). Each contract
  error and each rule id has a test that triggers it. The shared valid and invalid specifications of section 3 are
  kept as fixtures.
- **The reference implementation** in the first project is the starting point for behaviour, not a file to copy
  unread. Each tool is written against the contract and then compared with the reference on the invented study.
  Section 12 of the contract lists where the reference still differs; researchteam's tools follow the contract.

## Order (each step its own reviewed pull request)

| Step | Contract step | Content | Waits for |
|---|---|---|---|
| A | 4 | The specification validator, the published JSON Schema, the manifest builder, `survey-validate` and `survey-status`, the invented example study. No signing | researchteam 1.3.0 released |
| B | 5 | Evidence and attribution row checks with rule ids and legacy exceptions; the batch merge; the registry (candidates, overrides, build, the record renewed by a merge); the table bucketer and the year rule | A |
| C | 5 | Codes: agreement, fail-closed finalising, rollup; provenance records (4.6) for every output | B |
| D | 5 | The frame of a passage or work study, its dropped list and passage list (4.7); the frame-change log and post-steps (4.4, 4.5) | C |
| E | 5 | The explorer projection (section 9): `evidence.csv`, `codes.csv`, `persons.csv` for explorer contract 1.1 | D |
| F | 6 | Sign-off verification and stage refusal | A. The `agentteams` gates-only log pattern is documented since its 1.3.0 (contract 6.2, settled 2026-11-24) |
| G | 7 | Enumeration log and stopping rule; blind coding packets; quote re-finding and fetch receipts; the query-plan runner | F for the stages that a gate blocks |
| H | 8 | The seven agents (rendered by `agentteams` from the brief, never by hand), the bridge commands in the managed block of `CLAUDE.md`, and the CI gate | G; `@security` review of every grant |

## Reviews and gates for every step

- `@code-hygiene` before merge; `@conflict-auditor` after a multi-file change; `@technical-validator` compares the
  tool's behaviour with the contract's text, section by section.
- `@security` for step F (it verifies signatures and decides refusals), for step G's fetch receipts (network),
  and for step H (agent grants, the managed block of `CLAUDE.md`, the CI workflow).
- A merge to `main` needs the operator's live answer naming the pull request and its head (PS-2).
- The first project's session is asked to run each step's tools on its own study and report differences. A
  difference is settled by the contract's text. If the text is silent, it is proposed as a contract change.

## Not in this plan

- An author study's frame, explorer contract 1.2, a checkable engine-pin field, exclusion rules over cells and
  plug-in bucketers in a frame (contract section 11, open points 2 to 6). Each needs a new contract version first.
- The analysis engine and the results page, which are another repository's.
- Any change to the first project's files or signed gates.

## Risks

- **Two implementations.** Until the first project moves to researchteam's tools there are two. The contract fixes
  the outputs byte for byte where it could (the frame's order and quoting, the manifest), so step D ends with a
  comparison of both tools' frames on the invented study.
- **Step F depends on another repository's release.** Steps A to E do not, and deliver a toolkit that checks and
  builds but does not yet refuse a stage on an uncleared gate. That state is stated in `survey-status` output.
- **Scope creep into the next release.** Steps A to E are the smallest useful set. F to H follow when they are
  ready and are not promised for the same release.
