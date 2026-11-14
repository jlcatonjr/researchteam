# agentteams v1.0.6 release notes: apply the corrected notes (verify-first)

Date: 2026-11-05. Operator: Jim (optional item, asked 2026-11-05).

## Background

The extractor used by the v1.0.6 ship script overran the notes. agentteams-87 fixed it and wrote the corrected
notes to `~/githubrepositories/agentteams/tmp/by-week/2026-W45/release-notes-1.0.6.md`
(3570 bytes, 2026-11-03), with the command
`gh release edit v1.0.6 --repo jlcatonjr/agentteams --notes-file <that file>`.

## Finding (2026-11-05)

The live v1.0.6 release body already matches that file. `diff` shows only one trailing blank line, and the body has
the same three sections: release notes, security, and fixed. So the corrected notes were already applied, either by
Jim or by agentteams-87.

## Plan

1. Re-check: diff the live body against the file again, ignoring trailing whitespace, and confirm v1.0.6 is still a
   full release (not a pre-release).
2. If they match: do nothing; record the item as already done. No edit, because a no-op edit only changes
   `updated_at`.
3. If they differ: do **not** edit from here. The release belongs to agentteams. Ask Jim whether to apply the file
   (a one-line `gh release edit`, reversible by re-editing).

## Audit revisions (@adversarial, 2026-11-05): OK

- Who applied the notes is not recorded; nothing here shows who did it.
- The corrected file is not overrun: 43 lines, three sections, ending at the frozen-render fix.
- If the bodies ever differ, the edit is routed to an agentteams session, not run from here (C-5).
