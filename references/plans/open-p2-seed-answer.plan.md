# P2: the local seed-answer copy (revised)

**State.** The local copy is AI-generated text the operator pasted (C-4 data, 3,009 bytes) in ignored
`tmp/by-week/2026-W42/`. The canonical copy is in the private `jlcatonjr/security` repository
(`Projects/ai-cryptography-threats/sources/seed-answer.data.md`), as the archived bootstrap plan said it would be.
None of its content is ever copied into public output.

**Match rule, fixed before comparing.** The two copies match if they are byte-identical, or if the canonical
copy differs only by lines added before the local copy's first line (a provenance header).

**Steps**
1. Read the canonical copy through the GitHub API and compare it with the local copy, without writing anything.
2. Pointer. Add one line to `references/plans/archive/README.md`, saying that the seed answer is kept as C-4
   data in the private security repository. The archived plan itself is not edited, so that P1's check still
   holds.
3. If the copies match: `@security` and `@cleanup` clearance, then the operator's S-4 confirmation in the
   metaplan's Phase 2 (keeping is the default). Then delete by path. If they differ: keep the local copy and
   report it.

**Outcome (2026-11-14).** The copies differ in one provenance-header line; the pasted bodies are identical.
Under the match rule fixed in advance, that is "differ", so the local copy is **kept**. The pointer line was added
to `archive/README.md`. No private content was copied out.
