"""Step D part 1: survey-frame (contract 4.7; the frame-change log check of 4.4, lines 461-476; the post-step checks
of 4.5, without running a step). Expected outputs are worked out by hand from the invented study."""
import json
import os
import shutil
import subprocess
import sys

import pytest

from survey_support import ROOT, STUDY_REL, SURVEY, make_repo, run, survey_provenance as prov, tree

_saved = sys.dont_write_bytecode
sys.dont_write_bytecode = True
import survey_cells as sc  # noqa: E402
import survey_changelog as cl  # noqa: E402
import survey_finalize  # noqa: E402
import survey_frame  # noqa: E402
sys.dont_write_bytecode = _saved

ROWS = f"{STUDY_REL}/rows"
OUT = f"{STUDY_REL}/out"
LOG = f"{ROWS}/frame-changes.jsonl"
CELLS = ["warden-01|logbook", "warden-02|letter"]

#: The invented study's frame, by hand (4.7), with the rule not-on-question removed (open point: the dropped list's
#: name). Cells: p-001 (warden-01, logbook, firm) and p-002 (warden-02, letter, firm); p-003 is "doubtful", so
#: guild-01 has no counted passage and no cell. warden-01|logbook: ev-001's work_date 1742 is in period 1 ("early",
#: cuts 1750, 1800); no harbour or duty row: harbour NE, duties_NE 1; slack_bell agreed "for". warden-02|letter: no
#: work_date row, no person-level life_dates row: era NE; ev-003 "North Quay" -> "north" (the harbour table); no duty
#: row; slack_bell adjudicated "tolerates".
FRAME = (b'"unit_id","author","genre","unit_kind","era","era_num","harbour","duties_lamp","duties_bell","duties_NE",'
         b'"slack_bell"\n'
         b'"warden-01|logbook","warden-01","logbook","person","early","1","NE","0","0","1","for"\n'
         b'"warden-02|letter","warden-02","letter","person","NE","NE","north","0","0","1","tolerates"\n')
#: The passage list (lines 656-671): one row per evidence row on an attribution unit, in evidence-file order;
#: ev-002 and ev-004 are person-level and not listed; p-003's status "doubtful" is not counted.
PASSAGES = (b'"unit_id","passage_id","evidence_id","person_id","attribution","counted","not_counted_reason"\n'
            b'"warden-01|logbook","p-001","ev-001","warden-01","firm","true",""\n'
            b'"warden-02|letter","p-002","ev-003","warden-02","firm","true",""\n'
            b'"guild-01|letter","p-003","ev-005","guild-01","doubtful","false","attribution-doubtful"\n')
SHA = cl.frame_sha256(FRAME)


def _no_rule(s):
    s["frame_rules"]["exclude"] = []


def _entry(units=CELLS, sha=SHA, added=None, removed=(), eid="fc-1", **more):
    e = {"id": eid, "date": "2026-11-25", "reason": "the first frame", "results_seen": False, "frame_sha256": sha,
         "n_units": len(units), "added": list(units if added is None else added), "removed": list(removed),
         "units": list(units)}
    e.update(more)
    return json.dumps(e) + "\n"


def _repo(tmp_path, mutate=None, log=True):
    def both(s):
        _no_rule(s)
        if mutate is not None:
            mutate(s)
    root = make_repo(tmp_path, both)
    (root / OUT).mkdir()
    if log:
        (root / LOG).write_text(_entry(), encoding="utf-8")
    assert run(survey_finalize, "--root", str(root), "tidebell", "--out", "out/final.csv")[0] == 0
    return root


def _frame(root, final="out/final.csv", out="out/frame.csv", passages="out/passages.csv"):
    return run(survey_frame, "--root", str(root), "tidebell", final, "--out", out, "--passages", passages)


def _refused(root, *args, needle=""):
    before = tree(root)
    code, out, _ = _frame(root, *args)
    assert code == 1 and "REFUSED" in out and needle in out, out
    assert tree(root) == before
    return out


