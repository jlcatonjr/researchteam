"""Gates, manifests, states and the refusal rule (contract 6.1), the ledger's structural checks (6.2), and the
commands survey-validate, survey-status and survey-manifest (section 7)."""
import hashlib
import json
import os
import shutil
import subprocess
import sys

import pytest

from survey_support import (
    FAKE_PEM, LEDGER, ROOT, STUDY_REL, build_ledger, edit_spec, make_repo, rules, run, survey_gates as gates,
    survey_ledger as ledger_mod, survey_manifest, survey_spec as sp, survey_status, survey_validate, tree,
)
from survey_support import survey_core as core

MDIR = f"{LEDGER}/references"  # where survey-manifest writes (beside the log, 6.2)


def _study(root):
    study = sp.load_study("tidebell", root)
    assert study.ok, [f.line() for f in study.findings]
    return study


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------- the manifest (6.1)
def test_the_manifest_is_exactly_the_6_1_object(tmp_path):
    root = make_repo(tmp_path)
    base = root / STUDY_REL
    data = gates.build_manifest(_study(root), "S6")
    expected = {
        "kind": "survey-signoff", "gate": "S6", "project": "tidebell", "mode": "retroactive", "schema_version": "1",
        # the specification first; the two covers resolve to one file, so it is listed once, as first declared
        "files": [{"path": f"{STUDY_REL}/study.json", "sha256": _sha((base / "study.json").read_bytes())},
                  {"path": f"{STUDY_REL}/analysis/plan.md", "sha256": _sha((base / "analysis/plan.md").read_bytes())}],
    }
    assert data == (json.dumps(expected, sort_keys=True, separators=(",", ":")) + "\n").encode()


def test_covers_keep_their_declared_order(tmp_path):
    root = make_repo(tmp_path)
    paths = [e["path"] for e in json.loads(gates.build_manifest(_study(root), "S0"))["files"]]
    assert paths == [f"{STUDY_REL}/{p}" for p in ("study.json", "rules/forbidden.txt", "rules/stop_words.txt",
                                                  "tables/harbour.csv", "tables/duties.csv", "plans/query_plan.md")]


def test_a_repeat_of_the_specification_in_covers_is_removed(tmp_path):
    root = make_repo(tmp_path, lambda s: s["signoffs"]["gates"]["S5"]["covers"].insert(0, "study.json"))
    files = json.loads(gates.build_manifest(_study(root), "S5"))["files"]
    assert [f["path"] for f in files] == [f"{STUDY_REL}/study.json", f"{STUDY_REL}/codebooks/slack_bell.md"]


def test_crlf_in_a_covered_text_file_does_not_change_the_manifest(tmp_path):
    root = make_repo(tmp_path)
    before = gates.build_manifest(_study(root), "S5")
    book = root / STUDY_REL / "codebooks" / "slack_bell.md"
    book.write_bytes(book.read_bytes().replace(b"\n", b"\r\n"))
    assert gates.build_manifest(_study(root), "S5") == before


def test_the_manifest_carries_schema_version_0_and_the_mode(tmp_path):
    root = make_repo(tmp_path, lambda s: s.update(schema_version="0"))
    doc = json.loads(gates.build_manifest(_study(root), "S0"))
    assert doc["schema_version"] == "0" and doc["mode"] == "prospective"


def test_scope_and_action_are_the_6_2_names():
    assert gates.scope("S0", "x-study") == "survey-signoff/S0/x-study"
    assert gates.action("S0", "x-study", "ab") == "survey-signoff/S0/x-study:sha256-ab"


# --------------------------------------------------------------------------- the three states (6.1)
def _states(root):
    study = _study(root)
    led = ledger_mod.check_ledger(study)
    return {g: gates.gate_status(study, g, led)[0] for g in gates.GATES}


def test_before_any_request_a_declared_gate_is_unavailable(tmp_path):
    states = _states(make_repo(tmp_path))
    assert {g: s.state for g, s in states.items()} == {"S0": "UNAVAILABLE", "S5": "UNAVAILABLE",
                                                       "S6": "UNAVAILABLE", "S8": "NOT DECLARED"}
    assert gates.NO_VERIFICATION in states["S0"].reason


def test_a_change_to_a_covered_file_after_the_request_is_uncleared(tmp_path):
    root = make_repo(tmp_path)
    assert run(survey_manifest, "--root", str(root), "tidebell", "S5")[0] == 0
    assert _states(root)["S5"].state == "UNAVAILABLE"
    (root / STUDY_REL / "codebooks" / "slack_bell.md").write_text("an edit\n")
    st = _states(root)
    assert st["S5"].state == "UNCLEARED" and "changed since the stored manifest file was written" in st["S5"].reason
    assert st["S0"].state == "UNAVAILABLE"  # no request for S0 was made


