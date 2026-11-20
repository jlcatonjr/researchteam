# Plan: survey toolkit (2026-11-19)

Request (2026-11-19, from the session that coordinates the position-survey work for the operator): move
the reusable part of a derived repository's survey reference implementation into researchteam, as part of
the scholarly profile.

Operator rulings, given in this session's picker on 2026-11-19:

- **Placement:** researchteam 1.3. The contract first; the tools and agents only after the first project
  using the specification has run a stage.
- **Sign-offs:** recorded in a per-study log, not in the team's security decisions log.

The study specification is v0-unstable until the first project has had gates S0 and S5 signed and has run
one stage (a sequencing call agreed between the sessions, not an operator ruling).

Constraints: no project data in this repository; standard library only; agents are rendered by
agentteams, never hand-written; a change under `.github/workflows/` or `.github/agents/` needs a
`@security` PASS naming the paths; every merge to `main` needs the operator's live approval naming the PR
and head.

This plan covers the contract only. The later work is listed in `docs/survey-toolkit.md`, section 10,
and gets its own plan when it starts.

1. **Draft the contract** at `docs/survey-toolkit.md` from the shapes-only inventory the integrating
   session supplied.
2. **Open a draft PR** so the text is tracked and public.
3. **Send the draft for checking** against the reference implementation; revise until agreed.
4. **Close:** `@conflict-auditor` on the PR; ask the operator for the merge.

Steps: `survey-toolkit-2026-11-19.steps.csv`.
