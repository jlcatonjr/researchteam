"""The frame of a passage or work study (contract 4.7): its cells, columns and rows, the cells the rule
``not-on-question`` leaves out, and the passage list. This module writes nothing; ``survey-frame`` writes.

- **Cells.** A cell is one author and one value of each ``unit.rollup_by`` attribute, its ``unit_id``
  ``<person_id>|<value>|...`` (lines 582-585). The frame's cells are those with at least one counted passage: the
  passage list's "the cell the passage belongs to, or would belong to if it were counted" (line 661) reads a cell
  as made by counted passages (a reading, listed in the check table).
- **Counted passages** are the rollup's: attribution rows whose status is counted and which no
  ``unit.exclude_from_rollup`` value leaves out (lines 587-589).
- **Columns** in the order of line 593; **outcome cells** by the table of lines 612-616; **the period** by
  ``periods.basis`` (lines 623-633); **attribute evidence** bucketed by the attribute's table (lines 635-639).
- **Checks** (lines 651-653): every value one its column allows, each ``unit_id`` unique, every column present.

No code is ever filled in (rule 1.3): a cell with no final code is empty (line 621).
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field

from survey_codes import coded_outcomes
from survey_core import Finding, q
from survey_final import apply_rule, authors
from survey_tables import bucket_all, bucket_first, life_year, period_of, year_of

NOT_ON_QUESTION = "not-on-question"
MIXED = "mixed"
DROPPED_COLUMNS = ("unit_id", "rule", "reason")
PASSAGE_COLUMNS = ("unit_id", "passage_id", "evidence_id", "person_id", "attribution", "counted", "not_counted_reason")


def quoted_csv(columns: tuple, rows: list) -> bytes:
    """CSV with every cell quoted, lines ending in LF (4.7, lines 646-647)."""
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_ALL, lineterminator="\n")
    writer.writerow(columns)
    for r in rows:
        writer.writerow([r[c] for c in columns])
    return buf.getvalue().encode("utf-8")


# --------------------------------------------------------------------------- the specification's view of the frame
def period_attribute(spec: dict) -> dict | None:
    return next((a for a in spec["attributes"] if a["kind"] == "period"), None)


def period_columns(spec: dict) -> tuple:
    """``(<key>, <key>_num)``; ``period`` and ``period_num`` without a period attribute (section 3, lines 269-270)."""
    a = period_attribute(spec)
    key = a["key"] if a is not None else "period"
    return key, f"{key}_num"


def period_missing(spec: dict) -> str:
    """The period's missing value: the period attribute's ``missing`` (default ``NE``); ``NE`` without one (line
    607)."""
    a = period_attribute(spec)
    return a.get("missing", "NE") if a is not None else "NE"


def frame_outcomes(spec: dict) -> dict:
    """The outcomes the frame carries: source ``codes`` and rollup not ``none``, in declared order (line 603)."""
    return {k: o for k, o in coded_outcomes(spec).items() if o["rollup"] != "none"}


def frame_columns(spec: dict) -> tuple:
    """``unit_id, author, <each rollup_by key>, unit_kind, <period key>, <period key>_num, <attribute columns>,
    <outcome columns>`` (line 593): a categorical attribute one column; a flags attribute one per flag, then
    ``<key>_<missing>``; the period attribute not repeated (lines 601-606)."""
    unit = spec["unit"]
    cols = ["unit_id", "author", *unit.get("rollup_by", []), "unit_kind", *period_columns(spec)]
    for a in spec["attributes"]:
        if a["kind"] == "categorical":
            cols.append(a["key"])
        elif a["kind"] == "flags":
            cols += [f"{a['key']}_{flag}" for flag in a.get("flags", [])]
            cols.append(f"{a['key']}_{a.get('missing', 'NE')}")
    cols += list(frame_outcomes(spec))
    return tuple(cols)


def cell_id(spec: dict, att: dict, person: str | None = None) -> str:
    """``<person_id>|<value>|...`` in ``rollup_by`` order; the ``person_id`` alone without ``rollup_by`` (line 583).
    *person* is the passage's author read through the merges (ruling D); the attribution row's own id otherwise."""
    return "|".join((att["person_id"] if person is None else person,
                     *(att[k] for k in spec["unit"].get("rollup_by", []))))


def excluded_by(spec: dict, att: dict) -> tuple | None:
    """The first ``unit.exclude_from_rollup`` key, in the order the specification gives, whose list holds the
    passage's value: ``(key, value)``, or None (line 666)."""
    for key, values in spec["unit"].get("exclude_from_rollup", {}).items():
        if att.get(key) in values:
            return key, att[key]
    return None


