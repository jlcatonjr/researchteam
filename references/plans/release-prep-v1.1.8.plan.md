# Plan: researchteam v1.1.8 (still pins agentteams v1.1.4)

Operator rulings: #182 ships in v1.1.8 (2026-11-16, relayed by the fleet coordinator and recorded in its
operator-preferences register); "Prepare v1.1.8 from main" and, for the evergreen PR #201, "Review and merge
it" (2026-11-17, picker in this session).

Contents: everything on `main` since v1.1.7.
- #199 and #200 (#182): the autosync gate runs in a job with no write token; a separate job opens the PR.
- #193, #195, #196: the term register and term index, the `doctor` check, the `update` reminder and the
  opt-in validate workflow. This is a new feature in a release numbered as a patch; the CHANGELOG says so.
- #201: the evergreen autosync PR from the #182 verification run (threat-intelligence refresh;
  `toolchain.lock` pins researchteam `262eea1`).
- Records: #194, #197, #198, #202.

1. Release prep on a branch:
   - CHANGELOG 1.1.8 (the Unreleased entries move under it);
   - `docs/release/release-notes-v1.1.8.md`;
   - `12-cut-v1.1.8.sh`, copied from 09 with TAG=v1.1.8 and its texts; AT_TAG=v1.1.4 unchanged; plus a
     scrubbed tracked copy.
2. `@security` and `@conflict-auditor` review it; it is merged under PS-2.
3. The operator runs the cut: fast-forward `release/1.1`, sign and push v1.1.8, create the GitHub release.
4. Verify the tag; send infrastructuremanagement-65 and infrastructuremanagement-4d the tag object and the
   peeled SHA; work summary.
