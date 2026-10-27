"""Informational doctor lines: they report, and never fail doctor."""
from __future__ import annotations

import subprocess

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
    assert [kind for kind, _ in lines] == ["ok", "ok"] and all("not expected" in m for _, m in lines)


def test_doctor_does_not_fail_without_scholarly_tooling(tmp_path, monkeypatch, capsys):
    (tmp_path / ".researchteam").write_text("layer1 = off\n")
    monkeypatch.setattr(_update_cmd, "_resolve_agentteams", lambda: (None, "nowhere"))
    _doctor_cmd.run_doctor(tmp_path)  # must not raise SystemExit
    out = capsys.readouterr()
    assert f"{SCRIPTS[0]} missing" in out.out and "[FAIL]" not in out.err
