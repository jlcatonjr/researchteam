"""Step C part 2: survey-finalize and survey-rollup (contract 4.2, lines 397-422; section 7, lines 933-934; the
operator's decisions of 2026-11-25, D2 to D6). Expected outputs are worked out by hand from the invented study."""
import json
import os
import shutil
import subprocess
import sys

import pytest

from survey_support import (
    ROOT, STUDY_REL, SURVEY, make_repo, run, survey_provenance as prov, tree,
)

_saved = sys.dont_write_bytecode
sys.dont_write_bytecode = True
import survey_final as sf  # noqa: E402
import survey_finalize  # noqa: E402
import survey_rollup  # noqa: E402
sys.dont_write_bytecode = _saved

ROWS = f"{STUDY_REL}/rows"
OUT = f"{STUDY_REL}/out"
CODES = f"{ROWS}/codes-slack_bell.csv"
ADJ = f"{ROWS}/adjudications-slack_bell.csv"

#: The invented study's final codes, by hand (D3): p-001's passes agree on "for" but cite ev-001 and ev-001;ev-002,
#: so pass A's row with coder and note "agreed; evidence differed"; p-002's passes disagree (against / tolerates),
#: so the adjudication's row; p-003 has pass A only, so the missing-pass adjudication's row.
FINAL = (b"unit_id,person_id,outcome,code,pass,coder,basis,reporter,evidence_ids,level,note\n"
         b"p-001,warden-01,slack_bell,for,final,agreed,own,,ev-001,,agreed; evidence differed\n"
         b"p-002,warden-02,slack_bell,tolerates,final,adjudicator-c (invented),reported,harbour clerk,ev-003,,"
         b"the clerk's account is hedged\n"
         b"p-003,guild-01,slack_bell,NA,final,adjudicator-c (invented),own,,ev-005,,"
         b"\"missing pass: B, the second coder's packet was never returned\"\n")
#: The rollup, by hand (4.2, lines 403-421): p-003 is "doubtful", not a counted status, so guild-01 is left out;
#: warden-01 (p-001, logbook) gets "for"; warden-02 (p-002, letter) gets "tolerates"; rollup_by genre and
#: rollup_types genre.
ROLLUP = (b"person_id,genre,author_kind,slack_bell,slack_bell__types\n"
          b"warden-01,logbook,person,for,logbook\n"
          b"warden-02,letter,person,tolerates,letter\n")


def _repo(tmp_path, mutate=None):
    root = make_repo(tmp_path, mutate)
    (root / OUT).mkdir()
    return root


def _finalize(root, out="out/final.csv"):
    return run(survey_finalize, "--root", str(root), "tidebell", "--out", out)


def _rollup(root, final="out/final.csv", out="out/rollup.csv"):
    return run(survey_rollup, "--root", str(root), "tidebell", final, "--out", out)


def _refused(fn, root, *args, needle=""):
    before = tree(root)
    code, out, _ = fn(root, *args)
    assert code == 1 and "REFUSED" in out and needle in out, out
    assert tree(root) == before
    return out


# --------------------------------------------------------------------------- finalising
def test_the_invented_studys_final_codes(tmp_path):
    root = _repo(tmp_path)
    code, out, _ = _finalize(root)
    assert code == 0 and (root / OUT / "final.csv").read_bytes() == FINAL
    assert (root / ROWS / "codes-slack_bell.csv").read_bytes().count(b",final,") == 0  # the passes file is only read


def test_the_final_codes_record(tmp_path):
    """D6: the inputs read with their hashes, gate S5 only, the legacy exceptions; 4.6's shape."""
    import hashlib
    root = _repo(tmp_path)
    _finalize(root)
    doc = json.loads((root / OUT / "final.csv.provenance.json").read_bytes())
    assert prov.check_record_shape(doc, "r") == [] and doc["tool"] == "survey-finalize"
    assert list(doc["gates"]) == ["S5"] and doc["gates"]["S5"]["state"] in ("UNCLEARED", "UNAVAILABLE", "CLEARED")
    assert doc["gates"]["S5"]["mode"] == "prospective" and doc["legacy_exceptions"] == 0
    paths = [e["path"] for e in doc["inputs"]]
    assert paths == [f"{STUDY_REL}/study.json", CODES, ADJ, f"{ROWS}/evidence.csv", f"{ROWS}/attribution.csv"]
    for e in doc["inputs"]:
        assert e["sha256"] == hashlib.sha256((root / e["path"]).read_bytes()).hexdigest()
    assert prov.check_current(root, f"{OUT}/final.csv.provenance.json").built


