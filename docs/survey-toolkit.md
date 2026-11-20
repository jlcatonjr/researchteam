# Survey toolkit: contract

**Status: agreed draft, revision 2 (2026-11-19).** Agreed with the first integrating project after two
checks and a line-by-line comparison with its reference implementation. Nothing here is implemented in
researchteam yet. The
study specification is `schema_version "0"` and is **v0-unstable**: the first project using it is still
changing it. It is frozen as version 1 only after that project has had its S0 and S5 gates signed and has
run one stage. Planned for researchteam 1.3 (operator ruling, 2026-11-19).

A *position survey* answers a question of the form "what did the people in this frame hold about X, and
on what evidence". The toolkit is the reusable part of running one: a study specification, the row
shapes, the checks, the gates and the commands. It knows nothing about any topic. It follows a reference
implementation in a derived repository, whose project-specific parts stay there.

Sections: 1 rules; 2 what the toolkit owns; 3 the study specification; 4 row files; 5 plug-ins; 6 gates
and sign-offs; 7 commands and CI; 8 agents; 9 relation to the bibliography explorer; 10 delivery and
order of work; 11 open points.

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
   the locus it was re-found at, that a code is right, or that the frame is complete.
10. **Folded text.** Where this contract says text is *folded*, it means: decomposed (NFD) with combining
   marks removed, lower-cased, soft hyphens removed, a hyphen followed by white space removed together
   with that white space, and each remaining run of white space made one space, with none at either end.
   *Folded without spaces* removes the white space altogether.

## 2. What the toolkit owns, and what a project owns

| The toolkit (researchteam) | The project |
|---|---|
| The specification's shape and its checks | `study.json` and every file it names |
| Row shapes and row checks (section 4) | The rows |
| The table bucketer and the period rule | Bucket tables; any plug-in bucketer |
| Identity candidates, registry build, override handling | The identity source; every link or merge decision |
| Quote re-finding, fetch receipts | The text store and its layout (declared in the specification) |
| Agreement statistics, fail-closed finalising, rollup | Codebooks; the two coding passes; adjudication |
| Enumeration log and the stopping rule | Query plans, seeds, the rounds themselves |
| Gate manifests, gate status, stage refusal | What each gate covers; the operator's signatures |
| The plug-in interfaces (section 5) | The plug-ins, including any vantage module and vocabulary rule |

The analysis engine and the results page are a separate workstream in another repository. The toolkit
stops at finalised codes and a rollup; `analysis` in the specification is carried, checked only for
shape, and covered by gate S6.

## 3. The study specification (`study.json`, v0-unstable)

One JSON file per study, at `Projects/<project>/study.json` unless the project says otherwise. Unknown
keys are an error at every level. A study is a draft only by its `status`; a file's name never makes it
one. The validator is researchteam's own, written against the standard
library; it is the authority. A JSON Schema file (2020-12) is published beside it as a description for
editors. A shared set of valid and invalid specifications is kept in the tests so the two can be compared
wherever a JSON Schema library is installed; researchteam's own CI does not install one.

Fields marked `?` are optional. `slug` is `^[a-z0-9][a-z0-9_-]*$`. `path` is a string under rule 1.6.

