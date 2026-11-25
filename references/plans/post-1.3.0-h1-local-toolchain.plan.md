# H1: bring the local toolchain to the pinned commits (2026-11-25)

Metaplan: `post-1.3.0-high-items.metaplan.md`.

**Problem.** The session-start check reports the main checkout's `.venv` behind `toolchain.lock`: researchteam
and agentteams are installed at the commits of the previous lock. Local `validate`, `doctor` and hook runs
therefore use old code.

**Change.** Run `bash scripts/bootstrap_toolchain.sh` in the main checkout. It installs the commits in
`toolchain.lock` over the existing ignored `.venv`, in place, with agentteams' `signing` extra under the vetted
constraints. The script keeps no backup, so the session first records `pip freeze` of the old `.venv` and copies
the folder aside (inside the ignored `tmp/`), and removes the copy once the checks pass. Nothing tracked changes.

**Alone.** No other local step runs while the bootstrap does (metaplan, wave 0). If the sandbox blocks the
network, the step is handed to the operator as a script with one command (PS-3).

**Checks.** `python3 scripts/check_toolchain.py` reports the installed pair equal to the lock;
`researchteam doctor` reports no failure; the signed toolchain group verifies in that environment.

**Limits.** The lock on `main` pins researchteam at an earlier `main` commit than the `v1.3.0` tag (the autosync
moves it in its own pull request). H1 installs what the lock says and does not move the lock. If the bootstrap
fails part-way, the copy is moved back, the failure is recorded here, and wave 1 proceeds with the old
environment, saying so wherever it runs a local check.

Steps: `post-1.3.0-h1-local-toolchain.steps.csv`.
