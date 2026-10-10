"""Toolchain pinning (OrthodoxLLM Item 3): toolchain.lock, check/bootstrap scripts, resolution, nudges."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from researchteam import _update_cmd
from researchteam._manifest import FRAMEWORK_MANAGED_FILES, managed_files_for

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location("check_toolchain", ROOT / "scripts" / "check_toolchain.py")
ct = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ct)

A, B = "a" * 40, "b" * 40


def _vcs(sha: str, url: str = "https://github.com/jlcatonjr/agentteams.git") -> dict:
    return {"version": "1", "direct_url": {"url": url, "vcs_info": {"vcs": "git", "commit_id": sha}}}


def test_upstream_lock_pins_both_packages_to_full_shas():
    pins = ct.read_lock(str(ROOT / "toolchain.lock"))
    for name in ct.PACKAGES:
        repo, sha = pins[name]
        assert repo == f"jlcatonjr/{name}" and ct._SHA.match(sha), (name, repo, sha)


def test_lock_roundtrip_keeps_orthodoxllm_line_format(tmp_path):
    lock = tmp_path / "toolchain.lock"
    ct.write_lock({"researchteam": ("jlcatonjr/researchteam", A), "agentteams": ("jlcatonjr/agentteams", B)},
                  str(lock))
    lines = [ln for ln in lock.read_text().splitlines() if not ln.startswith("#")]
    assert lines == [f"researchteam=jlcatonjr/researchteam@{A}", f"agentteams=jlcatonjr/agentteams@{B}"]
    assert ct.read_lock(str(lock)) == {"researchteam": ("jlcatonjr/researchteam", A),
                                       "agentteams": ("jlcatonjr/agentteams", B)}


def test_missing_lock_is_advisory(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(ct, "LOCK", str(tmp_path / "toolchain.lock"))
    assert ct.main(["--no-remote"]) == 0
    assert "no toolchain.lock yet" in capsys.readouterr().out


def test_commit_of_variants():
    assert ct.commit_of(_vcs(A)) == (A, "git pin")
    sha, how = ct.commit_of({"direct_url": None})
    assert sha is None and "no commit" in how
    sha, how = ct.commit_of({"direct_url": {"url": "file:///x", "dir_info": {}}})
    assert sha is None and "local folder" in how
    sha, how = ct.commit_of({"direct_url": {"url": "x", "vcs_info": "garbage", "dir_info": "garbage"}})
    assert sha is None  # malformed records never raise


def test_mismatch_is_reported_and_strict_fails(tmp_path, monkeypatch, capsys):
    lock = tmp_path / "toolchain.lock"
    ct.write_lock({"researchteam": ("jlcatonjr/researchteam", A), "agentteams": ("jlcatonjr/agentteams", B)},
                  str(lock))
    monkeypatch.setattr(ct, "LOCK", str(lock))
    monkeypatch.setattr(ct, "installed", lambda py: {"researchteam": _vcs(A), "agentteams": _vcs(A)})
    assert ct.main(["--python", "py", "--no-remote"]) == 0
    out = capsys.readouterr().out
    assert "BEHIND: agentteams: installed aaaaaaa" in out and "pins bbbbbbb" in out
    assert ct.main(["--python", "py", "--no-remote", "--strict"]) == 1


def test_write_lock_records_clean_commits_only(tmp_path, monkeypatch):
    lock = tmp_path / "toolchain.lock"
    monkeypatch.setattr(ct, "LOCK", str(lock))
    rt = _vcs(A, "https://github.com/jlcatonjr/researchteam.git")
    monkeypatch.setattr(ct, "installed", lambda py: {"researchteam": rt, "agentteams": _vcs(B)})
    assert ct.main(["--python", "py", "--write-lock"]) == 0
    assert ct.read_lock() == {"researchteam": ("jlcatonjr/researchteam", A), "agentteams": ("jlcatonjr/agentteams", B)}
    lock.unlink()
    monkeypatch.setattr(ct, "installed", lambda py: {"researchteam": rt, "agentteams": {"direct_url": None}})
    assert ct.main(["--python", "py", "--write-lock"]) == 1 and not lock.exists()


def test_hook_detection_and_update_nudge(tmp_path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "check_toolchain.py").write_text("")
    assert not ct.hook_installed(str(tmp_path)) and not _update_cmd._toolchain_hook_installed(tmp_path)
    assert "settings.toolchain.example.json" in _update_cmd._toolchain_hook_note(tmp_path)
    (tmp_path / ".claude").mkdir()
    shutil.copy(ROOT / ".claude" / "settings.toolchain.example.json", tmp_path / ".claude" / "settings.json")
    assert ct.hook_installed(str(tmp_path)) and _update_cmd._toolchain_hook_installed(tmp_path)
    assert _update_cmd._toolchain_hook_note(tmp_path) == ""
    (tmp_path / ".claude" / "settings.json").write_text("{not json")
    assert not _update_cmd._toolchain_hook_installed(tmp_path)  # unreadable settings never raise


def test_no_nudge_before_the_check_script_arrives(tmp_path):
    assert _update_cmd._toolchain_hook_note(tmp_path) == ""


def test_example_settings_is_valid_and_points_at_the_check():
    data = json.loads((ROOT / ".claude" / "settings.toolchain.example.json").read_text())
    cmd = data["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    assert "scripts/check_toolchain.py" in cmd


def test_toolchain_files_are_managed_for_every_profile():
    new = ["scripts/check_toolchain.py", "scripts/bootstrap_toolchain.sh", ".claude/settings.toolchain.example.json"]
    assert all(f in FRAMEWORK_MANAGED_FILES for f in new)
    assert all(f in managed_files_for("generic") for f in new)
    assert "toolchain.lock" not in managed_files_for(None)  # repo-owned; written by the autosync gate


def test_validator_admits_the_lock(tmp_path):
    env = dict(os.environ, VALIDATION_CHANGED_FILES="toolchain.lock", VALIDATION_SKIP_SCOPE="0")
    r = subprocess.run(["bash", str(ROOT / "scripts" / "validate_agentteams_update.sh")], cwd=tmp_path,
                       env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def _launcher(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\necho agentteams\n")
    path.chmod(0o755)


def test_resolution_prefers_agentteams_beside_the_interpreter(tmp_path, monkeypatch):
    venv_bin, path_bin = tmp_path / "venv" / "bin", tmp_path / "elsewhere"
    _launcher(venv_bin / "agentteams")
    _launcher(path_bin / "agentteams")
    monkeypatch.setattr(sys, "executable", str(venv_bin / "python"))
    monkeypatch.setenv("PATH", f"{path_bin}:/usr/bin:/bin")
    exe, where = _update_cmd._resolve_agentteams()
    assert exe == str(venv_bin / "agentteams") and "beside" in where


def test_resolution_falls_back_to_path_and_says_so(tmp_path, monkeypatch):
    path_bin = tmp_path / "elsewhere"
    _launcher(path_bin / "agentteams")
    monkeypatch.setattr(sys, "executable", str(tmp_path / "venv" / "bin" / "python"))
    monkeypatch.setenv("PATH", f"{path_bin}:/usr/bin:/bin")
    exe, where = _update_cmd._resolve_agentteams()
    assert exe == str(path_bin / "agentteams") and "PATH" in where


@pytest.mark.parametrize("args, expect", [([], "toolchain.lock not found"),
                                          (["--local"], "no local researchteam checkout found")])
def test_bootstrap_refuses_cleanly_without_inputs(tmp_path, args, expect):
    repo = tmp_path / "isolated" / "deep" / "repo"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy(ROOT / "scripts" / "bootstrap_toolchain.sh", repo / "scripts")
    env = {k: v for k, v in os.environ.items() if k not in ("RESEARCHTEAM_SRC", "AGENTTEAMS_SRC")}
    r = subprocess.run(["/bin/bash", str(repo / "scripts" / "bootstrap_toolchain.sh"), *args],
                       env=env, capture_output=True, text=True)
    assert r.returncode == 2 and expect in r.stderr, r.stdout + r.stderr
    assert not (repo / ".venv").exists()  # refuses before creating anything


@pytest.mark.parametrize("first, second", [
    ("#!{py}\n", ""),
    ("#!/usr/bin/env python3\n", ""),
    ("#!/bin/sh\n", "'''exec' \"{py}\" \"$0\" \"$@\"\n"),
])
def test_launcher_interpreter_follows_every_shebang_form(tmp_path, first, second):
    py = shutil.which("python3")
    exe = tmp_path / "researchteam"
    exe.write_text(first.format(py=py) + second.format(py=py) + "print('x')\n")
    assert ct.launcher_interpreter(str(exe)) == py


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", *args], check=True,
                   capture_output=True)


def test_commit_of_editable_checkout_and_dirty_refusal(tmp_path, monkeypatch):
    repo = tmp_path / "agent teams"  # a space, percent-encoded in the file:// URL
    repo.mkdir()
    (repo / "x.py").write_text("x = 1\n")
    _git(repo, "init", "-q")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "x")
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    info = {"direct_url": {"url": repo.as_uri(), "dir_info": {"editable": True}}}
    assert ct.commit_of(info) == (head, f"editable {repo}")
    (repo / "x.py").write_text("x = 2\n")
    sha, how = ct.commit_of(info)
    assert sha == head and how.endswith("(dirty)")
    lock = tmp_path / "toolchain.lock"
    monkeypatch.setattr(ct, "LOCK", str(lock))
    monkeypatch.setattr(ct, "installed", lambda py: {"researchteam": _vcs(A, "https://github.com/jlcatonjr/researchteam"),
                                                     "agentteams": info})
    assert ct.main(["--python", "py", "--write-lock"]) == 1 and not lock.exists()


@pytest.mark.parametrize("repo, sha, expect", [
    ("attacker/agentteams", B, "only jlcatonjr/agentteams is allowed"),
    ("jlcatonjr/agentteams", "main", "not a 40-hex commit"),
])
def test_foreign_or_partial_pins_are_rejected(tmp_path, monkeypatch, capsys, repo, sha, expect):
    lock = tmp_path / "toolchain.lock"
    lock.write_text(f"researchteam=jlcatonjr/researchteam@{A}\nagentteams={repo}@{sha}\n")
    monkeypatch.setattr(ct, "LOCK", str(lock))
    monkeypatch.setattr(ct, "installed", lambda py: {"researchteam": _vcs(A), "agentteams": _vcs(B)})
    assert ct.main(["--python", "py", "--no-remote", "--strict"]) == 1
    assert expect in capsys.readouterr().out
    # --write-lock refuses to record a foreign repository too
    monkeypatch.setattr(ct, "installed", lambda py: {"researchteam": _vcs(A, "https://github.com/jlcatonjr/researchteam"),
                                                     "agentteams": _vcs(B, "https://github.com/attacker/agentteams")})
    assert ct.main(["--python", "py", "--write-lock"]) == 1


def test_upstream_newer_than_pin_is_a_note_not_a_failure(tmp_path, monkeypatch, capsys):
    lock = tmp_path / "toolchain.lock"
    ct.write_lock({"researchteam": ("jlcatonjr/researchteam", A), "agentteams": ("jlcatonjr/agentteams", B)}, str(lock))
    monkeypatch.setattr(ct, "LOCK", str(lock))
    monkeypatch.setattr(ct, "installed", lambda py: {"researchteam": _vcs(A), "agentteams": _vcs(B)})
    monkeypatch.setattr(ct, "remote_main", lambda repo: "c" * 40)
    assert ct.main(["--python", "py", "--strict"]) == 0
    assert "upstream main is ccccccc, newer than the pin" in capsys.readouterr().out


def test_bootstrap_rejects_a_foreign_repository_before_installing(tmp_path):
    repo = tmp_path / "isolated" / "deep" / "repo"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy(ROOT / "scripts" / "bootstrap_toolchain.sh", repo / "scripts")
    (repo / "toolchain.lock").write_text(f"researchteam=jlcatonjr/researchteam@{A}\nagentteams=attacker/agentteams@{B}\n")
    r = subprocess.run(["/bin/bash", str(repo / "scripts" / "bootstrap_toolchain.sh")], capture_output=True, text=True)
    assert r.returncode == 2 and "must be jlcatonjr/agentteams@" in r.stderr, r.stderr
    assert not (repo / ".venv").exists()


def test_doctor_reports_the_toolchain_section(tmp_path, capsys):
    from researchteam._doctor_cmd import _check_toolchain
    (tmp_path / "scripts").mkdir()
    shutil.copy(ROOT / "scripts" / "check_toolchain.py", tmp_path / "scripts")
    seen: list[tuple[str, str]] = []
    _check_toolchain(tmp_path, lambda m: seen.append(("ok", m)), lambda m: seen.append(("warn", m)))
    text = " | ".join(m for _, m in seen)
    assert "no toolchain.lock yet" in text and "not wired to SessionStart" in text
