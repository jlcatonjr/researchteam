#!/usr/bin/env python3
"""Build the bibliography explorer's data file from a project's input tables.

Purpose: read the input tables of templates/bibliography-explorer/CONTRACT.md (section 3), check them
    (section 4), render Chicago citations for the .bib entries and write one explorer file (section 2).
Lifecycle: UTILITY
Created: 2026-11-18

CEILING (do not soften): a clean export means the file is WELL-FORMED AND INTERNALLY CONSISTENT. It
does not mean any value, quote, citation or summary is true. Nothing is inferred: no key is guessed
from free text, no names are matched, no near-duplicate citations are merged.

Usage:
  python3 scripts/build_bibliography_explorer.py <input-dir> --out <file>
          [--bib <file.bib>] [--literature <literature.jsonl>] [--report <file>]
Exit codes: 0 written, 1 the inputs have errors (nothing written, and an earlier file at --out is
removed), 2 usage or environment error.
The report (counts, warnings, the sources made from free-text citations) goes to --report, or to
standard output without it. The output is deterministic: the same inputs give the same bytes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bibtex_chicago as bc  # noqa: E402

SCHEMA = "researchteam.bibliography-explorer"
SCHEMA_VERSION = "1.0"
EXPORTER_ID = "researchteam-bibliography-explorer-exporter-v1"
ID_RX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
URL_RX = re.compile(r"^https?://\S+$")

CSV_COLUMNS = {
    "persons.csv": ["id", "kind", "display_name", "sort_name", "aliases", "period_id", "period_year",
                    "year_basis"],
    "evidence.csv": ["id", "person_id", "attribute_kind", "value", "tier", "source_id", "citation",
                     "locator", "quote", "url", "access", "via", "audit"],
    "works.csv": ["source_id", "title", "date", "locator"],
    "links.csv": ["person_id", "source_id", "role", "basis"],
    "codes.csv": ["person_id", "key", "label", "value_label", "established", "basis", "evidence_ids"],
    "source_attributes.csv": ["source_id", "label", "value"],
}
VOCABS = {
    "attribute_kinds": ({"id", "label", "order", "multi"}, set()),
    "tiers": ({"id", "label", "establishes"}, {"description"}),
    "access": ({"id", "label"}, set()),
    "roles": ({"id", "label"}, set()),
    "person_kinds": ({"id", "label"}, set()),
}


class Export:
    """One export run: the inputs read so far, and the errors and warnings found."""

    def __init__(self, input_dir: Path) -> None:
        self.dir = input_dir
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.inputs: dict[str, str] = {}

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    # ---- readers
    def _bytes(self, path: Path) -> bytes | None:
        if not path.is_file():
            return None
        data = path.read_bytes()
        self.inputs[path.name] = hashlib.sha256(data).hexdigest()
        return data

    def _text(self, path: Path, required: bool = False) -> str | None:
        data = self._bytes(path)
        if data is None:
            if required:
                self.error(f"{path.name}: the file is required and was not found")
            return None
        try:
            return data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            self.error(f"{path.name}: not UTF-8 ({exc})")
            return None

    def csv(self, name: str, required: bool = False) -> list[dict]:
        text = self._text(self.dir / name, required)
        if text is None:
            return []
        reader = csv.DictReader(io.StringIO(text, newline=""))
        want = CSV_COLUMNS[name]
        have = reader.fieldnames or []
        missing = [c for c in want if c not in have]
        unknown = [c for c in have if c not in want]
        if missing or unknown or len(set(have)) != len(have):
            self.error(f"{name}: columns must be exactly {', '.join(want)}"
                       + (f"; missing: {', '.join(missing)}" if missing else "")
                       + (f"; unknown: {', '.join(map(str, unknown))}" if unknown else ""))
            return []
        rows = []
        for n, row in enumerate(reader, start=2):
            if None in row or any(v is None for v in row.values()):
                self.error(f"{name} row {n}: wrong number of cells")
                continue
            clean = {k: (v if k == "quote" else v.strip()) for k, v in row.items()}
            clean["_row"] = n
            rows.append(clean)
        return rows

    def json(self, name: str, required: bool = False):
        text = self._text(self.dir / name, required)
        if text is None:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            self.error(f"{name}: not valid JSON ({exc})")
            return None

    def jsonl(self, path: Path) -> list[tuple[int, dict]]:
        text = self._text(path)
        if text is None:
            self.error(f"{path.name}: the file was not found")
            return []
        out = []
        for n, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                self.error(f"{path.name} line {n}: not valid JSON ({exc})")
                continue
            if not isinstance(rec, dict):
                self.error(f"{path.name} line {n}: not an object")
                continue
            out.append((n, rec))
        return out

    # ---- small checks
    def keys(self, obj, required: set, optional: set, where: str) -> bool:
        if not isinstance(obj, dict):
            self.error(f"{where}: must be an object")
            return False
        missing = required - obj.keys()
        unknown = obj.keys() - required - optional
        if missing:
            self.error(f"{where}: missing {', '.join(sorted(missing))}")
        if unknown:
            self.error(f"{where}: unknown key {', '.join(sorted(unknown))}")
        return not missing and not unknown

    def text(self, value, where: str, required: bool = True) -> bool:
        if isinstance(value, str) and value.strip():
            return True
        if required or value not in (None, ""):
            self.error(f"{where}: must be a non-empty string")
        return False

    def ident(self, value, where: str) -> bool:
        if isinstance(value, str) and ID_RX.match(value):
            return True
        self.error(f"{where}: {value!r} is not a valid id")
        return False

    def url(self, value, where: str) -> bool:
        if isinstance(value, str) and URL_RX.match(value):
            return True
        self.error(f"{where}: {value!r} is not an http(s) URL")
        return False


def _put(target: dict, **optional) -> dict:
    """Add the optional fields that are present; an absent field is omitted, never written empty."""
    for key, value in optional.items():
        if value not in (None, "", []):
            target[key] = value
    return target


def _split(cell: str) -> list[str]:
    return [p.strip() for p in cell.split(";") if p.strip()]


# --------------------------------------------------------------------------- config
def _config(x: Export) -> tuple[dict, dict, list]:
    cfg = x.json("explorer.json", required=True)
    empty = {k: [] for k in VOCABS}
    if cfg is None or not x.keys(cfg, {"title", "vocab", "periods"}, {"notice"}, "explorer.json"):
        return {"title": ""}, empty, []
    x.text(cfg["title"], "explorer.json title")
    x.text(cfg.get("notice"), "explorer.json notice", required=False)
    vocab = dict(empty)
    if x.keys(cfg["vocab"], set(VOCABS), set(), "explorer.json vocab"):
        for name, (required, optional) in VOCABS.items():
            items, seen = cfg["vocab"][name], set()
            if not isinstance(items, list):
                x.error(f"explorer.json vocab.{name}: must be a list")
                continue
            good = []
            for n, item in enumerate(items):
                where = f"explorer.json vocab.{name}[{n}]"
                if not x.keys(item, required, optional, where) or not x.ident(item["id"], where):
                    continue
                if item["id"] in seen:
                    x.error(f"{where}: the id {item['id']!r} is used twice")
                    continue
                seen.add(item["id"])
                x.text(item["label"], where + " label")
                for flag in ("multi", "establishes"):
                    if flag in item and not isinstance(item[flag], bool):
                        x.error(f"{where}: {flag} must be true or false")
                if "order" in item and (not isinstance(item["order"], int) or isinstance(item["order"], bool)):
                    x.error(f"{where}: order must be an integer")
                good.append(item)
            vocab[name] = good
    return cfg, vocab, _periods(x, cfg["periods"])


def _periods(x: Export, items) -> list:
    if not isinstance(items, list) or not items:
        x.error("explorer.json periods: must be a non-empty list")
        return []
    good, seen = [], set()
    for n, p in enumerate(items):
        where = f"explorer.json periods[{n}]"
        if not x.keys(p, {"id", "label", "order", "start_year", "end_year", "established"}, set(), where):
            continue
        ok = x.ident(p["id"], where) and x.text(p["label"], where + " label")
        if not ok:
            continue
        if p["id"] in seen:
            x.error(f"{where}: the id {p['id']!r} is used twice")
            ok = False
        seen.add(p["id"])
        if not isinstance(p["established"], bool):
            x.error(f"{where}: established must be true or false")
            ok = False
        for f in ("order", "start_year", "end_year"):
            v = p[f]
            if isinstance(v, bool) or not (isinstance(v, int) or (v is None and f != "order")):
                x.error(f"{where}: {f} must be an integer" + ("" if f == "order" else " or null"))
                ok = False
        if ok:
            good.append(p)
    if len(good) != len(items):
        return good
    if len({p["order"] for p in good}) != len(good):
        x.error("explorer.json periods: two periods share an order")
    unestablished = [p for p in good if not p["established"]]
    if len(unestablished) > 1:
        x.error("explorer.json periods: more than one period has established: false")
    for p in unestablished:
        if p["start_year"] is not None or p["end_year"] is not None:
            x.error(f"explorer.json period {p['id']!r}: an unestablished period has no years")
    ranged = sorted((p for p in good if p["established"]), key=lambda p: p["order"])
    for k, p in enumerate(ranged):
        if p["start_year"] is None and k != 0:
            x.error(f"explorer.json period {p['id']!r}: only the first period may have no start_year")
        if p["end_year"] is None and k != len(ranged) - 1:
            x.error(f"explorer.json period {p['id']!r}: only the last period may have no end_year")
        if p["start_year"] is not None and p["end_year"] is not None and p["start_year"] > p["end_year"]:
            x.error(f"explorer.json period {p['id']!r}: start_year is after end_year")
        if k and None not in (ranged[k - 1]["end_year"], p["start_year"]) \
                and ranged[k - 1]["end_year"] >= p["start_year"]:
            x.error(f"explorer.json periods {ranged[k - 1]['id']!r} and {p['id']!r} overlap")
    return good


# --------------------------------------------------------------------------- sources
def _bib_sources(x: Export, bib_path: Path | None) -> dict:
    if bib_path is None:
        return {}
    data = x._bytes(bib_path)
    if data is None:
        x.error(f"{bib_path.name}: the .bib file was not found")
        return {}
    sources: dict = {}
    unused: dict[str, int] = {}
    try:
        entries = bc.parse_bib(data.decode("utf-8-sig"))
    except (bc.BibError, UnicodeDecodeError) as exc:
        x.error(f"{bib_path.name}: {exc}")
        return {}
    for entry in entries:
        where = f"{bib_path.name} entry {entry['key']!r}"
        if not x.ident(entry["key"], where + " key"):
            continue
        try:
            fields, extra = bc.decode_entry(entry)
            runs = bc.render_chicago(entry["type"], fields)
        except bc.BibError as exc:
            prefix = f"entry {entry['key']!r}: "
            x.error(f"{where}: {str(exc).removeprefix(prefix)}")
            continue
        for name in extra:
            unused[name] = unused.get(name, 0) + 1
        if "title" not in fields:
            x.warn(f"{where}: no title")
        if "url" in fields and not x.url(fields["url"], where + " url"):
            continue
        note = fields.pop("note", None)
        links = []
        if "doi" in fields:
            links.append({"label": "DOI", "url": "https://doi.org/" + fields["doi"]})
        if "url" in fields:
            links.append({"label": "URL", "url": fields["url"]})
        sources[entry["key"]] = _put(
            {"id": entry["key"], "origin": "bibliography", "type": entry["type"],
             "citation": {"chicago": "".join(r["text"] for r in runs), "chicago_runs": runs},
             "fields": fields, "links": links},
            note=note)
    for name in sorted(unused):
        x.warn(f"{bib_path.name}: the field {name!r} is not carried ({unused[name]} "
               f"entr{'y' if unused[name] == 1 else 'ies'})")
    return sources


def _work_sources(x: Export, sources: dict) -> None:
    for row in x.csv("works.csv"):
        where = f"works.csv row {row['_row']}"
        if not x.ident(row["source_id"], where + " source_id") or not x.text(row["title"], where + " title"):
            continue
        if row["source_id"] in sources:
            x.error(f"{where}: the source id {row['source_id']!r} is already used")
            continue
        sources[row["source_id"]] = {
            "id": row["source_id"], "origin": "work-title", "citation": {"as_recorded": row["title"]},
            "fields": _put({"title": row["title"]}, date=row["date"], locator=row["locator"]),
            "links": []}


# --------------------------------------------------------------------------- persons and evidence
def _persons(x: Export, vocab: dict, periods: list) -> dict:
    kinds = {k["id"] for k in vocab["person_kinds"]}
    by_period = {p["id"]: p for p in periods}
    persons: dict = {}
    for row in x.csv("persons.csv", required=True):
        where = f"persons.csv row {row['_row']}"
        if not x.ident(row["id"], where + " id"):
            continue
        if row["id"] in persons:
            x.error(f"{where}: the id {row['id']!r} is used twice")
            continue
        x.text(row["display_name"], where + " display_name")
        if row["kind"] not in kinds:
            x.error(f"{where}: unknown kind {row['kind']!r}")
        period = {"id": row["period_id"]}
        p = by_period.get(row["period_id"])
        if p is None:
            x.error(f"{where}: unknown period {row['period_id']!r} (a person has exactly one period)")
        if row["period_year"]:
            if not re.fullmatch(r"-?\d+", row["period_year"]):
                x.error(f"{where}: period_year {row['period_year']!r} is not a whole number")
            else:
                year = period["year"] = int(row["period_year"])
                if p is not None and not p["established"]:
                    x.error(f"{where}: a period_year is given for an unestablished period")
                elif p is not None and ((p["start_year"] is not None and year < p["start_year"])
                                        or (p["end_year"] is not None and year > p["end_year"])):
                    x.error(f"{where}: period_year {year} is outside the period {p['id']!r}")
        _put(period, year_basis=row["year_basis"])
        persons[row["id"]] = _put(
            {"id": row["id"], "kind": row["kind"], "display_name": row["display_name"],
             "period": period, "attributes": []},
            sort_name=row["sort_name"], aliases=_split(row["aliases"]))
    return persons


def _evidence(x: Export, vocab: dict, persons: dict, sources: dict) -> tuple[list, dict]:
    """Read evidence.csv. Returns (evidence rows, made) where made maps url -> the evidence-citation
    sources created for it, for the report."""
    kinds = {k["id"]: k for k in vocab["attribute_kinds"]}
    tiers = {t["id"]: t for t in vocab["tiers"]}
    access = {a["id"] for a in vocab["access"]}
    evidence, seen = [], set()
    made: dict[str, dict] = {}
    values: dict[tuple, dict] = {}
    for row in x.csv("evidence.csv", required=True):
        where = f"evidence.csv row {row['_row']}"
        ok = x.ident(row["id"], where + " id")
        if row["id"] in seen:
            x.error(f"{where}: the id {row['id']!r} is used twice")
            ok = False
        seen.add(row["id"])
        if row["person_id"] not in persons:
            x.error(f"{where}: unknown person {row['person_id']!r}")
            ok = False
        if row["attribute_kind"] not in kinds:
            x.error(f"{where}: unknown attribute_kind {row['attribute_kind']!r}")
            ok = False
        if row["tier"] not in tiers:
            x.error(f"{where}: unknown tier {row['tier']!r}")
            ok = False
        if row["access"] and row["access"] not in access:
            x.error(f"{where}: unknown access {row['access']!r}")
            ok = False
        ok = x.text(row["value"], where + " value") and ok
        if row["url"]:
            ok = x.url(row["url"], where + " url") and ok
        source_id = row["source_id"]
        if source_id:
            if source_id not in sources or sources[source_id]["origin"] == "evidence-citation":
                x.error(f"{where}: source_id {source_id!r} names no .bib entry and no works.csv row")
                ok = False
        elif not row["citation"]:
            x.error(f"{where}: neither source_id nor citation is given")
            ok = False
        elif ok:
            digest = hashlib.sha256((row["citation"] + "\x1f" + row["url"]).encode("utf-8")).hexdigest()
            source_id = "ec-" + digest[:16]
            if source_id not in sources:
                sources[source_id] = {
                    "id": source_id, "origin": "evidence-citation",
                    "citation": {"as_recorded": row["citation"]},
                    "fields": _put({}, url=row["url"]),
                    "links": [{"label": "URL", "url": row["url"]}] if row["url"] else []}
            entry = made.setdefault(source_id, {"url": row["url"], "citation": row["citation"], "rows": 0})
            entry["rows"] += 1
        if not ok:
            continue
        evidence.append(_put(
            {"id": row["id"], "person_id": row["person_id"], "attribute_kind": row["attribute_kind"],
             "value": row["value"], "tier": row["tier"], "source_id": source_id},
            cited_as=row["citation"] if row["source_id"] else "",
            locator=row["locator"], quote=row["quote"], url=row["url"], access=row["access"],
            via=row["via"], audit=row["audit"]))
        key = (row["person_id"], row["attribute_kind"], row["value"])
        value = values.get(key)
        if value is None:
            value = values[key] = {"kind": row["attribute_kind"], "value": row["value"],
                                   "evidence_ids": [], "established": False}
            persons[row["person_id"]]["attributes"].append(value)
        value["evidence_ids"].append(row["id"])
        value["established"] = value["established"] or tiers[row["tier"]]["establishes"] is True
    order = {k: v.get("order", 0) for k, v in kinds.items()}
    for person in persons.values():
        person["attributes"].sort(key=lambda a: order.get(a["kind"], 0))   # stable: file order within a kind
        if not person["attributes"]:
            x.warn(f"person {person['id']!r} has no attributes")
    return evidence, made


def _owned(x: Export, ids, person_id: str, owner: dict, where: str) -> list:
    """Check a list of evidence ids used inside one person's record."""
    if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
        x.error(f"{where}: evidence_ids must be a list of ids")
        return []
    for i in ids:
        if i not in owner:
            x.error(f"{where}: unknown evidence id {i!r}")
        elif owner[i] != person_id:
            x.error(f"{where}: evidence {i!r} belongs to another person ({owner[i]!r})")
    return ids


