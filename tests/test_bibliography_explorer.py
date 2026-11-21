"""The bibliography explorer: citation code, exporter and the template's fixed properties
(templates/bibliography-explorer/CONTRACT.md).

Export tests copy the invented example inputs to tmp_path, change one thing and run the exporter.
"""
import csv
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "bibliography-explorer"
EXAMPLE = TEMPLATE / "example"
SCRIPT = ROOT / "scripts" / "build_bibliography_explorer.py"

sys.path.insert(0, str(ROOT / "scripts"))
import bibtex_chicago as bc  # noqa: E402
import build_bibliography_explorer as exporter  # noqa: E402


def cite(bib: str) -> str:
    (entry,) = bc.parse_bib(bib)
    fields, _ = bc.decode_entry(entry)
    return "".join(run["text"] for run in bc.render_chicago(entry["type"], fields))


# --------------------------------------------------------------------------- LaTeX and names
@pytest.mark.parametrize("latex, text", [
    (r"Ionu{\c{t}}", "Ionuţ"),
    (r"Mar{\'i}a", "María"),
    (r"\v{S}\'{\i}", "Ší"),
    (r"na\"{\i}ve {\"o} \ss{} \L\'od\'z", "naïve ö ß Łódź"),
    (r"1800--1900 --- A~B", "1800–1900 — A B"),
    (r"R \& D, 50\%, {\emph{Nested {Braces}}}", "R & D, 50%, Nested Braces"),
    (r"``quoted''", "“quoted”"),
])
def test_latex_is_decoded(latex, text):
    assert bc.latex_to_unicode(latex) == text


@pytest.mark.parametrize("latex", [r"\unknowncommand{x}", r"$x^2$", r"{unclosed", r"stray}"])
def test_latex_that_cannot_be_read_is_an_error(latex):
    with pytest.raises(bc.BibError):
        bc.latex_to_unicode(latex)


def test_names_are_read_in_every_form():
    names, et_al = bc.split_names(
        r"Ionu{\c{t}} Example and {{Guild of Makers and Menders}} and de la Fictive, Ana and "
        r"Ludwig van Sample and Brask, Jr., Tolliver and Mononym and others")
    assert names == [
        {"family": "Example", "given": "Ionuţ"},
        {"literal": "Guild of Makers and Menders"},
        {"family": "de la Fictive", "given": "Ana"},
        {"family": "van Sample", "given": "Ludwig"},
        {"family": "Brask", "given": "Tolliver", "suffix": "Jr."},
        {"family": "Mononym"},
    ]
    assert et_al is True


@pytest.mark.parametrize("raw", ["A, B, C, D", "others", "Doe, Jane and {}", "A and others and B"])
def test_a_name_list_that_cannot_be_read_is_an_error(raw):
    with pytest.raises(bc.BibError):
        bc.split_names(raw)


def test_et_al_and_quotes_inside_a_quoted_title():
    assert cite("@article{k, author={Smith, John and others}, title={On ``Being'' Invented}}") == \
        "Smith, John, et al. “On ‘Being’ Invented.”"


# --------------------------------------------------------------------------- parser
def test_parser_reads_macros_cases_quotes_and_comments():
    entries = bc.parse_bib('''
% a comment line with an @ sign
@comment{ignored {nested}}
@string{press = "Invented Press"}
@Book{k1, TITLE = "A {B} C", publisher = press # " Ltd", year = 1901, month = mar,}
''')
    assert entries[0]["key"] == "k1" and entries[0]["type"] == "book"
    assert entries[0]["fields"] == {"title": "A {B} C", "publisher": "Invented Press Ltd",
                                    "year": "1901", "month": "March"}


