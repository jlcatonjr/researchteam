# Per-Project Vectorized Literature Library — Protocol

Agent documentation for building and maintaining a **per-project, vectorized library of the
literature the agents deem relevant** while investigating. Reusable across projects; each project
builds and owns its own library, separable from every other. This is the single authoritative spec —
`reference-manager`, `literature-review-expert`, and the orchestrator point here.

## The honest ceiling (read first — binding; do not soften)

Generalized from the OrthodoxLLM instance, whose guardrails "must not be softened to make it usable":

- **Records ship `UNVERIFIED`** (`verification_state: "UNVERIFIED — no human resolution performed"`).
  A green `check_literature_library_integrity.sh` certifies **structure, not truth**.
- **Vector similarity is navigation, not evidence.** A query candidate is a pointer for a human to
  inspect — never a source relationship, never a link, never anchors a claim. "Absence of a candidate
  ≠ absence of a source." Candidates are query-time output; they are not stored as facts.
- **"Vectorized" = a real, LEXICAL TF-IDF layer** *for this base library*. Vectors are computed by a
  real vectoriser (`build_literature_library.py`, stdlib, deterministic) — **never authored by a
  model** (an LLM-typed vector is fabrication). The base literature library is deliberately lexical:
  never call *it* "semantic search," and never claim "semantic search over all the <topic>
  literature." A **semantic/dense** layer over source *body text* is no longer only a stub — it is
  standardized as **retrieval surface #5 (source corpus)** in `docs/retrieval-surfaces.md`, an
  **additive** dense index a corpus may adopt (real local embedder, page-anchored, `text_sha256`
  traceability, its own honest ceiling). Adopting surface #5 does **not** make this base library
  semantic; the two are disjoint surfaces (relevance summaries vs. source body text).
- **No self-attestation.** The gate rejects a record claiming `verification_state: resolved/attested`
  in an autonomous run; a human sign-off (`LIBRARY_HUMAN_SIGNOFF=1`) with an out-of-band anchor is
  required to assert resolution.
- **Acquisition is out-of-band.** Full text / abstracts are provisioned by a separate, human-gated
  step — **never an audit-time fetch** by an investigating agent. The base library needs no fetch.
- **Not exhaustive.** The library captures the sources the agents surfaced and deemed relevant so
  far; the `coverage_statement` disclaims completeness. "Exhaustive" is a goal, not a provable claim.

## What the library is

Under `Projects/<project>/references/library/` (user-owned; the researchteam generator never touches it):

- `literature.jsonl` — one record per relevant source, keyed to the project `.bib`:
  `{key, title, authors, year, source_url, doi, source_db?, relevance:{summary, deemed_by,
  investigation, source}, abstract?, tags?, verification_state, record_text_sha256}`. The
  **`relevance.summary`** — *why/how this source matters to the project* — is the text that gets
  vectorized. `source_db` is populated **only if an agent supplies it explicitly**; it is never
  inferred from a URL host (a WorldCat/Amazon/`search?q=` landing is a finding aid, not a database of
  origin). `record_text_sha256` hashes the indexed text (freshness) — it is **not** a source-text
  confirmation.
- `term-vectors.jsonl` — one line per record, **raw term counts** (`{key, n_terms, terms}`). IDF is
  computed at **query time**, so the committed artifact is low-churn and a future shared-vocabulary
  re-fit (cross-project aggregation) stays possible. Never commit global `idf`/`postings`.
- `library-manifest.json` — counts, freshness hashes, `vector_model_id`, `vector_method`,
  `coverage_statement`, and the ceiling banner.

## How agents build it out as they investigate

1. **Deem relevance.** When investigating (e.g. `@literature-review-expert` preparing a Component
   Brief, or `@reference-manager` adding a verified citation), a source judged relevant is added to
   the project `.bib` with a `url`/`doi` (the `[LINK]`/`[REFURL]` citation standards apply).
2. **Author the relevance record.** `@reference-manager` (which holds `edit`) creates/updates the
   source's `literature.jsonl` record with a **substantive `relevance.summary`** in the agent's own
   words — *why this source is relevant to this project, what it contributes* — and sets
   `relevance.source: "agent-authored"` (and `deemed_by`/`investigation` where known). A first
   `build_literature_library.py` run **seeds** records from `.bib` notes as a starting point, stamped
   `relevance.source: "seeded-from-bib-note"`; the gate flags every seeded/thin record
   `NEEDS-ENRICHMENT` until an agent authors/confirms it. **That flag is the loop** — it is how the
   library "builds out as the agents investigate."
3. **Rebuild the vectors** — `bash scripts/claude_researchteam_bridge.sh library-build <project>`
   (deterministic, offline). Automatic surface: the orchestrator's **advisory closeout hook** rebuilds
   + gates before `@output-compiler`. What is automatic is the *rebuild*; the *relevance judgment* is
   the agents' investigation.
4. **Navigate** — `… library-query <project> "<terms>"` returns lexical candidates (navigation only).
5. **Gate** — `… library-check <project>` (fail-closed) before relying on the library.

## Commands

```bash
bash scripts/claude_researchteam_bridge.sh library-build <project>          # (re)build the index
bash scripts/claude_researchteam_bridge.sh library-query <project> "<terms>" # navigate (candidates)
bash scripts/claude_researchteam_bridge.sh library-check <project>          # fail-closed integrity gate
# direct: python3 scripts/build_literature_library.py <project>;  scripts/check_literature_library_integrity.sh <project>
```

## Separability & future aggregation

Each project's library is independent (own records, own `.bib`, own vectors). Cross-project cosine
scores are **not comparable** (per-project IDF) — by design. Cross-topic **aggregation** (a shared
library over multiple projects) is deferred; the raw-term-count storage keeps it possible via a
future shared-vocabulary re-fit over the union of records. Do not compare or merge project vectors
until that aggregator exists.

## Deferred: the out-of-band full-text layer

For public-domain sources, an optional layer (OrthodoxLLM-style) acquires full text **out-of-band**
into `Projects/<project>/references/library/corpus/<slug>.txt` (gitignored) + a committed
`<slug>.provenance.json` (source URL + sha256 + license), and vectorizes the text. This is documented
for future work; it is **not** built by the base capability, and acquisition is **never** an
audit-time agent fetch.

> **A separate, opt-in profile exists for products that genuinely need answer-time grounding.** Some
> interactive/conversational products cannot use a pre-provisioned corpus and must ground a reply *now*.
> That case is documented as a distinct, clearly-labelled option — `docs/on-the-fly-retrieval-profile.md`
> — which relaxes **only** the acquisition ceiling (answer-time fetch from a curated allowlist) and carries
> its own weaker honesty label ("navigation, not a proof; not peer-reviewed truth"). It does **not** change
> the corpus-of-record law above: the base library's acquisition remains out-of-band and human-gated.

## Relation to OrthodoxLLM

OrthodoxLLM has its own **instance-local, domain-specific** library pipeline
(`build_catalogue.py`/`acquire_text.py`/`build_vectors.py` with sklearn, `check_library_integrity.sh`,
canonical-repertory IDs) — a superset. This researchteam capability is the **domain-agnostic,
stdlib** generalization; its gate is deliberately named `check_literature_library_integrity.sh` so it
never overwrites OrthodoxLLM's instance-local `check_library_integrity.sh`.
