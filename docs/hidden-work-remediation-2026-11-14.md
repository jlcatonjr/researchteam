# Hidden session work: report and remediation (2026-11-14)

The operator ruled on 2026-11-14 that all session work must be public. No working notes may live
outside the repository, in the system root (`/private/tmp`, the session scratchpad), or in ignored
or local-only storage. This report covers the session that prepared and released researchteam
v1.1.4 (PR #159, tag `v1.1.4`, tag object `e789cd17`, commit `5fd8ec3b`). It records what that
session kept out of public view, why, and what has been done about it.

## Where the rule is written

The operator stated the rule as an agentteams rule. A search of this repository's agent docs, its
`CLAUDE.md` files and the local agentteams checkout found no text that states it outright. The
nearest texts point the other way:

- Constitutional Rule 9 sends plans to `tmp/by-week/`;
- this repository's managed `.gitignore` ignores all of `tmp/`;
- the Claude Code harness tells the agent to keep temporary files in a session scratchpad under
  `/private/tmp`.

The rule is now written down as a Project-Specific Rule in `.claude/CLAUDE.md`, so it binds every
later session here. It should also go into the agentteams template (see "Upstream" below).

## What was hidden, and why

| # | Item | Where it was | Why it was there | Remediation |
|---|------|--------------|------------------|-------------|
| 1 | v1.1.4 plan and step CSV | `tmp/by-week/2026-W46/release-prep-v1.1.4.*` (gitignored) | Rule 9's location, which `.gitignore` hides | Published to `references/plans/release-prep-v1.1.4.plan.md` and `.steps.csv`, where this repository already keeps tracked plans |
| 2 | Signing inputs: the root-row spec, its template and the unsigned group file | `tmp/signing/` (gitignored) | Kept out of the repository until the operator signed them | Published to `docs/release/signing-inputs-2026-11-13/`. The unsigned group file's sha256 is `3b4a6925…8955`, the input the operator signed |
| 3 | S-10 vetting query script (PyPI + OSV) | session scratchpad, `vet/vet.py` | Treated as throwaway, so only its results reached `s10-dependency-vetting-2026-11-13.md` | Published as `docs/release/s10-dependency-vetting-2026-11-13.query.py` |
| 4 | GitHub release notes for v1.1.4 | session scratchpad | Drafted for the operator's approval | Published as `docs/release/release-notes-v1.1.4.md`. The v1.1.4 GitHub release was created from this file on 2026-11-14 |
| 5 | Daily work summary for 2026-11-13 | untracked `workSummaries/daily/2026-11-13.md` | Held back so #159's reviewed head would not move | Committed in this change |
| 6 | Superseded WIP from `fix/autosync-cooldown-safe-installs` | local `git stash` | The operator chose "stash" for work that duplicated #152/#155 | Pushed as branch `archive/fix-autosync-cooldown-safe-installs-wip` (`7a4e7888`), with the same tree as the stash. The stash was then dropped |
| 7 | Cross-session messages with infrastructuremanagement-40 and -4d (rulings relayed, tag verification) | session transcripts only | They are sent and received through the harness | Their substance is now in the plan's "Release (2026-11-14)" section (item 1) and the work summary (item 5): tag object `e789cd17`, commit `5fd8ec3b` and tree `7f4d9f60`, which 4d confirmed independently |
| 8 | PR body and review diffs | session scratchpad | Working copies | Already public: they are PR #159's body and its diff. The scratchpad copies were deleted |
| 9 | A copy of agentteams source files, a no-group-file test repository, and test logs | session scratchpad | Used to check behaviour against the real binary | Can be rebuilt from public sources: the agentteams tag `v1.1.3` and `tests/test_release_lock.py`. Deleted |

The operator's signing install is not a note, and it stays outside the repository. The signer
refuses any install that an agent could edit, so it has to be a root-owned install. This one was
built from the verified agentteams `v1.1.3` tag (tag object `1f1ffe6b`, commit `cbd41a74`) with
that release's constraints file. Its location is left out on purpose: a `@security` review in this
session advised against repeating where the signer lives.

## Hidden work left from earlier sessions (not published by this change)

`tmp/` holds about 229 ignored files from earlier sessions. Among them:

- W46 handoffs, notices and operator scripts;
- the 1.0-cut operator scripts in `tmp/by-week/2026-W42/operator/`, which `docs/release-policy.md`
  cites as "local, not committed";
- root-level plans and drafts for research projects.

Six older `git stash` entries (2026-09-22 to 2026-10-19) also remain. Most of them are
regenerable re-render churn.

These were not published here, for two reasons:

- some may hold private material, so making them public needs the operator's review, file by file;
- cross-repository notes among them belong in infrastructureManagement, not here.

The operator should decide on each one: publish, move, or delete with `@cleanup` clearance.

## A gap found during the review

`docs/release-policy.md` requires a `@security` row for every pin move. Every earlier pin move in
`security-decisions.log.csv` has an operator-signed row, but the move to agentteams v1.1.3 does not.
Its spec, `docs/release/pin-agentteams-v1.1.3.decision-spec.json`, is ready. v1.1.4 was released
without the row. Until the operator signs the spec, this is an open item. No agent signs decision rows.

## Upstream

Rule 9's plan location and the template's `tmp/` ignore conflict with this rule in every derived
repository. A durable fix is upstream: track `tmp/by-week/`, or move plans to a tracked path and
state the rule in the agentteams template. That is a change to another repository, so it goes to
infrastructureManagement for routing.
