"""Evidence rows (contract 4.1, ``survey-evidence-0``): every row check with the contract's own rule ids, the legacy
exceptions, the forbidden vocabulary (5.3), and the form and presence of a fetch-receipt citation (5.4, section 3).

Re-finding a quotation, at a text-store locus or inside a receipt, is step G: :func:`refind_quotation` is the seam.
Nothing here fetches, and nothing is inferred (rule 1.3): a check reads the cells as written.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from survey_attribution import check_attribution
from survey_attribution import columns as attribution_columns
from survey_core import (
    MAX_JSON_BYTES, Finding, fold, load_json_strict, read_capped, sha256_bytes,
)
from survey_tables import check_table, read_rows

COLUMNS = ("id", "person_id", "attribute_kind", "value", "tier", "source_id", "citation", "locator", "quote", "url",
           "access", "via", "audit", "basis", "reporter", "unit_id", "note", "downgraded_from")

#: The rule ids of 4.1 (lines 330-349), in the table's order.
RULES = ("columns", "id-empty", "id-duplicate", "attribute-kind", "person-unknown", "unit-id", "unit-unknown",
         "unit-person", "id-separator", "tier-unknown", "counted-quote", "counted-citation", "counted-basis",
         "reported-reporter", "own-reporter", "ne-quote", "ne-note", "vocabulary")
#: Rule ids an exceptions file cannot list (4.1, lines 357-358).
UNLISTABLE = ("columns", "id-empty", "id-duplicate")

REGISTRY_COLUMNS = ("person_id", "display_name", "identity_id", "merged_from")
EXCEPTION_COLUMNS = ("id", "rule")
#: A text-store locus (5.4): ``<work slug>#p<N>``, the slug as section 3 defines one.
LOCUS = re.compile(r"[a-z0-9][a-z0-9_-]*#p[0-9]+")
RECEIPT_KEYS = {"url", "quote", "fetched_at", "quote_fold_sha256", "status", "final_url", "content_type", "sha256",
                "found", "context", "reason", "wayback", "receipt_id"}


@dataclass
class EvidenceReport:
    rows: int = 0
    findings: list = field(default_factory=list)
    excused: dict = field(default_factory=dict)  # rule -> count of listed breaches (4.1, line 356)
    exceptions: int = 0  # lines in the exceptions file it was read with
    reported: list = field(default_factory=list)  # 5.4: reported, not errors (a legacy study's unfindable rows)
    not_refound: int = 0  # rows whose quotation step A/B could not re-find (the step G seam)


# --------------------------------------------------------------------------- the declared attribute kinds
def declared_kinds(spec: dict) -> set:
    """The attribute kinds the specification declares: ``evidence.attribute_kinds``, and those the outcomes and
    attributes use (4.1, lines 314-315), the period's ``basis`` included (4.7 reads ``work_date`` and
    ``life_dates`` rows for the period attribute)."""
    kinds = set(spec["evidence"].get("attribute_kinds", []))
    for o in spec["outcomes"]:
        if o["source"]["kind"] == "evidence-attribute":
            kinds.add(o["source"]["attribute"])
    for a in spec["attributes"]:
        kinds.update(a.get("source_attributes", []))
    kinds.update(spec["periods"]["basis"])
    return kinds


# --------------------------------------------------------------------------- the registry, read only
def read_registry(study) -> tuple:
    """The person ids the registry holds, or None when there is no registry. Returns ``(persons, findings)``.
    Building the registry is not in this module."""
    rp = study.paths.get("/identity/registry")
    if rp is None:
        return None, []
    path = study.repo_root / rp.repo_rel
    if not os.path.lexists(path):
        return None, []
    rows = read_rows(path, rp.repo_rel, REGISTRY_COLUMNS, "registry-columns")
    if rows.findings:
        return set(), rows.findings
    persons, findings = set(), []
    for n, r in rows.rows:
        if r["person_id"] == "" or r["person_id"] in persons:
            findings.append(Finding("registry-person", f"{rp.repo_rel}:{n}", f"person_id {r['person_id']!r} is empty "
                                    "or repeated"))
        persons.add(r["person_id"])
    return persons, findings


# --------------------------------------------------------------------------- vocabulary (5.3)
def read_vocabulary(study) -> tuple:
    """The compiled forbidden-vocabulary patterns, or None when no vocabulary is declared."""
    rp = study.paths.get("/vocabulary/forbidden")
    if rp is None:
        return None, []
    where = rp.repo_rel
    try:
        data = read_capped(study.repo_root / rp.repo_rel, MAX_JSON_BYTES)
    except OSError as exc:
        return [], [Finding("vocabulary-file", where, f"cannot be read: {exc}")]
    if data is None:
        return [], [Finding("vocabulary-file", where, f"larger than {MAX_JSON_BYTES} bytes")]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [], [Finding("vocabulary-file", where, f"not UTF-8: {exc}")]
    patterns, findings = [], []
    for n, line in enumerate(text.splitlines(), start=1):
        if line.strip() == "" or line.lstrip().startswith("#"):
            continue
        try:
            patterns.append((n, re.compile(line, re.IGNORECASE)))
        except re.error as exc:
            findings.append(Finding("vocabulary-file", f"{where}:{n}", f"{line!r} does not compile: {exc}"))
    return patterns, findings


# --------------------------------------------------------------------------- receipts (5.4; section 3 line 223)
def receipt_id(url: str, quote: str) -> str:
    """The first 24 hex characters of the SHA-256 of the URL, a line feed and the quote folded without spaces
    (4.4, lines 483-484)."""
    return sha256_bytes(f"{url}\n{fold(quote, spaces=False)}".encode("utf-8"))[:24]


def cites_receipt(row: dict) -> bool:
    """A row whose ``locator`` is not a text-store locus is checked against the fetch receipt for its ``url`` and
    quote (5.4, lines 770-772)."""
    return LOCUS.fullmatch(row["locator"]) is None


def refind_quotation(study, row: dict, receipt: dict | None) -> bool | None:
    """THE RE-FIND SEAM (step G). Whether the quotation occurs at its locus, or in its receipt. Step B does not
    re-find: it returns None ("not checked"), and nothing counts it as found."""
    return None


def _check_receipt(study, row: dict, where: str, legacy: bool, report: EvidenceReport) -> list:
    """The citation's form and presence, which need no network. Returns findings; in a legacy study an absent or
    unusable receipt is reported and counted, not an error (5.4, lines 773-775)."""
    if "receipts" not in study.spec["evidence"]:
        return [Finding("receipts-undeclared", where, "the row cites a fetch receipt (its locator is not a "
                        "<work slug>#p<N> locus) but evidence.receipts is not declared (section 3)")]
    rp = study.paths["/evidence/receipts"]
    problem = None
    if row["url"] == "":
        problem = ("receipt-url", "the row cites a fetch receipt but has no url to find it by (5.4)")
    else:
        rid = receipt_id(row["url"], row["quote"])
        rel = f"{rp.repo_rel}/{rid}.json"
        path = study.repo_root / rel
        if not os.path.lexists(path):
            problem = ("receipt-missing", f"no fetch receipt {rel}; the quotation cannot be re-found (5.4)")
        else:
            try:
                data = read_capped(path, MAX_JSON_BYTES)
            except OSError as exc:
                data, problem = None, ("receipt-malformed", f"{rel} cannot be read: {exc}")
            if data is not None:
                doc, errs = load_json_strict(data, rel)
                if errs or not isinstance(doc, dict) or set(doc) - RECEIPT_KEYS:
                    problem = ("receipt-malformed", f"{rel} is not a fetch receipt object (4.4)")
                elif doc.get("receipt_id") != rid or doc.get("url") != row["url"] or \
                        not isinstance(doc.get("quote"), str) or \
                        fold(doc["quote"], spaces=False) != fold(row["quote"], spaces=False):
                    problem = ("receipt-malformed", f"{rel} is not the receipt of this row's url and quote")
                else:
                    if refind_quotation(study, row, doc) is None:
                        report.not_refound += 1
            elif problem is None:
                problem = ("receipt-malformed", f"{rel} is larger than {MAX_JSON_BYTES} bytes")
    if problem is None:
        return []
    if legacy:
        report.reported.append(Finding(problem[0], where, problem[1] + " (reported: a legacy study, 5.4)"))
        return []
    return [Finding(problem[0], where, problem[1])]


# --------------------------------------------------------------------------- the row checks (4.1)
def row_breaches(study, row: dict, ids: dict, persons: set | None, units: dict, kinds: set, vocab: list) -> list:
    """Every 4.1 rule (but ``columns``) one row breaks: a list of ``(rule, message)`` in the table's order."""
    spec = study.spec
    ev = spec["evidence"]
    passage = spec["unit"]["kind"] in ("passage", "work")
    out = []
    add = lambda rule, msg: out.append((rule, msg))  # noqa: E731
    if row["id"] == "":
        add("id-empty", "an empty id")
    elif ids[row["id"]] > 1:
        add("id-duplicate", f"id {row['id']!r} is repeated")
    if row["attribute_kind"] not in kinds:
        add("attribute-kind", f"attribute_kind {row['attribute_kind']!r} is not declared")
    if persons is not None and row["person_id"] not in persons:
        add("person-unknown", f"person_id {row['person_id']!r} is not in the registry")
    uid = row["unit_id"]
    if not passage and uid != "":
        add("unit-id", "a unit_id in an author study")
    if passage and uid == "":
        add("unit-id", f"no unit_id in a {spec['unit']['kind']} study")
    if passage and uid != "":
        if uid in units:
            if units[uid]["person_id"] != row["person_id"]:
                add("unit-person", f"unit {uid!r} is attributed to {units[uid]['person_id']!r}, not to "
                    f"{row['person_id']!r}")
        elif uid != row["person_id"]:
            add("unit-unknown", f"unit_id {uid!r} is neither an attribution unit nor the row's person_id")
    if "|" in row["person_id"] or "|" in uid:
        add("id-separator", "a '|' in person_id or unit_id (4.7)")
    tier = row["tier"]
    if tier not in ev["tiers"]:
        add("tier-unknown", f"tier {tier!r} is not declared")
    counted = tier in ev["counted_tiers"]
    if counted and row["quote"] == "":
        add("counted-quote", "a counted row without a quote")
    if counted and row["citation"] == "" and row["source_id"] == "":
        add("counted-citation", "a counted row with neither citation nor source_id")
    if counted and row["basis"] not in ("own", "reported"):
        add("counted-basis", f"a counted row whose basis {row['basis']!r} is not own or reported")
    if row["basis"] == "reported" and row["reporter"] == "":
        add("reported-reporter", "a reported row without a reporter")
    if row["basis"] == "own" and row["reporter"] != "":
        add("own-reporter", "an own row that names a reporter")
    if tier == ev["not_established_tier"]:
        if row["quote"] != "":
            add("ne-quote", "a not-established row with a quote")
        if row["note"] == "":
            add("ne-note", "a not-established row without a note (what was tried)")
    if vocab:
        exempt = set(spec.get("vocabulary", {}).get("exempt_columns", ["quote"]))
        for col in COLUMNS:
            if col in exempt or row[col] == "":
                continue
            folded = fold(row[col])
            for line, pattern in vocab:
                if pattern.search(folded):
                    add("vocabulary", f"column {col} matches forbidden pattern {pattern.pattern!r} (line {line})")
                    break
    return out