def test_an_agreed_unit_with_the_same_evidence_says_agreed(tmp_path):
    root = _repo(tmp_path)
    path = root / CODES
    path.write_bytes(path.read_bytes().replace(b"ev-001;ev-002", b"ev-001"))
    _finalize(root)
    assert b"p-001,warden-01,slack_bell,for,final,agreed,own,,ev-001,,agreed\n" in (root / OUT / "final.csv").read_bytes()


def test_finalising_is_deterministic_and_unchanged_twice(tmp_path):
    a, b = _repo(tmp_path / "a"), _repo(tmp_path / "b")
    _finalize(a), _finalize(b)
    assert (a / OUT / "final.csv").read_bytes() == (b / OUT / "final.csv").read_bytes()
    before = tree(a)
    code, out, _ = _finalize(a)
    assert code == 0 and out.startswith("unchanged:") and tree(a) == before


def test_an_existing_different_output_is_refused(tmp_path):
    root = _repo(tmp_path)
    (root / OUT / "final.csv").write_bytes(FINAL.replace(b"tolerates", b"against"))
    _refused(_finalize, root, needle="never appended to or overwritten")


@pytest.mark.parametrize("arg", ["repo:CLAUDE.md", "../final.csv", "rows/evidence.csv", "rules/final.csv",
                                 "ledger/final.csv", "nowhere/final.csv", "study.json"])
def test_where_the_final_codes_may_not_go(tmp_path, arg):
    root = _repo(tmp_path)
    (root / "CLAUDE.md").write_text("keep\n", encoding="utf-8")
    _refused(_finalize, root, arg)


def test_a_linked_output_folder_is_refused(tmp_path):
    root = _repo(tmp_path)
    os.symlink("out", root / STUDY_REL / "linked")
    _refused(_finalize, root, "linked/final.csv", needle="symbolic link")


def test_a_disagreement_without_an_adjudication_refuses(tmp_path):
    root = _repo(tmp_path)
    (root / ADJ).write_bytes((root / ADJ).read_bytes().replace(
        b"p-002,slack_bell,tolerates,adjudicator-c (invented),reported,harbour clerk,ev-003,the clerk's account is "
        b"hedged\n", b""))
    out = _refused(_finalize, root)
    assert "[final-no-adjudication]" in out and "p-002" in out and "disagree" in out


def test_a_unit_with_one_pass_and_no_adjudication_refuses(tmp_path):
    root = _repo(tmp_path)
    data = (root / ADJ).read_bytes()
    (root / ADJ).write_bytes(data[:data.index(b"p-003")])
    out = _refused(_finalize, root)
    assert "[final-no-adjudication]" in out and "pass B is missing" in out


def test_a_unit_with_no_pass_refuses_and_every_one_is_listed(tmp_path):
    """D4: coverage against the attribution file's units; stricter than the reference tool."""
    root = _repo(tmp_path)
    path = root / ROWS / "attribution.csv"
    path.write_bytes(path.read_bytes() + b"p-004,warden-01,person,logbook-02,logbook-02#p1,firm,letter,own,\n"
                     b"p-005,warden-02,person,register-03,register-03#p2,firm,letter,own,\n")
    out = _refused(_finalize, root)
    assert out.count("[final-no-pass]") == 2 and "p-004" in out and "p-005" in out


def test_a_final_row_in_the_passes_file_refuses(tmp_path):
    """D2: the passes file holds passes A and B; final codes go to the file survey-finalize writes."""
    root = _repo(tmp_path)
    path = root / CODES
    path.write_bytes(path.read_bytes() + b'p-003,guild-01,slack_bell,NA,final,adjudicator-c (invented),own,,ev-005,,'
                     b"\"missing pass: B, the second coder's packet was never returned\"\n")
    out = _refused(_finalize, root)
    assert "[final-in-codes]" in out