def is_counted(spec: dict, att: dict) -> bool:
    """A counted passage (lines 587-589): its status is counted and no exclusion value applies."""
    return att["status"] in spec["unit"]["attribution"]["counted_statuses"] and excluded_by(spec, att) is None


def drops_not_on_question(spec: dict) -> dict | None:
    """The ``frame_rules.exclude`` entry declaring ``not-on-question``, or None (lines 641-644)."""
    return next((e for e in spec["frame_rules"]["exclude"] if e["rule"] == NOT_ON_QUESTION), None)


# --------------------------------------------------------------------------- building the frame
@dataclass
class Built:
    columns: tuple = ()
    rows: list = field(default_factory=list)       # the frame's rows, ascending code-point order of unit_id
    dropped: list = field(default_factory=list)    # (unit_id, rule, reason) rows, same order
    passages: list = field(default_factory=list)   # the passage list, in evidence-file order
    findings: list = field(default_factory=list)

    @property
    def units(self) -> list:
        return [r["unit_id"] for r in self.rows]


def build(spec: dict, final_rows: list, attribution: dict, evidence: list, tables: dict,
          persons: dict | None = None) -> Built:
    """The frame (4.7). *final_rows* are the current final codes; *attribution* maps a unit to its attribution row, in
    file order; *evidence* is the evidence file's rows, in file order; *tables* maps an attribute key to its checked
    bucket-table rows; *persons* maps a merged id to the person it was merged into (``survey_final.merged_persons``,
    ruling D), shared with the rollup: a passage, and a row, of a merged id count for that person."""
    out = Built(columns=frame_columns(spec))
    add = lambda rule, where, msg: out.findings.append(Finding(rule, where, msg))  # noqa: E731
    persons = persons or {}
    person_of = lambda pid: persons.get(pid, pid)  # noqa: E731
    unit = spec["unit"]
    keys = unit.get("rollup_by", [])
    counted_tiers = set(spec["evidence"]["counted_tiers"])
    author_of, kind_of, out.findings = authors(attribution, persons)
    cells: dict = {}  # cell id -> {"person", "values", "kind", "passages"}
    for uid, att in attribution.items():
        if is_counted(spec, att):
            person = author_of[uid]
            c = cells.setdefault(cell_id(spec, att, person), {"person": person, "values": tuple(att[k] for k in keys),
                                                              "kind": kind_of[person], "passages": []})
            c["passages"].append(uid)
    finals = {(r["unit_id"], r["outcome"]): r["code"] for r in final_rows if r["pass"] == "final"}
    outcomes = frame_outcomes(spec)
    pkey, pnum = period_columns(spec)
    pmissing = period_missing(spec)
    rule = drops_not_on_question(spec)
    dropped_ids = set()
    for cid in sorted(cells):
        c = cells[cid]
        person, passages = c["person"], set(c["passages"])
        row = {"unit_id": cid, "author": person, "unit_kind": c["kind"]}
        row.update(dict(zip(keys, c["values"])))
        period = _period(spec, person, passages, evidence, counted_tiers, person_of)
        row[pkey], row[pnum] = (spec["periods"]["labels"][period - 1], str(period)) if period else (pmissing, pmissing)
        for a in spec["attributes"]:
            if a["kind"] == "period":
                continue
            # the author's rows: person-level (the row's unit_id is its own person_id) or on one of the cell's
            # passages; a merged id's rows are its person's (ruling D)
            values = [(r["attribute_kind"], r["value"]) for r in evidence
                      if r["tier"] in counted_tiers and person_of(r["person_id"]) == person
                      and r["attribute_kind"] in a.get("source_attributes", [])
                      and (r["unit_id"] == r["person_id"] or r["unit_id"] in passages)]
            given = [(k, v) for k, v in values if v != ""]
            missing = a.get("missing", "NE")
            try:
                if a["kind"] == "categorical":
                    row[a["key"]] = missing if not given else bucket_first(tables[a["key"]], given,
                                                                         a["bucketer"].get("fallback"), missing)
                else:
                    flags = a.get("flags", [])
                    found = bucket_all(tables[a["key"]], given) if given else set()
                    for flag in flags:
                        row[f"{a['key']}_{flag}"] = "1" if flag in found else "0"
                    row[f"{a['key']}_{missing}"] = "0" if found & set(flags) else "1"
            except ValueError as exc:
                add("frame-value-too-long", f"cell {q(cid)}", f"attribute {q(a['key'])}: {exc}")
                for col in attribute_columns(a):
                    row[col] = ""
        for key, o in outcomes.items():
            row[key] = _outcome_cell(o, [finals[(p, key)] for p in c["passages"] if (p, key) in finals],
                                     cid, key, add)
        if rule is not None and all(row[k] == "" for k in outcomes):
            dropped_ids.add(cid)
            out.dropped.append({"unit_id": cid, "rule": NOT_ON_QUESTION, "reason": rule["reason"]})
            continue
        out.rows.append(row)
    out.findings += check_rows(spec, out.columns, out.rows)
    out.passages = passage_list(spec, attribution, evidence, dropped_ids, author_of)
    return out


