# Open Items — ResearchTeam work review (2026-07-08, REVISED ×2)

Review of everything built across recent sessions (2-fold citation & claim audit; `[LINK]`/`[REFURL]`
source-link standards; agentteams auto-integration; per-project vectorized literature library;
derived-repo updates + private-repo baselines). **Revised after an adversarial audit** (§0), then
**refreshed after resolving P0 + re-updating both derived repos via the on-PATH CLI** (§0.1).

## 0. What the audit corrected (binding)
- **No infra gate is currently RED.** `validate` is **green (exit 0) in all three repos**
  (researchteam, OrthodoxLLM, SSH) — the draft's "P0: gate RED" was a *transient* during-update state
  (dirty `.vscode/tasks.json`), not persistent. Downgraded.
- Misdiagnoses fixed: the `.vscode/` validate gap is latent (and `validate` only diffs *unstaged
  tracked* files, so a one-line regex fix helps little); OrthodoxLLM's `.git` bloat is
  `index/text/*.jsonl` (its own corpus, from the baseline snapshot commit), **not** `.npz`/LFS; SSH bib
  remediation is **project-owner** work, not the maintainer's.
- Ownership tags: **[RT]** researchteam-maintainer · **[PO]** project-owner · **[AT]** upstream-agentteams.

## 0.1 Resolved this session (2026-07-08)
- ✅ **P0 — `researchteam` now on PATH.** Installed **editable** into anaconda from the stable repo
  path (`/opt/anaconda3/bin/researchteam`, version 0.1.0, `MANAGED_FILES` current, points at the
  stable checkout — not a worktree, so it won't go stale). `researchteam doctor` all-green.
- ✅ **Both derived repos re-updated via the bare on-PATH `researchteam update`** (the real workflow).
  Dry-runs showed **0 layer-2 changes** (already fully synced from the prior session); the agentteams
  merges regenerated only timestamps/counters (fences balanced, user content preserved). No
  corruption; capabilities work. Committed atop baselines (`c827381`, `644809e`).
- ⬇️ **Item 3 downgraded:** the **synced** `docs/literature-library-protocol.md` already reaches the
  derived repos and carries the "how agents build it" routing — only the *in-agent-frontmatter* PSN
  pointer doesn't propagate (a convenience, not the routing home).

## 0.2 Code-index integration (F-CODEIDX) — this session
Integrated agentteams' **code & API vector index (retrieval surface #2)** — full audited record in
`docs/code-index-integration-plan.md` (binding R1–R11). Branch `feat/code-index-integration`
(`7ac7743` non-bridge + `eda95d8` claude bridge regen); **not yet merged to main / pushed**.
- ✅ Shipped: `.gitignore` cache block; managed `docs/retrieval-surfaces.md` (4-surface superset that
  supersedes the bridge's 3-surface `domain-boundary.md`); guarded `code-query` bridge command; PSN
  pointers (navigator/reference-manager/literature-review-expert/orchestrator); advisory `doctor`
  `--query-code` probe; `.claude/skills/code-recall.md`. Gates: lit-lib 10/10, citation 38/38, doctor
  green, `--bridge-check` PASS, build+query proven, cache verified gitignored. No revert triggered.
- ⏸️ **Deferred (validated):** full agent-team `--update` regen (orthogonal — code-index isn't in the
  agent templates); goose bridge regen (`/code-recall` is claude-only).
- 🆕 **New open items** (added to the tiers below by tag): P2 `[AT]` upstream asks — agentteams emit the
  `references/code-index/` gitignore into managed projects; a `domain-boundary` hook that points at a
  project's `retrieval-surfaces.md` (the durable end to 3-vs-4); goose `code-query` parity. P2 `[RT]` —
  a `code-query` smoke test + CI wiring (mirrors the pending library-test item). Accepted lags: the
  `memory-index.json` 2-vs-3-surface embedding self-heals on the next weekly `--update`; every local
  `researchteam update` re-refreshes the gitignored cache (no tracked change). Note: `.gitignore` is a
  MANAGED full-overwrite file — derived-local ignore lines must be upstreamed or they're lost.

## Status (DONE — for context)
Shipped to `jlcatonjr/researchteam@main`: citation audit + `[LINK]`/`[REFURL]` + `--layer1-only`
auto-integration + literature library, with bash-3.2 tests, docs, `MANAGED_FILES`. Source links
remediated for ZeldaTimeline + development-of-offices. **OrthodoxLLM** and **SocialScienceHumanities**
each have a **private GitHub repo** (revert baseline pushed) and are **fully updated** (no corruption;
R7 rename verified — OrthodoxLLM's instance-local `check_library_integrity.sh` byte-identical). Revert
of any bad change = one `git reset` to a prior commit on the private repo.

---

## P0 — Truly immediate
*(none — the researchteam-on-PATH blocker is resolved; §0.1. `validate` is green ×3.)*

## P1 — Soon (cheap, real, RT-maintainer)
2. **[RT] Wire the existing library test into CI + add a query smoke test (M2).** `scripts/tests/
   test_literature_library.sh` exists but no workflow runs it; `query_literature_library.py` has **zero
   test coverage** (only build + gate are tested). Add a blocking test step (upstream) + advisory scan,
   mirroring citation/methodology, and a query smoke test (ranking/tokenization parity, empty-result).
3. **[RT/shared] Make the library/citation routing hint reach derived repos.** The PSN pointers live in
   the **layer-1** agent docs (`reference-manager`, `orchestrator`) which do **not** sync to existing
   derived repos — OrthodoxLLM/SSH lack them (verified). The **protocol docs *do* sync** (layer-2), so
   carry the routing hint there (or a layer-2 managed PSN), not per-instance agent frontmatter.
4. **[RT, low-urgency] `.vscode/` validate scope.** `validate_agentteams_update.sh:11` omits `.vscode/`
   (agentteams writes `.vscode/tasks.json`), so the CI-sync window can trip. One-line regex add — but
   `validate` diffs only *unstaged tracked* files, so this is a narrow, latent fix. **[AT co-owner]:**
   the durable fix is agentteams declaring `.vscode/` in its managed scope.

## P2 — Can wait (deferred by design / lower value) — [RT] unless noted
5. **Literature relevance authoring** — records are seeded/thin (`NEEDS-ENRICHMENT`); an agent must
   author real "why relevant" summaries for the vectors to be strong. Ongoing loop, **[PO]** per project.
6. **Doubled citation audit is documented, not enforced** — only the deterministic detector is
   mechanical; Round-1/Round-2 is prose (partly inherent to semantic passes).
7. **Auto-integration isn't durable** — the pre-commit full-merge block is per-clone (`.git/hooks`
   un-versioned); durable homes = the agentteams hook-installer **[AT]** or a CI drift-check.
8. **Derived-repo CI runs almost no mechanical gates (M4)** — `agentteams-sync-derived.yml` runs only a
   citation *advisory* scan (no methodology, no blocking tests, no library). State the posture / expand.
9. **Library STUBs** — out-of-band full-text layer; semantic/dense embedder; cross-project aggregation;
   a first-class `literature-librarian` archetype. All documented-deferred.

## P3 — Housekeeping
10. **[PO] Derived-repo source-link remediation.** SSH `religionAndInstitutions` = **102 `[LINK]`
    gaps** (blocks only if/when that project compiles; CI is advisory); OrthodoxLLM projects too. Owner's
    curation, not the maintainer's queue.
11. **[PO] OrthodoxLLM git heaviness (M3).** 3.3G tree / **427M `.git`** — the heavy tracked blobs are
    `index/text/*.jsonl` (≈259 × 10–12M, its own corpus), embedded by the baseline snapshot commit (871
    files / ~224k insertions). No `.npz` tracked; LFS/history-rewrite is a one-way cleanup if desired.
12. **[RT] Dangling plans** — 4 `references/plans/*egyptian-cosmopolitanism*` files reference a
    non-existent project; and `researchteam/_doctor_cmd.py` doesn't surface the new library/citation
    capabilities. Low-value cleanup.
13. **[PO] SSH's earlier uncommitted bridge edit** was overwritten by a prior managed-file sync (likely
    lost; was never committed). The private-repo baseline now prevents recurrence.