```
{
  "schema_version": "0",
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
  "analysis"?: object,                                 // carried; shape owned by the analysis engine
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
- a passage or work study without `unit.attribution`;
- a `saturation` stopping rule without both `rounds_without_new` and `min_new_share`; a
  `legacy-unrecorded` stopping rule in a study whose `status` is not `legacy`;
- a referenced input file that does not exist, unless `status` is `draft`. These may be absent, because
  a stage writes them or they start empty: `log`, `change_log`, `identity.registry`,
  `identity.overrides`, `evidence.receipts`, an outcome's `adjudications`;
- a plug-in (a reader, a bucketer or the vantage module), the `vocabulary.forbidden` file or the
  `identity.stop_words` file that is not covered by gate S0 (5.1, 5.3). Coverage is judged on resolved
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

## 4. Row files

All are CSV, UTF-8, with exactly the columns listed, in this order. A missing or extra column is an
error. An empty cell means "not given"; a tool never treats it as a value.

### 4.1 Evidence (`survey-evidence-0`)

`id, person_id, attribute_kind, value, tier, source_id, citation, locator, quote, url, access, via,
audit, basis, reporter, unit_id, note, downgraded_from`

The first thirteen columns are the bibliography explorer's `evidence.csv` (contract 1.0), with the same
meanings. The last five are the survey's:

| Column | Meaning |
|---|---|
| `basis` | `own` (the person's own words) or `reported` (someone else's account of them) |
| `reporter` | who reports, when `basis` is `reported` |
| `unit_id` | the passage or work the row belongs to, in a passage or work study |
| `note` | free text; on a not-established row, what was tried |
| `downgraded_from` | the value and tier the row had before an audit downgraded it |

Errors:

- a row in a counted tier without a `quote`, or with neither `citation` nor `source_id`;
- a row in a counted tier without a `basis`; `reported` without a `reporter`; a `reporter` on an `own` row;
- a row in the not-established tier (`evidence.not_established_tier`) with a `quote`, or without a
  `note`. Not-established is a tier of the row; its `value` is free text and is not an outcome code;
- a `tier` not in `evidence.tiers`; an `attribute_kind` the specification does not declare;
- a `unit_id` in an author study, or none in a passage or work study;
- a duplicate `id`; a `person_id` the registry does not hold;
- text matching the project's forbidden-vocabulary file in any column not listed in
  `vocabulary.exempt_columns` (5.3).

The row checks apply to the whole evidence file whenever it is checked, not only to rows being added, and
none of them is skipped because an optional declaration or file is absent: an `attribute_kind` is checked
against the outcomes and attributes that use it, and a missing registry is itself an error.

**Rule ids.** Each evidence check has an id, which reports use and the exceptions file below is keyed on:

| Rule id | Breach |
|---|---|
| `columns` | the columns are not exactly the eighteen, in order |
| `id-empty` | an empty `id` |
| `id-duplicate` | a repeated `id` |
| `attribute-kind` | an `attribute_kind` that is not declared |
| `person-unknown` | a `person_id` the registry does not hold |
| `unit-id` | a `unit_id` in an author study, or none in a passage or work study |
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
  `missing`;
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
attribution file is checked like any other row file, header included.

### 4.4 Logs and working files

**Enumeration log** (`enumerations[].log`; CSV, every cell quoted), one row per round:

`enumeration, round, date, method, queries, candidates, new, new_share, new_ids, note`

`round`, `candidates` and `new` are integers; `new_share` is between 0 and 1, to four decimals; `new_ids`
is a `;`-separated list. Each enumeration writes the file its own `log` names. The stopping rule is
computed from these rows only: a study cannot be declared saturated by assertion.

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
or work study and its `person_id` values in an author study. The first entry lists every unit as added.
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
  in a file beside it, named as the output with `.provenance.json` added, written in the same run. An
  output of that kind whose record is missing, or whose `inputs` no longer match the files, is treated
  by the next stage as not built.
- `gates` lists each gate the stage depends on. A gate the specification does not declare has the state
  `NOT DECLARED`. `plugins` lists each plug-in that was loaded; `legacy_exceptions` is the number the
  evidence file was read with, 0 when there is none.
- It is written as canonical JSON, like a manifest, and carries no date.
- A message on the screen is not a record. Nothing is added to a CSV's own columns for this.

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
project's own format), a **bucketer** (`attributes[].bucketer`: maps a unit's source values to a level)
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

## 6. Gates and sign-offs

### 6.1 Gates

| Gate | What it clears | The stage that refuses without it |
|---|---|---|
| S0, study specification | the specification and the files it declares, including every plug-in, the vocabulary file and the stop-words file | enumeration |
| S5, codebooks | the codebooks and shared coding rules | building coding packets |
| S6, analysis plan | the analysis plan or code | analysis (in the analysis engine) |
| S8, publication | the report and the page | building the report and page |

There is no S1 to S4 or S7 gate. In the reference implementation only S5 is enforced today; this
contract requires S0 enforcement before the enumeration tools are moved, and leaves S6 and S8 to the
tools that run those stages.

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
| `survey-enumerate` | records an enumeration round; reports the stopping rule (needs S0) |
| `survey-packets` | builds blind coding packets for passes A and B (needs S5) |
| `survey-agreement` | reports agreement between passes A and B |
| `survey-finalize` | writes final codes, fail-closed (4.2) |
| `survey-rollup` | rolls final codes up to the author |
| `survey-quotecheck` | re-finds each quotation at its locus or against its fetch receipt |

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
`@security` review. That is after the tools, and not in this draft.

## 9. Relation to the bibliography explorer

The explorer displays people, evidence and sources; the toolkit produces them. The join is a projection:

- **Evidence:** the first thirteen columns of 4.1 are the explorer's `evidence.csv`. The projection drops
  `unit_id`, writes one explorer row per survey row, and appends a row's `downgraded_from` to its `audit`
  text, labelled as such.
- **`basis`, `reporter`, `note`:** the explorer contract 1.0 has nowhere to show them on a piece of
  evidence (only its codes carry a `basis`), and they must not
  be folded into `via` or `audit`. The proposal is explorer contract **1.1**: three optional
  `evidence.csv` columns with these names, shown beside each piece of evidence. It is an additive change
  made in the explorer's own contract, tests and component before the projection is written (open
  point 2). Until then the projection refuses to run on rows that have a `reported` basis, because
  showing a reported statement without saying so would misstate it.
- **Codes:** the explorer's `codes.csv` is one row per person and code key. It is generated from the rollup, never
  written by hand; `established` is false for the outcome's `missing` value.
- **Persons:** display names come from the registry, which is also what writes the explorer's
  `persons.csv`.

## 10. Delivery and order of work

The toolkit is part of the scholarly profile and reaches a derived repository through
`researchteam update`, like the term index. It never touches a project's `study.json`, rows, codebooks,
tables or plug-ins.

Order, each step its own reviewed pull request:

1. This contract, checked against the reference implementation, then agreed.
2. Explorer contract 1.1 (section 9).
3. **Wait** for the first project to have S0 and S5 signed and one stage run. Freeze the specification
   as version 1, with a recorded list of what changed from this draft.
4. The specification validator, the manifest builder and `survey-validate` / `survey-status`, with an
   invented example study and tests. No signing yet.
5. Row checks, the registry, the table bucketer, agreement, finalising and rollup.
6. Sign-off verification and stage refusal, once the `agentteams` pattern is documented.
7. Enumeration, packets, quote re-finding and the query-plan runner.
8. The agents, the bridge commands in `CLAUDE.md`'s managed block, and the CI gate.

Steps 1 and 2 can be done now. No tool is written before step 3 (operator ruling, 2026-11-19: the
contract first, the tools and agents after the first project has run a stage).

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

Still open:

1. **Per-study ledger.** The folder layout `agentteams` expects for a gates-only log, and whether a HALT
   in the team's log binds it. Waits for the `agentteams` issue. It blocks step 6 of section 10, not this
   contract's agreement.
2. **Explorer 1.1.** Agreed in outline (`basis`, `reporter`, `note`); to be written into the explorer's
   own contract (step 2 of section 10).
