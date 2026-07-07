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

## Automatic Integration (keep the tree always integrated)

Goal: the committed repository state should always equal what `agentteams --update --merge` would
generate, so the "latest agentteams update" is integrated without a manual step. Three layers:

1. **Pre-commit hook (local, immediate).** When agent infrastructure is staged (`*.agent.md`,
   `brief.json`, `_build-description.json`), the hook regenerates and re-stages the derived
   artifacts before the commit is created:
   - the AgentTeams-managed block refreshes the topology/architecture graphs;
   - the `RESEARCHTEAM:agentteams-integrate` block runs the full union-descriptor merge via
     `researchteam update --layer1-only` and re-stages the result.
   Both are **non-blocking** (skip cleanly if the tools are absent) so a commit never fails on them.
2. **On-demand / manual.** `researchteam update --layer1-only` runs the same union-descriptor merge
   with **no** layer-2 file sync — safe on the upstream repo (a full `researchteam update` there would
   overwrite local managed-file edits with the older upstream versions).
3. **CI backstop (remote, periodic).** The `agentteams-sync` workflow runs the merge on schedule and
   on `workflow_dispatch`, opening a PR when drift exists (see Execution Policy).

**Propagation caveat.** Git hooks are **per-clone** and are not version-controlled, so the hook does
not travel with `git push`/`clone`. Its durable install is `agentteams --install-git-hooks`; the
`RESEARCHTEAM:agentteams-integrate` block should live in that installer (agentteams repo) for
cross-repo propagation. Until then, add the block per clone (it is present in the upstream repo and
in each derived repo updated by a maintainer). The CI backstop (layer 3) is the version-controlled,
always-propagating guarantee.

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

- `.github/agents/.github/**` is forbidden nested mirror content and not source-of-truth.
- `.github/agents/.agentteams-backups/**` is archival backup content and not source-of-truth.
- Do not include either path family in sync scope or review baselines.

## Escalation

Escalate to maintainer review if:
- out-of-scope path changes are detected,
- fence mismatches are detected,
- duplicate-tree drift reappears in active source-of-truth paths.

## Validator Test Matrix (Local)

Use these commands to verify validator behavior locally:

1. Baseline outside git worktree context (expected fail, exit 1)

```bash
bash scripts/validate_agentteams_update.sh
echo $?
```

Expected:
- Error indicating no git worktree and no override.
- Exit code `1`.

2. Allow-skip outside git worktree context (expected pass, exit 0)

```bash
VALIDATION_ALLOW_NO_GIT=1 bash scripts/validate_agentteams_update.sh
echo $?
```

Expected:
- Warning indicating skip is explicitly allowed.
- Exit code `0`.

3. Allowed changed file simulation (expected pass, exit 0)

```bash
VALIDATION_CHANGED_FILES='docs/agentteams-update-policy.md' bash scripts/validate_agentteams_update.sh
echo $?
```

Expected:
- Validation completes successfully.
- Exit code `0`.

4. Forbidden nested mirror simulation (expected fail, exit 1)

```bash
VALIDATION_CHANGED_FILES='.github/agents/.github/reintroduced.txt' bash scripts/validate_agentteams_update.sh
echo $?
```

Expected:
- Error indicating forbidden nested mirror path.
- Exit code `1`.

5. Agent file with unresolved placeholders (expected fail, exit 1)

```bash
VALIDATION_CHANGED_FILES='.github/agents/conclusion-expert.agent.md' bash scripts/validate_agentteams_update.sh
echo $?
```

Expected:
- Error indicating unresolved `{MANUAL:*}` placeholders in changed active agent file.
- Exit code `1`.