# --------------------------------------------------------------------------- person extras
def _codes(x: Export, persons: dict, owner: dict) -> None:
    seen = set()
    for row in x.csv("codes.csv"):
        where = f"codes.csv row {row['_row']}"
        if row["person_id"] not in persons:
            x.error(f"{where}: unknown person {row['person_id']!r}")
            continue
        ok = all([x.text(row[c], f"{where} {c}") for c in ("key", "label", "value_label")])
        if (row["person_id"], row["key"]) in seen:
            x.error(f"{where}: the code {row['key']!r} is given twice for this person")
            ok = False
        seen.add((row["person_id"], row["key"]))
        if row["established"] not in ("true", "false"):
            x.error(f"{where}: established must be 'true' or 'false'")
            continue
        established = row["established"] == "true"
        ids = _owned(x, _split(row["evidence_ids"]), row["person_id"], owner, where)
        if established and not ids:
            x.error(f"{where}: an established code needs evidence")
            ok = False
        if ok:
            persons[row["person_id"]].setdefault("codes", []).append(_put(
                {"key": row["key"], "label": row["label"], "value_label": row["value_label"],
                 "established": established, "evidence_ids": ids}, basis=row["basis"]))


def _bios(x: Export, persons: dict, owner: dict) -> None:
    bios = x.json("bios.json")
    if bios is None:
        return
    if not isinstance(bios, dict):
        x.error("bios.json: must be an object keyed by person id")
        return
    for pid, bio in bios.items():
        where = f"bios.json {pid!r}"
        if pid not in persons:
            x.error(f"{where}: unknown person")
            continue
        if not x.keys(bio, {"text", "basis", "verification_state"}, {"clauses", "authored_by"}, where):
            continue
        ok = all([x.text(bio[k], f"{where} {k}") for k in ("text", "basis", "verification_state")])
        x.text(bio.get("authored_by"), where + " authored_by", required=False)
        if "clauses" in bio:
            clauses = bio["clauses"]
            if not isinstance(clauses, list) or not clauses:
                x.error(f"{where}: clauses must be a non-empty list")
                continue
            for n, clause in enumerate(clauses):
                cw = f"{where} clauses[{n}]"
                if not x.keys(clause, {"text", "evidence_ids"}, set(), cw) or not x.text(clause["text"], cw):
                    ok = False
                    continue
                _owned(x, clause["evidence_ids"], pid, owner, cw)
            if ok and " ".join(c["text"] for c in clauses) != bio["text"]:
                x.error(f"{where}: text differs from the clauses joined by one space")
        if ok:
            persons[pid]["bio"] = _put({k: bio[k] for k in ("text", "basis", "verification_state")},
                                       clauses=bio.get("clauses"), authored_by=bio.get("authored_by"))


