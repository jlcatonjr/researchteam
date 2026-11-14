# P4: the 27 notes about other repositories (revised)

**State.** IM adopted them in its own session. They are commit `60f872e` on infrastructureManagement's `main`,
under `references/plans/from-researchteam/`: 27 notes plus a `README.md`, with review row `eea57a0`. IM's
`@security` required these edits:
- names and the email address became "the operator";
- a quote in row 8 of `2026-W46/fleet-evaluation-followups.steps.csv` was closed;
- `handoffs/fleet-update.proposed.sh` was renamed `.sh.txt`, with content unchanged;
- a provenance README was added.

IM leaves the worktree in place until the operator confirms. This session does not touch the worktree; it was
HALTed (C-2). A relayed message is not the operator's consent.

**Steps**
1. Read IM's committed copies through the GitHub API (read-only, no fetch into IM's `.git`). Compare each with
   researchteam's original, allowing this session's scrub plus IM's listed edits. A note that is missing or
   differs otherwise keeps its original.
2. Add the matching originals to the manifest as one `P4` row: a count plus a digest of the local path and hash
   list. The paths are not published, because they name other repositories.
3. Delete them only after `@security` and `@cleanup` clearance and the **operator's own** S-4 confirmation
   (metaplan Phase 2).

**Outcome (2026-11-14).** All 27 originals match IM's copies at `60f872e`, allowing IM's recorded edits. They are
**kept**, as with P1. The manifest carries one P4 row (count and digest). The path list stays local
(`tmp/by-week/2026-W46/open-p4-originals.local-manifest.txt`), because the file names mention other
repositories.
