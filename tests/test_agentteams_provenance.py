"""A layer-1 render runs reviewed agentteams code (researchteam/_agentteams_provenance.py).

Adapted from mathAgents tests/test_refresh_guard.py (PR #24). CA-033: mathAgents' v0.2.6 renders ran an
unrecorded agentteams snapshot that predated the adopted-row fix and dropped every adopted routing row.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from researchteam import _agentteams_provenance, _update_cmd


def g(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", *args], check=True,
                   capture_output=True)


def fake_agentteams(tmp: Path, install: str = "editable", layout: str = "flat", shebang: str = "direct",
                    git_repo: bool = True) -> tuple[Path, Path, Path, dict]:
    """(repo, package dir, launcher, env): a fake agentteams source tree (flat or src/ layout, optionally a git
    checkout with origin/main), dist metadata recording how it was installed (PEP 610: editable, vcs or local
    snapshot), and an `agentteams` launcher using a direct, env-style or pip-trampoline shebang."""
    repo = tmp / "agentteams src"  # a space in the path, deliberately
    root = repo / "src" if layout == "src" else repo
    pkg = root / "agentteams"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (root / "build_team.py").write_text("def main(): pass\n")  # the launcher's entry module (build_team:main)
    if git_repo:
        g(repo, "init", "-q", "-b", "main")
        g(repo, "add", ".")
        g(repo, "commit", "-qm", "init")
        g(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    site = tmp / "site dir"
    info = site / "agentteams-9.9.dist-info"
    info.mkdir(parents=True)
    (info / "METADATA").write_text("Metadata-Version: 2.1\nName: agentteams\nVersion: 9.9\n")
    direct = {"editable": {"url": repo.as_uri(), "dir_info": {"editable": True}},
              "vcs": {"url": "https://github.com/x/agentteams", "vcs_info": {"vcs": "git", "commit_id": "c" * 40}},
              "snapshot": {"url": repo.as_uri(), "dir_info": {}}}[install]
    (info / "direct_url.json").write_text(json.dumps(direct))
    pythonpath = f"{site}:{root}"
    if install != "editable":  # an installed copy lives in site-packages and is listed in the install's RECORD
        (site / "agentteams").mkdir()
        (site / "agentteams" / "__init__.py").write_text("")
        (site / "build_team.py").write_text("def main(): pass\n")
        (info / "RECORD").write_text("agentteams/__init__.py,,\nbuild_team.py,,\nagentteams-9.9.dist-info/METADATA,,\n")
        pythonpath = str(site)
    bin_dir = tmp / "bin"
    bin_dir.mkdir()
    py = sys.executable
    first = {"direct": f"#!{py}\n", "env": "#!/usr/bin/env python3\n",
             "trampoline": f"#!/bin/sh\n'''exec' \"{py}\" \"$0\" \"$@\"\n' '''\n"}[shebang]
    launcher = bin_dir / "agentteams"
    launcher.write_text(first + "print('agentteams 9.9')\n")
    launcher.chmod(0o755)
    path = f"{bin_dir}:{Path(py).parent}:/usr/bin:/bin"  # env-style shebangs resolve python3 from PATH
    return repo, pkg, launcher, {"PATH": path, "PYTHONPATH": pythonpath}


@pytest.fixture
def provenance(monkeypatch, capfd):
    """Run the check against a launcher with the given PATH/PYTHONPATH; return (exit code, stdout, stderr)."""
    def run(launcher: Path, env: dict) -> tuple[int, str, str]:
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        code = _agentteams_provenance.check(str(launcher))
        out, err = capfd.readouterr()
        return code, out, err
    return run


def test_an_editable_checkout_on_main_passes_and_is_named(tmp_path, provenance):
    *_, launcher, env = fake_agentteams(tmp_path)
    code, out, err = provenance(launcher, env)
    assert code == 0 and "editable checkout" in out and "branch main" in out, out + err


def test_an_unmerged_branch_is_refused(tmp_path, provenance):
    repo, pkg, launcher, env = fake_agentteams(tmp_path)
    g(repo, "checkout", "-qb", "someone-elses-branch")
    (pkg / "x.py").write_text("x = 1\n")
    g(repo, "add", ".")
    g(repo, "commit", "-qm", "wip")
    code, _, err = provenance(launcher, env)
    assert code == 1 and "not on origin/main" in err and "someone-elses-branch" in err


def test_edits_and_untracked_modules_are_refused_but_bytecode_is_not(tmp_path, provenance):
    _, pkg, launcher, env = fake_agentteams(tmp_path)
    (pkg / "__pycache__").mkdir()
    (pkg / "__pycache__" / "x.cpython-312.pyc").write_bytes(b"\0")
    assert provenance(launcher, env)[0] == 0
    (pkg / "new_module.py").write_text("y = 2\n")
    code, _, err = provenance(launcher, env)
    assert code == 1 and "new_module.py" in err
    (pkg / "new_module.py").unlink()
    (pkg / "__init__.py").write_text("edited = True\n")
    assert provenance(launcher, env)[0] == 1


def test_a_src_layout_is_checked_where_python_imports_it(tmp_path, provenance):
    _, pkg, launcher, env = fake_agentteams(tmp_path, layout="src")
    assert provenance(launcher, env)[0] == 0
    (pkg / "__init__.py").write_text("edited = True\n")
    assert provenance(launcher, env)[0] == 1


@pytest.mark.parametrize("shebang", ["env", "trampoline"])
def test_env_and_pip_trampoline_shebangs_are_followed(tmp_path, provenance, shebang):
    *_, launcher, env = fake_agentteams(tmp_path, shebang=shebang)
    code, out, err = provenance(launcher, env)
    assert code == 0 and "editable checkout" in out, out + err


def test_a_failing_git_status_is_a_refusal_not_a_pass(tmp_path, provenance):
    repo, _, launcher, env = fake_agentteams(tmp_path)
    (repo / ".git" / "index").write_bytes(b"not an index")
    assert provenance(launcher, env)[0] == 1


def test_a_vcs_install_passes_and_names_its_commit(tmp_path, provenance):
    *_, launcher, env = fake_agentteams(tmp_path, install="vcs", git_repo=False)
    code, out, err = provenance(launcher, env)
    assert code == 0 and "VCS install" in out and "cccccccccccc" in out, out + err


def test_a_local_snapshot_is_refused_by_default(tmp_path, provenance, monkeypatch):
    """CA-033/034: a stale, unrecorded snapshot is what dropped mathAgents' adopted routing rows."""
    monkeypatch.delenv(_agentteams_provenance.ALLOW_SNAPSHOT_ENV, raising=False)
    *_, launcher, env = fake_agentteams(tmp_path, install="snapshot", git_repo=False)
    code, out, err = provenance(launcher, env)
    assert code == 1 and "snapshot" in out and "REFUSED" in err and "ALLOW_AGENTTEAMS_SNAPSHOT" in err, out + err


