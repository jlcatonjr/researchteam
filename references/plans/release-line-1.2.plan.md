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
