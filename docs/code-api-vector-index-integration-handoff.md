# Handoff — Integrating agentteams **Code & API Vector Index (F-CODEIDX)** into researchteam

**From:** agentteams (upstream) — PR #50 `feat(code-index): …`, merged to `main` (`efe8f12`).
**To:** researchteam maintainer(s).
**Date:** 2026-07-08.
**Scope:** (1) integrate the feature into the **researchteam module**, and (2) into researchteam's
**local agent infrastructure**.
**Status of upstream:** shipped, audited (two adversarial + conflict rounds), full CI green (macOS +
Ubuntu × Py 3.11/3.12). Design: `agentteams/references/plans/code-api-vector-index.plan.md`.

> **You do not need to copy any agentteams code.** researchteam consumes agentteams as the optional
> `update` extra (`pyproject.toml`: `update = ["agentteams @ git+…/agentteams"]`). The feature arrives by
> **refreshing that dependency**; the work here is (a) surfacing the new CLI/skill and (b) reconciling it
> with researchteam's own **literature library**, which is a domain sibling of this feature.

---

## 1. What F-CODEIDX is (30-second version)

A stdlib-only **sparse TF-IDF vector index over code**: repository local scripts (`local-script`), the
external **API modules** those scripts import (`api-module`), and **API documentation** (`api-doc`),
labeled by `source_kind` and filterable with `--code-kind`. It is the code sibling of agentteams'
prose **memory-index**.

- **New CLI:** `agentteams --refresh-code-index`, `--query-code TEXT`, `--code-query-k N`,
  `--code-query-strategy {lexical,vector}`, `--code-kind {local,api,doc,all}`.
- **New skill:** `/code-recall` (emitted into `.claude/skills/` by the copilot→claude bridge).
- **Artifact:** a **gitignored local cache** at `references/code-index/` (`manifest.json` + per-kind
  partition files). Never committed, never drift-tracked, never git-hook-staged.
- **Never executes third-party code:** API resolution is static (`ast` + `importlib.metadata` +
  `direct_url.json`) only. Unresolvable deps degrade to declared-only.
- **Triggers:** query-time staleness (primary; `api-*` keyed on a **dependency fingerprint** so a
  dependency upgrade is caught even when no local file changed); `--update` keeps an *existing* cache
  fresh; optional off-by-default `--code-index-hook` pre-commit warm-up.

---

## 2. Relationship map — researchteam now has (up to) FOUR retrieval surfaces

