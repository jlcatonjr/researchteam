"""Codes and adjudications (contract 4.2): their rows, every check on them, and agreement between passes A and B.

Rule 1.3 holds: no tool fills a missing code. A code is written by a named coder and checked here, never derived.
Agreement follows the operator's decisions of 2026-11-25 (``statistics``). Finalising and the rollup are not in this
module.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction
from pathlib import Path

from survey_core import Finding, q, unsafe_chars
from survey_tables import read_rows

CODES_COLUMNS = ("unit_id", "person_id", "outcome", "code", "pass", "coder", "basis", "reporter", "evidence_ids",
                 "level", "note")
ADJUDICATION_COLUMNS = ("unit_id", "outcome", "code", "coder", "basis", "reporter", "evidence_ids", "note")
PASSES = ("A", "B", "final")
MISSING_PASS = ("missing pass: A, ", "missing pass: B, ")
#: Identifier cells: compared exactly, so they hold none of the shared unsafe characters (a tightening).
CODES_ID_COLUMNS = ("unit_id", "person_id", "outcome", "code", "pass", "coder", "basis", "evidence_ids")


@dataclass
class Codes:
    """The code rows of every codes file, by outcome, and the adjudications, as read and checked."""

    rows: dict = field(default_factory=dict)  # outcome -> [(where, row)]
    adjudications: dict = field(default_factory=dict)  # outcome -> {unit_id: (where, row)}
    findings: list = field(default_factory=list)


def coded_outcomes(spec: dict) -> dict:
    """``{outcome key: outcome}`` for every outcome whose source is ``codes``."""
    return {o["key"]: o for o in spec["outcomes"] if o["source"]["kind"] == "codes"}


def allowed_codes(outcome: dict) -> set:
    """An outcome's allowed codes (4.2, lines 372-373): its level codes, its NA codes and its ``missing`` value."""
    return ({lv["code"] for lv in outcome["levels"]} | set(outcome.get("na_codes", [])) |
            {outcome.get("missing", "NE")})


@dataclass
class Context:
    """What the checks read beside the code files: the evidence ids with their owner, and the attribution units."""

    evidence_owner: dict  # evidence id -> the person the row belongs to
    units: dict  # unit id -> attributed author (passage or work study); empty in an author study
    passage: bool
    persons: set | None  # the registry's ids, or None without a registry


def evidence_owners(evidence_rows: list, units: dict, passage: bool) -> dict:
    """Who each evidence row belongs to (4.2, lines 380-382): in a passage or work study, "a unit's evidence belongs
    to the unit's attributed author", and a person-level row (its ``unit_id`` the person's own id) to that person; in
    an author study, its ``person_id``."""
    owners = {}
    for r in evidence_rows:
        if passage and r["unit_id"] in units:
            owners[r["id"]] = units[r["unit_id"]]
        else:
            owners[r["id"]] = r["person_id"]
    return owners


def _check_row(row: dict, outcome: dict | None, where: str, ctx: Context, expected_person: str, add,
               adjudication: bool) -> None:
    """The checks a codes row and an adjudication share (4.2, lines 377-383; 392: adjudications "are checked like
    codes rows")."""
    prefix = "adjudication" if adjudication else "codes"
    for col in (CODES_ID_COLUMNS if not adjudication else [c for c in CODES_ID_COLUMNS if c in row]):
        bad = unsafe_chars(row[col])
        if bad:
            add(f"{prefix}-value", where, f"{col} {q(row[col])} holds a control, format or line-separator character "
                "(an identifier cell; a tightening)")
    if outcome is None:
        return
    missing = outcome.get("missing", "NE")
    if row["code"] not in allowed_codes(outcome):
        add(f"{prefix}-code", where, f"code {q(row['code'])} is not a level code, NA code or the missing value of "
            f"{q(outcome['key'])} (4.2, lines 372-373)")
    if row["coder"] == "":
        add(f"{prefix}-coder", where, "no coder: a code is always written by a named agent or person (rule 1.3"
            + ("; 4.2 line 392: coder is required" if adjudication else "") + ")")
    if row["code"] != missing:
        if row["evidence_ids"] == "":
            add(f"{prefix}-evidence", where, f"code {q(row['code'])} is not the missing value and has no evidence_ids "
                "(4.2, line 378)")
        if row["basis"] == "":
            add(f"{prefix}-basis", where, f"code {q(row['code'])} is not the missing value and has no basis (4.2, line "
                "378)")
    if row["basis"] not in ("", "own", "reported"):
        add(f"{prefix}-basis", where, f"basis {q(row['basis'])} is not own or reported (a tightening: 4.1's two "
            "bases)")
    if row["basis"] == "reported" and row["reporter"] == "":
        add(f"{prefix}-reporter", where, "a reported code without a reporter (4.2, line 379)")
    for eid in [e for e in row["evidence_ids"].split(";")] if row["evidence_ids"] else []:
        if eid not in ctx.evidence_owner:
            add(f"{prefix}-evidence-unknown", where, f"evidence id {q(eid)} does not exist (4.2, line 380)")
        elif ctx.evidence_owner[eid] != expected_person:
            add(f"{prefix}-evidence-person", where, f"evidence id {q(eid)} belongs to {q(ctx.evidence_owner[eid])}, "
                f"not to {q(expected_person)} (4.2, lines 380-382)")


