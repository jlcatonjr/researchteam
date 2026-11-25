"""Step B part 2b: the batch merge, survey-rows (contract 4.1 lines 322-326, 4.4 lines 515-523, section 7 line 929),
and the first exceptions draft (4.1 lines 364-365)."""
import os
import shutil
import subprocess
import sys

import pytest

from survey_support import (
    FIXTURES, ROOT, STUDY_REL, SURVEY, edit_spec, make_repo, run, survey_provenance as prov, survey_registry, tree,
)

_saved = sys.dont_write_bytecode
sys.dont_write_bytecode = True
import survey_rows  # noqa: E402  (on sys.path through survey_support)
sys.dont_write_bytecode = _saved

ROWS = f"{STUDY_REL}/rows"
EVIDENCE = f"{ROWS}/evidence.csv"
RECORD = f"{ROWS}/registry.csv.provenance.json"
HEADER = (b"id,person_id,attribute_kind,value,tier,source_id,citation,locator,quote,url,access,via,audit,basis,"
          b"reporter,unit_id,note,downgraded_from\n")
GOOD = b"ev-201,warden-01,harbour,North Quay,quoted,src-9,Invented letter,letter-09#p1,from the north quay,,,,,own,,p-001,,\n"


def _repo(tmp_path, mutate=None, *, build=True):
    root = make_repo(tmp_path, mutate)
    shutil.copy(FIXTURES / "batches" / "batch-01.csv", root / STUDY_REL / "batch-01.csv")
    if build:
        assert run(survey_registry, "--root", str(root), "tidebell")[0] == 0
    return root


def _batch(root, body: bytes, name="batch.csv", header=HEADER):
    (root / STUDY_REL / name).write_bytes(header + body)
    return name


def _merge(root, batch="batch-01.csv"):
    return run(survey_rows, "--root", str(root), "tidebell", batch)


def _refused(root, batch="batch-01.csv", needle=""):
    before = tree(root)
    code, out, _ = _merge(root, batch)
    assert code == 1 and "REFUSED" in out and needle in out, out
    assert tree(root) == before
    return out


# --------------------------------------------------------------------------- the merge
def test_a_batch_is_appended_and_the_registrys_record_renewed(tmp_path):
    root = _repo(tmp_path)
    before = (root / EVIDENCE).read_bytes()
    code, out, _ = _merge(root)
    assert code == 0 and "merged: 2 row(s)" in out and f"renewed: {RECORD}" in out
    after = (root / EVIDENCE).read_bytes()
    batch_rows = (FIXTURES / "batches" / "batch-01.csv").read_bytes().split(b"\n", 1)[1]
    assert after == before + batch_rows  # existing rows untouched, the batch appended in batch order
    assert prov.check_current(root, RECORD, expect_tool="survey-registry").built
    code, out, _ = run(survey_registry, "--root", str(root), "tidebell")
    assert out.startswith("unchanged:")  # the renewed record is what a fresh build writes


def test_the_merged_file_is_byte_deterministic(tmp_path):
    a, b = _repo(tmp_path / "a"), _repo(tmp_path / "b")
    _merge(a), _merge(b)
    assert (a / EVIDENCE).read_bytes() == (b / EVIDENCE).read_bytes()
    assert (a / RECORD).read_bytes() == (b / RECORD).read_bytes()


def test_a_batch_keeps_the_files_crlf_line_endings(tmp_path):
    root = make_repo(tmp_path)
    path = root / EVIDENCE
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    assert run(survey_registry, "--root", str(root), "tidebell")[0] == 0
    name = _batch(root, GOOD)
    assert _merge(root, name)[0] == 0
    assert path.read_bytes().endswith(GOOD.replace(b"\n", b"\r\n")) and b"\r\n\n" not in path.read_bytes()


def test_a_file_without_a_final_line_feed_gets_one(tmp_path):
    root = make_repo(tmp_path)
    path = root / EVIDENCE
    path.write_bytes(path.read_bytes().rstrip(b"\n"))
    assert run(survey_registry, "--root", str(root), "tidebell")[0] == 0
    name = _batch(root, GOOD)
    assert _merge(root, name)[0] == 0
    assert path.read_bytes().endswith(b",,\n" + GOOD)


