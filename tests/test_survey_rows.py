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
    assert "quotations: 4 counted quotation(s) not re-found (0 reported); re-finding is not in this version" in out


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
    _evidence(root, add=[_with(note="OBVIOU\u00adSLY")])  # a soft hyphen and capitals fold away
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
           "quote_fold_sha256": "x", "status": 200, "final_url": row["url"], "content_type": "text/html",
           "found": True, "reason": "", "receipt_id": rid}
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


def test_a_row_file_reached_through_a_link_inside_the_repository_is_read(tmp_path):
    """Rule 1.6, as step A treats a covered file: a link that resolves inside the repository is followed, and the
    file is opened at its resolved place."""
    root = make_repo(tmp_path)
    os.replace(root / ROWS / "evidence.csv", root / ROWS / "real.csv")
    os.symlink("real.csv", root / ROWS / "evidence.csv")
    assert _report(root).findings == [] and _report(root).rows == 5


def test_a_row_file_linked_outside_the_repository_is_refused(tmp_path):
    root = make_repo(tmp_path)
    (tmp_path / "outside.csv").write_bytes((root / ROWS / "evidence.csv").read_bytes())
    (root / ROWS / "evidence.csv").unlink()
    os.symlink(tmp_path / "outside.csv", root / ROWS / "evidence.csv")
    assert "path-outside" in {f.rule for f in sp.load_study("tidebell", root).findings}


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
    assert tb.bucket_first(rows, [("harbour", "  CAF\u00c9\n QUAY ")], None, "NE") == "north"