def test_a_code_file_error_refuses(tmp_path):
    root = _repo(tmp_path)
    path = root / CODES
    path.write_bytes(path.read_bytes().replace(b",for,A,", b",perhaps,A,"))
    out = _refused(_finalize, root, needle="a row or code file has an error")
    assert "[codes-code]" in out


@pytest.mark.parametrize("which", [0, 1])
def test_a_refusal_at_either_late_check_changes_nothing(tmp_path, monkeypatch, which):
    root = _repo(tmp_path)
    calls = []
    real = prov.check_writable

    def late(r, rel):
        calls.append(rel)
        if len(calls) == 3 + which:
            raise prov.WriteRefused(f"{rel} became unsafe")
        real(r, rel)
    monkeypatch.setattr(prov, "check_writable", late)
    _refused(_finalize, root, needle="became unsafe")


@pytest.mark.parametrize("victim", [CODES, ADJ, f"{ROWS}/attribution.csv"])
def test_an_input_changed_before_the_write_refuses(tmp_path, monkeypatch, victim):
    """The guards: every input read is read again just before the first replace."""
    root = _repo(tmp_path)
    calls = []
    real = prov.check_writable

    def touch(r, rel):
        calls.append(rel)
        if len(calls) == 3:
            (root / victim).write_bytes((root / victim).read_bytes() + b"\n")
        real(r, rel)
    monkeypatch.setattr(prov, "check_writable", touch)
    code, out, _ = _finalize(root)
    assert code == 1 and "changed while this run was being prepared" in out
    assert not (root / OUT / "final.csv").exists()


def test_finalising_in_an_author_study_uses_the_registrys_persons(tmp_path):
    """D4: in an author study the units are the registry's persons."""
    def author(s):
        s["unit"] = {"kind": "author"}
        s["frame_rules"]["exclude"] = []
    root = _repo(tmp_path, author)
    ev = root / ROWS / "evidence.csv"
    ev.write_bytes(ev.read_bytes().replace(b",p-001,", b",,").replace(b",p-002,", b",,").replace(b",p-003,", b",,")
                   .replace(b",warden-01,,", b",,,").replace(b",warden-02,searched", b",,searched"))
    (root / ADJ).unlink()
    (root / CODES).write_bytes(b"unit_id,person_id,outcome,code,pass,coder,basis,reporter,evidence_ids,level,note\n"
                               b"warden-01,warden-01,slack_bell,for,A,coder-a,own,,ev-001,,\n"
                               b"warden-01,warden-01,slack_bell,for,B,coder-b,own,,ev-001,,\n")
    out = _refused(_finalize, root)
    assert "[final-no-pass]" in out and "guild-01" in out and "warden-02" in out


# --------------------------------------------------------------------------- the rollup
def test_the_invented_studys_rollup(tmp_path):
    root = _repo(tmp_path)
    _finalize(root)
    code, out, _ = _rollup(root)
    assert code == 0 and (root / OUT / "rollup.csv").read_bytes() == ROLLUP
    assert "1 author(s) left out" in out
    doc = json.loads((root / OUT / "rollup.csv.provenance.json").read_bytes())
    assert list(doc["gates"]) == ["S5"] and doc["tool"] == "survey-rollup"
    assert [e["path"] for e in doc["inputs"]] == [f"{STUDY_REL}/study.json", f"{OUT}/final.csv",
                                                  f"{ROWS}/attribution.csv"]


def test_the_rollup_is_deterministic_and_unchanged_twice(tmp_path):
    root = _repo(tmp_path)
    _finalize(root)
    _rollup(root)
    before = tree(root)
    code, out, _ = _rollup(root)
    assert code == 0 and out.startswith("unchanged:") and tree(root) == before


