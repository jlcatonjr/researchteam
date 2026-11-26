"""Step F: sign-off verification and stage refusal (docs/survey-toolkit.md, version 1, 6.1 and 6.2).

Two kinds of test:

- **Everywhere** (no agentteams, no cryptography): every state the tools decide themselves, the order of
  ``gate_status``, the tools' rules on the row that decides (with unsigned invented rows, which the tools must refuse
  before agentteams is asked), the interim family-HALT scan, the child's answer (``interpret``), its environment,
  ``stage_decision`` and the commands' output. A fake verifier stands in for agentteams where a test needs one; it
  proves the wiring, never that a signature verifies.
- **Signing** (skipped, with the reason, unless agentteams 1.3.0 and cryptography are importable): the CLEARED path
  end to end through the real child, with a key pair generated at run time (``survey_signing``).

Every repository, ledger folder, key and log is built in a temporary folder; no test reads this repository's teams.
"""
from __future__ import annotations

import contextlib
import csv
import io
import json
import os
import sys

import pytest

ALL = {"S0", "S5", "S6"}  # the declared gates of the invented study

from survey_support import (
    LEDGER, STUDY_REL, git_init, make_repo, run, survey_gates as gates, survey_ledger as ledger_mod,
    survey_manifest, survey_spec as sp, survey_status, survey_validate,
)

import survey_core as core  # noqa: E402  (on sys.path through survey_support)
import survey_verify as verify  # noqa: E402

STUDY_ID = "tidebell-survey"


# --------------------------------------------------------------------------- helpers
def _study(root):
    study = sp.load_study("tidebell", root)
    assert study.ok, [f.line() for f in study.findings]
    return study


def _refs(root):
    return root / LEDGER / "references"


def _request(root, gate="S0"):
    """Run survey-manifest; return the action it prints."""
    code, out, _ = run(survey_manifest, "--root", str(root), "tidebell", gate)
    assert code == 0, out
    return next(line.split(": ", 1)[1] for line in out.splitlines() if line.startswith("action: "))


def _append(root, **cells):
    """Append an unsigned, invented row to the ledger log (``sig_scheme`` ed25519 unless given)."""
    row = {c: "" for c in ledger_mod.LOG_HEADER}
    row.update({"timestamp": "2026-11-25", "date": "2026-11-25", "verdict": "PASS", "author": "operator",
                "key_id": "op-test", "sig_scheme": "ed25519", "signature": "00"})
    row.update(cells)
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerow([row[c] for c in ledger_mod.LOG_HEADER])
    with open(_refs(root) / "security-decisions.log.csv", "a", encoding="utf-8", newline="") as fh:
        fh.write(buf.getvalue())


def _team_log(root, rel, rows, header="timestamp,requesting_agent,action_reviewed,verdict,conditions,"
                                     "conditions_verified"):
    refs = root / rel / "references"
    refs.mkdir(parents=True, exist_ok=True)
    (refs / "agent-privilege.json").write_text("{}\n")
    (refs / "security-decisions.log.csv").write_text(header + "\n" + "".join(r + "\n" for r in rows))


class FakeVerifier(verify.Verifier):
    """Stands in for agentteams: answers as told, and records every action it is asked about. It proves the wiring
    only."""

    def __init__(self, outcome="cleared", why="", on_run=None):
        self.outcome, self.why, self.on_run, self.calls, self.actions = outcome, why, on_run, 0, []

    def probe(self):
        return self.why

    def check(self, repo_root, team_dir, scope, manifest, action):
        self.calls += 1
        self.actions.append(action)
        if self.on_run:
            self.on_run()
        info = {"version": "1.3.0", "file": "/x/site-packages/agentteams/__init__.py", "purelib": "/x/site-packages",
                "prefix": sys.prefix, "cleared": self.outcome == "cleared", "action": action}
        return verify.ChildResult(self.outcome, "" if self.outcome == "cleared" else "fake: not cleared", info)


def _state(root, gate="S0", verifier=None):
    study = _study(root)
    led = ledger_mod.check_ledger(study)
    return gates.gate_status(study, gate, led, verifier if verifier is not None else FakeVerifier())[0]


# --------------------------------------------------------------------------- the order (6.1; design note section 1)
def test_a_well_formed_row_reaches_the_verifier_and_its_answer_decides(tmp_path):
    root = make_repo(tmp_path)
    act = _request(root)
    _append(root, action_reviewed=act)
    fake = FakeVerifier("cleared")
    st = _state(root, verifier=fake)
    assert st.state == "CLEARED" and fake.calls == 1 and "signed by 'operator' with key 'op-test'" in st.reason
    assert _state(root, verifier=FakeVerifier(verify.NOT_CLEARED)).state == "UNCLEARED"
    assert _state(root, verifier=FakeVerifier(verify.UNAVAILABLE)).state == "UNAVAILABLE"


def test_no_request_is_uncleared_and_never_asks_agentteams(tmp_path):
    root = make_repo(tmp_path)
    fake = FakeVerifier()
    st = _state(root, verifier=fake)
    assert st.state == "UNCLEARED" and "no sign-off request" in st.reason and fake.calls == 0  # Q7


