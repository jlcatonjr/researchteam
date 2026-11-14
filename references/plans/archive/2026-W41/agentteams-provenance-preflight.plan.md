# agentteams provenance pre-flight + P5a requirement (2026-10-07)

**Why.** mathAgents' v0.2.6 renders (`researchteam materialize --adopt-orphans`) dropped every adopted
routing row (CA-033). agentteams-a9 reproduced it: the agentteams that ran was a frozen local snapshot
(5090eb0) that predates agentteams #106, and nothing recorded which commit it was. The same class of
risk applies to an *editable* agentteams that follows the shared checkout (e.g. `/opt/anaconda3`),
which other sessions switch between branches. Separately, before P5a an `--overwrite` render dropped
user-editable `## Project-Specific Notes/Rules`. P5a (agentteams f113f5d) is now on main.

**Operator decisions (Jim, 2026-10-07).**
1. Add a provenance guard to `_preflight_agentteams`, adapted from mathAgents PR #24
   (`scripts/lib/agentteams_provenance.py`, f6205a7).
2. Repin `researchteam/.venv` agentteams to a VCS install at agentteams origin/main.
3. Require P5a for `materialize`, and forward a new `--discard-user-regions` flag. No duplicate
   region parsing in researchteam.
4. Leave `/opt/anaconda3` alone; the guard refuses it with a clear message.
5. Deliver as branch `fix/agentteams-provenance-preflight` + PR (no merge).

**Changes.**
- `researchteam/_agentteams_provenance.py` (new, stdlib-only, runs under the launcher's interpreter).
- `researchteam/_update_cmd.py`: `_preflight_agentteams` runs the guard; `_run_agentteams` /
  `run_materialize` require P5a on the overwrite path and forward `--discard-user-regions`.
- `researchteam/cli.py`: `materialize --discard-user-regions`.
- Tests in `tests/test_agentteams_provenance.py` and `tests/test_materialize_surfaces.py`.
