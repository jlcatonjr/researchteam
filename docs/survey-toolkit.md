# Survey toolkit: contract

**Status: draft 1 (2026-11-19). Not agreed, and nothing here is implemented in researchteam yet.** The
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
5. **Deterministic.** The same inputs give byte-identical outputs. Outputs carry no timestamp; a log row
   carries the date its author gives it.
6. **Paths stay in the repository.** A path in the specification is relative to the study's folder, or
   to the repository root when it starts with `repo:`. An absolute path, a `..` segment, or a path that
   resolves outside the repository through a link is an error.
7. **Standard library only.** The tools import nothing outside the Python standard library. Verifying a
   signature needs `agentteams`, which is optional: without it a gate's state is `UNAVAILABLE`, and a
   blocking gate in that state refuses like an uncleared one.
8. **No project data upstream.** researchteam holds the toolkit, an invented example study and tests on
   invented data. A project's specification, codebooks, tables, plug-ins and rows stay in the project.
9. **What a clean run means.** The study is well-formed, internally consistent and, where gates are
   cleared, unchanged since the operator signed. It does not mean that any quotation is accurate beyond
   the locus it was re-found at, that a code is right, or that the frame is complete.

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
keys are an error at every level. The validator is researchteam's own, written against the standard
library; it is the authority. A JSON Schema file (2020-12) is published beside it as a description for
editors. A shared set of valid and invalid specifications is kept in the tests so the two can be compared
wherever a JSON Schema library is installed; researchteam's own CI does not install one.

Fields marked `?` are optional. `slug` is `^[a-z0-9][a-z0-9_-]*$`. `path` is a string under rule 1.6.

