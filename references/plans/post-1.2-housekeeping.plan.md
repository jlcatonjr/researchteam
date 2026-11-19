# Plan: housekeeping after the v1.2.0 release (2026-11-19)

Operator instruction (typed in the session, 2026-11-19): proceed with the items left open after the v1.2.0
close-out; decisions go through the picker; anything run outside the sandbox comes as a script with one command.

- **Issue #213.** `docs/agentteams-update-policy.md` says a first-party member's release needs no decision-log row
  only in a workspace the signed group file lists. Name the second case (decision signing off, exemption from the
  brief's `s10_cooldown_exempt_repos`) and say what the record and the tag check are there. `@security` sets the
  sentence. Docs only; merge needs the operator's live approval.
- **Merged remote branches.** S-4 deletion, done as on 2026-11-16: a script the operator runs, after a `@security`
  `--branch-cleanup` review. Never touched: `main`, `release/**`, `archive/**`, `chore/agentteams-autosync`, the
  head of an open PR, and any branch not merged into `main`.
- **Local leftovers.** Update `.venv` to the lock (`scripts/bootstrap_toolchain.sh`); remove this session's
  worktree for the merged pin branch; delete the session's scratch files (PS-1).
- **Not in this plan.** The term-index core switch (researchteam 1.3.0) waits for agentteams 1.3.0.

Steps: `post-1.2-housekeeping.steps.csv`.