def test_a_first_batch_creates_the_evidence_file_in_a_draft(tmp_path):
    root = make_repo(tmp_path, lambda s: s.update(status="draft"))
    (root / EVIDENCE).unlink()
    assert run(survey_registry, "--root", str(root), "tidebell")[0] == 0
    name = _batch(root, GOOD)
    code, out, _ = _merge(root, name)
    assert code == 0 and (root / EVIDENCE).read_bytes() == HEADER + GOOD


# --------------------------------------------------------------------------- refusals before anything is written
def test_the_registry_must_be_built(tmp_path):
    root = _repo(tmp_path, build=False)
    _refused(root, needle="the registry is not built")


def test_a_stale_registry_refuses(tmp_path):
    root = _repo(tmp_path)
    (root / ROWS / "overrides.csv").write_bytes(b"alias_id,target_id,decision,decided_by,reason\n"
                                                b"warden-02,warden-01,distinct,Ines Marlow (invented),two people\n")
    _refused(root, needle="the registry is not built")


def test_a_hand_edited_registry_is_found(tmp_path):
    """A-8: the record cannot hash the registry, but a build over the merged file gives other rows."""
    root = _repo(tmp_path)
    reg = root / ROWS / "registry.csv"
    reg.write_bytes(reg.read_bytes().replace(b"warden-02,warden-02,,", b"warden-02,warden-02,,warden-99"))
    assert prov.check_current(root, RECORD).built  # the record alone cannot see it
    _refused(root, needle="would change the registry's rows")


def test_a_batch_with_a_new_person_refuses(tmp_path):
    root = _repo(tmp_path)
    name = _batch(root, GOOD.replace(b"warden-01", b"warden-77").replace(b"p-001", b"warden-77"))
    out = _refused(root, name)
    assert "[person-unknown]" in out


@pytest.mark.parametrize("body,rule", [
    (GOOD.replace(b"quoted", b"rumoured"), "tier-unknown"),
    (GOOD.replace(b"ev-201", b"ev-001"), "id-duplicate"),  # a duplicate between the batch and the file
    (GOOD + GOOD, "id-duplicate"),  # a duplicate within the batch
    (GOOD.replace(b",own,", b",reported,"), "reported-reporter"),
    (GOOD.replace(b"p-001", b"p-002"), "unit-person"),
])
def test_a_batch_row_that_fails_a_check_refuses(tmp_path, body, rule):
    root = _repo(tmp_path)
    name = _batch(root, body)
    out = _refused(root, name, needle="nothing was appended")
    assert f"[{rule}]" in out and "batch row" in out


def test_a_breach_already_in_the_file_refuses(tmp_path):
    """The batch is checked "together with the file it joins" (4.1, line 323)."""
    root = _repo(tmp_path)
    path = root / EVIDENCE
    path.write_bytes(path.read_bytes().replace(b"ev-005,guild-01,duty,lamp and bell,quoted",
                                               b"ev-005,guild-01,duty,lamp and bell,rumoured"))
    assert run(survey_registry, "--root", str(root), "tidebell")[0] == 0
    out = _refused(root)
    assert f"[tier-unknown] {EVIDENCE}:6" in out


@pytest.mark.parametrize("data", [b"", b"id,person_id\nx,y\n", HEADER, HEADER + b"ev-1,a\x00b" + b",x" * 16 + b"\n"],
                         ids=["no-header", "other-columns", "empty", "nul"])
def test_a_malformed_or_empty_batch_refuses(tmp_path, data):
    root = _repo(tmp_path)
    (root / STUDY_REL / "batch.csv").write_bytes(data)
    _refused(root, "batch.csv")


@pytest.mark.parametrize("arg", ["repo:CLAUDE.md", "../outside.csv", "/abs/batch.csv", "rows/evidence.csv",
                                 "repo:Projects/tidebell/rows/evidence.csv", "absent.csv", "rows"])
def test_where_a_batch_may_not_come_from(tmp_path, arg):
    root = _repo(tmp_path)
    (root / "CLAUDE.md").write_bytes(HEADER + GOOD)
    _refused(root, arg)