def test_an_edit_to_the_specification_unclears_every_requested_gate(tmp_path):
    root = make_repo(tmp_path)
    for g in ("S0", "S5"):
        run(survey_manifest, "--root", str(root), "tidebell", g)
    edit_spec(root, lambda s: s.update(title="A changed invented title"))
    st = _states(root)
    assert st["S0"].state == st["S5"].state == "UNCLEARED" and st["S6"].state == "UNAVAILABLE"


def test_a_covered_file_removed_after_the_request_is_uncleared(tmp_path):
    root = make_repo(tmp_path, lambda s: s.update(status="draft"))
    run(survey_manifest, "--root", str(root), "tidebell", "S5")
    (root / STUDY_REL / "codebooks" / "slack_bell.md").unlink()
    assert _states(root)["S5"].state == "UNCLEARED"


def test_uncleared_holds_even_when_the_ledger_is_malformed(tmp_path):
    root = make_repo(tmp_path)
    run(survey_manifest, "--root", str(root), "tidebell", "S5")
    (root / STUDY_REL / "codebooks" / "slack_bell.md").write_text("an edit\n")
    (root / LEDGER / "references" / "security-waivers.log.csv").write_text("x\n")
    st = _states(root)
    assert st["S5"].state == "UNCLEARED" and st["S0"].state == "UNAVAILABLE"


def test_a_malformed_ledger_leaves_every_gate_unavailable(tmp_path):
    root = make_repo(tmp_path)
    (root / LEDGER / "references" / "security-waivers.log.csv").write_text("x\n")
    st = _states(root)
    assert all(st[g].state == "UNAVAILABLE" and "ledger" in st[g].reason for g in ("S0", "S5", "S6"))


def test_no_gate_ever_reads_cleared_in_this_version(tmp_path):
    root = make_repo(tmp_path)
    for g in ("S0", "S5", "S6"):
        run(survey_manifest, "--root", str(root), "tidebell", g)
    out = run(survey_status, "--root", str(root), "tidebell")[1]
    assert "CLEARED" not in out.replace("UNCLEARED", "").replace("reads CLEARED", "")


def test_the_verification_seam_says_why_it_cannot_clear(tmp_path):
    root = make_repo(tmp_path)
    study = _study(root)
    assert gates.verify_signoff(study, "S0", "0" * 64, ledger_mod.check_ledger(study)) == \
        ("UNAVAILABLE", gates.NO_VERIFICATION)


# --------------------------------------------------------------------------- runs or refuses (6.1)
@pytest.mark.parametrize("state,enforce,declared,legacy,expected", [
    ("CLEARED", "blocking", True, False, "runs"),
    ("UNCLEARED", "blocking", True, False, "refuses"),
    ("UNAVAILABLE", "blocking", True, False, "refuses"),
    ("CLEARED", "build-only", True, False, "runs"),
    ("UNCLEARED", "build-only", True, False, "runs"),
    ("UNAVAILABLE", "build-only", True, False, "runs"),
    ("UNCLEARED", "blocking", True, True, "refuses"),    # a legacy study's declared gate follows the table
    ("UNAVAILABLE", "build-only", True, True, "runs"),
    ("NOT DECLARED", "", False, False, "refuses"),       # undeclared: refuses ...
    ("NOT DECLARED", "", False, True, "runs"),           # ... except in a legacy study
])
def test_stage_decision_follows_the_6_1_table(state, enforce, declared, legacy, expected):
    decision, recorded = gates.stage_decision(state, enforce, declared, legacy)
    assert decision == expected
    assert recorded == state


def test_stage_decision_refuses_unknown_values():
    with pytest.raises(ValueError):
        gates.stage_decision("MAYBE", "blocking", True, False)
    with pytest.raises(ValueError):
        gates.stage_decision("CLEARED", "advisory", True, False)


# --------------------------------------------------------------------------- the ledger folder (6.2)
def _ledger_rules(root):
    study = _study(root)
    return rules(ledger_mod.check_ledger(study).findings)


def _refs(root):
    return root / LEDGER / "references"


def test_the_built_ledger_is_well_formed(tmp_path):
    assert _ledger_rules(make_repo(tmp_path)) == set()


@pytest.mark.parametrize("value,rule", [
    ("ledger", "ledger-form"), ("agentteams-clearance:", "ledger-form"), ("clearance:ledger", "ledger-form"),
    ("agentteams-clearance:/abs/ledger", "path-absolute"), ("agentteams-clearance:../ledger", "path-dotdot"),
    ("agentteams-clearance:absent", "ledger-missing"),
])
def test_the_ledger_value(tmp_path, value, rule):
    root = make_repo(tmp_path, lambda s: s["signoffs"].update(ledger=value))
    assert rule in _ledger_rules(root)


def test_a_repo_rooted_ledger(tmp_path):
    root = make_repo(tmp_path, lambda s: s["signoffs"].update(ledger="agentteams-clearance:repo:gates/tidebell"),
                     ledger=False)
    build_ledger(root / "gates" / "tidebell")
    assert _ledger_rules(root) == set()


