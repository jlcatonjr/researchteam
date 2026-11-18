# Bibliography explorer

A reusable view of a project's people and sources: pick a period, find a person, read a brief bio with the
attributes and evidence behind it, and open any source for its full citation, summary and other attributes.

It has two parts:

- **The exporter** (`scripts/build_bibliography_explorer.py`, with `scripts/bibtex_chicago.py`) reads a
  project's input tables and its `.bib` file, checks them, renders Chicago-style citations and writes one
  JSON file. Python standard library only.
- **The component** (`explorer.js`, `explorer.css`) displays that file. It is a dependency-free ES module
  with no build step.

The data shapes and the checks are in [`CONTRACT.md`](CONTRACT.md). This folder holds no project data: the
example under `example/` is invented.

## What a clean export means

The file is well-formed and internally consistent. It does not mean any value, quote, citation or summary
is true, and a rendered citation is not a check that the source exists. The component shows each item's
tier, basis and verification state so a reader can see what stands behind it.

## Try the example

```bash
python3 -m http.server 8000 --directory templates/bibliography-explorer
# then open http://localhost:8000/example/
```

To rebuild the example's data file from its inputs:

```bash
python3 scripts/build_bibliography_explorer.py templates/bibliography-explorer/example/inputs \
    --bib templates/bibliography-explorer/example/inputs/example.bib \
    --out templates/bibliography-explorer/example/explorer-data.json
```

## Use it in a project

1. **Vendor the files at a pinned commit.** Copy the five files listed in `FILES.sha256` into the project
   and record the researchteam commit they came from. The paths in the list are relative to the
   repository root, so in a checkout of that commit run
   `shasum -a 256 -c templates/bibliography-explorer/FILES.sha256` from the root; compare the hashes
   of the project's copies by hand.
   Pin a signed release tag's commit once a release contains this folder. `researchteam update` does not
   sync these files.
2. **Write the input tables** (CONTRACT.md, section 3) from the project's own data. This mapping is the
   project's code and stays in the project.
3. **Run the exporter.** It writes the data file, or stops with a list of errors and writes nothing. Read
   the report: it lists warnings and every source it made from a free-text citation, grouped by url.
4. **Mount the component.**

```html
<link rel="stylesheet" href="vendor/bibliography-explorer/explorer.css">
<div id="bibliography"></div>
<script type="module">
  import { mount } from "./vendor/bibliography-explorer/explorer.js";
  const data = await (await fetch("data/explorer-data.json")).json();
  const explorer = mount(document.getElementById("bibliography"), data, {
    headingLevel: 3,                       // the level of each view's heading (default 2)
    initial: { view: "periods" },          // where to start
    onNavigate: (target) => { /* sync the host's own state */ },
    labels: { filter: "Find an author" },  // override any text in DEFAULT_LABELS
  });
</script>
```

`mount` returns `{ show(target), destroy() }`. A target is one of:

| Target | Shows |
|---|---|
| `{ view: "periods" }` | the periods, each with its count |
| `{ view: "period", id }` | the people in a period, with a name filter and a sort by name or year |
| `{ view: "person", id }` | a person: bio, attributes with evidence, codes, groups, sources, works |
| `{ view: "source", id, person? }` | a source; `person` keeps that person in the breadcrumb |

`show` throws on a target that is not in the data. `onNavigate` is called after each navigation, but not
for the initial view. The component does not read or write the URL; a host that wants links to a view
keeps them itself with `onNavigate` and `show`.

## Styling

All rules are scoped under `.bibx` and take their colours from custom properties, whose defaults derive
from the inherited text colour, so the component follows a light or dark host without changes. To use a
host's tokens, set the properties:

```css
.bibx { --bibx-accent: var(--accent); --bibx-surface: var(--panel); --bibx-line: var(--rule); }
```

The properties are `--bibx-text`, `--bibx-muted`, `--bibx-line`, `--bibx-surface`, `--bibx-accent`,
`--bibx-yes`, `--bibx-no`, `--bibx-advisory`, `--bibx-radius` and `--bibx-gap`.

## Safety properties

- Every string from the data is inserted as a text node. The component never parses markup from the data.
- A link is made only for an `http://` or `https://` address; the exporter rejects any other.
- The component loads nothing: no network requests, no storage, no third-party code.

## Tests

`tests/test_bibliography_explorer.py` covers the LaTeX decoder, the name reader, the BibTeX parser, each
citation template, the exporter's checks, the example's currency and this folder's hash list. The
component was checked by hand in a browser against the example; the repository's CI has no JavaScript
runtime, so the tests check the component only for the static safety properties above.

After changing any of the five vendored files, rewrite the hash list from the repository root:

```bash
shasum -a 256 templates/bibliography-explorer/explorer.js templates/bibliography-explorer/explorer.css \
    templates/bibliography-explorer/CONTRACT.md scripts/build_bibliography_explorer.py \
    scripts/bibtex_chicago.py > templates/bibliography-explorer/FILES.sha256
```