def test_a_batch_linked_outside_the_repository_refuses(tmp_path):
    root = _repo(tmp_path)
    (tmp_path / "outside.csv").write_bytes(HEADER + GOOD)
    os.symlink(tmp_path / "outside.csv", root / STUDY_REL / "batch-link.csv")
    _refused(root, "batch-link.csv")


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="os.mkfifo is not available here")
def test_a_batch_that_is_a_fifo_is_not_opened(tmp_path):
    root = _repo(tmp_path)
    os.mkfifo(root / STUDY_REL / "batch.fifo")
    _refused(root, "batch.fifo")


def test_a_merge_into_a_plugin_format_refuses(tmp_path):
    root = _repo(tmp_path)
    edit_spec(root, lambda s: s["evidence"].update(format="plugin", reader={"file": "rules/forbidden.txt",
                                                                           "attr": "R", "version": "1"}))
    _refused(root, needle="plugin format")


def test_a_malformed_specification_refuses(tmp_path):
    root = _repo(tmp_path)
    edit_spec(root, lambda s: s.update(colour="blue"))
    _refused(root, needle="malformed")


# --------------------------------------------------------------------------- legacy studies
def _legacy(tmp_path, lines=b""):
    def mutate(s):
        s["status"] = "legacy"
        s["evidence"]["legacy_exceptions"] = "rules/exceptions.csv"
        s["signoffs"]["gates"]["S0"]["covers"].append("rules/exceptions.csv")
    root = make_repo(tmp_path, mutate)
    (root / STUDY_REL / "rules" / "exceptions.csv").write_bytes(b"id,rule\n" + lines)
    return root


def test_a_legacy_exception_never_covers_a_batch_row(tmp_path):
    root = _legacy(tmp_path, b"ev-201,counted-basis\n")
    assert run(survey_registry, "--root", str(root), "tidebell")[0] == 0
    name = _batch(root, GOOD.replace(b",own,", b",,"))
    out = _refused(root, name)
    assert "[counted-basis]" in out and "batch row 1" in out


def test_a_batch_row_gets_no_legacy_leniency_on_receipts(tmp_path):
    """5.4, lines 774-775: rows that predate receipts; a row added now does not."""
    root = _legacy(tmp_path)
    assert run(survey_registry, "--root", str(root), "tidebell")[0] == 0
    name = _batch(root, GOOD.replace(b"letter-09#p1", b"https://archive.invalid/x").replace(
        b",,,,,own", b",https://archive.invalid/x,,,,own"))
    out = _refused(root, name)
    assert "[receipt-missing]" in out


# --------------------------------------------------------------------------- what may be written
def test_an_evidence_file_outside_the_study_folder_is_not_written(tmp_path):
    root = make_repo(tmp_path)
    (root / "shared").mkdir()
    shutil.copy(root / EVIDENCE, root / "shared" / "evidence.csv")
    edit_spec(root, lambda s: s["evidence"].update(file="repo:shared/evidence.csv"))
    assert run(survey_registry, "--root", str(root), "tidebell")[0] == 0
    shutil.copy(FIXTURES / "batches" / "batch-01.csv", root / STUDY_REL / "batch-01.csv")
    _refused(root, needle="not inside the study's folder")


def test_an_evidence_file_a_gate_covers_is_not_a_target(tmp_path):
    """No other declared file may be the target: with a gate's covers naming the evidence file, the evidence file
    is refused even with its own pointer (and the registry beside it too: its folder holds a covered file)."""
    from survey_support import survey_spec as sp
    root = _repo(tmp_path)
    edit_spec(root, lambda s: s["signoffs"]["gates"]["S5"]["covers"].append("rows/evidence.csv"))
    study = sp.load_study("tidebell", root)
    with pytest.raises(prov.WriteRefused, match="which the specification names"):
        prov.check_output_target(study, EVIDENCE, own_pointer="/evidence/file")
    _refused(root)


