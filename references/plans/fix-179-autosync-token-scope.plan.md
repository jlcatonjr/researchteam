# Plan: autosync token scope (#179)

Issue: #179. Advisory from Batallion's @security (Batallion PR #47), relayed by the IM pin coordinator; the operator
said to proceed on the recommendation (2026-11-16).

## Changes (both `.github/workflows/agentteams-sync.yml` and `researchteam/scaffold/agentteams-sync-derived.yml`)

1. Workflow-level `permissions: {}`. Each job states its own.
2. New job `evergreen_pr` with `contents: read` and `pull-requests: read` only (read-only; `contents: read` was added in review so a private derived repo's lookup does not silently fall back). It runs the `gh pr list` lookup and exposes `open`.
3. Job `autosync` keeps `contents: write` / `pull-requests: write`. It `needs: evergreen_pr` and runs unless
   cancelled (`!cancelled()`), so a failed lookup gives an empty output, which the gate treats as unknown and
   falls back to the current branch's ref.
4. `actions/checkout` gets `persist-credentials: false`, so the write token is not stored in `.git/config` while
   the gate runs integrated code. `fetch-depth: 0` already fetches every branch, so the separate evergreen fetch
   step is dropped. create-pull-request authenticates with its own `token` input and does not rely on the
   persisted credentials.
5. Tests: the lookup's job has read-only permissions; the gate reads the job output; no token reaches the gate
   step; checkout does not persist credentials.

PS-2: touches `.github/workflows/`, so the merge needs a @security PASS naming that path.