@pytest.mark.parametrize("bib, message", [
    ("@book{k, title = {unclosed {brace}", "unclosed brace"),
    ("@book{k, title = {a}}\n@book{k, title = {b}}", "used twice"),
    ("@book{k, title = {a}, Title = {b}}", "appears twice"),
    ("@book{k, title = undefinedmacro}", "undefined abbreviation"),
    ("@book{k, title = {a {b}\n@book{j, title = {c}}\n}}", "runs into the next entry"),
    ("@book{, title = {a}}", "no key"),
    ("@book{k, title = {a} year = {2000}}", "comma is missing"),
    ("@book{Key, title = {a}}\n@book{key, title = {b}}", "used twice"),
])
def test_malformed_bib_is_an_error(bib, message):
    with pytest.raises(bc.BibError, match=message):
        bc.parse_bib(bib)


# --------------------------------------------------------------------------- Chicago
@pytest.mark.parametrize("bib, expected", [
    ("@book{k, author={Brask, Tolliver and Ana de la Fictive}, title={An Invented History, 1750--1900}, "
     "publisher={Invented Press}, address={Nowhere}, year={1950}, volume={2}, series={Imaginary Studies}, number={7}}",
     "Brask, Tolliver, and Ana de la Fictive. An Invented History, 1750–1900. Vol. 2. Imaginary Studies 7. "
     "Nowhere: Invented Press, 1950."),
    ("@book{k, editor={Ed One and Ed Two}, title={Edited Volume}, publisher={Invented Press}, year={2000}}",
     "One, Ed, and Ed Two, eds. Edited Volume. Invented Press, 2000."),
    ("@book{k, author={A. Author}, editor={Ed One}, title={Collected}, year={2000}}",
     "Author, A. Collected. Edited by Ed One. 2000."),
    ("@article{k, author={Sample, Q. R.}, title={Is This Real?}, journal={Journal of Invented Results}, "
     "volume={12}, number={3}, month=mar, year={2001}, pages={45-67}, DOI={https://doi.org/10.5555/x.1}}",
     "Sample, Q. R. “Is This Real?” Journal of Invented Results 12, no. 3 (March 2001): 45–67. "
     "https://doi.org/10.5555/x.1."),
    ("@incollection{k, author={Placeholder, Pat}, title={A Chapter}, booktitle={The Made-Up Handbook}, "
     "editor={Ed One}, pages={1--9}, publisher={Invented Press}, address={Nowhere}, year={1999}}",
     "Placeholder, Pat. “A Chapter.” In The Made-Up Handbook, edited by Ed One, 1–9. Nowhere: Invented Press, 1999."),
    ("@phdthesis{k, author={Nobody, Nell}, title={On Nothing}, school={University of Nowhere}, year={1980}, "
     "url={https://example.org/a\\_b}}",
     "Nobody, Nell. “On Nothing.” PhD diss., University of Nowhere, 1980. https://example.org/a_b."),
    ("@misc{k, author={{Guild of Makers}}, title={Charter}, howpublished={Invented Archive}, year={1903}, "
     "note={never part of the citation}}",
     "Guild of Makers. “Charter.” Invented Archive. 1903."),
    ("@misc{k, title={Only a Title}}", "“Only a Title.”"),
])
def test_chicago_entries(bib, expected):
    assert cite(bib) == expected


def test_italic_runs_join_to_the_plain_citation():
    (entry,) = bc.parse_bib("@book{k, author={A. Author}, title={The Title}, year={2000}}")
    runs = bc.render_chicago("book", bc.decode_entry(entry)[0])
    assert {"text": "The Title", "italic": True} in runs
    assert "".join(r["text"] for r in runs) == "Author, A. The Title. 2000."


def test_more_than_ten_authors_are_cut_to_seven():
    authors = " and ".join(f"Person{n}, P." for n in range(11))
    text = cite(f"@book{{k, author={{{authors}}}, title={{T}}}}")
    assert "Person6" in text and "Person7" not in text and "et al." in text


def test_unsupported_type_and_bad_doi_are_errors():
    with pytest.raises(bc.BibError, match="unsupported entry type"):
        cite("@techreport{k, title={T}}")
    with pytest.raises(bc.BibError, match="doi"):
        cite("@book{k, title={T}, doi={not-a-doi}}")


