# PLAN (v1, pre-audit) — Integrate agentteams Code & API Vector Index (F-CODEIDX) into researchteam

**Source:** `docs/code-api-vector-index-integration-handoff.md` (agentteams PR #50 → `efe8f12`).
**Discipline:** plan → adversarial+conflict audit → revise (binding R#) → implement → gates green.
**Date:** 2026-07-08. researchteam @ `66eec1c` (clean); agentteams editable @ `efe8f12` (F-CODEIDX live).

---

## A. Verified preconditions (recon complete — these are checked, not assumed)

1. agentteams editable install already exposes `--refresh-code-index / --query-code / --code-kind /
   --code-index-hook` in `--help`. **A1 (refresh the dep) is already satisfied** — no pip action needed.
   `pyproject.toml` pins `agentteams @ git+…/agentteams` (tracks main) as the optional `update` extra;
   base install stays dependency-free; F-CODEIDX is stdlib-only → **no new runtime dep** (A2). Python
   `>=3.10` satisfies `sys.stdlib_module_names`/`ast.unparse` (A3).
2. researchteam has **no** code-index surface today: no `.claude/skills/code-recall.md`, no gitignore
   rule, no references anywhere except the handoff doc.
3. `.gitignore` **and** `docs/*.md` are `MANAGED_FILES` (`_manifest.py`) → edits propagate to derived
   repos on their next `researchteam update` (after the CLI-reinstall sequencing caveat, below).
4. The bridge (`agentteams/bridge.py`) really emits `.claude/skills/code-recall.md` (L222) and a
   code-index-aware `domain-boundary.md` (`_render_domain_boundary`, L723; "code/API → /code-recall"
   L773). The current researchteam `domain-boundary.md` is the **2-surface** version.
5. **Bridge regen is manual** — grep found no `--bridge-from` in `scripts/` or CI. The weekly
   `agentteams-sync.yml` runs only `--update --merge` (L85). So `/code-recall` will NOT appear
   automatically; B1-step-2 (the bridge run) is genuinely required.
6. **Generated agent-doc bodies do NOT gain code-index content.** code-index/code-recall strings live
   only in agentteams' CLI wiring + builder + git-hook + bridge (`cli/artifacts.py`, `parser.py`,
   `git_hooks.py`, `bridge.py`) — **not** in `templates/archetypes/agents`. ⇒ A full agent-team
   `--update` regen (handoff B1-step-1) is **orthogonal** to surfacing the feature.

## B. Scope decision (what's IN vs deferred, with rationale)

**IN (this session):**
- **S2** Prove the feature: `--refresh-code-index` (builds gitignored cache) + `--query-code` returns
  ranked `[local-script]` hits. (Verification, not a committed artifact.)
- **S3 / B2** `.gitignore`: add `references/code-index/` + `**/references/code-index/` block (managed →
  propagates; partially resolves §7-4 for researchteam-managed projects).
- **S4 / B3 + §7-2** New **`docs/retrieval-surfaces.md`** — the canonical **4-surface** doc (memory /
  code / retrieval-integrator / literature library), carrying the anti-fabrication ceiling. Add to
  `MANAGED_FILES`. This is the durable, propagating home for surface #4 — chosen over hand-editing the
  bridge-regenerated `domain-boundary.md` (which would be clobbered on next bridge run).
- **S5 / B1-step-2** Bridge regen (**claude required; goose for parity**), `--bridge-merge` ONLY,
  `--bridge-check` PASS, diff-reviewed. Emits `code-recall.md` + 3-surface `domain-boundary.md`.
- **S6 / A5-equiv** Add a `code-query` command to `scripts/claude_researchteam_bridge.sh` (thin shell to
  `agentteams --query-code`), mirroring `library-query`. Managed → propagates. (Chosen over the
  `researchteam/cli.py` passthrough — the bridge is the established one-interface home; cli.py would be
  redundant.)
- **S7 / B4** PSN pointers in `reference-manager`, `navigator`, `literature-review-expert`,
  `orchestrator`: "prose → /recall · code/API → /code-recall · sources → library-query," pointing at
  `docs/retrieval-surfaces.md`.
- **S8 (small)** `researchteam doctor`: add one **advisory** capability probe — does the resolved
  agentteams expose `--query-code` (feature present)? Non-fatal `warn` if absent.
- **S9** Verification checklist (§6): all items; researchteam suite green; **no library-scripts/tests
  regression**.

**DEFERRED / OUT (with reason):**
- **B1-step-1 full agent-team `--update` regen** — orthogonal (A.6), high diff-noise (30 agents), already
  covered by weekly CI + on-demand `researchteam update --layer1-only`. Not part of this feature.
- **`--code-index-hook`** (§7-3) — off by default; query-time staleness already keeps results fresh.
  Enabling it is a separate opt-in; leave off.
- **`researchteam/cli.py` passthrough** (A5) — redundant with the bridge `code-query` command.
- **Upstream-agentteams asks** (§7-4: emit the code-index ignore into managed projects) — file as an
  open-item/[AT] note, not code here.
- **Committing a code index** (§4 delta) — the cache is gitignored by design; nothing committed.

## C. Steps (ordered, each with the integrity guard it must honor)

- **S1 Checkpoint.** Commit the untracked handoff doc + this plan's *committed* successor so there's a
  clean baseline to diff every regen against and to `git reset` if a regen corrupts (user's standing
  revert constraint). Confirm `git status` clean before any generator runs.
- **S2 Prove** (no commit): build + query the index against `brief.json`, `--output .github/agents`.
- **S3 gitignore** → verify `git check-ignore .github/agents/references/code-index/manifest.json`.
- **S4 retrieval-surfaces.md** + `MANAGED_FILES += docs/retrieval-surfaces.md`.
- **S5 bridge regen** (claude, then goose): commit S3–S4 first (clean tree), run `--bridge-merge`,
  `--bridge-check` (expect PASS), **review the full diff** — assert: `recall.md`/`todo-from-plan.md`
  untouched, only fenced regions + new `code-recall.md` changed, no entry-file clobber. If anything
  outside fenced/expected regions changed → **revert that file** and fall back to a hand-authored
  `code-recall.md` + manual domain-boundary note.
- **S6 bridge `code-query`** command + help/usage text + (mirror the existing guard style).
- **S7 PSN pointers** — edit ONLY the `## Project-Specific Notes` regions (never AGENTTEAMS fences).
- **S8 doctor probe** (advisory) + extend its test if one exists.
- **S9 gates:** `bash scripts/tests/test_literature_library.sh`, `test_citation_integrity.sh`,
  `validate`, `library-check`/`citation-audit` sanity, `--bridge-check` PASS, `researchteam doctor` green.
- **S10 Commit + memory + open-items** (record the derived-repo sequencing caveat).

## D. Invariants carried across (binding)
- `--bridge-merge` **never** `--bridge-refresh` at the repo root (output root == repo).
- The code-index cache is **never committed** (gitignored); it embeds machine-specific resolved
  paths/versions. Navigation-only — never evidence, never a claim/link anchor, not exhaustive, lexical
  (semantic = stub). Do not conflate the four surfaces.
- No third-party code execution during indexing (static `ast` + metadata only) — safe on collectors.
- Revert any file whose regen corrupts it or breaks infra; baseline commit exists first.

## E. Known sequencing caveat (not a blocker; for open-items)
New `MANAGED_FILES` (`docs/retrieval-surfaces.md`) + the gitignore edit reach **derived** repos only
after (a) researchteam `main` is pushed AND (b) each derived repo reinstalls the CLI (the `_manifest.py`
list ships via pip, not layer-2 self-sync) and runs `researchteam update`. Same R11 sequencing as the
literature library. Upstream integration here is independent of that.

## F. Open audit questions (for the adversarial + conflict pass)
1. Is deferring B1-step-1 (agent-team regen) truly safe, or does it drop a needed surface?
2. Does `docs/retrieval-surfaces.md` create a two-sources-of-truth conflict with the bridge's
   `domain-boundary.md`? How do we keep them from diverging/contradicting?
3. Any path the new `.gitignore` rule would wrongly ignore (something that SHOULD be tracked)?
4. Bridge regen on the repo root — any residual clobber risk beyond `--bridge-merge`? Does regenerating
   the **goose** bridge introduce risk or drift?
5. Does the `code-query` bridge command name/behavior collide with anything; is shelling to a
   possibly-absent `agentteams` handled (guard)?
6. Anti-fabrication: does any wording (doc, skill, PSN) overstate the index as evidence/semantic/
   exhaustive, or blur it with the literature library (which vectorizes relevance summaries, not code)?
7. Does adding to `MANAGED_FILES` risk breaking a derived `update` (404 on the new file) before the CLI
   is reinstalled there?
