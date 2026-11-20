# T1: pin researchteam to agentteams 1.3.0 (version 2, 2026-11-20, revised after audit)

Target of `release-1.3.0.metaplan.md`. Covers F1 and F12. Model: `references/plans/release-line-1.2.plan.md`.

## Entry conditions for part B (all required)
- agentteams `v1.3.0` is signed, and `check_toolchain.py --verify-tag agentteams v1.3.0` passes.
- The operator has confirmed the line move in this session (D1).
- T5 has merged or been dropped. PR #234 and any PS-2 path-list PR merge whenever they are ready; whichever
  of them and T1 merges later rebases and repeats its `@security` review.

## Part A: soak on the upstream candidate (starts at agentteams `v1.3.0-rc.1`)
A draft branch pinned to the candidate, carrying the T2 rehearsal, under the conditions of the metaplan's
section 4 step 1: a recorded `@security` clearance naming the tag first; never marked ready, never merged; no
change to the lock on `main`; no autosync and no workflow with write credentials; a branch name no sync reads;
renders only in its own worktree; no provisional manifest on `main`; the branch goes to `archive/` after the
final.

`@git-operations` runs the checks and renders in that worktree; `@technical-validator` reads the output. The
frozen-fences state file is cleared only if the candidate lacks upstream's fix, and only after the operator's
confirmation in the picker (S-4) and a recorded `@security` clearance. The report is written to a tracked
record (`docs/release/`) and sent to the coordinator. Every upstream behaviour change that breaks a researchteam
command becomes a fix PR on `main` (F12), with tests, before the pin.

## Part B: the pin PR
1. Re-check what changed upstream between the soaked candidate and the final; repeat the affected checks.
2. The operator signs the decision row `release-line-agentteams-1.3` with a handoff script (`@security`
   reviews the script before and after it is filled).
3. Install agentteams at the verified tag in the working environment (`--write-lock` records the installed
   commit). Drop `agentteams.tag=`, then `check_toolchain.py --write-lock --tag agentteams=v1.3.0 --sync-extras`.
   `.github/agentteams-autosync-ref` moves with the lock.
4. S-10: vulnerability search on agentteams at the tag; the first-party group lifts only the cooldown.
5. Regenerate the team; `scripts/validate_agentteams_update.sh`; `agentteams --sync-project-rules`; check that
   PS-1 to PS-3 survive in every projected copy; `agentteams --verify-toolchain-pin`; every rendered Claude
   agent declares `tools:`. If the frozen-fences file must be cleared here, the same confirmation and
   clearance as in part A apply. If T5 was dropped: check `brief.json` `s10_cooldown_exempt_repos` at this
   render.
6. Search the regenerated team, the memory indexes included, for a home path, a username or any personal
   detail (S-8) before asking for review.
7. `@security` PASS naming `toolchain.lock`, `pyproject.toml`, `.github/agentteams-autosync-ref`,
   `.github/agents/`, the regenerated `.claude/` tree, `CLAUDE.md` and `.claude/CLAUDE.md`,
   `references/security-decisions.log.csv`, and `.github/workflows/` if the regeneration touches it; a final
   PASS at the head that carries the signed row. `@code-hygiene` on any code change.
8. The orchestrator asks the operator, naming the PR and head; `@git-operations` merges with
   `--match-head-commit` and checks the merge and `main`.

## Risks
- A rendered agent or index leaks a local path (the cause of the HALT on PR #214): step 6.
- The overwrite render now refuses on routing loss: found in part A, fixed before part B.
- The final differs from the soaked candidate: step 1.

## Done when
`main` is pinned to agentteams `v1.3.0`, tests are green, and the tag and pin checks pass.
