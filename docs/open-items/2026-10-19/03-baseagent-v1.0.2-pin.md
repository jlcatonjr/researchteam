# OI-2026-10-19-03: baseAgent's move to researchteam v1.0.2 isn't finished

| | |
|---|---|
| **Status** | Partly done: pinned on `release/1.0`, but not tagged and not on `main` |
| **Owner** | [PO] baseAgent (baseagent-bd owns its `toolchain.lock` pins) |
| **Repo** | jlcatonjr/baseAgent |
| **Recorded** | 2026-10-19, researchteam-51 closeout |
| **Update (2026-10-20)** | `v1.0.1` tagged (tag object `f3aadeb1`); baseAgent `main` pins researchteam v1.0.2 (`10a36758`); autosync active (#173 merged); #167 and #163 still open; the `@security` pin row was not checked |

## Summary
researchteam v1.0.2 (tag object `5e5aeca593d568b2f57b6ce63283961069afa643`, peeled
`10a36758d7fcbb3ccc4c8a8cf1e822c375591f7e`) was announced to baseAgent. The announcement first went to
baseagent-86, which doesn't own pins, then to baseagent-bd, which does. baseAgent folded the pin into its own
1.0.1 release, skipping researchteam v1.0.1, so it moves once rather than twice.

## Where things stand (checked 2026-10-19)
- **Pinned:** baseAgent #166 ("release: baseAgent 1.0.1 (installed-wheel fix, researchteam v1.0.2, codex
  frozen…)") is merged into **`release/1.0`** at `61526bb`. That branch's `toolchain.lock` has
  `researchteam=…@10a36758…` and `researchteam.tag=v1.0.2`.
- **Not tagged:** baseAgent has **no `v1.0.1` tag**. Its newest is `v1.0.0`.
- **`main` still old:** baseAgent's `main` still pins **researchteam v1.0.0** (`a21e7db`). The merge-forward
  hasn't happened.
- **PRs still open:** baseAgent #167 (operator scripts, ASSUME_YES) and #163 (baseagent-73 closeout).
- **Autosync:** baseAgent's weekly autosync is `disabled_manually`.
- **Also in this release:** `frozen_surfaces: ["codex"]` freezes `AGENTS.md`, so Goose's `AGENTS.md` content and
  the bridges stop refreshing. That limitation is documented in baseAgent [1.0.1].

## Next actions (baseAgent)
1. The operator signs and pushes `v1.0.1` at the `release/1.0` merge commit.
2. Merge `release/1.0` forward into `main`, so `main` pins researchteam v1.0.2.
3. Re-run `bash scripts/bootstrap_toolchain.sh`, then check `check_toolchain.py`, and check that the signed rows
   clear the gate in `.venv` (the #100 fix).
4. Then decide on the autosync (OI-2026-10-19-05).

## Done when
baseAgent `v1.0.1` is tagged, and `main`'s lock pins researchteam v1.0.2 with its `@security` pin row.
