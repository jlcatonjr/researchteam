# Concept map

A reusable, interactive figure of a debate. It shows who held which view, who answered whom, and where the project's
findings stand. Clicking a claim lists every author tied to it, grouped by how they stand. Clicking a writer lists
that writer.

It has two parts, like the bibliography explorer beside it:

- **The exporter** (`scripts/build_concept_map.py`) reads one map spec. It checks the spec, writes the Graphviz DOT
  for the static figure, gets the layout from Graphviz and works out who each node ties to. It then writes one
  JSON map file. It uses the Python standard library only, plus Graphviz's `dot`.
- **The component** (`concept-map.js`, `concept-map.css`) draws that file and reports what is clicked. It is a
  dependency-free ES module with no build step. It lists no people itself. The host does that, in its own panel,
  so a map tab looks like the host's other drill-downs.

The data shapes and checks are in [`CONTRACT.md`](CONTRACT.md). The procedure around them (drafting, the
two-round independent audit, the second pass and the audit log) is in
[`docs/concept-map-protocol.md`](../../docs/concept-map-protocol.md). The example under `example/` is invented.

## What a clean build means

The map is well-formed and internally consistent. With `--registry`, each person id that is not in the register is
listed as a warning. Each line to or from a group node that does not yet say whom it speaks for is listed as a
REVIEW warning. Warnings do not stop the build, so read the report: a map is ready for audit only when it has no
REVIEW line and no unexplained unregistered person. A clean build does not mean any label, line or attribution is
true. That is what the protocol's audit is for.

## Try the example

```bash
python3 -m http.server 8000 --directory templates/concept-map
# then open http://localhost:8000/example/
```

To rebuild the example's files from its spec (needs Graphviz):

```bash
python3 scripts/build_concept_map.py templates/concept-map/example/spec.json \
    --out templates/concept-map/example/map-data.json \
    --dot templates/concept-map/example/map.dot --svg templates/concept-map/example/map.svg
```

The example leaves one group line (`F_date -> chron`) unjudged on purpose, so its report shows a REVIEW warning.

## Use it in a project

1. **Vendor the files at a pinned commit.** Copy the four files listed in `FILES.sha256` into the project, and
   record the researchteam commit they came from. The paths in the list are relative to the repository root, so
   in a checkout of that commit run `shasum -a 256 -c templates/concept-map/FILES.sha256` from the root. Take the
   exporter and the component from the same commit. Pin a signed release tag's commit once a release contains
   this folder. `researchteam update` does not sync these files.
2. **Write the spec** (CONTRACT.md, section 3) by following the protocol. The spec is the project's file; keep it
   beside the figure (for example `figures/<map>.json`).
3. **Build it** with the project's person register: `--registry` takes a bibliography-explorer file. The build
   writes the map file, the DOT and the SVG, or stops with a list of errors and writes nothing. Read the report,
   and judge every REVIEW line.
4. **Mount the component** and list the people in the host's own panel:

```html
<link rel="stylesheet" href="vendor/concept-map/concept-map.css">
<div id="map"></div>
<script type="module">
  import { mount, membersByRelation } from "./vendor/concept-map/concept-map.js";
  const data = await (await fetch("concept-map-data.json")).json();
  const map = mount(document.getElementById("map"), data, {
    onSelect: (s) => {
      if (!s) return panel.clear();
      if (s.role === "actor") return panel.list(s.node, [{ label: "", people: s.persons }]);
      panel.list(s.node, membersByRelation(data, s.node.id).map((g) => ({ label: g.label, people: g.members.map((m) => m.person) })));
    },
    labels: { fit: "Fit to width" },    // override any text in DEFAULT_LABELS
    fit: true,                          // start fitted to the width (default); false starts at actual size
  });
</script>
```

`mount` returns `{ el, selected, select(id | null), destroy() }`. `select` from code also calls `onSelect`;
`options.initial` marks a node selected without calling it. Each person has `key`, `name`, `registered`, and `id`
when it has one, so a host can open its own record for that person (the first integrating project opens the bibliography explorer).
Each member also has `relation`, `active` and `via` (the edges and boxes the tie comes through). The host can show
those beside the name.

## Styling

All rules are scoped under `.cmap`. Colours come from custom properties, whose defaults derive from the inherited
text colour, so the component follows a light or dark host without changes. Node fills come from the data and are
expected to be pale, so node text is set in `--cmap-node-ink`. To use a host's tokens:

```css
.cmap { --cmap-text: var(--text-primary); --cmap-muted: var(--text-muted); --cmap-line: var(--grid);
        --cmap-surface: var(--surface-1); --cmap-accent: var(--series-1); }
```

The properties are `--cmap-text`, `--cmap-muted`, `--cmap-line`, `--cmap-surface`, `--cmap-accent`, `--cmap-ink`
(lines drawn in the keyword `ink`), `--cmap-node-ink` and `--cmap-radius`.

## Safety properties

- Every string from the data is inserted as a text node or an attribute value. The component never parses markup
  from the data. The legend in the static DOT is an HTML-like Graphviz label, so the exporter escapes it.
- A colour is used only when it is `#rrggbb`. The exporter refuses any other value, and the component falls back
  to the host's ink.
- The component loads nothing: no network requests, no storage, no third-party code. The host fetches the map file.

## Tests

`tests/test_concept_map.py` covers the exporter's checks, membership (with direction, `only` and repeated persons),
the DOT and its escaping, fail-closed output, determinism, the example's currency, the component's static safety
properties and this folder's hash list. `templates/concept-map/tests/component.test.mjs` runs the component in Node
against a minimal DOM shim. It checks drawing, selection by click and keyboard, the `onSelect` payload, Escape,
`select()`, the schema guard and text-only rendering. The Graphviz tests skip when `dot` is not installed, and the
Node test when `node` is not. **The repository's CI installs neither, so in CI those tests are skipped.** No test
runs a browser. Check layout, theming and phone width by hand in one before relying on a change.

After changing any of the four vendored files, rewrite the hash list from the repository root:

```bash
shasum -a 256 templates/concept-map/concept-map.js templates/concept-map/concept-map.css \
    templates/concept-map/CONTRACT.md scripts/build_concept_map.py > templates/concept-map/FILES.sha256
```
