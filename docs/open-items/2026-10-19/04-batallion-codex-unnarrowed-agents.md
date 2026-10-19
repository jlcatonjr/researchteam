# OI-2026-10-19-04: Batallion has two Codex agent files outside the native render, not restricted under orchestrator-only

| | |
|---|---|
| **Status** | Open, not started |
| **Owner** | [PO] Batallion (orchestrator + `@security`) |
| **Repo** | jlcatonjr/Batallion (private) |
| **Recorded** | 2026-10-19, researchteam-51 closeout |

## Summary
Batallion's Codex team is native and orchestrator-only: decision row `codex-orchestrator-only-native-render`
(op-2026), from Batallion #12. Every `researchteam update` warns:

> Codex: WARNING: .codex/agents holds agent file(s) the native render did not generate: content-enricher.toml,
> team-builder.toml. They are not narrowed under orchestrator-only and fail agentteams' write-policy audit.

Both files declare `sandbox_mode = "read-only"`. But Batallion's own Codex agent headers say `sandbox_mode` "is a
declaration, NOT enforced: Codex ignores a spawned agent's sandbox_mode". So those two agents aren't held to the
orchestrator-only policy the team was cleared under. The files were last touched in `842b56a` (2026-10-19, the
Notion integration).

## Options
1. **Remove them** (`git rm .codex/agents/content-enricher.toml .codex/agents/team-builder.toml`), if Codex
   sessions don't need them. Both are generic Copilot-era agents. `team-builder` builds VS Code Copilot teams.
2. **Restrict them** with `agentteams.write_policy.apply`, so they're read-only proposers like the other 27.
3. **Adopt them** as bespoke Codex agents. Per #12's decisions, adopting bespoke agents into Codex or Grok is a
   v1.0.1 item. Under the frozen-Codex rule (shared policy §5, draft 6, quoted in `docs/release-policy.md`, "Codex (#210)"), adopted agents keep Codex frozen until Codex
   interop arrives in agentteams 1.0.x.

Recommendation: option 1, unless an operator ruling wants them.

## Next actions
1. The operator chooses an option.
2. Make the change in a PR with an `@security` review, since removing agent files is destructive (C-5).
3. Confirm the warning is gone on the next `researchteam update`, and the write-policy audit passes.

## Done when
`researchteam update` no longer warns about extra Codex agent files, and every file in `.codex/agents` is either
generated or restricted.
