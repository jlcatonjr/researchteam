# Bibliography explorer: data contract

**Status:** agreed with the first integrating project on 2026-11-18. Schema id
`researchteam.bibliography-explorer`, version `1.1` (2026-11-20; section 7 lists what changed from
`1.0`). The exporter is
`scripts/build_bibliography_explorer.py`; the citation code is `scripts/bibtex_chicago.py`.

The bibliography explorer is a reusable component: period → person → bio and attributes → sources →
source detail. It knows nothing about any study. A project maps its own files into the *input tables*
(section 3); the exporter in researchteam checks them, renders citations and writes one *explorer file*
(section 2); the component displays that file and nothing else.

## 1. Rules that hold everywhere

1. **The exporter is the only writer of the explorer file.** It is deterministic: the same inputs give a
   byte-identical file. The file carries no timestamp; it carries the SHA-256 of each input.
2. **Fail closed.** Any violation of section 4 stops the export with a non-zero exit and no output file.
   A file left at the output path by an earlier export is removed, so it cannot pass for this one.
3. **Nothing is inferred.** The exporter does not guess a bibliography key from free text, match names,
   merge near-duplicate citations or fill a missing field. Identity comes only from ids the project gives.
4. **Text is text.** Every string is displayed as plain text. The component never interprets HTML or
   Markdown. A URL must start with `http://` or `https://`.
5. **Provenance is displayed.** Evidence tier, access, `via`, `basis`, `reporter`, `deemed_by` and
   `verification_state` are shown beside the content they qualify. Absent content is stated plainly
   ("No summary yet", "Not established"), never left blank.
6. **Labels come from the data.** Period labels, attribute names, tier names and role names are in the
   file's vocabularies. The component has no domain words of its own beyond its navigation labels, which
   the host can override.
7. **Ids** match `^[A-Za-z0-9][A-Za-z0-9._:-]*$` and are unique within their list. Hyphens and
   underscores are both allowed, so existing slugs need no change.

## 2. The explorer file (output)

One JSON file, UTF-8, keys sorted. Fields marked `?` are optional; an absent optional field is omitted,
not written as an empty string.

```
{
  "schema": "researchteam.bibliography-explorer",
  "schema_version": "1.1",
  "meta": {
    "title": string,
    "notice"?: string,                  // caveat shown at the top of every view
    "exporter": string,                 // exporter id and version
    "citation_renderer": string,        // e.g. "researchteam-chicago-v1"
    "inputs": [ { "name": string, "sha256": string } ],
    "counts": { "persons": int, "sources": int, "evidence": int, "links": int }
  },
  "vocab":   { ... },                   // 2.1
  "periods": [ Period ],                // 2.2
  "persons": [ Person ],                // 2.3
  "evidence": [ Evidence ],             // 2.4
  "sources": [ Source ],                // 2.5
  "links":   [ Link ]                   // 2.6
}
```

### 2.1 Vocabularies

```
"vocab": {
  "attribute_kinds": [ { "id", "label", "order": int, "multi": bool } ],
  "tiers":           [ { "id", "label", "establishes": bool, "description"? } ],
  "access":          [ { "id", "label" } ],
  "roles":           [ { "id", "label" } ],      // roles on "by" links: author, editor, ...
  "person_kinds":    [ { "id", "label" } ]       // person, institution, corporate, ...
}
```

`tiers[].establishes` is the only thing that decides whether a value counts as established (2.3).

### 2.2 Period

```
{ "id", "label", "order": int,
  "start_year": int | null,       // null = open-ended ("before X")
  "end_year":   int | null,       // null = open-ended ("X on"); inclusive when set
  "established": bool }           // false for the "not established" bin; at most one such bin
```

Established periods are ordered by `order`, must not overlap, and the unestablished bin is shown last.

### 2.3 Person

```
{ "id", "kind": <person_kinds id>, "display_name": string,
  "sort_name"?: string,                     // defaults to display_name
  "aliases"?: [ string ],
  "period": { "id": <period id>,            // exactly one
              "year"?: int,                 // the year the period derives from; used for sorting
              "year_basis"?: string },      // shown as given, e.g. how the year was chosen
  "bio"?: Bio,
  "attributes": [ AttributeValue ],
  "codes"?:  [ Code ],
  "groups"?: [ Group ] }
```

`period.year`, when set, must fall inside the period's range.

**AttributeValue** — one per (person, attribute kind, value):

```
{ "kind": <attribute_kinds id>, "value": string,
  "evidence_ids": [ <evidence id> ],        // at least one
  "established": bool }                     // computed by the exporter, never supplied
```

