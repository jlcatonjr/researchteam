# AgentTeams Update/Merge CI Plan (ResearchTeam)

Date: 2026-05-20
Owner: Orchestrator
Objective: Automatically integrate upstream AgentTeams template updates into this repository's agent infrastructure with controlled, reviewable changes.

## 1. Desired End State

- Agent infrastructure can be refreshed non-interactively using `agentteams --update --merge` (or equivalent `build_team.py --update --merge`).
- CI creates a pull request when upstream template changes produce local diffs.
- AGENTTEAMS fenced regions are updated safely while user-authored sections outside fenced regions are preserved.
- Every automation run emits an auditable artifact set (logs + changed file list + risk summary).

## 2. Current-State Constraints (Observed)

- No `.github/workflows/` exists yet.
- Repository appears to be a copied working tree without Git metadata in this environment (`.git` unavailable), so CI files should be staged now and activated after GitHub registration.
- Active infra includes generated files under `.github/agents/` and fenced regions in `.github/copilot-instructions.md`.
- Historical snapshots exist in `.github/agents/.agentteams-backups/`; these must be excluded from change-scoping and quality summaries.
- A nested `.github/agents/.github/` tree exists and should be reviewed as likely duplicated scaffold output.

## 3. Automation Architecture

### Trigger Model

- Scheduled trigger: weekly (e.g., Monday 06:00 UTC).
- Manual trigger: `workflow_dispatch` with options:
  - `agentteams_ref` (tag/branch/commit)
  - `dry_run` (true/false)
  - `open_pr` (true/false)

### Execution Model

1. Checkout repo.
2. Install AgentTeams CLI/runtime (pin a version or commit SHA).
3. Run update command in non-interactive mode:
   - Preferred: `agentteams --description brief.json --update --merge --yes`
   - Fallback if CLI shape differs: `python build_team.py --description brief.json --update --merge --yes`
4. Run validation checks:
   - Detect unresolved placeholders: `{MANUAL:*}` not expected to remain.
   - Ensure fenced blocks remain syntactically paired (`BEGIN`/`END`).
   - Ensure no writes outside approved paths:
     - `.github/**`
     - `brief.json` (only if expected)
5. Produce artifacts:
   - changed-file list
   - update log
   - lightweight risk report
6. If diff exists and checks pass, open/update PR `chore/agentteams-sync-YYYYMMDD`.

### Guardrails

- Block auto-merge when:
  - critical files outside allowed paths changed
  - unresolved placeholder growth detected
  - fence integrity check fails
- Always require human review for first 4 automation cycles.

## 4. CI/CD Workflow Specification (to create after repo registration)

Suggested file: `.github/workflows/agentteams-sync.yml`

High-level jobs:

1. `update-agentteams`
- run on schedule + manual
- executes update/merge command
- uploads artifacts

2. `validate-diff`
- checks changed paths and placeholder/fence integrity
- fails on violations

3. `open-pr`
- conditional on successful validation + non-empty diff
- creates/updates PR with:
  - summary of changed files
  - pinned AgentTeams source ref
  - checklist for reviewers

## 5. Rollout Plan

Phase 1: Manual reproducibility (1-2 runs)
- Run exact command locally and verify deterministic diffs.
- Finalize approved path allowlist.

Phase 2: CI dry-run only (1-2 weeks)
- Run on schedule with `dry_run=true`.
- Publish artifacts without PR creation.

Phase 3: CI creates PRs
- Enable PR creation for non-empty, validated diffs.
- Keep auto-merge disabled.

Phase 4: Optional controlled auto-merge
- Enable only if:
  - 4+ consecutive clean cycles
  - no out-of-scope file changes
  - reviewers sign off on policy

## 6. Required Repository Files for Activation

1. `.github/workflows/agentteams-sync.yml`
2. `scripts/validate_agentteams_update.sh` (path/fence/placeholder checks)
3. `docs/agentteams-update-policy.md` (human review + rollback policy)

## 7. Rollback Strategy

- Any failed run leaves no merge commit; only a PR draft or failed job artifacts.
- If an unsafe PR is opened, close PR and pin older AgentTeams ref.
- Keep `.agentteams-backups/` snapshots and CI artifacts for comparison.

## 8. Success Metrics

- >=95% of scheduled runs complete with no manual intervention.
- 0 unauthorized path modifications in merged updates.
- Median reviewer time per sync PR < 10 minutes after stabilization.
- 0 fence-integrity regressions over 8 consecutive runs.

## 9. Next-Step Execution Order (User-Directed: 2 -> 1 -> 0)

Index mapping used for this queue:
- `2` = JS/runtime hardening pass for reader support modules
- `1` = deduplicate nested scaffold tree and align authoritative infra paths
- `0` = implement CI workflow + validation scripts for automated AgentTeams sync

### Step 2: JS/Reader Hardening (Execute First)

Scope:
- Guard sidebar initialization when `.sidebar` is absent.
- Make table-loader behavior graceful when table assets are missing.
- Keep existing reader functionality intact.

Target files:
- `Projects/JSModules/sidebar.js`
- `Projects/JSModules/tableLoader.js`
- `Projects/JSModules/tableHTMLLoader.js`

Acceptance criteria:
- No runtime exception if sidebar element is missing.
- Missing table assets produce explicit warnings, not hard failures.
- `get_errors` reports no new diagnostics.

### Step 1: Infra Deduplication (Execute Second)

Scope:
- Review nested scaffold mirror under `.github/agents/.github/`.
- Keep one authoritative location for active agent infrastructure.
- Preserve backups and user-authored merge-safe sections.

Target paths:
- `.github/agents/.github/`
- `.github/agents/`

Acceptance criteria:
- Duplicate active definitions removed or archived to backup path.
- No loss of user-authored content outside AGENTTEAMS fenced regions.
- Post-change grep confirms single active source-of-truth tree.

### Step 0: CI Automation Activation (Execute Third)

Scope:
- Add initial dry-run workflow and validator script.
- Prepare PR-creation mode but keep disabled until GitHub registration and first dry-run validation.

Files to create:
- `.github/workflows/agentteams-sync.yml`
- `scripts/validate_agentteams_update.sh`
- `docs/agentteams-update-policy.md`

Acceptance criteria:
- Workflow passes in dry-run mode.
- Validation script blocks unauthorized path drift and fence mismatches.
- Policy doc defines reviewer gate and rollback protocol.

## 10. Stage Gates Between Ordered Steps

- Gate A (after Step 2): JS hardening merged; no new frontend/runtime errors.
- Gate B (after Step 1): infra tree normalized; duplication risk removed.
- Gate C (after Step 0): CI dry-run artifacts generated; ready for post-registration activation.