def test_a_rollup_needs_a_current_final_file(tmp_path):
    root = _repo(tmp_path)
    (root / OUT / "final.csv").write_bytes(FINAL)  # written by hand: no record
    _refused(_rollup, root, needle="not a current output of survey-finalize")
    root2 = _repo(tmp_path / "b")
    _finalize(root2)
    path = root2 / OUT / "final.csv"
    path.write_bytes(path.read_bytes().replace(b"tolerates", b"against"))  # edited after it was written
    _refused(_rollup, root2, needle="is not what survey-finalize gives")


def test_a_rollup_with_a_final_file_outside_the_study_is_refused(tmp_path):
    root = _repo(tmp_path)
    (root / "final.csv").write_bytes(FINAL)
    _refused(_rollup, root, "repo:final.csv")


def test_a_rollup_in_an_author_study_is_refused(tmp_path):
    def author(s):
        s["unit"] = {"kind": "author"}
        s["frame_rules"]["exclude"] = []
    root = _repo(tmp_path, author)
    _refused(_rollup, root, needle="author study")


def test_a_counted_unit_and_an_excluded_one(tmp_path):
    """p-003 counted ("firm") but its genre "draft" is in exclude_from_rollup: guild-01 is still left out."""
    root = _repo(tmp_path)
    path = root / ROWS / "attribution.csv"
    path.write_bytes(path.read_bytes().replace(b"p-003,guild-01,guild,minutes-01,minutes-01#p2,doubtful,letter",
                                               b"p-003,guild-01,guild,minutes-01,minutes-01#p2,firm,draft"))
    _finalize(root)
    code, out, _ = _rollup(root)
    assert code == 0 and b"guild-01" not in (root / OUT / "rollup.csv").read_bytes() and "1 author(s) left out" in out


def test_a_collective_author_keeps_its_kind_and_na_gives_the_missing_value(tmp_path):
    """p-003 counted ("firm", genre "letter"): guild-01's only final code is NA, which is skipped, so the cell is the
    missing value NE (4.2, line 408); guild-01 keeps author_kind "guild" (line 422)."""
    root = _repo(tmp_path)
    path = root / ROWS / "attribution.csv"
    path.write_bytes(path.read_bytes().replace(b",doubtful,", b",firm,"))
    _finalize(root)
    assert _rollup(root)[0] == 0
    assert b"guild-01,letter,guild,NE,letter\n" in (root / OUT / "rollup.csv").read_bytes()


# --------------------------------------------------------------------------- each rule by hand (4.2, lines 412-418)
ORDINAL = {"key": "o", "scale": "ordinal", "levels": [{"code": "against", "label": "a", "order": 1},
                                                       {"code": "tolerates", "label": "t", "order": 2},
                                                       {"code": "for", "label": "f", "order": 3}],
           "na_codes": ["NA"], "missing": "NE"}
NOMINAL = {"key": "n", "scale": "nominal", "levels": [{"code": "iron", "label": "i"}, {"code": "bronze", "label": "b"},
                                                       {"code": "brass", "label": "r"}], "missing": "NE"}


def _rule(base, rule, codes, **more):
    return sf.apply_rule(dict(base, rollup=rule, **more), codes)


def test_max_order_takes_the_highest_order():
    """against(1), for(3), tolerates(2): the highest order is for."""
    assert _rule(ORDINAL, "max-order", ["against", "for", "tolerates"]) == ("for", "")


def test_any_present():
    """present_code "tolerates" present -> tolerates. Absent, ordinal: the lowest order (against before for);
    nominal: the code declared first in levels among those left (iron before brass)."""
    assert _rule(ORDINAL, "any-present", ["for", "tolerates"], present_code="tolerates") == ("tolerates", "")
    assert _rule(ORDINAL, "any-present", ["for", "against"], present_code="tolerates") == ("against", "")
    assert _rule(NOMINAL, "any-present", ["brass", "iron"], present_code="bronze") == ("iron", "")


def test_single_code_and_its_conflict():
    assert _rule(NOMINAL, "single-code", ["iron", "iron"]) == ("iron", "")
    value, error = _rule(NOMINAL, "single-code", ["iron", "brass"])
    assert value == "" and "single-code allows one" in error