# --------------------------------------------------------------------------- exporter
@pytest.fixture
def inputs(tmp_path):
    shutil.copytree(EXAMPLE / "inputs", tmp_path / "in")
    return tmp_path / "in"


def export(inputs, **kw):
    return exporter.build(inputs, kw.get("bib", inputs / "example.bib"), kw.get("literature"))


def edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not in {path.name}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def test_example_export_is_current_and_deterministic(inputs, tmp_path):
    """The committed example file is what the exporter writes from the committed inputs."""
    out = tmp_path / "out.json"
    cmd = [sys.executable, str(SCRIPT), str(inputs), "--bib", str(inputs / "example.bib"),
           "--out", str(out), "--report", str(tmp_path / "report.txt")]
    assert subprocess.run(cmd).returncode == 0
    first = out.read_bytes()
    assert subprocess.run(cmd).returncode == 0
    assert out.read_bytes() == first
    assert first == (EXAMPLE / "explorer-data.json").read_bytes()
    assert "does not mean" in (tmp_path / "report.txt").read_text(encoding="utf-8")


def test_established_about_links_and_free_text_sources_are_computed(inputs):
    doc, run, made = export(inputs)
    assert run.errors == []
    ada = next(p for p in doc["persons"] if p["id"] == "ada-wickmere")
    by_value = {a["value"]: a for a in ada["attributes"]}
    assert by_value["1811–1879"] == {"kind": "life-dates", "value": "1811–1879", "established": True,
                                     "evidence_ids": ["ev-001", "ev-002"]}
    assert by_value["Keeper of the pattern book"]["established"] is False
    about = [l for l in doc["links"] if l["relation"] == "about" and l["person_id"] == "ada-wickmere"
             and l["source_id"] == "brask-fictive-1950"]
    assert about == [{"person_id": "ada-wickmere", "source_id": "brask-fictive-1950", "relation": "about",
                      "attribute_kinds": ["life-dates", "origin"], "evidence_ids": ["ev-001", "ev-003"]}]
    free = [s for s in doc["sources"] if s["origin"] == "evidence-citation"]
    assert len(free) == len(made) == 5 and all(s["id"].startswith("ec-") for s in free)
    assert all("chicago" not in s["citation"] for s in free)
    cited = next(e for e in doc["evidence"] if e["id"] == "ev-004")
    assert cited["source_id"] == "guild-charter-1903" and cited["cited_as"].startswith("Charter")
    assert doc["periods"][-1]["established"] is False
    assert "grouped by url" in exporter.report(doc, run, made)


def test_quote_is_kept_exactly_and_other_cells_are_trimmed(inputs):
    edit(inputs / "evidence.csv", '"Wickmere, born', '"  Wickmere, born')
    edit(inputs / "evidence.csv", "ev-003,ada-wickmere,origin,Mirrowmere,", "ev-003,ada-wickmere,origin,  Mirrowmere ,")
    doc, run, _ = export(inputs)
    assert run.errors == []
    ev = {e["id"]: e for e in doc["evidence"]}
    assert ev["ev-001"]["quote"].startswith("  Wickmere")
    assert ev["ev-003"]["value"] == "Mirrowmere"


def test_evidence_basis_reporter_and_note_are_carried(inputs):
    """Contract 1.1: the three optional evidence columns reach the explorer file; empty cells are omitted."""
    doc, run, _ = export(inputs)
    assert run.errors == [] and doc["schema_version"] == "1.1"
    ev = {e["id"]: e for e in doc["evidence"]}
    assert (ev["ev-005"]["basis"], ev["ev-005"]["reporter"], ev["ev-005"]["note"]) == \
        ("reported", "the encyclopedia's anonymous editor", "The entry names no source for this.")
    assert ev["ev-006"]["basis"] == "own" and "reporter" not in ev["ev-006"] and "note" not in ev["ev-006"]
    assert not {"basis", "reporter", "note"} & set(ev["ev-001"])