# --------------------------------------------------------------------------- years and periods (4.8)
@pytest.mark.parametrize("value,basis,year", [
    ("1742", "work_date", 1742), ("written 1742, copied 1790", "work_date", 1742),
    ("written 1742, copied 1790", "life_dates", 1790), ("1701-1768", "life_dates", 1768),
    ("1701-1768", "work_date", 1701), ("about 850", "work_date", 850),
    ("12345", "work_date", None), ("in 42", "work_date", None), ("-350", "work_date", None),
    ("c. -350 to -120", "life_dates", None), ("c. -350 to 120", "life_dates", 120),
    ("4th c.", "work_date", 350), ("1st c.", "life_dates", 50),
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


# --------------------------------------------------------------------------- review fixes (step B part 1)
def test_a_forged_header_cannot_add_an_output_line(tmp_path):
    """S1: a header cell holding a line feed or ESC is quoted, and the output line escapes every control
    character."""
    root = make_repo(tmp_path)
    (root / ROWS / "evidence.csv").write_text('"id\nOK: forged","\x1b[2Jx"\n', encoding="utf-8")
    code, out, _ = run(survey_validate, "--root", str(root), "tidebell")
    assert code == 1
    assert "\nOK: forged" not in out and "\x1b" not in out
    assert all(not line.startswith("OK") for line in out.splitlines())


def test_control_characters_from_any_file_value_are_escaped(tmp_path):
    root = make_repo(tmp_path)
    _evidence(root, add=[_with(attribute_kind="shoe\x1b[31m\nsize\u2028x", tier="t\u202e")])
    code, out, _ = run(survey_validate, "--root", str(root), "tidebell")
    assert code == 1
    for bad in ("\x1b", "\u2028", "\u202e", "shoe\nsize"):
        assert bad not in out
    assert "\\x1b" in out and "\\u202e" in out


def test_a_control_character_in_a_declared_path_is_escaped(tmp_path):
    """S6: a path declared in study.json reaches the output escaped."""
    from survey_support import survey_status
    root = make_repo(tmp_path, lambda s: s["evidence"].update(file="rows/evi\x1bdence.csv"))
    code, out, _ = run(survey_validate, "--root", str(root), "tidebell")
    assert code == 1 and "\x1b" not in out and "evi\\x1bdence" in out
    root2 = make_repo(tmp_path / "b", lambda s: s["signoffs"].update(ledger="agentteams-clearance:led\nger"))
    out2 = run(survey_status, "--root", str(root2), "tidebell")[1]
    assert "led\nger" not in out2


@pytest.mark.parametrize("text", ["a{1,4294967296}", "(" * 2000 + ")" * 2000, "x" * 1001],
                         ids=["huge-repeat", "deep-nesting", "over-long"])
def test_a_pattern_that_cannot_be_compiled_is_a_finding_whatever_it_raises(tmp_path, text):
    """S2, S3: a huge repeat count, nesting deeper than the engine allows, an over-long pattern."""
    root = make_repo(tmp_path)
    (root / STUDY_REL / "rules" / "forbidden.txt").write_text(text + "\n", encoding="utf-8")
    assert "vocabulary-file" in _rules(root)
    _table(root, "harbour.csv", [["harbour", text, "", "north", "n"]])
    assert "table-pattern" in _rules(root)


@pytest.mark.parametrize("exc", [OverflowError, RecursionError, ValueError])
def test_every_compile_failure_is_caught(monkeypatch, exc):
    def boom(*_a, **_k):
        raise exc("raised for the test")
    monkeypatch.setattr(tb.re, "compile", boom)
    pattern, why = tb.compile_pattern("x")
    assert pattern is None and exc.__name__ in why


def test_too_many_patterns_and_too_long_text(tmp_path, monkeypatch):
    root = make_repo(tmp_path)
    monkeypatch.setattr(ev, "MAX_PATTERNS", 1)
    (root / STUDY_REL / "rules" / "forbidden.txt").write_text("a\nb\n", encoding="utf-8")
    assert "vocabulary-file" in _rules(root)
    monkeypatch.setattr(tb, "MAX_MATCH_CHARS", 10)
    (root / STUDY_REL / "rules" / "forbidden.txt").write_text("zzz\n", encoding="utf-8")
    found = [f for f in _report(root).findings if f.rule == "vocabulary"]
    assert found and "not checked" in found[0].message
    with pytest.raises(ValueError):
        tb.bucket_first(_rows([("*", "x", "", "a")]), [("k", "y" * 11)], None, "NE")


def test_an_upper_case_table_pattern_is_refused(tmp_path):
    """T13: values are folded to lower case first, so an upper-case pattern could never match."""
    root = make_repo(tmp_path)
    _table(root, "harbour.csv", [["harbour", "North", "", "north", "n"]])
    assert "table-pattern" in _rules(root)
    _table(root, "harbour.csv", [["harbour", r"\Snorth\W", "", "north", "n"]])  # escapes are not letters
    assert "table-pattern" not in _rules(root)


def test_a_nul_in_a_cell_is_a_finding(tmp_path):
    root = make_repo(tmp_path)
    # The csv writer of Python 3.10 cannot write a NUL, so the cell is written with a marker and the NUL is put
    # into the file's bytes afterwards.
    _evidence(root, add=[_with(note="aNULMARKERb")])
    path = root / ROWS / "evidence.csv"
    data = path.read_bytes()
    assert data.count(b"NULMARKER") == 1
    path.write_bytes(data.replace(b"NULMARKER", b"\x00"))
    assert "cell-nul" in _rules(root)


def test_line_numbers_follow_quoted_multi_line_cells(tmp_path):
    """S4: a row's line is the line it starts on."""
    root = make_repo(tmp_path)
    _evidence(root, add=[_with(id="ev-500", note="two\nlines"), _with(id="")])
    found = [f for f in _report(root).findings if f.rule == "id-empty"]
    assert [f.where for f in found] == [f"{ROWS}/evidence.csv:9"]


def test_a_row_file_over_the_cap_is_not_read(tmp_path, monkeypatch):
    root = make_repo(tmp_path)
    monkeypatch.setattr(tb, "MAX_CSV_BYTES", 100)
    found = [f for f in _report(root).findings if f.rule == "columns"]
    assert found and "larger than 100 bytes" in found[0].message


def test_the_row_file_cap_is_64_mib():
    assert tb.MAX_CSV_BYTES == 64 * 1024 * 1024


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="os.mkfifo is not available here")
def test_a_row_file_that_is_a_fifo_is_not_opened(tmp_path):
    root = make_repo(tmp_path, lambda s: s.update(status="draft"))
    (root / ROWS / "evidence.csv").unlink()
    os.mkfifo(root / ROWS / "evidence.csv")  # a blocking open would hang the test
    assert "columns" in _rules(root)


def test_a_draft_may_lack_the_attribution_and_vocabulary_files(tmp_path):
    """T1: a missing input file is an error "unless status is draft" (section 3, line 217)."""
    root = make_repo(tmp_path, lambda s: s.update(status="draft"))
    (root / ROWS / "attribution.csv").unlink()
    assert {f.rule for f in _report(root).findings} <= {"unit-unknown"}  # the units it named are gone
    root2 = make_repo(tmp_path / "b", lambda s: s.update(status="draft"))
    (root2 / STUDY_REL / "rules" / "forbidden.txt").unlink()
    assert _report(root2).findings == []


@pytest.mark.parametrize("key", ev.RECEIPT_REQUIRED)
def test_a_receipt_missing_a_required_key_is_malformed(tmp_path, key):
    """T2: of a receipt's thirteen keys only sha256, context and wayback may be absent (4.4, lines 480-486)."""
    root = make_repo(tmp_path)
    _evidence(root, add=[URL_ROW])
    rid = _receipt(root, URL_ROW)
    path = root / ROWS / "receipts" / f"{rid}.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    del doc[key]
    path.write_text(json.dumps(doc), encoding="utf-8")
    assert "receipt-malformed" in _rules(root)


def test_ten_receipt_keys_are_required():
    assert len(ev.RECEIPT_REQUIRED) == 10 and set(ev.RECEIPT_OPTIONAL) == {"sha256", "context", "wayback"}


def test_an_uncounted_row_that_cites_a_receipt_needs_the_receipts_declared(tmp_path):
    """T8: line 223 and line 771 have no tier limit."""
    root = make_repo(tmp_path, lambda s: s["evidence"].pop("receipts"))
    _evidence(root, add=[dict(URL_ROW, tier="not-established", quote="", note="tried", basis="")])
    assert "receipts-undeclared" in _rules(root)


def test_an_uncounted_row_with_a_broken_receipt_fails_but_one_without_needs_none(tmp_path):
    root = make_repo(tmp_path)
    uncounted = dict(URL_ROW, tier="not-established", quote="", note="tried", basis="")
    _evidence(root, add=[uncounted])
    assert _rules(root) == set()  # its quotation need not be re-found (5.4, line 773)
    rid = ev.receipt_id(uncounted["url"], uncounted["quote"])
    (root / ROWS / "receipts").mkdir()
    (root / ROWS / "receipts" / f"{rid}.json").write_text("{", encoding="utf-8")
    assert "receipt-malformed" in _rules(root)


def test_a_broken_receipt_is_an_error_in_a_legacy_study_too(tmp_path):
    """T9: a receipt that is there and broken is not a row "that predates receipts" (5.4, line 775)."""
    root = _legacy(tmp_path, [], add=[URL_ROW])
    _receipt(root, URL_ROW, url="https://elsewhere.invalid")
    assert "receipt-malformed" in _rules(root)


def test_excused_counts_and_unfindable_totals_print_on_a_failing_run(tmp_path):
    """T10."""
    root = _legacy(tmp_path, [["ev-100", "counted-basis"]], add=[_with(basis=""), _with(id="ev-101", tier="x"),
                                                               dict(URL_ROW, id="ev-102")])
    code, out, _ = run(survey_validate, "--root", str(root), "tidebell")
    assert code == 1
    assert "breaches excused by rule: counted-basis 1" in out
    assert "quotations: 6 counted quotation(s) not re-found (1 reported)" in out


def test_a_pipe_in_a_person_id_is_an_error(tmp_path):
    root = make_repo(tmp_path)
    _evidence(root, add=[_with(person_id="warden|01", unit_id="warden|01")])
    assert "id-separator" in _rules(root)


def test_a_counted_row_without_a_locator_is_refused(tmp_path):
    root = make_repo(tmp_path)
    _evidence(root, add=[_with(locator="")])
    assert "locator-missing" in _rules(root)
    legacy = _legacy(tmp_path / "legacy", [], add=[_with(locator="")])
    report = _report(legacy)
    assert report.findings == [] and [f.rule for f in report.reported] == ["locator-missing"]


@pytest.mark.parametrize("value,year", [
    ("AD 1200", 1200), ("1200 CE", 1200), ("c. 1750", 1750), ("ca. 1750", 1750),
    ("Epistulae ad Familiares, 1742", 1742), ("ce livre, 1750", 1750),  # "ad" and "ce" are ordinary words here
    ("5th centre, 1750", 1750),  # "centre" is not a century word; the run rule reads 1750
    ("the cedar log, 1742", 1742),
])
def test_values_read_by_the_run_rule(value, year):
    """4.8, line 699: the first run of three or four digits, whatever words stand around it."""
    assert tb.year_of(value, "work_date") == year


@pytest.mark.parametrize("value,year", [
    ("4th c.", 350), ("4th c", 350), ("4th C.", 350), ("4th century", 350), ("4TH CENTURY", 350),
    ("12th cent.", 1150), ("12th cent", 1150), ("1st c.", 50), ("2nd c.", 150), ("3rd century", 250),
    ("4th-5th centuries", 450), ("21st c.", 2050),
])
def test_a_stated_century_gives_its_middle_year(value, year):
    """4.8, lines 700-701: "4th c." is the text's example of a stated century, not its only spelling."""
    assert tb.year_of(value, "work_date") == year


@pytest.mark.parametrize("value", ["5th centre", "4th cell", "4th", "the 4th chapter", "4th cc."])
def test_an_ordinary_word_after_an_ordinal_is_not_a_century(value):
    assert tb.year_of(value, "work_date") is None


@pytest.mark.parametrize("value", ["350 BC", "350 bc", "350 B.C.", "350 BCE", "350 B.C.E.", "4th c. BC"])
def test_a_year_marked_bc_is_negative_and_not_read(value):
    """4.8, line 701: negative years are not read; BC/BCE after a number marks it negative (proposal 14)."""
    assert tb.year_of(value, "work_date") is None and tb.year_of(value, "life_dates") is None


def test_a_bc_run_does_not_hide_another_run():
    assert tb.year_of("350 BC and 1200", "work_date") == 1200


def test_a_run_of_digits_comes_before_a_stated_century():
    """4.8, line 700: a century is read only "where a value has no such run"."""
    assert tb.year_of("in 1750 (4th c.)", "work_date") == 1750
    assert tb.year_of("4th c., copied 1750", "life_dates") == 1750
    assert tb.year_of("4th c. and 12th c.", "life_dates") == 1150
    assert tb.year_of("4th c. and 12th c.", "work_date") == 350


def test_a_long_value_is_cut_in_messages_only(tmp_path):
    """S3: a message quotes at most MAX_QUOTED_CHARS of a value; the check still sees the whole value."""
    from survey_support import survey_core as core
    root = make_repo(tmp_path)
    _evidence(root, add=[_with(attribute_kind="k" * 5000)])
    found = [f for f in _report(root).findings if f.rule == "attribute-kind"]
    assert found and "k" * 201 not in found[0].message and "\u2026" in found[0].message
    assert core.q("x" * 10) == "'xxxxxxxxxx'"
    assert core.q("x" * 300) == repr("x" * core.MAX_QUOTED_CHARS) + "\u2026"


def test_a_read_error_partway_through_a_row_file_is_a_finding(tmp_path, monkeypatch):
    """S2: an OSError while the rows are read is a finding, not a traceback."""
    import io as _io

    class Failing(_io.StringIO):
        def __next__(self):
            raise OSError("device went away")

    monkeypatch.setattr(tb, "open_text_capped", lambda path, cap: Failing("id\n"))
    rows = tb.read_rows(tmp_path / "any.csv", "any.csv", ("id",), "columns")
    assert [f.rule for f in rows.findings] == ["columns"] and "device went away" in rows.findings[0].message


def test_a_usage_error_is_printed_escaped(tmp_path):
    """S1: a project name holding a control character reaches stderr escaped."""
    root = make_repo(tmp_path)
    code, _out, err = run(survey_validate, "--root", str(root), "tide\x1bbell")
    assert code == 2 and "\x1b" not in err and "\\x1b" in err