`established` is true exactly when at least one of the value's evidence rows has a tier with
`establishes: true`. A kind with `multi: false` may still hold several values (competing claims); the
component then shows them all with their tiers.

**Bio**

```
{ "text": string,
  "clauses"?: [ { "text": string, "evidence_ids": [ <evidence id> ] } ],
  "basis": string,                          // e.g. "assembled from established attributes" | "written"
  "authored_by"?: string,
  "verification_state": string }            // required, shown verbatim
```

When `clauses` is present, `text` must equal the clause texts joined by one space, so the displayed bio
and its evidence cannot drift apart. A clause may have an empty `evidence_ids` list only for connective
text; the component marks such a clause as unsourced.

**Code** — a categorical code derived from the evidence, for the analysis subset:

```
{ "key": string, "label": string,           // e.g. the code's name
  "value_label": string,                    // display text of the value, including "not established"
  "established": bool,
  "basis"?: string,                         // e.g. "own words" | "reported", plus a source label
  "evidence_ids": [ <evidence id> ] }       // may be empty only when established is false
```

A boolean flag is a Code whose `value_label` is the flag's yes/no wording. Non-exclusive flags are
separate Codes.

**Group** — a titled block for project-specific records, so the component needs no domain knowledge:

```
{ "id", "title": string,
  "advisory": bool,                         // true: shown in a visually distinct advisory block
  "caveat"?: string,                        // required when advisory is true; shown with the block
  "rows": [ { "label": string, "value": string,
              "links"?: [ { "label": string, "url": string } ],
              "evidence_ids"?: [ <evidence id> ],
              "note"?: string } ] }
```

### 2.4 Evidence

```
{ "id", "person_id": <person id>,
  "attribute_kind": <attribute_kinds id>,   // the one (person, attribute, value) this row is evidence for
  "value": string,
  "tier": <tiers id>,
  "source_id": <source id>,                 // every evidence row points at a Source (2.5)
  "cited_as"?: string,                      // the row's own citation text, when source_id was given
  "locator"?: string,
  "quote"?: string,                         // verbatim; the exporter does not trim or normalise it
  "url"?: string,                           // the page actually consulted, if it differs from the source's
  "access"?: <access id>,
  "via"?: string,                           // third-party channel: the value is reported by someone else
  "audit"?: string,                         // audit trail, shown in a collapsed detail
  "basis"?: string,                         // whose words the evidence is, e.g. "own" | "reported"
  "reporter"?: string,                      // who reports it; only with a basis
  "note"?: string }                         // a remark on this piece of evidence
```

`basis`, `reporter` and `note` are shown as given, each under its own label beside the evidence. The
component attaches no meaning to a `basis` value; the project chooses the words. `via` is the channel
the evidence reached the project through, and `reporter` is the one whose account it is, so a row may
carry both.

### 2.5 Source

Three origins share one shape, so every source can be opened the same way:

| `origin` | What it is | Citation shown |
|---|---|---|
| `bibliography` | an entry in the project `.bib` | Chicago, rendered by the exporter |
| `evidence-citation` | a free-text citation on an evidence row, with no `.bib` entry | the text as recorded, labelled as such |
| `work-title` | a work known only by title (and perhaps date and locator) | the title as recorded, labelled "uncatalogued" |

```
{ "id", "origin": "bibliography" | "evidence-citation" | "work-title",
  "type"?: string,                          // BibTeX entry type, bibliography only
  "citation": { "chicago"?: string,         // bibliography only
                "chicago_runs"?: [ { "text": string, "italic": bool } ],   // the same string, with italics
                "as_recorded"?: string },   // the other two origins; chicago or as_recorded, never both
  "fields": {                               // only fields the input had
    "title"?, "authors"?: [ Name ], "editors"?: [ Name ],
    "year"?, "month"?, "journal"?, "booktitle"?, "publisher"?, "address"?, "volume"?, "number"?,
    "series"?, "pages"?, "school"?, "howpublished"?, "doi"?, "isbn"?, "issn"?, "url"?,
    "date"?, "locator"? },                  // the last two for work-title
  "note"?: string,                          // the .bib note, shown as provenance, never inside the citation
  "attributes"?: [ { "label": string, "value": string } ],   // project-given, shown as given
  "links": [ { "label": string, "url": string } ],   // built from url and doi
  "summary"?: { "text": string,
                "deemed_by": string,        // who wrote it: a named author or agent
                "basis": string,            // what was read: full text | abstract | record only
                "read_url"?: string,        // what was actually read
                "caveats"?: [ string ],     // e.g. "different edition", "snippet only"
                "verification_state": string } }

Name = { "family": string, "given"?: string, "suffix"?: string } | { "literal": string }   // literal = corporate name
```

