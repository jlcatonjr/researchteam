# OI-2026-10-19-01: Kronos P1 data and competitor packages need S-10 review

| | |
|---|---|
| **Status** | Open, not started |
| **Owner** | [PO] Batallion (Kronos P1, `@security` + `@primary-producer`) |
| **Repo** | jlcatonjr/Batallion (private) |
| **Blocks** | P1 step 5 (data fetch), and so steps 7–14 (grid, effective-cutoff test, results, report) |
| **Recorded** | 2026-10-19, researchteam-51 closeout |

## Summary
P1 (the zero-shot Kronos benchmark on metals futures) needs four packages that the `vendor-kronos-inference-core`
clearance does **not** cover: `yfinance`, `akshare`, `statsforecast`, and the Chronos runtime. Condition (1) of
that clearance says that any package added to `.venv-kronos` after the cleared 28-pin
`requirements-kronos.lock` needs a new Rule S-10 review. Without that review, P1 can't fetch data or run its
baselines.

## Where things stand
- Batallion #21 (`7e92b3d`) vendored the Kronos inference core, with the operator-signed row
  `vendor-kronos-inference-core` (text_digest `sha256:45b4bcf3…`).
- Batallion #22 (`b3a2ceb`) added the CI guard: Kronos loads only through `batallion_safe_load`. This was step 3a.
- P1 steps 1, 2, 3, 3a and 6 are done. Step 4 (harness) is unblocked. **Step 5 is pending.**
  - Step 5 is defined in `tmp/by-week/2026-W43/kronos-p1-zero-shot-benchmark.steps.csv` as: S-10 review of the
    four packages, then fetch CME GC/SI and SHFE au/ag individual contracts, SGE Ag(T+D) and the control gold
    series, then the open-interest roll. Yahoo continuation series are a cross-check only.

## What the review must cover (Rule S-10)
1. **Pins:** an exact version for each package and every transitive dependency, resolved with
   `--exclude-newer` at least 14 days back, and hash-pinned. Use a separate lock, or an amendment to
   `requirements-kronos.lock` with its own signed row.
2. **Vulnerabilities:** an OSV and GHSA search for every pin.
3. **Runtime behaviour:**
   - `yfinance` and `akshare` scrape third-party endpoints.
   - `akshare` has a large transitive tree and reaches Chinese exchange sites.
   - The Chronos runtime pulls model weights, and must follow the same rules as the Kronos loader:
     pinned revision, SHA-256-verified bytes, no `from_pretrained` outside a reviewed loader, and no
     `trust_remote_code`.
4. **Scope:** a decision spec under `docs/release/` and an op-2026 signature. The signing script is derived from
   `tmp/by-week/2026-W43/operator/sign-vendor-kronos-inference-core.sh`. Use a fresh worktree; since Batallion
   #23, worktrees include the agentteams team files.

## Next actions
1. `@security`: write the S-10 dossier for the four packages. Consider dropping `akshare` if SHFE and SGE data
   can come from a smaller client.
2. Write the decision spec, then the operator signs it.
3. `@primary-producer`: write the data-fetch scripts, with provenance in `data/fetch_log.json`.
4. Extend the Kronos loader guard if the Chronos runtime adds another loading path.

## Done when
A signed S-10 row covers every package P1 imports, the lock is hash-pinned, and step 5's data files exist with
fetch provenance.