# --------------------------------------------------------------------------- the invented study
def test_the_invented_studys_frame_and_passage_list(tmp_path):
    root = _repo(tmp_path)
    code, out, _ = _frame(root)
    assert code == 0, out
    assert (root / OUT / "frame.csv").read_bytes() == FRAME
    assert (root / OUT / "passages.csv").read_bytes() == PASSAGES
    assert f"frame_sha256 {SHA}" in out


def test_the_records(tmp_path):
    """4.6; line 653: gates S5 and S6; every file read, the frame-change log among them."""
    root = _repo(tmp_path)
    _frame(root)
    for name in ("frame.csv", "passages.csv"):
        doc = json.loads((root / OUT / f"{name}.provenance.json").read_bytes())
        assert prov.check_record_shape(doc, "r") == [] and doc["tool"] == "survey-frame"
        assert list(doc["gates"]) == ["S5", "S6"] and doc["plugins"] == [] and doc["legacy_exceptions"] == 0
        paths = [e["path"] for e in doc["inputs"]]
        assert paths[:3] == [f"{STUDY_REL}/study.json", f"{OUT}/final.csv", f"{OUT}/final.csv.provenance.json"]
        assert paths[-1] == LOG
        assert prov.check_current(root, f"{OUT}/{name}.provenance.json").built


def test_the_records_inputs_are_the_files_read(tmp_path, monkeypatch):
    """4.6 line 563: every file the command opens is in its inputs (gate S5 and S6's reads aside, which their gates
    entries stand for: operator ruling O4)."""
    import survey_core as core
    root = _repo(tmp_path)
    seen = []
    real = core._open_regular

    def note(path):
        p = os.path.realpath(path)
        base = os.path.realpath(root) + os.sep
        if p.startswith(base):
            seen.append(p[len(base):].replace(os.sep, "/"))
        return real(path)
    monkeypatch.setattr(core, "_open_regular", note)
    real_open = open

    def opener(path, *a, **k):
        note_path = os.path.realpath(path)
        if note_path.startswith(os.path.realpath(root) + os.sep):
            seen.append(note_path[len(os.path.realpath(root)) + 1:].replace(os.sep, "/"))
        return real_open(path, *a, **k)
    monkeypatch.setattr(core, "open", opener, raising=False)
    assert _frame(root)[0] == 0
    doc = json.loads((root / OUT / "frame.csv.provenance.json").read_bytes())
    gate_reads = (f"{STUDY_REL}/ledger/", f"{STUDY_REL}/codebooks/", f"{STUDY_REL}/analysis/")
    outputs = {f"{OUT}/{n}{s}" for n in ("frame.csv", "passages.csv") for s in ("", ".provenance.json")}
    opened = {p for p in seen if not p.startswith(gate_reads) and p not in outputs}
    assert opened == {e["path"] for e in doc["inputs"] if e["sha256"] != ""}


def test_deterministic_and_unchanged_twice(tmp_path):
    a, b = _repo(tmp_path / "a"), _repo(tmp_path / "b")
    _frame(a), _frame(b)
    for name in ("frame.csv", "passages.csv"):
        assert (a / OUT / name).read_bytes() == (b / OUT / name).read_bytes()
    before = tree(a)
    code, out, _ = _frame(a)
    assert code == 0 and out.startswith("unchanged:") and tree(a) == before


def test_an_existing_different_output_is_refused(tmp_path):
    root = _repo(tmp_path)
    (root / OUT / "passages.csv").write_bytes(b"other\n")
    _refused(root, needle="never appended to or overwritten")


@pytest.mark.parametrize("args,needle", [
    (("out/final.csv", "study.json", "out/passages.csv"), "declared"),
    (("out/final.csv", "../frame.csv", "out/passages.csv"), ""),
    (("out/final.csv", "out/frame.csv", "out/frame.csv"), "same path"),
    (("out/final.csv", "out/final.csv", "out/passages.csv"), "would be the final file"),
    (("out/final.csv", "out/f.provenance.json", "out/passages.csv"), "the name of a provenance record"),
])
def test_where_the_outputs_may_not_go(tmp_path, args, needle):
    root = _repo(tmp_path)
    _refused(root, *args, needle=needle)