def attribute_columns(a: dict) -> list:
    """The frame columns one attribute gives (lines 601-602)."""
    if a["kind"] == "categorical":
        return [a["key"]]
    if a["kind"] == "flags":
        return [f"{a['key']}_{flag}" for flag in a.get("flags", [])] + [f"{a['key']}_{a.get('missing', 'NE')}"]
    return []


def _period(spec: dict, person: str, passages: set, evidence: list, counted_tiers: set, person_of) -> int | None:
    """The cell's period number from 1, or None (lines 623-633)."""
    cuts = spec["periods"]["cuts"]
    for basis in spec["periods"]["basis"]:
        if basis == "work_date":
            years = [year_of(r["value"], "work_date") for r in evidence
                     if r["tier"] in counted_tiers and r["attribute_kind"] == "work_date" and r["unit_id"] in passages]
            found = {period_of(y, cuts) for y in years if y is not None}
            if len(found) == 1:
                return found.pop()
        elif basis == "life_dates":
            year = life_year([r["value"] for r in evidence
                              if r["tier"] in counted_tiers and r["attribute_kind"] == "life_dates"
                              and r["unit_id"] == r["person_id"] and person_of(r["person_id"]) == person])
            if year is not None:
                return period_of(year, cuts)
    return None


def _outcome_cell(outcome: dict, codes: list, cid: str, key: str, add) -> str:
    """One outcome cell (lines 612-621): empty for no final code or NA codes only; the ``missing`` value for at least
    one ``missing`` and no level code; else the outcome's rollup over the level codes. Any other code is an error."""
    levels = {lv["code"] for lv in outcome["levels"]}
    na = set(outcome.get("na_codes", []))
    missing = outcome.get("missing", "NE")
    strange = sorted({c for c in codes if c not in levels | na | {missing}})
    if strange:
        add("frame-code", f"cell {q(cid)}, outcome {q(key)}", f"final code(s) {', '.join(map(q, strange))} are not a "
            "level code, an NA code or the missing value (4.7, lines 620-621)")
        return ""
    level_codes = [c for c in codes if c in levels]
    if level_codes:
        value, error = apply_rule(outcome, level_codes)
        if error:
            add("frame-rollup", f"cell {q(cid)}, outcome {q(key)}", error)
        return value
    return missing if missing in codes else ""