@pytest.mark.parametrize("value, expected", [("1", 0), ("0", 1), ("yes", 1)])
def test_a_local_snapshot_runs_only_with_the_explicit_override(tmp_path, provenance, value, expected):
    *_, launcher, env = fake_agentteams(tmp_path, install="snapshot", git_repo=False)
    code, _, err = provenance(launcher, {**env, _agentteams_provenance.ALLOW_SNAPSHOT_ENV: value})
    assert code == expected and ("WARNING" in err if expected == 0 else "REFUSED" in err), err


def test_an_install_inside_another_repo_is_not_judged_by_that_repo(tmp_path, provenance):
    """A venv inside an unrelated git repo on an unmerged branch (researchteam/.venv): a VCS install there passes."""
    outer = tmp_path / "outer"
    outer.mkdir()
    g(outer, "init", "-q", "-b", "feature")
    g(outer, "commit", "-q", "--allow-empty", "-m", "x")
    *_, launcher, env = fake_agentteams(outer, install="vcs", git_repo=False)
    assert provenance(launcher, env)[0] == 0


def test_a_checkout_shadowing_a_verified_install_is_refused(tmp_path, provenance):
    """The VCS record says one thing; a checkout earlier on sys.path is what actually runs."""
    repo, _, launcher, env = fake_agentteams(tmp_path, install="vcs")
    env["PYTHONPATH"] = f"{repo}:{env['PYTHONPATH']}"
    code, out, err = provenance(launcher, env)
    assert code == 1 and "shadows" in err, out + err


def test_an_editable_record_pointing_elsewhere_is_refused(tmp_path, provenance):
    *_, launcher, env = fake_agentteams(tmp_path)
    other = tmp_path / "elsewhere"
    (other / "agentteams").mkdir(parents=True)
    (other / "agentteams" / "__init__.py").write_text("")
    (other / "build_team.py").write_text("")
    env["PYTHONPATH"] = env["PYTHONPATH"].split(":")[0] + f":{other}"  # the record's checkout is not what imports
    code, out, err = provenance(launcher, env)
    assert code == 1 and "outside the editable checkout" in err, out + err


