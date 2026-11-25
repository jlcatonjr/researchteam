"""Evidence rows (contract 4.1, ``survey-evidence-0``): every row check with the contract's own rule ids, the legacy
exceptions, the forbidden vocabulary (5.3), and the form and presence of a fetch-receipt citation (5.4, section 3).

Re-finding a quotation, at a text-store locus or inside a receipt, is step G: :func:`refind_quotation` is the seam.
Nothing here fetches, and nothing is inferred (rule 1.3): a check reads the cells as written. Every file is opened
at its resolved place under rule 1.6, and every value from a file is quoted with ``repr`` in a message.
"""
from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from survey_attribution import check_attribution
from survey_core import (
    MAX_JSON_BYTES, Finding, fold, inside, load_json_strict, q, read_capped, reason, sha256_bytes,
)
from survey_tables import MAX_PATTERNS, check_table, compile_pattern, read_rows, read_rows_hashed, search

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
#: A fetch receipt's fields (4.4, lines 480-481); ``sha256``, ``context`` and ``wayback`` may be absent (485-486).
RECEIPT_KEYS = ("url", "quote", "fetched_at", "quote_fold_sha256", "status", "final_url", "content_type", "sha256",
                "found", "context", "reason", "wayback", "receipt_id")
RECEIPT_OPTIONAL = ("sha256", "context", "wayback")
RECEIPT_REQUIRED = tuple(k for k in RECEIPT_KEYS if k not in RECEIPT_OPTIONAL)
#: Receipt problems that 5.4 lets a legacy study report instead of failing: the quotation "cannot be re-found"
#: because the row predates receipts (lines 773-775). A receipt that is there but broken is an error everywhere.
LEGACY_REPORTABLE = ("receipt-missing", "receipt-url")


@dataclass
class EvidenceReport:
    rows: int = 0
    findings: list = field(default_factory=list)
    excused: dict = field(default_factory=dict)  # rule -> count of listed breaches (4.1, line 356)
    exceptions: int = 0  # lines in the exceptions file it was read with
    reported: list = field(default_factory=list)  # 5.4: reported, not errors (a legacy study's unfindable rows)
    not_refound: int = 0  # counted rows whose quotation this version could not re-find (the step G seam)


# --------------------------------------------------------------------------- the declared attribute kinds
def declared_kinds(spec: dict) -> set:
    """The attribute kinds the specification declares: ``evidence.attribute_kinds``, and those the outcomes and
    attributes use (4.1, line 314), the period attribute included: it reads ``work_date`` and ``life_dates`` rows
    (4.7, lines 626 and 630; 3, lines 269-270), which ``periods.basis`` names."""
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
    A row holds its ``person_id`` and every id listed in its ``merged_from`` (``;``-separated): two ids a ``merge``
    made one person (4.4, line 497) are both that person's, so evidence rows may still carry the merged id.
    Building the registry is not in this module."""
    rp = study.paths.get("/identity/registry")
    if rp is None or not os.path.lexists(rp.real):
        return None, []
    rows = read_rows(Path(rp.real), rp.repo_rel, REGISTRY_COLUMNS, "registry-columns")
    if rows.findings:
        return set(), rows.findings
    persons, findings = set(), []
    for n, r in rows.rows:
        merged = [m for m in r["merged_from"].split(";") if m != ""] if r["merged_from"] else []
        for pid in (r["person_id"], *merged):
            if pid == "" or pid in persons:
                findings.append(Finding("registry-person", f"{rp.repo_rel}:{n}", f"id {q(pid)} is empty or held "
                                        "twice (as a person_id or in merged_from)"))
            persons.add(pid)
    return persons, findings


# --------------------------------------------------------------------------- vocabulary (5.3)
def read_vocabulary(study) -> tuple:
    """The compiled forbidden-vocabulary patterns, or None when none is declared or (in a draft) the file is not
    there. Matched without regard to case (5.3, line 753)."""
    rp = study.paths.get("/vocabulary/forbidden")
    if rp is None or not os.path.lexists(rp.real):
        return None, []
    where = rp.repo_rel
    try:
        data = read_capped(Path(rp.real), MAX_JSON_BYTES)
    except OSError as exc:
        return [], [Finding("vocabulary-file", where, f"cannot be read: {reason(exc)}")]
    if data is None:
        return [], [Finding("vocabulary-file", where, f"larger than {MAX_JSON_BYTES} bytes")]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [], [Finding("vocabulary-file", where, f"not UTF-8: {reason(exc)}")]
    patterns, findings = [], []
    for n, line in enumerate(text.splitlines(), start=1):
        if line.strip() == "" or line.lstrip().startswith("#"):
            continue
        if len(patterns) >= MAX_PATTERNS:
            findings.append(Finding("vocabulary-file", where, f"more than {MAX_PATTERNS} patterns"))
            break
        pattern, why = compile_pattern(line, re.IGNORECASE)
        if pattern is None:
            findings.append(Finding("vocabulary-file", f"{where}:{n}", f"{q(line)} {why}"))
        else:
            patterns.append((n, pattern))
    return patterns, findings


# --------------------------------------------------------------------------- receipts (5.4; section 3 line 223)
def receipt_id(url: str, quote: str) -> str:
    """The first 24 hex characters of the SHA-256 of the URL, a line feed and the quote folded without spaces
    (4.4, lines 483-484)."""
    return sha256_bytes(f"{url}\n{fold(quote, spaces=False)}".encode("utf-8"))[:24]


def cites_receipt(row: dict) -> bool:
    """A row with a ``locator`` that is not a text-store locus is checked against the fetch receipt for its ``url``
    and quote (5.4, lines 770-772). An empty locator is not given (section 4, line 276): it cites nothing."""
    return row["locator"] != "" and LOCUS.fullmatch(row["locator"]) is None


def refind_quotation(study, row: dict, receipt: dict | None) -> bool | None:
    """THE RE-FIND SEAM (step G). Whether the quotation occurs at its locus, or in its receipt. Step B does not
    re-find: it returns None ("not checked"), and nothing counts it as found. A receipt's own ``found`` field is not
    read either: whether a ``found: false`` receipt fails the row is step G's to decide with the re-find."""
    return None