def _groups(x: Export, persons: dict, owner: dict) -> None:
    groups = x.json("groups.json")
    if groups is None:
        return
    if not isinstance(groups, dict):
        x.error("groups.json: must be an object keyed by person id")
        return
    for pid, items in groups.items():
        where = f"groups.json {pid!r}"
        if pid not in persons:
            x.error(f"{where}: unknown person")
            continue
        if not isinstance(items, list):
            x.error(f"{where}: must be a list of groups")
            continue
        seen, good = set(), True
        for n, group in enumerate(items):
            gw = f"{where}[{n}]"
            if not x.keys(group, {"id", "title", "advisory", "rows"}, {"caveat"}, gw):
                good = False
                continue
            if not (x.ident(group["id"], gw + " id") and x.text(group["title"], gw + " title")):
                good = False
                continue
            if group["id"] in seen:
                x.error(f"{gw}: the id {group['id']!r} is used twice")
                good = False
            seen.add(group["id"])
            if not isinstance(group["advisory"], bool):
                x.error(f"{gw}: advisory must be true or false")
                good = False
            elif group["advisory"] and not x.text(group.get("caveat"), gw + " caveat (required when advisory)"):
                good = False
            elif "caveat" in group and not x.text(group["caveat"], gw + " caveat"):
                good = False
            if not isinstance(group["rows"], list):
                x.error(f"{gw}: rows must be a list")
                good = False
                continue
            for m, row in enumerate(group["rows"]):
                rw = f"{gw} rows[{m}]"
                if not x.keys(row, {"label", "value"}, {"links", "evidence_ids", "note"}, rw):
                    good = False
                    continue
                good = x.text(row["label"], rw + " label") and good
                if not isinstance(row["value"], str):
                    x.error(f"{rw}: value must be a string")
                    good = False
                x.text(row.get("note"), rw + " note", required=False)
                if "evidence_ids" in row:
                    _owned(x, row["evidence_ids"], pid, owner, rw)
                links = row.get("links", [])
                if not isinstance(links, list):
                    x.error(f"{rw}: links must be a list")
                    good = False
                    continue
                for k, link in enumerate(links):
                    lw = f"{rw} links[{k}]"
                    if x.keys(link, {"label", "url"}, set(), lw):
                        x.text(link["label"], lw + " label")
                        x.url(link["url"], lw + " url")
        if good:
            persons[pid]["groups"] = [_put(
                {"id": g["id"], "title": g["title"], "advisory": g["advisory"],
                 "rows": [_put({"label": r["label"], "value": r["value"]}, links=r.get("links"),
                               evidence_ids=r.get("evidence_ids"), note=r.get("note")) for r in g["rows"]]},
                caveat=g.get("caveat")) for g in items]