def test_a_stale_request_is_uncleared_before_anything_else(tmp_path):
    root = make_repo(tmp_path)
    act = _request(root)
    _append(root, action_reviewed=act)
    (root / STUDY_REL / "rules" / "forbidden.txt").write_text("an edit\n")
    (_refs(root) / "security-waivers.log.csv").write_text("x\n")  # a malformed ledger does not change it (817)
    fake = FakeVerifier("cleared", why="agentteams is not installed")
    st = _state(root, verifier=fake)
    assert st.state == "UNCLEARED" and "changed since the request" in st.reason and fake.calls == 0


def test_files_put_back_to_a_signed_state_read_uncleared_until_the_request_is_rewritten(tmp_path):
    """Session-adopted default Q8."""
    root = make_repo(tmp_path)
    act = _request(root)
    _append(root, action_reviewed=act)
    rules = root / STUDY_REL / "rules" / "forbidden.txt"
    original = rules.read_bytes()
    rules.write_text("an edit\n")
    _request(root)  # a newer request
    rules.write_bytes(original)  # back to the signed bytes
    assert _state(root).state == "UNCLEARED"
    assert _request(root) == act  # the rewritten request is the signed one
    assert _state(root).state == "CLEARED"


def test_python_without_agentteams_reads_unavailable_and_blocking_stages_refuse(tmp_path, monkeypatch):
    """Python 3.10 (agentteams needs 3.11), or any interpreter without agentteams: the real probe says why."""
    monkeypatch.setattr(verify.importlib.util, "find_spec", lambda name: None)
    root = make_repo(tmp_path)
    act = _request(root)
    _append(root, action_reviewed=act)
    study = _study(root)
    led = ledger_mod.check_ledger(study)
    st = gates.gate_status(study, "S0", led, verify.Verifier())[0]
    assert st.state == "UNAVAILABLE" and "agentteams is not installed for this interpreter" in st.reason
    decision, record, _ = gates.require_gate(study, "S0", led, verify.Verifier())
    assert decision == "refuses" and record["state"] == "UNAVAILABLE"
    assert gates.require_gate(study, "S6", led, verify.Verifier())[0] == "runs"  # build-only still runs


@pytest.mark.parametrize("cells", [{}, {"key_id": "op-other"}, {"author": "someone-else"},
                                   {"verdict": "CONDITIONAL PASS", "conditions_verified": "pending"}])
def test_without_agentteams_a_row_the_tools_would_refuse_still_reads_unavailable(tmp_path, monkeypatch, cells):
    """T1, rule 1.7 (line 45) and lines 915-917: with no usable agentteams a gate is UNAVAILABLE, so the probe comes
    before the tools' row rules. Only no request and a stale request read UNCLEARED (line 817; Q7)."""
    monkeypatch.setattr(verify.importlib.util, "find_spec", lambda name: None)
    root = make_repo(tmp_path)
    act = _request(root)
    if cells:
        _append(root, action_reviewed=act, **cells)  # else: no row for the action at all
    st = _state(root, verifier=verify.Verifier())
    assert st.state == "UNAVAILABLE" and "agentteams is not installed" in st.reason
    assert _state(root, "S5", verifier=verify.Verifier()).state == "UNCLEARED"  # no request for S5


def test_no_request_and_a_manifest_that_cannot_be_built_is_uncleared(tmp_path):
    """T5: a manifest that cannot be built is not a cause of UNAVAILABLE that line 816 lists."""
    root = make_repo(tmp_path, lambda s: s.update(status="draft"))
    (root / STUDY_REL / "codebooks" / "slack_bell.md").unlink()
    st = _state(root, "S5")
    assert st.state == "UNCLEARED" and "cannot be built" in st.reason


def test_an_old_or_unreadable_agentteams_version_is_unavailable(monkeypatch):
    monkeypatch.setattr(verify.importlib.util, "find_spec", lambda name: object())
    for version, needle in (("1.2.9", "older than 1.3.0"), ("1.3.0rc1", "cannot be read"), (None, "cannot be read")):
        monkeypatch.setattr(verify, "installed_version", lambda v=version: v)
        assert needle in verify.probe()
    monkeypatch.setattr(verify, "installed_version", lambda: "1.3.0")
    assert verify.probe() == ""


def test_a_change_while_agentteams_checks_is_unavailable(tmp_path):
    root = make_repo(tmp_path)
    act = _request(root)
    _append(root, action_reviewed=act)
    fake = FakeVerifier("cleared", on_run=lambda: _append(root, action_reviewed="other", verdict="HALT"))
    st = _state(root, verifier=fake)
    assert st.state == "UNAVAILABLE" and "changed while agentteams checked" in st.reason


