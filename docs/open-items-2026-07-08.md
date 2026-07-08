# Open Items — ResearchTeam work review (2026-07-08, REVISED)

Review of everything built across recent sessions (2-fold citation & claim audit; `[LINK]`/`[REFURL]`
source-link standards; agentteams auto-integration; per-project vectorized literature library;
derived-repo updates + private-repo baselines). **Revised after an adversarial audit** (§0).

## 0. What the audit corrected (binding)
- **No infra gate is currently RED.** `validate` is **green (exit 0) in all three repos** now
  (researchteam, OrthodoxLLM, SSH) — the draft's "P0: gate RED" was a *transient* during-update state
  (dirty `.vscode/tasks.json`), not persistent. Downgraded.
- **The one genuinely-immediate item was missing:** the `researchteam` CLI is **not on PATH**
  (installed only in the repo `.venv`, editable) — now **P0 (M1)**.
- Misdiagnoses fixed: the `.vscode/` validate gap is latent (and `validate` only diffs *unstaged
  tracked* files, so a one-line regex fix helps little); OrthodoxLLM's `.git` bloat is
  `index/text/*.jsonl` (its own corpus, from the baseline snapshot commit), **not** `.npz`/LFS; SSH bib
  remediation is **project-owner** work, not the maintainer's. Added M2–M4.
- Ownership tags: **[RT]** researchteam-maintainer · **[PO]** project-owner · **[AT]** upstream-agentteams.

## Status (DONE — for context)
Shipped to `jlcatonjr/researchteam@main`: citation audit + `[LINK]`/`[REFURL]` + `--layer1-only`
auto-integration + literature library, with bash-3.2 tests, docs, `MANAGED_FILES`. Source links
remediated for ZeldaTimeline + development-of-offices. **OrthodoxLLM** and **SocialScienceHumanities**
each have a **private GitHub repo** (revert baseline pushed) and are **updated** (no corruption; R7
rename verified — OrthodoxLLM's instance-local `check_library_integrity.sh` byte-identical). Both
update-results committed atop their baselines → revert = one `git reset`.

---

## P0 — Truly immediate
1. **[RT/env] `researchteam` is not on PATH.** `command -v researchteam` → not found; it lives only in
   `researchteam/.venv/bin` (editable) — absent from anaconda and the bare shell. The documented
   `researchteam update` workflow (CLAUDE.md Quick Start) can't run in a normal shell; a future update
   would silently fail to launch. **Fix:** `pip install -e /path/to/researchteam` into an environment
   on PATH (as `agentteams` already is), or document venv activation. *(Everything this session ran via
   the explicit `.venv/bin/researchteam` path, so work was unblocked — but the user-facing workflow is.)*

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
