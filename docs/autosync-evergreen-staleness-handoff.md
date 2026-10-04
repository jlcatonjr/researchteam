# Handoff → researchteam: the evergreen autosync PR goes stale and conflicts

**From:** baseAgent (a derived repo; operator Jim) · **To:** researchteam maintainers, who own the managed
`scripts/agentteams_autosync_gate.sh` and the `agentteams-sync.yml` template · **Date:** 2026-10-04
**Status:** a defect report with evidence. **Action needed:**
- rebuild or flag the evergreen PR when the base drifts;
- diagnose the `file_hashes` entries the CI build drops.

**Source:** baseAgent `references/handoffs/to-agentteams/branch-lifecycle-policy.md` §4. The rest of that handoff,
the branch-lifecycle procedure for the `@git-operations` and `@cleanup` agents, went to agentteams as
`references/branch-lifecycle-policy.handoff.md`.

**Evidence:**
- baseAgent PR #9 (`chore/agentteams-autosync`, commit `200ef03`);
- baseAgent `docs/branch-audit-2026-10-04.md` §10.

---

## Requested change: the evergreen autosync PR goes stale and conflicts

**Background.** `.github/workflows/agentteams-sync.yml` delegates to `scripts/agentteams_autosync_gate.sh`, which
researchteam manages. The gate keys on the agentteams SHA, so timestamp-only regenerations correctly open no PR.

**Observed.** PR #9 (branch `chore/agentteams-autosync`) holds one commit, `200ef03`, from 28 September, built on
`63d038f`:
- the autosync-ref moves from `f3a8b8c` to `3c06a93`;
- a threat-intel refresh in which only the timestamps changed (`security-vulnerability-watch.json` and the fenced
  snapshot in `security.agent.md`);
- a new manifest fingerprint and a new `memory-index.vcache` key.

Since then main has changed `memory-index.vcache` (`528a927`), so the PR now **conflicts**.
- **Why it stays stale:** the SHA-gate compares against the ref recorded on the evergreen branch. While the
  agentteams SHA doesn't move, no run changes anything (the 21 September run failed), so the branch is never
  rebuilt.
- **Its intel also ages.** That matters, because a fresh intel snapshot is what clears the intel-freshness gate on
  `agentteams --adopt-orphans --overwrite`.

**Requested:**
1. **Rebuild or flag on base drift.** When the default branch has moved and the open evergreen PR no longer merges
   cleanly, rebuild the branch on the current base even if the SHA is unchanged, or at least label or comment on
   the PR.
2. **Diagnose the dropped hashes.** The CI-regenerated `build-log.json` on the PR branch **drops** two `file_hashes`
   entries that main's locally built log records: `../../sandbox/confine-run.sh` and `../../.vscode/tasks.json`.
   Merging the PR would silently stop drift-checking the sandbox launcher. Please find the cause; a difference
   between the local and CI emit configurations is plausible. Until then, flag any PR that removes hash entries.
3. **Record:** 3 of the last 5 runs failed (2 Sep dispatch, 7 Sep and 21 Sep scheduled). Check that the failures
   aren't what keeps the branch stale.

## Acceptance

1. **A conflicting PR gets rebuilt or flagged.** An open evergreen PR that no longer merges cleanly into the
   default branch is either rebuilt on the current base or visibly flagged (a label or comment) on the next run,
   even when the agentteams SHA is unchanged.
2. **A PR that removes hash entries is flagged.** A PR whose `build-log.json` removes `file_hashes` entries
   relative to the default branch carries a warning in its body. The cause of the local-vs-CI difference is
   identified.
