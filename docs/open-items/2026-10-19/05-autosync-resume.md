# OI-2026-10-19-05: Turning the weekly AgentTeams autosync back on, and mathAgents' schedule is still active

| | |
|---|---|
| **Status** | Open: operator decision, plus one inconsistency to fix now |
| **Owner** | [OP] operator (James); per-repo sessions carry it out |
| **Recorded** | 2026-10-19, researchteam-51 closeout |

## Summary
`docs/release-policy.md` keeps each repo's weekly `agentteams-sync` schedule disabled during the joint cut. Under
shared-policy draft 9 (operator ruling 2026-10-18), it stays disabled until researchteam v1.0.1 is tagged and
the consumer pins it. The policy text names v1.0.1. v1.0.2 is a later patch on the same `release/1.0` line, and baseAgent skips v1.0.1, so this record reads the condition as "pinned to v1.0.1 or later". The operator should confirm that reading.
Separately, James ruled that Batallion's autosync is re-enabled **only on his word, once all four repositories
have tagged v1.0.0**.

## State per repo (checked 2026-10-19)
| Repo | researchteam pin (`main`) | Autosync workflow |
|---|---|---|
| researchteam | advisory self-pin `a21e7db` (v1.0.0) | `disabled_manually` |
| Batallion | **v1.0.2** (`10a36758`) | `disabled_manually` |
| baseAgent | v1.0.0 on `main`; v1.0.2 on `release/1.0` (OI-03) | `disabled_manually` |
| mathAgents | **v1.0.0** | **active**. Its last three runs all failed: 2026-10-10 dispatch, 2026-10-12 **schedule**, 2026-10-18 dispatch. |
| agentteams | (n/a) | no autosync. The AI Bad-Habits catalog sync is active, and unrelated. |

**Inconsistency:** mathAgents' weekly schedule is still **active**. It ran on schedule on 2026-10-12, and
failed. mathAgents is still on v1.0.0, so under the policy its schedule should be disabled until it pins v1.0.1
or later. Each failed run costs CI time and may open a PR.

## Next actions
1. **Now (mathAgents):** disable the schedule (`gh workflow disable -R jlcatonjr/mathAgents "ResearchTeam +
   AgentTeams Autosync (SHA-gated evergreen PR)"`), or pin it to v1.0.2 first. Read why the 2026-10-12 and
   2026-10-18 runs failed.
2. **Operator decision:**
   - Batallion is pinned to v1.0.2 and its `AGENTTEAMS_ALLOWED_SIGNERS` is set, so it's technically eligible.
     Under the 2026-10-19 ruling it waits for all four repos.
   - Record the go-ahead, then run `gh workflow enable` on each repo.
3. Before re-enabling any repo, run one `workflow_dispatch` with `force=true`, and check the gate passes against
   the release-locked tag.

## Done when
Every repo's autosync state matches the policy and the operator's ruling. mathAgents' schedule is not running
against a v1.0.0 pin.
