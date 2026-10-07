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

**Item 1: the diagnosis above is outdated.** The latest evidence (agentteams-a9, mathagents-04)
suggests the renders that dropped the rows ran the shared editable agentteams checkout while it
was on another session's WIP branch (`fix/write-policy-capability-keys` at `ea36a3c`, with
uncommitted edits). On agentteams `main`, the rows survive with the same argv. This is not
confirmed: if the refresh resolved `agentteams` to a non-editable snapshot of `main`, the cause is
elsewhere. Install facts checked by researchteam-4c on 2026-10-06 against each install's
`direct_url.json`:

- `/opt/anaconda3`: agentteams is **editable**, pointing at `~/githubrepositories/agentteams`. It
  is the only one of the three installs that exposes a render to another session's branch state.
  That day the checkout was on `chore/repin-github-gate-hook` (`3e7e209`), not on `origin/main`,
  and had local edits.
- `researchteam/.venv`: agentteams `1.0.0rc8` is a **non-editable** local snapshot, frozen at
  install time.
- `agentteams/.venv-ci`: a VCS install pinned to `c7c846f`, which is on `origin/main`.

`researchteam materialize` runs `agentteams --update --overwrite` (`researchteam/_update_cmd.py:493`)
on whichever `agentteams` `shutil.which` finds first (`_preflight_agentteams`, `:304`). So whether
a render is exposed depends on PATH order. A guard has landed in mathAgents: PR #24 (`f6205a7`),
`scripts/lib/agentteams_provenance.py`, which refuses an editable agentteams that is off
`origin/main` or dirty. A matching pre-flight in researchteam is proposed but not yet approved. The
adopted-row fence restored by hand in mathAgents is still fragile until the render source is pinned.

**Item 2 stands and is researchteam's to fix.** `researchteam update` should leave a committed file
alone when its upstream source is missing, and should never write an absolute local path into a
synced file. This is open.

**Related: the render descriptor cannot be recovered.** `_resolve_descriptor`
(`_update_cmd.py:330`) writes the merged `brief.json` + `_build-description.json` descriptor to a
`tempfile.mkstemp` file (`:392`) and deletes it after the run (`:522`). So the descriptor a past
render used cannot be reconstructed. Proposed: record that descriptor, or its SHA-256, together
with the resolved `agentteams` path, version and editable/commit state, in the build log for each
render. This is open.