def receipt_problem(study, row: dict) -> tuple:
    """What is wrong with a receipt-citing row's receipt, as ``(rule, message)``, or ``None`` (and the receipt).
    Needs no network: the receipt's place, presence, shape, and that it is this row's."""
    if "receipts" not in study.spec["evidence"]:
        return ("receipts-undeclared", "the row cites a fetch receipt (its locator is not a <work slug>#p<N> locus) "
                "but evidence.receipts is not declared (section 3, line 223)"), None
    if row["url"] == "":
        return ("receipt-url", "the row cites a fetch receipt but has no url to find it by (5.4)"), None
    rp = study.paths["/evidence/receipts"]
    rid = receipt_id(row["url"], row["quote"])
    rel = f"{rp.repo_rel}/{rid}.json"
    place = os.path.join(rp.real, f"{rid}.json")
    if not os.path.lexists(place):
        return ("receipt-missing", f"no fetch receipt {rel}; the quotation cannot be re-found (5.4)"), None
    real = os.path.realpath(place)
    if not inside(real, os.path.realpath(study.repo_root)):
        return ("receipt-malformed", f"{rel} resolves outside the repository (rule 1.6)"), None
    try:
        data = read_capped(Path(real), MAX_JSON_BYTES)
    except OSError as exc:
        return ("receipt-malformed", f"{rel} cannot be read: {reason(exc)}"), None
    if data is None:
        return ("receipt-malformed", f"{rel} is larger than {MAX_JSON_BYTES} bytes"), None
    doc, errs = load_json_strict(data, rel)
    if errs or not isinstance(doc, dict):
        return ("receipt-malformed", f"{rel} is not a JSON object"), None
    extra = sorted(set(doc) - set(RECEIPT_KEYS))
    missing = [k for k in RECEIPT_REQUIRED if k not in doc]
    if extra or missing:
        return ("receipt-malformed", f"{rel} is not a 4.4 receipt (missing {q(missing)}, extra {q(extra)})"), None
    if doc["receipt_id"] != rid or doc["url"] != row["url"] or not isinstance(doc["quote"], str) or \
            fold(doc["quote"], spaces=False) != fold(row["quote"], spaces=False):
        return ("receipt-malformed", f"{rel} is not the receipt of this row's url and quote"), None
    return None, doc


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
        add("id-duplicate", f"id {q(row['id'])} is repeated")
    if row["attribute_kind"] not in kinds:
        add("attribute-kind", f"attribute_kind {q(row['attribute_kind'])} is not declared")
    if persons is not None and row["person_id"] not in persons:
        add("person-unknown", f"person_id {q(row['person_id'])} is not in the registry")
    uid = row["unit_id"]
    if not passage and uid != "":
        add("unit-id", "a unit_id in an author study")
    if passage and uid == "":
        add("unit-id", f"no unit_id in a {spec['unit']['kind']} study")
    if passage and uid != "":
        if uid in units:
            if units[uid]["person_id"] != row["person_id"]:
                add("unit-person", f"unit {q(uid)} is attributed to {q(units[uid]['person_id'])}, not to "
                    f"{q(row['person_id'])}")
        elif uid != row["person_id"]:
            add("unit-unknown", f"unit_id {q(uid)} is neither an attribution unit nor the row's person_id")
    if "|" in row["person_id"] or "|" in uid:
        add("id-separator", "a '|' in person_id or unit_id (4.7)")
    tier = row["tier"]
    if tier not in ev["tiers"]:
        add("tier-unknown", f"tier {q(tier)} is not declared")
    counted = tier in ev["counted_tiers"]
    if counted and row["quote"] == "":
        add("counted-quote", "a counted row without a quote")
    if counted and row["citation"] == "" and row["source_id"] == "":
        add("counted-citation", "a counted row with neither citation nor source_id")
    if counted and row["basis"] not in ("own", "reported"):
        add("counted-basis", f"a counted row whose basis {q(row['basis'])} is not own or reported")
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
                try:
                    hit = search(pattern, folded)
                except ValueError as exc:
                    add("vocabulary", f"column {col} was not checked: {reason(exc)} (contract silent; refused)")
                    break
                if hit:
                    add("vocabulary", f"column {col} matches forbidden pattern {q(pattern.pattern)} (line {line})")
                    break
    return out