# --------------------------------------------------------------------------- refusals before anything is built
def test_an_author_study_is_refused(tmp_path):
    def author(s):
        s["unit"] = {"kind": "author"}
        s["frame_rules"]["exclude"] = []
    root = make_repo(tmp_path, author)
    (root / OUT).mkdir()
    before = tree(root)
    code, out, _ = _frame(root)
    assert code == 1 and "author study's frame is not part of version 1" in out and tree(root) == before


def test_a_plug_in_bucketer_is_refused(tmp_path):
    """Line 639: refused in a frame, and nothing is written (open point 6)."""
    root = _repo(tmp_path)
    plug = root / STUDY_REL / "rules" / "bucket.py"
    plug.write_text("def bucket(values):\n    return 'north'\n", encoding="utf-8")

    def mutate(s):
        s["attributes"][0]["bucketer"] = {"kind": "plugin", "plugin": {"file": "rules/bucket.py", "attr": "bucket",
                                                                       "version": "1"}}
        s["signoffs"]["gates"]["S0"]["covers"].append("rules/bucket.py")
    from survey_support import edit_spec
    edit_spec(root, mutate)
    out = _refused(root, needle="does not load or define")
    assert "[frame-plugin-bucketer]" in out


def test_a_study_declaring_not_on_question_stops_on_the_open_point(tmp_path):
    root = _repo(tmp_path, lambda s: s["frame_rules"]["exclude"].append(
        {"rule": "not-on-question", "reason": "a cell with no code says nothing on the question"}))
    out = _refused(root)
    assert "[frame-dropped-name]" in out and "open point" in out


def test_a_merged_id_named_by_no_file_does_not_stop(tmp_path):
    root = _repo(tmp_path)
    reg = root / ROWS / "registry.csv"
    reg.write_bytes(reg.read_bytes().replace(b"Tamsin Rook (invented),,\n", b"Tamsin Rook (invented),,warden-09\n"))
    assert run(survey_finalize, "--root", str(root), "tidebell", "--out", "out/final.csv")[0] == 0
    assert _frame(root)[0] == 0


def test_a_merged_id_still_named_stops_on_the_open_point(tmp_path):
    """warden-02 is merged into warden-02b, but the attribution and evidence files still name warden-02: whether the
    frame reads warden-02's rows as warden-02b's is open, so the build stops."""
    root = _repo(tmp_path)
    reg = root / ROWS / "registry.csv"
    reg.write_bytes(reg.read_bytes().replace(b"warden-02,Tamsin Rook (invented),,\n",
                                             b"warden-02b,Tamsin Rook (invented),,warden-02\n"))
    assert run(survey_finalize, "--root", str(root), "tidebell", "--out", "out/final.csv")[0] == 0
    out = _refused(root)
    assert "[frame-merged-id]" in out and "'warden-02'" in out


# --------------------------------------------------------------------------- the final codes must be current (line 653)
def test_a_final_file_that_is_not_current_is_refused(tmp_path):
    root = _repo(tmp_path)
    vocab = root / STUDY_REL / "rules" / "forbidden.txt"
    vocab.write_bytes(vocab.read_bytes() + b"# a comment\n")
    _refused(root, needle="not a current output of survey-finalize")


def test_a_hand_edited_final_file_is_refused(tmp_path):
    root = _repo(tmp_path)
    path = root / OUT / "final.csv"
    path.write_bytes(path.read_bytes().replace(b"tolerates", b"against"))
    _refused(root, needle="is not what survey-finalize gives")


# --------------------------------------------------------------------------- the frame-change log (4.4)
def test_no_entry_refuses_and_prints_the_entry_needed(tmp_path):
    root = _repo(tmp_path, log=False)
    out = _refused(root, needle="does not end with this frame's entry")
    assert "the entry the log needs" in out and SHA in out and '"results_seen": null' in out
    assert '"added": ["warden-01|logbook", "warden-02|letter"]' in out


