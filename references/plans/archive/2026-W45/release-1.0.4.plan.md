# researchteam 1.0.4 — pin agentteams v1.0.7 on release/1.0, S-10 restored with the local-repo carve-out, pip pin

Date: 2026-11-04. Operator: Jim (approved "proceed" on 2026-11-04).

## Goal

The 1.0 release line catches up with what 1.1 got in rc.4/rc.5, and then researchteam `v1.0.4` is signed for
derived repositories that stay on 1.0 (baseAgent, Batallion):

- pin the signed agentteams `v1.0.7` (tag object `37531c96`, peeled `8b934600`; deps unchanged from `v1.0.0`);
- S-10 restored (14-day cooldown, vulnerability carve-out), with the local-repo exemption
  `s10_cooldown_exempt_repos: ["jlcatonjr/agentteams"]`;
- the bootstrap pins pip (#141).

## Approach

Branch `release-prep/1.0.4` from `origin/release/1.0` (2764f7c). The 1.1-only work stays off it. Bring over from
main only:

- `.github/agents/references/security-decisions.log.csv` (taken whole from main). The log is append-only and
  hash-chained, and main's copy is a superset of release/1.0's. It already carries Jim's signed
  `s10-release-cooldown-restored` and `s10-cooldown-exempt:jlcatonjr/agentteams` rows, so no re-signing is needed.
  The 1.1 rows in it are history and authorize nothing on 1.0.
- `.github/agents/references/exception-registry.json` (the consumed exemption's registry entry, which expires
  2027-02-01);
- the `s10_cooldown_exempt_repos` key in `brief.json`;
- the pip pin in `scripts/bootstrap_toolchain.sh` and `tests/test_toolchain.py`;
- the `agent-surface-matrix.md` allowlist line in validate, but only if 1.0.7 emits that file.

Then:
1. Pin with `check_toolchain.py --write-lock --tag agentteams=v1.0.7 --sync-extras`.
2. Run the autosync gate under a 1.0.7 venv.
3. Write the CHANGELOG and the pin decision spec.
4. Jim signs one row: `pin-agentteams-v1.0.7`.
5. Merge the PR into release/1.0 (not main), then Jim signs tag `v1.0.4` on its merge commit.
6. Notify baseAgent and Batallion.

## Risks

- If 1.0.7 cannot read main's log format, fall back to re-signing the two policy rows on release/1.0 (3
  signatures).
- The PR targets release/1.0; main is not touched.
