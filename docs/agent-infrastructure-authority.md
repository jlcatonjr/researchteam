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

The nested mirror below is legacy and must not be treated as active infrastructure source-of-truth:

- `.github/agents/.github/**`

This mirror exists from prior scaffold generation and is retained temporarily for forensic comparison only.

## Operational Rules

1. Update runs and validation checks must scope to authoritative paths only.
2. Legacy mirror paths must be excluded from quality summaries, drift checks, and PR review baselines.
3. No content in user-authored sections outside AGENTTEAMS fences should be removed by normalization tasks.
4. Before any destructive deduplication, run a backup pass and produce a path-level diff ledger.

## Planned Follow-Up

- After initial CI dry-run stability, perform controlled destructive deduplication with explicit pre/post diffs.
