# 2-Fold Citation & Claim Audit — Protocol

This is the single authoritative procedure for the doubled citation-and-claim audit. `CLAUDE.md`,
the orchestrator's Project-Specific Notes, the preflight checklist, and the research-report prompt
all point here — the procedure lives in one place.

## What it is

Two audit **dimensions**, run in **two independent rounds**:

- **Dimension A — Citation & bibliography integrity.** Every in-text citation is backed by a real
  bibliography record; **every record carries a source link** (a `url` or `doi` — a direct link, a
  purchase link, or a descriptive URL such as RePEc/WorldCat when no direct link exists), **and that
  link is also embedded in the reference-list entry at the end of the document** (the
  `## References` / `## Works cited` section); every record carries its metadata; URLs are
  well-formed; the `.bib` and each deliverable's reference list do not drift.
- **Dimension B — Claim & interpretation integrity.** Every fact and interpretation is paired with
  the reference(s) cited to justify it; no claim outruns its evidence; no citation is mis-attributed.

"**2-fold**" = the two dimensions. "**occur twice**" = the whole {A, B} audit runs in two rounds,
the second adversarially framed and cross-checked against the first.

## The honest ceiling (read this first — it is binding)

**`WELL-FORMED ≠ RESOLVED`.** No script and no model can *prove* a citation or claim is genuine. A
syntactically valid but fabricated DOI, or a plausible but unsupported paraphrase, passes every
automated check. The two rounds are the **same models over the same repo** — their errors are
**correlated**, so a second pass raises the odds of catching a *non-systematic slip* but adds little
against a *shared blind spot*. Therefore this audit:

- **catches** structural defects deterministically (the detector),
- **surfaces** fabrication-shaped signals (unbacked in-text cites, drift, uncited entries),
- **drives** every unresolved item to an explicit `UNVERIFIED` that **blocks compile** until a
  **human** resolves it out-of-band.

It never emits "proven genuine," and no step may claim the audit certifies non-fabrication. Its job
is maximal *detection* plus honest *escalation*, not proof.

## When it runs

- **Best-effort at initiate / develop.** When a project is scaffolded, or a deliverable is drafted
  or revised, run the mechanical layer (below) and route findings. "Initiated" and "developed" are
  not events the system can detect on its own, so this depends on the operator/agent following the
  workflow — it is *not* a reliable automatic trigger.
- **Primary anchor: pre-compile closeout.** The enforcing checkpoint is **before
  `@output-compiler`** assembles a release. Regardless of whether an initiate/develop prompt fired,
  no project is compiled until the doubled audit has run and no `CU`/`FU`/`AE` finding is unresolved
  (orchestrator Constitutional **Rule 12**; `@conflict-auditor` Rule 6).
- **Automatic surface: CI advisory scan** (`CITATION_INTEGRITY_ADVISORY=1`) reports the mechanical
  layer on every sync run — visibility, not a gate.

## Layer 1 — the mechanical detector (deterministic)

`scripts/check_citation_integrity.sh [project]` (also `bash scripts/claude_researchteam_bridge.sh
citation-audit [project]`) checks the machine-certain subset and code-tags every line:

| Class | Codes | Meaning | Exit effect |
|-------|-------|---------|-------------|
| `DEFECT` | `[DUP]` `[META]` `[LINK]` `[REFURL]` | duplicate key; entry with no title, or no author **and** no editor; entry with **no source link** (no `url` and no `doi`); a **reference-list entry that embeds no URL** (the link in the `.bib` must also appear in the end-of-document entry) | blocks (exit 1); `CITATION_INTEGRITY_ADVISORY=1` downgrades to exit 0 |
| `NEEDS-REVIEW` | `[CU]` `[RM]` `[PE]` `[META]` `[URL]` `[DOI]` `[STRUCT]` | in-text cite with no backing; `## References` entry absent from `.bib`; uncited entry; missing year; malformed-looking locator; missing reference list | advisory only — never changes the exit code |

The detector is a **stateless stdout scanner**: it does not write `conflict-log.csv`. Its code tags
map onto the `@conflict-auditor` taxonomy so consolidation is mechanical — `[CU]→CU`, `[RM]→RM`,
`[PE]→PE`, and a `[CU]`/`[RM]` that a human confirms as a real unsupported claim escalates to `FU`
or `AE`.

## Layer 2 — the doubled semantic audit (agents)

**Round 1 — baseline.**
1. `@reference-manager` runs Dimension A against `references/bibliography.bib` (key resolution,
   metadata completeness, resolver check where network is available, deduplication).
2. `@technical-validator` runs Dimension B (claim ledger; `CH-08` every claim paired with explicit
   evidence; `CH-09` insufficient → `UNVERIFIED`; `CH-10` contradicted → escalate).
3. `@conflict-auditor` consolidates both into `CU/FU/AE/RM/RX/PE` findings and logs them. Any
   unresolved `CU`/`FU`/`AE` **blocks** publication/compilation/acceptance (Rule 12 / Rule 6).

**Round 2 — independent adversarial re-audit.**
4. `@adversarial` frames the premise "assume a citation or claim in this deliverable **is**
   fabricated — find it."
5. `@reference-manager` and `@technical-validator` re-audit **from the deliverable alone**, without
   reading Round 1's PASS conclusions.
6. `@conflict-auditor` **diffs Round 2 against Round 1.** Convergence-clean is the confidence bar
   (subject to the ceiling above); any divergence is escalated and unresolved until reconciled.

**Output.** A per-project `NN-adversarial-conflict-audit.md` ledger (the format the existing projects
already use: located finding → challenge → remediation → status), plus the explicit list of residual
`UNVERIFIED` items for human resolution.

This promotes what `references/plans/adversarial-conflict-audit-labor-matching.plan.md` did once, by
hand, into the standing procedure.

## Optional — per-commit local trigger (opt-in)

There is deliberately **no** default git hook (`.git/hooks` is not version-controlled and would not
propagate). To get an advisory check on every commit that touches project content, add this to your
own `.git/hooks/pre-commit` (it never blocks the commit):

```sh
CITATION_INTEGRITY_ADVISORY=1 bash scripts/check_citation_integrity.sh || true
```

## What this protocol does NOT do

- It does not prove non-fabrication (ceiling above).
- It does not block on heuristic/fuzzy signals — only on duplicate keys and entries missing a title
  or an author/editor. Everything else is advisory.
- It does not add a numbered Workflow inside an `AGENTTEAMS` fence, a new Constitutional Rule, or a
  blocking pre-commit hook. Routing lives in USER-EDITABLE notes and this doc; the gate is Rule 12.