**Citation rendering.** Chicago notes-bibliography, bibliography-entry form, for `book`, `article`,
`incollection`, `phdthesis` and `misc`. The exact templates are in the docstring of
`scripts/bibtex_chicago.py`. `chicago` is the plain string; `chicago_runs` is the same string split
into runs so the component can set titles in italics without interpreting markup.

- LaTeX in `.bib` fields is decoded to Unicode before rendering: accents (`{\'a}`, `\c{t}`, `\v{s}`),
  special letters (`\ss`, `\o`, `\l`), escaped characters, `--` and `---`, and `~`. Braces may nest to
  any depth. A command the decoder does not know, or math mode, is an error, not a guess.
- A double-braced author is a corporate name and is kept whole. `Family, Given`, `Given Family` and
  `Given von Family` are all read; a name that cannot be read is an error.
- Field names are read in any letter case; the same field twice in one entry is an error.
- A `doi` given as a `https://doi.org/` address or with a `doi:` prefix is reduced to the bare DOI.
- A missing field is left out; nothing is supplied in its place.
- A translator named only inside `note` is not extracted (rule 3); the note is shown beside the citation.
- An entry type outside the five is an error. A field the contract does not carry is left out and listed
  in the report. That includes `edition`, `translator`, `chapter` and `crossref`: an entry for a second
  edition is rendered without its edition, so read the report's list before relying on a citation.
- `and others` in a name list is rendered as "et al." and recorded as `authors_et_al: true` or
  `editors_et_al: true` beside the list in `fields`.
- Keys are compared without regard to case; two keys that differ only in case are an error.

### 2.6 Link

```
{ "person_id", "source_id",
  "relation": "about" | "by",
  "role"?: <roles id>,                      // "by" only, required there
  "basis"?: string,                         // "by" only: how the link was established
  "attribute_kinds"?: [ <attribute_kinds id> ],   // "about" only
  "evidence_ids"?: [ <evidence id> ] }             // "about" only
```

- **`about` links are computed by the exporter** from the evidence rows: one per (person, source), listing
  the attribute kinds and evidence rows that source supports. The project never supplies them.
- **`by` links are supplied by the project** (section 3). A person may have none; a source may link to
  several persons, and to one person in more than one role (one Link per role).

## 3. Input tables (what a project supplies)

All inputs sit in one directory. CSV files are UTF-8 with a header row; an empty cell means "absent".
A list inside a CSV cell is separated by `;`.

| File | Required | Columns or shape |
|---|---|---|
| `explorer.json` | yes | `{ "title", "notice"?, "vocab": {…2.1…}, "periods": [ …2.2… ] }` |
| `persons.csv` | yes | `id, kind, display_name, sort_name, aliases, period_id, period_year, year_basis` |
| `evidence.csv` | yes | `id, person_id, attribute_kind, value, tier, source_id, citation, locator, quote, url, access, via, audit`, then optionally any of `basis, reporter, note` |
| the `.bib` file | no | passed by path (`--bib`); a source id of `bibliography` origin is its BibTeX key |
| `works.csv` | no | `source_id, title, date, locator` — `work-title` sources |
| `links.csv` | no | `person_id, source_id, role, basis` — the `by` links |
| `codes.csv` | no | `person_id, key, label, value_label, established, basis, evidence_ids` |
| `bios.json` | no | `{ <person id>: Bio }` |
| `groups.json` | no | `{ <person id>: [ Group ] }` |
| `source_attributes.csv` | no | `source_id, label, value` — shown on the source in file order |
| `summaries.jsonl` | no | one per line: `{ "source_id", "text", "deemed_by", "basis", "verification_state", "read_url"?, "caveats"? }` |

**`evidence.csv` is one row per (person, attribute, value, evidence)**, which is the shape most
evidence tables already have. The exporter groups rows with the same `person_id`, `attribute_kind` and
exactly equal `value` into one AttributeValue. Cells are trimmed of surrounding white space, except
`quote`, which is kept exactly. An optional column that is absent reads as empty in every row, so a
file with only the thirteen required columns is valid. A row whose tier does not establish (for example a "not established"
tier that records what was searched) is kept and shown like any other.

**How an evidence row finds its source:**

- `source_id` set → it must name a `.bib` key or a `works.csv` row. `citation` may still be given and is
  then kept on the evidence row's source view as "cited as".
