# Concept map: data contract

**Status:** draft, written with the first integrating project (a derived project's reception map) on
2026-11-23. Schema ids `researchteam.concept-map-spec` (input) and `researchteam.concept-map` (output), version
`1.0`. The exporter is `scripts/build_concept_map.py`; the component is `concept-map.js` beside this file. The
procedure that produces and audits a map is `docs/concept-map-protocol.md`.

A concept map shows how views of a question developed, divided and converged: **actors** (a writer, or a group of
writers) joined by typed lines to **topics** (a claim in contention, or a finding of the project), and to each other.
A project writes one *spec* (section 3). The exporter checks it, writes the Graphviz DOT for the static figure, asks
Graphviz for the layout, works out who each node ties to, and writes one *map file* (section 2). The component draws
the map file and reports what the reader clicks; the host page lists the people. The component knows nothing about
any study.

## 1. Rules that hold everywhere

1. **The exporter is the only writer of the map file, the DOT and the SVG.** Do not edit them; edit the spec and
   rebuild. The same spec, registry and Graphviz version give byte-identical files. The map file carries no
   timestamp; it carries the SHA-256 of each input and the Graphviz version.
2. **Fail closed.** Any violation of section 4 stops the build with a non-zero exit and no map file, DOT or
   SVG (the report is still written). Files left at the
   output paths by an earlier build are removed, so they cannot pass for this one. Only files the exporter (or
   Graphviz, for the SVG) wrote are removed; any other file at an output path is left and named in the report. An
   output path that names the spec, the registry or another output is refused before anything is read.
3. **Nothing is inferred.** The exporter does not match names to people, guess who a group stands for, or decide what
   a line means. A person is tied to a node only by an id (or an explicit unregistered entry) in the spec, and to a
   topic only through an edge the spec draws.
4. **Who a topic ties to is computed, never supplied.** A topic's `members` are the persons of every actor node an
   edge joins to it (section 2.4). The spec cannot list them by hand, so the map and its lists cannot drift apart.
5. **Text is text.** Every string is shown as plain text. The component never interprets HTML or Markdown from the
   data. Colours must be `#rrggbb` or the keyword `ink` (the host's text colour).
6. **Labels come from the data.** Kind, fill, relation and band names are in the spec's vocabularies. The component
   has no domain words of its own beyond its controls, which the host can override.
7. **Ids** match `^[A-Za-z0-9][A-Za-z0-9._:-]*$` and are unique within their list. Node ids and band ids share one
   name space.
8. **A clean build means well-formed and internally consistent.** It does not mean any label, line, date or
   attribution is true. That is what the protocol's audit is for.

## 2. The map file (output)

One JSON file, UTF-8, keys sorted. Coordinates are in points, origin top left, y downwards (Graphviz's layout,
flipped). Optional fields marked `?` are omitted when absent.

```
{
  "schema": "researchteam.concept-map", "schema_version": "1.0",
  "meta": {
    "title", "subtitle"?, "notice"?, "status"?, "audit"?, "legend_note"?,
    "map_id", "exporter", "layout_engine",          // e.g. "graphviz 14.0.5"
    "font": { "family", "node_size", "edge_size", "band_size" },
    "inputs": [ { "name", "sha256" } ],             // the spec, and the registry when given
    "counts": { "nodes", "topics", "edges", "persons" },
    "registry": bool                                // true: person ids were checked against a register
  },
  "vocab": { "node_kinds": [...], "fills": [...], "relations": [...] },   // as in the spec (3.1)
  "canvas": { "width", "height", "unit": "pt" },
  "bands": [ { "id", "label", "x"?, "y"? } ],
  "nodes": [ Node ],
  "edges": [ Edge ]
}
```

### 2.1 Node

```
{ "id", "kind", "fill", "label_lines": [ string ], "x", "y", "w", "h",     // centre and size
  "band"?, "emphasis"?: 1 | 2, "note"?, "basis"?: [ string ],
  "persons"?: [ Person ],          // actor nodes only
  "members"?: [ Member ],          // topic nodes only (2.4)
  "related": [ Tie ] }             // every edge that is not counted in members
```

### 2.2 Person

```
{ "key",                           // "id:<person id>" or "name:<name>"; unique on the map
  "id"?, "name", "registered": bool, "note"? }
```

`registered` is true when the id was checked against a registry (`--registry`). An unregistered person has no id;
`note` says why (the spec's `unregistered` text). A host shows such a person by name only.

### 2.3 Edge

```
{ "id": "e<n>",                    // n = the edge's position in the spec
  "from", "to", "relation",
  "path": [ [x, y] ],              // cubic Bézier: a start point, then three points per segment
  "tip"?: [x, y],                  // where the arrowhead (or tee) ends
  "tail"?: [x, y],
  "label_lines"?, "label_at"?: [x, y],
  "emphasis"?, "basis"?,
  "only"?: [ person key ] }        // the subset of the actor end's persons the edge holds for (3.4)
```

### 2.4 Members and ties

For each topic node, the exporter walks every edge that joins it to an actor node and records each person of that
actor, honouring the edge's `only`:

```
Member = { "person": Person, "relation", "active": bool, "via": [ { "edge", "node" } ] }
Tie    = { "edge", "node", "relation", "outgoing": bool }
```

- One Member per (person, relation, direction). `active` is true when the actor is the edge's tail: the person
  *affirms*, *denies*, ... the topic. It is false when the topic is the tail: the person is *affirmed by*,
  *rebutted by*, ... the topic, which the relation's `passive_label` names. `via` lists every edge and actor node
  the tie comes through, so a person in two boxes with the same relation appears once with both.
- Members are sorted by relation (vocabulary order), active before passive, then by name.
- An edge between two topics, or between two actors, is a Tie on both of its nodes, never a Member. An actor node's
  edges are all Ties: its own list is its `persons`.

## 3. The spec (input)

One JSON file. Unknown keys are errors.

```
{
  "schema": "researchteam.concept-map-spec", "schema_version": "1.0",
  "id", "title", "subtitle"?, "notice"?, "status"?, "audit"?, "legend_note"?,
  "layout"?: { "rankdir"?: "TB" | "LR", "nodesep"?, "ranksep"?, "fontname"?, "fontsize"? },
  "vocab": { "node_kinds": [...], "fills": [...], "relations": [...] },
  "bands"?: [ { "id", "label" } ],                 // ordered; a newline in a label is a line break
  "nodes": [ ... ],
  "edges": [ ... ]
}
```

### 3.1 Vocabularies

```
node_kinds: { "id", "label", "shape": "box" | "ellipse" | "octagon",
              "role": "actor" | "topic", "fill"?: <fills id>, "description"? }
fills:      { "id", "label", "color": "#rrggbb", "legend"?: bool }       // legend: false hides it from the legend
relations:  { "id", "label", "passive_label"?, "stroke": "#rrggbb" | "ink",
              "style"?: "solid" | "dotted" | "dashed", "head"?: "normal" | "tee" | "none",
              "width"?: number in (0, 6], "inferred"?: bool, "description"? }
```

`label` reads from the tail ("affirms"); `passive_label` from the head ("affirmed by"). Give `passive_label` for any
relation that can run from a topic to an actor; without it the component shows "<label> (reverse)". Mark a relation
`inferred: true` when its lines record no documented influence; hosts show such ties apart.

### 3.2 Nodes

```
{ "id", "kind": <node_kinds id>, "label": string,     // "\n" breaks lines
  "band"?: <bands id>,          // required when the spec has bands
  "fill"?: <fills id>,          // required when the kind has no fill
  "emphasis"?: 1 | 2,           // a heavier outline
  "persons"?: [ PersonRef ],    // required on an actor node, refused on a topic
  "basis"?: [ string ],         // where the node is grounded, e.g. "01 §3", "attribution row B2:..."
  "note"? }

PersonRef = { "id", "name"? }                              // name is required when no registry is given
          | { "name", "unregistered": <why not in the register> }
```

A group node lists every person its label names. When the project has a person register, pass it with
`--registry` (a bibliography-explorer file, `templates/bibliography-explorer/CONTRACT.md`): every id is then checked
and the register's display name is used. A `name` given in the spec is then only a check: if it differs from the
register's, the report says so. A person with no entry is listed with `unregistered` and a reason, and appears in
the build report. An id may not start with `name:`, the prefix that marks unregistered persons in `only`.

### 3.3 Bands

Bands are the rows of the layout (in `rankdir: TB`), usually periods. Each node sits in one band. The DOT chains the
band labels in order with invisible edges and ranks each band's nodes with its label, so Graphviz sets the labels as
a column (it chooses the side). The legend is ranked with the last band.

### 3.4 Edges

```
{ "from", "to", "relation", "label"?, "emphasis"?: 1 | 2, "basis"?: [ string ],
  "only"?: [ person id | "name:<name>" ],      // the subset of the actor end's persons this edge holds for
  "all_members"?: true }                       // reviewed: the edge holds for every person of its group node
```

A line from a group box speaks for every person in the box unless it says otherwise. When the line's label (or the
evidence) speaks for some of them, name them in `only`. When it has been checked and holds for all of them, mark it
`all_members: true`. Until one or the other is given, the build report lists the edge under REVIEW, so a group edge
cannot pass unexamined.

## 4. What the exporter checks

Errors (no output):

- an output path that names the spec, the registry or another output (refused before anything is read);
- an unknown key anywhere; a wrong or missing `schema`, or a different major `schema_version`;
- an id that is malformed or duplicated, or a node id that is also a band id; any reference that does not resolve
  (kind, fill, band, relation, node);
- a vocabulary that is empty, a kind with a bad `shape` or `role`, no kind with role `actor`, a colour that is not
  `#rrggbb` (or `ink` for a stroke), a bad `style`, `head` or `width`;
- a node without `band` when the spec has bands; a node with no fill from itself or its kind; an empty label;
- an actor node without `persons`, or a topic node with them; a person id not in the registry; a person with
  neither id nor `unregistered`, or with both; a person listed twice in one node; with no registry, a person id
  without a name; a person id starting with `name:`;
- a value of the wrong type anywhere (for example a list where an id belongs, or a non-string `fontname`); a
  registry that is not a bibliography-explorer file with a `persons` list;
- an edge from a node to itself; the same (from, to, relation) twice;
- `only` on an edge that does not have exactly one actor end, naming a person who is not in that node, naming a
  person twice, or naming all of them; `all_members` that is not `true`, or given with `only`;
- Graphviz missing, failing, or returning no geometry for a node or edge.

Warnings (output written, listed in the report):

- each unregistered person;
- a person whose `name` in the spec differs from the registry's;
- REVIEW: each edge between a group node (an actor node with more than one person) and a topic, in either
  direction, with neither `only` nor `all_members`. An edge between two actor nodes is never listed;
- a node no edge touches; a band with no node.

## 5. The component (for orientation)

`mount(element, data, options)` returns `{ el, selected, select(id | null), destroy() }`. It draws the bands, the
edges (each with its arrowhead or tee and its label) and the nodes, with a legend built from the vocabularies, a
"Fit to width / Actual size" toggle and a scrolling frame. A node is a focusable button: click, Enter or Space
selects it; selecting it again or Escape clears. The selected node and its edges stay at full strength and the rest
fade. `options.onSelect(selection | null)` is called on every selection or clear, from the reader or from
`select()`; `options.initial` marks a node selected without calling it.

```
selection = { node, kind, role: "actor" | "topic", related,
              persons?,        // role "actor": the node's persons
              members? }       // role "topic": its members (2.4)
```

`membersByRelation(data, nodeId)` returns a topic's members grouped by relation and direction, in vocabulary order,
each group with its label ("affirms", or "affirmed by this node"), for hosts that list them. `passive(relation)`
returns the passive label. The component lists no people itself: the host does, in its own panel and with its own
person items, so a map tab looks like the host's other drill-downs. Styling is by CSS custom properties only (`README.md`).
