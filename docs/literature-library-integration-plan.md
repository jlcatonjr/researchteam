# Integration Plan — Per-Project Vectorized Literature Library

**Date:** 2026-07-08
**Author:** infrastructure integration (Claude)
**Trigger (user request):** "Create agent documentation that builds out a vectorized library of
literature deemed relevant via the agents' investigation … occur automatically as the agents
investigate … exhaustive for the project … each project builds its own library … separable between
projects."
**Status:** IMPLEMENTED & VERIFIED 2026-07-08 (all acceptance criteria met — §4; demonstrated on
OrthodoxLLM `development-of-offices`). Revised after adversarial + conflict audit (§0).

---

## 0. What the audit changed (binding resolutions — do not revert to the draft)

The draft was audited by independent adversarial (measured against real `.bib` files) and conflict
(against the anti-fabrication memory + on-disk OrthodoxLLM) passes. These are binding; §§1–5 reflect
them.

- **R1 (CRITICAL — the artifact was a toy).** The draft vectorized `.bib` records. Measured: real
  bibs have almost no relevance text (`LaborMatchingMacroeconomics`: 25 entries, **one** `note` =
  `Volume 3A`, **zero** abstracts) → the vectors collapse to **title similarity**, not a library.
  → The library vectorizes the **agents' relevance text**: a **required** per-source
  `relevance.summary` (the investigation output — *why/how this source matters to the project*) +
  optional `abstract`, plus the title. Sources with only a title (thin/absent relevance) are **valid
  but flagged by the gate for enrichment** — that flag *is* the "build it out as agents investigate"
  loop. It stays a "literature library" because it vectorizes real investigation prose; it is honestly
  **lexical over relevance summaries/abstracts**, semantic = STUB.
- **R2 (CRITICAL — fabricated provenance).** The draft inferred `source_db` from the URL host. But the
  real URLs are finding-aids/verification landings (`search.worldcat.org/…`, `openlibrary.org/…`,
  `amazon.com/…`, even `…/search?q=…`) — **not** the database a source came from. → **No host→`source_db`
  inference.** Record `source_url`/`doi` verbatim; set `source_db` only when the agent supplies it
  explicitly (never inferred), else omit.
- **R3 (relevance is a first-class, enforced field).** Not "the `.bib` note" (that is
  existence-verification, and empty for 24/25 real entries). → A dedicated
  `relevance:{summary, deemed_by, investigation, source}` per record; the **gate enforces** a
  non-trivial `summary`. Seeding `summary` from an existing `.bib` note is allowed but stamped
  `source:"seeded-from-bib-note"` + `UNVERIFIED`, and still flagged if thin. Relevance capture is an
  **enforced obligation, not an advisory PSN pointer** (the on-disk evidence shows advisory ⇒ nobody
  does it).
- **R4 (no committed IDF/postings — churn + merge-conflict + aggregation killer).** Global `idf`
  rewrites on every add; file-order record indices renumber on insert → whole-file diffs + guaranteed
  merge conflicts, and per-project IDF makes cross-project vectors incomparable (precluding the
  aggregation the draft claimed to preserve). → Commit **raw per-record term counts**
  (`library/term-vectors.jsonl`, one stable line per record, keyed) + the records; **compute IDF at
  query time**. Low-churn, and a future shared-vocabulary re-fit (aggregation) stays possible.
- **R5 (honest automation boundary).** "Automatic as agents investigate" over-claimed. → What is
  automatic is the **index (re)build** (a script/bridge/closeout step over text already present,
  offline); the **relevance judgment + summary** are the agents' investigation (enforced by the gate,
  not magic). **No pre-commit rebuild hook in this cut** (churn/theater risk). Full-text/abstract
  **acquisition stays out-of-band — never an audit-time fetch.**