def _unit_person(row: dict, where: str, ctx: Context, add, prefix: str, person: str | None) -> str:
    """The person a coded unit belongs to, and the unit checks (a tightening: 4.2 names none). In a passage or work
    study the unit is an attribution unit, and a codes row's ``person_id`` is its attributed author; in an author
    study the unit is a person the registry holds, and the codes row's ``person_id`` is that person."""
    uid = row["unit_id"]
    if ctx.passage:
        if uid not in ctx.units:
            add(f"{prefix}-unit", where, f"unit {q(uid)} is not a unit of the attribution file (a tightening)")
            return person or ""
        author = ctx.units[uid]
        if person is not None and person != author:
            add(f"{prefix}-unit-person", where, f"unit {q(uid)} is attributed to {q(author)}, not {q(person)} (a "
                "tightening)")
        return author
    if ctx.persons is not None and uid not in ctx.persons:
        add(f"{prefix}-unit", where, f"unit {q(uid)} is not a person the registry holds (a tightening)")
    if person is not None and person != uid:
        add(f"{prefix}-unit-person", where, f"in an author study a unit is its person; {q(person)} is not {q(uid)} (a "
            "tightening)")
    return uid


def read_codes(study, ctx: Context) -> Codes:
    """Read and check every codes file and adjudications file the coded outcomes name (4.2)."""
    out = Codes()
    add = lambda rule, where, msg: out.findings.append(Finding(rule, where, msg))  # noqa: E731
    outcomes = coded_outcomes(study.spec)
    order = list(outcomes)  # the order the study declares them (as the frame orders its outcome columns, line 603)
    files: dict = {}  # codes file (repo_rel) -> (ResolvedPath, [outcome keys that name it])
    for i, o in enumerate(study.spec["outcomes"]):
        if o["source"]["kind"] != "codes":
            continue
        rp = study.paths.get(f"/outcomes/{i}/source/codes_file")
        if rp is not None:
            files.setdefault(rp.repo_rel, (rp, []))[1].append(o["key"])
    for rel, (rp, keys) in files.items():
        if not os.path.lexists(rp.real):
            continue  # absent only in a draft (section 3's file check)
        rows = read_rows(Path(rp.real), rel, CODES_COLUMNS, "codes-columns")
        out.findings += rows.findings
        for n, r in rows.rows:
            where = f"{rel}:{n}"
            outcome = outcomes.get(r["outcome"])
            if outcome is None:
                add("codes-outcome", where, f"outcome {q(r['outcome'])} is not declared with source codes (4.2, line "
                    "377)")
            elif r["outcome"] not in keys:
                add("codes-outcome", where, f"outcome {q(r['outcome'])} names another codes file; this file belongs "
                    f"to {q(', '.join(keys))} (a tightening)")
                outcome = None
            if r["pass"] not in PASSES:
                add("codes-pass", where, f"pass {q(r['pass'])} is not A, B or final (4.2, line 372)")
            person = _unit_person(r, where, ctx, add, "codes", r["person_id"])
            _check_row(r, outcome, where, ctx, person, add, adjudication=False)
            if outcome is not None:
                out.rows.setdefault(r["outcome"], []).append((where, r))
    for i, o in enumerate(study.spec["outcomes"]):
        if o["source"]["kind"] != "codes":
            continue
        rp = study.paths.get(f"/outcomes/{i}/source/adjudications")
        if rp is None or not os.path.lexists(rp.real):
            continue  # it may be absent (section 3, line 219)
        rows = read_rows(Path(rp.real), rp.repo_rel, ADJUDICATION_COLUMNS, "adjudication-columns")
        out.findings += rows.findings
        adj = out.adjudications.setdefault(o["key"], {})
        for n, r in rows.rows:
            where = f"{rp.repo_rel}:{n}"
            if r["outcome"] != o["key"]:
                add("adjudication-outcome", where, f"outcome {q(r['outcome'])} is not {q(o['key'])}, whose "
                    "adjudications file this is (4.2, line 391)")
                continue
            if r["note"] == "":
                add("adjudication-note", where, "an adjudication without a note (4.2, line 392)")
            person = _unit_person(r, where, ctx, add, "adjudication", None)
            _check_row(r, o, where, ctx, person, add, adjudication=True)
            if r["unit_id"] in adj:
                add("adjudication-duplicate", where, f"a second adjudication for unit {q(r['unit_id'])} (checked like "
                    "codes rows: one row per unit and outcome, 4.2 lines 383 and 392)")
                continue
            adj[r["unit_id"]] = (where, r)
    out.rows = {k: out.rows[k] for k in order if k in out.rows}
    _check_passes(out, add)
    return out