```
{
  "schema_version": "0",
  "id": slug, "title": string, "question": string,
  "status"?: "draft" | "active" | "legacy",
  "vantage"?: { "module": string | null, "guide"?: path, "inclusion"?: string | null },     // 5.2
  "vocabulary"?: { "forbidden": path },                                                     // 5.3
  "corpus"?: { "text": path, "works"?: path },                                              // 5.4
  "unit": {
    "kind": "passage" | "work" | "author",
    "aggregate_to"?: "author",                         // required unless kind is "author"
    "attribution"?: { "file": path, "statuses": [string], "counted_statuses"?: [string] },
    "passage_attributes"?: [ LevelSet ],
    "rollup_by"?: [string],
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
    "counted_tiers": [string],
    "tier_map"?: { string: string },
    "attribute_kinds"?: [string]
  },
  "outcomes": [ {
    "key": slug, "label": string,
    "source": { "kind": "evidence-attribute", "attribute": string }
            | { "kind": "codes", "codes_file": path },
    "codebook"?: path,
    "scale": "nominal" | "ordinal",
    "levels": [ Level ],                               // at least 2
    "na_codes"?: [string],
    "missing"?: string,                                // default "NE"
    "merges"?: { string: string },
    "rollup"?: "single-code" | "mixed-if-conflict" | "max-order" | "any-present" | "none",
    "held_out"?: true
  } ],
  "attributes": [ {
    "key": slug, "label": string,
    "kind": "categorical" | "flags" | "period",
    "source_attributes"?: [string],
    "bucketer"?: Bucketer,
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
    "exclude"?: [ { "rule": "institutions" | "not-on-question" | "unit-ids" | "id-contains",
                    "values"?: [string], "reason": string } ],
    "change_log"?: path,
    "post_steps"?: [path]
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

**Checks beyond shape.** Each is an error:

- outcome keys and attribute keys are unique; level codes are unique within an outcome;
- `rollup: "max-order"` without `scale: "ordinal"`, or with a level that has no `order`;
- a merge whose source is not a declared level code or NA code (a target may be a new label);
- `cuts` not ascending, or `labels` not one longer than `cuts`; a `strata` key that is not a period
  number from 1 to the number of labels;
- a passage or work study with no outcome whose source is `codes`;
- a referenced input file that does not exist, unless `status` is `draft`. Files a stage writes
  (`log`, `change_log`) may be absent;
- a plug-in or `vantage.module` file that is not covered by gate S0 (section 5.1);
- a gate that covers no file, or a `covers` path that does not exist in an `active` study.

**Changes from the reference implementation**, each for the reason given:

| Field | Reference | Here | Why |
|---|---|---|---|
| `evidence.format` | `author-attributions-v1`, `explorer-evidence-1.0` | `survey-evidence-0`, `plugin` | The first is one project's legacy file, read through a reader plug-in that stays in that project. The second name claimed the explorer's 13 columns for a file that has 17. |
| `bucketer.plugin` | `"module.path:attr"` | `{file, attr, version}` | A file path can be confined to the repository, hashed and covered by a gate; an import path cannot. |
| `vocabulary` | a constant in the tools | a file the specification names | The rule is a project's, not the toolkit's. |
| `corpus` | a fixed layout | declared paths | The text store's layout is a project's. |
| `analysis` | fixed fields | an opaque object | Its shape belongs to the analysis engine, which is proposing to replace it. |
| `signoffs.ledger` | the team's decisions log | a per-study log (6.2) | Operator ruling, 2026-11-19. |

## 4. Row files

All are CSV, UTF-8, with exactly the columns listed, in this order. A missing or extra column is an
error. An empty cell means "not given"; a tool never treats it as a value.

### 4.1 Evidence (`survey-evidence-0`)

`id, person_id, attribute_kind, value, tier, source_id, citation, locator, quote, url, access, via,
audit, basis, reporter, unit_id, note`

The first thirteen columns are the bibliography explorer's `evidence.csv` (contract 1.0), with the same
meanings. The last four are the survey's:

| Column | Meaning |
|---|---|
| `basis` | `own` (the person's own words) or `reported` (someone else's account of them) |
| `reporter` | who reports, when `basis` is `reported` |
| `unit_id` | the passage or work the row belongs to, in a passage or work study |
| `note` | free text; on a not-established row, what was tried |

Errors:

- a row in a counted tier without a `quote`, or with neither `citation` nor `source_id`;
- a row in a counted tier without a `basis`; `reported` without a `reporter`; a `reporter` on an `own` row;
- a not-established row (the outcome's `missing` value) with a `quote`, or without a `note`;
- a `tier` or `attribute_kind` the specification does not declare;
- a `unit_id` in an author study, or none in a passage or work study;
- a duplicate `id`; a `person_id` the registry does not hold;
- text matching the project's forbidden-vocabulary file in `value`, `via`, `audit` or `note` (5.3). The
  `quote` column is exempt: a quotation is reported as it stands.

### 4.2 Codes

`unit_id, person_id, outcome, code, pass, coder, basis, reporter, evidence_ids, level, note`

`pass` is `A`, `B` or `final`. `code` is one of the outcome's level codes, its NA codes, or its `missing`
value. `evidence_ids` is a `;`-separated list of evidence ids.

Errors: an outcome the specification does not declare as `codes`; a code outside the allowed set; a code
other than `missing` without `evidence_ids` or without a `basis`; an evidence id that does not exist or
belongs to another person; `reported` without a `reporter`; two rows for the same unit, outcome and pass;
a `final` row for a unit that lacks an `A` or a `B` row.

**Finalising is fail-closed.** Where passes A and B agree, the final row is theirs. Where they disagree,
no final row is written until an adjudicated row is supplied with its own coder and note; the tool lists
the disagreements and exits non-zero. Agreement is reported as raw agreement, Cohen's κ and Gwet's AC1,
per outcome, with the number of units each rests on.

### 4.3 Attribution (passage and work studies)

`unit_id, person_id, author_kind, work, locator, status` followed by one column per key in
`unit.passage_attributes`, then `basis, note`.

`status` is one of `unit.attribution.statuses`. Only rows whose status is in `counted_statuses` enter a
rollup.

### 4.4 Logs

- **Enumeration log** (`enumerations[].log`): one row per round, with the round number, the query or
  seed set used, the number of candidates seen and the number new. The stopping rule is computed from
  these rows only; a study cannot be declared saturated by assertion.
- **Frame-change log** (`frame_rules.change_log`): one row per unit added to or removed from the frame
  after gate S0, with the rule and a reason. A frame that differs from the enumeration result without a
  row for each difference is an error.
- **Fetch receipts:** for evidence taken from the web, one record per fetch with the URL, the date and
  the SHA-256 of the body, so a quotation can be re-found against what was fetched.

The exact columns of the three logs are taken from the reference implementation when the tools are
moved; they are not fixed in this draft.

## 5. Plug-ins

### 5.1 Common rules

A plug-in is a Python file in the project's repository, named in the specification as
`{ "file": path, "attr": string, "version": string }`.

- The toolkit loads the file by path. It does not import by module name and does not search `sys.path`.
- **Every plug-in file must be covered by gate S0.** A specification naming one that is not is invalid.
  Loading a plug-in runs the project's code, so it is cleared the same way the specification is.
- A plug-in is a pure function of its arguments and the files the specification names. It makes no
  network request and writes no file.
- `version` is recorded in every output the plug-in contributes to.

Three kinds exist: an evidence **reader** (`evidence.reader`: yields rows in the 4.1 shape from a
project's own format), a **bucketer** (`attributes[].bucketer`: maps a unit's source values to a level)
and a **vantage** module (5.2).

### 5.2 Vantage (optional)

A study may be read from a declared standpoint: a project's own review of who the people in the frame
are, relative to that standpoint. The toolkit takes no position on any such review and holds none. With
`vantage.module` null or absent, identities come from the project's own registry file and every person
is included.

A vantage module provides:

```
identities() -> iterable of { "person_id": str, "display_name": str, "aliases": [str] }
included(person_id: str, rule: str) -> (bool, str)     # the specification's vantage.inclusion; a reason
```

`identities()` is the repository-wide identity source. `included()` applies `vantage.inclusion`; the
reason is recorded beside every exclusion it causes, in the frame-change log.

The reference implementation also proposed `lookup(name) -> { status, person_id }`. It is left out of
this draft: matching a name to an identity is a candidate search the toolkit already does over
`identities()` (exact match on folded text, listed, never linked), and a review status is the vantage
module's own vocabulary. If a stage needs the status, the proposal is a third function
`status(person_id) -> str`, with the allowed values declared by the module (open point 3).

### 5.3 Forbidden vocabulary

`vocabulary.forbidden` names a text file of regular expressions, one per line, with `#` comments. The row
checks apply them as in 4.1. The file is the project's and must be covered by S0. Without it no
vocabulary check runs. researchteam ships no pattern.

