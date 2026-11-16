# Plan: coded term definitions and a synced term-occurrence index (2026-11-16)

Operator request (2026-11-16): every researchteam project should define its terms in a coded register so
consistent usage can be enforced; every appearance of a listed term across project documentation should be
indexed; and the index should be kept in sync by a hook or a similarly reliable trigger.

The work has three parts, in this order.

1. **Research project** `Projects/CodedTermIndexing/`. It identifies the role of synced term indexing in the
   academic literature and in existing infrastructures and field guides. It follows the standard protocols:
   interpretive map with a Historical setting register, the mechanical citation audit, the doubled semantic
   audit, and an audit ledger.
2. **Feature plan** `docs/terminology-index-integration-plan.md`, derived from the research. It is audited by
   `@adversarial`, `@conflict-auditor`, `@security` and `@code-hygiene`, then revised.
3. **Implementation** of the revised plan, with tests, on branch `feat/term-index`, merged under PS-2.

Scope notes.

- The tool documentation the operator asked about (existing infrastructures and field guides) is cited as
  primary evidence of what each tool does. It sits outside the scholarly authority hierarchy and is labelled
  as such in the deliverables.
- No change is made to generated agent files inside `AGENTTEAMS` fences.
- `.claude/settings.json` is operator-owned and is not edited. Hook wiring ships as an example file.

Steps: `term-index-2026-11-16.steps.csv`.
