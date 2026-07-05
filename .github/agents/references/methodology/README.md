<!-- AGENTTEAMS:BEGIN content v=1 -->
# Interpretive Methodology Guide Library — ResearchTeam

> **Purpose:** House reusable, auditable **reasoning references** that tell the research
> team *how to interpret* the literature of a domain — the methodological commitments of
> each tradition, the philosophy-of-science source each uses to justify its models, the
> centuries-spanning genealogy of its concepts, and the conflicts that shape it.
> **Applies to:** any project whose topic falls within a covered domain.
> **Relationship:** These are *references for reasoning*, **NOT authoritative** sources of
> fact and **not** a citation database. Each guide represents *one interpretation among
> several* scholarly framings. Citation authority remains with `@reference-manager` and
> project-local `bibliography.bib`; these guides never resolve citation keys themselves.
> **Authority Position:** Complements (does not supersede) the authority hierarchy in
> `orchestrator.agent.md`. Sits inside `.github/agents/references/` — already within the
> `@conflict-auditor` Audit Scope and the authority map's authoritative paths.
> **Commissioned by:** `@interpretation-advisor` (read-only; produces Briefs).
> **Authored by:** `@content-enricher` (fills the template from the advisor's Brief).
> **Maintenance owner:** `@agent-updater` (mirrors the `unix-philosophy-mapping` precedent).
> **Audited by:** `@reference-manager` (existence) + `@technical-validator` (claim ledger)
> + `@adversarial` (selection) + `@conflict-auditor` (contradictions/boundary).

---

## Why this library exists

A good interpretive frame does not merely list relevant literature; it maps the
*methodological* and *philosophical* commitments behind each perspective and traces how
they developed — often back to Aristotle — while surfacing the intellectual and political
conflicts that shaped them. Encoding that once per domain, rigorously and auditably, lets
every project in that domain read its sources on their own terms instead of flattening
rival traditions into a single frame.

## File class and naming

| File | Role |
|------|------|
| `README.md` | This index + schema + lifecycle (you are here). |
| `_TEMPLATE.methodology.guide.md` | The blank schema every guide fills. |
| `<domain>.methodology.guide.md` | One reasoning reference per domain. |

- Suffix is **`.methodology.guide.md`** — *"guide"*, deliberately **not** `.reference.md`.
  The `.reference.md` suffix and the word "reference database" are reserved for
  `@agent-refactor`'s extracted agent-reference files and `@reference-manager`'s
  bibliography, respectively. A guide is neither.

## Epistemic status and the reasoning-reference carve-out

Every guide carries a `status: provisional | active` field and an explicit Epistemic
Status ("interpretation, contested"). Because guides are **reasoning references** — like
`unix-philosophy-mapping.reference.md` — and not report deliverables, their interpretive
attributions are **exempt from the deliverable-layer `FACT_UNVERIFIED` / `CITATION_UNVERIFIED`
zero-defect gate**, provided:
1. every lineage arrow is either attributed to a named secondary source *as that source's
   claim* or marked `[editors' inference — unsourced]`; and
2. `status: provisional` is set until the full audit chain clears.

This carve-out is documented in `@conflict-auditor`'s Project-Specific Notes. It does **not**
relax anything for compiled deliverables: a `[editors' inference — unsourced]` line may
never anchor a released report claim.

## Anti-fabrication rule (mandatory)

Intellectual history is fabrication-prone because the *works* in a lineage all exist while
the *arrows between them* are contestable historiography. Therefore every arrow is EITHER
`Claim (per <Author Year>, <work>)` — that source's assertion, never stated as settled
fact — OR `Claim [editors' inference — unsourced]`. `@reference-manager` confirms works
exist; `@technical-validator` runs a claim ledger; genuine faithfulness is a **named human
/ historiographic review** recorded in the guide's audit log. No agent is claimed to close
this gap mechanically.

## Guide lifecycle

enumerate (name the survey(s) + their known exclusions; ≥2 surveys or an explicit
inherited-canon statement) → draft → `@reference-manager` (existence) →
`@technical-validator` (claim ledger; `UNVERIFIED` → inference) → `@adversarial`
(superset / pruning / survey choice) + `@conflict-auditor` (contradictions; boundary vs.
`00`/`01`) → `@content-enricher` persists → `status: active`. `provisional` until every
step clears.

## Index of guides

| Domain | File | Status |
|--------|------|--------|
| Economics — theories of the business cycle | `economics-business-cycles.methodology.guide.md` | provisional |

_(Add a row when a guide is activated.)_
<!-- AGENTTEAMS:END content -->