def test_no_component_of_the_ledger_path_is_a_link(tmp_path):
    root = make_repo(tmp_path, lambda s: s["signoffs"].update(ledger="agentteams-clearance:linked"))
    os.symlink("ledger", root / STUDY_REL / "linked")
    assert "ledger-link" in _ledger_rules(root)


#: The header agentteams 1.3.0 writes for a new decisions log, spelled out here independently of the constant.
EXACT_HEADER = ("timestamp,requesting_agent,date,action_reviewed,verdict,scope,conditions,conditions_verified,"
                "evidence,author,derives_from,effect_class,effect_grants,effect_targets,effect_relaxes,"
                "effect_destructive,effect_cross_repo,effect_bulk,text_digest,sig_scheme,key_id,prev_digest,"
                "signature\n")
#: Step A's first fixture header: the signed columns without timestamp and requesting_agent. agentteams refuses it.
OLD_FIXTURE_HEADER = EXACT_HEADER[len("timestamp,requesting_agent,"):]


def test_the_log_header_is_exactly_agentteams_new_log_header(tmp_path):
    assert ",".join(ledger_mod.LOG_HEADER) + "\n" == EXACT_HEADER
    root = make_repo(tmp_path)  # the fixture writes a header-only log with that header
    folder = root / STUDY_REL / "ledger" / "references"
    assert (folder / "security-decisions.log.csv").read_text() == EXACT_HEADER
    assert _ledger_rules(root) == set()


def test_agentteams_accepts_the_fixtures_header_only_log(tmp_path):
    """Where agentteams is importable: its public log check passes the fixture's log, and its own new-log header is
    the toolkit's constant."""
    governance_logs = pytest.importorskip("agentteams.governance_logs",
                                          reason="agentteams is not installed in this interpreter")
    decision_log = pytest.importorskip("agentteams.cli.decision_log", reason="agentteams is not installed")
    root = make_repo(tmp_path)
    log = root / STUDY_REL / "ledger" / "references" / "security-decisions.log.csv"
    assert governance_logs.check_log(log) == []
    assert ("timestamp", "requesting_agent", *decision_log.SIGNED_DECISION_COLUMNS) == ledger_mod.LOG_HEADER


@pytest.mark.parametrize("damage,rule", [
    (lambda r: shutil.rmtree(r), "ledger-layout"),
    (lambda r: (r / "agent-privilege.json").unlink(), "ledger-privilege"),
    (lambda r: (r / "agent-privilege.json").write_text("[]"), "ledger-privilege"),
    (lambda r: (r / "security-decisions.log.csv").unlink(), "ledger-log"),
    (lambda r: (r / "security-decisions.log.csv").write_text("date,action_reviewed,verdict\n"), "ledger-log"),
    (lambda r: (r / "security-decisions.log.csv").write_text(
        "action_reviewed,verdict,signature,sig_scheme,key_id,derives_from\na,b\n"), "ledger-log"),
    (lambda r: (r / "security-decisions.log.csv").write_text(OLD_FIXTURE_HEADER), "ledger-log"),
    (lambda r: (r / "security-decisions.log.csv").write_text(" " + EXACT_HEADER), "ledger-log"),
    (lambda r: (r / "security-decisions.log.csv").write_bytes(b"\xff\xfe"), "ledger-log"),
    (lambda r: shutil.rmtree(r / "authorized-verify-keys"), "ledger-keys"),
    (lambda r: (r / "authorized-verify-keys" / "notes.txt").write_text("x"), "ledger-keys"),
    (lambda r: (r / "authorized-verify-keys" / "op-test.pub.pem").write_text("not a key"), "ledger-keys"),
    (lambda r: (r / "authorized-verify-keys" / "op-test.pub.pem").unlink(), "ledger-keys-empty"),
    (lambda r: (r / "security-approvers.txt").unlink(), "ledger-approvers"),
    (lambda r: (r / "security-approvers.txt").write_text("# only a comment\n\n"), "ledger-approvers-empty"),
    (lambda r: (r / "security-waivers.log.csv").write_text(""), "ledger-waiver"),
])
def test_structural_errors_of_the_ledger_folder(tmp_path, damage, rule):
    root = make_repo(tmp_path)
    damage(_refs(root))
    assert rule in _ledger_rules(root)
    code, out, _ = run(survey_validate, "--root", str(root), "tidebell")
    assert code == 1 and f"[{rule}]" in out


def _team(root, rel, *, approvers=None, keys=None, privilege=None):
    refs = root / rel / "references"
    refs.mkdir(parents=True, exist_ok=True)
    (refs / "agent-privilege.json").write_text(json.dumps(privilege or {}))
    if approvers is not None:
        (refs / "security-approvers.txt").write_text(approvers)
    if keys:
        (refs / "authorized-verify-keys").mkdir(exist_ok=True)
        for k, pem in keys.items():
            (refs / "authorized-verify-keys" / f"{k}.pub.pem").write_text(pem)