def test_a_changed_frame_needs_a_new_entry(tmp_path):
    """p-002's adjudication changed: the frame differs from the last entry, so nothing is written and the new entry
    is printed (nothing added or removed: the same cells)."""
    root = _repo(tmp_path)
    adj = root / ROWS / "adjudications-slack_bell.csv"
    adj.write_bytes(adj.read_bytes().replace(b"p-002,slack_bell,tolerates", b"p-002,slack_bell,against"))
    assert run(survey_finalize, "--root", str(root), "tidebell", "--out", "out/final2.csv")[0] == 0
    out = _refused(root, "out/final2.csv", needle="a frame cannot change without an entry")
    assert '"added": [], "removed": []' in out


@pytest.mark.parametrize("log,needle", [
    (_entry() + "\n", "a blank line"),
    ("{not json\n", "not a JSON object"),
    (_entry().replace('"results_seen": false', '"results_seen": 0'), "results_seen"),
    (_entry().replace('"n_units": 2', '"n_units": 3'), "n_units 3 is not the number of units"),
    (_entry(added=["warden-01|logbook"]), "the first entry lists every unit as added"),
    (_entry().replace('"reason": "the first frame", ', ''), "an entry has exactly the fields"),
    (_entry() + _entry(eid="fc-1"), "given twice"),
    (_entry(sha="ABC"), "64 lower-case hex digits"),
])
def test_a_malformed_log_is_refused_and_no_entry_proposed(tmp_path, log, needle):
    root = _repo(tmp_path)
    (root / LOG).write_text(log, encoding="utf-8")
    out = _refused(root, needle=needle)
    assert "[change-log]" in out and "the entry the log needs" not in out


def test_a_later_entry_lists_what_changed():
    first = json.loads(_entry(units=["a"], sha="0" * 64))
    second = json.loads(_entry(units=["a", "b"], added=["b"], eid="fc-2"))
    data = (json.dumps(first) + "\n" + json.dumps(second) + "\n").encode()
    entries, findings = cl.read_log(data, "log")
    assert findings == [] and len(entries) == 2
    bad = json.loads(_entry(units=["b"], added=["b"], removed=[], eid="fc-2"))
    _e, findings = cl.read_log((json.dumps(first) + "\n" + json.dumps(bad) + "\n").encode(), "log")
    assert [f.rule for f in findings] == ["change-log"] and "gained and lost" in findings[0].message


def test_the_frame_hash_is_a_text_files():
    assert cl.frame_sha256(b"a\r\nb\n") == cl.frame_sha256(b"a\nb\n")


# --------------------------------------------------------------------------- post-steps (4.5): checked, not run
def _with_step(root, gate, declared="steps/add.py"):
    step = root / STUDY_REL / "steps"
    step.mkdir(exist_ok=True)
    (step / "add.py").write_text("print('never run')\n", encoding="utf-8")
    from survey_support import edit_spec

    def mutate(s):
        s["frame_rules"]["post_steps"] = [declared]
        s["signoffs"]["gates"][gate]["covers"].append(declared)
    edit_spec(root, mutate)


def test_post_steps_allowed_by_their_gate_are_not_yet_run(tmp_path):
    """S6 is build-only: the gate allows the step, and this version refuses with a clear finding."""
    root = _repo(tmp_path)
    _with_step(root, "S6")
    out = _refused(root)
    assert "[post-steps-unavailable]" in out and "not yet available" in out


def test_a_post_step_under_a_blocking_gate_not_cleared_is_refused(tmp_path):
    root = _repo(tmp_path)
    _with_step(root, "S5")
    out = _refused(root)
    assert "[post-step-gate]" in out and "UNCLEARED" in out and "[post-steps-unavailable]" not in out


def test_a_post_step_outside_the_study_folder_is_refused(tmp_path):
    root = _repo(tmp_path)
    (root / "steps").mkdir()
    (root / "steps" / "add.py").write_text("print('never run')\n", encoding="utf-8")
    from survey_support import edit_spec

    def mutate(s):
        s["frame_rules"]["post_steps"] = ["repo:steps/add.py"]
        s["signoffs"]["gates"]["S6"]["covers"].append("repo:steps/add.py")
    edit_spec(root, mutate)
    out = _refused(root)
    assert "[post-step-place]" in out