def _read_exceptions(study) -> tuple:
    """The legacy exceptions file: ``{(id, rule): line}``, and its findings."""
    listed, findings, _digest = read_exceptions_hashed(study)
    return listed, findings


def read_exceptions_hashed(study) -> tuple:
    """The legacy exceptions file: ``({(id, rule): line}, findings, sha256 of the bytes read)``; the hash is None when
    there is no file and :data:`survey_provenance.ABSENT` (``""``) when one is declared but absent."""
    rp = study.paths.get("/evidence/legacy_exceptions")
    if rp is None:
        return {}, [], None
    if not os.path.lexists(rp.real):
        return {}, [], ""
    rows, digest = read_rows_hashed(Path(rp.real), rp.repo_rel, EXCEPTION_COLUMNS, "exceptions-columns")
    if rows.findings:
        return {}, rows.findings, digest
    listed, findings = {}, []
    for n, r in rows.rows:
        at = f"{rp.repo_rel}:{n}"
        if r["rule"] in UNLISTABLE:
            findings.append(Finding("exceptions-unlistable", at, f"rule {q(r['rule'])} cannot be listed (4.1)"))
        elif r["rule"] not in RULES:
            findings.append(Finding("exceptions-rule", at, f"{q(r['rule'])} is not a rule id of 4.1"))
        elif r["id"] == "":
            findings.append(Finding("exceptions-id", at, "an exception names no row id"))
        elif (r["id"], r["rule"]) in listed:
            findings.append(Finding("exceptions-duplicate", at, f"({q(r['id'])}, {q(r['rule'])}) is listed twice"))
        else:
            listed[(r["id"], r["rule"])] = n
    return listed, findings, digest