This is the crux of the handoff. After integration, researchteam's agents can reach these **distinct,
navigation-only** retrieval surfaces. They must **not be conflated** (agentteams ships a
`domain-boundary.md` that already names the first three; researchteam must extend it to include #4):

| # | Surface | Content | Query | Storage |
|---|---------|---------|-------|---------|
| 1 | **memory-index** (agentteams) | durable **prose** — work summaries, CHANGELOG, plans | `agentteams --query-index` · `/recall` | gitignored/local |
| 2 | **code-index** (agentteams, **NEW**) | **code + external APIs** the scripts use | `agentteams --query-code` · `/code-recall` | **gitignored cache** `references/code-index/` |
| 3 | **project retrieval-integrator** | relational/metadata contract | project-defined | project-defined |
| 4 | **literature library** (researchteam) | research **sources / relevance summaries** | `library-query` (bridge) | **committed base index** `references/library/*.jsonl` + gitignored corpus/vectors |

**Design deltas between #2 (code-index) and #4 (literature library)** — both are stdlib TF-IDF,
deterministic, offline, no LLM-authored numbers, navigation-only, but they diverge deliberately:

- **IDF timing / churn.** The literature library commits **raw per-record term counts** and computes IDF
  *at query time* (low churn, aggregation-safe) because its base index **is committed**. The code-index
  computes IDF + `vector_norm_sq` *at build time* because its cache **is gitignored** (churn is a
  non-issue). If researchteam ever decides to *commit* a code index, prefer the library's query-time-IDF
  scheme; as a gitignored cache, the build-time scheme is correct as-is.
- **Content domain is disjoint.** Literature = sources the agents cite; code-index = the *code and APIs*
  that do the collecting/analysis. They answer different questions ("what did we read about X" vs "where is
  the collector / which API does it call"). Keep them separate; do not merge the corpora.

**Conflation risk (act on this):** agents will now have `/recall` (prose), `/code-recall` (code/API), and
`library-query` (literature). Update the disambiguation guidance in
`reference-manager`, `navigator`, `literature-review-expert`, and `orchestrator` (PSN pointers) so an
agent picks the right surface. researchteam already practices this discipline (e.g. renaming
`check_literature_library_integrity.sh` to avoid clobbering OrthodoxLLM's check) — extend it.

---

## 3. Part A — Integrate into the researchteam **module**

researchteam's module (`researchteam/`) does **not** vendor agentteams; `researchteam update`
(`_update_cmd.py::_run_agentteams`) shells out to the `agentteams` console script with `--update --merge`
against a union descriptor. So:

**A1 — Refresh the agentteams dependency (the whole integration at the module level).**
- Editable local checkout (preferred for dev):
  `pip install -e /Users/jamescaton/githubrepositories/agentteams --no-build-isolation`
  (the checkout is already on `main` with F-CODEIDX).
- Or the git extra: `pip install -U 'agentteams @ git+https://github.com/jlcatonjr/agentteams'`.
- Verify: `agentteams --version` runnable; `researchteam doctor` green (its preflight liveness-checks the
  `agentteams` console script).

**A2 — What becomes available immediately** (no researchteam code changes required):
`agentteams --refresh-code-index`, `--query-code`, `--code-kind`, and `/code-recall` emission. Because
researchteam's base install stays **dependency-free** and F-CODEIDX is **stdlib-only**, this adds **no new
runtime dependency** to researchteam (`jsonschema` was already required by the `update` extra).

**A3 — Compatibility (verified against researchteam `requires-python = ">=3.10"`):** F-CODEIDX uses
`sys.stdlib_module_names` (3.10+) and `ast.unparse` (3.9+) — both satisfied. No blockers.

**A4 — Decide the code-index's scope for researchteam.** Point it at researchteam's own code — the
`researchteam/` module, `scripts/`, and any collectors — so agents can navigate "where is the collector /
build step / which API does it call". Note: researchteam's scripts are largely **stdlib** (urllib, json,
hashlib, tarfile…), so the `api-module`/`api-doc` partitions will be small/empty and the value concentrates
in the `local-script` partition. The **no-execution** guarantee matters here: indexing collector scripts
that import scraping/scientific libraries will **never** trigger their network or import side effects.

**A5 (optional) — module-level convenience.** If you want `researchteam query-code …` to mirror
`library-query`, add a thin passthrough in `researchteam/cli.py` that shells to
`agentteams --query-code …` (same pattern `_run_agentteams` already uses). Not required — the
`agentteams` console script is sufficient.

---

## 4. Part B — Integrate into researchteam's **local agent infrastructure**

researchteam's `.github/agents/` (30 agents), `.claude/`, and `.goose/` are generated from `brief.json`
via agentteams. Two concrete regenerations surface the feature to the agents:

**B1 — Regenerate the agent team + the claude bridge.**
1. Agent team (picks up the new architecture/module map, etc.):
   `researchteam update` (delegates to `agentteams --update --merge`) — or run agentteams directly.
2. **Claude bridge** (this is what emits `.claude/skills/code-recall.md` and the three-surface
   `domain-boundary.md`; `researchteam update` does **not** run the bridge):
   ```
   agentteams --bridge-from .github/agents --framework claude --output . --bridge-merge
   ```
   **Integrity-critical:** use `--bridge-merge`, **never** `--bridge-refresh`, because the output root is
   the researchteam repo itself (same invariant agentteams documents in
   `references/bridge-refresh-safety.md`). `--bridge-merge` refreshes only fenced/managed regions and
   preserves your entry files; it writes a backup under `.agentteams-backups/`. Confirm with
   `--bridge-check` (expect PASS) afterward.
   Expected result: `.claude/skills/` gains `code-recall.md` (alongside the existing `recall.md`,
   `todo-from-plan.md`).

**B2 — Gitignore the code-index cache (researchteam does NOT yet ignore it).**
researchteam's `.gitignore` ignores the literature library's bulky store but has **no** `references/code-index/`
rule. Because researchteam also manages nested projects, add both the root and nested patterns:
```
# agentteams code & API index — gitignored local cache (never commit; embeds
# machine-specific resolved paths/versions). See docs/…-handoff.md.
references/code-index/
**/references/code-index/
```
(Upstream follow-up worth filing: have agentteams *emit* this ignore into managed projects, the way it
already emits the literature library's managed `.gitignore` block — until then, add it here.)

**B3 — Extend the domain-boundary doc to FOUR surfaces.** The bridge emits agentteams'
three-surface `domain-boundary.md`. Add researchteam's **literature library** as surface #4 (see the table
in §2) in researchteam's own agent-facing docs, so the boundary the agents read is complete.

**B4 — Update agent disambiguation (PSN pointers).** In `reference-manager`, `navigator`,
`literature-review-expert`, `orchestrator`: "prose → `/recall`; code/API → `/code-recall`; research
sources → `library-query`." Mirror the existing literature-library pointer wiring you added in
commit `0a8a519`.

---

## 5. Integrity & safety (carry these invariants across)

- **`--bridge-merge`, never `--bridge-refresh`** at the repo root (B1). Same rule as agentteams'
  `bridge-refresh-safety.md`; researchteam inherits it.
- **Backups + git checkpoint.** Commit before regenerating; agentteams also auto-backs-up under
  `.agentteams-backups/`. Regeneration is fenced-region-only under `--merge`, so manual content is preserved.
- **No third-party execution** during indexing (static `ast` + metadata only) — safe for collector code.
- **Determinism / low churn.** The code-index is a gitignored cache (no commit churn). If you ever commit a
  code index, adopt the literature library's query-time-IDF scheme to keep diffs small.

---

## 6. Verification checklist

- [ ] `pip install -e /…/agentteams` (or `-U` the git extra); `agentteams --version` runs; `researchteam doctor` green.
- [ ] `agentteams --refresh-code-index --description brief.json --output .github/agents` builds `references/code-index/` (under the agent dir).
- [ ] `agentteams --query-code "literature library build" --description brief.json` returns ranked `[local-script]` hits.
- [ ] `agentteams --bridge-from .github/agents --framework claude --output . --bridge-merge` → `.claude/skills/code-recall.md` present; `--bridge-check` PASS.
- [ ] `.gitignore` updated; `git check-ignore .github/agents/references/code-index/manifest.json` → ignored.
- [ ] Domain-boundary + agent PSN pointers updated for all four surfaces.
- [ ] researchteam test suite green; no regression to the literature-library scripts/tests.

---

## 7. Open decisions for the researchteam maintainer

1. **Adopt the code-index over researchteam's own code?** Recommended for the `researchteam/` module +
   `scripts/` (navigation value); the API partitions will be thin given the stdlib-only code.
2. **Unify the retrieval-surfaces doc?** One `docs/retrieval-surfaces.md` enumerating all four is clearer
   than four scattered notes — and blocks future conflation.
3. **Enable the `--code-index-hook` warm-up?** Off by default; query-time staleness already keeps results
   fresh. Only enable if you want the cache pre-warmed on commit (it never `git add`s the cache).
4. **File the upstream ask** to have agentteams emit the `references/code-index/` ignore into managed
   projects (so B2 becomes automatic for every researchteam-managed project).

---

*Prepared as an agentteams → researchteam handoff. agentteams reference:
`docs_src/api-reference/code-index.md`, `docs_src/api-reference/code-sources.md`,
`references/plans/code-api-vector-index.plan.md` (+ `.adversarial.md`, `.conflict-audit.md`).*