def test_a_linked_post_step_is_refused(tmp_path):
    root = _repo(tmp_path)
    _with_step(root, "S6")
    step = root / STUDY_REL / "steps"
    os.replace(step / "add.py", step / "real.py")
    os.symlink("real.py", step / "add.py")
    out = _refused(root)
    assert "[post-step-place]" in out and "symbolic link" in out


def test_no_post_step_is_executed(tmp_path, monkeypatch):
    """Part 1 runs no project code: no child process is started and nothing is imported from the step."""
    root = _repo(tmp_path)
    _with_step(root, "S6")
    started = []
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: started.append(a) or (_ for _ in ()).throw(OSError()))
    _refused(root)
    assert started == [] and "add" not in sys.modules


# --------------------------------------------------------------------------- the rules by hand (4.7)
SPEC = {
    "unit": {"kind": "passage", "attribution": {"counted_statuses": ["firm"]}, "rollup_by": [],
             "passage_attributes": [], "collective": {"kinds": ["guild"]}},
    "evidence": {"counted_tiers": ["quoted"]},
    "attributes": [
        {"key": "harbour", "kind": "categorical", "source_attributes": ["harbour"], "levels": ["north", "other"],
         "bucketer": {"kind": "table", "fallback": "other"}},
        {"key": "duties", "kind": "flags", "source_attributes": ["duty"], "flags": ["lamp", "bell"],
         "bucketer": {"kind": "table"}},
    ],
    "periods": {"basis": ["work_date", "life_dates"], "cuts": [1750, 1800], "labels": ["early", "middle", "late"]},
    "frame_rules": {"exclude": []},
    "outcomes": [{"key": "o", "source": {"kind": "codes"}, "scale": "ordinal", "rollup": "max-order",
                  "levels": [{"code": "a", "order": 1}, {"code": "b", "order": 2}], "na_codes": ["NA"],
                  "missing": "NE"}],
}


def _tables():
    import re
    from survey_tables import TableRow
    return {"harbour": [TableRow(1, "harbour", re.compile("north"), None, "north")],
            "duties": [TableRow(1, "duty", re.compile("lamp"), None, "lamp"),
                       TableRow(2, "duty", re.compile("bell"), None, "bell")]}


def _att(uid, person, status="firm", kind="person", **more):
    return {"unit_id": uid, "person_id": person, "author_kind": kind, "status": status, **more}


def _ev(eid, person, kind, value, unit, tier="quoted"):
    return {"id": eid, "person_id": person, "attribute_kind": kind, "value": value, "tier": tier, "unit_id": unit}


def _final(uid, code, outcome="o"):
    return {"unit_id": uid, "outcome": outcome, "code": code, "pass": "final"}


def _build(att, ev, finals, spec=SPEC):
    return sc.build(spec, finals, {a["unit_id"]: a for a in att}, ev, _tables())


def test_the_outcome_cell_table():
    """Lines 612-616: none or NA only -> empty; missing and no level code -> missing; a level code -> the rollup."""
    o = SPEC["outcomes"][0]
    cell = lambda codes: sc._outcome_cell(o, codes, "c", "o", lambda *a: None)  # noqa: E731
    assert cell([]) == "" and cell(["NA", "NA"]) == ""
    assert cell(["NE", "NA"]) == "NE"
    assert cell(["a", "NE", "b", "NA"]) == "b"
    seen = []
    assert sc._outcome_cell(o, ["zz"], "c", "o", lambda *a: seen.append(a)) == "" and seen[0][0] == "frame-code"


def test_mixed_if_conflict_in_a_frame_cell():
    o = dict(SPEC["outcomes"][0], rollup="mixed-if-conflict", scale="nominal")
    assert sc._outcome_cell(o, ["a", "b"], "c", "o", lambda *a: None) == "mixed"


