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
