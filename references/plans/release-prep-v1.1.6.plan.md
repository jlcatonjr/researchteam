# Plan: researchteam v1.1.6 on agentteams v1.1.4

Operator ruling (2026-11-16, picker): "v1.1.6 on agentteams v1.1.4". This matches the fleet pair IM reports as R19.
Contents: #181 (#179, autosync token scope) and the agentteams pin move v1.1.3 -> v1.1.4 (autosync PR #180).

1. `@security` reviews autosync PR #180. It changes `toolchain.lock`, the `pyproject.toml` extras pins,
   `.github/agents/` and the other agent surfaces. The PASS must name those paths (PS-2). The PR is merged under
   PS-2 on green CI.
2. Records PR #183 (2026-11-16 summary): `@conflict-auditor`, then merge.
3. Release prep on a branch:
   - CHANGELOG 1.1.6 (from Unreleased, plus the pin move);
   - `docs/release/release-notes-v1.1.6.md`;
   - cut script `08-cut-v1.1.6.sh`, copied from 05 with TAG=v1.1.6 and AT_TAG=v1.1.4, plus a scrubbed tracked copy.
   `@security` and `@conflict-auditor` review it; it is merged under PS-2.
4. The operator runs the cut: fast-forward `release/1.1`, sign and push v1.1.6, create the GitHub release.
5. Verify the tag; send IM-4d the tag object and the peeled SHA; work summary.
