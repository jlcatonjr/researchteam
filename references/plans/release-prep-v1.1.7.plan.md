# Plan: researchteam v1.1.7 (still pins agentteams v1.1.4)

Operator ruling (2026-11-16, picker): "Prepare 1.1.7 now".
Contents: #188 (#186: derived autosync schedule off by default; `researchteam workflow-sync`) and the #187 docs
note.

1. Release prep on a branch:
   - CHANGELOG 1.1.7 (moved from Unreleased);
   - `docs/release/release-notes-v1.1.7.md`;
   - `09-cut-v1.1.7.sh`, copied from 08 with TAG=v1.1.7 and AT_TAG=v1.1.4 unchanged, plus a scrubbed tracked copy.
2. `@security` and `@conflict-auditor` review it; it is merged under PS-2.
3. The operator runs the cut: fast-forward `release/1.1`, sign and push v1.1.7, create the GitHub release.
4. Verify the tag; send IM-4d the tag object and the peeled SHA; work summary.
