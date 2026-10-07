<!-- Provenance: mathAgents-friction:docs/handoffs/2026-10-07-to-researchteam-refresh-adopted-rows-and-script-stubs.md (mathAgents branch fix/pipeline-friction, released in v0.2.6).
     Filed 2026-10-07 by the baseAgent orchestrator session for operator Jim; body copied verbatim below. -->

# To researchteam / agentteams: two refresh defects found on fix/pipeline-friction (2026-10-07)

Found while re-deriving mathAgents' surfaces with `scripts/refresh_agent_surfaces.sh` for the
pipeline-friction fixes (F1–F3). Both are worked around by hand on this branch, and neither
workaround lasts: the next refresh repeats both defects. Recorded under `@security`'s overwrite
clearances of 2026-10-07T00:56:07Z and 02:02:59Z (condition g) and conflict CA-033.

## 1. The overwrite render drops every adopted agent's routing row (CA-033)

`researchteam materialize --yes --adopt-orphans --no-codex` re-rendered each orchestrator's
`routing_table_rows` fence without the `*(adopted)*` rows for the bespoke agents. The counts were
Copilot 11, Claude 12, Goose 12 and Codex 11 on main (023a4d9), and 0 after the render (caf5556). The
earlier D39 render (fc68f8c) emitted those rows, so the behaviour is not stable across runs. The
agents stay in the orchestrators' `agents:` front matter and in the Goose `sub_recipes`, but the
prose routing table no longer names them.

Workaround on this branch: the fence was restored byte-for-byte from 023a4d9 in the Copilot, Claude
and Goose orchestrators, and Codex was re-projected after the restore. This is a hand edit of a
generated fence, so the next refresh will drop the rows again.

Wanted, either:
- `refresh_agent_surfaces.sh` saves and restores the adopted rows around step 3, as
  `scripts/lib/preserve_psn.py` already does for the notes and rules; or
- an adopt step that always emits the rows (`agentteams --adopt-orphans --overwrite`), unblocked under
  a signed operator decision.

## 2. `researchteam update` overwrites committed scripts with home-path stubs

Step 1 (`researchteam update --yes`) replaced the committed `scripts/goose-openrouter-route-proxy.py`
and `scripts/goose-run-resilient.py` with stubs of about five lines. The stubs name the absent
upstream file by absolute path under the operator's home directory. This happens because the
installed agentteams does not ship those files. The render check then fails (step 4/5, home paths).
On both runs the two files were restored to HEAD with `git checkout --`, which `@security` accepted.

Wanted: `researchteam update` leaves a committed file alone when its upstream source is missing,
and never writes an absolute local path into a synced file.
