# Survey toolkit: contract

**Status: version 1, frozen 2026-11-23.** Agreed with the first integrating project after two checks and
a line-by-line comparison with its reference implementation (as revision 2 of this contract,
2026-11-19), then frozen once
that project had its S0 and S5 gates signed and had run a stage that writes evidence rows (operator
ruling, 2026-11-21: enumeration alone was not enough). What the freeze changed is listed in section 12.
From here a change to a shape, rule or command is a new version of this contract, not an edit. No survey
tool is implemented in researchteam yet; the bibliography explorer's contract 1.1 (section 10, step 2)
is, since 2026-11-20. The contract ships in researchteam 1.3.0 (operator ruling, 2026-11-19); the tools are
planned for the minor release after it (operator ruling, 2026-11-23).

A *position survey* answers a question of the form "what did the people in this frame hold about X, and
on what evidence". The toolkit is the reusable part of running one: a study specification, the row
shapes, the checks, the gates and the commands. It knows nothing about any topic. It follows a reference
implementation in a derived repository, whose project-specific parts stay there.

Sections: 1 rules; 2 what the toolkit owns; 3 the study specification; 4 row files; 5 plug-ins; 6 gates
and sign-offs; 7 commands and CI; 8 agents; 9 relation to the bibliography explorer; 10 delivery and
order of work; 11 open points; 12 what the freeze changed. Bucket tables are 4.8.

## 1. Rules that hold everywhere

1. **The specification is the single source.** Every level, cut, tier, rule and file a stage uses is
   named in the study's `study.json`. No tool carries a topic constant.
2. **Fail closed.** A tool that finds a violation exits non-zero and writes nothing. A stage whose
   blocking gate is not cleared refuses to run (section 6).
3. **Nothing is inferred.** No tool matches names to link identities, guesses whether a statement is in
   a person's own words, or fills a missing code. A tool may list *candidates*; a link, a basis and a
   code are always written by a named agent or person and are checked, not derived.
4. **No self-attestation.** An agent never signs a gate, and no tool writes a sign-off. A gate is cleared
   only by the operator's signature over the hash of a manifest of every covered file. Any later edit to
   a covered file un-clears the gate.
5. **Deterministic.** The same inputs give byte-identical outputs. Outputs carry no timestamp. A log row
   carries the date its author gives it; a tool does not read the clock to fill one in. Two exceptions: a
   fetch receipt (4.4), whose fetch time is a fact about the fetch, and the date in a sign-off request,
   which is a field of `agentteams`.
6. **Paths stay in the repository.** A path in the specification is relative to the study's folder, or
   to the repository root when it starts with `repo:`. An absolute path, a `..` segment, or a path that
   resolves outside the repository through a link is an error, in a draft as much as in an active study.
   Two paths are the same file when they resolve to the same place, however each is written.
7. **Standard library only.** The tools import nothing outside the Python standard library. Verifying a
   signature needs `agentteams`, which is optional: without it a gate's state is `UNAVAILABLE`, and a
   blocking gate in that state refuses like an uncleared one.
8. **No project data upstream.** researchteam holds the toolkit, an invented example study and tests on
   invented data. A project's specification, codebooks, tables, plug-ins and rows stay in the project.
9. **What a clean run means.** The study is well-formed, internally consistent and, where gates are
   cleared, unchanged since the operator signed. It does not mean that any quotation is accurate beyond
   the locus it was re-found at, that a code is right, or that the frame is complete. A re-found
   quotation is a string that occurs at its locus, and no more than that (5.4).
10. **Folded text.** Where this contract says text is *folded*, it means: decomposed (NFD) with combining
   marks removed, lower-cased, soft hyphens removed, a hyphen followed by white space removed together
   with that white space, and each remaining run of white space made one space, with none at either end.
   *Folded without spaces* removes the white space altogether.

## 2. What the toolkit owns, and what a project owns

| The toolkit (researchteam) | The project |
|---|---|
| The specification's shape and its checks | `study.json` and every file it names |
| Row shapes and row checks (section 4) | The rows |
| The table bucketer and the period rule (4.8) | Bucket tables; any plug-in bucketer |
| Identity candidates, registry build, override handling | The identity source; every link or merge decision |
| Quote re-finding, fetch receipts | The text store and its layout (declared in the specification) |
| Agreement statistics, fail-closed finalising, rollup, the frame | Codebooks; the two coding passes; adjudication |
| Enumeration log and the stopping rule | Query plans, seeds, the rounds themselves |
| Gate manifests, gate status, stage refusal | What each gate covers; the operator's signatures |
| The plug-in interfaces (section 5) | The plug-ins, including any vantage module and vocabulary rule |
| The frame, its passage list, and the projection to the explorer's tables (4.7, section 9) | The results page |

The analysis engine and the results page are a separate workstream in another repository. The toolkit
ends with finalised codes, a rollup, the frame an analysis reads (4.7) and the explorer's input tables
(section 9); `analysis` in the specification is carried, checked only for shape, and covered by gate S6.

## 3. The study specification (`study.json`, version 1)

One JSON file per study, at `Projects/<project>/study.json` unless the project says otherwise. Unknown
keys are an error at every level. `schema_version` is `"1"` or `"0"`, and the two are checked identically.
`"0"` is what a study written before the freeze carries; accepting it means the freeze alone does not
un-clear that study's signed gates. A manifest carries whichever the specification says. Anything that
writes a new specification writes `"1"`. A study is a draft only by its `status`; a file's name never makes it
one. The validator is researchteam's own, written against the standard
library; it is the authority. A JSON Schema file (2020-12) is published beside it as a description for
editors. A shared set of valid and invalid specifications is kept in the tests so the two can be compared
wherever a JSON Schema library is installed; researchteam's own CI does not install one.

Fields marked `?` are optional. `slug` is `^[a-z0-9][a-z0-9_-]*$`. `path` is a string under rule 1.6.