- `source_id` empty → `citation` is required. The exporter creates one `evidence-citation` source for
  each distinct, exactly equal (`citation`, `url`) pair and gives it a stable id derived from their hash.
  Two rows that differ by one character get two sources; the export report lists every source made this
  way, grouped by url, so near-duplicates are easy to spot and a project can assign explicit ids where
  it wants them merged.

A bibliography key that appears inside a free-text citation is not detected. The project's own mapping
puts the key in `source_id`.

A literature library (`literature.jsonl`, `docs/literature-library-protocol.md`) can be passed with
`--literature`, alone or beside `summaries.jsonl` (a source summarised in both is an error). Mapping,
version 1:

- only records with `relevance.source: "agent-authored"` become summaries; a seeded or other record is
  skipped, because a seeded text is a `.bib` note, not a summary;
- an agent-authored record with no `relevance.deemed_by` is also skipped: the library protocol records
  `deemed_by` only "where known", and a summary here must say who wrote it;
- every skipped record is listed in the report by key, with the reason;
- `key` → `source_id`; `relevance.summary` → `text`; `relevance.deemed_by` → `deemed_by`;
  `verification_state` → `verification_state`;
- `relevance.basis` → `basis`, or "record only" when absent; `relevance.read_url` → `read_url`;
  `relevance.caveats` → `caveats`. These three are optional additions a project may write into its
  records. The library protocol does not define them; its builder keeps them and its gate ignores them.

## 4. What the exporter checks

Errors (no output):

- an id that is malformed or duplicated; any reference that does not resolve (period, person, source,
  evidence, vocabulary id);
- a person without exactly one period; a `period_year` outside its period, or given for the
  unestablished period;
- periods that overlap or share an `order`; a period whose `start_year` is after its `end_year`; an
  open start on any period but the first, or an open end on any but the last; more than one
  unestablished period, or one that has years;
- an evidence row with neither `source_id` nor `citation`; an evidence row with a `reporter` and no
  `basis`; a URL that is not `http(s)`;
- a bio whose `text` differs from its joined clauses; a bio or summary without `verification_state`;
  a summary without `deemed_by` or `basis`;
- a code marked established with no evidence, or given twice for one person; an advisory group without
  a caveat;
- a `by` link without a role, or given twice; a `doi` that does not start with `10.` once a leading
  `https://doi.org/` or `doi:` is removed; a `.bib` entry of an unsupported type; a `.bib` entry that cannot be
  parsed or decoded;
- an evidence id used in a bio, code or group of a person it does not belong to;
- a CSV file with a missing or unknown column (an optional column of section 3 is not unknown), or with
  a column given twice; a JSON record with an unknown key.

Warnings (output written, listed in the report):

- a person with no attributes; a source with no link to any person; a `.bib` entry no row refers to;
- a `.bib` field the contract does not carry; a `.bib` entry with no title; a literature record that
  is skipped;
- each `evidence-citation` source created from free text.

A clean export means the file is **well-formed and internally consistent**. It does not mean any value,
quote, citation or summary is true.

## 5. The component (for orientation; specified separately)

A dependency-free ES module: `mount(element, data, options)` returns `{ show(target), destroy() }`.
Views: period list with counts → persons in a period, with a name filter, sortable by name or year,
each showing kind and year and marked when nothing about them is established → person (bio, attributes
with evidence, codes, groups, sources about, works by) → source (citation, summary or "No summary yet",
fields, links, note, attributes, linked persons with role). `options.onNavigate(target)` is called after
every navigation except the initial view, so the host can sync its own UI; the component itself does not touch the URL. Styling
is by CSS custom properties only, so it takes the host's light and dark tokens. It works at 390 px, by
keyboard, and inside a host tab panel. Details: `README.md` beside this file.

## 6. Settled in review (2026-11-18)

1. One evidence row is evidence for exactly one (person, attribute, value).
2. Values group by exact string equality; no value ids.
3. One evidence-citation source per exact (`citation`, `url`) pair; explicit `source_id` merges.
4. The Group shape holds a nested project record as rows with links; nothing nests deeper.

## 7. Changes in 1.1 (2026-11-20)

Additive; nothing in 1.0 is removed or changes meaning.

- `evidence.csv` may carry any of three more columns: `basis`, `reporter` and `note`. They become the Evidence fields of the same names (2.4) and are shown beside each
  piece of evidence.
- One new error: a `reporter` on a row with no `basis`.
- The exporter writes `schema_version` `1.1` whether or not the columns are present.

Compatibility: inputs written for 1.0 export unchanged apart from the version string. The component
checks only the major version, so a 1.0 component opens a 1.1 file, but it does not show the three new
fields, which breaks rule 5 for a file that has them. Take the exporter and the component from the same
commit (`FILES.sha256`).