@pytest.mark.parametrize("kept", [[], ["note"], ["basis", "reporter"]])
def test_an_evidence_file_without_the_optional_columns_is_valid(inputs, kept):
    """An input written for contract 1.0 (thirteen columns) still exports, as does any subset of the three."""
    path = inputs / "evidence.csv"
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline="")))
    columns = [c for c in rows[0] if c not in {"basis", "reporter", "note"} or c in kept]
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, columns, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(out.getvalue(), encoding="utf-8")
    doc, run, _ = export(inputs)
    assert run.errors == []
    carried = {k for e in doc["evidence"] for k in e} & {"basis", "reporter", "note"}
    assert carried == set(kept)


def test_component_shows_the_evidence_basis_reporter_and_note():
    """Rule 5. A static check, because CI has no JavaScript runtime."""
    source = (TEMPLATE / "explorer.js").read_text(encoding="utf-8")
    for shown in ("row(L.evidenceBasis, ev.basis)", "row(L.reporter, ev.reporter)", "row(L.evidenceNote, ev.note)"):
        assert shown in source, shown


CASES = [
    ("persons.csv", "ionut_glasswright,person", "ada-wickmere,person", "used twice"),
    ("persons.csv", "middle,1842", "middle,1742", "outside the period"),
    ("persons.csv", "middle,1871", "nowhere,1871", "unknown period"),
    ("persons.csv", "unknown,,", "unknown,1900,", "unestablished period"),
    ("persons.csv", "id,kind,display_name", "id,kind,surprise,display_name", "columns must be exactly"),
    ("evidence.csv", "ev-003,ada-wickmere", "ev 003,ada-wickmere", "not a valid id"),
    ("evidence.csv", "ev-003,ada-wickmere,origin,Mirrowmere,confirmed", "ev-003,ada-wickmere,origin,Mirrowmere,certain", "unknown tier"),
    ("evidence.csv", "ev-003,ada-wickmere,origin,Mirrowmere,confirmed,brask-fictive-1950", "ev-003,ada-wickmere,origin,Mirrowmere,confirmed,no-such-key", "names no .bib entry"),
    ("evidence.csv", "ev-016,unnamed-apprentice,role,not established,not-established,,\"Searched: guild register (fictional)\"", "ev-016,unnamed-apprentice,role,not established,not-established,,", "neither source_id nor citation"),
    ("evidence.csv", "https://example.org/encyclopedia/quillon", "javascript:alert(1)", "not an http"),
    ("evidence.csv", "reported,the encyclopedia's anonymous editor", ",the encyclopedia's anonymous editor", "reporter is given without a basis"),
    ("evidence.csv", "via,audit,basis,reporter,note", "via,audit,basis,reporter,note,extra", "columns must be exactly"),
    ("evidence.csv", "via,audit,basis,reporter,note", "via,audit,basis,reporter,basis", "columns must be exactly"),
    ("codes.csv", "Not established,false,,\nionut", "Yes,true,,\nionut", "needs evidence"),
    ("codes.csv", "true,,ev-001", "true,,ev-009", "belongs to another person"),
    ("bios.json", "She was master of the guild.\",\n", "She led the guild.\",\n", "differs from the clauses"),
    ("bios.json", "\"basis\": \"written\",\n    \"verification_state\": \"UNVERIFIED — invented example\"", "\"basis\": \"written\"", "missing verification_state"),
    ("groups.json", "\"caveat\": \"Advisory only. This assessment is the example's own reading of invented rolls and settles nothing.\",", "", "caveat"),
    ("groups.json", "https://example.org/rolls/honour", "ftp://example.org/rolls", "not an http"),
    ("links.csv", "wickmere-letters,attributed", "wickmere-letters,", "needs a role"),
    ("links.csv", "tolliver-brask,brask-fictive-1950", "tolliver-brask,missing-source", "unknown source"),
    ("summaries.jsonl", "\"deemed_by\": \"example generator\", \"basis\": \"abstract\"", "\"deemed_by\": \"\", \"basis\": \"abstract\"", "deemed_by"),
    ("source_attributes.csv", "wickmere-trimming,Kind", "nobody-here,Kind", "unknown source"),
    ("example.bib", "@phdthesis{nobody-thesis-1980", "@techreport{nobody-thesis-1980", "unsupported entry type"),
    ("example.bib", "Mar{\\'i}a", "Mar{\\zz{i}}a", "unknown LaTeX command"),
    ("groups.json", "\"value\": \"Two\"", "\"value\": 2", "value must be a string"),
    ("groups.json", "\"id\": \"standing\"", "\"id\": [\"standing\"]", "not a valid id"),
    ("explorer.json", "\"id\": \"early\"", "\"id\": {\"a\": 1}", "not a valid id"),
    ("summaries.jsonl", "{\"source_id\": \"brask-fictive-1950\"", "{\"source_id\": [\"brask-fictive-1950\"]", "unknown source"),
    ("example.bib", "author  = {Ionu{\\c{t}} Sample and Q. R. Placeholder}", "author  = {others}", "'others' with no name"),
    ("explorer.json", "\"end_year\": 1799", "\"end_year\": 1850", "overlap"),
    ("explorer.json", "\"start_year\": null, \"end_year\": null, \"established\": false", "\"start_year\": null, \"end_year\": null, \"established\": false, \"colour\": 1", "unknown key"),
]