def _read_exceptions(study) -> tuple:
    """The legacy exceptions file: ``{(id, rule): line}``, and its findings."""
    rp = study.paths.get("/evidence/legacy_exceptions")
    if rp is None:
        return {}, []
    rows = read_rows(study.repo_root / rp.repo_rel, rp.repo_rel, EXCEPTION_COLUMNS, "exceptions-columns")
    if rows.findings:
        return {}, rows.findings
    listed, findings = {}, []
    for n, r in rows.rows:
        at = f"{rp.repo_rel}:{n}"
        if r["rule"] in UNLISTABLE:
            findings.append(Finding("exceptions-unlistable", at, f"rule {r['rule']!r} cannot be listed (4.1)"))
        elif r["rule"] not in RULES:
            findings.append(Finding("exceptions-rule", at, f"{r['rule']!r} is not a rule id of 4.1"))
        elif r["id"] == "":
            findings.append(Finding("exceptions-id", at, "an exception names no row id"))
        elif (r["id"], r["rule"]) in listed:
            findings.append(Finding("exceptions-duplicate", at, f"({r['id']!r}, {r['rule']!r}) is listed twice"))
        else:
            listed[(r["id"], r["rule"])] = n
    return listed, findings


def check_row_files(study) -> EvidenceReport:
    """Every row file sections 4.1, 4.3 and 4.8 define that is present: the evidence file (with the registry it
    needs), the attribution file, the legacy exceptions, the vocabulary file and the bucket tables."""
    spec = study.spec
    report = EvidenceReport()
    persons, reg_findings = read_registry(study)
    report.findings += reg_findings
    vocab, vocab_findings = read_vocabulary(study)
    report.findings += vocab_findings
    report.findings += check_tables(study)

    rows = None
    rp = study.paths.get("/evidence/file")
    if spec["evidence"]["format"] == "plugin":
        report.findings.append(Finding("evidence-plugin", rp.repo_rel, "evidence in a plugin format is read through "
                                       "its reader plug-in, which this version does not load; the rows are not "
                                       "checked"))
    elif os.path.lexists(study.repo_root / rp.repo_rel):  # absent only in a draft (section 3's file check)
        rows = read_rows(study.repo_root / rp.repo_rel, rp.repo_rel, COLUMNS, "columns")
        report.findings += rows.findings
        if rows.findings:
            rows = None

    units = {}
    if spec["unit"]["kind"] in ("passage", "work"):
        stand_in = persons
        if stand_in is None:  # the registry's own sources stand in (4.4); this can only refuse more
            stand_in = set(_attribution_persons(study))
            if rows is not None:
                stand_in |= {r["person_id"] for _n, r in rows.rows}
        att = check_attribution(study, stand_in)
        report.findings += att.findings
        units = att.units
    if rows is None:
        return report
    report.rows = len(rows.rows)
    if persons is None:
        report.findings.append(Finding("registry-missing", study.paths["/identity/registry"].repo_rel,
                                       "the registry does not exist; a missing registry is itself an error (4.1)"))
    _check_rows(study, rows, rp.repo_rel, persons, units, vocab or [], report)
    return report