### 5.4 Corpus

`corpus.text` and `corpus.works` name the project's text store, which the quote re-finder and the
query-plan runner read. Their record shapes are an open point (4); until it is settled these two tools
are moved last.

## 6. Gates and sign-offs

### 6.1 Gates

| Gate | What it clears | The stage that refuses without it |
|---|---|---|
| S0, study specification | the specification and the files it declares, including every plug-in and the vocabulary file | enumeration |
| S5, codebooks | the codebooks and shared coding rules | building coding packets |
| S6, analysis plan | the analysis plan or code | analysis (in the analysis engine) |
| S8, publication | the report and the page | building the report and page |

There is no S1 to S4 or S7 gate. In the reference implementation only S5 is enforced today; this
contract requires S0 enforcement before the enumeration tools are moved, and leaves S6 and S8 to the
tools that run those stages.

A **manifest** lists the specification and every file the gate covers, each with its SHA-256, sorted by
path, with the gate's `mode`. The gate's identity is the SHA-256 of the manifest's bytes.

A gate is in one of three states: `CLEARED` (a valid signature exists for the current manifest hash),
`UNCLEARED`, or `UNAVAILABLE` (signatures cannot be verified here).

| `enforce` | `CLEARED` | `UNCLEARED` or `UNAVAILABLE` |
|---|---|---|
| `blocking` | the stage runs | the stage refuses, exit non-zero |
| `build-only` | the stage runs | the stage runs and its output says the gate is not cleared |