def _with_parent(root, value):
    (_refs(root) / "agent-privilege.json").write_text(json.dumps({"parent_team": value}))


def test_a_sound_parent_team(tmp_path):
    root = make_repo(tmp_path)
    _team(root, "governance/team")
    _with_parent(root, "governance/team")
    assert _ledger_rules(root) == set()


@pytest.mark.parametrize("setup,value,why", [
    (None, "/governance/team", "is absolute"), (None, "../elsewhere", "has a '..' segment"),
    (None, "governance/none", "is not a team directory"),
    ("self", f"{LEDGER}", "names the ledger folder itself"),
    ("own-parent", "governance/team", "declares a parent of its own"),
    ("link", "governance/linked", "symbolic link"), ("inner-link", "governance/team", "symbolic link"),
])
def test_parent_team_rules_leave_the_gates_unavailable_and_are_not_errors(tmp_path, setup, value, why):
    """6.2, lines 910-913: these leave the gate UNAVAILABLE; the contract does not make them errors."""
    root = make_repo(tmp_path)
    _team(root, "governance/team", privilege={"parent_team": ".github/agents"} if setup == "own-parent" else {})
    if setup == "link":
        os.symlink("team", root / "governance" / "linked")
    if setup == "inner-link":  # L1: a link inside the team dir must not redirect what is read
        shutil.move(str(root / "governance/team/references"), str(root / "elsewhere"))
        os.symlink(root / "elsewhere", root / "governance/team/references")
    _with_parent(root, value)
    led = ledger_mod.check_ledger(_study(root))
    assert led.findings == [] and any(why in r for r in led.unavailable), led.unavailable
    assert all(st.state == "UNAVAILABLE" and why in st.reason
               for g, st in _states(root).items() if g != "S8")
    assert run(survey_validate, "--root", str(root), "tidebell")[0] == 0
    assert run(survey_status, "--root", str(root), "tidebell")[0] == 0


@pytest.mark.parametrize("value", [7, "", None, ["governance/team"], "governance/te\x00am", "repo:governance/team",
                                   "governance\\team", "./governance/team", "governance//team"])
def test_a_parent_team_value_that_is_no_path_is_a_malformed_ledger(tmp_path, value):
    """Not one of the causes 6.2 lists: a bad value in the folder's own agent-privilege.json."""
    root = make_repo(tmp_path)
    _team(root, "governance/team")
    _with_parent(root, value)
    led = ledger_mod.check_ledger(_study(root))
    assert any(f.rule == "ledger-privilege" and "parent_team" in f.message for f in led.findings), led.findings
    assert run(survey_status, "--root", str(root), "tidebell")[0] == 1
    assert run(survey_validate, "--root", str(root), "tidebell")[0] == 1


def test_a_link_inside_a_generated_team_dir_leaves_the_gates_unavailable(tmp_path):
    root = make_repo(tmp_path)
    _team(root, ".github/agents", approvers="someone-else\n", keys={"op-other": FAKE_PEM})
    (root / "other-refs").mkdir()
    shutil.move(str(root / ".github/agents/references/security-approvers.txt"), str(root / "other-refs/a.txt"))
    os.symlink(root / "other-refs/a.txt", root / ".github/agents/references/security-approvers.txt")
    led = ledger_mod.check_ledger(_study(root))
    assert led.findings == []  # the comparison was not redirected through the link, and not made
    assert any(".github/agents" in r and "symbolic link" in r for r in led.unavailable)


def test_a_team_directory_reached_through_a_link_leaves_the_gates_unavailable(tmp_path):
    root = make_repo(tmp_path)
    _team(root, "real-team")
    (root / ".claude").mkdir()
    os.symlink(root / "real-team", root / ".claude" / "agents")
    code, out, _ = run(survey_status, "--root", str(root), "tidebell")
    assert code == 0
    assert "S0: UNAVAILABLE" in out and "the team directory .claude/agents is reached through a symbolic link" in out
    code, out, _ = run(survey_validate, "--root", str(root), "tidebell")
    assert code == 0 and "note: the gates read UNAVAILABLE" in out


def test_the_folder_names_the_same_approvers_and_keys_as_the_team(tmp_path):
    root = make_repo(tmp_path)
    _team(root, ".github/agents", approvers="# roster\nOperator\n", keys={"op-test": FAKE_PEM})
    assert _ledger_rules(root) == set()  # names compare as agentteams compares an author
    (root / ".github/agents/references/security-approvers.txt").write_text("operator\nsecond\n")
    assert "ledger-parity" in _ledger_rules(root)


def test_different_key_files_are_a_parity_error(tmp_path):
    root = make_repo(tmp_path)
    _team(root, ".github/agents", approvers="operator\n", keys={"op-other": FAKE_PEM})
    assert "ledger-parity" in _ledger_rules(root)