def test_the_period_rule():
    """work_date years in one period place the cell; in two the next basis (life_dates, the largest year) is
    tried; a person-level work_date row is not used; an uncounted tier is not used."""
    att = [_att("p1", "x"), _att("p2", "x"), _att("q1", "y"), _att("r1", "z")]
    ev = [_ev("e1", "x", "work_date", "1742", "p1"), _ev("e2", "x", "work_date", "1790", "p2"),
          _ev("e3", "x", "life_dates", "1701-1768", "x"),
          _ev("e4", "y", "work_date", "1810", "y"), _ev("e5", "y", "work_date", "1760", "q1", tier="hearsay"),
          _ev("e6", "z", "work_date", "1742", "r1"), _ev("e7", "z", "work_date", "the year 1749", "r1")]
    built = _build(att, ev, [_final(u, "a") for u in ("p1", "p2", "q1", "r1")])
    rows = {r["unit_id"]: r for r in built.rows}
    assert (rows["x"]["period"], rows["x"]["period_num"]) == ("middle", "2")  # 1742 and 1790 differ; life 1768
    assert (rows["y"]["period"], rows["y"]["period_num"]) == ("NE", "NE")
    assert (rows["z"]["period"], rows["z"]["period_num"]) == ("early", "1")


def test_attribute_evidence():
    """Lines 635-639: the author's rows in counted tiers, person-level or on the cell's passages; bucketed by the
    table; a categorical with no value gets the missing value, one with values none of which fires the fallback;
    flags 1/0 and <key>_<missing>."""
    att = [_att("p1", "x"), _att("q1", "y"), _att("r1", "z")]
    ev = [_ev("e1", "x", "harbour", "North Quay", "x"), _ev("e2", "x", "duty", "lamp and bell", "p1"),
          _ev("e3", "y", "harbour", "East Pier", "q1"), _ev("e4", "y", "duty", "lamp", "q1", tier="hearsay"),
          _ev("e5", "x", "harbour", "south", "q1")]
    rows = {r["unit_id"]: r for r in _build(att, ev, [_final(u, "a") for u in ("p1", "q1", "r1")]).rows}
    assert rows["x"]["harbour"] == "north" and (rows["x"]["duties_lamp"], rows["x"]["duties_bell"],
                                                 rows["x"]["duties_NE"]) == ("1", "1", "0")
    assert rows["y"]["harbour"] == "other" and rows["y"]["duties_NE"] == "1"
    assert rows["z"]["harbour"] == "NE"


def test_cells_split_by_rollup_by_and_ordered_by_code_point():
    spec = json.loads(json.dumps(SPEC))
    spec["unit"]["rollup_by"] = ["genre"]
    spec["unit"]["passage_attributes"] = [{"key": "genre", "levels": [{"code": "logbook"}, {"code": "letter"}]}]
    att = [_att("p1", "x", genre="logbook"), _att("p2", "x", genre="letter"), _att("p3", "B", genre="letter")]
    built = _build(att, [], [_final(u, "a") for u in ("p1", "p2", "p3")], spec)
    assert built.units == ["B|letter", "x|letter", "x|logbook"]


def test_a_cell_without_a_counted_passage_is_not_in_the_frame():
    att = [_att("p1", "x"), _att("p2", "y", status="doubtful")]
    assert _build(att, [], [_final("p1", "a"), _final("p2", "a")]).units == ["x"]


def test_not_on_question_drops_cells_with_all_outcomes_empty():
    """Lines 641-644 (built; the file is not written while its name is open)."""
    spec = json.loads(json.dumps(SPEC))
    spec["frame_rules"]["exclude"] = [{"rule": "not-on-question", "reason": "nothing on the question"}]
    att = [_att("p1", "x"), _att("p2", "y")]
    ev = [_ev("e1", "x", "harbour", "north", "p1"), _ev("e2", "y", "harbour", "north", "p2")]
    built = _build(att, ev, [_final("p1", "a"), _final("p2", "NA")], spec)
    assert built.units == ["x"]
    assert built.dropped == [{"unit_id": "y", "rule": "not-on-question", "reason": "nothing on the question"}]
    assert [r["not_counted_reason"] for r in built.passages] == ["", "not-on-question"]