@pytest.mark.parametrize("which", [0, 1])
def test_a_write_refused_at_either_last_check_changes_nothing(tmp_path, monkeypatch, which):
    root = _repo(tmp_path)
    calls = []
    real = prov.check_writable

    def refuse_late(r, rel):
        calls.append(rel)
        if len(calls) == 3 + which:  # the first two calls are the early checks
            raise prov.WriteRefused(f"{rel} became unsafe")
        real(r, rel)
    monkeypatch.setattr(prov, "check_writable", refuse_late)
    _refused(root, needle="became unsafe")


def test_an_interruption_between_the_writes_leaves_the_registry_not_built(tmp_path, monkeypatch):
    """4.4, lines 521-523: the evidence file first, the record last; never wrongly current."""
    root = _repo(tmp_path)
    calls = []
    real = prov.replace

    def second_fails(*args):
        calls.append(args[1])
        if len(calls) == 2:
            raise KeyboardInterrupt("interrupted before the record")
        real(*args)
    monkeypatch.setattr(prov, "replace", second_fails)
    with pytest.raises(KeyboardInterrupt):
        _merge(root)
    monkeypatch.undo()
    assert b"ev-102" in (root / EVIDENCE).read_bytes()  # the evidence file landed
    cur = prov.check_current(root, RECORD)
    assert not cur.built and any("evidence.csv" in r for r in cur.reasons)
    assert run(survey_registry, "--root", str(root), "tidebell")[0] == 0  # a build makes it current again
    assert prov.check_current(root, RECORD).built


def test_an_os_error_while_writing_is_a_refusal(tmp_path, monkeypatch):
    root = _repo(tmp_path)

    def broken(*_args):
        raise OSError(28, "No space left on device")
    monkeypatch.setattr(prov, "replace", broken)
    _refused(root, needle="No space left on device")


# --------------------------------------------------------------------------- a first exceptions file
def _legacy_without_exceptions(tmp_path):
    return make_repo(tmp_path, lambda s: s.update(status="legacy"))


def test_a_first_exceptions_file_is_printed_and_nothing_is_written(tmp_path):
    root = _legacy_without_exceptions(tmp_path)
    path = root / EVIDENCE
    path.write_bytes(path.read_bytes().replace(b"ev-005,guild-01,duty,lamp and bell,quoted",
                                               b"ev-005,guild-01,duty,lamp and bell,rumoured"))
    before = tree(root)
    code, out, err = run(survey_rows, "--root", str(root), "tidebell", "--draft-exceptions")
    assert code == 0 and out == "id,rule\nev-005,tier-unknown\n" and "nothing was written" in err
    assert tree(root) == before


def test_a_first_exceptions_file_never_adds_to_an_existing_one(tmp_path):
    root = _legacy(tmp_path)
    code, out, _ = run(survey_rows, "--root", str(root), "tidebell", "--draft-exceptions")
    assert code == 1 and "already declares the exceptions file" in out and "never adds to an existing one" in out


def test_a_first_exceptions_file_is_for_a_legacy_study(tmp_path):
    root = make_repo(tmp_path)
    assert run(survey_rows, "--root", str(root), "tidebell", "--draft-exceptions")[0] == 1


def test_no_first_exceptions_file_while_an_unlistable_breach_stands(tmp_path):
    root = _legacy_without_exceptions(tmp_path)
    path = root / EVIDENCE
    path.write_bytes(path.read_bytes() + b"ev-001" + GOOD[6:])
    code, out, _ = run(survey_rows, "--root", str(root), "tidebell", "--draft-exceptions")
    assert code == 1 and "[id-duplicate]" in out and "cannot be listed" in out


# --------------------------------------------------------------------------- the command line and the bridge
def test_usage_errors(tmp_path):
    root = _repo(tmp_path)
    assert run(survey_rows, "--root", str(root), "tidebell")[0] == 2
    assert run(survey_rows, "--root", str(root), "tidebell", "a.csv", "b.csv")[0] == 2