```
{
  "schema_version": "1",                               // or "0", read identically
  "id": slug, "title": string, "question": string,
  "status": "draft" | "active" | "legacy",
  "vantage"?: { "module": Plugin | null, "guide"?: path, "inclusion"?: string | null },     // 5.2
  "vocabulary"?: { "forbidden": path, "exempt_columns"?: [string] },                        // 5.3
  "corpus"?: { "text": path, "works"?: path },                                              // 5.4
  "identity": { "registry": path, "overrides": path, "stop_words"?: path },                 // 4.4
  "unit": {
    "kind": "passage" | "work" | "author",             // passages and works roll up to their author
    "attribution"?: { "file": path, "statuses": [string], "counted_statuses": [string] },
    "passage_attributes"?: [ LevelSet ],
    "rollup_by"?: [string],
    "rollup_types"?: string,                           // a passage attribute key; 4.2
    "exclude_from_rollup"?: { "<passage attribute key>": [string] },                         // 4.2
    "collective"?: { "kinds": [string], "analysis": "apart" | "with-authors" }
  },
  "enumerations": [ {
    "id": slug, "label": string,
    "window": { "from": int | null, "to": int | null },
    "seeds"?: [string], "query_plan"?: path, "log": path,
    "stopping_rule": {
      "kind": "saturation" | "exhaustive-corpus" | "closed-list" | "legacy-unrecorded",
      "rounds_without_new"?: int,                      // >= 1
      "min_new_share"?: number,                        // 0..1
      "note"?: string }
  } ],
  "evidence": {
    "file": path,
    "format": "survey-evidence-0" | "plugin",          // 4.1; "plugin" reads through 5.1
    "reader"?: Plugin,                                 // required when format is "plugin"
    "tiers": [string],                                 // every tier a row may carry
    "counted_tiers": [string],                         // a subset of tiers
    "not_established_tier": string,                    // one of tiers, not counted
    "receipts"?: path,                                 // folder of fetch receipts, 4.4
    "legacy_exceptions"?: path,                        // legacy studies only; 4.1
    "attribute_kinds"?: [string]
  },
  "outcomes": [ {
    "key": slug, "label": string,
    "source": { "kind": "evidence-attribute", "attribute": string }
            | { "kind": "codes", "codes_file": path, "adjudications": path },
    "codebook"?: path,
    "scale": "nominal" | "ordinal",
    "levels": [ Level ],                               // at least 2
    "na_codes"?: [string],
    "missing"?: string,                                // default "NE"
    "merges"?: { string: string },
    "rollup": "single-code" | "mixed-if-conflict" | "max-order" | "any-present" | "none",
    "present_code"?: string                            // required when rollup is "any-present"
  } ],
  "attributes": [ {
    "key": slug, "label": string,
    "kind": "categorical" | "flags" | "period",
    "source_attributes"?: [string],
    "bucketer": Bucketer,
    "levels"?: [string], "flags"?: [string],
    "missing"?: string                                 // default "NE"
  } ],
  "periods": {
    "basis": [ "work_date" | "life_dates" ],
    "cuts": [int],                                     // ascending
    "labels": [string],                                // one more than cuts
    "strata"?: { "<period number>": string }
  },
  "frame_rules": {
    "exclude": [ { "rule": "institutions" | "not-on-question" | "unit-ids" | "id-contains",
                    "values"?: [string], "reason": string } ],       // may be empty
    "change_log": path,
    "post_steps"?: [path]                              // 4.5
  },
  "analysis"?: object,                                 // carried; shape owned by the analysis engine;
                                                       // it may name files by path (see below)
  "signoffs": {
    "ledger": string,                                  // 6.2
    "gates": { "S0" | "S5" | "S6" | "S8": Gate }
  }
}

Level    = { "code": string, "label": string, "order"?: int }
LevelSet = { "key": slug, "label": string, "levels": [ Level ] }
Bucketer = { "kind": "table", "table": path, "match"?: "first" | "all", "fallback"?: string }
         | { "kind": "period" }
         | { "kind": "plugin", "plugin": Plugin, "fallback"?: string }
Plugin   = { "file": path, "attr": string, "version": string }                              // 5.1
Gate     = { "covers": [path], "enforce": "blocking" | "build-only",
             "mode": "prospective" | "retroactive" }
```

**Bounds.** There is at least one enumeration, outcome, attribute and cut, and at least two period
labels. A level set has at least one level, and each `exclude_from_rollup` list at least one value.
`title`, `question`, every path and a plug-in's `version` are not empty. A plug-in's `attr` matches
`^[A-Za-z_][A-Za-z0-9_]*$`. A bucketer carries only the fields of its own kind.

**Checks beyond shape.** Each is an error:

- a key used twice among the outcomes and attributes together; a level code used twice within an outcome;
- `rollup: "max-order"` without `scale: "ordinal"`, or with a level that has no `order`;
- a merge whose source is not a declared level code or NA code (a target may be a new label);
- `cuts` not strictly ascending, or `labels` not one longer than `cuts`; a `strata` key that is not a period
  number from 1 to the number of labels;
- a passage or work study with no outcome whose source is `codes`;
- `counted_tiers` not a subset of `tiers`; `not_established_tier` not in `tiers`, or counted;
- `rollup: "any-present"` without a `present_code`, or with one that is not a level code of the outcome;
  a `present_code` on any other rollup;
- an `exclude_from_rollup` key that is not a `passage_attributes` key, or a value that is not one of its
  level codes; a level code `mixed` in any outcome;
- `rollup: "any-present"` on an ordinal outcome with a level that has no `order`;
- a `rollup_types`, or a `rollup_by` entry, that is not a `passage_attributes` key;
- more than one attribute of kind `period`; an attribute of kind `period` whose bucketer is not of kind
  `period`, or the reverse;
- two frame columns with the same name (4.7). The frame's columns are generated from the keys, so this is
  for example an attribute or outcome named `unit_id`, `author` or `unit_kind`, an outcome named like the
  period's `<key>_num`, a key equal to a `rollup_by` key, or a flag column `<key>_<flag>` or
  `<key>_<missing>` equal to another column;
- `match: "all"` on a bucketer of an attribute that is not of kind `flags`; `match: "first"` or a
  `fallback` on the bucketer of a flags attribute (4.8);
- within an outcome, a level code, an NA code and the `missing` value that are not all different, or any
  of them equal to `mixed`; an attribute whose `missing` value is one of its levels or flags;
- a `|` in a level code of a `rollup_by` level set (4.7);
- in a passage or work study, a `frame_rules.exclude` rule other than `not-on-question`: version 1 does
  not define the other rules over cells (4.7);
- a passage or work study without `unit.attribution`;
- a `saturation` stopping rule without both `rounds_without_new` and `min_new_share`; a
  `legacy-unrecorded` stopping rule in a study whose `status` is not `legacy`;
- a referenced input file that does not exist, unless `status` is `draft`. These may be absent, because
  a stage writes them or they start empty: `log`, `change_log`, `identity.registry`,
  `identity.overrides`, `evidence.receipts`, an outcome's `adjudications`;
- a plug-in (a reader, a bucketer or the vantage module), a bucket table (4.8), the `vocabulary.forbidden`
  file or the `identity.stop_words` file that is not covered by gate S0 (5.1, 5.3). Coverage is judged on resolved
  paths (rule 1.6);
- evidence that cites a fetch receipt when `evidence.receipts` is not declared;
- `evidence.legacy_exceptions` in a study whose `status` is not `legacy`, or naming a file that no gate
  covers;
- a `post_steps` file that no gate covers (4.5);
- a gate that covers no file, or a `covers` path that does not exist, unless `status` is `draft`.

**Changes from the first version of the reference implementation**, each for the reason given. The
reference has since taken them.

| Field | First reference | Here | Why |
|---|---|---|---|
| `evidence.format` | `author-attributions-v1`, `explorer-evidence-1.0` | `survey-evidence-0`, `plugin` | The first is one project's legacy file, read through a reader plug-in that stays in that project. The second name claimed the explorer's 13 columns for a file that has 18. |
| `bucketer.plugin` | `"module.path:attr"` | `{file, attr, version}` | A file path can be confined to the repository, hashed and covered by a gate; an import path cannot. |
| `vocabulary` | a constant in the tools | a file the specification names | The rule is a project's, not the toolkit's. |
| `corpus` | a fixed layout | declared paths | The text store's layout is a project's. |
| `analysis` | fixed fields | an opaque object | Its shape belongs to the analysis engine, which is proposing to replace it. |
| `signoffs.ledger` | the team's decisions log | a per-study log (6.2) | Operator ruling, 2026-11-19. |
| `vantage.module` | a string | a `Plugin` or null | It must be a file gate S0 can cover. |
| `vocabulary.exempt_columns` | every column checked | declarable, default `["quote"]` | Which columns the rule spares is a project's rule. |
| `evidence.tiers`, `not_established_tier` | constants in the row checker | declared | Rule 1.1. |
| `unit.exclude_from_rollup` | one value hard-coded | declared | Rule 1.1. |
| `unit.aggregate_to` | `"author"`, required for passage and work studies | removed | It had one allowed value. Collective bodies are authors of a declared kind, not another aggregate. |
| `outcomes[].held_out` | required, always `true` | removed | A field with one value says nothing. The rule it stood for is stated below. |
| `outcomes[].present_code` | a word fixed in the tool | declared | Rule 1.1. |
| `evidence.tier_map` | a mapping from a project's own states to tiers | removed | No tool read it; rows carry declared tiers directly. |
| `identity`, `evidence.receipts` | fixed file locations | declared paths | Rule 1.1. |
| `frame_rules.change_log` | optional | required | A frame change, or an exclusion a vantage module causes, must have somewhere to be recorded. |

