#!/usr/bin/env python3
"""Generate bibliography.bib and each deliverable's reference list from sources.json.

One record per source keeps the .bib and the end-of-document reference lists from drifting apart
(citation-claim audit, Dimension A). Run from anywhere:

    python3 Projects/CodedTermIndexing/references/build_references.py

A deliverable gets an entry for every source whose in-text label it uses, written under its
"## References" heading (everything after that heading is replaced).
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
SOURCES = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))
ORDER = ["author", "editor", "title", "booktitle", "journal", "series", "year", "volume", "number",
         "pages", "edition", "publisher", "address", "organization", "howpublished", "doi", "url", "note"]


def link(src):
    return src.get("url") or "https://doi.org/" + src["doi"]


def bib_entry(src):
    fields = dict(src["bib"])
    fields["year"] = str(src["year"])
    if src.get("doi"):
        fields["doi"] = src["doi"]
    fields["url"] = link(src)
    notes = [n for n in (fields.get("note"), "Access level: " + src["access"]) if n]
    fields["note"] = ". ".join(notes)
    keys = [k for k in ORDER if k in fields] + sorted(k for k in fields if k not in ORDER)
    width = max(len(k) for k in keys)
    body = ",\n".join(f"  {k.ljust(width)} = {{{fields[k]}}}" for k in keys)
    return f"@{src['type']}{{{src['key']},\n{body}\n}}"


def uses(text, label):
    """True when the text cites the label, as 'Label Year' or narrative 'Label (Year)'."""
    name, year = label.rsplit(" ", 1)
    flat = re.sub(r"\s+", " ", text)  # deliverables are hard-wrapped; a label may span a line break
    return re.search(rf"{re.escape(name)},? \(?{year}\b", flat) is not None


def write_bib():
    head = ("% bibliography.bib — CodedTermIndexing project\n"
            "% GENERATED from sources.json by build_references.py. Edit sources.json, then rebuild.\n"
            "% Chicago author-date compatible records. Every record carries a source link and the\n"
            "% access level reached when it was read (full text, abstract only, description only).\n\n")
    entries = sorted(SOURCES, key=lambda s: s["key"].lower())
    (HERE / "bibliography.bib").write_text(head + "\n\n".join(bib_entry(s) for s in entries) + "\n",
                                           encoding="utf-8")


def write_reference_lists():
    for path in sorted(PROJECT.glob("0[1-9]-*.md")):
        text = path.read_text(encoding="utf-8")
        marker = "\n## References\n"
        if marker not in text:
            continue
        body = text.split(marker)[0]
        cited = [s for s in SOURCES if uses(body, s["label"])]
        cited.sort(key=lambda s: s["chicago"].lower())
        lines = [" ".join([s["chicago"], link(s)] + s.get("also", [])) for s in cited]
        path.write_text(body + marker + "\n" + "\n\n".join(lines) + "\n", encoding="utf-8")
        print(f"{path.name}: {len(cited)} references")


if __name__ == "__main__":
    labels = [s["label"] for s in SOURCES]
    keys = [s["key"] for s in SOURCES]
    assert len(set(keys)) == len(keys), "duplicate key"
    assert len(set(labels)) == len(labels), "duplicate label"
    write_bib()
    write_reference_lists()
    print(f"bibliography.bib: {len(SOURCES)} records")
