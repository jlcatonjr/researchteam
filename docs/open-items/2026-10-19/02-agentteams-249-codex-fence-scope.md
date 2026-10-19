# OI-2026-10-19-02: Codex write-policy fence in the shared AGENTS.md is unscoped, so Grok reads it

| | |
|---|---|
| **Status** | Open: filed upstream, no owner yet |
| **Owner** | [AT] agentteams |
| **Tracking** | [jlcatonjr/agentteams#249](https://github.com/jlcatonjr/agentteams/issues/249) (labels `bug`, `needs-backport-1.0`; no comments) |
| **Affects** | Every derived repo that renders both Codex (with `write_policy: orchestrator-only`) and Grok. Confirmed in Batallion. |
| **Recorded** | 2026-10-19, researchteam-51 closeout |

## Summary
The Codex render writes an `AGENTTEAMS:BEGIN codex_write_policy` fence into the root `AGENTS.md`, which Goose
owns:
- Source: `agentteams/frameworks/codex.py:854-856`, through `_agents_md_ownership.codex_write_policy_decision`,
  on agentteams `main` `7ff49145`.

The fence's heading and text don't name a framework: "## Write Policy: You Are the Orchestrator … the only
agent that writes … run `agentteams --issue-dispatch` before every dispatch".

Grok Build loads the same `AGENTS.md`. In Batallion (lines 294–312 at `b5ef157`), the `grok_runtime` fence comes
straight after it. Orchestrator-only covers only Codex (`write_policy_frameworks: ["codex"]`), so a Grok session
is given a write policy that doesn't apply to it. It may refuse writes, or issue dispatches that no runner serves.

## History
- Found during Batallion's v1.0.0 sync (batallion-1f).
  - batallion-1f first attributed the fence to the Goose render.
  - researchteam-51 traced it to the Codex render.
- Sent to agentteams-6d twice (no reply; that session was waiting on operator input), then filed as #249.

## Suggested fix (in the issue)
- Scope the fence to Codex. For example, use the heading "## Codex Write Policy" and open with "applies to Codex
  sessions only; Grok and Goose ignore it".
- Add a test: after a goose → codex → grok render, the `codex_write_policy` fence is still explicitly scoped to
  Codex.
- Fix on `main` first, then backport for agentteams 1.0.x.

## Next actions
1. An agentteams session takes #249 and fixes it on `main`.
2. Backport it in the agentteams 1.0.x patch. researchteam #98 and #102 ship alongside that patch
   (OI-2026-10-19-06).
3. Derived repos pick it up through their next pin move and `researchteam update`.

## Done when
#249 is closed by a merged fix, and a Batallion re-render shows the fence explicitly scoped to Codex.