**Outcomes are never analysis inputs.** An outcome is what the study asks about; an attribute is the
background it is read against. The specification keeps them in separate lists, and an analysis must not
use an outcome to form its groups or distances: a specification's `analysis` that names an outcome key
among its grouping attributes is to be refused by the engine that runs it.

`rollup`, `bucketer` and `frame_rules.exclude` are required, as in the reference, so that no tool supplies
a default silently.

**The analysis-engine pin may live in a file of its own.** Every manifest lists the specification first
(6.1), so anything written in `study.json` is covered by every gate, and a new engine release recorded
there would un-clear S0 and S5 although nothing they clear had changed. A study may therefore keep the
pin (which engine, at which commit and release) in a separate file that `analysis` names by path and
that only S6 covers. A study may also keep it inside `analysis`; then every gate moves with it. The
toolkit reads neither: the pin's fields are the analysis engine's (operator ruling, 2026-11-22).
Because `analysis` is opaque, no toolkit check can confirm that such a file exists or that S6 covers it.
That is checked by whoever prepares S6 and by the operator who signs it: a pin file that S6's `covers`
does not list is not cleared by anything (open point 5).

**The period attribute.** A study has at most one attribute of kind `period`. Its `key` names the frame's
two period columns, `<key>` and `<key>_num` (4.7); a study without one gets `period` and `period_num`.
An analysis that stratifies by period names that column.

## 4. Row files

All are CSV, UTF-8, with exactly the columns listed, in this order. A missing or extra column is an
error. An empty cell means "not given"; a tool never treats it as a value.

### 4.1 Evidence (`survey-evidence-0`)

`id, person_id, attribute_kind, value, tier, source_id, citation, locator, quote, url, access, via,
audit, basis, reporter, unit_id, note, downgraded_from`

The first thirteen columns are the bibliography explorer's required `evidence.csv` columns, with the
same meanings. The last five are the survey's; the explorer's contract 1.1 also carries `basis`,
`reporter` and `note` as optional columns (section 9):

| Column | Meaning |
|---|---|
| `basis` | `own` (the person's own words) or `reported` (someone else's account of them) |
| `reporter` | who reports, when `basis` is `reported` |
| `unit_id` | in a passage or work study, the passage or work the row belongs to; or, for a row about the person and not about one passage (life dates, language, office), the row's own `person_id` |
| `note` | free text; on a not-established row, what was tried |
| `downgraded_from` | the value and tier the row had before an audit downgraded it |

Errors:

- columns that are not exactly the eighteen, in order;
- a row in a counted tier without a `quote`, or with neither `citation` nor `source_id`;
- a row in a counted tier whose `basis` is not `own` or `reported`; `reported` without a `reporter`; a
  `reporter` on an `own` row;
- a row in the not-established tier (`evidence.not_established_tier`) with a `quote`, or without a
  `note`. Not-established is a tier of the row; its `value` is free text and is not an outcome code;
- a `tier` not in `evidence.tiers`; an `attribute_kind` the specification does not declare;
- a `unit_id` in an author study, or none in a passage or work study;
- in a passage or work study, a `unit_id` that is neither a unit of the attribution file nor the row's
  own `person_id`; or a row on an attribution unit whose `person_id` is not that unit's attributed
  author;
- an empty or duplicate `id`; a `person_id` the registry does not hold; a `|` in a `person_id` or a
  `unit_id` (4.7);
- text matching the project's forbidden-vocabulary file in any column not listed in
  `vocabulary.exempt_columns` (5.3).

The row checks apply to the whole evidence file whenever it is checked, not only to rows being added, and
none of them is skipped because an optional declaration or file is absent: an `attribute_kind` is checked
against the outcomes and attributes that use it, and a missing registry is itself an error.

**Person-level rows in a passage or work study.** Such a study needs a `unit_id` on every row, and some
rows are about the person, not about one passage. Those rows carry the person's own id as `unit_id`. It
matches no unit of the attribution file, so a coding packet never contains the row, and the frame reads
it as the person's own attribute (4.7).

**Adding rows.** Rows are written as a batch file with the same columns and merged by the row tool. A
batch is checked in full, together with the file it joins, and nothing is appended unless every row
passes. A legacy exception never covers a batch row. Merging into a `plugin` format is the project's own
write path and is refused. A merge also renews the registry's record, and is refused where it could not
(4.4).

**Rule ids.** Each evidence check has an id, which reports use and the exceptions file below is keyed on:

| Rule id | Breach |
|---|---|
| `columns` | the columns are not exactly the eighteen, in order |
| `id-empty` | an empty `id` |
| `id-duplicate` | a repeated `id` |
| `attribute-kind` | an `attribute_kind` that is not declared |
| `person-unknown` | a `person_id` the registry does not hold |
| `unit-id` | a `unit_id` in an author study, or none in a passage or work study |
| `unit-unknown` | in a passage or work study, a `unit_id` that is neither an attribution unit nor the row's `person_id` |
| `unit-person` | a row on an attribution unit whose `person_id` is not the unit's attributed author |
| `id-separator` | a `\|` in a `person_id` or a `unit_id` |
| `tier-unknown` | a `tier` that is not declared |
| `counted-quote` | a counted row without a `quote` |
| `counted-citation` | a counted row with neither `citation` nor `source_id` |
| `counted-basis` | a counted row whose `basis` is not `own` or `reported` |
| `reported-reporter` | a `reported` row without a `reporter` |
| `own-reporter` | an `own` row that names a `reporter` |
| `ne-quote` | a not-established row with a `quote` |
| `ne-note` | a not-established row without a `note` |
| `vocabulary` | forbidden vocabulary in a column that is not exempt |

**Rows that predate the rules, in a legacy study.** A `legacy` study may name a file of exceptions,
`evidence.legacy_exceptions`, with the columns `id, rule`: one line for each existing row and each rule
that row breaks. Rewriting such rows would change the evidence of a study that is already closed.

- A row that breaks a rule fails the check unless that row and that rule are listed. A listed breach is
  reported, with counts by rule, and does not fail.
- `columns`, `id-empty` and `id-duplicate` cannot be listed: without sound columns and ids no row can be
  named.
- Nothing else is excused. A row that is not listed, and so every row added later, must pass in full; a
  listed row that comes to break a further rule fails on that rule.
- A listed exception that no longer applies, because the row was removed or now passes, is an error:
  the file is corrected, so it never claims more than is true.
- The file is the project's, is covered by a gate, and is allowed only when `status` is `legacy`. The
  tool can write a first version from the current breaches for a person to review; it never adds to an
  existing one.
- Every output that rests on the evidence file records how many exceptions it was read with (4.6).

### 4.2 Codes

`unit_id, person_id, outcome, code, pass, coder, basis, reporter, evidence_ids, level, note`

`pass` is `A`, `B` or `final`. `code` is one of the outcome's level codes, its NA codes, or its `missing`
value. `evidence_ids` is a `;`-separated list of evidence ids.

Errors:

- an outcome the specification does not declare with source `codes`; a code outside the allowed set;
- a code other than `missing` without `evidence_ids` or without a `basis`; `reported` without a
  `reporter`;
