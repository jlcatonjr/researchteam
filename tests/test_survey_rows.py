"""Step B: the row files. Evidence (4.1) with its rule ids and legacy exceptions, attribution (4.3), the receipt
citation (5.4), the forbidden vocabulary (5.3), bucket tables and years (4.8), and survey-validate's row-file part."""
import csv
import io
import json
import os

import re

import pytest

from survey_support import STUDY_REL, edit_spec, make_repo, run, survey_validate, tree
from survey_support import survey_attribution as att_mod
from survey_support import survey_evidence as ev
from survey_support import survey_spec as sp
from survey_support import survey_tables as tb

ROWS = f"{STUDY_REL}/rows"


def _csv(header, rows) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    for r in rows:
        w.writerow([r.get(c, "") for c in header] if isinstance(r, dict) else r)
    return buf.getvalue()


def _read(root, name):
    text = (root / ROWS / name).read_text(encoding="utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return reader.fieldnames, list(reader)


def _write(root, name, header, rows):
    (root / ROWS / name).write_text(_csv(header, rows), encoding="utf-8")


def _evidence(root, mutate=None, add=()):
    header, rows = _read(root, "evidence.csv")
    if mutate:
        mutate(rows)
    rows += [dict({c: "" for c in header}, **r) for r in add]
    _write(root, "evidence.csv", header, rows)


def _attribution(root, mutate=None, add=()):
    header, rows = _read(root, "attribution.csv")
    if mutate:
        mutate(rows)
    rows += [dict({c: "" for c in header}, **r) for r in add]
    _write(root, "attribution.csv", header, rows)


def _report(root):
    return ev.check_row_files(sp.load_study("tidebell", root))


def _rules(root):
    return {f.rule for f in _report(root).findings}


GOOD = {"id": "ev-100", "person_id": "warden-01", "attribute_kind": "harbour", "value": "South Steps",
        "tier": "quoted", "source_id": "src-9", "citation": "Invented letter", "locator": "letter-09#p1",
        "quote": "from the south steps", "basis": "own", "unit_id": "p-001"}


def test_the_invented_study_passes_every_row_check(tmp_path):
    root = make_repo(tmp_path)
    report = _report(root)
    assert report.findings == [] and report.rows == 5 and report.exceptions == 0
    code, out, _ = run(survey_validate, "--root", str(root), "tidebell")
    assert code == 0 and "evidence: 5 row(s); read with 0 legacy exception(s)" in out
    assert "not re-found: re-finding is not in this version" in out


def test_the_good_row_passes(tmp_path):
    root = make_repo(tmp_path)
    _evidence(root, add=[GOOD])
    assert _report(root).findings == []


# --------------------------------------------------------------------------- every rule id of 4.1
def _with(**cells):
    return dict(GOOD, **cells)


RULE_CASES = {
    "id-empty": dict(add=[_with(id="")]),
    "id-duplicate": dict(add=[_with(id="ev-001")]),
    "attribute-kind": dict(add=[_with(attribute_kind="shoe_size")]),
    "person-unknown": dict(add=[_with(person_id="warden-99", unit_id="warden-99")]),
    "unit-id": dict(add=[_with(unit_id="")]),
    "unit-unknown": dict(add=[_with(unit_id="p-404")]),
    "unit-person": dict(add=[_with(unit_id="p-002")]),
    "id-separator": dict(add=[_with(unit_id="p|001")]),
    "tier-unknown": dict(add=[_with(tier="rumoured")]),
    "counted-quote": dict(add=[_with(quote="")]),
    "counted-citation": dict(add=[_with(citation="", source_id="")]),
    "counted-basis": dict(add=[_with(basis="")]),
    "reported-reporter": dict(add=[_with(basis="reported")]),
    "own-reporter": dict(add=[_with(reporter="a harbour clerk")]),
    "ne-quote": dict(add=[_with(tier="not-established", note="tried", quote="a quote")]),
    "ne-note": dict(add=[_with(tier="not-established", quote="", basis="")]),
    "vocabulary": dict(add=[_with(value="Obviously the south steps")]),
}


def test_every_rule_id_but_columns_has_a_case():
    assert set(RULE_CASES) | {"columns"} == set(ev.RULES)


@pytest.mark.parametrize("rule", sorted(RULE_CASES))
def test_each_rule_id_is_triggered(tmp_path, rule):
    root = make_repo(tmp_path)
    _evidence(root, **RULE_CASES[rule])
    assert rule in _rules(root)
    code, out, _ = run(survey_validate, "--root", str(root), "tidebell")
    assert code == 1 and f"ERROR [{rule}]" in out


def test_columns_rule(tmp_path):
    root = make_repo(tmp_path)
    header, rows = _read(root, "evidence.csv")
    _write(root, "evidence.csv", [c for c in header if c != "note"], rows)
    assert _rules(root) == {"columns"}


def test_a_unit_id_in_an_author_study_is_an_error(tmp_path):
    def author(s):
        s["unit"] = {"kind": "author"}
        s["outcomes"][0]["source"] = {"kind": "evidence-attribute", "attribute": "duty"}
        s["frame_rules"]["exclude"] = []
    root = make_repo(tmp_path, author)
    rules = [f for f in _report(root).findings if f.rule == "unit-id"]
    assert len(rules) == 5  # every fixture row carries a unit_id


def test_a_person_level_row_carries_its_own_person_id(tmp_path):
    root = make_repo(tmp_path)  # ev-002 and ev-004 are person-level rows
    _evidence(root, add=[_with(unit_id="warden-01", attribute_kind="life_dates", value="1701-1768")])
    assert _report(root).findings == []


def test_reported_and_own_rules_hold_outside_counted_tiers_too(tmp_path):
    root = make_repo(tmp_path)
    _evidence(root, add=[_with(id="ev-200", tier="not-established", quote="", note="tried", basis="reported")])
    assert _rules(root) == {"reported-reporter"}


def test_the_vocabulary_spares_quotes_unless_told_otherwise(tmp_path):
    root = make_repo(tmp_path)
    _evidence(root, add=[_with(quote="obviously from the south steps")])
    assert _rules(root) == set()
    edit_spec(root, lambda s: s["vocabulary"].update(exempt_columns=[]))
    assert _rules(root) == {"vocabulary"}


def test_vocabulary_is_matched_on_folded_text(tmp_path):
    root = make_repo(tmp_path)
    _evidence(root, add=[_with(note="OBVIOU­SLY")])  # a soft hyphen and capitals fold away
    assert _rules(root) == {"vocabulary"}


def test_a_forbidden_pattern_that_does_not_compile(tmp_path):
    root = make_repo(tmp_path)
    (root / STUDY_REL / "rules" / "forbidden.txt").write_text("# comment\n(unclosed\n", encoding="utf-8")
    assert "vocabulary-file" in _rules(root)


def test_a_missing_registry_is_itself_an_error(tmp_path):
    root = make_repo(tmp_path)
    (root / ROWS / "registry.csv").unlink()
    assert "registry-missing" in _rules(root)


def test_a_draft_without_evidence_needs_no_registry(tmp_path):
    root = make_repo(tmp_path, lambda s: s.update(status="draft"))
    (root / ROWS / "registry.csv").unlink()
    (root / ROWS / "evidence.csv").unlink()
    assert _report(root).findings == []


def test_registry_shape(tmp_path):
    root = make_repo(tmp_path)
    (root / ROWS / "registry.csv").write_text("person_id,name\nwarden-01,x\n", encoding="utf-8")
    assert "registry-columns" in _rules(root)
    _write(root, "registry.csv", ev.REGISTRY_COLUMNS, [["warden-01", "", "", ""], ["warden-01", "", "", ""]])
    assert "registry-person" in _rules(root)


def test_plugin_format_evidence_is_not_checked_and_says_so(tmp_path):
    root = make_repo(tmp_path, lambda s: s["evidence"].update(
        format="plugin", reader={"file": "rules/forbidden.txt", "attr": "R", "version": "1"}))
    assert "evidence-plugin" in _rules(root)


# --------------------------------------------------------------------------- legacy exceptions (4.1)
def _legacy(tmp_path, lines, add=()):
    def mutate(s):
        s["status"] = "legacy"
        s["evidence"]["legacy_exceptions"] = "rules/exceptions.csv"
        s["signoffs"]["gates"]["S0"]["covers"].append("rules/exceptions.csv")
    root = make_repo(tmp_path, mutate)
    (root / STUDY_REL / "rules" / "exceptions.csv").write_text(_csv(["id", "rule"], lines), encoding="utf-8")
    _evidence(root, add=add)
    return root


def test_a_listed_breach_is_excused_and_counted(tmp_path):
    root = _legacy(tmp_path, [["ev-100", "counted-basis"]], add=[_with(basis="")])
    report = _report(root)
    assert report.findings == [] and report.excused == {"counted-basis": 1} and report.exceptions == 1
    code, out, _ = run(survey_validate, "--root", str(root), "tidebell")
    assert code == 0 and "read with 1 legacy exception(s); breaches excused by rule: counted-basis 1" in out


def test_a_listed_row_that_breaks_a_further_rule_fails_on_it(tmp_path):
    root = _legacy(tmp_path, [["ev-100", "counted-basis"]], add=[_with(basis="", quote="")])
    assert _rules(root) == {"counted-quote"}


@pytest.mark.parametrize("lines,rule", [
    ([["ev-001", "counted-quote"]], "exceptions-stale"),        # the row passes
    ([["ev-gone", "counted-quote"]], "exceptions-stale"),       # the row was removed
    ([["ev-100", "columns"]], "exceptions-unlistable"),
    ([["ev-100", "id-duplicate"]], "exceptions-unlistable"),
    ([["ev-100", "made-up"]], "exceptions-rule"),
    ([["", "counted-quote"]], "exceptions-id"),
    ([["ev-100", "counted-basis"], ["ev-100", "counted-basis"]], "exceptions-duplicate"),
])
def test_exception_file_errors(tmp_path, lines, rule):
    root = _legacy(tmp_path, lines, add=[_with(basis="")])
    assert rule in _rules(root)


def test_the_exceptions_file_has_exactly_two_columns(tmp_path):
    root = _legacy(tmp_path, [])
    (root / STUDY_REL / "rules" / "exceptions.csv").write_text("id,rule,why\n", encoding="utf-8")
    assert "exceptions-columns" in _rules(root)


def test_a_duplicated_id_cannot_be_excused(tmp_path):
    root = _legacy(tmp_path, [["ev-001", "counted-basis"]], add=[_with(id="ev-001", basis="")])
    rules = _rules(root)
    assert {"id-duplicate", "counted-basis", "exceptions-stale"} <= rules


def test_exceptions_are_allowed_only_in_a_legacy_study(tmp_path):
    root = _legacy(tmp_path, [])
    edit_spec(root, lambda s: s.update(status="active"))
    assert "legacy-exceptions-status" in {f.rule for f in sp.load_study("tidebell", root).findings}


# --------------------------------------------------------------------------- receipt citations (5.4, section 3)
URL_ROW = _with(id="ev-300", locator="https://archive.invalid/letter-9", url="https://archive.invalid/letter-9",
                quote="from the south steps")


def _receipt(root, row, **over):
    rid = ev.receipt_id(row["url"], row["quote"])
    doc = {"url": row["url"], "quote": row["quote"], "fetched_at": "2026-01-01T00:00:00Z",
           "quote_fold_sha256": "x", "status": 200, "found": True, "receipt_id": rid}
    doc.update(over)
    folder = root / ROWS / "receipts"
    folder.mkdir(exist_ok=True)
    (folder / f"{rid}.json").write_text(json.dumps(doc), encoding="utf-8")
    return rid


def test_the_receipt_id_follows_4_4():
    import hashlib
    expected = hashlib.sha256(b"https://a.invalid/x\nfromthesouthsteps").hexdigest()[:24]
    assert ev.receipt_id("https://a.invalid/x", "From the  south\nsteps") == expected


def test_a_locus_locator_cites_no_receipt():
    assert not ev.cites_receipt({"locator": "logbook-01#p3"})
    assert ev.cites_receipt({"locator": "logbook-01, page 3"})
    assert ev.cites_receipt({"locator": "Logbook-01#p3"})  # a slug is lower-case


def test_a_cited_receipt_that_is_present_passes(tmp_path):
    root = make_repo(tmp_path)
    _evidence(root, add=[URL_ROW])
    _receipt(root, URL_ROW)
    report = _report(root)
    assert report.findings == [] and report.not_refound == 5  # four fixture rows and this one


@pytest.mark.parametrize("case,rule", [
    ("undeclared", "receipts-undeclared"), ("no-url", "receipt-url"), ("absent", "receipt-missing"),
    ("other-url", "receipt-malformed"), ("not-json", "receipt-malformed"), ("extra-key", "receipt-malformed"),
])
def test_receipt_citation_errors(tmp_path, case, rule):
    root = make_repo(tmp_path, (lambda s: s["evidence"].pop("receipts")) if case == "undeclared" else None)
    row = dict(URL_ROW, url="") if case == "no-url" else URL_ROW
    _evidence(root, add=[row])
    if case in ("other-url", "extra-key", "not-json"):
        rid = _receipt(root, URL_ROW, **({"url": "https://elsewhere.invalid"} if case == "other-url" else
                                         {"colour": "red"} if case == "extra-key" else {}))
        if case == "not-json":
            (root / ROWS / "receipts" / f"{rid}.json").write_text("{", encoding="utf-8")
    assert rule in _rules(root)


def test_a_legacy_study_reports_an_unfindable_quotation(tmp_path):
    root = _legacy(tmp_path, [], add=[URL_ROW])
    report = _report(root)
    assert report.findings == [] and [f.rule for f in report.reported] == ["receipt-missing"]
    code, out, _ = run(survey_validate, "--root", str(root), "tidebell")
    assert code == 0 and "REPORTED [receipt-missing]" in out


def test_the_refind_seam_never_counts_a_quotation_as_found():
    assert ev.refind_quotation(None, {}, None) is None


# --------------------------------------------------------------------------- attribution (4.3)
ATT_CASES = {
    "attribution-unit-empty": dict(add=[{"unit_id": "", "person_id": "warden-01", "author_kind": "person",
                                         "status": "firm", "genre": "letter"}]),
    "attribution-unit-duplicate": dict(add=[{"unit_id": "p-001", "person_id": "warden-01", "author_kind": "person",
                                             "status": "firm", "genre": "letter"}]),
    "attribution-unit-is-person": dict(add=[{"unit_id": "warden-02", "person_id": "warden-01",
                                             "author_kind": "person", "status": "firm", "genre": "letter"}]),
    "attribution-person-empty": dict(add=[{"unit_id": "p-009", "person_id": "", "author_kind": "person",
                                           "status": "firm", "genre": "letter"}]),
    "attribution-separator": dict(add=[{"unit_id": "p|009", "person_id": "warden-01", "author_kind": "person",
                                        "status": "firm", "genre": "letter"}]),
    "attribution-status": dict(add=[{"unit_id": "p-009", "person_id": "warden-01", "author_kind": "person",
                                     "status": "rumoured", "genre": "letter"}]),
    "attribution-author-kind": dict(add=[{"unit_id": "p-009", "person_id": "warden-03", "author_kind": "ship",
                                          "status": "firm", "genre": "letter"}]),
    "attribution-passage-attribute": dict(add=[{"unit_id": "p-009", "person_id": "warden-01",
                                                "author_kind": "person", "status": "firm", "genre": ""}]),
    "attribution-author-kinds": dict(add=[{"unit_id": "p-009", "person_id": "warden-01", "author_kind": "guild",
                                           "status": "firm", "genre": "letter"}]),
}


@pytest.mark.parametrize("rule", sorted(ATT_CASES))
def test_each_attribution_check_is_triggered(tmp_path, rule):
    root = make_repo(tmp_path)
    _attribution(root, **ATT_CASES[rule])
    assert rule in _rules(root)


def test_attribution_columns_follow_the_passage_attributes(tmp_path):
    root = make_repo(tmp_path)
    assert att_mod.columns(sp.load_study("tidebell", root).spec) == (
        "unit_id", "person_id", "author_kind", "work", "locator", "status", "genre", "basis", "note")
    header, rows = _read(root, "attribution.csv")
    _write(root, "attribution.csv", [c for c in header if c != "genre"], rows)
    assert "attribution-columns" in _rules(root)


def test_without_a_registry_the_registrys_sources_stand_in(tmp_path):
    root = make_repo(tmp_path, lambda s: s.update(status="draft"))
    (root / ROWS / "registry.csv").unlink()
    (root / ROWS / "evidence.csv").unlink()
    _attribution(root, add=[{"unit_id": "warden-02", "person_id": "warden-01", "author_kind": "person",
                             "status": "firm", "genre": "letter"}])
    assert "attribution-unit-is-person" in _rules(root)


# --------------------------------------------------------------------------- row files (section 4)
def test_a_row_of_the_wrong_width_and_a_blank_line_are_errors(tmp_path):
    root = make_repo(tmp_path)
    path = root / ROWS / "evidence.csv"
    text = path.read_text(encoding="utf-8")
    path.write_text(text + "\nev-9,warden-01\n", encoding="utf-8")
    found = [f for f in _report(root).findings if f.rule == "columns"]
    assert len(found) == 2


@pytest.mark.parametrize("data", [b"", b"\xef\xbb\xbfid,person_id\n", b"\xff\xfe"])
def test_an_unreadable_or_headless_row_file(tmp_path, data):
    root = make_repo(tmp_path)
    (root / ROWS / "evidence.csv").write_bytes(data)
    assert "columns" in _rules(root)


def test_a_row_file_reached_through_a_final_link_is_not_read(tmp_path):
    root = make_repo(tmp_path)
    os.replace(root / ROWS / "evidence.csv", root / ROWS / "real.csv")
    os.symlink("real.csv", root / ROWS / "evidence.csv")
    assert "columns" in _rules(root)


def test_validate_writes_nothing_and_is_deterministic(tmp_path):
    root = make_repo(tmp_path)
    _evidence(root, add=[_with(id="")])
    before = tree(root)
    first = run(survey_validate, "--root", str(root), "tidebell")
    assert first == run(survey_validate, "--root", str(root), "tidebell") and first[0] == 1
    assert tree(root) == before


# --------------------------------------------------------------------------- bucket tables (4.8)
def _table(root, name, rows, header=tb.TABLE_COLUMNS):
    (root / STUDY_REL / "tables" / name).write_text(_csv(header, rows), encoding="utf-8")


@pytest.mark.parametrize("rows,header,rule", [
    ([["harbour", "x", "", "north", "n"]], ("field", "pattern", "bucket", "note"), "table-columns"),
    ([], tb.TABLE_COLUMNS, "table-empty"),
    ([["harbour", "", "", "north", "n"]], tb.TABLE_COLUMNS, "table-row"),
    ([["harbour", "x", "", "north", ""]], tb.TABLE_COLUMNS, "table-row"),
    ([["harbour", "x", "", "", "n"]], tb.TABLE_COLUMNS, "table-row"),
    ([["harbour", "(x", "", "north", "n"]], tb.TABLE_COLUMNS, "table-pattern"),
    ([["harbour", "x", "[", "north", "n"]], tb.TABLE_COLUMNS, "table-pattern"),
    ([["harbour", "x", "", "east", "n"]], tb.TABLE_COLUMNS, "table-bucket"),
])
def test_bucket_table_errors(tmp_path, rows, header, rule):
    root = make_repo(tmp_path)
    _table(root, "harbour.csv", rows, header)
    assert rule in _rules(root)


def test_a_fallback_outside_the_levels_is_refused(tmp_path):
    root = make_repo(tmp_path, lambda s: s["attributes"][0]["bucketer"].update(fallback="east"))
    assert "table-fallback" in _rules(root)


def _rows(lines):
    return [tb.TableRow(i, f, re.compile(p), re.compile(u) if u else None, b)
            for i, (f, p, u, b) in enumerate(lines)]


def test_match_first_takes_the_first_row_that_fires():
    rows = _rows([("harbour", "quay", "", "north"), ("*", "steps", "", "south"), ("harbour", "", "", "other")])
    assert tb.bucket_first(rows, [("harbour", "The South Steps"), ("harbour", "North Quay")], None, "NE") == "north"
    assert tb.bucket_first(rows[:2], [("duty", "the steps")], None, "NE") == "south"  # '*' looks at any kind
    assert tb.bucket_first(rows[:1], [("duty", "quay")], None, "NE") == "NE"  # the field must match
    assert tb.bucket_first(rows[:1], [("harbour", "inland")], "other", "NE") == "other"
    assert tb.bucket_first(rows[:1], [("harbour", "")], None, "NE") == "NE"  # an empty cell is not given


def test_unless_stops_a_row_firing():
    rows = _rows([("*", "quay", "old", "north"), ("*", "quay", "", "south")])
    assert tb.bucket_first(rows, [("harbour", "Old Quay")], None, "NE") == "south"


def test_match_all_collects_every_bucket():
    rows = _rows([("duty", "lamp", "", "lamp"), ("duty", "bell", "", "bell"), ("duty", "fog", "", "fog")])
    assert tb.bucket_all(rows, [("duty", "Lamp and Bell")]) == {"lamp", "bell"}
    assert tb.bucket_all(rows, [("duty", "nothing")]) == set()


def test_patterns_search_the_folded_value():
    rows = _rows([("*", "cafe quay", "", "north")])
    assert tb.bucket_first(rows, [("harbour", "  CAFÉ\n QUAY ")], None, "NE") == "north"


# --------------------------------------------------------------------------- years and periods (4.8)
@pytest.mark.parametrize("value,basis,year", [
    ("1742", "work_date", 1742), ("written 1742, copied 1790", "work_date", 1742),
    ("written 1742, copied 1790", "life_dates", 1790), ("1701-1768", "life_dates", 1768),
    ("1701-1768", "work_date", 1701), ("about 850", "work_date", 850),
    ("12345", "work_date", None), ("in 42", "work_date", None), ("-350", "work_date", None),
    ("c. -350 to -120", "life_dates", None), ("c. -350 to 120", "life_dates", 120), ("4th c.", "work_date", 350), ("1st c.", "life_dates", 50),
    ("4th c. and 12th c.", "life_dates", 1150), ("4th c. and 12th c.", "work_date", 350),
    ("in 1750 (4th c.)", "work_date", 1750), ("no date", "life_dates", None), ("", "work_date", None),
])
def test_a_year_from_one_value(value, basis, year):
    assert tb.year_of(value, basis) == year


def test_life_dates_take_the_largest_year_among_values():
    assert tb.life_year(["1701-1768", "d. 1770", "no year"]) == 1770
    assert tb.life_year(["no year"]) is None


def test_an_unknown_basis_is_refused():
    with pytest.raises(ValueError):
        tb.year_of("1742", "birth")


@pytest.mark.parametrize("year,period", [(1700, 1), (1749, 1), (1750, 2), (1799, 2), (1800, 3), (2000, 3)])
def test_a_year_equal_to_a_cut_begins_the_later_period(year, period):
    assert tb.period_of(year, [1750, 1800]) == period