def _check_rows(study, rows, where: str, persons, units: dict, vocab: list, report: EvidenceReport) -> None:
    """The 4.1 row checks over the whole file, the legacy exceptions, and the receipt citations."""
    spec = study.spec
    kinds = declared_kinds(spec)
    listed, exc_findings = _read_exceptions(study)
    report.findings += exc_findings
    report.exceptions = len(listed)
    legacy = spec["status"] == "legacy"
    counted = spec["evidence"]["counted_tiers"]
    ids: dict = {}
    for _n, r in rows.rows:
        ids[r["id"]] = ids.get(r["id"], 0) + 1
    used = set()
    for n, r in rows.rows:
        at = f"{where}:{n}"
        nameable = r["id"] != "" and ids[r["id"]] == 1
        for rule, msg in row_breaches(study, r, ids, persons, units, kinds, vocab):
            key = (r["id"], rule)
            if nameable and key in listed:
                used.add(key)
                report.excused[rule] = report.excused.get(rule, 0) + 1
                continue
            report.findings.append(Finding(rule, at, msg))
        if r["tier"] in counted:
            if cites_receipt(r):
                report.findings += _check_receipt(study, r, at, legacy, report)
            elif refind_quotation(study, r, None) is None:
                report.not_refound += 1
    if listed:
        exc_rel = study.paths["/evidence/legacy_exceptions"].repo_rel
        for key, line in sorted(listed.items(), key=lambda kv: kv[1]):
            if key not in used:
                report.findings.append(Finding("exceptions-stale", f"{exc_rel}:{line}", f"row {key[0]!r} does not "
                                               f"break rule {key[1]!r} (or is gone); the file must not claim more "
                                               "than is true (4.1)"))


def check_tables(study) -> list:
    """Every bucket table the attributes name (4.8)."""
    findings = []
    for i, a in enumerate(study.spec["attributes"]):
        rp = study.paths.get(f"/attributes/{i}/bucketer/table")
        if rp is None or not os.path.lexists(study.repo_root / rp.repo_rel):
            continue
        allowed = a.get("flags") if a["kind"] == "flags" else a.get("levels")
        _rows, errs = check_table(study.repo_root / rp.repo_rel, rp.repo_rel, allowed)
        findings += errs
        fallback = a["bucketer"].get("fallback")
        if fallback is not None and allowed is not None and fallback not in allowed:
            findings.append(Finding("table-fallback", f"{study.spec_rel}#/attributes/{i}/bucketer/fallback",
                                    f"fallback {fallback!r} is not one of the attribute's levels (contract silent; "
                                    "refused)"))
    return findings


def _attribution_persons(study) -> set:
    rp = study.paths.get("/unit/attribution/file")
    if rp is None or not os.path.lexists(study.repo_root / rp.repo_rel):
        return set()
    rows = read_rows(study.repo_root / rp.repo_rel, rp.repo_rel, attribution_columns(study.spec),
                     "attribution-columns")
    return {r["person_id"] for _n, r in rows.rows}