- an evidence id that does not exist, or that belongs to another person. In a passage or work study,
  belonging is read through the attribution file: a unit's evidence belongs to the unit's attributed
  author;
- two rows for the same unit, outcome and pass;
- a `final` row for a unit that lacks an `A` or a `B` row, unless it comes from an adjudication whose
  `note` begins `missing pass: A, ` or `missing pass: B, ` followed by the reason the pass could not be
  made.

**Adjudications** are a row file of their own, written by the adjudicator:

`unit_id, outcome, code, coder, basis, reporter, evidence_ids, note`

The file is the one the outcome's `source.adjudications` names. Its rows are checked like codes rows, and
`coder` and `note` are required. An adjudication for a unit and outcome on which passes A and B agree is
an error: an agreed code is not changed. Where a pass is missing, the adjudication's `note` begins
`missing pass: A, ` or `missing pass: B, `, followed by the reason.

**Finalising is fail-closed.** Where passes A and B agree, the final row is theirs. Where they disagree,
or where one pass is missing, the final row is the adjudication's, with the adjudication's own coder,
basis, evidence and note. Without one, no final row is written; the tool lists the units and exits non-zero. A single
pass never becomes final on its own. Agreement is reported as raw agreement, Cohen's κ and Gwet's AC1, per outcome, with the number of
units each rests on.

**Rollup** takes passage or work codes to their author:

- only `final` rows count, and only for units whose attribution status is in `counted_statuses`;
- a unit whose passage-attribute value is listed in `unit.exclude_from_rollup` is left out;
- NA codes and the `missing` value are skipped. An author whose remaining codes are all skipped gets
  `missing`. The frame is stricter here and keeps "not applicable" apart from "not established" (4.7);
- an author all of whose units were left out by status or exclusion is not in the rollup. The tool
  reports how many authors that is;
- an outcome whose source is an evidence attribute does not appear in the rollup;
- `single-code`: the one code all remaining units share; more than one is an error;
- `mixed-if-conflict`: the shared code, or the reserved code `mixed` where units differ;
- `max-order`: the code with the highest `order`;
- `any-present`: the outcome's `present_code` if any remaining unit has it. Otherwise, for an ordinal
  outcome, the remaining code with the lowest `order`; for a nominal one, the remaining code declared
  first in `levels`;
- `none`: the outcome does not appear in the rollup;
- results are split by each key in `unit.rollup_by`;
- where `unit.rollup_types` names a passage attribute, the rollup reports beside each outcome the values
  of that attribute among the units behind it (`<outcome>__types`);
- a collective author keeps its `author_kind`.

### 4.3 Attribution (passage and work studies)

`unit_id, person_id, author_kind, work, locator, status` followed by one column per key in
`unit.passage_attributes`, then `basis, note`.

`status` is one of `unit.attribution.statuses`. Only rows whose status is in `counted_statuses` enter a
rollup. `author_kind` is `person` or one of `unit.collective.kinds`; anything else is an error. The
attribution file is checked like any other row file, header included. Each of these is an error, and
none can be listed as a legacy exception, which covers evidence rows only:

- a `unit_id` that is empty, repeated, or equal to a `person_id` the registry holds: that would make a
  passage indistinguishable from a person-level evidence row (4.1);
- a passage-attribute cell that is empty or is not one of the attribute's level codes;
- one `person_id` with more than one `author_kind`;
- a `|` in a `unit_id` or a `person_id`.

The attribution file is written before any evidence row exists, and the registry takes its persons from
it (4.4).

### 4.4 Logs and working files

**Enumeration log** (`enumerations[].log`; CSV, every cell quoted), one row per round:

`enumeration, round, date, method, queries, candidates, new, new_share, new_ids, note`

`round`, `candidates` and `new` are integers; `new_share` is between 0 and 1, to four decimals; `new_ids`
is a `;`-separated list. Each enumeration writes the file its own `log` names. The stopping rule is
computed from these rows only: a study cannot be declared saturated by assertion. A round with no
candidates is refused and not logged: it found nothing, so it cannot count towards a stopping rule.

| `stopping_rule.kind` | Met when |
|---|---|
| `saturation` | each of the last `rounds_without_new` rounds has a `new_share` no greater than `min_new_share`. Both fields are required; there is no default |
| `exhaustive-corpus` | one round is recorded that ran the whole query plan over the corpus |
| `closed-list` | one round is recorded that went through the whole list |
| `legacy-unrecorded` | always, and it is allowed only in a `legacy` study: it records that no log was kept |

**Frame-change log** (`frame_rules.change_log`; JSON Lines), one entry per change to the frame:

```
{ "id": string, "date": string, "reason": string, "results_seen": bool,
  "frame_sha256": string, "n_units": int,
  "added": [string], "removed": [string], "units": [string] }
```

The log is the file `frame_rules.change_log` names. A frame's units are its `unit_id` values in a passage
or work study and its `person_id` values in an author study. In a passage or work study the frame has
one row per cell and its `unit_id` is the cell's id (4.7), so the log records cells, not passages.
`frame_sha256` is the hash of the frame file as it stands after the last post-step (4.5), computed as a
manifest computes a text file's (6.1). The first entry lists every unit as added.
`id` is what a report cites. `results_seen` records whether any coded result had been seen when the change
was made, and is shown wherever the change is reported. The check fails when the current frame's hash
differs from the last entry's: a frame cannot change without an entry.

**Fetch receipt** (one JSON file per receipt, `<evidence.receipts>/<receipt id>.json`):

`url, quote, fetched_at, quote_fold_sha256, status, final_url, content_type, sha256, found, context,
reason, wayback, receipt_id`

`receipt_id` is the first 24 hex characters of the SHA-256 of the URL, a line feed and the quote folded
without spaces (rule 1.10). `context` is at most about 100 characters each side of the quote, with
whitespace collapsed. `sha256`, `context` and `wayback` are absent when the fetch failed; `context` is
absent for a response that is not text; `wayback` is absent when no archive copy was asked for. The fetched
page itself is cached only in a folder the repository ignores, and is never committed.

**Identity files:**

- the overrides file (`identity.overrides`): `alias_id, target_id, decision, decided_by, reason`. Every
  column is required in every row. `decision` is one of:

  | `decision` | Means | `target_id` |
  |---|---|---|
  | `link` | the project's person is the identity-source person | an id in the identity source; it may equal `alias_id` |
  | `merge` | two of the project's ids are one person | another id of the project |
  | `distinct` | reviewed, and they are different people | the other id, from either side |

  A `distinct` row settles that one pair and no other: a candidate that appears later for the same alias
  is undecided until it has a row of its own. An `alias_id` may have several `distinct` rows but at most
  one `link` or `merge`; a second is an error, and so is a `distinct` row for a pair that is also linked
  or merged. A `merge` or `distinct` row whose `target_id` equals its `alias_id` is an error, and so is the
  same pair and decision given twice; a pair is the same whichever id is written first. The decision is always written, never read off which side `target_id` belongs to. **The
  registry links and merges only from this file**, and a candidate counts as decided only when a row
  names that pair.
