# Autosync: gate job without a write token, separate job opens the PR (#182)

**Date:** 2026-11-16. **Release:** v1.1.8 (operator ruling 2026-11-16, relayed by the fleet coordinator and
recorded in infrastructureManagement `docs/operator-preferences.md`: "Next release, v1.1.8").

## Problem

In both autosync workflows (`.github/workflows/agentteams-sync.yml` and
`researchteam/scaffold/agentteams-sync-derived.yml`) the gate step runs integrated agentteams and
researchteam code in the job that later opens the pull request with a write token. Since #181 the token is
not in `.git/config`, but integrated code can still shape later steps of that job, for example through
`$GITHUB_ENV`, git hooks or git config.

## Design

1. **Gate job (`autosync`, name kept).** `permissions: contents: read`. It runs the gate as today, then
   packages the result: a binary patch of the staged change against `HEAD` and the PR body, uploaded as one
   artifact. The gate's `changed`, `new_sha` and `sensitive` become job outputs.
2. **Write job (`open_pr`, new).** `contents: write`, `pull-requests: write`. It runs no integrated code: a
   fresh checkout, the artifact download, one check-and-apply step, then create-pull-request. Everything
   from the gate job is treated as data:
   - `new_sha` must be 7 to 40 hex characters and `sensitive` must be `true` or `false`;
   - the artifact must hold exactly the patch and the body, both regular files;
   - the patch is applied with `git apply --index`; afterwards any staged path with a `.git` component, and
     any new symbolic link or submodule entry, fails the job;
   - the PR body is passed by path (`body-path`), so its text never goes through `$GITHUB_OUTPUT`.
3. **Kept as they are:** the `evergreen_pr` lookup job (#172, #179), the F-5 "no PR" failure (now in the
   write job), the trust-root and install steps.
4. **New action pins:** `actions/upload-artifact` v7.0.2 and `actions/download-artifact` v8.0.2, each pinned
   to its commit. Both were released 2026-10-07 (outside the 14-day cooldown) and are the latest stable
   releases. OSV search 2026-11-16: no advisory affects either version (the one advisory for
   download-artifact, GHSA-cxww-7g56-2vh6, was fixed in 4.1.3).

## Adversarial review of the design (before the edit)

Verdict: cleared on conditions. Each finding and what was done:

| # | Finding | Disposition |
|---|---|---|
| 1 | The `sensitive` label was still the gate job's own report | done: `open_pr` classifies the staged paths with the committed gate script (copied before the patch is applied) and repeats the `toolchain.lock` comparison; the gate's answer can only add. No committed script means sensitive |
| 2 | Gate outputs must reach scripts through `env`, and the PR must use the check step's outputs | done; a test asserts no expression appears in the write job's scripts |
| 3 | The symbolic-link check missed a file turned into a link | done: the destination mode of every staged entry is checked |
| 4 | Git config set by integrated code could reshape the patch | done: global and system config ignored, diff options spelled out, and `open_pr` checks that its checkout is the gate's commit. Residual: the gate job's local `.git/config` |
| 5 | A `.gitattributes` filter could make the PR step commit LFS pointers | done: a patch that adds `filter=` is refused |
| 6 | The gate job can write Actions caches and artifacts | recorded in `docs/agentteams-update-policy.md`; `open_pr` restores no cache |
| 7 | A shallow checkout in the write job | done: `fetch-depth: 0` |
| 9 | Size limits could turn a sync red | done: the gate's text is cut at 50,000 bytes; artifact kept 3 days, documented |
| 8, 10, 11 | Not problems, or already covered | none needed |

Found while testing: a `new_sha` with a second line passed a line-based check and could have set a step
output. The check is now a whole-string match, with a test.

## Reviews of the implementation (PR #199, head 8706884)

- **`@security`: CONDITIONAL PASS.**
  - Medium, fixed: git quotes a name that holds a quote, a backslash or a control character, so such a name
    under `scripts/` escaped the label rule. The names now come from the NUL-separated listing; tested.
  - Low, fixed: three checks read `git diff` through a pipe and would pass if git failed. Each listing now
    goes to a file first.
  - Low, recorded: the gate job's text in the PR body can imitate the write job's banner (the real banner
    comes first); a `toolchain.lock` change that only moves a commit is not labelled, as before (in this
    repository PS-2 asks for `@security` on any `toolchain.lock` change by path, whatever the label).
  - Action pins: evidence sufficient; no pin row or operator decision is needed for a GitHub Action pin.
  - Condition for after the merge: run the workflow once by `workflow_dispatch` and confirm the artifact
    handover and the label.
  - The verdict is recorded in the PR comments. A row in the decisions log needs the operator's key.
- **`@code-hygiene`: PASS.** Should-fix, all done: the equality test now compares the whole handover (both
  jobs' added steps, not only the two scripts); the header comments no longer call the workflow a thin
  shell; the `.git` path test says which refusal fires. Notes taken: a symlink target under the test's
  folder; no chained statements.
- **`@conflict-auditor`: no blocking conflict.** Four non-blocking, all done: a stale comment in
  `scripts/validate_agentteams_update.sh`; the summary's open item for #182; "in-job" wording in the gate's
  PR text and the policy; the "no renames" wording in the term-index protocol.

## Not changed

The gate script's logic (one line of its PR text and one comment in `validate_agentteams_update.sh` were reworded), the `on:` block that `workflow-sync` preserves, and what a derived repository must do to
receive the new workflow (`researchteam workflow-sync`).

## Reviews

`@security` PASS naming both workflow paths (PS-2), `@code-hygiene` for the tests, `@adversarial` on the
design, `@conflict-auditor` at close.