def test_a_corrupt_install_record_is_a_clean_refusal(tmp_path, provenance):
    *_, launcher, env = fake_agentteams(tmp_path)
    site = Path(env["PYTHONPATH"].split(":")[0])
    (site / "agentteams-9.9.dist-info" / "direct_url.json").write_text("{not json")
    code, _, err = provenance(launcher, env)
    assert code == 1 and "REFUSED" in err and "Traceback" not in err, err


def test_an_edited_entry_module_is_refused(tmp_path, provenance):
    """The launcher runs build_team.py, which sits beside the package, not inside it."""
    repo, _, launcher, env = fake_agentteams(tmp_path)
    (repo / "build_team.py").write_text("def main(): print('patched')\n")
    code, _, err = provenance(launcher, env)
    assert code == 1 and "build_team.py" in err, err


def test_a_shadowing_entry_module_is_refused(tmp_path, provenance):
    *_, launcher, env = fake_agentteams(tmp_path, install="vcs", git_repo=False)
    shadow = tmp_path / "shadow"
    shadow.mkdir()
    (shadow / "build_team.py").write_text("def main(): pass\n")
    env["PYTHONPATH"] = f"{shadow}:{env['PYTHONPATH']}"
    code, out, err = provenance(launcher, env)
    assert code == 1 and "build_team" in err and "shadows" in err, out + err


def test_an_editable_record_with_vcs_info_is_checked_as_a_checkout(tmp_path, provenance):
    """A working checkout stays mutable whatever commit its record names, so the editable checks win."""
    repo, _, launcher, env = fake_agentteams(tmp_path)
    info = Path(env["PYTHONPATH"].split(":")[0]) / "agentteams-9.9.dist-info" / "direct_url.json"
    info.write_text(json.dumps({"url": repo.as_uri(), "dir_info": {"editable": True},
                                "vcs_info": {"vcs": "git", "commit_id": "c" * 40}}))
    g(repo, "checkout", "-qb", "wip")
    g(repo, "commit", "-q", "--allow-empty", "-m", "wip")
    code, _, err = provenance(launcher, env)
    assert code == 1 and "not on origin/main" in err, err


def test_a_malformed_install_record_is_a_clean_refusal(tmp_path, provenance):
    *_, launcher, env = fake_agentteams(tmp_path, install="vcs", git_repo=False)
    info = Path(env["PYTHONPATH"]) / "agentteams-9.9.dist-info" / "direct_url.json"
    info.write_text(json.dumps({"url": "x", "vcs_info": "not a dict"}))
    code, _, err = provenance(launcher, env)
    assert code == 1 and "malformed" in err and "Traceback" not in err, err


def test_an_unparseable_launcher_is_refused(tmp_path, provenance):
    launcher = tmp_path / "agentteams"
    launcher.write_text("no shebang here\n")
    launcher.chmod(0o755)
    code, _, err = provenance(launcher, {"PATH": f"{tmp_path}:/usr/bin:/bin"})
    assert code == 1 and "shebang not understood" in err


# --- wiring into _update_cmd -----------------------------------------------------------------------------------

def test_preflight_checks_the_launcher_it_will_execute(tmp_path, monkeypatch):
    """The PATH winner is checked (not researchteam's own interpreter), and a refusal stops the render."""
    *_, launcher, env = fake_agentteams(tmp_path, install="vcs", git_repo=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    checked: list[str] = []
    monkeypatch.setattr(_update_cmd, "_VERIFIED_LAUNCHERS", set())
    monkeypatch.setattr(_agentteams_provenance, "check", lambda exe: checked.append(exe) or 0)
    assert _update_cmd._preflight_agentteams() == str(launcher) and checked == [str(launcher)]
    assert _update_cmd._preflight_agentteams() == str(launcher) and len(checked) == 1   # checked once per run
    monkeypatch.setattr(_update_cmd, "_VERIFIED_LAUNCHERS", set())
    monkeypatch.setattr(_agentteams_provenance, "check", lambda exe: 1)
    with pytest.raises(SystemExit, match="Refusing to run unreviewed agentteams"):
        _update_cmd._preflight_agentteams()


def _help_launcher(tmp_path: Path, help_text: str) -> str:
    launcher = tmp_path / "agentteams"
    launcher.write_text(f"#!/bin/sh\necho '{help_text}'\n")
    launcher.chmod(0o755)
    return str(launcher)


def test_an_agentteams_with_p5a_is_accepted(tmp_path):
    _update_cmd._require_p5a(_help_launcher(tmp_path, "  --discard-user-regions  opt out"))


def test_an_agentteams_without_p5a_is_refused(tmp_path):
    with pytest.raises(SystemExit, match="predates agentteams P5a"):
        _update_cmd._require_p5a(_help_launcher(tmp_path, "  --overwrite  re-render"))

