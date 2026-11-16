# Plan: delete remote branches already merged into main (2026-11-16)

Operator ruling (2026-11-16, picker): "Script, after @security". S-4 deletion; the operator runs the script.

- Scope: 28 remote branches whose tip is an ancestor of `origin/main`, listed with their commits.
- Never touched: `main`, `release/**`, `archive/**`, `chore/agentteams-autosync` (the live evergreen branch), any
  branch that is the head of an open PR, and any branch not merged into main.
- `10-delete-merged-branches.sh` re-checks each branch at deletion time:
  - it is still at the listed commit (`--force-with-lease`);
  - that commit is still an ancestor of `origin/main`;
  - no open PR has it as head.
  It lists the branches and asks once before deleting. Merged commits stay reachable from `main`, so nothing is
  lost.

1. `@security` `--branch-cleanup` review of the list and the script.
2. The operator runs the script.
3. Read back the remote branches; record the result.