def check_row_files(study, merged=None, batch_from: int | None = None) -> EvidenceReport:
    """Every row file sections 4.1, 4.3 and 4.8 define that is present: the evidence file (with the registry it
    needs), the attribution file, the legacy exceptions, the vocabulary file and the bucket tables.

    For a merge (4.1, lines 322-326), *merged* is the evidence file with the batch appended, as parsed rows not yet
    written, and *batch_from* the index of its first batch row: the whole merged file is checked, and no legacy
    exception covers a row from the batch."""
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
                                       "its reader plug-in, which this version does not load, so the rows cannot be "
                                       "checked; not implemented (fails closed)"))
    elif merged is not None:
        rows = merged
        report.findings += rows.findings
        if rows.findings:
            rows = None
    elif os.path.lexists(rp.real):  # absent only in a draft (section 3's file check)
        rows = read_rows(Path(rp.real), rp.repo_rel, COLUMNS, "columns")
        report.findings += rows.findings
        if rows.findings:
            rows = None

    units = {}
    if spec["unit"]["kind"] in ("passage", "work"):
        evidence_persons = {r["person_id"] for _n, r in rows.rows} if rows is not None else set()
        att = check_attribution(study, persons, evidence_persons)
        report.findings += att.findings
        units = att.units
    report.findings += _check_overrides(study)
    if rows is None:
        return report
    report.rows = len(rows.rows)
    if persons is None:
        report.findings.append(Finding("registry-missing", study.paths["/identity/registry"].repo_rel,
                                       "the registry does not exist; a missing registry is itself an error (4.1)"))
    _check_rows(study, rows, rp.repo_rel, persons, units, vocab or [], report, batch_from)
    return report


def _check_overrides(study) -> list:
    """The overrides file (4.4, lines 491-506), when it is there. Imported here, not at the top: the identity module
    reads the evidence columns from this one."""
    from survey_identity import identity_refusals, project_persons, read_overrides

    rp = study.paths.get("/identity/overrides")
    if rp is None or not os.path.lexists(rp.real) or identity_refusals(study):
        return []
    persons = project_persons(study)
    return read_overrides(study, persons.persons).findings if not persons.findings else []


def _check_rows(study, rows, where: str, persons, units: dict, vocab: list, report: EvidenceReport,
                batch_from: int | None = None) -> None:
    """The 4.1 row checks over the whole file, the legacy exceptions, and the receipt citations. Rows from
    *batch_from* on are a batch: "a legacy exception never covers a batch row" (4.1, line 324), and the leniency a
    legacy study has for rows "that predate receipts" (5.4, lines 774-775) does not reach a row added now."""
    spec = study.spec
    kinds = declared_kinds(spec)
    listed, exc_findings = _read_exceptions(study)
    report.findings += exc_findings
    report.exceptions = len(listed)
    legacy = spec["status"] == "legacy"
    counted_tiers = spec["evidence"]["counted_tiers"]
    ids: dict = {}
    for _n, r in rows.rows:
        ids[r["id"]] = ids.get(r["id"], 0) + 1
    used = set()
    for index, (n, r) in enumerate(rows.rows):
        at = f"{where}:{n}"
        in_batch = batch_from is not None and index >= batch_from
        if in_batch:
            at = f"{where} (batch row {index - batch_from + 1})"
        nameable = r["id"] != "" and ids[r["id"]] == 1 and not in_batch
        for rule, msg in row_breaches(study, r, ids, persons, units, kinds, vocab):
            key = (r["id"], rule)
            if nameable and key in listed:
                used.add(key)
                report.excused[rule] = report.excused.get(rule, 0) + 1
                continue
            report.findings.append(Finding(rule, at, msg))
        _check_citation(study, r, at, r["tier"] in counted_tiers, legacy and not in_batch, report)
    if listed:
        exc_rel = study.paths["/evidence/legacy_exceptions"].repo_rel
        for key, line in sorted(listed.items(), key=lambda kv: kv[1]):
            if key not in used:
                report.findings.append(Finding("exceptions-stale", f"{exc_rel}:{line}", f"row {q(key[0])} does not "
                                               f"break rule {q(key[1])} (or is gone); the file must not claim more "
                                               "than is true (4.1)"))