# --------------------------------------------------------------------------- source extras and links
def _summary(x: Export, rec: dict, where: str) -> dict | None:
    need = ("text", "deemed_by", "basis", "verification_state")
    if not all([x.text(rec.get(k), f"{where} {k}") for k in need]):
        return None
    summary = {k: rec[k] for k in need}
    if rec.get("read_url") not in (None, ""):
        if not x.url(rec["read_url"], where + " read_url"):
            return None
        summary["read_url"] = rec["read_url"]
    caveats = rec.get("caveats")
    if caveats not in (None, []):
        if not isinstance(caveats, list) or not all(isinstance(c, str) and c.strip() for c in caveats):
            x.error(f"{where}: caveats must be a list of non-empty strings")
            return None
        summary["caveats"] = caveats
    return summary


def _summaries(x: Export, sources: dict, literature: Path | None) -> None:
    def attach(source_id, summary, where):
        if not isinstance(source_id, str) or source_id not in sources:
            x.error(f"{where}: unknown source {source_id!r}")
        elif "summary" in sources[source_id]:
            x.error(f"{where}: the source {source_id!r} already has a summary")
        elif summary is not None:
            sources[source_id]["summary"] = summary

    path = x.dir / "summaries.jsonl"
    if path.is_file():
        allowed = {"source_id", "text", "deemed_by", "basis", "verification_state", "read_url", "caveats"}
        for n, rec in x.jsonl(path):
            where = f"summaries.jsonl line {n}"
            if x.keys(rec, allowed - {"read_url", "caveats"}, {"read_url", "caveats"}, where):
                attach(rec["source_id"], _summary(x, rec, where), where)
    if literature is None:
        return
    for n, rec in x.jsonl(literature):
        where = f"{literature.name} line {n}"
        rel = rec.get("relevance")
        if not isinstance(rel, dict) or rel.get("source") != "agent-authored":
            x.warn(f"{where}: record {rec.get('key')!r} skipped (relevance.source is not 'agent-authored')")
            continue
        if not (isinstance(rel.get("deemed_by"), str) and rel["deemed_by"].strip()):
            x.warn(f"{where}: record {rec.get('key')!r} skipped (no relevance.deemed_by)")
            continue
        mapped = {"text": rel.get("summary"), "deemed_by": rel.get("deemed_by"),
                  "basis": rel.get("basis") or "record only",
                  "verification_state": rec.get("verification_state"),
                  "read_url": rel.get("read_url"), "caveats": rel.get("caveats")}
        attach(rec.get("key"), _summary(x, mapped, where), where)


