# Plan: keppra-transition-report

**Trigger:** User request — "Build a report substantiated by academic literature concerning the safest way to transition from keppra."
**Goal:** Produce `Projects/SiezureTransition/06-keppra-transition-report.md` — a standalone, evidence-tiered, Chicago Author-Date report covering the safest transition protocols from levetiracetam (Keppra), including indications, risk stratification, taper protocols, alternative ASM selection, monitoring, and special-population considerations.

**Agent Sequence:**
1. `@orchestrator` — plan documentation (this file)
2. `@topic-scoping-expert` / `@literature-review-expert` (combined via primary-producer) — draft report drawing on existing bibliography and evidence tier system
3. `@reference-manager` — verify all citations against `references/bibliography.bib`; flag any gaps for addition
4. `@adversarial` — review draft for presupposition blockers
5. `@conflict-auditor` — verify consistency with existing SiezureTransition deliverables

**Success Criteria:**
- All citations map to verified keys in `references/bibliography.bib`
- No claim marked UNVERIFIED appears as evidentiary support
- Evidence tier label appears at every major factual claim
- Adversarial audit: PASS (no blockers)
- Conflict audit: PASS (no contradictions with 00–05 documents)

**Rollback Notes:**
- File is additive; no existing file is modified at creation
- Bibliography entries added during this workflow append-only; no existing entries are altered

**Completion Date:** May 8, 2026