def test_a_team_with_only_a_comment_list_and_no_key_has_neither(tmp_path):
    root = make_repo(tmp_path)
    _team(root, ".github/agents", approvers="# generated: no approvers yet\n")
    assert _ledger_rules(root) == set()


def test_the_parent_team_is_compared_too(tmp_path):
    root = make_repo(tmp_path)
    _team(root, "governance/team", approvers="someone-else\n", keys={"op-test": FAKE_PEM})
    _with_parent(root, "governance/team")
    assert "ledger-parity" in _ledger_rules(root)


# --------------------------------------------------------------------------- the commands (section 7)
def test_validate_and_status_write_nothing(tmp_path):
    root = make_repo(tmp_path)
    before = tree(root)
    assert run(survey_validate, "--root", str(root), "tidebell")[0] == 0
    assert run(survey_status, "--root", str(root), "tidebell")[0] == 0
    assert tree(root) == before


def test_status_prints_hash_state_enforce_and_mode_and_the_environment(tmp_path):
    root = make_repo(tmp_path)
    code, out, _ = run(survey_status, "--root", str(root), "tidebell")
    study = _study(root)
    s0 = _sha(gates.build_manifest(study, "S0"))
    assert code == 0
    assert f"S0: UNAVAILABLE manifest_sha256={s0} enforce=blocking mode=prospective" in out
    assert "S6: UNAVAILABLE" in out and "enforce=build-only mode=retroactive" in out
    assert "S8: NOT DECLARED" in out
    import unicodedata
    assert f"unicodedata {unicodedata.unidata_version}" in out


def test_status_exits_0_whatever_the_states(tmp_path):
    root = make_repo(tmp_path)
    run(survey_manifest, "--root", str(root), "tidebell", "S5")
    (root / STUDY_REL / "codebooks" / "slack_bell.md").write_text("an edit\n")
    code, out, _ = run(survey_status, "--root", str(root), "tidebell")
    assert code == 0 and "S5: UNCLEARED" in out


@pytest.mark.parametrize("break_it", ["spec", "ledger", "manifest"])
def test_status_exits_non_zero_only_when_something_is_malformed(tmp_path, break_it):
    root = make_repo(tmp_path)
    run(survey_manifest, "--root", str(root), "tidebell", "S0")
    if break_it == "spec":
        edit_spec(root, lambda s: s.update(colour="blue"))
    elif break_it == "ledger":
        (_refs(root) / "security-waivers.log.csv").write_text("")
    else:
        (root / MDIR / "tidebell-survey.S0.manifest.json").write_text('{"kind": "survey-signoff"}\n')
    code, out, _ = run(survey_status, "--root", str(root), "tidebell")
    assert code == 1 and "FAIL" in out


@pytest.mark.parametrize("content", [
    b'{"files":[],"gate":"S0","kind":"survey-signoff","mode":"prospective","project":"tidebell","schema_version":"1"}',
    b'{"files": [], "gate": "S0", "kind": "survey-signoff", "mode": "prospective", "project": "tidebell", '
    b'"schema_version": "1"}\n',
    b'{"files":[],"gate":"S5","kind":"survey-signoff","mode":"prospective","project":"tidebell","schema_version":"1"}\n',
    b'{"files":[{"path":"x"}],"gate":"S0","kind":"survey-signoff","mode":"prospective","project":"tidebell",'
    b'"schema_version":"1"}\n',
])
def test_a_malformed_manifest_file(tmp_path, content):
    root = make_repo(tmp_path)
    (root / MDIR / "tidebell-survey.S0.manifest.json").write_bytes(content)
    code, out, _ = run(survey_validate, "--root", str(root), "tidebell")
    assert code == 1 and "[manifest-malformed]" in out
    assert _states(root)["S0"].state == "UNAVAILABLE"


def test_manifest_writes_the_file_and_prints_what_the_operator_signs(tmp_path):
    root = make_repo(tmp_path)
    before = tree(root)
    code, out, _ = run(survey_manifest, "--root", str(root), "tidebell", "S0")
    rel = f"{MDIR}/tidebell-survey.S0.manifest.json"
    data = (root / rel).read_bytes()
    digest = _sha(data)
    assert code == 0 and data == gates.build_manifest(_study(root), "S0")
    assert set(tree(root)) - set(before) == {rel}  # the manifest and nothing else
    assert f"manifest_sha256: {digest}" in out
    assert "scope: survey-signoff/S0/tidebell-survey" in out
    assert f"action: survey-signoff/S0/tidebell-survey:sha256-{digest}" in out
    assert f"--clearance-file {rel} --output {LEDGER}" in out
    log = (_refs(root) / "security-decisions.log.csv").read_text()
    assert log.count("\n") == 1  # no ledger row was written
    assert str(tmp_path) not in out  # repository-relative paths only