def test_an_error_file_appearing_during_the_check_is_unavailable(tmp_path):
    """A waiver file is an error (6.2, lines 866-868), and one appearing while agentteams checks is noticed."""
    root = make_repo(tmp_path)
    act = _request(root)
    _append(root, action_reviewed=act)
    fake = FakeVerifier("cleared", on_run=lambda: (_refs(root) / "security-waivers.log.csv").write_text(""))
    assert _state(root, verifier=fake).state == "UNAVAILABLE"


# --------------------------------------------------------------------------- the tools' own rules on the deciding row
@pytest.mark.parametrize("cells,needle", [
    ({"verdict": "CONDITIONAL PASS", "conditions_verified": "pending"}, "only a PASS"),
    ({"verdict": "HALT"}, "is a HALT"),
    ({"verdict": "USED"}, "only a PASS"),
    ({"conditions_verified": "signed-from-checkout (--allow-checkout-signing)"}, "signed from a checkout"),
    ({"derives_from": "survey-signoff/S0/x"}, "derives_from"),
    ({"scope": "ACTION"}, "scope"),
    ({"effect_grants": "write"}, "effect_grants"),
    ({"key_id": "../op-test"}, "not a plain file stem"),
    ({"key_id": "keys/op-test"}, "not a plain file stem"),
    ({"key_id": "op-other"}, "not a key file in the ledger folder"),
    ({"author": "someone-else"}, "not on the ledger folder's approver list"),
    ({"requesting_agent": "someone-else"}, "not on the ledger folder's approver list"),
])
def test_the_tools_refuse_a_row_that_breaks_their_rules(tmp_path, cells, needle):
    root = make_repo(tmp_path)
    act = _request(root)
    _append(root, action_reviewed=act, **{k: (act if v == "ACTION" else v) for k, v in cells.items()})
    fake = FakeVerifier("cleared")
    st = _state(root, verifier=fake)
    assert st.state == "UNCLEARED" and needle in st.reason and fake.calls == 0


def test_a_verified_conditional_pass_reaches_the_verifier(tmp_path):
    root = make_repo(tmp_path)
    act = _request(root)
    _append(root, action_reviewed=act, verdict="CONDITIONAL PASS", conditions_verified="verified")
    assert _state(root).state == "CLEARED"


def test_the_newest_row_for_the_action_must_name_it_exactly(tmp_path):
    """Ids are matched across separators, so a suffixed id is the latest row for the action; the tools then require
    the exact action (@security case 46: actions are compared exactly, case included)."""
    root = make_repo(tmp_path)
    act = _request(root)
    _append(root, action_reviewed=act)
    _append(root, action_reviewed=act + "-later")
    st = _state(root)
    assert st.state == "UNCLEARED" and "not exactly the action" in st.reason
    root2 = make_repo(tmp_path / "b")
    act2 = _request(root2)
    _append(root2, action_reviewed=act2.upper())
    assert "not exactly the action" in _state(root2).reason


def test_a_row_for_a_study_id_that_extends_this_one_never_decides(tmp_path):
    """A PASS for study ``tidebell-survey-2`` (same gate, even the same manifest hash) is not this study's: the row
    that decides must name exactly the action the tools computed, and the verifier is never asked about it."""
    root = make_repo(tmp_path)
    act = _request(root)
    other = act.replace(f"/{STUDY_ID}:", f"/{STUDY_ID}-2:")
    _append(root, action_reviewed=other)
    fake = FakeVerifier("cleared")
    st = _state(root, verifier=fake)
    assert st.state == "UNCLEARED" and fake.calls == 0
    _append(root, action_reviewed=act)
    _append(root, action_reviewed=other)
    fake = FakeVerifier("cleared")
    assert _state(root, verifier=fake).state == "CLEARED" and fake.actions == [act]  # only ever the exact action


def test_a_retraction_never_restores_an_older_sign_off(tmp_path):
    """After a retraction no earlier permission survives: PASS, HALT, HALT-RETRACTED leaves the HALT deciding, and
    agentteams is never asked; only a new PASS after the retraction can clear."""
    root = make_repo(tmp_path)
    act = _request(root)
    _append(root, action_reviewed=act)
    _append(root, action_reviewed=act, verdict="HALT")
    _append(root, action_reviewed=act, verdict="HALT-RETRACTED", evidence="lifted")
    fake = FakeVerifier("cleared")
    st = _state(root, verifier=fake)
    assert st.state == "UNCLEARED" and fake.calls == 0


def test_a_retraction_row_is_skipped_and_the_halt_behind_it_decides(tmp_path):
    root = make_repo(tmp_path)
    act = _request(root)
    _append(root, action_reviewed=act)
    _append(root, action_reviewed=act, verdict="HALT")
    _append(root, action_reviewed=act, verdict="HALT-RETRACTED", evidence="lifted")
    assert "is a HALT" in _state(root).reason
    _append(root, action_reviewed=act)
    assert _state(root).state == "CLEARED"


