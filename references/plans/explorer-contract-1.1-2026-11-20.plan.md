# Plan: bibliography explorer contract 1.1 (2026-11-20)

Request: step 2 of `docs/survey-toolkit.md`, section 10, and its open point 2. The operator told the
session to continue on 2026-11-20; this is the one piece of the survey work that may be done before the
first project has run a stage (operator ruling, 2026-11-19). No survey tool is written here.

What 1.1 adds: three optional columns on the explorer's `evidence.csv` (`basis`, `reporter`, `note`),
carried into the explorer file and shown beside each piece of evidence. The change is additive: an
input written for 1.0 is still valid, and a 1.0 component still opens a 1.1 file.

Constraints: standard library only; the example stays invented; a code change needs a `@code-hygiene`
audit; a multi-file change closes with `@conflict-auditor`; the merge needs the operator's live approval
naming the PR and head.

1. **Contract.** Revise `templates/bibliography-explorer/CONTRACT.md` to version 1.1.
2. **Exporter.** Optional columns, the two new checks, schema version 1.1.
3. **Component.** Show the three fields beside the evidence.
4. **Example and tests.** Extend the invented example; rebuild its data file; add tests; rewrite the
   hash list.
5. **Records.** Mark the point settled in `docs/survey-toolkit.md`; changelog; correct the survey
   plan's last step and the 2026-11-19 summary; write the day's summary.
6. **Close.** `@code-hygiene` and `@conflict-auditor`; open the PR; ask the operator for the merge.

Steps: `explorer-contract-1.1-2026-11-20.steps.csv`.