- the registry (`identity.registry`, written by the registry tool): `person_id, display_name, identity_id, merged_from`. `identity_id` is the id in the
  identity source.
  - **Where its persons come from.** The evidence file and, in a passage or work study, the attribution
    file. A study can therefore build its registry before its first evidence row, which it must, because
    a row whose person the registry does not hold is refused (4.1). The attribution file is then one of
    the registry's recorded inputs (4.6).
  - **Names.** `display_name` is, in this order: the `display_name` of the identity the person is linked
    to; a name the evidence reader supplies (a `plugin` format may carry one); the `person_id` itself.
  - **After an evidence merge.** The evidence file is a recorded input of the registry, so appending rows
    would leave the registry "not built" (4.6) although its rows had not changed. A merge therefore also
    renews the registry's record, in this way. It refuses unless the registry is built. Before writing
    anything it works out the merged evidence file and the registry that a build over it would give. If
    that registry's rows differ from the present ones (because the overrides, the attribution file or the
    identity source changed since the last build, whatever the batch holds), it stops, writes nothing,
    and says that the registry must be built first. Otherwise it writes the evidence file and then the
    registry's new provenance record, last, so that an interrupted run leaves the registry not built and
    never wrongly current.
- **Candidates.** The registry tool lists possible matches between the project's persons and the identity
  source, each with its kind: `same-id` (the two ids are equal), `exact` (the folded names are equal) or
  `similar` (the names share tokens). A candidate is never a link, whatever its kind: two sources can
  give the same id to different people. The tool may write proposed override rows to a separate file for
  a person to review; it never writes the overrides file.
- `identity.stop_words` names a text file of words left out when names are compared, one per line. It is
  the project's. Without it no word is left out.

### 4.5 Frame post-steps

`frame_rules.post_steps` lists scripts of the project's, run in the order given after the frame is
written. A post-step adds columns to the frame and does nothing else.

- The frame build runs each step. Every later check and stage treats the frame as it stands after the
  last step.
- A step whose output has different units from its input, puts them in a different order, or changes any
  column that was already there, is refused: the build stops and the frame is not written.
- A step is deterministic and follows the plug-in rules of 5.1 on network and clock.
- Running a step runs the project's code, so each step file must be covered by a gate (S6 in the
  reference implementation). While that gate is blocking and not cleared, the frame build refuses to run
  the step.

### 4.6 What every output records

Several rules above say an output "records" something: a gate's state and mode, a plug-in's version, the
number of legacy exceptions. They are all met in one place. Every file a tool writes for a later stage or
a reader has a **provenance record**:

```
{ "output": path, "tool": string, "study": slug, "schema_version": string,
  "inputs": [ { "path": path, "sha256": string } ],
  "gates": { "<gate>": { "state": string, "mode": string, "enforce": string,
                         "manifest_sha256"?: string } },
  "plugins": [ { "file": path, "attr": string, "version": string, "sha256": string } ],
  "legacy_exceptions": int }
```

- A JSON output carries it as its top-level `provenance` field. Any other output (a CSV, a report) has it
  in a file beside it, named as the output with `.provenance.json` added, written in the same run.
- `inputs` lists the files the tool actually read, the specification among them, each as it was read. A
  plug-in file is listed under `plugins` only.
- The record holds no hash of the output it describes: a record inside a file cannot hash that file.
- An output whose record is missing, or whose `inputs` or `plugins` no longer match the files, is treated
  by the next stage as not built, and the stage refuses. Running the earlier stage again writes a new
  record. In a `draft` study the mismatch is reported and the stage runs.
- `gates` lists each gate the stage depends on. A gate the specification does not declare has the state
  `NOT DECLARED`. `plugins` lists each plug-in that was loaded; `legacy_exceptions` is the number the
  evidence file was read with, 0 when there is none.
- It is written as canonical JSON, like a manifest, and carries no date.
- A message on the screen is not a record. Nothing is added to a CSV's own columns for this.

### 4.7 The frame (passage and work studies)

The frame is the table an analysis reads: one row per cell, with its background attributes and its
outcomes. The frame builder writes it from the final codes, the attribution file, the evidence and the
specification. This section fixes the frame of a passage or work study. An author study's frame is not
part of version 1, and the frame tool refuses to run in one.

**Cells.** A *cell* is one author (a person or a collective) and one value of each attribute in
`unit.rollup_by`. Its `unit_id` is `<person_id>|<value>|...`, in the order `rollup_by` gives; with no
`rollup_by` it is the `person_id`. No `person_id`, `unit_id` or `rollup_by` level code contains `|`
(section 3, 4.1, 4.3), so a cell id reads one way only.

**Counted passages.** The units behind a cell are the rollup's (4.2): the attribution rows of that
author and those `rollup_by` values that have no value listed in `unit.exclude_from_rollup` and whose
status is in `counted_statuses`. Everything below that speaks of a cell's passages means these.

**Columns**, in this order:

`unit_id, author, <each rollup_by key>, unit_kind, <period key>, <period key>_num, <attribute columns>,
<outcome columns>`

| Column | Value |
|---|---|
| `author` | the cell's `person_id` |
| `unit_kind` | the author's `author_kind` (one per person, 4.3) |
| `<period key>`, `<period key>_num` | the period's label as declared in `periods.labels`, and its number from 1; both the missing value when no year places the cell |
| a categorical attribute | one column, `<key>`: a declared level, or the missing value |
| a flags attribute | one column per flag, `<key>_<flag>`, `1` or `0`, in the order `flags` gives; then `<key>_<missing>`, `1` when no value maps to any flag and `0` otherwise |
| an outcome | one column, `<key>`, for each outcome whose source is `codes` and whose rollup is not `none`, in the order declared |

Attribute columns follow the order of `attributes`. The attribute of kind `period` is not repeated among
them: it is the period column. The missing value of an attribute or of the period is the attribute's
`missing` (default `NE`); a study with no period attribute uses `NE`.

**Outcome cells.** The value is the outcome's declared rollup (4.2) over the final codes of the cell's
passages, with one difference:

| The cell's final codes for the outcome | Frame value |
|---|---|
| none, or NA codes only | empty |
| at least one `missing`, and no level code | the outcome's `missing` value |
| at least one level code | the rollup of 4.2 over them: a level code, or `mixed` for `mixed-if-conflict` |

An empty cell says the question did not arise; `missing` says it arose and was not established. The
rollup of 4.2 writes `missing` for both, because it reports per author what is established. An NA code
never appears in a frame. A final code that is not a level code, an NA code or the `missing` value of
its outcome is an error. A passage with no final code at all counts as "none" (open point 4).

**The period.** A year is sought by each entry of `periods.basis` in turn (4.8 says how a year is read
from a value):

- `work_date`: the evidence rows in counted tiers whose `attribute_kind` is `work_date` and whose
  `unit_id` is one of the cell's passages. Each gives a year or none. If the years found all fall in one
  period, that is the cell's period. If they fall in more than one, or none is found, the next basis is
  tried. A person-level `work_date` row is not used.
- `life_dates`: the person-level rows (4.1) of that `attribute_kind` in counted tiers. If they give a
  year, its period is the cell's.

If no basis places the cell, both period columns hold the missing value.

**Attribute evidence.** An attribute's values are the `value` cells of the author's rows in counted tiers
whose `attribute_kind` is one of its `source_attributes` and whose `unit_id` is either the person's own
id (a person-level row) or one of the cell's passages, in the order of the evidence file. They are
bucketed by the attribute's table (4.8). A categorical attribute with no value at all gets the missing
value. A plug-in bucketer is refused in a frame, and nothing is written (open point 6).

**Cells that are not on the question.** Where `frame_rules.exclude` declares the rule
`not-on-question`, a cell whose outcome columns are all empty is left out of the frame and written to
`<frame>.dropped.csv` (`unit_id, rule, reason`), so that it can still be inspected. Without the rule the
cell stays in the frame. The other exclusion rules are not defined over cells in version 1 (section 3).

