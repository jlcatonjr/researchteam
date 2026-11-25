"""Step C part 1: codes and adjudications (contract 4.2, lines 368-395) and survey-agreement (lines 400-401;
section 7, line 932)."""
import os
import shutil
import subprocess
import sys

import pytest

from survey_support import (
    ROOT, STUDY_REL, SURVEY, make_repo, run, survey_agreement, survey_codes as sc, survey_evidence as ev,
    survey_spec as sp, survey_validate, tree,
)

ROWS = f"{STUDY_REL}/rows"
CODES = f"{ROWS}/codes-slack_bell.csv"
ADJ = f"{ROWS}/adjudications-slack_bell.csv"
CH = b"unit_id,person_id,outcome,code,pass,coder,basis,reporter,evidence_ids,level,note\n"
AH = b"unit_id,outcome,code,coder,basis,reporter,evidence_ids,note\n"
A1 = b"p-001,warden-01,slack_bell,for,A,coder-a,own,,ev-001,,\n"
B1 = b"p-001,warden-01,slack_bell,for,B,coder-b,own,,ev-001,,\n"


def _codes(root, *lines, header=CH):
    """Write the codes file's bytes directly (a value may be one csv.writer cannot write on every Python)."""
    (root / CODES).write_bytes(header + b"".join(lines))


def _adj(root, *lines, header=AH):
    (root / ADJ).write_bytes(header + b"".join(lines))


def _rules(root):
    return {f.rule for f in ev.check_row_files(sp.load_study("tidebell", root)).findings}


def test_the_invented_codes_and_adjudications_pass(tmp_path):
    root = make_repo(tmp_path)
    assert _rules(root) == set()
    assert run(survey_validate, "--root", str(root), "tidebell")[0] == 0


# --------------------------------------------------------------------------- every codes check (4.2)
CODES_CASES = {
    "codes-pass": [A1.replace(b",A,", b",C,")],
    "codes-outcome": [A1.replace(b"slack_bell", b"bell_metal")],  # bell_metal's source is an evidence attribute
    "codes-code": [A1.replace(b",for,", b",perhaps,")],
    "codes-coder": [A1.replace(b"coder-a", b"")],
    "codes-evidence": [A1.replace(b"ev-001", b"")],
    "codes-basis": [A1.replace(b",own,", b",,")],
    "codes-reporter": [A1.replace(b",own,,", b",reported,,")],
    "codes-evidence-unknown": [A1.replace(b"ev-001", b"ev-999")],
    "codes-evidence-person": [A1.replace(b"ev-001", b"ev-003")],  # ev-003 belongs to warden-02
    "codes-duplicate": [A1, A1.replace(b"coder-a", b"coder-z")],
    "codes-unit": [A1.replace(b"p-001", b"p-404")],
    "codes-unit-person": [A1.replace(b"p-001,warden-01", b"p-001,warden-02")],
    "codes-value": [A1.replace(b"coder-a", "coder​a".encode())],
}


#: Every codes-row id the module emits (the shared ones are built as f"{prefix}-..." with prefix "codes").
CODES_IDS = {"codes-pass", "codes-outcome", "codes-code", "codes-coder", "codes-evidence", "codes-basis",
             "codes-reporter", "codes-evidence-unknown", "codes-evidence-person", "codes-duplicate", "codes-unit",
             "codes-unit-person", "codes-value", "codes-final-unpaired"}


def test_every_codes_check_has_a_case():
    assert set(CODES_CASES) | {"codes-final-unpaired"} == CODES_IDS


@pytest.mark.parametrize("rule", sorted(CODES_CASES))
def test_each_codes_check(tmp_path, rule):
    root = make_repo(tmp_path)
    _adj(root)
    _codes(root, *CODES_CASES[rule])
    assert rule in _rules(root)
    code, out, _ = run(survey_validate, "--root", str(root), "tidebell")
    assert code == 1 and f"[{rule}]" in out


def test_codes_columns(tmp_path):
    root = make_repo(tmp_path)
    _codes(root, header=b"unit_id,person_id,outcome,code,pass\n")
    assert "codes-columns" in _rules(root)


def test_the_missing_value_needs_no_evidence_or_basis(tmp_path):
    """4.2, line 378: "a code other than missing without evidence_ids or without a basis" is the error."""
    root = make_repo(tmp_path)
    _adj(root)
    _codes(root, b"p-001,warden-01,slack_bell,NE,A,coder-a,,,,,\n")
    assert _rules(root) == set()