- **R6 (prove before propagating).** The draft shipped ~12 managed surfaces before the core was shown
  useful. → Implement the core (build/query/gate scripts + protocol + one agent-doc surface + bridge +
  tests), **demonstrate on one real project with real relevance text** (OrthodoxLLM
  `development-of-offices`, whose notes carry genuine agent relevance judgments), *then* register
  `MANAGED_FILES`. Defer: the PD-full-text acquisition layer (document only) and any first-class roster
  agent.
- **R7 (HIGH CONFLICT — filename clobber).** The draft's managed `scripts/check_library_integrity.sh`
  is the **exact name** of OrthodoxLLM's instance-local 13 KB domain gate → `researchteam update` would
  **overwrite it** on the reference instance the memory protects. → Rename the managed gate
  **`scripts/check_literature_library_integrity.sh`**. The build/query script names don't collide.
- **R8 (MANAGED sequencing — R11-shaped).** `_update_cmd.py` 404s on any `MANAGED_FILES` entry absent
  upstream; `_manifest.py` ships **via the pip package** (not self-synced). → Land the 4 files on
  upstream `main` **with** the `_manifest.py` edit (this repo *is* upstream — committing+pushing does
  it); derived repos get the new list only after `pip install -U`. Documented, not silent.
- **R9 (schema honesty).** Set `artifact_type:"literature-index"`. The index mirrors the *TF-IDF/
  postings approach* of `memory-index.json`, not its `vector_model_id:null` convention — use a non-null
  `vector_model_id:"researchteam-tfidf-v1"` with `vector_method:"lexical-baseline"` and the STUB banner
  adjacent so it can't read as a neural model.
- **R10 (hash semantics).** `record_text_sha256` hashes the record's **indexed text** (freshness/
  determinism), explicitly **not** a source-text confirmation — named distinctly from OrthodoxLLM's
  `source_text_sha256` so it can't be mistaken for text-fidelity evidence that doesn't exist here.
- **R11 (exec-bit reality).** The exec-bit sync fix is `.sh`-only. → Invoke the `.py` scripts via
  `python3` in the bridge; only the `.sh` gate relies on `+x`.
- **R12 (gitignore coupling).** Because the scripts are managed (R7), the *optional* full-text corpus
  ignore pattern (`Projects/*/references/library/corpus/*.txt`) goes in the **managed root `.gitignore`**
  (propagates). The base layer commits raw term counts — **no gitignored vector store**.
- **R13 (no false parity).** Don't claim ranking-score parity with OrthodoxLLM's sklearn vectors —
  honest lexical baseline.
- **R14 (push back on "exhaustive").** "Exhaustive" is not deliverable or provable. → The gate asserts
  a `coverage_statement` that **disclaims completeness**; reframed to "captures the sources the agents
  surfaced and deemed relevant." Stated plainly to the user.
- **R15 (protocol-first, no new roster agent).** Matches OrthodoxLLM's audited protocol-only choice and
  avoids agentteams-roster fragility; indexing is script-mechanical. "Agent documentation" = the
  protocol doc + `reference-manager` / `literature-review-expert` USER-EDITABLE sections that name the
  **literature-librarian responsibility**. A first-class archetype is a documented future option.
- **R16 (ceiling honored — keep it).** All ceiling rules baked into every surface: records ship
  `UNVERIFIED`; vectors computed by a real (stdlib) vectoriser, never authored; vector = **navigation,
  not evidence** (candidates segregated, never a link/claim anchor); no self-attestation (gate rejects
  `resolved`/`attested` without `LIBRARY_HUMAN_SIGNOFF=1`); acquisition out-of-band; green gate =
  structure not truth; never claim "semantic search over all <topic> literature."

---

## 1. What the user is asking for (decomposed, with the honesty the audit requires)

A **per-project, vectorized store of the literature the agents deem relevant while investigating**,
separable per project. **Honest reframes:** "vectorized" = a real *lexical* TF-IDF navigation layer
over the agents' relevance prose (a semantic/dense layer is a documented STUB). "Automatic" = the
index rebuild is scripted; the relevance judgment is the agents' investigation (gate-enforced).
"Exhaustive" is **not provable** — reframed as "captures the sources the agents surfaced and deemed
relevant," with a coverage statement that disclaims completeness.