def test_the_passage_list_reasons_in_order():
    """Lines 663-671: tier first (tier-blank for an empty tier), then exclusion (the first key in the
    specification's order), then the status; person-level rows not listed."""
    spec = json.loads(json.dumps(SPEC))
    spec["unit"]["exclude_from_rollup"] = {"genre": ["draft"], "hand": ["copy"]}
    att = {"p1": _att("p1", "x", genre="draft", hand="copy", status="doubtful"),
           "p2": _att("p2", "x", genre="logbook", hand="copy", status="doubtful"),
           "p3": _att("p3", "x", genre="logbook", hand="own", status="doubtful")}
    ev = [_ev("e1", "x", "harbour", "v", "p1", tier=""), _ev("e2", "x", "harbour", "v", "p1"),
          _ev("e3", "x", "harbour", "v", "p2"), _ev("e4", "x", "harbour", "v", "p3"),
          _ev("e5", "x", "harbour", "v", "x")]
    rows = sc.passage_list(spec, att, ev, set())
    assert [r["not_counted_reason"] for r in rows] == ["tier-blank", "excluded-genre-draft", "excluded-hand-copy",
                                                       "attribution-doubtful"]
    assert all(r["counted"] == "false" for r in rows)


def test_every_cell_is_checked():
    """Lines 651-652: a value its column does not allow, a unit_id given twice, a column missing."""
    cols = sc.frame_columns(SPEC)
    good = {c: "" for c in cols}
    good.update(unit_id="x", author="x", unit_kind="person", period="NE", period_num="NE", harbour="north",
                duties_lamp="0", duties_bell="0", duties_NE="1", o="a")
    assert sc.check_rows(SPEC, cols, [good]) == []
    bad = dict(good, harbour="east", o="NA")
    rules = [f.rule for f in sc.check_rows(SPEC, cols, [bad, good, {"unit_id": "z"}])]
    assert rules.count("frame-value") == 2 and "frame-unit-duplicate" in rules and "frame-column" in rules


def test_the_frame_columns():
    """Line 593, with no period attribute: period and period_num (section 3, line 270)."""
    assert sc.frame_columns(SPEC) == ("unit_id", "author", "unit_kind", "period", "period_num", "harbour",
                                      "duties_lamp", "duties_bell", "duties_NE", "o")


def test_every_cell_is_quoted():
    assert sc.quoted_csv(("a", "b"), [{"a": "1", "b": 'x"y'}]) == b'"a","b"\n"1","x""y"\n'


# --------------------------------------------------------------------------- the bridge
def test_the_bridge_runs_the_command_and_refuses_root(tmp_path):
    root = _repo(tmp_path)
    (root / "scripts").mkdir()
    shutil.copy(ROOT / "scripts" / "claude_researchteam_bridge.sh", root / "scripts")
    shutil.copytree(SURVEY, root / "scripts" / "survey", ignore=shutil.ignore_patterns("__pycache__"))
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    bridge = ["bash", str(root / "scripts" / "claude_researchteam_bridge.sh")]
    res = subprocess.run([*bridge, "survey-frame", "tidebell", "out/final.csv", "--out", "out/frame.csv",
                          "--passages", "out/passages.csv"], capture_output=True, text=True, env=env)
    assert res.returncode == 0 and "frame: 2 cell(s)" in res.stdout, res.stdout + res.stderr
    res = subprocess.run([*bridge, "survey-frame", "--root", str(tmp_path), "tidebell"], capture_output=True,
                         text=True, env=env)
    assert res.returncode == 2 and "--root is not accepted" in res.stderr
    assert not list((root / "scripts" / "survey").glob("__pycache__"))


def test_usage_errors(tmp_path):
    root = _repo(tmp_path)
    assert run(survey_frame, "--root", str(root), "tidebell", "out/final.csv", "--out", "x.csv")[0] == 2
    assert run(survey_frame, "--root", str(root), "tidebell", "--out", "x.csv", "--passages", "y.csv")[0] == 2
