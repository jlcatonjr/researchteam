# Plan: researchteam v1.1.9 (still pins agentteams v1.1.4)

The fleet's pin coordinator relayed an operator ruling (R27, 2026-11-17): build and review the #205 release
now, and cut the tag only after the fleet's v1.1.8 move is complete, so no repository is retargeted
mid-rollout. The coordinator says when the last v1.1.8 merge is in. This session has not seen the ruling
recorded; the cut and its timing stay with the operator.

Contents: #206 (#205: autosync hardening, clearer `workflow-sync` and `check_toolchain` messages, the
no-cache rule in the update policy) and the evergreen PR #207 from its verification run.

1. Release prep on a branch:
   - CHANGELOG 1.1.9 (the Unreleased entry moves under it);
   - `docs/release/release-notes-v1.1.9.md`;
   - `13-cut-v1.1.9.sh`, copied from 12 with TAG=v1.1.9 and its texts; AT_TAG=v1.1.4 unchanged; plus a
     scrubbed tracked copy.
2. `@security` and `@conflict-auditor` review it; it is merged under PS-2.
3. **Wait** for the coordinator's word that the fleet's v1.1.8 move is complete.
4. The operator runs the cut: fast-forward `release/1.1`, sign and push v1.1.9, create the GitHub release.
5. Verify the tag; send infrastructuremanagement-4d and infrastructuremanagement-65 the tag object and the
   peeled SHA; work summary.