@pytest.mark.parametrize("scheme", ["", "hmac", "ED25519 "])
def test_every_row_of_the_folder_log_must_be_ed25519(tmp_path, scheme):
    """Operator decision Q5: a shared-secret (or unlabelled) row anywhere makes the folder malformed."""
    root = make_repo(tmp_path)
    act = _request(root)
    _append(root, action_reviewed="something-else", sig_scheme=scheme)
    _append(root, action_reviewed=act)
    study = _study(root)
    assert "ledger-scheme" in {f.rule for f in ledger_mod.check_ledger(study).findings}
    assert _state(root).state == "UNAVAILABLE"
    assert run(survey_validate, "--root", str(root), "tidebell")[0] == 1
    assert run(survey_status, "--root", str(root), "tidebell")[0] == 1


def test_a_log_with_an_extra_column_is_malformed(tmp_path):
    """The header's set of columns has no ``consumed`` column, so such a log is refused; a check spends nothing (6.2,
    lines 852 and 889)."""
    root = make_repo(tmp_path)
    log = _refs(root) / "security-decisions.log.csv"
    log.write_text(log.read_text().rstrip("\n") + ",consumed\n")
    assert "ledger-log" in {f.rule for f in ledger_mod.check_ledger(_study(root)).findings}


# --------------------------------------------------------------------------- the interim family-HALT scan (Q1)
@pytest.mark.parametrize("where,action,blocked", [
    (".github/agents", "survey-signoff", ALL),
    (".claude/agents", "Survey_Signoff/s0", {"S0"}),
    (".codex/agents", " SURVEY-SIGNOFF/S5 ", {"S5"}),
    (".github/agents", "survey.signoff", ALL),
    (".github/agents", "survey-signoffs", ALL),  # the squashed id contains the family name
    # @security S1: ids that extend a family name, letter case, format characters, fullwidth letters, separators
    (".github/agents", "survey-signoff:freeze", ALL),
    (".github/agents", "survey-signoff/S0-2026", {"S0"}),
    (".github/agents", "freeze-survey-signoff", ALL),
    (".github/agents", "Survey-SignOff", ALL),
    (".github/agents", "survey-signOff/S0", {"S0"}),
    (".github/agents", "SurveySignoff/S5:hold", {"S5"}),
    (".github/agents", "sur\u200bvey-signoff", ALL),
    (".github/agents", "\uff53\uff55\uff52\uff56\uff45\uff59-signoff/\uff33\uff16", {"S6"}),
    (".github/agents", "  Freeze_SURVEY  signoff  ", ALL),
    (".github/agents", "survey / signoff : s5 . hold", {"S5"}),
    # a study's own scope or action is exempt (agentteams' check in the child judges it) ...
    (".github/agents", "survey-signoff/S0/tidebell-survey", set()),
    (".github/agents", "survey-signoff/S0/other-study", set()),
    (".github/agents", "survey-signoff/S0/tidebell-survey:sha256-" + "ab" * 32, set()),
    # ... and only exactly that: anything else after a colon, or another spelling, is a family HALT
    (".github/agents", "survey-signoff/S0/tidebell-survey:hold", {"S0"}),
    (".github/agents", "SURVEY-SIGNOFF/S0/tidebell-survey:sha256-" + "ab" * 32, {"S0"}),
    # @security B1: the exemption is decided on the raw cell, so a padded study scope is a family HALT
    (".github/agents", "survey-signoff/S0/tidebell-survey\u3000", {"S0"}),
    (".github/agents", "survey-signoff/S0/tidebell-survey ", {"S0"}),
    (".github/agents", "survey-signoff/S0/tidebell-survey\n", {"S0"}),
    (".github/agents", " survey-signoff/S0/tidebell-survey", {"S0"}),
    (".github/agents", "survey-signoff/S0/tidebell-survey\r", {"S0"}),
    (".github/agents", "survey-signoff/S0/tidebell-survey\t", {"S0"}),
    (".github/agents", "\tsurvey-signoff/S0/tidebell-survey", {"S0"}),
    # @security A3: a combining mark, decomposed or precomposed, does not hide the family name
    (".github/agents", "su\u0308rvey-signoff", ALL),
    (".github/agents", "s\u00fcrvey-signoff", ALL),
])
def test_a_family_halt_in_any_scanned_log_blocks_the_gates_it_names(tmp_path, where, action, blocked):
    root = make_repo(tmp_path)
    for g in ("S0", "S5", "S6"):
        _request(root, g)
    _team_log(root, where, [f'2026-11-25,security,"{action}",HALT,x,',
                            f'2026-11-25,security,"{action}",HALT-RETRACTED,lifted,'])  # a retraction never counts
    got = {g for g in ("S0", "S5", "S6") if _state(root, g).state == "UNAVAILABLE"}
    assert got == blocked
    for g in blocked:
        assert "a retraction does not count until agentteams offers a public call" in _state(root, g).reason


def test_a_family_halt_in_the_other_column_schema_or_the_parent_team_binds(tmp_path):
    root = make_repo(tmp_path)
    _request(root)
    _team_log(root, "governance/team", ["2026-11-25,x,1,survey-signoff/S0,halt,,,,owner"],
              header="date,plan_slug,step,decision,status,conditions,conditions_verified,evidence,owner")
    (_refs(root) / "agent-privilege.json").write_text(json.dumps({"parent_team": "governance/team"}))
    assert _state(root).state == "UNAVAILABLE"