---

## 2. Findings (unchanged from the draft; see §0 for what they forced)

OrthodoxLLM already built this — a scripted `build_catalogue → acquire_text (out-of-band) →
build_vectors (real sklearn TF-IDF) → query_vectors` pipeline + a fail-closed gate, **instance-local,
protocol-only**, with the anti-fabrication ceiling (UNVERIFIED; vector=navigation-not-evidence;
real-vectoriser-never-authored; no self-attestation; out-of-band acquisition; "vectorized"=lexical,
semantic=STUB). Its vectorized **corpus is shared** (one domain); per-project separation is at the
secondary-`.bib` level. researchteam's `memory-index.json` proves a **stdlib** TF-IDF is viable (no
dense embeddings anywhere; base install dependency-free). Per-project references are user-owned under
`Projects/<project>/references/` — untouched by the generator, so built by a project script.

---

## 3. Design (post-audit)

### 3.1 Per-project layout — `Projects/<project>/references/library/` (all committed, low-churn)
- `literature.jsonl` — one JSON record per relevant source (stable, keyed, append-friendly):
  `{ key (ties to the .bib), title, authors, year, source_url, doi, source_db?(agent-supplied only),
     relevance:{summary, deemed_by?, investigation?, source}, abstract?, tags?,
     verification_state:"UNVERIFIED", record_text_sha256 }`.
- `term-vectors.jsonl` — one line per record: `{ key, n_terms, terms:{term:count} }` (**raw counts**,
  computed by a real tokenizer; IDF deferred to query time). Stable per record → low churn, aggregation-safe.
- `library-manifest.json` — `{ artifact_type:"literature-index", schema_version, project, built_at,
   source_bib_sha256, records_sha256, record_count, vector_model_id:"researchteam-tfidf-v1",
   vector_method:"lexical-baseline", vector_state:"lexical-operational; dense/semantic STUB",
   inclusion_criterion, coverage_statement (disclaims completeness), ceiling_banner }`.
- (optional advanced, deferred) `library/corpus/<slug>.txt` (gitignored) + `<slug>.provenance.json`
  (committed) for out-of-band PD full text — documented in the protocol, not built now.

### 3.2 Scripts (stdlib-only; no new dependency)
- `scripts/build_literature_library.py` — reconciles the project `.bib` with `literature.jsonl`
  (**seeds** missing records from `.bib` entries, `relevance.source:"seeded-from-bib-note"`,
  `UNVERIFIED`, flagged-thin), tokenizes each record's indexed text (title + relevance.summary +
  abstract), writes **raw** `term-vectors.jsonl` + `library-manifest.json`. Deterministic, offline, no
  network, **no LLM-authored numbers**. Invoked `python3 …`.
- `scripts/query_literature_library.py` — loads records + raw term vectors, computes IDF over the
  corpus, cosine-ranks against a query → prints candidates stamped **navigation-only, never a link**.
- `scripts/check_literature_library_integrity.sh` — **fail-closed, bash-3.2** gate (renamed per R7):
  manifest fresh vs `.bib`+records (`source_bib_sha256`/`records_sha256`); every record ties to a `.bib`
  entry and carries a `source_url`/`doi`, `verification_state:UNVERIFIED` (rejects self-attested
  `resolved`/`attested` without `LIBRARY_HUMAN_SIGNOFF=1`), and a **non-trivial `relevance.summary`**
  (else `NEEDS-ENRICHMENT`, advisory); `coverage_statement` present + disclaims completeness; ceiling
  banner present. `LITERATURE_LIBRARY_ADVISORY=1` downgrades. Prints "green = structure, not truth."
- `scripts/tests/test_literature_library.sh` — bash-3.2 throwaway fixtures: fresh/stale manifest,
  missing-link, self-attested-without-signoff, thin-relevance, determinism, advisory downgrade.