@pytest.mark.parametrize("name, old, new, message", CASES, ids=[f"{c[0]}:{c[3]}" for c in CASES])
def test_a_broken_input_fails_closed(inputs, tmp_path, name, old, new, message):
    edit(inputs / name, old, new)
    out = tmp_path / "out.json"
    proc = subprocess.run([sys.executable, str(SCRIPT), str(inputs), "--bib", str(inputs / "example.bib"),
                           "--out", str(out)], capture_output=True, text=True)
    assert proc.returncode == 1
    assert not out.exists()
    assert message in proc.stdout
    assert "Traceback" not in proc.stderr


def test_a_failed_export_removes_an_earlier_output_and_reports_no_traceback(inputs, tmp_path):
    out = tmp_path / "out.json"
    cmd = [sys.executable, str(SCRIPT), str(inputs), "--bib", str(inputs / "example.bib"), "--out", str(out)]
    assert subprocess.run(cmd, capture_output=True).returncode == 0 and out.exists()
    edit(inputs / "persons.csv", "middle,1842", "middle,1742")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 1 and not out.exists()
    assert "was removed" in proc.stderr and "Traceback" not in proc.stderr
    assert list(tmp_path.glob("out.json.*")) == []


def test_a_failed_export_removes_the_earlier_output_even_when_the_report_cannot_be_written(inputs, tmp_path):
    out = tmp_path / "out.json"
    out.write_text("{}", encoding="utf-8")
    edit(inputs / "persons.csv", "middle,1842", "middle,1742")
    proc = subprocess.run([sys.executable, str(SCRIPT), str(inputs), "--bib", str(inputs / "example.bib"),
                           "--out", str(out), "--report", str(tmp_path / "missing" / "r.txt")],
                          capture_output=True, text=True)
    assert proc.returncode == 2 and not out.exists()


def test_an_unwritable_output_path_is_a_usage_error(inputs, tmp_path):
    proc = subprocess.run([sys.executable, str(SCRIPT), str(inputs), "--bib", str(inputs / "example.bib"),
                           "--out", str(tmp_path / "missing" / "out.json"), "--report", str(tmp_path / "r.txt")],
                          capture_output=True, text=True)
    assert proc.returncode == 2 and "Traceback" not in proc.stderr


def test_group_output_omits_empty_optional_fields(inputs):
    edit(inputs / "groups.json", '"value": "Two", "links"', '"value": "Two", "note": "", "evidence_ids": [], "links"')
    doc, run, _ = export(inputs)
    assert run.errors == []
    row = next(p for p in doc["persons"] if p["id"] == "ada-wickmere")["groups"][0]["rows"][0]
    assert set(row) == {"label", "value", "links"}