**How the files are written.** The frame, the dropped list and the passage list are CSV with every cell
quoted, lines ending in LF, and rows in ascending code-point order of `unit_id`. The passage list is the exception: its rows are in the order of
the evidence file. The frame-change log's `frame_sha256` is taken from the
frame file (4.4).

**Checks.** Every cell is checked before anything is written: each value is one its column allows, each
`unit_id` is unique, and every column is present. On any breach nothing is written and the breaches are
listed. The finalised codes must be current (4.6). The frame's provenance record lists gates S5 and S6.
Post-steps (4.5) run after these checks.

**The passage list.** A second output of the same tool, for a reader who wants to see what stands behind
a cell. One row per evidence row whose `unit_id` is an attribution unit, counted or not:

`unit_id, passage_id, evidence_id, person_id, attribution, counted, not_counted_reason`

`unit_id` is the cell the passage belongs to, or would belong to if it were counted; `passage_id` is the
passage's own unit id; `person_id` is its attributed author; `attribution` is its status; `counted` is
`true` or `false`. A row that is not counted gives the first reason that applies, in this order:

1. `tier-<tier>`: the row's tier is not counted (`tier-blank` for an empty tier);
2. `excluded-<attribute>-<value>`: `unit.exclude_from_rollup`, the first key that applies in the order
   the specification gives;
3. `attribution-<status>`: the passage's status is not counted (`attribution-blank` for an empty one);
4. `not-on-question`: the cell was dropped.

A reason is a label to show, not a field to take apart. Person-level rows are not listed.

### 4.8 Bucket tables and years

**A bucket table** (`bucketer.kind: "table"`) is a CSV with the columns `field, pattern, unless, bucket,
note`, read from the top:

| Column | Meaning |
|---|---|
| `field` | the `attribute_kind` the row looks at, or `*` for any |
| `pattern` | a regular expression searched in the folded value (rule 1.10, spaces kept) |
| `unless` | optional; the row does not fire on a value this also matches |
| `bucket` | the level or flag the row assigns |
| `note` | why the row exists; required |

An empty table, other columns, a row without `pattern`, `bucket` or `note`, and an expression that does
not compile are errors. A table is the project's. It decides values an analysis reads, so it must be
listed in the `covers` of gate S0.

- `match: "first"` (the default, for a categorical attribute): rows are tried in order, and the first row
  that fires on any of the values decides. If none fires, the result is the bucketer's `fallback`, or the
  attribute's missing value when no `fallback` is declared.
- `match: "all"` (for a flags attribute, and only there): every row that fires adds its bucket; the
  result is the set of buckets, and a flag is `1` when it is in the set. There is no fallback: an empty
  set is what `<key>_<missing>` records.

**A year** is read from a value like this, for the period rule:

- From one value: for `work_date`, the first run of three or four digits that is not part of a longer
  number; for `life_dates`, the largest such run. Where a value has no such run, for either basis, a
  stated century ("4th c.") gives its middle year (350). Two-digit and negative years are not read. A
  value that yields no year places nothing.
- From several values: for `work_date`, each value gives its own year, and 4.7 says how a cell's years
  combine. For `life_dates`, the largest year among the values is the person's.
- A year `y` is in period `i`, counted from 1, when `i - 1` of the `cuts` are less than or equal to `y`:
  a year equal to a cut begins the later period.

## 5. Plug-ins

### 5.1 Common rules

A plug-in is a Python file in the project's repository, named in the specification as
`{ "file": path, "attr": string, "version": string }`.

- The toolkit loads the file by path. It does not import by module name and does not search `sys.path`.
- **Every plug-in file must be covered by gate S0.** A specification naming one that is not is invalid.
  Loading a plug-in runs the project's code, so it is cleared the same way the specification is.
- A plug-in's result depends only on its arguments and on the files the specification names. It may
  keep what it has read from those files, but nothing else between calls: a value that varies per call,
  such as a person's year, is passed as an argument. There is no separate initialisation step. It makes
  no network request and writes no file.
- `version` is recorded in every output the plug-in contributes to (4.6).
- No tool calls anything in a plug-in file except the object its `attr` names.

Three kinds exist: an evidence **reader** (`evidence.reader`: yields rows in the 4.1 shape from a
project's own format), a plug-in **bucketer** (`bucketer.kind: "plugin"`: maps a unit's source values to a level)
and a **vantage** module (5.2).

### 5.2 Vantage (optional)

A study may be read from a declared standpoint: a project's own review of who the people in the frame
are, relative to that standpoint. The toolkit takes no position on any such review and holds none. With
`vantage.module` null or absent, identities are the persons the project's own rows name, as the registry records them, the candidate
search of 4.4 compares those persons with one another, and every person
is included.

The vantage plug-in's `attr` names an object with two functions:

```
identities() -> iterable of { "person_id": str, "display_name": str, "aliases": [str] }
included(person_id: str, rule: str) -> (bool, str)     # the specification's vantage.inclusion; a reason
```

`identities()` is the repository-wide identity source. `included()` applies `vantage.inclusion`; the
reason is recorded beside every exclusion it causes, in the frame-change log.

There is no name-lookup or review-status function. Matching a name to an identity is the candidate search
of 4.4, which the toolkit does over `identities()`, and no stage needs a review status.

### 5.3 Forbidden vocabulary

`vocabulary.forbidden` names a text file of regular expressions, one per line, with `#` comments. They
are matched without regard to case against the folded text of a cell (rule 1.10). The row
checks apply them to every column except those in `exempt_columns`, which defaults to `["quote"]`: a
quotation is reported as it stands. A project that wants quotations checked as well declares an empty
list. The file is the project's and must be covered by S0. Without it no vocabulary check runs.
researchteam ships no pattern.

### 5.4 Corpus

`corpus.text` and `corpus.works` name the folders of the project's text store, which the quote re-finder
and the query-plan runner read. The tools read only what is listed here, and a tool that needs the
corpus refuses to run when it is not declared; there is no default location.

- **Text:** one JSON Lines file per work, `<text>/<work slug>.jsonl`. Each line has `locus_id`
  (`<work slug>#p<N>`) and `text`. Other fields are ignored.
- **Works:** one JSON file per work, `<works>/<work slug>.json`, with `author`; `stored_language`
  (ISO 639-3), or `language` when that is absent; and `publication.composition.year` or `.date`, each a
  scalar or `{ "value": ... }`, of which the first integer is taken.
- A `locator` of the form `<work slug>#p<N>` is a text-store locus. The quote re-finder looks for the
  quotation in that line. A row with any other locator is checked against the fetch receipt for its
  `url` and quote.
- A row in a counted tier whose quotation cannot be re-found, at a locus or in a receipt, is an error in
  a `draft` or `active` study. In a `legacy` study it is reported and counted, and is not an error: rows
  that predate receipts cannot be made re-findable.
- **What a re-find proves.** That the string occurs at the locus. It does not prove that the string is
  one author's continuous text. Where a page was set in columns and its stored text interleaves them, a
  span that runs from one column into the other is still a substring of the locus and is re-found. The
  first project found such spans in its first run and repaired each by hand to a single column.
  Whoever writes a quotation reads it at the locus (section 8); the re-finder does not stand in for that.

## 6. Gates and sign-offs

### 6.1 Gates

| Gate | What it clears | The stage that refuses without it |
|---|---|---|
| S0, study specification | the specification and the files it declares, including every plug-in, the vocabulary file and the stop-words file | enumeration |
| S5, codebooks | the codebooks and shared coding rules | building coding packets |
| S6, analysis plan | the analysis plan or code, and the analysis-engine pin when it is a file of its own (section 3) | analysis (in the analysis engine) |
| S8, publication | the report and the page | building the report and page |