def test_manifest_is_deterministic(tmp_path):
    root = make_repo(tmp_path)
    first = run(survey_manifest, "--root", str(root), "tidebell", "S0")
    data = (root / MDIR / "tidebell-survey.S0.manifest.json").read_bytes()
    second = run(survey_manifest, "--root", str(root), "tidebell", "S0")
    assert (root / MDIR / "tidebell-survey.S0.manifest.json").read_bytes() == data
    assert first[1].replace("wrote:", "unchanged:") == second[1]
    other = make_repo(tmp_path / "again")
    run(survey_manifest, "--root", str(other), "tidebell", "S0")
    assert (other / MDIR / "tidebell-survey.S0.manifest.json").read_bytes() == data


@pytest.mark.parametrize("setup,needle", [
    (lambda root: edit_spec(root, lambda s: s["signoffs"]["gates"].pop("S5")), "not declared"),
    (lambda root: (_refs(root) / "security-waivers.log.csv").write_text(""), "ledger folder is malformed"),
    (lambda root: edit_spec(root, lambda s: s.update(colour="x")), "malformed"),
    (lambda root: (edit_spec(root, lambda s: s.update(status="draft")),
                   (root / STUDY_REL / "codebooks" / "slack_bell.md").unlink()), "cannot be built"),
    (lambda root: (root / MDIR / "tidebell-survey.S5.manifest.json").write_text("{}"), "remove it first"),
    (lambda root: (root / MDIR / "tidebell-survey.S5.manifest.json").mkdir(), "not a regular file"),
])
def test_manifest_refuses_and_writes_nothing(tmp_path, setup, needle):
    root = make_repo(tmp_path)
    setup(root)
    before = tree(root)
    code, out, _ = run(survey_manifest, "--root", str(root), "tidebell", "S5")
    assert code == 1 and "REFUSED" in out and needle in out
    assert tree(root) == before


@pytest.mark.parametrize("args", [
    ("tidebell",), ("tidebell", "S1"), ("../tidebell", "S0"), ("absent", "S0"), ("--root",),
])
def test_manifest_usage_errors_exit_2(tmp_path, args):
    root = make_repo(tmp_path)
    full = ("--root", str(root), *args) if args != ("--root",) else args
    assert run(survey_manifest, *full)[0] == 2


def test_a_root_without_git_is_a_usage_error(tmp_path):
    root = make_repo(tmp_path)
    shutil.rmtree(root / ".git")
    assert run(survey_validate, "--root", str(root), "tidebell")[0] == 2


# --------------------------------------------------------------------------- the bridge (section 7)
def _repo_with_scripts(tmp_path, with_survey=True):
    root = make_repo(tmp_path)
    (root / "scripts").mkdir()
    shutil.copy(ROOT / "scripts" / "claude_researchteam_bridge.sh", root / "scripts")
    if with_survey:
        shutil.copytree(ROOT / "scripts" / "survey", root / "scripts" / "survey",
                        ignore=shutil.ignore_patterns("__pycache__"))
    return root


def _bridge(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    return subprocess.run(["bash", str(root / "scripts" / "claude_researchteam_bridge.sh"), *args],
                          capture_output=True, text=True, env=env)


def test_the_bridge_runs_the_three_commands_isolated(tmp_path):
    root = _repo_with_scripts(tmp_path)
    assert _bridge(root, "survey-validate", "tidebell").returncode == 0
    res = _bridge(root, "survey-manifest", "tidebell", "S0")
    assert res.returncode == 0 and "action: survey-signoff/S0/tidebell-survey:sha256-" in res.stdout
    res = _bridge(root, "survey-status", "tidebell")
    assert res.returncode == 0 and "S0: UNAVAILABLE" in res.stdout
    assert not list((root / "scripts" / "survey").glob("__pycache__"))


def test_the_bridge_refuses_clearly_without_the_survey_tools(tmp_path):
    root = _repo_with_scripts(tmp_path, with_survey=False)
    for cmd in ("survey-validate", "survey-status", "survey-manifest"):
        res = _bridge(root, cmd, "tidebell")
        assert res.returncode == 1 and "scripts/survey/" in res.stderr


def test_the_bridge_needs_a_project(tmp_path):
    root = _repo_with_scripts(tmp_path)
    assert _bridge(root, "survey-status").returncode == 2




# --------------------------------------------------------------------------- review fixes
def test_a_symlinked_key_file_is_not_read(tmp_path):
    root = make_repo(tmp_path)
    keys = _refs(root) / "authorized-verify-keys"
    (root / "elsewhere.pem").write_text(FAKE_PEM, encoding="utf-8")
    (keys / "op-test.pub.pem").unlink()
    os.symlink(root / "elsewhere.pem", keys / "op-test.pub.pem")
    led = ledger_mod.check_ledger(_study(root))
    assert {"ledger-keys", "ledger-keys-empty"} <= rules(led.findings)
    assert ledger_mod.read_keys(keys) == {}


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="os.mkfifo is not available here")
def test_a_fifo_key_file_is_not_opened(tmp_path):
    root = make_repo(tmp_path)
    keys = _refs(root) / "authorized-verify-keys"
    os.mkfifo(keys / "op-fifo.pub.pem")  # opening it for reading would block: the test hangs if the tool opens it
    led = ledger_mod.check_ledger(_study(root))
    assert any(f.rule == "ledger-keys" and "op-fifo" in f.where for f in led.findings)
    assert set(ledger_mod.read_keys(keys)) == {"op-test.pub.pem"}