`mode: "retroactive"` records that a gate was signed after the work it covers was done. It is written
into the manifest and carried into every output that depends on the gate, to be shown to the reader.

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
  are not moved before that is settled (open point 5).

## 7. Commands and CI

Bridge commands, each taking a project:

| Command | Does |
|---|---|
| `survey-validate` | checks the specification and every row file present; writes nothing |
| `survey-status` | prints each gate's manifest hash, state, `enforce` and `mode` |
| `survey-manifest <gate>` | writes the gate's manifest and prints what the operator signs |
| `survey-registry` | builds the identity registry; lists candidates; applies recorded overrides |
| `survey-enumerate` | records an enumeration round; reports the stopping rule (needs S0) |
| `survey-packets` | builds blind coding packets for passes A and B (needs S5) |
| `survey-agreement` | reports agreement between passes A and B |
| `survey-finalize` | writes final codes, fail-closed (4.2) |
| `survey-rollup` | rolls final codes up to the aggregate unit |
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
| `@adjudicator` | adjudicated rows for disagreements | changes a row on which A and B agree |
| `@results-writer` | the report, from finalised codes | states a result that is not in the rollup |

Their grants, and the hook or check that enforces each "never", are fixed when the agents are added, with
`@security` review. That is after the tools, and not in this draft.

## 9. Relation to the bibliography explorer

The explorer displays people, evidence and sources; the toolkit produces them. The join is a projection:

- **Evidence:** the first thirteen columns of 4.1 are the explorer's `evidence.csv`. The projection drops
  `unit_id` and writes one explorer row per survey row.
- **`basis`, `reporter`, `note`:** the explorer contract 1.0 has nowhere to show them, and they must not
  be folded into `via` or `audit`. The proposal is explorer contract **1.1**: three optional
  `evidence.csv` columns with these names, shown beside each piece of evidence. It is an additive change
  made in the explorer's own contract, tests and component before the projection is written (open
  point 2). Until then the projection refuses to run on rows that have a `reported` basis, because
  showing a reported statement without saying so would misstate it.
- **Codes:** the explorer's `codes.csv` is one row per person. It is generated from the rollup, never
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
3. The specification validator, the manifest builder and `survey-validate` / `survey-status`, with an
   invented example study and tests. No signing yet.
4. **Wait** for the first project to have S0 and S5 signed and one stage run. Freeze the specification
   as version 1, with a recorded list of what changed from this draft.
5. Row checks, the registry, the table bucketer, agreement, finalising and rollup.
6. Sign-off verification and stage refusal, once the `agentteams` pattern is documented.
7. Enumeration, packets, quote re-finding and the query-plan runner.
8. The agents, the bridge commands in `CLAUDE.md`'s managed block, and the CI gate.

Steps 1 to 3 can be done now. A copy of the specification taken before step 4 is labelled v0-unstable.

## 11. Open points

1. **Standard-library validator.** The reference implementation validates with a JSON Schema library.
   Does anything in the 866-line schema (conditional requirements, `$defs`) resist a hand-written check?
2. **Explorer 1.1.** Are `basis`, `reporter` and `note` enough for the explorer, or does a downgraded
   value's history (`downgraded_from`) also need its own column rather than living in `audit`?
3. **Vantage.** Is `status(person_id)` needed by any stage, and with what values?
4. **Corpus.** The record shapes of the text store and the works file, as field names and types.
5. **Per-study ledger.** The exact folder layout `agentteams` expects for a gates-only log, and whether
   a HALT in the team's log binds it.
6. **`unit.aggregate_to`.** It has one allowed value. Is another aggregate planned, or should it go?
7. **Evidence reader plug-in.** Is a reader enough for the legacy evidence format, or does that study
   need to write the legacy format as well?
8. **Log columns** (4.4): the three logs' columns, as names and types.
