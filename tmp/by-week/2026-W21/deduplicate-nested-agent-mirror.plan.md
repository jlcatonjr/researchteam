# Plan: Deduplicate Nested Agent Mirror

Trigger: User requested to proceed with deduplication of nested mirror tree.
Date: 2026-05-20

Goal:
- Remove active duplication risk from `.github/agents/.github/` while preserving all content via archival move.
- Produce pre/post evidence files for auditability.

Strategy:
1. Inventory current nested mirror files.
2. Archive-copy nested mirror to dated backup path.
3. Remove original nested mirror path after successful archive verification.
4. Record before/after ledgers in tmp/by-week.

Success criteria:
- `.github/agents/.github/` no longer exists as active path.
- Archived copy exists under `.github/agents/.agentteams-backups/`.
- Ledger files document moved content.

Rollback notes:
- Restore archived directory back to `.github/agents/.github/` if required.

Completion: 2026-05-20
