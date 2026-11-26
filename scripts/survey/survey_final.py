"""Final codes and the rollup (contract 4.2, lines 397-422; the operator's decisions of 2026-11-25, D2 to D6).

Finalising is fail-closed: where passes A and B agree the final row is theirs (pass A's, marked ``agreed``); where they
disagree, or one pass is missing, it is the adjudication's; without one, nothing is written and the units are listed.
A unit with no pass at all also refuses (D4). No code is ever filled in by the tool (rule 1.3).

The rollup takes the final codes of passage or work units to their author, by each outcome's declared rule.
Both outputs are files named on the command line, inside the study's folder, with a provenance record beside them
(4.6). This module writes nothing; the commands write through ``survey_provenance.write_all``.
"""
from __future__ import annotations

import csv
import io
import os
from dataclasses import dataclass, field
from pathlib import Path

from survey_codes import CODES_COLUMNS, coded_outcomes
from survey_core import Finding, q, resolve_path, symlink_components
from survey_evidence import REGISTRY_COLUMNS
from survey_tables import read_rows

AGREED = "agreed"
AGREED_EVIDENCE_DIFFERED = "agreed; evidence differed"
MIXED = "mixed"


def locate_in_study(study, declared: str, what: str):
    """A path named on the command line, under rule 1.6 (relative to the study's folder, or ``repo:``-rooted), which
    must lie inside the study's folder with no symbolic link on its way. Returns ``(ResolvedPath, findings)``."""
    import unicodedata

    rp, errors = resolve_path(declared, study.study_rel, study.repo_root, what)
    if errors:
        return None, errors
    links = symlink_components(study.repo_root, rp.repo_rel)
    if links:
        return None, [Finding(f"{what}-place", rp.repo_rel, f"a component of the {what} path is a symbolic link "
                              f"({', '.join(map(q, links))})")]
    norm = lambda p: unicodedata.normalize("NFC", p).casefold()  # noqa: E731
    study_real = os.path.realpath(study.repo_root.joinpath(*study.study_rel.split("/"))) if study.study_rel else ""
    inside_path = bool(study.study_rel) and norm(rp.repo_rel).startswith(norm(study.study_rel) + "/")
    inside_real = bool(study_real) and os.path.commonpath([rp.real, study_real]) == study_real and \
        rp.real != study_real
    if not (inside_path and inside_real):
        return None, [Finding(f"{what}-place", rp.repo_rel, f"the {what} lies inside the study's folder (operator "
                              "decision D2)")]
    return rp, []


