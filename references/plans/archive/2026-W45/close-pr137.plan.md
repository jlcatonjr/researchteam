# Close researchteam PR #137 (superseded rc.14 pin)

Date: 2026-11-05. Operator: Jim (asked 2026-11-05).

## Goal

Close #137 ("chore: pin agentteams v1.1.0-rc.14 (d88c53e) + autosync"), without merging it. Superseded by:
- #139, which pinned rc.15 and was merged 8edaae50;
- #143, which pinned rc.16 and was merged f4be2d99.

## Checks before closing (fail-closed)

- #137 is OPEN and unmerged, and its head branch is `chore/agentteams-1.1.0-rc.14`.
- main pins agentteams v1.1.0-rc.16 (a036d09f), which shows the change #137 proposed is obsolete.
- #137 carries no commit that main lacks and still needs. Specifically, check that its decisions-log rows and
  CHANGELOG text are not unique work. A rc.14 pin row would be the only candidate, and it is moot.

## Action

`gh pr close 137 --repo jlcatonjr/researchteam --comment "Superseded by #139 (agentteams v1.1.0-rc.15) and #143
(v1.1.0-rc.16), both merged; main now pins v1.1.0-rc.16."`

The head branch is **not** deleted, so the close is fully reversible with `gh pr reopen 137`. Deleting branches is
a separate, destructive cleanup and is not part of this plan.

## Audit revisions (@adversarial, 2026-11-05): OK

- #139's merge commit is 8edaae50b102984566c9a976bd75d0f04b7ee70d (confirmed).
- #137's only change main needed was a60fd11 (validate allowlist + test), and main has it (validate line 36,
  test line 105).
- The autosync uses its own branch `chore/agentteams-autosync`, so it cannot push to #137's branch or reopen it.
- The close comment cannot be removed, but the close itself can be undone.
