# H1: bring the local toolchain to the pinned commits (2026-11-25)

Metaplan: `post-1.3.0-high-items.metaplan.md`.

**Problem.** The session-start check reports the main checkout's `.venv` behind `toolchain.lock`: researchteam
and agentteams are installed at the commits of the previous lock. Local `validate`, `doctor` and hook runs
therefore use old code.

**Change.** Run `bash scripts/bootstrap_toolchain.sh` in the main checkout. It rebuilds the ignored `.venv`
from the commits in `toolchain.lock`, with agentteams' `signing` extra under the vetted constraints. Nothing
tracked changes.

**Checks.** `python3 scripts/check_toolchain.py` reports the installed pair equal to the lock;
`researchteam doctor` reports no failure; the signed toolchain group verifies in that environment.

**Limits.** The lock on `main` pins researchteam at an earlier `main` commit than the `v1.3.0` tag (the autosync
moves it in its own pull request). H1 installs what the lock says and does not move the lock. If the bootstrap
cannot reach the network or a constraint fails, the old `.venv` is restored from the bootstrap's own backup if it
made one, and the failure is reported; nothing else depends on H1 hard enough to wait for it.

Steps: `post-1.3.0-h1-local-toolchain.steps.csv`.