def test_a_family_halt_in_the_folder_log_binds(tmp_path):
    root = make_repo(tmp_path)
    act = _request(root)
    _append(root, action_reviewed=act)
    _append(root, action_reviewed="survey-signoff/S0", verdict="HALT")
    assert _state(root).state == "UNAVAILABLE"


@pytest.mark.parametrize("content", [b'action_reviewed,verdict\n"open quote,HALT\n', b"a,b\n1,2,3\n", b"\xff\xfe\n",
                                     b"x,y\n1,2\n"])
def test_a_team_log_that_cannot_be_read_leaves_every_gate_unavailable(tmp_path, content):
    root = make_repo(tmp_path)
    _request(root)
    refs = root / ".github/agents/references"
    refs.mkdir(parents=True)
    (refs / "security-decisions.log.csv").write_bytes(content)
    st = _state(root)
    assert st.state == "UNAVAILABLE" and "cannot be read for HALTs" in st.reason
    assert run(survey_status, "--root", str(root), "tidebell")[0] == 0  # a reason, not a malformed ledger


def test_more_than_one_git_root_above_the_folder_is_unavailable(tmp_path):
    """@security case 39."""
    git_init(tmp_path)  # an enclosing repository above the study's
    root = make_repo(tmp_path)
    _request(root)
    st = _state(root)
    assert st.state == "UNAVAILABLE" and "2 git roots enclose the ledger folder" in st.reason


# --------------------------------------------------------------------------- the child's answer and environment
def _line(**over):
    info = {"version": "1.3.0", "file": os.path.join(sys.prefix, "lib", "site-packages", "agentteams", "__init__.py"),
            "purelib": os.path.join(sys.prefix, "lib", "site-packages"), "prefix": sys.prefix, "cleared": True,
            "action": "A"}
    info.update(over)
    return (json.dumps(info) + "\n").encode()


@pytest.mark.parametrize("returncode,stdout,outcome", [
    (0, _line(), verify.CLEARED),
    (0, _line(cleared=False), verify.NOT_CLEARED),
    (1, _line(), verify.UNAVAILABLE),
    (None, "could not start", verify.UNAVAILABLE),
    (0, _line() + _line(), verify.UNAVAILABLE),
    (0, b"", verify.UNAVAILABLE),
    (0, b"cleared\n", verify.UNAVAILABLE),
    (0, b"[1]\n", verify.UNAVAILABLE),
    (0, _line(cleared="yes"), verify.UNAVAILABLE),
    (0, _line(version="1.2.9"), verify.UNAVAILABLE),
    (0, _line(version="1.3.0.dev1"), verify.UNAVAILABLE),
    (0, _line(file="/elsewhere/agentteams/__init__.py"), verify.UNAVAILABLE),
    (0, _line(file=os.path.join(sys.prefix, "lib", "site-packages", "x", "agentteams", "__init__.py")),
     verify.UNAVAILABLE),  # S4: under purelib is not enough; exactly <purelib>/agentteams/__init__.py
    (0, _line(file=os.path.join(sys.prefix, "lib", "site-packages", "agentteams", "cli", "__init__.py")),
     verify.UNAVAILABLE),
    (0, _line(prefix="/another/env"), verify.UNAVAILABLE),
    (0, _line(action="B"), verify.UNAVAILABLE),
    (0, b"x" * (verify.MAX_STDOUT + 1), verify.UNAVAILABLE),
])
def test_only_one_well_formed_answer_for_the_exact_action_clears(returncode, stdout, outcome):
    assert verify.interpret(returncode, stdout, "A").outcome == outcome


def test_the_childs_environment_is_an_allowlist(monkeypatch):
    monkeypatch.setenv("AGENTTEAMS_DECISION_SIGNING_KEY", "s" * 64)
    monkeypatch.setenv("XDG_CONFIG_HOME", "/x")
    monkeypatch.setenv("GIT_DIR", "/x")
    env = verify.child_env("/fresh-empty-home")
    assert env == {"PATH": verify.CHILD_PATH, "LC_ALL": "C", "HOME": "/fresh-empty-home", "TMPDIR": "/fresh-empty-home"}


def test_the_child_snippet_calls_only_the_public_check():
    assert "check_file_clearance" in verify.CHILD and "clearance_action" in verify.CHILD
    import re
    assert not re.search(r"\._[a-z]", verify.CHILD)  # no private name (dunders such as __version__ are public)


