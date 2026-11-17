# Plan: term-index follow-ups (2026-11-16)

Operator choice (2026-11-16, picker in this session): proceed with all four next steps after #193.

1. **Hooks here.** Merge the term-index hook entries into this repository's `.claude/settings.json`. Done in
   the session at the operator's instruction; the file is gitignored, so nothing tracked changes.
2. **`doctor` check and `update` nudge.** `researchteam doctor` reports on the term index: whether the
   scripts are present, how many projects have a register, what the gate says, whether the hooks are wired
   and whether a workflow runs `validate`. `researchteam update` prints a reminder while a project has a
   register and the hooks are not wired. Both are advisory.
3. **A CI workflow for derived repositories.** A scaffold `researchteam-validate-derived.yml` that runs
   `validate` on pull requests and on pushes to `main`, read-only. Opt-in: written only by
   `researchteam workflow-sync --workflow validate`. `init` does not install it and `update` never
   touches it.
4. **Decision-log handoff.** A decision spec for the #193 review and an operator script that signs the row,
   on its own branch, following the earlier signed rows. The session commits the signed row and merges it.

Steps 2 and 3 go in one PR. It touches the workflow scaffold, so `@security` names
`researchteam/scaffold/researchteam-validate-derived.yml` and the changed modules; `@code-hygiene` reviews
the code; `@conflict-auditor` closes.

Steps: `term-index-followups-2026-11-16.steps.csv`.
