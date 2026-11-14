# Open items and doc-audit refresh (2026-10-27)

Request (Jim): carry on with development on open items, and give him .sh scripts for whatever only he can do.

1. Rebuild the 2026-10-20 stale-fact audit on a fresh branch off current main (`docs/stale-fact-audit-1.1`,
   worktree `researchteam-wt-docaudit`). A fleet update had snapshotted part of that work onto the old branch
   and left generated-file churn. The old branch and its working tree stay untouched; a backup is in the
   session scratchpad.
2. Re-audit those docs against the 1.1 state (rc.2, agentteams rc.7, the cooldown deprecation) and fix them.
3. Refresh every open item (OI-2026-10-19-*, the 2026-07-08 leftovers, the dependency-audit F-2/4/5/9).
   Classify each as done, operator, dev or other session.
4. Do the researchteam dev items on branches; open PRs.
5. Write operator scripts (full paths, refuse inside agent sessions, y/N before anything irreversible) for
   the merges and the operator-only actions.
6. Validate, run the @conflict-auditor closeout, write the daily summary.
