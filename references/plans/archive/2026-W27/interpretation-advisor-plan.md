# Plan — Interpretation Advisor + Methodology Guide Library (2026-W27)

**Goal:** Add an expert interpretation agent that maps the methodological commitments,
philosophy-of-science provenance, centuries-spanning genealogy, and shaping conflicts
behind a research topic, plus a reusable, auditable methodology-guide library it draws on.

**Process followed:** plan → adversarial + conflict audit (round 1) → revise (v2) →
adversarial + conflict audit (round 2) → revise (v3) → implement → validate. Full audit
reports and v1/v2/v3 plans retained in the session scratchpad.

## Design (v3, twice-audited)
- Agent `@interpretation-advisor`: read-only advisory **archetype** (in
  `selected_archetypes`, not a compiled component; not governance). Named off the
  `-expert` suffix so the eval "one expert per component" invariant stays true.
- **Commissions, does not write:** `@primary-producer` writes the per-project
  `Projects/<project>/interpretation/interpretive-map.md` scaffold; `@content-enricher`
  persists `.github/agents/references/methodology/<domain>.methodology.guide.md`;
  `@agent-updater` maintains guides.
- **Anti-fabrication:** every lineage arrow is attributed to a named secondary source
  *as that source's claim* or marked `[editors' inference — unsourced]`; reference-manager
  checks existence, technical-validator runs a claim ledger, human review is the only true
  faithfulness check. Reasoning-reference carve-out documented in conflict-auditor notes.

## Key audit findings resolved
- R1: fabrication gate can't be mechanical → honest inline-marking + claim ledger.
- R2: guide writer mis-chartered (agent-refactor extracts) → content-enricher authors.
- R3: component registration blocks output-compiler / trips eval count → archetype, non-`-expert` name.
- R4: placement/ownership/terminology → `.github/agents/references/methodology/`, `.guide.md`, owned+authority-mapped.

## Residual (honest)
- Weekly CI `agentteams --update --merge` may normalize the archetype; local generator is
  broken (editable install points at a deleted worktree) so it could not be pre-run.
- provisional/active is convention+audit, not a fail-closed pipeline validator.

See `interpretation-advisor-steps.csv` for the step ledger.