def test_the_child_runs_isolated_with_an_empty_home(tmp_path, monkeypatch):
    """The real child, with the snippet swapped for one that reports its environment."""
    monkeypatch.setattr(verify, "CHILD", "import json, os, sys; print(json.dumps({'env': dict(os.environ), "
                                         "'home': os.listdir(os.environ['HOME']), 'flags': sys.flags.isolated, "
                                         "'nobytecode': sys.flags.dont_write_bytecode}))")
    monkeypatch.setenv("AGENTTEAMS_DECISION_SIGNING_KEY", "s" * 64)
    code, out = verify.run_child(tmp_path, tmp_path, "scope", tmp_path / "m.json")
    seen = json.loads(out)
    assert code == 0 and seen["home"] == [] and seen["flags"] == 1 and seen["nobytecode"] == 1  # -B (T2)
    assert not any(k.startswith(("AGENTTEAMS_", "XDG_", "GIT_")) for k in seen["env"])
    assert not os.path.exists(seen["env"]["HOME"])  # removed afterwards


def test_the_child_is_started_with_minus_b_and_minus_i(tmp_path, monkeypatch):
    """T2: ``-I`` does not imply ``-B``; the child must not write ``__pycache__``."""
    seen = {}

    class Stop(Exception):
        pass

    def fake_popen(argv, **kwargs):
        seen["argv"] = argv
        raise Stop

    monkeypatch.setattr(verify.subprocess, "Popen", fake_popen)
    with pytest.raises(Stop):
        verify.run_child(tmp_path, tmp_path, "scope", tmp_path / "m.json")
    assert seen["argv"][:4] == [sys.executable, "-B", "-I", "-c"]


def test_the_childs_stdout_is_read_through_a_bounded_read(tmp_path, monkeypatch):
    """S5: a child that prints without end is stopped at the cap, and the answer is refused."""
    monkeypatch.setattr(verify, "CHILD", "import sys\nwhile True: sys.stdout.write('x' * 65536)")
    code, out = verify.run_child(tmp_path, tmp_path, "scope", tmp_path / "m.json")
    assert len(out) == verify.MAX_STDOUT + 1
    assert verify.interpret(code, out, "A").outcome == verify.UNAVAILABLE


def test_a_grandchild_holding_stdout_open_is_stopped_with_its_group(tmp_path, monkeypatch):
    """S3: the child runs in a session of its own; on a timeout the whole group is stopped, so a grandchild that
    keeps stdout open cannot hang the check, and the answer is UNAVAILABLE."""
    monkeypatch.setattr(verify, "TIMEOUT_SECONDS", 2)
    monkeypatch.setattr(verify, "CHILD", "import subprocess, sys\n"
                                         "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
                                         "print('{}')")
    code, out = verify.run_child(tmp_path, tmp_path, "scope", tmp_path / "m.json")
    assert code is None and "did not finish" in out
    assert verify.interpret(code, out, "A").outcome == verify.UNAVAILABLE


def test_a_log_that_cannot_be_read_is_reported_without_its_path(tmp_path):
    """S4: an OS error is reported by its reason, never with the path it names."""
    if os.geteuid() == 0:
        pytest.skip("root reads a file whatever its mode")
    root = make_repo(tmp_path)
    _request(root)
    _team_log(root, ".github/agents", ["2026-11-25,security,x,PASS,,"])
    log = root / ".github/agents/references/security-decisions.log.csv"
    log.chmod(0)
    try:
        st = _state(root)
        out = run(survey_status, "--root", str(root), "tidebell")[1]
    finally:
        log.chmod(0o644)
    assert st.state == "UNAVAILABLE" and "Permission denied" in st.reason
    assert str(tmp_path) not in st.reason and str(tmp_path) not in out


def test_the_verifier_location_never_shows_a_home_path(tmp_path):
    inside = verify.location({"file": str(tmp_path / ".venv/lib/site-packages/agentteams/__init__.py"),
                              "prefix": str(tmp_path / ".venv")}, tmp_path)
    assert inside == ("inside the work tree: .venv/lib/site-packages/agentteams/__init__.py; its interpreter is "
                      "inside the work tree")  # S6
    outside = verify.location({"file": "/somewhere/home/u/env/lib/python3.13/site-packages/agentteams/__init__.py",
                               "prefix": "/somewhere/home/u/env"}, tmp_path)
    assert outside == ("outside the work tree: site-packages/agentteams/__init__.py; its interpreter is outside the "
                       "work tree")


# --------------------------------------------------------------------------- stages (6.1; operator decision Q9)
@pytest.mark.parametrize("state,enforce,expected", [
    ("CLEARED", "blocking", "refuses"), ("CLEARED", "build-only", "refuses"),
    ("UNAVAILABLE", "build-only", "refuses"), ("UNCLEARED", "blocking", "refuses"),
])
def test_a_malformed_sign_off_folder_refuses_every_gated_stage(state, enforce, expected):
    assert gates.stage_decision(state, enforce, True, False, folder_malformed=True)[0] == expected


def test_require_gate_records_the_4_6_entry(tmp_path):
    root = make_repo(tmp_path)
    study = _study(root)
    led = ledger_mod.check_ledger(study)
    decision, record, _ = gates.require_gate(study, "S6", led, FakeVerifier())
    assert decision == "runs" and record["state"] == "UNCLEARED" and record["mode"] == "retroactive"
    assert record["enforce"] == "build-only" and len(record["manifest_sha256"]) == 64
    (_refs(root) / "security-waivers.log.csv").write_text("")
    led = ledger_mod.check_ledger(study)
    assert gates.require_gate(study, "S6", led, FakeVerifier())[0] == "refuses"  # Q9
    assert gates.require_gate(study, "S8", led, FakeVerifier())[:2] == ("refuses", {"state": "NOT DECLARED",
                                                                                    "mode": "", "enforce": ""})