def test_literature_library_maps_only_agent_authored_records(inputs, tmp_path):
    (inputs / "summaries.jsonl").unlink()
    lib = tmp_path / "literature.jsonl"
    state = "UNVERIFIED — no human resolution performed"
    records = [
        {"key": "brask-fictive-1950", "verification_state": state,
         "relevance": {"summary": "An invented history.", "source": "agent-authored", "deemed_by": "agent-x",
                       "basis": "abstract", "read_url": "https://example.org/r", "caveats": ["snippet only"]}},
        {"key": "sample-question-2001", "verification_state": state,
         "relevance": {"summary": "Another.", "source": "agent-authored", "deemed_by": "agent-x"}},
        {"key": "nobody-thesis-1980", "verification_state": state,
         "relevance": {"summary": "A bib note.", "source": "seeded-from-bib-note"}},
        {"key": "guild-charter-1903", "verification_state": state,
         "relevance": {"summary": "No author recorded.", "source": "agent-authored", "deemed_by": None}},
    ]
    lib.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    doc, run, _ = export(inputs, literature=lib)
    assert run.errors == []
    src = {s["id"]: s for s in doc["sources"]}
    assert src["brask-fictive-1950"]["summary"] == {
        "text": "An invented history.", "deemed_by": "agent-x", "basis": "abstract",
        "read_url": "https://example.org/r", "caveats": ["snippet only"], "verification_state": state}
    assert src["sample-question-2001"]["summary"]["basis"] == "record only"
    assert "summary" not in src["nobody-thesis-1980"]
    assert "summary" not in src["guild-charter-1903"]
    skipped = [w for w in run.warnings if "skipped" in w]
    assert len(skipped) == 2 and "'nobody-thesis-1980'" in skipped[0] and "no relevance.deemed_by" in skipped[1]


def test_a_source_summarised_twice_is_an_error(inputs, tmp_path):
    lib = tmp_path / "literature.jsonl"
    lib.write_text(json.dumps({"key": "brask-fictive-1950", "verification_state": "UNVERIFIED",
                               "relevance": {"summary": "s", "source": "agent-authored", "deemed_by": "a"}}) + "\n")
    _, run, _ = export(inputs, literature=lib)
    assert any("already has a summary" in e for e in run.errors)


def test_usage_error_for_a_missing_directory(tmp_path):
    proc = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path / "nope"), "--out", str(tmp_path / "o")],
                          capture_output=True, text=True)
    assert proc.returncode == 2


# --------------------------------------------------------------------------- template properties
def test_component_never_parses_markup_or_touches_the_url():
    """CONTRACT.md rule 4: text is text. A static check, because CI has no JavaScript runtime."""
    source = (TEMPLATE / "explorer.js").read_text(encoding="utf-8")
    for banned in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "DOMParser", "eval(",
                   "new Function", "location.", "history.", "localStorage", "import("):
        assert banned not in source, banned
    assert re.findall(r"^import .*$", source, flags=re.M) == []


def test_example_data_is_marked_invented_and_uses_reserved_addresses():
    data = json.loads((EXAMPLE / "explorer-data.json").read_text(encoding="utf-8"))
    assert "invented" in data["meta"]["notice"].lower()
    text = json.dumps(data)
    assert set(re.findall(r"https?://([^/\"\\]+)", text)) <= {"example.org", "doi.org"}
    assert all(d.startswith("10.5555/") for d in re.findall(r"doi\.org/([^\"\\]+)", text))


def test_vendoring_file_list_is_current():
    listed = {}
    for line in (TEMPLATE / "FILES.sha256").read_text(encoding="utf-8").splitlines():
        digest, path = line.split("  ", 1)
        listed[path] = digest
    assert set(listed) == {"templates/bibliography-explorer/explorer.js",
                           "templates/bibliography-explorer/explorer.css",
                           "templates/bibliography-explorer/CONTRACT.md",
                           "scripts/build_bibliography_explorer.py", "scripts/bibtex_chicago.py"}
    for path, digest in listed.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, f"{path}: rerun the hash list"