def csv_bytes(columns: tuple, rows: list) -> bytes:
    """CSV, UTF-8, LF, the header then the rows, cells quoted only where CSV needs it."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(columns)
    for r in rows:
        writer.writerow([r[c] for c in columns])
    return buf.getvalue().encode("utf-8")


# --------------------------------------------------------------------------- the units a study codes (D4)
def study_units(study) -> tuple:
    """``({unit id: author}, findings)``: the units every coded outcome must cover. In a passage or work study the
    attribution file's units, with their attributed authors; in an author study the registry's persons (their
    ``person_id`` rows), each its own author."""
    if study.spec["unit"]["kind"] in ("passage", "work"):
        from survey_attribution import columns
        rp = study.paths.get("/unit/attribution/file")
        if rp is None or not os.path.lexists(rp.real):
            return {}, [Finding("final-units", study.spec_rel, "no attribution file: the units cannot be listed")]
        rows = read_rows(Path(rp.real), rp.repo_rel, columns(study.spec), "attribution-columns")
        return {r["unit_id"]: r["person_id"] for _n, r in rows.rows}, rows.findings
    rp = study.paths.get("/identity/registry")
    if rp is None or not os.path.lexists(rp.real):
        return {}, [Finding("final-units", study.spec_rel, "no registry: an author study's units are its persons")]
    rows = read_rows(Path(rp.real), rp.repo_rel, REGISTRY_COLUMNS, "registry-columns")
    return {r["person_id"]: r["person_id"] for _n, r in rows.rows}, rows.findings


# --------------------------------------------------------------------------- finalising (4.2, lines 397-400; D3, D4)
@dataclass
class Finalised:
    rows: list = field(default_factory=list)  # final rows, CODES_COLUMNS, in output order
    findings: list = field(default_factory=list)


def finalise(study, codes, units: dict) -> Finalised:
    """The final rows for every coded outcome, in the order the study declares them, then in code-point order of
    ``unit_id``. *codes* is the checked ``survey_codes.Codes``; *units* maps each unit to its author."""
    out = Finalised()
    add = lambda rule, where, msg: out.findings.append(Finding(rule, where, msg))  # noqa: E731
    for outcome in coded_outcomes(study.spec):
        passes: dict = {}
        for where, r in codes.rows.get(outcome, []):
            if r["pass"] == "final":
                add("final-in-codes", where, "the codes file holds a final row; final codes go to the file "
                    "survey-finalize writes (operator decision D2), so the passes file has passes A and B only")
                continue
            passes.setdefault(r["unit_id"], {})[r["pass"]] = r
        adjudications = codes.adjudications.get(outcome, {})
        for uid in sorted(units):
            p = passes.get(uid, {})
            a, b = p.get("A"), p.get("B")
            adj = adjudications.get(uid)
            if a is None and b is None:
                add("final-no-pass", uid, f"unit {q(uid)} has no pass for outcome {q(outcome)}; every unit is coded "
                    "before codes are final (operator decision D4)")
                continue
            if a is not None and b is not None and a["code"] == b["code"]:
                differ = sorted(a["evidence_ids"].split(";")) != sorted(b["evidence_ids"].split(";"))
                out.rows.append(dict(a, coder=AGREED, level="", pass_="final",
                                     note=AGREED_EVIDENCE_DIFFERED if differ else AGREED))
                continue
            if adj is None:
                why = "passes A and B disagree" if (a is not None and b is not None) else \
                    f"pass {'B' if b is None else 'A'} is missing"
                add("final-no-adjudication", uid, f"unit {q(uid)}, outcome {q(outcome)}: {why}, and there is no "
                    "adjudication; no final row is written (4.2, lines 398-399)")
                continue
            _where, j = adj
            out.rows.append({"unit_id": uid, "person_id": units[uid], "outcome": outcome, "code": j["code"],
                             "pass_": "final", "coder": j["coder"], "basis": j["basis"], "reporter": j["reporter"],
                             "evidence_ids": j["evidence_ids"], "level": "", "note": j["note"]})
    for r in out.rows:
        r["pass"] = r.pop("pass_")
    return out


# --------------------------------------------------------------------------- the rollup (4.2, lines 403-422; D5)
def rollup_columns(spec: dict) -> tuple:
    """``person_id``; each key in ``unit.rollup_by``; ``author_kind``; one column per coded outcome whose rollup is not
    ``none``, in declared order; ``<outcome>__types`` beside each where ``unit.rollup_types`` is set (D5; 4.2 lines
    411-421)."""
    unit = spec["unit"]
    cols = ["person_id", *unit.get("rollup_by", []), "author_kind"]
    for key, o in coded_outcomes(spec).items():
        if o["rollup"] == "none":
            continue
        cols.append(key)
        if unit.get("rollup_types"):
            cols.append(f"{key}__types")
    return tuple(cols)


@dataclass
class Rolled:
    rows: list = field(default_factory=list)
    findings: list = field(default_factory=list)
    left_out: int = 0  # authors all of whose units were left out by status or exclusion (4.2, lines 409-410)


def apply_rule(outcome: dict, codes: list) -> tuple:
    """One cell's value by the outcome's rule (4.2, lines 412-418), over the codes that remain after NA codes and the
    missing value are skipped. ``(value, error)``; nothing left gives the missing value (line 408)."""
    missing = outcome.get("missing", "NE")
    if not codes:
        return missing, ""
    rule = outcome["rollup"]
    distinct = sorted(set(codes))
    if rule == "single-code":
        if len(distinct) > 1:
            return "", f"the units give {', '.join(map(q, distinct))}; single-code allows one (4.2, line 412)"
        return distinct[0], ""
    if rule == "mixed-if-conflict":
        return (distinct[0] if len(distinct) == 1 else MIXED), ""
    order = {lv["code"]: lv.get("order") for lv in outcome["levels"]}
    if rule == "max-order":
        return max(codes, key=lambda c: order[c]), ""
    if rule == "any-present":
        if outcome["present_code"] in codes:
            return outcome["present_code"], ""
        if outcome["scale"] == "ordinal":
            return min(codes, key=lambda c: order[c]), ""
        declared = [lv["code"] for lv in outcome["levels"]]
        return min(codes, key=declared.index), ""
    raise ValueError(f"no rollup rule {rule!r}")


def roll_up(study, final_rows: list, attribution: dict) -> Rolled:
    """The rollup (4.2, lines 403-422). *final_rows* are the final file's rows; *attribution* maps a unit to its
    attribution row. Rows are one per author and combination of ``rollup_by`` values, in code-point order of
    ``person_id``, then of those values in the order ``rollup_by`` names them."""
    spec = study.spec
    unit = spec["unit"]
    out = Rolled()
    counted = set(unit["attribution"]["counted_statuses"])
    exclude = unit.get("exclude_from_rollup", {})
    keys = unit.get("rollup_by", [])
    types_key = unit.get("rollup_types")
    outcomes = {k: o for k, o in coded_outcomes(spec).items() if o["rollup"] != "none"}
    authors_seen, authors_kept = set(), set()
    cells: dict = {}  # (person, values) -> {outcome: [(code, type)]}
    kind_of: dict = {}
    for uid, a in attribution.items():
        authors_seen.add(a["person_id"])
        if a["status"] not in counted or any(a.get(k) in vals for k, vals in exclude.items()):
            continue
        authors_kept.add(a["person_id"])
        kind_of[a["person_id"]] = a["author_kind"]
        cells.setdefault((a["person_id"], tuple(a[k] for k in keys)), {})
    for r in final_rows:
        if r["pass"] != "final" or r["outcome"] not in outcomes or r["unit_id"] not in attribution:
            continue
        a = attribution[r["unit_id"]]
        if a["status"] not in counted or any(a.get(k) in vals for k, vals in exclude.items()):
            continue
        cell = cells.setdefault((a["person_id"], tuple(a[k] for k in keys)), {})
        cell.setdefault(r["outcome"], []).append((r["code"], a[types_key] if types_key else ""))
    out.left_out = len(authors_seen - authors_kept)
    for (person, values) in sorted(cells):
        row = {"person_id": person, "author_kind": kind_of.get(person, "")}
        row.update(dict(zip(keys, values)))
        for key, o in outcomes.items():
            behind = cells[(person, values)].get(key, [])
            skipped = set(o.get("na_codes", [])) | {o.get("missing", "NE")}
            remaining = [c for c, _t in behind if c not in skipped]
            value, error = apply_rule(o, remaining)
            if error:
                out.findings.append(Finding("rollup-conflict", f"{person} {key}", error))
            row[key] = value
            if types_key:
                row[f"{key}__types"] = ";".join(sorted({t for _c, t in behind}))
        out.rows.append(row)
    return out
