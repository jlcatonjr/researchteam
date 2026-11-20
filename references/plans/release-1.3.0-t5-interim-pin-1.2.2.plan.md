# T5: interim pin to agentteams v1.2.2 (version 2, 2026-11-20, revised after audit)

Target of `release-1.3.0.metaplan.md`. Covers F13. Runs only if the operator says so (D2).

**Why now and not folded into T1:** agentteams' 1.2.2 notes label one change as security, and the date of
agentteams 1.3.0 is not set. **Why it might be folded instead:** it repeats the pin routine once more, and T1
replaces it. The operator chooses.

1. `check_toolchain.py --verify-tag agentteams v1.2.2`. Install agentteams at that tag in the working
   environment (`--write-lock` records the installed commit), then `--write-lock --tag agentteams=v1.2.2
   --sync-extras`; move `.github/agentteams-autosync-ref`. Same line (1.2), so no line-move row is needed.
2. S-10 vulnerability search at the tag. Read the 1.2.2 notes for behaviour changes.
3. Regenerate the team; validate; re-project the Project-Specific Rules; `agentteams --verify-toolchain-pin`;
   check `brief.json` `s10_cooldown_exempt_repos` at this render (an open obligation); S-8 search.
4. `@security` PASS naming `toolchain.lock`, `pyproject.toml`, `.github/agentteams-autosync-ref`,
   `.github/agents/`, the regenerated `.claude/` tree, `CLAUDE.md` and `.claude/CLAUDE.md`, and
   `.github/workflows/` if the regeneration touches it.
5. The orchestrator asks the operator, naming the PR and head; `@git-operations` merges and verifies.
6. Only if the operator also chose a researchteam 1.2.2 at D2:
   - a `git cherry-pick -x` PR brings the pin commit onto `release/1.2`, or `release/1.2` is fast-forwarded if
     `main` holds nothing else since `v1.2.1` that the allowlist refuses; either way after the operator's live
     answer naming the commit;
   - a release-prep PR and a cut script on the 1.2.1 model, with `v1.2.1` pinned as the ancestor;
   - after the tag, check that `main` contains the tagged commit, or merge `release/1.2` forward by PR;
   - T6 then pins `v1.2.2` as the previous release.
   Otherwise `release/1.2` stays at `v1.2.1`.

Done when `main` is pinned to agentteams `v1.2.2` and the tag and pin checks pass.
