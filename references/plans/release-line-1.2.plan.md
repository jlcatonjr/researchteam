# researchteam 1.2 line: pin agentteams v1.2.1, then v1.2.0-rc.1 and v1.2.0

Written 2026-11-19 by the researchteam agent session.

## Operator rulings (this session's picker, 2026-11-19)
- **Start the 1.2 line now.** researchteam cuts 1.2.0 pinned to agentteams v1.2.1: rc.1, CI, then the final, with no
  fleet soak. The pin PR may be built against the unsigned v1.2.1 commit and is confirmed against the signed tag
  before the operator is asked to approve the merge.
- **The term-index core switch moves to researchteam 1.3.0**, pinned to agentteams 1.3. researchteam 1.2.0 is the
  agentteams 1.2 pin release only. This replaces the 2026-11-17 ruling that 1.2.0 would carry the switch.

## Facts checked (read-only, 2026-11-19)
- agentteams `v1.2.0`: tag object `57cd49208382d4a38981a065ee6f1eb47b3b686d`, peeled `9d6e9080d795ff862265b730f7056abbf698af2f`,
  published as Latest.
- agentteams `release/1.2` head: `a7ab95e241244903339b6d54743f7c3366530071` (v1.2.1 merged, tag not yet signed).
- researchteam `main`: `c62c25c`; `toolchain.lock` pins agentteams v1.1.4 (`b82d78e7`).
- agentteams #511 (unscoped Claude agents fall back to Read/Grep/Glob): every rendered agent under `.claude/agents/`
  declares `tools:`, so no grant is missing. Re-checked after the regeneration (step 3).

## Update, 2026-11-19 (later the same day)
- agentteams `v1.2.1` is signed and published as Latest: tag object `a72a844e7afa468edb69cf1bf99d6f5f74390c1a`, peeled
  `a7ab95e241244903339b6d54743f7c3366530071`. The facts above describe the state when the plan was written.
- The lock, both extras and the autosync ref were written from the verified tag. `main` was merged into the branch
  (it then held #215, `e1243ea`, the commit the lock's advisory `researchteam=` line names).
- The head that carries the operator-signed row needs its own `@security` PASS naming `.github/agents/` before the
  operator is asked to approve the merge.

## Outcome, 2026-11-19
- `v1.2.0-rc.1`: tag object `8987baad79d341c7a02e318fde9ef14243839b92`, peeled `4bc357d4065c52b3586bb7f1d71feed4f98e0eed`.
- `v1.2.0`: tag object `c621290a2f45891a483e088ce33f3becbfc39a79`, peeled `7da258f62831ea300335b023ccbeb1b04cc7df0c`
  (the merge of PR #218). `main` and `release/1.2` are both at that commit; the release is marked Latest.
- All 12 steps are done. The gates below are kept as written; each was met. Record: `workSummaries/daily/2026-11-19.md`.

## Gates
- Nothing merges to `main`, moves `release/**` or is signed without the operator. The pin PR touches `toolchain.lock`,
  the extras and `.github/agents/`, so it needs a `@security` PASS naming those paths (PS-2), and the operator's
  live approval of the merge.
- The line move is a trust change with its own `@security` row, `release-line-agentteams-1.2`, separate from the pin
  review (release policy, by analogy with the 1.1 line). The operator signs the row.
- The lock is written only from the verified signed tag (`check_toolchain.py --write-lock --tag agentteams=v1.2.1
  --sync-extras`), after the `agentteams.tag=` line is dropped. Until the tag exists the PR stays a draft and the
  lock is unchanged.
- The coordinator reviews each signing script before it is filled.

## Steps
See `release-line-1.2.steps.csv`.
