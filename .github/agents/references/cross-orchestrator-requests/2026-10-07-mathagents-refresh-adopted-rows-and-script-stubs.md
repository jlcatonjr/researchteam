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

---

## Status (2026-10-07, researchteam)

Added by researchteam's own session when it took over this note from baseAgent. The handoff body
above is unchanged.

**Item 1: cause reproduced. It is researchteam's own stale agentteams snapshot.** (Corrected later on
2026-10-07. The first version of this section blamed a WIP branch in the shared editable
checkout. That was wrong.) agentteams-a9 reproduced CA-033 with the exact argv:

- shared editable checkout on WIP (`ea36a3c` + `2847cc4`): rows **kept** (11/12/12);
- `researchteam/.venv`'s non-editable local-folder snapshot of agentteams at `5090eb0`: rows **dropped**
  (0/0/0). `5090eb0` predates agentteams #106 (`d602269`), the change that renders adopted routing
  rows.

Fix applied 2026-10-07, with the operator's go-ahead: `researchteam/.venv`'s agentteams was reinstalled
as a VCS pin of agentteams `main` at `729a0ad`. That commit includes #106, #125 and the #128
overwrite-keeps-adopted-rows guard. Its `direct_url.json` now records `vcs_info.commit_id`
`729a0add38f1…`, so the version a render used can be recovered. `pip check` and
`researchteam doctor` pass.

**This is still open.** `researchteam materialize` runs `agentteams --update --overwrite`
(`researchteam/_update_cmd.py:493`) on whichever `agentteams` `shutil.which` resolves first
(`_preflight_agentteams`, `:304`), not necessarily the one in `researchteam/.venv`. In the operator's
shell, `agentteams/.venv-ci/bin` comes first on PATH. That install is a VCS pin at `c7c846f`, which
is also older than #106. `researchteam doctor` run from `researchteam/.venv` resolved to it. So a
render from that shell would still drop the rows. Two ways to close this, neither applied yet:
(a) prefer the `agentteams` that sits beside `sys.executable` over PATH, or (b) a pre-flight that
refuses an `agentteams` older than the required commit, in the spirit of mathAgents PR #24
(`f6205a7`, `scripts/lib/agentteams_provenance.py`). researchteam-4c has proposed a matching
pre-flight, which is waiting on approval. The adopted-row fence restored by hand in mathAgents is
safe only from a render that uses a pinned agentteams which includes #106.

**Item 2 stands and is researchteam's to fix.** `researchteam update` should leave a committed file
alone when its upstream source is missing, and should never write an absolute local path into a
synced file. This is open.

**Related: the render descriptor cannot be recovered.** `_resolve_descriptor`
(`_update_cmd.py:330`) writes the merged `brief.json` + `_build-description.json` descriptor to a
`tempfile.mkstemp` file (`:392`) and deletes it after the run (`:522`). So the descriptor a past
render used cannot be reconstructed. Proposed: record that descriptor, or its SHA-256, together
with the resolved `agentteams` path, version and editable/commit state, in the build log for each
render. This is open.