def _check_passes(codes: Codes, add) -> None:
    """The checks across rows (4.2, lines 383-395): one row per unit, outcome and pass; a final row needs both passes
    unless it comes from a missing-pass adjudication; an adjudication is not for a unit on which A and B agree; where
    a pass is missing the adjudication's note says so, with a reason."""
    for outcome, rows in codes.rows.items():
        by_unit: dict = {}
        for where, r in rows:
            passes = by_unit.setdefault(r["unit_id"], {})
            if r["pass"] in passes:
                add("codes-duplicate", where, f"a second {r['pass']} row for unit {q(r['unit_id'])} and outcome "
                    f"{q(outcome)} (4.2, line 383)")
                continue
            passes[r["pass"]] = (where, r)
        adj = codes.adjudications.get(outcome, {})
        for uid, passes in by_unit.items():
            if "final" in passes and not ("A" in passes and "B" in passes):
                a = adj.get(uid)
                lacking = [p for p in ("A", "B") if p not in passes]
                note = a[1]["note"] if a else ""
                ok = a is not None and len(lacking) == 1 and note.startswith(f"missing pass: {lacking[0]}, ")
                ok = ok and _same_as_adjudication(passes["final"][1], a[1])
                if not ok:
                    add("codes-final-unpaired", passes["final"][0], f"a final row for unit {q(uid)} that lacks "
                        f"{' and '.join(lacking)}, not from an adjudication whose note begins 'missing pass: "
                        f"{lacking[0]}, ' (4.2, lines 384-386)")
        for uid, (where, a) in adj.items():
            passes = by_unit.get(uid, {})
            has_a, has_b = "A" in passes, "B" in passes
            if has_a and has_b and passes["A"][1]["code"] == passes["B"][1]["code"]:
                add("adjudication-agreed", where, f"passes A and B agree on unit {q(uid)}: an agreed code is not "
                    "changed (4.2, lines 393-394)")
            elif not has_a and not has_b:
                add("adjudication-no-pass", where, f"unit {q(uid)} has neither pass A nor pass B (contract silent; "
                    "refused)")
            elif not (has_a and has_b):
                lacking = "A" if not has_a else "B"
                prefix = f"missing pass: {lacking}, "
                if not a["note"].startswith(prefix) or a["note"][len(prefix):].strip() == "":
                    add("adjudication-missing-pass", where, f"pass {lacking} is missing for unit {q(uid)}, so the "
                        f"note begins {q(prefix)} followed by the reason (4.2, lines 394-395)")
            elif any(a["note"].startswith(p) for p in MISSING_PASS):
                add("adjudication-missing-pass", where, f"the note says a pass is missing, but unit {q(uid)} has both "
                    "(a tightening)")


def _same_as_adjudication(final: dict, adjudication: dict) -> bool:
    """A final row "comes from" an adjudication when it carries its code, coder, basis, reporter, evidence and note
    (4.2, lines 397-399)."""
    return all(final[c] == adjudication[c] for c in ("code", "coder", "basis", "reporter", "evidence_ids", "note"))


# --------------------------------------------------------------------------- agreement (4.2, lines 400-401)
UNDEFINED = "undefined"


