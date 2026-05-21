# Agent Infrastructure Authority Map

Date: 2026-05-20
Status: Active policy

## Authoritative Paths

The following paths are authoritative for active agent infrastructure:

- `.github/copilot-instructions.md`
- `.github/agents/*.agent.md`
- `.github/agents/references/**`
- `.github/agents/_build-description.json`

## Non-Authoritative / Legacy Mirror Paths

The paths below are archival/legacy and must not be treated as active infrastructure source-of-truth:

- `.github/agents/.github/**`
- `.github/agents/.agentteams-backups/**`

These trees are retained for forensic comparison and rollback history only.

## Operational Rules

1. Update runs and validation checks must scope to authoritative paths only.
2. Legacy mirror paths must be excluded from quality summaries, drift checks, and PR review baselines.
3. No content in user-authored sections outside AGENTTEAMS fences should be removed by normalization tasks.
4. Before any destructive deduplication, run a backup pass and produce a path-level diff ledger.

## Deduplication Protocol

CI dry-run stability has been confirmed. Controlled destructive deduplication of legacy mirror content may proceed when needed, subject to:
1. Pre-run backup pass.
2. Explicit path-level diff ledger produced before and after.
3. Security clearance per operational rule 1 (authoritative paths only).