def _source_attributes(x: Export, sources: dict) -> None:
    for row in x.csv("source_attributes.csv"):
        where = f"source_attributes.csv row {row['_row']}"
        if row["source_id"] not in sources:
            x.error(f"{where}: unknown source {row['source_id']!r}")
        elif x.text(row["label"], where + " label") and x.text(row["value"], where + " value"):
            sources[row["source_id"]].setdefault("attributes", []).append(
                {"label": row["label"], "value": row["value"]})


def _links(x: Export, vocab: dict, persons: dict, sources: dict, evidence: list) -> list:
    about: dict[tuple, dict] = {}
    for ev in evidence:
        link = about.setdefault((ev["person_id"], ev["source_id"]), {
            "person_id": ev["person_id"], "source_id": ev["source_id"], "relation": "about",
            "attribute_kinds": [], "evidence_ids": []})
        if ev["attribute_kind"] not in link["attribute_kinds"]:
            link["attribute_kinds"].append(ev["attribute_kind"])
        link["evidence_ids"].append(ev["id"])
    links = list(about.values())
    roles = {r["id"] for r in vocab["roles"]}
    seen = set()
    for row in x.csv("links.csv"):
        where = f"links.csv row {row['_row']}"
        ok = True
        if row["person_id"] not in persons:
            x.error(f"{where}: unknown person {row['person_id']!r}")
            ok = False
        if row["source_id"] not in sources:
            x.error(f"{where}: unknown source {row['source_id']!r}")
            ok = False
        if not row["role"]:
            x.error(f"{where}: a 'by' link needs a role")
            ok = False
        elif row["role"] not in roles:
            x.error(f"{where}: unknown role {row['role']!r}")
            ok = False
        key = (row["person_id"], row["source_id"], row["role"])
        if key in seen:
            x.error(f"{where}: the same link is given twice")
            ok = False
        seen.add(key)
        if ok:
            links.append(_put({"person_id": row["person_id"], "source_id": row["source_id"],
                               "relation": "by", "role": row["role"]}, basis=row["basis"]))
    linked = {l["source_id"] for l in links}
    for sid, src in sources.items():
        if sid not in linked:
            x.warn(f"source {sid!r} ({src['origin']}) is not linked to any person")
    return links