@dataclass
class Agreement:
    """The agreement of one outcome (4.2, line 400; operator decisions of 2026-11-25). The statistics are exact
    fractions, or None where undefined."""

    outcome: str
    units: int  # n: units with both an A and a B row
    agreeing: int  # of those, units where A and B give the same code
    missing_pass: int  # units with exactly one of the two passes
    raw: Fraction | None = None
    kappa: Fraction | None = None
    ac1: Fraction | None = None


def statistics(pairs: list, allowed: set) -> tuple:
    """Raw agreement, Cohen's kappa and Gwet's AC1 over *pairs* (``(code A, code B)`` for each unit with both passes),
    exactly, as fractions; None where undefined (operator decisions of 2026-11-25, "standard definitions"):

    - every code is its own category, NA codes and the missing value included;
    - raw p_a = agreeing / n;
    - kappa, unweighted also for ordered levels: p_e = sum over codes of p_A(k) * p_B(k);
      kappa = (p_a - p_e) / (1 - p_e);
    - AC1: q = the number of codes *allowed* for the outcome (its level codes, NA codes and missing value, as the
      specification declares them, not those that occur); pi_k = (p_A(k) + p_B(k)) / 2;
      p_e1 = (1 / (q - 1)) * sum over the q allowed codes of pi_k * (1 - pi_k); AC1 = (p_a - p_e1) / (1 - p_e1);
    - undefined: n = 0 (all three); 1 - p_e = 0 (kappa); q <= 1 or 1 - p_e1 = 0 (AC1)."""
    n = len(pairs)
    if n == 0:
        return None, None, None
    raw = Fraction(sum(1 for a, b in pairs if a == b), n)
    count_a, count_b = {}, {}
    for a, b in pairs:
        count_a[a] = count_a.get(a, 0) + 1
        count_b[b] = count_b.get(b, 0) + 1
    p_a = {k: Fraction(v, n) for k, v in count_a.items()}
    p_b = {k: Fraction(v, n) for k, v in count_b.items()}
    p_e = sum((p_a.get(k, 0) * p_b.get(k, 0) for k in set(p_a) | set(p_b)), Fraction(0))
    kappa = None if p_e == 1 else (raw - p_e) / (1 - p_e)
    q = len(allowed)
    ac1 = None
    if q > 1:
        pi = {k: (p_a.get(k, Fraction(0)) + p_b.get(k, Fraction(0))) / 2 for k in allowed}
        p_e1 = sum((v * (1 - v) for v in pi.values()), Fraction(0)) / (q - 1)
        ac1 = None if p_e1 == 1 else (raw - p_e1) / (1 - p_e1)
    return raw, kappa, ac1


def three_decimals(value: Fraction | None) -> str:
    """A statistic as printed: rounded half to even at three decimals, from the exact fraction (Python's ``round`` of
    a Fraction rounds half to even exactly), and formatted with ``decimal``, so every platform and Python version
    prints the same (rule 1.5); ``undefined`` for None."""
    if value is None:
        return UNDEFINED
    thousandths = round(value * 1000)
    return str((Decimal(thousandths).scaleb(-3)).quantize(Decimal("0.001"), rounding=ROUND_HALF_EVEN))


def agreement(codes: Codes, outcomes: dict | None = None) -> list:
    """Agreement per outcome (4.2, lines 400-401), in the order the study declares the outcomes: over the units with
    both an A and a B row (a unit with one pass is left out of all three statistics and counted apart), raw
    agreement, Cohen's kappa and Gwet's AC1 (see :func:`statistics`). *outcomes* maps an outcome key to its
    declaration, for the codes it allows."""
    out = []
    for outcome in codes.rows:  # in the order the study declares the outcomes (see read_codes)
        by_unit: dict = {}
        for _where, r in codes.rows[outcome]:
            if r["pass"] in ("A", "B"):
                by_unit.setdefault(r["unit_id"], {})[r["pass"]] = r["code"]
        pairs = [(p["A"], p["B"]) for p in by_unit.values() if "A" in p and "B" in p]
        allowed = allowed_codes(outcomes[outcome]) if outcomes and outcome in outcomes else \
            {c for pair in pairs for c in pair}
        raw, kappa, ac1 = statistics(pairs, allowed)
        out.append(Agreement(outcome, len(pairs), sum(1 for a, b in pairs if a == b),
                             sum(1 for p in by_unit.values() if len(p) == 1), raw, kappa, ac1))
    return out