def test_the_bridge_runs_survey_rows_and_refuses_root(tmp_path):
    root = _repo(tmp_path)
    (root / "scripts").mkdir()
    shutil.copy(ROOT / "scripts" / "claude_researchteam_bridge.sh", root / "scripts")
    shutil.copytree(SURVEY, root / "scripts" / "survey", ignore=shutil.ignore_patterns("__pycache__"))
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    bridge = ["bash", str(root / "scripts" / "claude_researchteam_bridge.sh")]
    res = subprocess.run([*bridge, "survey-rows", "tidebell", "batch-01.csv"], capture_output=True, text=True, env=env)
    assert res.returncode == 0 and "merged: 2 row(s)" in res.stdout
    res = subprocess.run([*bridge, "survey-rows", "--root", str(tmp_path), "tidebell", "batch-01.csv"],
                         capture_output=True, text=True, env=env)
    assert res.returncode == 2 and "--root is not accepted" in res.stderr
    assert not list((root / "scripts" / "survey").glob("__pycache__"))


# --------------------------------------------------------------------------- review of part 2b
@pytest.mark.parametrize("tail", [b'ev-009,warden-01,harbour,"unclosed\n', b'ev-009,warden-01,harbour,"unclosed'])
def test_an_evidence_file_ending_in_an_unclosed_quote_is_refused(tmp_path, tail):
    """S1: a strict parse rejects it, and nothing is written."""
    root = _repo(tmp_path)
    path = root / EVIDENCE
    path.write_bytes(path.read_bytes() + tail)
    out = _refused(root)
    assert "not strict CSV" in out or "[columns]" in out


def test_a_batch_crafted_to_close_an_open_quote_is_refused(tmp_path, monkeypatch):
    """S1: even past the strict parse, the read-back compares cell for cell, so the file's last row cannot change."""
    from survey_support import survey_tables as tb
    root = _repo(tmp_path)
    path = root / EVIDENCE
    path.write_bytes(path.read_bytes() + b'ev-009,warden-01,harbour,"open')
    real = tb.rows_from_bytes
    calls = []

    def lenient_first_reads(data, where, columns, rule):  # let the file and the batch through as a lenient reader would
        calls.append(where)
        import csv, io
        if len(calls) <= 2:
            rows = tb.Rows()
            for n, rec in enumerate(csv.reader(io.StringIO(data.decode(), newline="")), start=1):
                if n == 1:
                    rows.header = rec
                elif len(rec) == len(columns):
                    rows.rows.append((n, dict(zip(columns, rec))))
            return rows, "x"
        return real(data, where, columns, rule)
    monkeypatch.setattr(survey_rows, "rows_from_bytes", lenient_first_reads)
    name = _batch(root, b'close",x,x,x,x,x,x,x,x,x,x,x,x,x,x\n' + GOOD)
    out = _refused(root, name)
    assert "does not read back" in out


def test_a_normal_merge_is_still_the_file_followed_by_the_batch(tmp_path):
    root = _repo(tmp_path)
    before = (root / EVIDENCE).read_bytes()
    name = _batch(root, GOOD)
    assert _merge(root, name)[0] == 0
    assert (root / EVIDENCE).read_bytes() == before + GOOD


def test_a_file_changed_between_the_checks_and_the_write_is_refused(tmp_path, monkeypatch):
    """S2: two merges at once; the second must not silently drop the first one's rows."""
    root = _repo(tmp_path)
    real = prov.check_writable
    calls = []

    def another_merge_lands(r, rel):
        calls.append(rel)
        if len(calls) == 3:  # the first late check: another run has just appended a row
            path = root / EVIDENCE
            path.write_bytes(path.read_bytes() + GOOD)
        real(r, rel)
    monkeypatch.setattr(prov, "check_writable", another_merge_lands)
    before_record = (root / RECORD).read_bytes()
    code, out, _ = _merge(root)
    assert code == 1 and "changed while this run was being prepared" in out
    assert (root / EVIDENCE).read_bytes().endswith(GOOD) and (root / RECORD).read_bytes() == before_record


@pytest.mark.parametrize("which", ["registry", "record"])
def test_a_registry_or_record_changed_before_the_write_is_refused(tmp_path, monkeypatch, which):
    root = _repo(tmp_path)
    target = root / (ROWS + "/registry.csv" if which == "registry" else RECORD)
    real = prov.check_writable
    calls = []

    def touch(r, rel):
        calls.append(rel)
        if len(calls) == 3:
            target.write_bytes(target.read_bytes() + b"\n")
        real(r, rel)
    monkeypatch.setattr(prov, "check_writable", touch)
    before = (root / EVIDENCE).read_bytes()
    code, out, _ = _merge(root)
    assert code == 1 and "changed while this run was being prepared" in out
    assert (root / EVIDENCE).read_bytes() == before


