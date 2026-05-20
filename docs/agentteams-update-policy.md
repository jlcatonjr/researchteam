# AgentTeams Update Policy

Date: 2026-05-20
Status: Active

## Purpose

Define review and rollback policy for automated AgentTeams synchronization runs using `--update --merge`.

## Execution Policy

1. Scheduled runs are dry-run only.
2. PR creation is allowed only for manual (`workflow_dispatch`) runs with explicit `dry_run=false` and `open_pr=true`.
3. Auto-merge is disabled by default.
4. Workflow defense-in-depth guard must fail CI if `.github/agents/.github/` exists before or after update execution.

## Reviewer Gate

Before merging a sync PR, reviewers must confirm:

1. Changed files are within approved scope (`.github/**`, `brief.json`, validator/policy docs when expected).
2. AGENTTEAMS fence pairing remains valid in all changed markdown/agent files.
3. No new `{MANUAL:*}` placeholders were introduced.
4. No user-authored content outside fenced regions was removed.

## Rollback Protocol

1. If validation fails in CI: do not open PR; inspect artifacts and rerun after fixes.
2. If unsafe PR is opened: close PR and pin prior AgentTeams ref.
3. If a bad sync is merged: revert commit and rerun in dry-run mode with stricter scope checks.

## Legacy Mirror Handling

- `.github/agents/.github/**` is legacy mirror content and not source-of-truth.
- Do not include legacy mirror files in sync scope or review baselines.

## Escalation

Escalate to maintainer review if:
- out-of-scope path changes are detected,
- fence mismatches are detected,
- duplicate-tree drift reappears in active source-of-truth paths.

## Validator Test Matrix (Local)

Use these commands to verify validator behavior locally:

1. Baseline outside git worktree context (expected pass, exit 0)

```bash
bash scripts/validate_agentteams_update.sh
echo $?
```

Expected:
- Message indicating no git worktree and no override.
- Exit code `0`.

2. Allowed changed file simulation (expected pass, exit 0)

```bash
VALIDATION_CHANGED_FILES='docs/agentteams-update-policy.md' bash scripts/validate_agentteams_update.sh
echo $?
```

Expected:
- Validation completes successfully.
- Exit code `0`.

3. Forbidden nested mirror simulation (expected fail, exit 1)

```bash
VALIDATION_CHANGED_FILES='.github/agents/.github/reintroduced.txt' bash scripts/validate_agentteams_update.sh
echo $?
```

Expected:
- Error indicating forbidden nested mirror path.
- Exit code `1`.

4. Agent file with unresolved placeholders (expected fail, exit 1)

```bash
VALIDATION_CHANGED_FILES='.github/agents/conclusion-expert.agent.md' bash scripts/validate_agentteams_update.sh
echo $?
```

Expected:
- Error indicating unresolved `{MANUAL:*}` placeholders in changed active agent file.
- Exit code `1`.
