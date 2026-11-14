# Public session record (2026-11-14)

Operator ruling, 2026-11-14: all session work is public; there are no hidden notes in the root. The
operator asked for a report on why the v1.1.4 session broke this, and for the breaches to be fixed.
Under the new rule PS-1, this tracked copy is the record. Rule 9's working copies are in `tmp/by-week/2026-W46/`.

Branch: `docs/public-session-record-2026-11-14`, cut from `origin/main` = `5fd8ec3b` (v1.1.4).

1. List every item the v1.1.4 session kept out of public view: the scratchpad, `tmp/`, the stash,
   untracked files and transcripts.
2. Copy this session's items to tracked paths, and check the signed-input hash.
3. Push the superseded stash to `archive/fix-autosync-cooldown-safe-installs-wip`, check the tree,
   then drop the stash.
4. Write the report: `docs/hidden-work-remediation-2026-11-14.md`.
5. Record the rule as PS-1 in `.claude/CLAUDE.md`, under Project-Specific Rules.
6. Commit the 2026-11-13 work summary.
7. Run validate, `@security` and `@conflict-auditor`, then commit, push and open a PR.
8. Publish the v1.1.4 GitHub release from `docs/release/release-notes-v1.1.4.md` and tell 4d.
9. Delete the scratchpad files that can be rebuilt from public sources.

Out of scope (left for the operator, as listed in the report): earlier sessions' ignored `tmp/` files,
the older stashes, and the upstream template fix.
