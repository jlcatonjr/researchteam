# P4 step 2: 25 isolated full test runs (2026-11-20)

Plan: `open-1119-p4-unreproduced-test-failure.plan.md`. Triage: `open-1119-p4-test-triage.md`. Runner:
`archive/2026-W47/p4/run.sh` and `series.sh`.

## Result
**25 runs, 24100 test executions, 0 failures, 0 errors.** The single failure seen once on 2026-11-19 was
**not reproduced under isolation**. That is all these runs show: clean isolated runs cannot test the two most
likely explanations of the original failure (a race with a team regeneration in the same checkout, and the old
local environment of that day), because neither condition exists any more. The item is closed under the plan's
limit (one series, no retry without new evidence).

## How the runs were made
- Code under test: a `git archive` extract of `main` at `fec2e30`, outside the repository, with
  `.git_archival.txt` restored to its checked-in text (an archive substitutes it, which one test checks).
- Each run: `PYTHONPATH=<extract> <python> -m pytest -q -p no:cacheprovider --basetemp=<scratch> --junitxml=...`
  from the extract root, one at a time, with a scratch `HOME`, `PYTHONDONTWRITEBYTECODE=1`, and the session's
  proxy, token and test-affecting variables unset. Each run recorded which `researchteam` and `agentteams` the
  interpreter imports, under the same command and environment. All 25 imported `researchteam` from the extract.
- Two interpreters, because the repository's `.venv` has no pytest and because of the leading explanation
  below. `noat`: Python 3.14 with no agentteams, as in CI. `at`: Python 3.14 in which agentteams is importable
  from a local agentteams checkout (on its `main` that day), as it is for this machine's default `python3`.
- 20 forward runs (10 per interpreter), then 5 with the test files in reverse order (3 and 2).

## Leading explanation of the 2026-11-19 failure (a hypothesis, not a finding)
`tests/test_scaffold_fixes.py::test_signer_appends_verified_row` is skipped when agentteams cannot be imported,
which is always the case in CI. Locally, a bare `python3` resolves to an interpreter where agentteams is
importable from a working checkout, at whatever commit that checkout is on. The test then signs a decision row
and checks the gate's refusal wording against that arbitrary version. On 2026-11-19 that checkout was moving
toward `v1.2.1`. In the `at` runs here the test ran and passed (963 passed, 1 skipped, against 962 and 2).
These runs do not use the agentteams version of that day, so this stays a hypothesis.

## What the triage did find
Two test files failed when run **alone** on `main`: `tests/test_update_native_surfaces.py` (4 of 10) and
`tests/test_materialize_surfaces.py` (13 of 20). `researchteam._frozen` binds `subprocess.run` at import, and
update and materialize import it lazily, after those files' fixtures had faked `subprocess.run`. A full run
hides this, so it cannot be the 2026-11-19 failure. One test also reached the real network. PR #233 fixed both
(merged as `89bda42`).

## Caveat
While the series ran, the session also ran single test files a few times and, once, every test file on its own.
No run in the series failed, so no timing-sensitive result needs to be discounted.

## Runs
| run | tests | failures | errors | skipped | seconds | agentteams importable | researchteam imported from |
|---|---|---|---|---|---|---|---|
| fwd-at-01 | 964 | 0 | 0 | 1 | 138 | yes | the extract |
| fwd-at-02 | 964 | 0 | 0 | 1 | 216 | yes | the extract |
| fwd-at-03 | 964 | 0 | 0 | 1 | 200 | yes | the extract |
| fwd-at-04 | 964 | 0 | 0 | 1 | 187 | yes | the extract |
| fwd-at-05 | 964 | 0 | 0 | 1 | 203 | yes | the extract |
| fwd-at-06 | 964 | 0 | 0 | 1 | 208 | yes | the extract |
| fwd-at-07 | 964 | 0 | 0 | 1 | 138 | yes | the extract |
| fwd-at-08 | 964 | 0 | 0 | 1 | 143 | yes | the extract |
| fwd-at-09 | 964 | 0 | 0 | 1 | 182 | yes | the extract |
| fwd-at-10 | 964 | 0 | 0 | 1 | 158 | yes | the extract |
| fwd-noat-01 | 964 | 0 | 0 | 2 | 220 | no | the extract |
| fwd-noat-02 | 964 | 0 | 0 | 2 | 218 | no | the extract |
| fwd-noat-03 | 964 | 0 | 0 | 2 | 167 | no | the extract |
| fwd-noat-04 | 964 | 0 | 0 | 2 | 146 | no | the extract |
| fwd-noat-05 | 964 | 0 | 0 | 2 | 145 | no | the extract |
| fwd-noat-06 | 964 | 0 | 0 | 2 | 154 | no | the extract |
| fwd-noat-07 | 964 | 0 | 0 | 2 | 148 | no | the extract |
| fwd-noat-08 | 964 | 0 | 0 | 2 | 158 | no | the extract |
| fwd-noat-09 | 964 | 0 | 0 | 2 | 161 | no | the extract |
| fwd-noat-10 | 964 | 0 | 0 | 2 | 140 | no | the extract |
| rev-at-01 | 964 | 0 | 0 | 1 | 146 | yes | the extract |
| rev-at-02 | 964 | 0 | 0 | 1 | 162 | yes | the extract |
| rev-noat-01 | 964 | 0 | 0 | 2 | 169 | no | the extract |
| rev-noat-02 | 964 | 0 | 0 | 2 | 200 | no | the extract |
| rev-noat-03 | 964 | 0 | 0 | 2 | 209 | no | the extract |