# --------------------------------------------------------------------------- build and report
def build(input_dir: Path, bib: Path | None = None, literature: Path | None = None) -> tuple[dict | None, Export, dict]:
    """Read and check the inputs. Returns (document or None on error, the run, evidence-citation sources)."""
    x = Export(input_dir)
    cfg, vocab, periods = _config(x)
    sources = _bib_sources(x, bib)
    _work_sources(x, sources)
    persons = _persons(x, vocab, periods)
    evidence, made = _evidence(x, vocab, persons, sources)
    owner = {e["id"]: e["person_id"] for e in evidence}
    _codes(x, persons, owner)
    _bios(x, persons, owner)
    _groups(x, persons, owner)
    _summaries(x, sources, literature)
    _source_attributes(x, sources)
    links = _links(x, vocab, persons, sources, evidence)
    if x.errors:
        return None, x, made
    meta = _put({
        "title": cfg["title"], "exporter": EXPORTER_ID, "citation_renderer": bc.RENDERER_ID,
        "inputs": [{"name": n, "sha256": h} for n, h in sorted(x.inputs.items())],
        "counts": {"persons": len(persons), "sources": len(sources), "evidence": len(evidence),
                   "links": len(links)}}, notice=cfg.get("notice"))
    doc = {"schema": SCHEMA, "schema_version": SCHEMA_VERSION, "meta": meta, "vocab": vocab,
           "periods": sorted(periods, key=lambda p: (not p["established"], p["order"])),
           "persons": list(persons.values()), "evidence": evidence,
           "sources": list(sources.values()), "links": links}
    return doc, x, made