def test_a_batch_reached_through_a_link_inside_the_study_is_refused(tmp_path):
    """S3: a batch is read without following a link on its path."""
    root = _repo(tmp_path)
    (root / STUDY_REL / "incoming").mkdir()
    shutil.copy(root / STUDY_REL / "batch-01.csv", root / STUDY_REL / "incoming" / "b.csv")
    os.symlink("incoming", root / STUDY_REL / "linked")
    out = _refused(root, "linked/b.csv")
    assert "symbolic link" in out
    os.symlink("batch-01.csv", root / STUDY_REL / "final-link.csv")
    out = _refused(root, "final-link.csv")
    assert "symbolic link" in out


@pytest.mark.parametrize("old,new", [
    (b"ev-201,", b'"ev\n201",'),                  # an LF in id
    (b",warden-01,", b',"warden\t01",'),           # a TAB in person_id
    (b",p-001,,", b',"p-001\r\n",,'),              # a CR LF in unit_id
    (b",src-9,", b',"src\n9",'),                   # an LF in source_id
    (b"North Quay", b'"North\rQuay"'),             # a lone CR, in a text column too
    (b"North Quay", "North\u200bQuay".encode()),   # a zero-width character (Cf)
    (b"North Quay", b"North\x07Quay"),             # a bell (Cc)
    (b"North Quay", "North\u2028Quay".encode()),   # a line separator (Zl)
])
def test_a_batch_cell_with_a_character_it_may_not_hold_is_refused(tmp_path, old, new):
    """T1/S4: identifier columns hold no control or white-space control character; any column, no lone CR and no
    Cc (but TAB, LF, CR LF in text), Cf, Zl or Zp."""
    root = _repo(tmp_path)
    name = _batch(root, GOOD.replace(old, new))
    out = _refused(root, name)
    assert "[batch-control]" in out


@pytest.mark.parametrize("old,new", [
    (b"from the north quay", b'"from the north quay,\nas the logbook has it"'),  # a two-line quotation
    (b"letter-09#p1,from", b"letter-09#p1,from"),  # unchanged quote; the note gets a tab below
])
def test_a_batch_with_a_line_break_or_tab_in_a_text_cell_merges(tmp_path, old, new):
    """T1: 4.1 line 323 judges a batch by the file's rules, which accept such cells; the merged file is the old bytes
    followed by the batch rows as the writer quotes them."""
    import csv
    import io
    root = _repo(tmp_path)
    body = GOOD.replace(old, new)
    if old == new:
        body = body.replace(b",,\n", b',"an invented\tnote",\n')
    name = _batch(root, body)
    before = (root / EVIDENCE).read_bytes()
    code, out, _ = _merge(root, name)
    assert code == 0, out
    row = next(csv.reader(io.StringIO(body.decode("utf-8"), newline="")))
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerow(row)
    assert (root / EVIDENCE).read_bytes() == before + buf.getvalue().encode("utf-8")


def test_a_private_use_character_is_accepted(tmp_path):
    """T1: private use (Co) is used by scholarly transcriptions; only Cc, Cf, Zl and Zp are refused."""
    root = _repo(tmp_path)
    name = _batch(root, GOOD.replace(b"from the north quay", "from the north \ue000quay".encode()))
    assert _merge(root, name)[0] == 0


def test_the_registry_and_the_batch_share_one_set_of_unsafe_characters():
    from survey_support import survey_core as core, survey_identity as ident
    rows = [{"person_id": "a\ue000", "display_name": "x", "identity_id": "", "merged_from": ""}]
    assert ident.unsafe_values(rows, "r") == [] and core.UNSAFE_CATEGORIES == ("Cc", "Cf", "Zl", "Zp")