def test_a_person_level_evidence_row_belongs_to_its_person(tmp_path):
    """4.2, lines 380-382: ev-002 is warden-01's own row (its unit_id is the person)."""
    root = make_repo(tmp_path)
    _adj(root)
    _codes(root, A1.replace(b"ev-001", b"ev-001;ev-002"))
    assert _rules(root) == set()


def test_a_codes_file_shared_by_two_outcomes_keeps_each_rows_outcome(tmp_path):
    """A row naming another coded outcome that has a file of its own is refused (a tightening)."""
    def second(s):
        o = dict(s["outcomes"][0])
        o.update(key="tide_horn", label="Horn at the turn")
        o["source"] = {"kind": "codes", "codes_file": "rows/codes-horn.csv",
                       "adjudications": "rows/adjudications-horn.csv"}
        s["outcomes"].append(o)
    root = make_repo(tmp_path, second)
    (root / ROWS / "codes-horn.csv").write_bytes(CH)
    _adj(root)
    _codes(root, A1.replace(b"slack_bell", b"tide_horn"))
    assert "codes-outcome" in _rules(root)


# --------------------------------------------------------------------------- final rows (4.2, lines 384-386)
def test_a_final_row_needs_both_passes(tmp_path):
    root = make_repo(tmp_path)
    _adj(root)
    _codes(root, A1, A1.replace(b",A,", b",final,"))
    assert "codes-final-unpaired" in _rules(root)


def test_a_final_row_from_a_missing_pass_adjudication_is_accepted(tmp_path):
    root = make_repo(tmp_path)
    note = b'"missing pass: B, the packet was lost"'
    _adj(root, b"p-001,slack_bell,for,adjudicator-c,own,,ev-001," + note + b"\n")
    _codes(root, A1, b"p-001,warden-01,slack_bell,for,final,adjudicator-c,own,,ev-001,," + note + b"\n")
    assert _rules(root) == set()


@pytest.mark.parametrize("final_note,adj_note", [
    (b'"missing pass: B, the packet was lost"', b'"missing pass: A, the packet was lost"'),  # names the wrong pass
    (b'"another note"', b'"missing pass: B, the packet was lost"'),  # the final row is not the adjudication's
])
def test_a_final_row_that_does_not_come_from_the_adjudication_is_refused(tmp_path, final_note, adj_note):
    root = make_repo(tmp_path)
    _adj(root, b"p-001,slack_bell,for,adjudicator-c,own,,ev-001," + adj_note + b"\n")
    _codes(root, A1, b"p-001,warden-01,slack_bell,for,final,adjudicator-c,own,,ev-001,," + final_note + b"\n")
    assert "codes-final-unpaired" in _rules(root)


# --------------------------------------------------------------------------- adjudications (4.2, lines 388-395)
ADJ_CASES = {
    "adjudication-columns": dict(header=b"unit_id,outcome,code\n", lines=[]),
    "adjudication-outcome": dict(lines=[b"p-002,bell_metal,for,adjudicator-c,own,,ev-003,why\n"]),
    "adjudication-note": dict(lines=[b"p-002,slack_bell,tolerates,adjudicator-c,reported,clerk,ev-003,\n"]),
    "adjudication-coder": dict(lines=[b"p-002,slack_bell,tolerates,,reported,clerk,ev-003,why\n"]),
    "adjudication-code": dict(lines=[b"p-002,slack_bell,perhaps,adjudicator-c,reported,clerk,ev-003,why\n"]),
    "adjudication-evidence-person": dict(lines=[b"p-002,slack_bell,tolerates,adjudicator-c,own,,ev-001,why\n"]),
    "adjudication-duplicate": dict(lines=[b"p-002,slack_bell,tolerates,adjudicator-c,reported,clerk,ev-003,why\n"] * 2),
    "adjudication-agreed": dict(lines=[b"p-001,slack_bell,against,adjudicator-c,own,,ev-001,why\n"]),
    "adjudication-missing-pass": dict(lines=[b"p-003,slack_bell,NA,adjudicator-c,own,,ev-005,no reason given\n"]),
    "adjudication-no-pass": dict(lines=[b"p-099,slack_bell,NA,adjudicator-c,own,,ev-005,why\n"]),
    "adjudication-unit": dict(lines=[b"p-404,slack_bell,NA,adjudicator-c,own,,ev-005,why\n"]),
}


@pytest.mark.parametrize("rule", sorted(ADJ_CASES))
def test_each_adjudication_check(tmp_path, rule):
    root = make_repo(tmp_path)
    case = ADJ_CASES[rule]
    _adj(root, *case["lines"], header=case.get("header", AH))
    assert rule in _rules(root)