# --------------------------------------------------------------------------- the commands' output
def test_status_escapes_every_value_from_a_log(tmp_path):
    """@security case 45: a newline or an escape sequence in a log value cannot forge a line or reach the terminal."""
    root = make_repo(tmp_path)
    act = _request(root)
    _append(root, action_reviewed=act, author="evil\nS0: CLEARED\x1b[2J")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = survey_status.main(["--root", str(root), "tidebell"], verifier=FakeVerifier("cleared"))
    out = buf.getvalue()
    assert code == 0 and "\x1b" not in out
    assert "S0: CLEARED" not in out.splitlines()
    # the author as agentteams reads it, lower-cased, quoted with q() (repr escapes the line feed and the escape)
    assert "'evil\\ns0: cleared\\x1b[2j'" in out


def test_status_prints_the_limit_the_gaps_and_the_verifier(tmp_path):
    root = make_repo(tmp_path)
    out = run(survey_status, "--root", str(root), "tidebell")[1]
    assert "it does not prove who put the key there" in out and "binds the manifest's bytes, not a repository" in out
    assert "no tool can detect every edit to a decisions log's history" in out
    assert "verifier: " in out and str(tmp_path) not in out


def test_manifest_prints_the_signing_commands_with_placeholders(tmp_path):
    root = make_repo(tmp_path)
    code, out, _ = run(survey_manifest, "--root", str(root), "tidebell", "S0")
    assert code == 0
    assert (f"sign: AGENTTEAMS_DECISION_ED25519_KEYFILE=<operator key file> agentteams --sign-decision <spec.json> "
            f"--output {LEDGER}") in out
    spec = json.loads(next(line for line in out.splitlines() if line.startswith("  {")))
    assert spec["action_reviewed"].startswith(f"survey-signoff/S0/{STUDY_ID}:sha256-") and spec["key_id"].startswith("<")
    assert "--confirm-review-sha256" in out and "never pass --allow-checkout-signing" in out
    assert str(tmp_path) not in out and os.path.expanduser("~") not in out


def test_validate_does_not_run_agentteams(tmp_path):
    root = make_repo(tmp_path)
    act = _request(root)
    _append(root, action_reviewed=act)
    assert "survey-validate does not verify" in verify.NotRun().probe()
    assert run(survey_validate, "--root", str(root), "tidebell")[0] == 0


def test_safe_escapes_controls_and_separators():
    assert core.safe("a\nb\x1b\x7f\x9b\u2028é") == "a\\x0ab\\x1b\\x7f\\x9b\\u2028é"


# --------------------------------------------------------------------------- signing: the real child (local only)
@pytest.fixture
def signed(tmp_path):
    """A study whose S0 request is signed with a throwaway key: (root, action, private PEM)."""
    from survey_signing import new_key, require_signing, sign_row
    require_signing()
    root = make_repo(tmp_path)
    pem = new_key(root / LEDGER)
    act = _request(root)
    sign_row(root / LEDGER, pem, act)
    return root, act, pem


def _real(root, gate="S0"):
    return _state(root, gate, verifier=verify.Verifier())


def test_signed_a_valid_ed25519_row_clears_through_agentteams(signed):
    root, _act, _pem = signed
    st = _real(root)
    assert st.state == "CLEARED", st.reason
    info = st.evidence["verifier"]
    assert info["cleared"] is True and verify.parse_version(info["version"]) >= (1, 3, 0)
    code, out, _ = run(survey_status, "--root", str(root), "tidebell")
    assert code == 0 and "S0: CLEARED" in out and "verified by agentteams" in out and "the work tree" in out
    study = _study(root)
    assert gates.require_gate(study, "S0", None, verify.Verifier())[0] == "runs"


def test_signed_a_swapped_key_is_not_cleared_by_agentteams(signed):
    from survey_signing import new_key
    root, _act, _pem = signed
    new_key(root / LEDGER)  # same key id, another key
    st = _real(root)
    assert st.state == "UNCLEARED" and st.reason == gates.NOT_CLEARED


def test_signed_a_covered_file_edited_after_signing_unclears(signed):
    root, _act, _pem = signed
    (root / STUDY_REL / "rules" / "forbidden.txt").write_text("an edit\n")
    assert "changed since the request" in _real(root).reason
    _request(root)
    assert "no row in the ledger log names this action" in _real(root).reason