def test_an_existing_row_with_a_line_break_is_not_rejudged(tmp_path):
    """S4: only batch rows are judged."""
    root = make_repo(tmp_path)
    path = root / EVIDENCE
    path.write_bytes(path.read_bytes().replace(b"searched the invented register; nothing on the metal",
                                               b'"searched the invented register;\nnothing on the metal"'))
    assert run(survey_registry, "--root", str(root), "tidebell")[0] == 0
    name = _batch(root, GOOD)
    assert _merge(root, name)[0] == 0


def test_a_registry_with_the_same_rows_but_other_bytes_is_refused(tmp_path):
    """T1: a hand edit that keeps the rows (line endings, quoting) would be rewritten by the next build."""
    root = _repo(tmp_path)
    reg = root / ROWS / "registry.csv"
    reg.write_bytes(reg.read_bytes().replace(b"\n", b"\r\n"))
    out = _refused(root)
    assert "its bytes are not" in out and "survey-registry" in out


def test_the_draft_study_refuses_a_merge_while_the_registry_is_not_built(tmp_path):
    """T2: decided by 4.4, line 517 ("It refuses unless the registry is built"), in a draft too."""
    root = _repo(tmp_path, lambda s: s.update(status="draft"), build=False)
    _refused(root, needle="the registry is not built")


def test_an_lf_file_with_a_crlf_inside_a_quoted_cell_stays_lf(tmp_path):
    """T3: the line ending is read from the header line only."""
    root = make_repo(tmp_path)
    path = root / EVIDENCE
    path.write_bytes(path.read_bytes().replace(b"searched the invented register; nothing on the metal",
                                               b'"searched the invented register;\r\nnothing on the metal"'))
    assert run(survey_registry, "--root", str(root), "tidebell")[0] == 0
    name = _batch(root, GOOD)
    assert _merge(root, name)[0] == 0
    assert path.read_bytes().endswith(b",,\n" + GOOD)


def test_a_successful_merge_reports_excused_breaches_and_reported_rows(tmp_path):
    """T5: 4.1, lines 355-356, and 5.4, line 774."""
    root = _legacy(tmp_path, b"ev-003,counted-basis\n")
    path = root / EVIDENCE
    path.write_bytes(path.read_bytes().replace(b",reported,harbour clerk,p-002", b",,,p-002"))
    assert run(survey_registry, "--root", str(root), "tidebell")[0] == 0
    name = _batch(root, GOOD)
    code, out, _ = _merge(root, name)
    assert code == 0 and "read with 1 legacy exception(s); breaches excused by rule: counted-basis 1" in out


def test_no_exceptions_draft_without_a_registry(tmp_path):
    """T6: a missing registry is itself an error (4.1, line 315); person-unknown cannot be judged without it."""
    root = _legacy_without_exceptions(tmp_path)
    (root / ROWS / "registry.csv").unlink()
    code, out, _ = run(survey_rows, "--root", str(root), "tidebell", "--draft-exceptions")
    assert code == 1 and "[registry-missing]" in out


def test_no_exceptions_draft_for_an_id_with_a_control_character(tmp_path):
    """T7: the printed draft could not name such an id exactly, so it is refused, naming the row."""
    root = _legacy_without_exceptions(tmp_path)
    path = root / EVIDENCE
    path.write_bytes(path.read_bytes().replace(b"ev-005,guild-01,duty,lamp and bell,quoted",
                                               b"ev\x1b-005,guild-01,duty,lamp and bell,rumoured"))  # with a breach
    code, out, _ = run(survey_rows, "--root", str(root), "tidebell", "--draft-exceptions")
    assert code == 1 and "[exceptions-draft]" in out and f"{EVIDENCE}:6" in out and "\x1b" not in out


def test_an_id_with_a_control_character_in_a_row_without_a_breach_does_not_stop_the_draft(tmp_path):
    """T4: only a row with a breach to list must be nameable."""
    root = _legacy_without_exceptions(tmp_path)
    path = root / EVIDENCE
    path.write_bytes(path.read_bytes().replace(b"ev-005,", b"ev\x1b-005,").replace(
        b"ev-001,warden-01,work_date,1742,quoted", b"ev-001,warden-01,work_date,1742,rumoured"))
    code, out, _ = run(survey_rows, "--root", str(root), "tidebell", "--draft-exceptions")
    assert code == 0 and out == "id,rule\nev-001,tier-unknown\n"