def check_rows(spec: dict, columns: tuple, rows: list) -> list:
    """Every cell checked before anything is written (lines 651-653): each value one its column allows, each
    ``unit_id`` unique, every column present."""
    findings = []
    allowed = allowed_values(spec)
    seen = set()
    for r in rows:
        where = f"cell {q(r.get('unit_id', ''))}"
        absent = [c for c in columns if c not in r]
        if absent:
            findings.append(Finding("frame-column", where, f"no value for {', '.join(map(q, absent))}"))
            continue
        if r["unit_id"] in seen:
            findings.append(Finding("frame-unit-duplicate", where, "a unit_id given twice (4.7, line 652)"))
        seen.add(r["unit_id"])
        for c in columns:
            ok = allowed.get(c)
            if ok is not None and r[c] not in ok:
                findings.append(Finding("frame-value", where, f"column {q(c)} holds {q(r[c])}, which it does not "
                                        f"allow ({', '.join(map(q, sorted(ok)))})"))
            elif ok is None and r[c] == "":
                findings.append(Finding("frame-value", where, f"column {q(c)} is empty"))
    return findings


def allowed_values(spec: dict) -> dict:
    """Each column's allowed values, or None for a column that must only be non-empty (``unit_id``, ``author``)."""
    unit = spec["unit"]
    out: dict = {}
    sets = {ls["key"]: {lv["code"] for lv in ls["levels"]} for ls in unit.get("passage_attributes", [])}
    for key in unit.get("rollup_by", []):
        out[key] = sets.get(key, set())
    out["unit_kind"] = {"person", *unit.get("collective", {}).get("kinds", [])}
    pkey, pnum = period_columns(spec)
    pm = period_missing(spec)
    labels = spec["periods"]["labels"]
    out[pkey] = set(labels) | {pm}
    out[pnum] = {str(i) for i in range(1, len(labels) + 1)} | {pm}
    for a in spec["attributes"]:
        missing = a.get("missing", "NE")
        if a["kind"] == "categorical":
            out[a["key"]] = set(a.get("levels", [])) | {missing}
        elif a["kind"] == "flags":
            for flag in a.get("flags", []):
                out[f"{a['key']}_{flag}"] = {"0", "1"}
            out[f"{a['key']}_{missing}"] = {"0", "1"}
    for key, o in frame_outcomes(spec).items():
        out[key] = {lv["code"] for lv in o["levels"]} | {o.get("missing", "NE"), ""} | \
            ({MIXED} if o["rollup"] == "mixed-if-conflict" else set())
    return out


# --------------------------------------------------------------------------- the passage list (lines 656-671)
def passage_list(spec: dict, attribution: dict, evidence: list, dropped: set, author_of: dict | None = None) -> list:
    """One row per evidence row whose ``unit_id`` is an attribution unit, counted or not, in the order of the evidence
    file; person-level rows are not listed. A row not counted gives the first reason that applies: its tier, an
    exclusion, its attribution status, its cell dropped. ``unit_id`` is the cell, its author read through the merges
    (*author_of*, ruling D); ``person_id`` is the attributed author as the attribution file writes it (rows stay as
    written)."""
    author_of = author_of or {}
    counted_tiers = set(spec["evidence"]["counted_tiers"])
    counted_statuses = set(spec["unit"]["attribution"]["counted_statuses"])
    rows = []
    for r in evidence:
        att = attribution.get(r["unit_id"])
        if att is None:
            continue
        cid = cell_id(spec, att, author_of.get(r["unit_id"]))
        excl = excluded_by(spec, att)
        if r["tier"] not in counted_tiers:
            why = f"tier-{r['tier'] or 'blank'}"
        elif excl is not None:
            why = f"excluded-{excl[0]}-{excl[1]}"
        elif att["status"] not in counted_statuses:
            why = f"attribution-{att['status'] or 'blank'}"
        elif cid in dropped:
            why = NOT_ON_QUESTION
        else:
            why = ""
        rows.append({"unit_id": cid, "passage_id": r["unit_id"], "evidence_id": r["id"],
                     "person_id": att["person_id"], "attribution": att["status"],
                     "counted": "false" if why else "true", "not_counted_reason": why})
    return rows