There is no S1 to S4 or S7 gate. This contract requires S0 enforcement before the enumeration tools are
moved, and leaves S6 and S8 to the tools that run those stages.

A **manifest** is one JSON object:

```
{ "kind": "survey-signoff", "gate": string, "project": string, "mode": string,
  "schema_version": string, "files": [ ... ] }
```

- `files` lists the specification first, then the gate's `covers` in the order declared, with repeats
  removed. Each entry is exactly `{ "path": ..., "sha256": ... }`: the repository-relative path as
  declared, with forward slashes, and the lower-case hex SHA-256 of the file's bytes after the next rule.
- It is written as canonical JSON: keys sorted, no whitespace, UTF-8, and one trailing line feed.
- A text file is hashed with each CRLF replaced by LF; any other file is hashed as it is. A file is text
  by its suffix alone, matched case-sensitively: `.json .jsonl .csv .tsv .md .txt .py .R .sh .yaml
  .yml`.
- The gate's identity is the SHA-256 of the manifest file's bytes, the line feed included. Every command
  that shows a gate's hash shows this one.

These are fixed because any difference changes every manifest hash and so un-clears every signed gate.

A gate is in one of three states: `CLEARED` (a valid signature exists for the current manifest hash),
`UNCLEARED`, or `UNAVAILABLE` (signatures cannot be verified here). A gate whose files have changed
since a request was made is `UNCLEARED` whether or not signatures can be verified.

A stage whose gate the specification does not declare refuses to run, except in a `legacy` study, where
the stage runs and its output records that the gate is not declared (4.6).

| `enforce` | `CLEARED` | `UNCLEARED` or `UNAVAILABLE` |
|---|---|---|
| `blocking` | the stage runs | the stage refuses, exit non-zero |
| `build-only` | the stage runs | the stage runs, and its output records the gate's state and mode |

`mode: "retroactive"` records that a gate was signed after the work it covers was done. It is written
into the manifest and carried into every output that depends on the gate (4.6), to be shown to the reader.

### 6.2 Sign-offs

- A sign-off is an operator-signed clearance made with `agentteams`, with scope
  `survey-signoff/<gate>/<study id>` and action `<scope>:sha256-<manifest hash>`.
- **It is recorded in a per-study log beside the manifests, not in the team's security decisions log**
  (operator ruling, 2026-11-19). A study gate is a research clearance for one study. Keeping it out of
  the team's log means a repository does not have to migrate that log to signed rows in order to run a
  study. `signoffs.ledger` names the log's folder: `agentteams-clearance:<path>`.
- The toolkit builds the manifest and prints what the operator must sign. It never signs. The operator
  signs from a trusted `agentteams` install outside every agent's write root, with one handoff script.
- Verification uses the team's approver list and verify keys. A signature by a key not on the list does
  not clear a gate.
- This depends on `agentteams` supporting a second, gates-only log as a documented and tested pattern,
  including whether a HALT in the team's log binds it (an open `agentteams` issue). The sign-off tools
  are not moved before that is settled (open point 1).

## 7. Commands and CI

Bridge commands, each taking a project:

| Command | Does |
|---|---|
| `survey-validate` | checks the specification and every row file present; writes nothing |
| `survey-status` | prints each gate's manifest hash, state, `enforce` and `mode`. It exits 0 whatever the states are, and non-zero only when a specification, manifest or ledger is malformed; refusing is a stage's job |
| `survey-manifest <gate>` | writes the gate's manifest and prints what the operator signs |
| `survey-registry` | builds the identity registry; lists candidates; applies recorded overrides |
| `survey-rows` | checks a batch of evidence rows and merges it into the evidence file, renewing the registry's record or refusing where it could not (4.1, 4.4) |
| `survey-enumerate` | records an enumeration round; reports the stopping rule (needs S0) |
| `survey-packets` | builds blind coding packets for passes A and B (needs S5) |
| `survey-agreement` | reports agreement between passes A and B |
| `survey-finalize` | writes final codes, fail-closed (4.2) |
| `survey-rollup` | rolls final codes up to the author |
| `survey-frame` | writes the frame of a passage or work study, and its passage list (4.7). It refuses in an author study |
| `survey-quotecheck` | re-finds each quotation at its locus or against its fetch receipt |

A later version may add commands. The explorer projection (section 9) and the query-plan runner
get theirs when those tools are written.

**CI.** `survey-validate` fails the build on any error. Gate state is *reported* and never fails a pull
request: an unsigned gate is the normal state while work is being prepared. A malformed manifest or
ledger does fail.

## 8. Agents

Seven roles, each with a declared tool grant. They are rendered into a derived repository by
`agentteams` from the project brief; none is written by hand.

| Agent | Writes | Never |
|---|---|---|
| `@study-designer` | the draft specification, codebooks, query plans | signs; edits a file a cleared gate covers without saying the gate will un-clear |
| `@source-enumerator` | enumeration rounds and their log | declares saturation; adds to the frame outside the log |
| `@identity-resolver` | identity overrides, each with a reason | links on a name match alone |
| `@profiler` | evidence rows | codes; writes a quotation it did not read at the locus |
| `@position-coder` A and B | one coding pass each, from a blind packet | sees the other pass, the other coder's notes or the rollup |
| `@adjudicator` | adjudications, for disagreements and for units where a pass is missing | changes a code on which A and B agree |
| `@results-writer` | the report, from finalised codes | states a result that is not in the rollup |

Their grants, and the hook or check that enforces each "never", are fixed when the agents are added, with
`@security` review. That is after the tools, and not in version 1.

## 9. Relation to the bibliography explorer

The explorer displays people, evidence and sources; the toolkit produces them. The join is a projection:

- **Evidence:** the first thirteen columns of 4.1 are the explorer's required `evidence.csv` columns.
  The projection drops
  `unit_id`, writes one explorer row per survey row, and appends a row's `downgraded_from` to its `audit`
  text, labelled as such.
- **`basis`, `reporter`, `note`:** explorer contract **1.1** (2026-11-20) carries them as three optional
  `evidence.csv` columns with these names, shown beside each piece of evidence. The projection copies
  them as they are; they are never folded into `via` or `audit`. A project must take the explorer's
  exporter and component at 1.1 or later before it projects rows that have a `reported` basis: a 1.0
  exporter refuses the columns, and showing a reported statement without saying so would misstate it.
- **Codes:** the explorer's `codes.csv` is one row per person and code key. It is generated from the rollup, never
  written by hand; `established` is false for the outcome's `missing` value.
- **Persons:** display names come from the registry, which is also what writes the explorer's
  `persons.csv`.
- **Passages:** the passage list of 4.7 is what a later explorer contract (1.2, not yet written) is to
  read in order to show, under a cell, the passages behind it and why any was not counted. Until that
  contract exists the list is an output with no reader in researchteam, and its columns are fixed here.

The projection is toolkit code: it is written in researchteam with the row tools (section 10, step 5),
not in each project.

## 10. Delivery and order of work

The toolkit is part of the scholarly profile and reaches a derived repository through
`researchteam update`, like the term index. It never touches a project's `study.json`, rows, codebooks,
tables or plug-ins.

Order, each step its own reviewed pull request:

1. This contract, checked against the reference implementation, then agreed.
2. Explorer contract 1.1 (section 9).
3. **Wait** for the first project to have S0 and S5 signed and to have run a stage that writes evidence
   rows or codes. A run of enumeration alone does not end the wait, because it exercises none of the
   evidence, codes, rollup or attribution shapes of section 4. Then freeze the specification as
   version 1, with a recorded list of what changed from revision 2 (section 12).