def test_a_symlinked_key_store_is_not_listed(tmp_path):
    root = make_repo(tmp_path)
    refs = _refs(root)
    shutil.move(str(refs / "authorized-verify-keys"), str(root / "store"))
    os.symlink(root / "store", refs / "authorized-verify-keys")
    assert "ledger-keys" in rules(ledger_mod.check_ledger(_study(root)).findings)
    assert ledger_mod.read_keys(refs / "authorized-verify-keys") == {}


def test_a_symlinked_approver_list_is_not_read(tmp_path):
    root = make_repo(tmp_path)
    (root / "names.txt").write_text("operator\n", encoding="utf-8")
    (_refs(root) / "security-approvers.txt").unlink()
    os.symlink(root / "names.txt", _refs(root) / "security-approvers.txt")
    assert "ledger-approvers" in _ledger_rules(root)


@pytest.mark.parametrize("approvers,keys,compared", [
    ("operator\n", {"op-test": FAKE_PEM}, True),        # both: both are compared
    ("operator\n", None, False),                         # approvers only: "has neither"
    ("# generated\n", {"op-test": FAKE_PEM}, False),     # comment-only list with a key: "has neither"
    ("# generated\n", None, False),                      # neither
])
def test_the_team_is_compared_only_when_it_has_both_approvers_and_a_key(tmp_path, approvers, keys, compared):
    """6.2, lines 870-873: a team directory with only the comment-only list, or with no key file, has neither."""
    root = make_repo(tmp_path)
    _team(root, ".github/agents", approvers=approvers, keys=keys)
    assert _ledger_rules(root) == set()  # equal to the folder's, or not compared
    refs = root / ".github/agents/references"
    if "operator" in approvers:
        (refs / "security-approvers.txt").write_text("someone-else\n", encoding="utf-8")
    if keys:
        (refs / "authorized-verify-keys/op-test.pub.pem").write_text(FAKE_PEM.replace("MCow", "MCox"),
                                                                     encoding="utf-8")
    found = [f for f in ledger_mod.check_ledger(_study(root)).findings if f.rule == "ledger-parity"]
    assert (len(found) == 2) if compared else (found == [])


def test_the_comparison_is_not_made_on_a_malformed_ledger_and_says_so(tmp_path):
    root = make_repo(tmp_path)
    _team(root, ".github/agents", approvers="someone-else\n", keys={"op-test": FAKE_PEM})
    (_refs(root) / "security-waivers.log.csv").write_text("", encoding="utf-8")
    led = ledger_mod.check_ledger(_study(root))
    assert "ledger-parity" not in rules(led.findings)
    assert any("comparison" in r and "not made" in r for r in led.unavailable)


def test_an_unreadable_team_list_is_reported_not_skipped(tmp_path):
    root = make_repo(tmp_path)
    _team(root, ".github/agents", keys={"op-test": FAKE_PEM})
    (root / ".github/agents/references/security-approvers.txt").mkdir()  # there, but not a regular file
    led = ledger_mod.check_ledger(_study(root))
    assert any(f.rule == "ledger-parity" and "not made" in f.message for f in led.findings)


@pytest.mark.parametrize("value", ["agentteams-clearance:repo:.git/gates", "agentteams-clearance:repo:.github/agents",
                                   "agentteams-clearance:repo:.claude/agents/gates"])
def test_a_ledger_inside_git_or_a_team_location_is_refused(tmp_path, value):
    root = make_repo(tmp_path, lambda s: s["signoffs"].update(ledger=value))
    assert "ledger-location" in _ledger_rules(root)


def test_the_ledger_log_and_json_files_are_size_capped(tmp_path, monkeypatch):
    root = make_repo(tmp_path)
    monkeypatch.setattr(ledger_mod, "MAX_LOG_BYTES", 10)
    monkeypatch.setattr(ledger_mod, "MAX_JSON_BYTES", 1)
    found = {(f.rule, "larger than" in f.message) for f in ledger_mod.check_ledger(_study(root)).findings}
    assert ("ledger-log", True) in found and ("ledger-privilege", True) in found


def test_the_manifest_file_is_mode_0644(tmp_path):
    root = make_repo(tmp_path)
    run(survey_manifest, "--root", str(root), "tidebell", "S0")
    assert os.stat(root / MDIR / "tidebell-survey.S0.manifest.json").st_mode & 0o777 == 0o644


