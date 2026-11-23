#!/usr/bin/env python3
"""Build a concept map: who holds, affirms or denies which position, and how views developed.

Reads one map spec (templates/concept-map/CONTRACT.md, section 3), checks it, writes the Graphviz DOT for
the static figure, asks Graphviz (`dot`) for the layout and writes one map file (section 2) that the
component (templates/concept-map/concept-map.js) displays. Python standard library only; Graphviz is
the one external program, and only this exporter runs it.

    python3 scripts/build_concept_map.py SPEC.json --out map-data.json \
        [--registry explorer-data.json] [--dot map.dot] [--svg map.svg] [--report report.txt] \
        [--dot-bin dot]

`--dot-bin` defaults to the environment variable CONCEPT_MAP_DOT, else `dot`.

Fail closed: any error stops the build with exit status 1, lists every error, writes nothing and removes
any file an earlier build left at an output path. It removes only files this exporter (or Graphviz, for the
SVG) wrote: any other file found at an output path is left in place and named in the report. An output path
that names the spec, the registry or another output is refused before anything is read or removed. A clean build means the map is well-formed and
internally consistent. It does not mean any label, link or attribution is true.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

EXPORTER_NAME = "researchteam-concept-map-exporter"
EXPORTER = EXPORTER_NAME + " 1.0"
SCHEMA = "researchteam.concept-map"
SPEC_SCHEMA = "researchteam.concept-map-spec"
SCHEMA_VERSION = "1.0"
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
SHAPES = {"box": "box", "ellipse": "ellipse", "octagon": "doubleoctagon"}
SHAPE_NAMES = {"box": "box", "ellipse": "ellipse", "octagon": "double octagon"}   # as drawn, for the legends
ROLES = {"actor", "topic"}
HEADS = {"normal", "tee", "none"}
STYLES = {"solid", "dotted", "dashed"}
INK_DOT = "#333333"           # what the stroke keyword "ink" becomes in the static figure

SPEC_KEYS = {"schema", "schema_version", "id", "title", "subtitle", "notice", "status", "audit", "layout",
             "vocab", "bands", "nodes", "edges", "legend_note"}
LAYOUT_KEYS = {"rankdir", "nodesep", "ranksep", "fontname", "fontsize"}
VOCAB_KEYS = {"node_kinds", "fills", "relations"}
KIND_KEYS = {"id", "label", "shape", "role", "fill", "description"}
FILL_KEYS = {"id", "label", "color", "legend"}
REL_KEYS = {"id", "label", "passive_label", "stroke", "style", "head", "width", "inferred", "description"}
BAND_KEYS = {"id", "label"}
NODE_KEYS = {"id", "kind", "band", "label", "fill", "emphasis", "persons", "basis", "note"}
PERSON_KEYS = {"id", "name", "unregistered"}
EDGE_KEYS = {"from", "to", "relation", "label", "emphasis", "basis", "only", "all_members"}


def person_key(p: dict) -> str:
    """The key a person reference is known by: its id, or its name when it is marked unregistered."""
    return p["id"] if "id" in p else "name:" + str(p.get("name"))


class SpecError(Exception):
    pass


def _k(v):
    """A value usable as a lookup key: the string itself, or None for anything else (lists, objects, numbers)."""
    return v if isinstance(v, str) else None


# --------------------------------------------------------------------------- reading and checking
def _unknown(errs, where, obj, allowed):
    if not isinstance(obj, dict):
        errs.append(f"{where}: must be an object")
        return False
    extra = sorted(set(obj) - allowed)
    if extra:
        errs.append(f"{where}: unknown key(s) {', '.join(extra)}")
    return True


def _text(errs, where, v, required=True):
    if v is None:
        if required:
            errs.append(f"{where}: required")
        return
    if not isinstance(v, str) or not v.strip():
        errs.append(f"{where}: must be a non-empty string")


def _ident(errs, where, v, seen=None):
    if not isinstance(v, str) or not ID_RE.match(v):
        errs.append(f"{where}: id {v!r} does not match {ID_RE.pattern}")
        return
    if seen is not None:
        if v in seen:
            errs.append(f"{where}: id {v!r} is duplicated")
        seen.add(v)


def load_registry(path: Path, errs: list) -> dict:
    """Person ids and names from a bibliography-explorer file (persons[].id, persons[].display_name)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        errs.append(f"registry {path.name}: cannot be read ({type(e).__name__})")
        return {}
    if not isinstance(data, dict) or data.get("schema") != "researchteam.bibliography-explorer":
        errs.append(f"registry {path.name}: not a researchteam.bibliography-explorer file")
        return {}
    persons = data.get("persons") if isinstance(data, dict) else None
    if not isinstance(persons, list):
        errs.append(f"registry {path.name}: has no persons list")
        return {}
    return {p["id"]: str(p.get("display_name") or p["id"]) for p in persons
            if isinstance(p, dict) and isinstance(p.get("id"), str)}