### 3.3 Agent documentation (protocol-first — R15)
- `docs/literature-library-protocol.md` (MANAGED) — the single authoritative spec: what the library
  is; the ceiling (verbatim R16); the per-project layout; **how agents build it as they investigate**
  (for each source deemed relevant, add/enrich a `literature.jsonl` record with a substantive
  `relevance.summary` + `source_url`; then `library-build`); how to query (navigation only); the
  separability guarantee + future-aggregation note; the deferred out-of-band full-text layer.
- USER-EDITABLE PSN sections (no fences touched): `reference-manager` (owns/edits the records) and
  `literature-review-expert` (deems relevance during investigation) each get a "Literature-librarian
  responsibility" pointer; the orchestrator gets a routing line + an **advisory closeout hook**
  (rebuild + gate before `@output-compiler`, patterned on the methodology-coverage / 2-fold-audit hooks).

### 3.4 Automation + bridge (R5 honesty)
- Bridge: `library-build [project]`, `library-check [project]`, `library-query [project] "<q>"`
  (each `python3`/`bash` invoked). On-demand; the closeout hook makes rebuild+gate a standing beat.
  **No pre-commit rebuild hook** in this cut.

### 3.5 Propagation (R6, R7, R8, R12)
- `_manifest.py::MANAGED_FILES` += `scripts/build_literature_library.py`,
  `scripts/query_literature_library.py`, `scripts/check_literature_library_integrity.sh`,
  `docs/literature-library-protocol.md`. Per-project `library/` stays user-owned under `Projects/`.
  Managed root `.gitignore` += `Projects/*/references/library/corpus/*.txt`. Sequencing per R8 (land on
  upstream `main` with the manifest edit; derived repos need `pip install -U`).

---

## 4. Acceptance criteria
- [x] `build_literature_library.py <project>` builds `Projects/<project>/references/library/` from the
      `.bib` + `literature.jsonl`, stdlib only, deterministically (same input → byte-identical output),
      no network; `term-vectors.jsonl` holds **raw counts** (no global idf/postings committed).
- [x] Records carry `source_url`/`doi`, a `relevance` object, `verification_state:UNVERIFIED`,
      `record_text_sha256`; **no `source_db` is inferred from a host**.
- [x] `query_literature_library.py <project> "<q>"` returns cosine-ranked candidates stamped
      navigation-only; IDF is computed at query time (not committed).
- [x] `check_literature_library_integrity.sh <project>` is fail-closed (bash 3.2): flags a stale index,
      a missing source link, a self-attested record without signoff, a thin `relevance.summary`
      (advisory `NEEDS-ENRICHMENT`), and a coverage statement that fails to disclaim completeness; prints
      the ceiling banner; `LITERATURE_LIBRARY_ADVISORY=1` downgrades. Unit tests pass under bash 3.2 and 5.
- [x] `bash …/claude_researchteam_bridge.sh library-build|library-check|library-query <project>` work.
- [x] **Demonstrated on a real project** (OrthodoxLLM `development-of-offices`): a library builds from
      real relevance text, a query returns sensible related-source candidates, the gate is green, and
      it honestly flags any thin records.
- [x] The managed gate is named `check_literature_library_integrity.sh` (does **not** collide with
      OrthodoxLLM's instance-local `check_library_integrity.sh`).
- [x] `docs/literature-library-protocol.md` + the agent PSN pointers reference one protocol; no
      `AGENTTEAMS` fence modified; `validate_agentteams_update.sh` passes; `researchteam update
      --dry-run` recognizes the new `MANAGED_FILES`; `Projects/*/references/library/` never treated as managed.
- [x] Every surface distinguishes navigation from evidence; nothing claims semantic search, proven
      relevance, or exhaustiveness.

## 5. Rollback
Additive and independent; revert order: bridge commands → orchestrator/agent PSN pointers → protocol
doc → gitignore/manifest entries → scripts+tests. No existing file destructively rewritten; per-project
`library/` data is regenerable/disposable.