def test_manifest_refuses_when_the_folder_becomes_a_link_before_writing(tmp_path, monkeypatch):
    root = make_repo(tmp_path)
    real_check = survey_manifest.check_ledger

    def check_then_swap(study):
        led = real_check(study)
        refs = root / MDIR
        shutil.move(str(refs), str(root / "moved-refs"))
        os.symlink(root / "moved-refs", refs)
        return led
    monkeypatch.setattr(survey_manifest, "check_ledger", check_then_swap)
    code, out, _ = run(survey_manifest, "--root", str(root), "tidebell", "S0")
    assert code == 1 and "symbolic link" in out
    assert not (root / "moved-refs" / "tidebell-survey.S0.manifest.json").exists()


def test_manifest_paths_are_carried_as_declared(tmp_path):
    root = make_repo(tmp_path, lambda s: s["signoffs"]["gates"]["S5"]["covers"].append(
        "repo:Projects/tidebell/plans/query_plan.md"))
    files = [f["path"] for f in json.loads(gates.build_manifest(_study(root), "S5"))["files"]]
    assert files[-1] == "Projects/tidebell/plans/query_plan.md"


def test_repeats_are_removed_by_file_identity_not_spelling(tmp_path):
    root = make_repo(tmp_path)
    if not os.path.exists(root / STUDY_REL / "CODEBOOKS" / "slack_bell.md"):
        pytest.skip("this file system is case-sensitive")
    edit_spec(root, lambda s: s["signoffs"]["gates"]["S5"]["covers"].append("CODEBOOKS/slack_bell.md"))
    files = json.loads(gates.build_manifest(_study(root), "S5"))["files"]
    assert [f["path"] for f in files] == [f"{STUDY_REL}/study.json", f"{STUDY_REL}/codebooks/slack_bell.md"]


def test_the_gate_names_have_one_definition():
    assert gates.GATES is core.GATES and sp.GATES is core.GATES
    assert sp._COVERS.pattern == r"^/signoffs/gates/(S0|S5|S6|S8)/covers/\d+$"


def test_the_bridge_refuses_a_root_option(tmp_path):
    root = _repo_with_scripts(tmp_path)
    for args in (("--root", str(tmp_path), "tidebell"), ("--root=/elsewhere", "tidebell"), ("tidebell", "--root")):
        res = _bridge(root, "survey-status", *args)
        assert res.returncode == 2 and "--root is not accepted" in res.stderr


@pytest.mark.parametrize("rel", [".GIT/gates", ".Git", "x/.git/y", ".Claude/agents", ".GITHUB/Agents/gates",
                                 ".github/agents", ".goose/RECIPES/x"])
def test_reserved_locations_are_compared_by_case_folded_name(rel):
    assert ledger_mod.reserved_by_name(rel)


@pytest.mark.parametrize("rel", ["gates", ".github/survey-gates", ".claude/agentsx", "git/x"])
def test_ordinary_locations_are_not_reserved(rel):
    assert not ledger_mod.reserved_by_name(rel)


def test_reserved_locations_are_compared_by_identity_on_disk(tmp_path):
    root = make_repo(tmp_path)
    (root / ".claude" / "agents").mkdir(parents=True)
    if not os.path.exists(root / ".CLAUDE" / "AGENTS"):
        pytest.skip("this file system is case-sensitive")
    assert ledger_mod.reserved_by_identity(root, ".CLAUDE/AGENTS/gates")
    assert ledger_mod.reserved_by_identity(root, ".GIT")
    assert not ledger_mod.reserved_by_identity(root, f"{STUDY_REL}/ledger")
    led_root = make_repo(tmp_path / "b", lambda s: s["signoffs"].update(ledger="agentteams-clearance:repo:.GIT/gates"))
    assert "ledger-location" in _ledger_rules(led_root)


# --------------------------------------------------------------------------- step A follow-ups (carried into step B)
#: The invented example study's S0 manifest hash. It moves when the study, a file S0 covers, or the manifest rules
#: of 6.1 change: a deliberate change updates it here, in one place.
EXAMPLE_S0_SHA256 = "7d0ee994d63e4fff4dd990b49572916537de05be1ed5dcaba92b758eace4d0da"


def test_the_example_studys_s0_manifest_hash_is_pinned(tmp_path):
    root = make_repo(tmp_path)
    assert _sha(gates.build_manifest(_study(root), "S0")) == EXAMPLE_S0_SHA256


def test_a_specification_reached_through_a_link_inside_the_repository_loads(tmp_path):
    root = make_repo(tmp_path)
    spec = root / STUDY_REL / "study.json"
    os.replace(spec, root / STUDY_REL / "study.real.json")
    os.symlink("study.real.json", spec)
    study = _study(root)
    assert study.spec["id"] == "tidebell-survey"
    assert _sha(gates.build_manifest(study, "S0")) == EXAMPLE_S0_SHA256  # the bytes, not the link, are hashed
    assert run(survey_validate, "--root", str(root), "tidebell")[0] == 0