@pytest.mark.parametrize("halted", ["ACTION", "SCOPE", "EXTENDED"])
def test_signed_a_halt_in_a_team_log_binds_through_agentteams(signed, halted):
    """A HALT on the action or the scope in a generated team log; and on a study id that extends this one (Q2)."""
    root, act, _pem = signed
    target = {"ACTION": act, "SCOPE": f"survey-signoff/S0/{STUDY_ID}",
              "EXTENDED": f"survey-signoff/S0/{STUDY_ID}-2"}[halted]
    _team_log(root, ".github/agents", [f"2026-11-25,security,{target},HALT,x,"])
    st = _real(root)
    assert st.state == "UNCLEARED" and "demo-2 against demo" in st.reason


def test_signed_a_retracted_halt_on_the_action_needs_a_new_pass(signed):
    from survey_signing import sign_row
    root, act, pem = signed
    sign_row(root / LEDGER, pem, act, verdict="HALT")
    assert "is a HALT" in _real(root).reason
    sign_row(root / LEDGER, pem, act, verdict="HALT-RETRACTED", evidence="the concern was resolved")
    assert _real(root).state == "UNCLEARED"
    sign_row(root / LEDGER, pem, act)
    assert _real(root).state == "CLEARED"


def test_signed_a_row_by_a_key_not_in_the_folder_never_reaches_agentteams(signed):
    root, _act, _pem = signed
    (root / LEDGER / "references" / "authorized-verify-keys" / "op-test.pub.pem").rename(
        root / LEDGER / "references" / "authorized-verify-keys" / "op-renamed.pub.pem")
    assert "not a key file in the ledger folder" in _real(root).reason


def test_signed_a_valid_pass_for_a_study_that_extends_this_one_never_clears_it(signed):
    """The row that decides must name exactly the action the tools computed; a signed PASS for ``tidebell-survey-2``
    never clears ``tidebell-survey``."""
    from survey_signing import new_key, sign_row
    root, act, _pem = signed
    log = root / LEDGER / "references" / "security-decisions.log.csv"
    log.write_text(",".join(ledger_mod.LOG_HEADER) + "\n")  # only the other study's row
    pem = new_key(root / LEDGER)
    sign_row(root / LEDGER, pem, act.replace(f"/{STUDY_ID}:", f"/{STUDY_ID}-2:"))
    st = _real(root)
    assert st.state == "UNCLEARED" and "no row in the ledger log names this action" in st.reason


@pytest.mark.parametrize("where", [".claude/agents", ".github/agents", ".codex/agents", ".goose/recipes",
                                   ".grok/agents", "parent_team"])
@pytest.mark.parametrize("target", ["ACTION", "SCOPE"])
def test_signed_an_exempt_halt_binds_through_agentteams_in_every_scanned_log(signed, where, target):
    """@security A1: a HALT on this study's own scope or action is exempt from the family scan and left to
    agentteams' check in the child; it blocks from each team location the scan covers and from ``parent_team``."""
    root, act, _pem = signed
    halted = act if target == "ACTION" else f"survey-signoff/S0/{STUDY_ID}"
    rel = "governance/team" if where == "parent_team" else where
    _team_log(root, rel, [f"2026-11-25,security,{halted},HALT,x,"])
    if where == "parent_team":
        (_refs(root) / "agent-privilege.json").write_text(json.dumps({"parent_team": rel}))
    assert ledger_mod.check_ledger(_study(root)).family_halts == {}  # exempt: not the tools' scan
    st = _real(root)
    assert st.state == "UNCLEARED" and st.reason == gates.NOT_CLEARED


def _reorder_log(log, order):
    """Rewrite a log with its columns in *order*, every row's cells moved with their column."""
    rows = list(csv.DictReader(io.StringIO(log.read_text(encoding="utf-8"), newline="")))
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=order, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    log.write_text(buf.getvalue(), encoding="utf-8")


def test_a_row_in_a_log_with_its_columns_reordered_is_read_by_name(tmp_path):
    """Every rule reads a row by column name: a reordered log decides exactly as the written order does."""
    root = make_repo(tmp_path)
    act = _request(root)
    _append(root, action_reviewed=act)
    _append(root, action_reviewed="survey-signoff/S5", verdict="HALT")
    before = {g: _state(root, g).state for g in ("S0", "S5")}
    _reorder_log(_refs(root) / "security-decisions.log.csv", list(ledger_mod.LOG_HEADER)[::-1])
    assert {g: _state(root, g).state for g in ("S0", "S5")} == before == {"S0": "CLEARED", "S5": "UNAVAILABLE"}
    lines = (_refs(root) / "security-decisions.log.csv").read_text().splitlines()
    assert lines[0].startswith("signature,prev_digest")


def test_signed_a_signed_row_in_a_reordered_log_still_clears(signed):
    """Operator decision, 2026-11-25: a log with agentteams' columns in another order is well-formed; agentteams'
    public log check and the child read it as written, so a valid row still clears."""
    root, _act, _pem = signed
    log = root / LEDGER / "references" / "security-decisions.log.csv"
    _reorder_log(log, list(ledger_mod.LOG_HEADER)[7:] + list(ledger_mod.LOG_HEADER)[:7])
    from agentteams.governance_logs import check_log
    assert check_log(log) == []
    st = _real(root)
    assert st.state == "CLEARED", st.reason