def check_spec(spec: dict, registry: dict | None) -> tuple[list, list]:
    """Return (errors, warnings). The spec is not changed."""
    errs: list[str] = []
    warns: list[str] = []
    if not _unknown(errs, "spec", spec, SPEC_KEYS):
        return errs, warns
    if spec.get("schema") != SPEC_SCHEMA:
        errs.append(f"spec.schema: must be {SPEC_SCHEMA!r}")
    if str(spec.get("schema_version", "")).split(".")[0] != SCHEMA_VERSION.split(".")[0]:
        errs.append(f"spec.schema_version: major version must be {SCHEMA_VERSION.split('.')[0]}")
    _ident(errs, "spec.id", spec.get("id"))
    _text(errs, "spec.title", spec.get("title"))
    for k in ("subtitle", "notice", "status", "audit", "legend_note"):
        _text(errs, f"spec.{k}", spec.get(k), required=False)
    lay = spec.get("layout", {})
    if _unknown(errs, "spec.layout", lay, LAYOUT_KEYS):
        if lay.get("rankdir", "TB") not in ("TB", "LR"):
            errs.append("spec.layout.rankdir: must be TB or LR")
        for k in ("nodesep", "ranksep", "fontsize"):
            if k in lay and not (isinstance(lay[k], (int, float)) and not isinstance(lay[k], bool) and lay[k] > 0):
                errs.append(f"spec.layout.{k}: must be a positive number")
        _text(errs, "spec.layout.fontname", lay.get("fontname"), required=False)

    vocab = spec.get("vocab")
    kinds, fills, rels = {}, {}, {}
    if _unknown(errs, "spec.vocab", vocab, VOCAB_KEYS):
        seen = set()
        for i, f in enumerate(vocab.get("fills") or []):
            w = f"vocab.fills[{i}]"
            if _unknown(errs, w, f, FILL_KEYS):
                _ident(errs, w, f.get("id"), seen)
                _text(errs, f"{w}.label", f.get("label"))
                if not (isinstance(f.get("color"), str) and COLOR_RE.match(f["color"])):
                    errs.append(f"{w}.color: must be #rrggbb")
                if "legend" in f and not isinstance(f["legend"], bool):
                    errs.append(f"{w}.legend: must be true or false")
                fills[f.get("id")] = f
        seen = set()
        for i, k in enumerate(vocab.get("node_kinds") or []):
            w = f"vocab.node_kinds[{i}]"
            if _unknown(errs, w, k, KIND_KEYS):
                _ident(errs, w, k.get("id"), seen)
                _text(errs, f"{w}.label", k.get("label"))
                if k.get("shape") not in SHAPES:
                    errs.append(f"{w}.shape: must be one of {', '.join(sorted(SHAPES))}")
                if k.get("role") not in ROLES:
                    errs.append(f"{w}.role: must be actor or topic")
                if k.get("fill") is not None and _k(k.get("fill")) not in fills:
                    errs.append(f"{w}.fill: {k.get('fill')!r} is not a fills id")
                kinds[k.get("id")] = k
        seen = set()
        for i, r in enumerate(vocab.get("relations") or []):
            w = f"vocab.relations[{i}]"
            if _unknown(errs, w, r, REL_KEYS):
                _ident(errs, w, r.get("id"), seen)
                _text(errs, f"{w}.label", r.get("label"))
                _text(errs, f"{w}.passive_label", r.get("passive_label"), required=False)
                st = r.get("stroke")
                if not (st == "ink" or (isinstance(st, str) and COLOR_RE.match(st))):
                    errs.append(f"{w}.stroke: must be #rrggbb or \"ink\"")
                if r.get("style", "solid") not in STYLES:
                    errs.append(f"{w}.style: must be one of {', '.join(sorted(STYLES))}")
                if r.get("head", "normal") not in HEADS:
                    errs.append(f"{w}.head: must be one of {', '.join(sorted(HEADS))}")
                if "width" in r and not (isinstance(r["width"], (int, float)) and not isinstance(r["width"], bool)
                                         and 0 < r["width"] <= 6):
                    errs.append(f"{w}.width: must be a number in (0, 6]")
                if "inferred" in r and not isinstance(r["inferred"], bool):
                    errs.append(f"{w}.inferred: must be true or false")
                rels[r.get("id")] = r
        for name, d in (("node_kinds", kinds), ("fills", fills), ("relations", rels)):
            if not d:
                errs.append(f"vocab.{name}: at least one entry is required")
        if kinds and not any(k.get("role") == "actor" for k in kinds.values()):
            errs.append("vocab.node_kinds: no kind has role actor")

    bands, seen = [], set()
    for i, b in enumerate(spec.get("bands") or []):
        w = f"bands[{i}]"
        if _unknown(errs, w, b, BAND_KEYS):
            _ident(errs, w, b.get("id"), seen)
            _text(errs, f"{w}.label", b.get("label"))
            bands.append(b.get("id"))

    nodes, seen = {}, set()
    for i, n in enumerate(spec.get("nodes") or []):
        w = f"nodes[{i}]"
        if not _unknown(errs, w, n, NODE_KEYS):
            continue
        _ident(errs, w, n.get("id"), seen)
        w = f"node {n.get('id')!r}"
        if n.get("id") in bands:
            errs.append(f"{w}: id is also a band id")
        kind = kinds.get(_k(n.get("kind")))
        if kind is None:
            errs.append(f"{w}.kind: {n.get('kind')!r} is not a node_kinds id")
        if "band" in n and _k(n["band"]) not in bands:
            errs.append(f"{w}.band: {n['band']!r} is not a bands id")
        if bands and "band" not in n:
            errs.append(f"{w}.band: required when the spec has bands")
        if not isinstance(n.get("label"), str) or not n["label"].strip():
            errs.append(f"{w}.label: must be a non-empty string")
        if "fill" in n and _k(n["fill"]) not in fills:
            errs.append(f"{w}.fill: {n['fill']!r} is not a fills id")
        if kind is not None and "fill" not in n and kind.get("fill") is None:
            errs.append(f"{w}.fill: required (its kind sets no fill)")
        if "emphasis" in n and (isinstance(n["emphasis"], bool) or n["emphasis"] not in (1, 2)):
            errs.append(f"{w}.emphasis: must be 1 or 2")
        for k in ("basis",):
            if k in n and not (isinstance(n[k], list) and all(isinstance(x, str) and x.strip() for x in n[k])):
                errs.append(f"{w}.{k}: must be a list of non-empty strings")
        _text(errs, f"{w}.note", n.get("note"), required=False)
        persons = n.get("persons")
        if persons is not None:
            if kind is not None and kind.get("role") != "actor":
                errs.append(f"{w}.persons: only actor nodes carry persons (kind {kind.get('id')!r} is a topic)")
            if not isinstance(persons, list) or not persons:
                errs.append(f"{w}.persons: must be a non-empty list")
                persons = []
            pseen = set()
            for j, p in enumerate(persons):
                pw = f"{w}.persons[{j}]"
                if not _unknown(errs, pw, p, PERSON_KEYS):
                    continue
                if "id" in p:
                    if "unregistered" in p:
                        errs.append(f"{pw}: give an id or mark unregistered, not both")
                    _ident(errs, pw, p["id"], pseen)
                    if isinstance(p["id"], str) and p["id"].startswith("name:"):
                        errs.append(f"{pw}: an id may not start with 'name:' (that prefix marks unregistered persons)")
                    if registry is not None and _k(p.get("id")) not in registry:
                        errs.append(f"{pw}: person id {p.get('id')!r} is not in the registry")
                    elif registry is not None and "name" in p and p["name"] != registry[p["id"]]:
                        warns.append(f"{w}: {p['id']!r} is named {p['name']!r} in the spec but "
                                     f"{registry[p['id']]!r} in the registry; the registry's name is used")
                    if registry is None and "name" not in p:
                        errs.append(f"{pw}: name is required when no registry is given")
                    if "name" in p:
                        _text(errs, f"{pw}.name", p["name"])
                else:
                    _text(errs, f"{pw}.name", p.get("name"))
                    _text(errs, f"{pw}.unregistered", p.get("unregistered"))
                    key = "name:" + str(p.get("name"))
                    if key in pseen:
                        errs.append(f"{pw}: {p.get('name')!r} is listed twice")
                    pseen.add(key)
                    warns.append(f"{w}: {p.get('name')!r} is not in the person register ({p.get('unregistered')})")
        elif kind is not None and kind.get("role") == "actor":
            errs.append(f"{w}.persons: an actor node must list its persons (or mark each one unregistered)")
        nodes[n.get("id")] = n

    seen_pairs = set()
    for i, e in enumerate(spec.get("edges") or []):
        w = f"edges[{i}]"
        if not _unknown(errs, w, e, EDGE_KEYS):
            continue
        for end in ("from", "to"):
            if _k(e.get(end)) not in nodes:
                errs.append(f"{w}.{end}: {e.get(end)!r} is not a node id")
        if e.get("from") == e.get("to"):
            errs.append(f"{w}: an edge may not join a node to itself")
        if _k(e.get("relation")) not in rels:
            errs.append(f"{w}.relation: {e.get('relation')!r} is not a relations id")
        if "label" in e and (not isinstance(e["label"], str) or not e["label"].strip()):
            errs.append(f"{w}.label: must be a non-empty string")
        if "emphasis" in e and (isinstance(e["emphasis"], bool) or e["emphasis"] not in (1, 2)):
            errs.append(f"{w}.emphasis: must be 1 or 2")
        if "basis" in e and not (isinstance(e["basis"], list) and all(isinstance(x, str) and x.strip() for x in e["basis"])):
            errs.append(f"{w}.basis: must be a list of non-empty strings")
        ends = [nodes.get(_k(e.get("from"))), nodes.get(_k(e.get("to")))]
        actors = [x for x in ends if x is not None and kinds.get(x.get("kind"), {}).get("role") == "actor"]
        if "all_members" in e and (e["all_members"] is not True or "only" in e or len(actors) != 1):
            errs.append(f"{w}.all_members: must be true, on an edge with one actor end and no `only`")
        if "only" in e:
            # `only` names the persons of the edge's actor end that the edge holds for (a group node whose
            # label or edge label speaks for some of its members, not all).
            if len(actors) != 1:
                errs.append(f"{w}.only: allowed only on an edge with exactly one actor end")
            elif not (isinstance(e["only"], list) and e["only"] and all(isinstance(x, str) for x in e["only"])):
                errs.append(f"{w}.only: must be a non-empty list of person ids (or 'name:<name>' for unregistered)")
            else:
                keys = [person_key(p) for p in actors[0].get("persons") or [] if isinstance(p, dict)]
                for x in e["only"]:
                    if x not in keys:
                        errs.append(f"{w}.only: {x!r} is not a person of node {actors[0].get('id')!r}")
                if len(set(e["only"])) != len(e["only"]):
                    errs.append(f"{w}.only: a person is listed twice")
                if set(e["only"]) == set(keys):
                    errs.append(f"{w}.only: names every person of {actors[0].get('id')!r}; leave it out")
        elif (len(actors) == 1 and isinstance(actors[0].get("persons"), list) and len(actors[0]["persons"]) > 1
              and e.get("all_members") is not True):
            warns.append(f"REVIEW edge {e.get('from')} -> {e.get('to')} ({e.get('relation')}"
                         f"{', ' + repr(e['label'].replace(chr(10), ' ')) if e.get('label') else ''}): holds for all "
                         f"{len(actors[0]['persons'])} persons of {actors[0].get('id')!r}; give `only` if it speaks for fewer")
        pair = (_k(e.get("from")), _k(e.get("to")), _k(e.get("relation")))
        if pair in seen_pairs:
            errs.append(f"{w}: the same (from, to, relation) is given twice")
        seen_pairs.add(pair)
    if not nodes:
        errs.append("nodes: at least one node is required")
    edges_list = [e for e in spec.get("edges") or [] if isinstance(e, dict)]
    linked = {_k(e.get("from")) for e in edges_list} | {_k(e.get("to")) for e in edges_list}
    for nid in nodes:
        if nid not in linked:
            warns.append(f"node {nid!r}: no edge touches it")
    for b in bands:
        if not any(n.get("band") == b for n in nodes.values()):
            warns.append(f"band {b!r}: no node is in it")
    return errs, warns