def test_mixed_if_conflict():
    assert _rule(NOMINAL, "mixed-if-conflict", ["iron", "iron"]) == ("iron", "")
    assert _rule(NOMINAL, "mixed-if-conflict", ["iron", "brass"]) == ("mixed", "")


def test_nothing_left_gives_the_missing_value():
    assert _rule(ORDINAL, "max-order", []) == ("NE", "")


def test_a_single_code_conflict_refuses_the_rollup(tmp_path):
    """Two counted letters of warden-02 with different final codes, under single-code: an error (line 412)."""
    root = _repo(tmp_path, lambda s: s["outcomes"][0].update(rollup="single-code"))
    att = root / ROWS / "attribution.csv"
    att.write_bytes(att.read_bytes() + b"p-006,warden-02,person,register-04,register-04#p1,firm,letter,own,\n")
    codes = root / CODES
    codes.write_bytes(codes.read_bytes() + b"p-006,warden-02,slack_bell,for,A,coder-a,reported,harbour clerk,ev-003,,\n"
                      b"p-006,warden-02,slack_bell,for,B,coder-b,reported,harbour clerk,ev-003,,\n")
    assert _finalize(root)[0] == 0
    out = _refused(_rollup, root, needle="cannot give a value")
    assert "[rollup-conflict]" in out


def test_the_rollup_columns_follow_d5():
    spec = {"unit": {"kind": "passage", "rollup_by": ["genre"], "rollup_types": "genre"},
            "outcomes": [{"key": "a", "source": {"kind": "codes"}, "rollup": "max-order"},
                         {"key": "b", "source": {"kind": "codes"}, "rollup": "none"},
                         {"key": "c", "source": {"kind": "evidence-attribute"}, "rollup": "single-code"}]}
    assert sf.rollup_columns(spec) == ("person_id", "genre", "author_kind", "a", "a__types")


# --------------------------------------------------------------------------- the bridge
def test_the_bridge_runs_both_commands_and_refuses_root(tmp_path):
    root = _repo(tmp_path)
    (root / "scripts").mkdir()
    shutil.copy(ROOT / "scripts" / "claude_researchteam_bridge.sh", root / "scripts")
    shutil.copytree(SURVEY, root / "scripts" / "survey", ignore=shutil.ignore_patterns("__pycache__"))
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    bridge = ["bash", str(root / "scripts" / "claude_researchteam_bridge.sh")]
    res = subprocess.run([*bridge, "survey-finalize", "tidebell", "--out", "out/final.csv"], capture_output=True,
                         text=True, env=env)
    assert res.returncode == 0 and "wrote:" in res.stdout
    res = subprocess.run([*bridge, "survey-rollup", "tidebell", "out/final.csv", "--out", "out/rollup.csv"],
                         capture_output=True, text=True, env=env)
    assert res.returncode == 0 and "rollup: 2 row(s)" in res.stdout
    for cmd in ("survey-finalize", "survey-rollup"):
        res = subprocess.run([*bridge, cmd, "--root", str(tmp_path), "tidebell"], capture_output=True, text=True,
                             env=env)
        assert res.returncode == 2 and "--root is not accepted" in res.stderr
    assert not list((root / "scripts" / "survey").glob("__pycache__"))


def test_usage_errors(tmp_path):
    root = _repo(tmp_path)
    assert run(survey_finalize, "--root", str(root), "tidebell")[0] == 2
    assert run(survey_rollup, "--root", str(root), "tidebell", "--out", "x.csv")[0] == 2


def test_a_hand_edited_final_file_is_refused_by_the_rollup(tmp_path):
    """The record holds no hash of the final file (4.6, line 565); the rollup works the final codes out again."""
    root = _repo(tmp_path)
    _finalize(root)
    assert prov.check_current(root, f"{OUT}/final.csv.provenance.json").built
    path = root / OUT / "final.csv"
    path.write_bytes(path.read_bytes().replace(b"agreed; evidence differed", b"agreed"))
    _refused(_rollup, root, needle="is not what survey-finalize gives")