def _check_citation(study, row: dict, at: str, counted: bool, legacy: bool, report: EvidenceReport) -> None:
    """Where a row's quotation is to be re-found (5.4). Every receipt-citing row, counted or not, needs the
    receipts declared and a usable receipt where one is there (line 771 has no tier limit); a counted row also needs
    a locator and its receipt (line 773). In a legacy study a counted row that predates receipts (no receipt, no
    url) is reported, not failed (lines 773-775)."""
    if counted and row["locator"] == "":
        finding = Finding("locator-missing", at, "a counted row without a locator: its quotation can be re-found "
                          "neither at a locus nor through a receipt (5.4)")
        if legacy:  # a row that predates receipts cannot be made re-findable (5.4, lines 774-775)
            report.reported.append(Finding(finding.rule, at, finding.message + " (reported: a legacy study, 5.4)"))
            report.not_refound += 1
        else:
            report.findings.append(finding)
        return
    if not cites_receipt(row):
        if counted and refind_quotation(study, row, None) is None:
            report.not_refound += 1
        return
    problem, receipt = receipt_problem(study, row)
    if problem is not None and problem[0] in LEGACY_REPORTABLE and not counted:
        return  # an uncounted row's quotation need not be re-found (5.4, line 773)
    if problem is None:
        if counted and refind_quotation(study, row, receipt) is None:
            report.not_refound += 1
        return
    if legacy and problem[0] in LEGACY_REPORTABLE:
        report.reported.append(Finding(problem[0], at, problem[1] + " (reported: a legacy study, 5.4)"))
        report.not_refound += 1
        return
    report.findings.append(Finding(problem[0], at, problem[1]))


def check_tables(study) -> list:
    """Every bucket table the attributes name (4.8)."""
    findings = []
    for i, a in enumerate(study.spec["attributes"]):
        rp = study.paths.get(f"/attributes/{i}/bucketer/table")
        if rp is None or not os.path.lexists(rp.real):
            continue
        allowed = a.get("flags") if a["kind"] == "flags" else a.get("levels")
        _rows, errs = check_table(Path(rp.real), rp.repo_rel, allowed)
        findings += errs
        fallback = a["bucketer"].get("fallback")
        if fallback is not None and allowed is not None and fallback not in allowed:
            findings.append(Finding("table-fallback", f"{study.spec_rel}#/attributes/{i}/bucketer/fallback",
                                    f"fallback {q(fallback)} is not one of the attribute's levels (contract silent; "
                                    "refused)"))
    return findings


def current_breaches(study) -> tuple:
    """The 4.1 breaches of the evidence file as it stands, as ``(id, rule)`` in file and rule order, for a first
    exceptions file (4.1, lines 364-365), and the findings that stop one being written: a breach of a rule that
    cannot be listed (``columns``, ``id-empty``, ``id-duplicate``), or a file that cannot be read."""
    spec = study.spec
    rp = study.paths["/evidence/file"]
    if not os.path.lexists(rp.real):
        return [], [Finding("exceptions-draft", rp.repo_rel, "there is no evidence file to read breaches from")]
    rows = read_rows(Path(rp.real), rp.repo_rel, COLUMNS, "columns")
    if rows.findings:
        return [], rows.findings
    persons, reg_findings = read_registry(study)
    vocab, vocab_findings = read_vocabulary(study)
    if persons is None:  # no check is skipped because a file is absent (4.1, lines 313-315)
        reg_findings = reg_findings + [Finding("registry-missing", study.paths["/identity/registry"].repo_rel,
                                               "the registry does not exist; a missing registry is itself an error "
                                               "(4.1, line 315), and person-unknown cannot be judged without it")]
    if reg_findings or vocab_findings:
        return [], reg_findings + vocab_findings
    units = {}
    if spec["unit"]["kind"] in ("passage", "work"):
        att = check_attribution(study, persons, {r["person_id"] for _n, r in rows.rows})
        units = att.units
    kinds = declared_kinds(spec)
    ids: dict = {}
    for _n, r in rows.rows:
        ids[r["id"]] = ids.get(r["id"], 0) + 1
    breaches, stops = [], []
    for n, r in rows.rows:
        bad = [ch for ch in r["id"] if unicodedata.category(ch)[0] == "C" or unicodedata.category(ch) in ("Zl", "Zp")]
        if bad:
            stops.append(Finding("exceptions-draft", f"{rp.repo_rel}:{n}", f"id {q(r['id'])} holds a control, format "
                                 "or line-separator character; a printed draft could not name it exactly"))
            continue
        for rule, msg in row_breaches(study, r, ids, persons, units, kinds, vocab or []):
            if rule in UNLISTABLE:
                stops.append(Finding(rule, f"{rp.repo_rel}:{n}", f"{msg}; a breach of {rule} cannot be listed (4.1, "
                                     "lines 357-358), so no exceptions file can name this row"))
            else:
                breaches.append((r["id"], rule))
    return breaches, stops