@pytest.mark.parametrize("note", [b'"missing pass: B, "', b'"missing pass: B,the packet"', b"missing pass B the packet"])
def test_a_missing_pass_note_must_name_the_pass_and_a_reason(tmp_path, note):
    root = make_repo(tmp_path)
    _adj(root, b"p-002,slack_bell,tolerates,adjudicator-c,reported,clerk,ev-003,why\n",
         b"p-003,slack_bell,NA,adjudicator-c,own,,ev-005," + note + b"\n")
    assert "adjudication-missing-pass" in _rules(root)


def test_a_missing_pass_note_on_a_unit_with_both_passes_is_refused(tmp_path):
    root = make_repo(tmp_path)
    _adj(root, b'p-002,slack_bell,tolerates,adjudicator-c,reported,clerk,ev-003,"missing pass: A, but it is there"\n')
    assert "adjudication-missing-pass" in _rules(root)


def test_without_adjudications_the_file_may_be_absent(tmp_path):
    root = make_repo(tmp_path)
    (root / ADJ).unlink()
    assert _rules(root) == set()


# --------------------------------------------------------------------------- agreement (4.2, lines 400-401)
def test_agreement_on_the_invented_study(tmp_path):
    """p-001: A for, B for (agree); p-002: A against, B tolerates (disagree); p-003: A only. So 1 of 2, and one unit
    with one pass."""
    root = make_repo(tmp_path)
    before = tree(root)
    code, out, _ = run(survey_agreement, "--root", str(root), "tidebell")
    assert code == 0 and tree(root) == before
    assert "slack_bell: raw agreement 1 of 2 unit(s) with both passes; 1 unit(s) with one pass only" in out
    assert "not computed" in out


def test_agreement_by_hand():
    """Five units. u1 for/for (agree), u2 for/against (no), u3 NA/NA (agree: every code counts as itself),
    u4 NE/NE (agree), u5 A only (one pass). Units with both passes: u1..u4 = 4; agreeing: u1, u3, u4 = 3.
    Raw agreement 3 of 4; one unit with one pass."""
    c = sc.Codes()
    rows = [("u1", "A", "for"), ("u1", "B", "for"), ("u2", "A", "for"), ("u2", "B", "against"),
            ("u3", "A", "NA"), ("u3", "B", "NA"), ("u4", "A", "NE"), ("u4", "B", "NE"), ("u5", "A", "for"),
            ("u1", "final", "for")]
    c.rows["x"] = [("w", {"unit_id": u, "pass": p, "code": k}) for u, p, k in rows]
    (a,) = sc.agreement(c)
    assert (a.outcome, a.units, a.agreeing, a.missing_pass) == ("x", 4, 3, 1)


def test_agreement_refuses_on_a_code_error_and_writes_nothing(tmp_path):
    root = make_repo(tmp_path)
    _codes(root, A1.replace(b",for,", b",perhaps,"))
    before = tree(root)
    code, out, _ = run(survey_agreement, "--root", str(root), "tidebell")
    assert code == 1 and "REFUSED" in out and "[codes-code]" in out and tree(root) == before


def test_agreement_refuses_without_a_coded_outcome(tmp_path):
    def author(s):
        s["unit"] = {"kind": "author"}
        s["outcomes"][0]["source"] = {"kind": "evidence-attribute", "attribute": "duty"}
        s["frame_rules"]["exclude"] = []
    root = make_repo(tmp_path, author)
    code, out, _ = run(survey_agreement, "--root", str(root), "tidebell")
    assert code == 1 and "no outcome whose source is codes" in out


def test_agreement_is_deterministic(tmp_path):
    root = make_repo(tmp_path)
    assert run(survey_agreement, "--root", str(root), "tidebell") == run(survey_agreement, "--root", str(root),
                                                                           "tidebell")


def test_the_bridge_runs_survey_agreement_and_refuses_root(tmp_path):
    root = make_repo(tmp_path)
    (root / "scripts").mkdir()
    shutil.copy(ROOT / "scripts" / "claude_researchteam_bridge.sh", root / "scripts")
    shutil.copytree(SURVEY, root / "scripts" / "survey", ignore=shutil.ignore_patterns("__pycache__"))
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    bridge = ["bash", str(root / "scripts" / "claude_researchteam_bridge.sh")]
    res = subprocess.run([*bridge, "survey-agreement", "tidebell"], capture_output=True, text=True, env=env)
    assert res.returncode == 0 and "raw agreement 1 of 2" in res.stdout
    res = subprocess.run([*bridge, "survey-agreement", "--root", str(tmp_path), "tidebell"], capture_output=True,
                         text=True, env=env)
    assert res.returncode == 2 and "--root is not accepted" in res.stderr
    assert not list((root / "scripts" / "survey").glob("__pycache__"))
