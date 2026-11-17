"""Informational doctor lines: they report, and never fail doctor."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from researchteam import _doctor_cmd, _update_cmd


def _collect():
    lines: list[tuple[str, str]] = []
    return lines, (lambda m: lines.append(("ok", m))), (lambda m: lines.append(("warn", m)))


def test_pandoc_found_reports_its_version(monkeypatch):
    monkeypatch.setattr(_doctor_cmd.shutil, "which", lambda name: "/usr/bin/pandoc")
    monkeypatch.setattr(_doctor_cmd.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
        a[0], 0, stdout="pandoc 3.1.11\nFeatures: +server\n", stderr=""))
    lines, ok, warn = _collect()
    _doctor_cmd._check_pandoc(ok, warn)
    assert lines == [("ok", "pandoc 3.1.11 (/usr/bin/pandoc)")]


def test_pandoc_missing_is_a_warning(monkeypatch):
    monkeypatch.setattr(_doctor_cmd.shutil, "which", lambda name: None)
    lines, ok, warn = _collect()
    _doctor_cmd._check_pandoc(ok, warn)
    assert len(lines) == 1 and lines[0][0] == "warn" and "compile/convert" in lines[0][1]


def test_doctor_does_not_fail_without_pandoc(tmp_path, monkeypatch, capsys):
    (tmp_path / ".researchteam").write_text("layer1 = off\n")
    monkeypatch.setattr(_update_cmd, "_resolve_agentteams", lambda: (None, "nowhere"))
    monkeypatch.setattr(_doctor_cmd.shutil, "which", lambda name: None)
    _doctor_cmd.run_doctor(tmp_path)  # must not raise SystemExit
    out = capsys.readouterr()
    assert "pandoc not found on PATH" in out.out and "[FAIL]" not in out.err


SCRIPTS = _doctor_cmd.SCHOLARLY_CAPABILITY_SCRIPTS


@pytest.mark.parametrize("brief", [None, '{"layer2_profile": "scholarly"}'])
def test_scholarly_tooling_present_and_missing(tmp_path, brief):
    if brief:
        (tmp_path / "brief.json").write_text(brief)
    (tmp_path / "scripts").mkdir()
    (tmp_path / SCRIPTS[0]).write_text("#!/bin/sh\n")
    lines, ok, warn = _collect()
    _doctor_cmd._check_scholarly_tooling(tmp_path, ok, warn)
    assert lines[0] == ("ok", f"scholarly tooling: {SCRIPTS[0]} present.")
    assert lines[1][0] == "warn" and SCRIPTS[1] in lines[1][1] and "researchteam update" in lines[1][1]


def test_generic_profile_is_not_warned(tmp_path):
    (tmp_path / "brief.json").write_text('{"layer2_profile": "generic"}')
    lines, ok, warn = _collect()
    _doctor_cmd._check_scholarly_tooling(tmp_path, ok, warn)
    assert [kind for kind, _ in lines] == ["ok"] * len(SCRIPTS) and all("not expected" in m for _, m in lines)


def test_doctor_does_not_fail_without_scholarly_tooling(tmp_path, monkeypatch, capsys):
    (tmp_path / ".researchteam").write_text("layer1 = off\n")
    monkeypatch.setattr(_update_cmd, "_resolve_agentteams", lambda: (None, "nowhere"))
    _doctor_cmd.run_doctor(tmp_path)  # must not raise SystemExit
    out = capsys.readouterr()
    assert f"{SCRIPTS[0]} missing" in out.out and "[FAIL]" not in out.err


# --------------------------------------------------------------------------- term index
ROOT = Path(__file__).resolve().parent.parent
HOOK = {"type": "command", "command": 'python3 "$CLAUDE_PROJECT_DIR/scripts/build_term_index.py" hook'}


def _term_repo(tmp_path, register=True, text="A term register.\n"):
    (tmp_path / "scripts").mkdir()
    for name in ("term_index_engine.py", "build_term_index.py", "check_term_index.py"):
        shutil.copy(ROOT / "scripts" / name, tmp_path / "scripts")
    if register:
        proj = tmp_path / "Projects" / "Demo"
        (proj / "terminology").mkdir(parents=True)
        (proj / "01-review.md").write_text(text)
        (proj / "terminology" / "terms.json").write_text(json.dumps({
            "schema": "researchteam-term-register",
            "terms": [{"id": "t", "label": "term register", "definition": "d", "source": "project definition"}]}))
    return tmp_path


def _settings(root, **events):
    (root / ".claude").mkdir(exist_ok=True)
    (root / ".claude" / "settings.json").write_text(json.dumps(
        {"hooks": {event: [{"hooks": [HOOK]}] for event, on in events.items() if on}}))


def _term_lines(root):
    lines, ok, warn = _collect()
    _doctor_cmd._check_term_index(root, ok, warn)
    return lines


def test_term_index_check_is_silent_without_the_scripts_and_brief_without_registers(tmp_path):
    assert _term_lines(tmp_path) == []  # a generic-profile repository
    lines = _term_lines(_term_repo(tmp_path, register=False))
    assert lines == [("ok", "term index: no project has a term register yet (docs/term-index-protocol.md).")]


def test_term_index_check_reports_the_gate_the_hooks_and_ci(tmp_path):
    root = _term_repo(tmp_path)
    lines = _term_lines(root)  # no index built, no hooks, no workflow
    assert [kind for kind, _ in lines] == ["warn", "warn", "warn"]
    assert "DEFECT: 1" in lines[0][1] and "term-check" in lines[0][1]
    assert "settings.terms.example.json" in lines[1][1]
    assert "workflow-sync --workflow validate" in lines[2][1]

    built = subprocess.run([sys.executable, "-B", str(root / "scripts" / "build_term_index.py"), "build"],
                           capture_output=True, text=True, env={"RT_ROOT": str(root)})
    assert built.returncode == 0, built.stdout + built.stderr
    _settings(root, PostToolUse=True)
    lines = _term_lines(root)
    assert lines[0][0] == "ok" and "registers checked: 1" in lines[0][1] and "DEFECT: 0" in lines[0][1]
    assert lines[1][0] == "warn" and "not at SessionStart" in lines[1][1]

    _settings(root, PostToolUse=True, SessionStart=True)
    workflows = root / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("steps:\n  # run: bash scripts/claude_researchteam_bridge.sh validate\n")
    lines = _term_lines(root)
    assert [kind for kind, _ in lines] == ["ok", "ok", "warn"]  # a commented-out step does not count
    (workflows / "ci.yml").write_text("steps:\n  - run: bash scripts/claude_researchteam_bridge.sh validate\n")
    assert [kind for kind, _ in _term_lines(root)] == ["ok", "ok", "ok"]


def test_term_index_check_ignores_a_callers_root_and_advisory_switch(tmp_path, monkeypatch):
    root = _term_repo(tmp_path)
    monkeypatch.setenv("RT_ROOT", str(tmp_path / "elsewhere"))
    monkeypatch.setenv("TERM_INDEX_ADVISORY", "1")
    lines = _term_lines(root)
    assert lines[0][0] == "warn" and "DEFECT: 1" in lines[0][1]


def test_update_nudges_only_while_a_register_exists_and_the_hooks_are_not_wired(tmp_path):
    assert _update_cmd._term_index_hook_note(tmp_path) == ""                       # no scripts
    root = _term_repo(tmp_path, register=False)
    assert _update_cmd._term_index_hook_note(root) == ""                           # no register yet
    proj = root / "Projects" / "Group" / "Nested" / "terminology"
    proj.mkdir(parents=True)
    (proj / "terms.json").write_text("{}")
    note = _update_cmd._term_index_hook_note(root)
    assert "settings.terms.example.json" in note and "term-build" in note and "outside the sandbox" in note
    _settings(root, SessionStart=True)
    assert _update_cmd._term_index_hook_note(root) != ""                           # SessionStart alone is not enough
    _settings(root, PostToolUse=True)
    assert _update_cmd._term_index_hook_note(root) == ""
    assert _update_cmd._toolchain_hook_installed(root) is False                    # a different script
    (root / ".claude" / "settings.json").write_text("not json")
    assert _update_cmd._term_index_hook_note(root) != ""                           # unreadable settings never raise


def test_doctor_runs_with_a_term_register_and_never_fails_on_it(tmp_path, monkeypatch, capsys):
    root = _term_repo(tmp_path)
    (root / ".researchteam").write_text("layer1 = off\n")
    monkeypatch.setattr(_update_cmd, "_resolve_agentteams", lambda: (None, "nowhere"))
    _doctor_cmd.run_doctor(root)  # a stale index is a warning here, never a SystemExit
    out = capsys.readouterr()
    assert "term index: gate: Projects seen: 1" in out.out and "[FAIL]" not in out.err


def test_term_index_check_takes_its_count_from_the_gate_not_from_a_glob(tmp_path):
    """A required register that is missing fails the gate, so doctor must not say "none yet"."""
    root = _term_repo(tmp_path, register=False)
    (root / "Projects" / "Paper").mkdir(parents=True)
    (root / "Projects" / "Paper" / "01-review.md").write_text("text\n")
    lines = _term_lines(root)
    assert lines == [("ok", "term index: no project has a term register yet (docs/term-index-protocol.md).")]
    (root / ".researchteam").write_text("term_index_require = true\n")
    lines = _term_lines(root)
    assert lines[0][0] == "warn" and "DEFECT: 1" in lines[0][1] and "registers checked: 0" in lines[0][1]
    (root / ".researchteam").unlink()
    foreign = root / "Projects" / "Paper" / "terminology"
    foreign.mkdir()
    (foreign / "terms.json").write_text('{"words": []}')  # not a researchteam register
    assert _term_lines(root)[0] == ("ok", "term index: no project has a term register yet (docs/term-index-protocol.md).")


def test_term_index_check_survives_a_gate_that_cannot_run(tmp_path, monkeypatch):
    root = _term_repo(tmp_path)
    (root / "scripts" / "term_index_engine.py").unlink()  # a broken install
    lines = _term_lines(root)
    assert lines[0][0] == "warn" and "(no summary line)" in lines[0][1]
    for exc in (subprocess.TimeoutExpired("gate", 120), OSError("no interpreter")):
        def boom(*a, _exc=exc, **k):
            raise _exc
        monkeypatch.setattr(_doctor_cmd.subprocess, "run", boom)
        lines = _term_lines(root)
        assert lines[0][0] == "warn" and "could not run" in lines[0][1] and type(exc).__name__ in lines[0][1]


def test_relayed_lines_lose_control_characters(tmp_path):
    root = _term_repo(tmp_path)
    (root / "scripts" / "check_term_index.py").write_text(
        'print("Projects seen: 1  |  registers checked: 1  |  \\x1b[31mDEFECT\\x1b[0m: 0\\x07")\n')
    message = _term_lines(root)[0][1]
    assert "\x1b" not in message and "\x07" not in message and "registers checked: 1" in message


def test_a_workflow_that_is_not_text_does_not_count(tmp_path):
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "a.yml").write_bytes(b"\xff\xfe run: bash scripts/claude_researchteam_bridge.sh validate")
    assert _doctor_cmd._workflow_runs_validate(tmp_path) is False
    (workflows / "b.yaml").write_text("      - run: bash scripts/claude_researchteam_bridge.sh validate\n")
    assert _doctor_cmd._workflow_runs_validate(tmp_path) is True