# --------------------------------------------------------------------------- DOT
def _q(s: str) -> str:
    """A DOT double-quoted string; a newline in the label becomes a centred line break."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def _h(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _rel_attrs(r: dict, emphasis: int | None) -> list:
    stroke = INK_DOT if r["stroke"] == "ink" else r["stroke"]
    a = [f"color={_q(stroke)}"]
    if r.get("style", "solid") != "solid":
        a.append(f"style={r['style']}")
    if r.get("head", "normal") != "normal":
        a.append(f"arrowhead={r['head']}")
    width = r.get("width", 1) + (emphasis or 0)
    if width != 1:
        a.append(f"penwidth={width:g}")
    return a


def to_dot(spec: dict) -> str:
    """Deterministic DOT for the spec. Node and edge ids are carried as `id` attributes for the layout."""
    lay = spec.get("layout", {})
    font = lay.get("fontname", "Helvetica")
    fs = lay.get("fontsize", 9)
    kinds = {k["id"]: k for k in spec["vocab"]["node_kinds"]}
    fills = {f["id"]: f for f in spec["vocab"]["fills"]}
    rels = {r["id"]: r for r in spec["vocab"]["relations"]}
    title = spec["title"] + (f"\n{spec['subtitle']}" if spec.get("subtitle") else "")
    out = [f"// Generated by {EXPORTER} from the map spec {spec['id']!r}. Do not edit; edit the spec and rebuild.",
           f"digraph {_q(spec['id'])} {{",
           f"  graph [rankdir={lay.get('rankdir', 'TB')}, newrank=true, fontname={_q(font)}, fontsize={fs + 3:g}, "
           f"nodesep={lay.get('nodesep', 0.25):g}, ranksep={lay.get('ranksep', 0.55):g}, label={_q(title)}, labelloc=t];",
           f"  node [shape=box, style=\"rounded,filled\", fillcolor=white, fontname={_q(font)}, fontsize={fs:g}, margin=\"0.08,0.04\"];",
           f"  edge [fontname={_q(font)}, fontsize={fs * 5 / 6:g}, color={_q(INK_DOT)}];"]
    bands = [b["id"] for b in spec.get("bands") or []]
    if bands:
        out.append("  // bands")
        out.append("  node [shape=plaintext, style=\"\", fontsize=%g, fontcolor=\"#555555\"];" % (fs + 1))
        for b in spec["bands"]:
            out.append(f"  {_q(b['id'])} [id={_q(b['id'])}, label={_q(b['label'])}];")
        if len(bands) > 1:     # with one band there is no chain; alone, this line would hide the band's label
            out.append("  " + " -> ".join(_q(b) for b in bands) + " [style=invis];")
        out.append(f"  node [shape=box, style=\"rounded,filled\", fontsize={fs:g}, fontcolor=black];")
    def node_line(n):
        k = kinds[n["kind"]]
        fill = fills[n.get("fill") or k["fill"]]["color"]
        a = [f"id={_q(n['id'])}", f"label={_q(n['label'])}", f"fillcolor={_q(fill)}"]
        if k["shape"] != "box":
            a.insert(1, f"shape={SHAPES[k['shape']]}")
        if n.get("emphasis"):
            a.append(f"penwidth={1 + n['emphasis']:g}")
        return f"  {_q(n['id'])} [{', '.join(a)}];"
    for b in bands or [None]:
        members = [n for n in spec["nodes"] if n.get("band") == b]
        if b is not None:
            out.append(f"  // band {b}")
        out.extend(node_line(n) for n in members)
        if b is not None:
            out.append("  { rank=same; " + "; ".join([_q(b)] + [_q(n["id"]) for n in members]) + "; }")
    # legend, from the vocabularies
    used_fills = [f for f in spec["vocab"]["fills"] if f.get("legend", True)]
    cols = 4
    rows = []
    cells = [f'<TD BGCOLOR="{f["color"]}">{_h(f["label"])}</TD>' for f in used_fills]
    for i in range(0, len(cells), cols):
        rows.append("<TR>" + "".join(cells[i:i + cols]) + "</TR>")
    rcells = []
    for r in spec["vocab"]["relations"]:
        stroke = INK_DOT if r["stroke"] == "ink" else r["stroke"]
        mark = {"tee": "⊣", "none": "—"}.get(r.get("head", "normal"), "→")
        rcells.append(f'<TD><FONT COLOR="{stroke}">{mark} {_h(r["label"])}</FONT></TD>')
    for i in range(0, len(rcells), cols):
        rows.append("<TR>" + "".join(rcells[i:i + cols]) + "</TR>")
    shapes = "; ".join(f"{_h(k['label'])}: {SHAPE_NAMES[k['shape']]}" for k in spec["vocab"]["node_kinds"])
    note = f" · {_h(spec['legend_note'])}" if spec.get("legend_note") else ""
    rows.insert(0, f'<TR><TD COLSPAN="{cols}"><B>Legend</B></TD></TR>')
    rows.append(f'<TR><TD COLSPAN="{cols}">{shapes}{note}</TD></TR>')
    out.append("  \"__legend\" [shape=plaintext, style=\"\", label=<<TABLE BORDER=\"1\" CELLBORDER=\"0\" CELLSPACING=\"2\" "
               "CELLPADDING=\"3\" COLOR=\"#999999\">" + "".join(rows) + "</TABLE>>];")
    if bands:
        out.append(f"  {{ rank=same; {_q(bands[-1])}; \"__legend\"; }}")
    out.append("  // edges")
    for i, e in enumerate(spec.get("edges") or []):
        a = [f"id=\"e{i}\""] + _rel_attrs(rels[e["relation"]], e.get("emphasis"))
        if e.get("label"):
            a.append(f"label={_q(e['label'])}")
        out.append(f"  {_q(e['from'])} -> {_q(e['to'])} [{', '.join(a)}];")
    out.append("}")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- layout
def run_dot(dot_bin: str, dot_text: str, fmt: str) -> str:
    try:
        r = subprocess.run([dot_bin, f"-T{fmt}"], input=dot_text, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        raise SpecError(f"Graphviz not found ({dot_bin!r}); install Graphviz or pass --dot-bin")
    except subprocess.TimeoutExpired:
        raise SpecError("Graphviz did not finish within 120 s")
    if r.returncode != 0:
        raise SpecError(f"Graphviz failed: {r.stderr.strip()}")
    return r.stdout


def dot_version(dot_bin: str) -> str:
    try:
        r = subprocess.run([dot_bin, "-V"], capture_output=True, text=True, timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "unknown"
    m = re.search(r"graphviz version (\S+)", (r.stderr or "") + (r.stdout or ""))
    return f"graphviz {m.group(1)}" if m else "unknown"


def _pts(s: str) -> list:
    return [[round(float(x), 2) for x in p.split(",")[:2]] for p in s.split()]


def layout(spec: dict, layout_json: str) -> dict:
    """Positions from `dot -Tjson`, flipped so y grows downwards (SVG), in points."""
    J = json.loads(layout_json)
    x0, y0, x1, y1 = (float(v) for v in J["bb"].split(","))
    H = y1
    flip = lambda p: [round(p[0] - x0, 2), round(H - p[1], 2)]
    nodes, bands = {}, {}
    for o in J.get("objects", []):
        oid = o.get("id")
        if not oid or "pos" not in o:
            continue
        x, y = (float(v) for v in o["pos"].split(","))
        box = {"x": flip([x, y])[0], "y": flip([x, y])[1],
               "w": round(float(o["width"]) * 72, 2), "h": round(float(o["height"]) * 72, 2)}
        (bands if o.get("shape") == "plaintext" else nodes)[oid] = box
    edges = {}
    for e in J.get("edges", []):
        eid = e.get("id")
        if not eid or not eid.startswith("e") or "pos" not in e:
            continue
        end = start = None
        parts = []
        for tok in e["pos"].split():
            if tok.startswith("e,"):
                end = flip(_pts(tok[2:])[0])
            elif tok.startswith("s,"):
                start = flip(_pts(tok[2:])[0])
            else:
                parts.append(flip(_pts(tok)[0]))
        g = {"path": parts}
        if end:
            g["tip"] = end
        if start:
            g["tail"] = start
        if "lp" in e:
            g["label_at"] = flip(_pts(e["lp"])[0])
        edges[eid] = g
    return {"width": round(x1 - x0, 2), "height": round(y1 - y0, 2), "nodes": nodes, "bands": bands, "edges": edges}


# --------------------------------------------------------------------------- the map file
def build_map(spec: dict, registry: dict | None, geo: dict, inputs: list, engine: str) -> dict:
    kinds = {k["id"]: k for k in spec["vocab"]["node_kinds"]}
    rels = {r["id"]: r for r in spec["vocab"]["relations"]}
    nodes_by_id = {n["id"]: n for n in spec["nodes"]}

    def persons_of(n):
        out = []
        for p in n.get("persons") or []:
            if "id" in p:
                name = registry[p["id"]] if registry is not None else p["name"]
                out.append({"key": "id:" + p["id"], "id": p["id"], "name": name, "registered": registry is not None})
            else:
                out.append({"key": "name:" + p["name"], "name": p["name"], "registered": False,
                            "note": p["unregistered"]})
        return out

    edges_out = []
    for i, e in enumerate(spec.get("edges") or []):
        eid = f"e{i}"
        if eid not in geo["edges"]:
            raise SpecError(f"layout: Graphviz returned no geometry for edge {eid} ({e['from']} -> {e['to']})")
        d = {"id": eid, "from": e["from"], "to": e["to"], "relation": e["relation"], **geo["edges"][eid]}
        if e.get("label"):
            d["label_lines"] = e["label"].split("\n")
        if e.get("emphasis"):
            d["emphasis"] = e["emphasis"]
        if e.get("basis"):
            d["basis"] = list(e["basis"])
        if e.get("only"):
            d["only"] = ["id:" + x if not x.startswith("name:") else x for x in e["only"]]
        edges_out.append(d)

    nodes_out = []
    n_persons = set()
    for n in spec["nodes"]:
        if n["id"] not in geo["nodes"]:
            raise SpecError(f"layout: Graphviz returned no geometry for node {n['id']!r}")
        k = kinds[n["kind"]]
        d = {"id": n["id"], "kind": n["kind"], "label_lines": n["label"].split("\n"),
             "fill": n.get("fill") or k["fill"], **geo["nodes"][n["id"]]}
        for opt in ("band", "emphasis", "note"):
            if n.get(opt):
                d[opt] = n[opt]
        if n.get("basis"):
            d["basis"] = list(n["basis"])
        if k["role"] == "actor":
            d["persons"] = persons_of(n)
            n_persons.update(p["key"] for p in d["persons"])
        # members: who this node ties to. Computed here, never supplied (CONTRACT.md, section 2.4).
        members, related = {}, []
        for e in edges_out:
            if n["id"] not in (e["from"], e["to"]):
                continue
            outgoing = e["from"] == n["id"]
            other = nodes_by_id[e["to"] if outgoing else e["from"]]
            if kinds[other["kind"]]["role"] == "actor" and k["role"] == "topic":
                # active: the actor is the edge's tail (it affirms, denies, ... this node);
                # not active: this node is the tail (the actor is affirmed, rebutted, ... by it).
                active = not outgoing
                for p in persons_of(other):
                    if e.get("only") and p["key"] not in e["only"]:
                        continue
                    m = members.setdefault((p["key"], e["relation"], active), {
                        "person": p, "relation": e["relation"], "active": active, "via": []})
                    m["via"].append({"edge": e["id"], "node": other["id"]})
            else:
                related.append({"edge": e["id"], "node": other["id"], "relation": e["relation"], "outgoing": outgoing})
        if k["role"] == "topic":
            order = {r: i for i, r in enumerate(rels)}
            d["members"] = sorted(members.values(), key=lambda m: (order[m["relation"]], not m["active"],
                                                                     m["person"]["name"].casefold(), m["person"]["key"]))
        d["related"] = related
        nodes_out.append(d)

    vocab = {"node_kinds": spec["vocab"]["node_kinds"], "fills": spec["vocab"]["fills"],
             "relations": spec["vocab"]["relations"]}
    lay = spec.get("layout", {})
    fs = lay.get("fontsize", 9)
    meta = {"title": spec["title"], "map_id": spec["id"], "exporter": EXPORTER, "layout_engine": engine,
            "inputs": inputs,
            "font": {"family": lay.get("fontname", "Helvetica"), "node_size": fs, "edge_size": round(fs * 5 / 6, 2),
                     "band_size": fs + 1},
            "counts": {"nodes": len(nodes_out), "edges": len(edges_out), "persons": len(n_persons),
                       "topics": sum(1 for n in nodes_out if kinds[n["kind"]]["role"] == "topic")},
            "registry": registry is not None}
    for k in ("subtitle", "notice", "status", "audit", "legend_note"):
        if spec.get(k):
            meta[k] = spec[k]
    bands = [{"id": b["id"], "label": b["label"], **({"x": geo["bands"][b["id"]]["x"], "y": geo["bands"][b["id"]]["y"]}
                                                    if b["id"] in geo["bands"] else {})}
             for b in spec.get("bands") or []]
    return {"schema": SCHEMA, "schema_version": SCHEMA_VERSION, "meta": meta, "vocab": vocab,
            "canvas": {"width": geo["width"], "height": geo["height"], "unit": "pt"},
            "bands": bands, "nodes": nodes_out, "edges": edges_out}


# --------------------------------------------------------------------------- main
def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ours(p: Path) -> bool:
    """True when the file at an output path is one this exporter wrote (or the Graphviz figure it asked for)."""
    try:
        if p.is_symlink() or not p.is_file():
            return False
        text = p.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return False
    if text.startswith(f"// Generated by {EXPORTER_NAME} ") or "<!-- Generated by graphviz" in text[:1024]:
        return True
    try:
        data = json.loads(text)
    except ValueError:
        return False
    return isinstance(data, dict) and data.get("schema") == SCHEMA


def _clear(paths, lines):
    """Remove what an earlier build left at the output paths; leave, and name, anything else found there."""
    for p in paths:
        if not p or not (p.exists() or p.is_symlink()):
            continue
        if _ours(p):
            p.unlink()
        else:
            lines.append(f"NOTE {p.name}: left in place (this exporter did not write it)")


def _same(a: Path, b: Path) -> bool:
    try:
        if a.resolve() == b.resolve():
            return True
        return a.exists() and b.exists() and os.path.samefile(a, b)
    except OSError:
        return False


def _path_clash(a):
    """An output that names an input or another output would be overwritten on success and removed on failure."""
    outs = [(n, p) for n, p in (("--out", a.out), ("--dot", a.dot), ("--svg", a.svg), ("--report", a.report)) if p]
    ins = [(n, p) for n, p in (("the spec", a.spec), ("--registry", a.registry)) if p]
    for i, (n, p) in enumerate(outs):
        for m, q in ins + outs[:i]:
            if _same(p, q):
                return f"{n} names the same file as {m}"
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("spec", type=Path)
    ap.add_argument("--out", type=Path, required=True, help="the map file (JSON) the component reads")
    ap.add_argument("--registry", type=Path, help="a bibliography-explorer file whose persons are the register")
    ap.add_argument("--dot", type=Path, help="also write the generated DOT here")
    ap.add_argument("--svg", type=Path, help="also write the static SVG figure here (Graphviz)")
    ap.add_argument("--report", type=Path, help="write the report here as well as to stdout")
    ap.add_argument("--dot-bin", default=os.environ.get("CONCEPT_MAP_DOT", "dot"))
    a = ap.parse_args(argv)
    outputs = [a.out, a.dot, a.svg]
    lines = [f"{EXPORTER}: {a.spec.name}"]
    clash = _path_clash(a)
    if clash:      # nothing is read, written or removed, and no report file is written (it may be the clash)
        sys.stdout.write("\n".join(lines + [f"ERROR {clash}", "1 error; nothing written."]) + "\n")
        return 1
    try:
        return _run(a, outputs, lines)
    except Exception as e:  # fail closed on anything unforeseen, too (CONTRACT.md, rule 2)
        _clear(outputs, lines)
        lines += [f"ERROR the spec could not be processed ({type(e).__name__}: {e})", "1 error; nothing written."]
        _emit(lines, a.report)
        return 1


def _run(a, outputs, lines) -> int:
    errs: list = []
    try:
        spec = json.loads(a.spec.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        errs.append(f"spec {a.spec.name}: cannot be read ({type(e).__name__})")
        spec = None
    registry = load_registry(a.registry, errs) if a.registry else None
    warns: list = []
    if spec is not None and not errs:
        e2, warns = check_spec(spec, registry)
        errs.extend(e2)
    if errs:
        _clear(outputs, lines)
        lines += [f"ERROR {e}" for e in errs] + [f"{len(errs)} error(s); nothing written."]
        _emit(lines, a.report)
        return 1
    try:
        dot_text = to_dot(spec)
        geo = layout(spec, run_dot(a.dot_bin, dot_text, "json"))
        svg = run_dot(a.dot_bin, dot_text, "svg") if a.svg else None
        inputs = [{"name": a.spec.name, "sha256": _sha(a.spec)}]
        if a.registry:
            inputs.append({"name": a.registry.name, "sha256": _sha(a.registry)})
        data = build_map(spec, registry, geo, inputs, dot_version(a.dot_bin))
    except SpecError as e:
        _clear(outputs, lines)
        lines += [f"ERROR {e}", "1 error; nothing written."]
        _emit(lines, a.report)
        return 1
    # write every output beside its target first, then move them all into place, so a failed write
    # cannot leave a new map file next to an old DOT or SVG
    staged = [(a.out, json.dumps(data, ensure_ascii=False, sort_keys=True, indent=1) + "\n")]
    if a.dot:
        staged.append((a.dot, dot_text))
    if a.svg:
        staged.append((a.svg, svg))
    tmps = []
    try:
        for path, text in staged:
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".partial", dir=path.parent)
            tmp = Path(name)
            tmps.append((tmp, path))
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)
            os.chmod(tmp, 0o666 & ~_umask())    # mkstemp makes the file private; an output is an ordinary file
        for tmp, path in tmps:
            os.replace(tmp, path)
    finally:
        for tmp, _ in tmps:
            if tmp.exists():
                tmp.unlink()
    c = data["meta"]["counts"]
    lines += [f"WARNING {w}" for w in warns]
    lines.append(f"ok: {c['nodes']} nodes ({c['topics']} topics), {c['edges']} edges, {c['persons']} persons; "
                 f"layout {data['meta']['layout_engine']}; {len(warns)} warning(s).")
    lines.append("A clean build means well-formed and internally consistent, not that any label or link is true.")
    _emit(lines, a.report)
    return 0


def _umask() -> int:
    m = os.umask(0)
    os.umask(m)
    return m


def _emit(lines, report):
    text = "\n".join(lines) + "\n"
    sys.stdout.write(text)
    if report:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