def dumps(doc: dict) -> str:
    return json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=1) + "\n"


def report(doc: dict | None, x: Export, made: dict) -> str:
    lines = ["Bibliography explorer export report", ""]
    if doc is None:
        lines.append(f"FAILED: {len(x.errors)} error(s). Nothing was written.")
    else:
        c = doc["meta"]["counts"]
        lines.append(f"Written: {c['persons']} persons, {c['sources']} sources, {c['evidence']} evidence "
                     f"rows, {c['links']} links.")
        lines.append("A clean export means well-formed and internally consistent. It does not mean any "
                     "value, quote, citation or summary is true.")
    for title, items in (("Errors", x.errors), ("Warnings", x.warnings)):
        if items:
            lines += ["", f"{title} ({len(items)})"] + [f"  - {m}" for m in items]
    if made:
        lines += ["", f"Sources made from free-text citations ({len(made)}), grouped by url",
                  "  Give a source_id in evidence.csv to merge any that are the same source."]
        by_url: dict[str, list] = {}
        for sid, info in made.items():
            by_url.setdefault(info["url"], []).append((info["citation"], sid, info["rows"]))
        for url in sorted(by_url):
            lines.append(f"  {url or '(no url)'}")
            for citation, sid, rows in sorted(by_url[url]):
                lines.append(f"    {sid}  [{rows} row{'s' if rows != 1 else ''}]  {citation}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the bibliography explorer's data file.")
    ap.add_argument("input_dir", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--bib", type=Path)
    ap.add_argument("--literature", type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args(argv)
    if not args.input_dir.is_dir():
        print(f"error: {args.input_dir} is not a directory", file=sys.stderr)
        return 2
    doc, x, made = build(args.input_dir, args.bib, args.literature)
    text = report(doc, x, made)
    try:
        stale = doc is None and args.out.is_file()
        if stale:
            args.out.unlink()           # fail closed, and first: an earlier export must not pass for this one
        if args.report:
            args.report.write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        if doc is None:
            print(f"error: {len(x.errors)} error(s); nothing written"
                  + (f"; the earlier file at {args.out} was removed" if stale else "")
                  + (f" (see {args.report})" if args.report else ""), file=sys.stderr)
            return 1
        _write_atomic(args.out, dumps(doc))
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


def _write_atomic(path: Path, text: str) -> None:
    """Write through a temporary file in the same directory, so a reader never sees half a file."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


if __name__ == "__main__":
    sys.exit(main())
