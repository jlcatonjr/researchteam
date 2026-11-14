
## Open items and doc refresh (researchteam-9c)

Plan: `tmp/by-week/2026-W44/open-items-and-doc-refresh.plan.md`.

**Operator rulings (Jim):**
- Disable autosync on security and masterTeacher.
- Prepare 1.0.3 now, with #98 and #102 and the agentteams pin left at v1.0.0.
- Remove the orphaned egyptian-cosmopolitanism plans in a PR.

**What happened:**
- **Doc audit rebuilt (#124).** The 2026-10-20 stale-fact audit was moved onto a fresh branch off `main`. A fleet update had snapshotted part of it onto the old branch. It was re-checked against the 1.1 line: 17 more findings were applied (versions, `release/1.1`, the stable versus RC install, Codex native rendering, unfreeze derivation, `init --vulnscan-level`). It adds `docs/open-items-2026-10-27.md`.
- **Plans removed (#125).** Four orphaned plan files, deleted under @security CONDITIONAL clearance: exactly 4 deletions.
- **1.0.3 prepared (#126, into `release/1.0`).** `cherry-pick -x` of #98 and #102, plus the CHANGELOG entry. Tests: 384 passed.
- **Hardening (#127).** Closes F-4 (actions SHA-pinned), F-5 (the gate fails closed on ls-remote), F-9 (fetch retry), F-2 (doctor reports pandoc), P3-12 (doctor reports scholarly capability), P1-2 (library suite and query smoke under pytest) and OI-11 (`conflict-log.csv`). Tests: 514 passed.
- **Operator scripts.** In `researchteam-wt-at11-gov/tmp/by-week/2026-W44/operator/`:
  - 40: disable autosync
  - 41: merge PRs, at their reviewed heads only
  - 42: sign v1.0.3
  - 43: SessionStart toolchain hook

  @security gave a CONDITIONAL PASS, and all 5 findings were fixed. In particular, 41's prompt had been reading the PR list instead of the terminal, and 43 now accepts only the managed hook.
- **@conflict-auditor:** no conflicts between the PRs. The dependency-audit report's status lines were added to #124.

**Follow-ups:**
- After 42: open the `release/1.0` → `main` merge-forward PR.
- F-5's "change but no PR" alert and F-2's compile-preflight probe are still open.
- No Dependabot config exists.
- agentteams `v1.1.0-rc.8` is tagged, so derived repos may move again.
- The old `docs/stale-fact-audit-2026-10-20` branch and the main checkout's fleet churn can be cleaned up with @cleanup clearance. A backup is in the session scratchpad.