4. The specification validator, the manifest builder and `survey-validate` / `survey-status`, with an
   invented example study and tests. No signing yet.
5. Row checks and the batch merge, the registry, the table bucketer, agreement, finalising, rollup, the
   frame and its passage list, and the explorer projection (section 9).
6. Sign-off verification and stage refusal, once the `agentteams` pattern is documented.
7. Enumeration, packets, quote re-finding and the query-plan runner.
8. The agents, the bridge commands in `CLAUDE.md`'s managed block, and the CI gate.

Steps 1 to 3 are done (step 2 on 2026-11-20, step 3 on 2026-11-23). No tool was written before step 3 (operator rulings: 2026-11-19, the
contract first, the tools and agents after the first project has run a stage; 2026-11-21, that stage
is one that writes evidence rows or codes, so that the freeze follows real rows and a change the first
project forces does not become a version after 1. The cost, accepted with the ruling, is that the tools
start later).

## 11. Open points

Settled by the first check (2026-11-19): a hand-written validator is enough (the published schema uses
only types, required keys, closed objects, enumerations, constants, patterns, bounds, references and
four conditionals); no review-status function is needed; `unit.aggregate_to` is removed; a reader
plug-in is enough for a legacy evidence format, and writing that format stays with the project; the
corpus shapes and the log columns are as given above.

Settled by the second check (2026-11-19): `held_out` is removed and its rule stated in section 3;
`any-present` takes a declared `present_code`; `mixed` is a reserved output code; a manifest's `files`
entries and its text rule are as in 6.1; `window` and `log` stay required on every enumeration. Settled after the consistency audit:
`evidence.tier_map` is removed, and `frame_rules.post_steps` is defined in 4.5.

Settled by the comparison with the reference at its revision of 2026-11-19: a draft is a draft by
`status` only; `identity.overrides` and `change_log` may be absent; a `none` or evidence-attribute outcome
is left out of the rollup; identity candidates may be approximate but are never links, equal ids
included; an unfindable quotation in a counted tier fails except in a legacy study; a stage with an
undeclared gate refuses except in a legacy study.

Added after the reference was aligned (2026-11-19): an override row states its decision, and `distinct`
records a reviewed pair of different people (4.4); a legacy study may list, row by row and rule by rule,
the breaches of rows that predate the rules (4.1); every output has a provenance record (4.6).

Settled on 2026-11-20: explorer contract 1.1 is written (`templates/bibliography-explorer/CONTRACT.md`,
section 7), with `basis`, `reporter` and `note` as optional evidence columns.

Settled at the freeze (2026-11-23): the points of section 12.

Still open:

1. **Per-study ledger.** The folder layout `agentteams` expects for a gates-only log, and whether a HALT
   in the team's log binds it. Waits for the `agentteams` issue. It blocks step 6 of section 10, not this
   contract's agreement.
2. **An author study's frame.** Version 1 fixes the frame of a passage or work study only (4.7).
3. **Explorer contract 1.2.** The reader of the passage list (section 9).
4. **A counted unit with no final code.** The frame writes an empty cell for it, as for "not applicable"
   (4.7). Whether that should stop the build, or be reported apart, is open: a study coded in rounds
   builds frames while some units are not yet coded.
5. **A checkable engine pin.** A pin file is named inside the opaque `analysis` object, so no toolkit
   check sees it (section 3). A declared field would let the validator require that S6 covers it.
6. **Frame rules over cells, plug-in bucketers in a frame, and `merges`.** Version 1 defines only
   `not-on-question` for a passage or work frame, refuses a plug-in bucketer there, and
   carries an outcome's `merges` without saying which tool applies them.

## 12. What the freeze changed

The first project ran its first stage that writes evidence on 2026-11-23, with gates S0, S5 and S6
signed. It kept a list of every point at which its reference implementation had moved away from
revision 2 of this contract. Each is taken here.

| # | Change | Sections | Found by |
|---|---|---|---|
| 1 | The frame of a passage or work study is specified: one row per cell, its columns, and an empty outcome cell for "not applicable" where the rollup writes `missing` | 2, 4.2, 4.7 | building the frame for analysis |
| 2 | The passage list, an output for a later explorer contract | 4.7, 9 | the results page |
| 3 | In a passage or work study the frame's unit, and so the frame-change log's, is the cell | 4.4 | building the frame |
| 4 | The registry takes persons from the attribution file as well as the evidence, and an id-only person takes the linked identity's name | 4.3, 4.4 | a new study could not write its first evidence row |
| 5 | A person-level row in a passage or work study carries the `person_id` as its `unit_id` | 4.1 | writing attribute rows |
| 6 | An enumeration round with no candidates is refused | 4.4 | two empty rounds met a saturation rule |
| 7 | The frame's period columns are named after the period attribute, and a study has at most one | 3, 4.7 | the analysis specification |
| 8 | The analysis-engine pin may be a file of its own that only S6 covers | 3, 6.1 | an engine release un-cleared every gate (operator ruling, 2026-11-22) |
| 9 | An evidence merge renews the registry's record, or is refused | 4.1, 4.4, 7 | the first merge left the registry stale |
| 10 | A re-found quotation is a string at its locus, not proof of continuous text | 1, 5.4 | quotations spliced across interleaved columns, in the first run |

Decided by researchteam at the freeze, beyond what the list asked:

- **`schema_version`.** `"1"` and `"0"` are both valid and checked identically (section 3). The evidence
  format keeps its name `survey-evidence-0`: the name stands for the eighteen columns, which did not
  change.
- **Checks that make the frame unambiguous.** New evidence rule ids `unit-unknown`, `unit-person` and
  `id-separator` (4.1); the attribution file's rules on unit ids, passage attributes and one
  `author_kind` per person (4.3); and in section 3 the checks on the period attribute, on frame columns
  with the same name, on distinct level, NA and `missing` codes, on `|` in a `rollup_by` code, and on
  exclusion rules in a passage or work study, and on a bucketer's `match` and `fallback`. Point 5 asked only that the convention be named; without
  the check a mistyped passage id would pass as a person-level row. Every row of the first project's
  first run passes all of them.
- **Point 9 is settled inside the merge**, not as an order for a person to follow: the merge works out
  the result first and writes nothing if the registry's rows would change.
- **What was written down for the first time.** The bucket table and the year rule (4.8), and how the
  frame files are written (4.7). Revision 2 relied on all three without stating them.
- **Commands.** `survey-rows` and `survey-frame` are added to section 7.
- **The explorer projection is toolkit code** (sections 2 and 9), written with the row tools.

**Where the reference implementation differs from version 1.** None of these changes a value in the
first project's data. The first group needs no gate re-signed there, because no gate covers those tools;
the second is in the frame tool, which that project's S6 covers, so it is taken at that project's next
S6 signing and must be taken before any study with another missing value uses the tool.

- In the specification and row checks: accepting `schema_version` `"1"`; the section 3 checks listed
  above, with those on bucket tables (`match`, `fallback`, S0 coverage); `unit-unknown`, `unit-person` and
  `id-separator` (4.1); the attribution rules (4.3).
- In the merge (4.1, 4.4): today it checks the batch but not the file it joins, refuses unless the
  registry is built, appends, and writes nothing else. It does not yet work out the registry first or
  renew its record, which is why the first project's registry went stale after its first merge.
- In the frame tool: it writes `NE` wherever 4.7 says "the missing value" of an attribute or the period,
  and ignores a table bucketer's `fallback`, where version 1 reads the attribute's `missing` and the
  declared `fallback`.
