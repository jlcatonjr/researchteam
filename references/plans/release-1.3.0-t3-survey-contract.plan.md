# T3: survey toolkit contract in 1.3.0 (version 2, 2026-11-20, revised after audit)

Target of `release-1.3.0.metaplan.md`. Covers F6, F7 and F8. The researchteam session that holds
`survey-toolkit-2026-11-19` writes the contract text; the lead edits plan files and integrates. Documentation
and the explorer template only: the operator ruled that no survey tool is written before the first project has
run a stage.

1. **Record (the lead).** Bring `survey-toolkit-2026-11-19.steps.csv` in line with what merged: its step 13
   reads pending, and PR #226 merged as `4435e14`. Goes with the lead's next records PR.
2. **Explorer contract 1.1 (F8, only-if-ready, after D2).** `templates/bibliography-explorer/CONTRACT.md`
   gains `basis`, `reporter` and `note`, with the explorer's tests, component and `FILES.sha256` as section 9
   of `docs/survey-toolkit.md` requires; open point 2 in section 11 is closed. Own PR; `@code-hygiene` and
   `@conflict-auditor`. It does not wait for step 3. **Done on 2026-11-20 (PR #238, `5b59aa5`).** The freeze
   renumbered the contract's open points; open point 1 (step 3 below) keeps its number.
3. **Open point 1 (F7).** After agentteams releases its gates-only team directory: write the per-study log's
   folder layout and the HALT rule into section 6 of `docs/survey-toolkit.md`, citing the released
   documentation, and close open point 1. `@security` reads the text, because it describes a sign-off log.
4. ~~The specification stays labelled v0-unstable in 1.3.0.~~ Superseded on 2026-11-23: the contract was frozen as
   version 1 (PR #251) once the first project had run a stage that writes evidence. 1.3.0 ships the frozen contract.

Done when the contract on `main` has no open point that 1.3.0 could close, and the plan record is true.
