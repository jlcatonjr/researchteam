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
