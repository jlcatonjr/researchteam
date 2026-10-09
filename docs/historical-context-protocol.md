# Historical Context — Protocol

This is the single authoritative procedure for placing sources in their own time. `CLAUDE.md`, the
interpretation-advisor, the methodology-guide template and the component quality criteria point
here. The procedure lives in one place.

## What it is

The framework already tracks **genealogy**: which thinker or school a concept descends from, with
every lineage arrow sourced or flagged (`interpretation-advisor`, anti-fabrication discipline). This
protocol adds the second half of history, the **setting** of each source:

- **when** it was written (a date or range, with how sure we are);
- **where**, and **for whom** or on what occasion;
- **which text** we are reading (a recension, an edition, a translation; interpolations;
  disputed authorship);
- **how it was received**, when a later reading is part of the argument.

A claim can be well cited and still mislead if it leaves the setting out. "Text X teaches Y" may be
true of one recension, one century or one community, and false of the tradition as a whole.

## The honest ceiling

`WELL-FORMED ≠ VERIFIED`, as in the citation & claim audit. The detector below checks that a
register exists and that every row states a date and a basis. It cannot check that the date is right
or that the cited source says it. Dates and settings are factual claims, and they go through the
claim audit like any other.

## The four rules

### 1. Register the setting of every load-bearing source

Each project's interpretive map (`Projects/<project>/interpretation/interpretive-map.md`) carries a
`## Historical setting` section with one row per source the argument leans on:

```markdown
## Historical setting

| Source | Date | Place | Occasion / audience | Text version | Basis |
|---|---|---|---|---|---|
| *Work* | c. 628–630 | North Africa | monastic readers | critical edition, vol. | (per Author Year, page) |
| *Other work* | c. 500 | Syria? | — | — | [editors' inference — unsourced] |
| *Third work* | unknown | — | — | — | unresolved |
```

- **Date** is never blank. Write a value, a range, `c.`, `before`/`after`, or `unknown`.
- **Basis** is exactly one of `(per <Author Year>, <locator>)`, `[editors' inference — unsourced]`
  or `unresolved`. The rules for genealogy arrows apply: an inference may never anchor a released
  claim, and an `UNVERIFIED` basis from the claim ledger is demoted to an inference.
- A dash (`—`) is allowed in Place, Occasion and Text version when nothing is known. Say so; do not
  guess.

### 2. Guard against anachronism in both directions

| Direction | What goes wrong | Required handling |
|---|---|---|
| **Forward** | A modern view is read into an older source ("the author held view V") | Frame it as an analogy under stated methodological commitments. State the sampling frame and include a "passages that resist this analogy" section. |
| **Backward** | A later category, label or settlement is applied to an earlier source | Use the source's own terms and those of its period. Name the later category as later ("what the later tradition calls …"). |
| **Flattening** | A tradition is treated as one thing across its whole history | Name the period, region or community the claim holds for. |
| **Text version** | The received text is treated as the text as first written | Name the version read. Flag interpolations and disputed authorship where they matter to the claim. |

### 3. Situate every comparison

When a deliverable compares two traditions, texts or practices, it states:

- **which** text, rite or period of each side is meant; and
- **who** first drew the comparison, **when**, and **in what setting**, if the comparison has a
  history of its own.

### 4. Carry the setting into the deliverable

- **Load-bearing claims.** When the truth of a claim depends on period, place or text version, the
  deliverable says which. The interpretive map is scaffolding and is not compiled. The setting the
  reader needs must appear in the deliverable.
- **Inferences.** A setting that rests on `[editors' inference — unsourced]` is marked as such
  wherever it is used.

## Who does what

| Agent | Role under this protocol |
|---|---|
| `@topic-scoping-expert` | The Source Strategy records the setting of each core source, or marks it unknown. |
| `@interpretation-advisor` | Commissions the `## Historical setting` register as part of the Interpretive Map Brief. Maps what key terms meant in each period. Directs the downstream experts. |
| `@literature-review-expert` / `@main-analysis-expert` | Apply rules 2–4 in their components. They do not restate the register. |
| `@primary-producer` | Writes the register and the deliverables, and keeps every basis tag verbatim. |
| `@reference-manager` | Confirms that each work cited as a basis exists. Where the project keeps a catalogue with composition fields (date, place), it drafts them from dating finding aids as `UNVERIFIED`. |
| `@technical-validator` | Puts each register row on the claim ledger. Any row it cannot confirm is marked `UNVERIFIED`. |
| `@quality-auditor` | Flags `Q-CTX`: a claim with no setting where the setting matters, or an anachronism. |
| `@adversarial` | Audits Historical (H) presuppositions, asking whether the evidence comes from the period itself or from a later source projecting back. |

`Q-CTX` and the H class are part of the agentteams templates, so they arrive with
`researchteam update`.

## When it runs

- **At initiate / develop.** The register is commissioned together with the interpretive map.
  Before release, run the detector:
  `scripts/check_historical_context.sh [project]`, or
  `bash scripts/claude_researchteam_bridge.sh history-check [project]`.
- **Pre-compile closeout.** Run it next to the methodology-coverage check and the citation & claim
  audit. A `MISSING-SETTING`, `EMPTY-SETTING` or `SETTING-BAD` line blocks compile unless the project
  has adopted advisory mode on purpose (`HISTORICAL_CONTEXT_ADVISORY=1`) while it backfills.

## The detector

`scripts/check_historical_context.sh` reads the same map path and unit layout as
`check_methodology_coverage.sh` (including brief.json `methodology_coverage`).

| Line | Meaning | Exit effect |
|---|---|---|
| `SETTING-OK` | Register present; every row has a source, a date and a valid basis. Counts sourced / inference / unresolved rows. | passes |
| `NO-MAP` | The project has no interpretive map; this is the coverage gate's concern. | skipped |
| `MISSING-SETTING` | The map has no `## Historical setting` section. | blocks |
| `EMPTY-SETTING` | The section has no table rows. | blocks |
| `SETTING-BAD` | One or more rows lack a source or date, or have a basis outside the three allowed forms. | blocks |

`HISTORICAL_CONTEXT_ADVISORY=1` downgrades a block to exit 0.

## What this protocol does not do

- It does not verify dates. That is the claim audit's job, ending with human resolution where needed.
- It does not ask for a history of everything. Only sources the argument leans on need a row.
- It does not replace genealogy. Lineage arrows stay in the interpretive map's Genealogy section
  under the anti-fabrication discipline.

## Origin

Generalised from the OrthodoxLLM historical-context audit (2026-10-09). A comparative project
(christ-the-eternal-tao, round 3) needed a context rule written into its plan after the fact, because
no agent owned setting. This protocol makes that rule the default.
