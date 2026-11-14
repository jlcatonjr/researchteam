# Open items, 2026-11-14 (session close)

This lists what remains after the v1.1.4 release session and its follow-ups (PRs #159-#166). Everything else from
the session is merged and recorded: see `workSummaries/daily/2026-11-14.md` and `references/plans/`.

Owner codes: [OP] the operator, [RT] researchteam (agent session, under PS-2), [AT] agentteams, [IM]
infrastructureManagement.

| # | Item | Owner | Notes |
|---|---|---|---|
| 1 | **Release v1.1.5** from `main` | [RT] prepares, [OP] signs the tag | `main` carries the build-pin re-vet (#161), the `python -m` fix (#165) and the docs and policy changes since v1.1.4. The tag is operator-signed (SSH release key). The agent prepares the CHANGELOG section, the release PR and the exact tag command. No urgency. |
| 2 | **Frozen `AGENTS.md` restore survives a killed run** | [RT] | The restore runs only while the process is alive (P5 side finding). Proposed fix: snapshot the bytes under `.git/` and restore them at the next `_frozen_begin`. A regression test is sketched in `references/plans/open-p5/repro-result.md`. Low risk on its own: agentteams' own frozen filter must also be missing. |
| 3 | **Merged branch cleanup** | [RT] with [OP] grant | 74 local branches are merged into `main`, and there are 20 remote heads. Remote deletion needs the operator's signed `branch-delete` grant or a recorded `@security` `--branch-cleanup` PASS. Local deletion follows S-4. Housekeeping only. |
| 4 | **Optional: delete the unscrubbed `tmp/` originals** | [OP] confirms | They are listed in `references/plans/archive/originals-manifest-2026-11-14.csv`. They are kept by default; they break no rule. |
| 5 | **Rule 9 plans in a tracked path (R15)** | [AT], routed by [IM] | An agentteams template change. researchteam already follows it (PS-1). |
| 6 | **The infrastructureManagement worktree** at `infrastructureManagement.worktrees/researchteam-hidden-notes-2026-11-14` | [IM], once [OP] confirms | IM adopted the notes (`60f872e`). Removing the worktree is IM's step. researchteam does not touch it, because the HALT on cross-repository writes stands. |
