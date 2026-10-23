"""`claude_researchteam_bridge.sh validate` runs repo-owned checks from scripts/validate.d/."""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy(ROOT / "scripts" / "claude_researchteam_bridge.sh", repo / "scripts")
    stub = repo / "scripts" / "validate_agentteams_update.sh"
    stub.write_text("#!/usr/bin/env bash\necho 'Validation passed.'\n")
    stub.chmod(0o755)
    return repo


def _hook(repo: Path, name: str, body: str, executable: bool = True) -> None:
    d = repo / "scripts" / "validate.d"
    d.mkdir(exist_ok=True)
    f = d / name
    f.write_text(f"#!/usr/bin/env bash\n{body}\n")
    if executable:
        f.chmod(0o755)


def _validate(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", str(repo / "scripts" / "claude_researchteam_bridge.sh"), "validate"],
                          capture_output=True, text=True)


def test_no_validate_d_is_unchanged(tmp_path):
    r = _validate(_repo(tmp_path))
    assert r.returncode == 0 and "Validation completed." in r.stdout


def test_hooks_run_in_name_order_from_the_repo_root(tmp_path):
    repo = _repo(tmp_path)
    _hook(repo, "20-second", 'echo "second $PWD"')
    _hook(repo, "10-first", 'echo "first $PWD"')
    r = _validate(repo)
    assert r.returncode == 0, r.stdout + r.stderr
    out = r.stdout
    assert out.index("first ") < out.index("second ")
    assert f"first {repo.resolve()}" in out or f"first {repo}" in out


def test_every_hook_runs_and_any_failure_fails_validate(tmp_path):
    repo = _repo(tmp_path)
    _hook(repo, "10-bad", "echo bad-ran; exit 3")
    _hook(repo, "20-good", "echo good-ran")
    r = _validate(repo)
    assert r.returncode == 1
    assert "bad-ran" in r.stdout and "good-ran" in r.stdout
    assert "Local validator failed: scripts/validate.d/10-bad" in r.stderr
    assert "Validation completed." not in r.stdout


def test_non_executable_and_hidden_files_are_skipped(tmp_path):
    repo = _repo(tmp_path)
    _hook(repo, "README", "exit 1", executable=False)
    _hook(repo, ".hidden", "exit 1")
    r = _validate(repo)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Skipping scripts/validate.d/README (not executable)" in r.stdout
    assert ".hidden" not in r.stdout


def test_validate_d_is_not_managed():
    from researchteam._manifest import MANAGED_FILES
    assert not any(p.startswith("scripts/validate.d") for p in MANAGED_FILES)


@pytest.mark.parametrize("cmd", ["open-reader", "open-summary"])
def test_the_example_project_commands_are_gone(cmd):
    """They printed fixed Projects/ZeldaTimeline paths, which no derived repo has (init skips Projects/)."""
    bridge = ROOT / "scripts" / "claude_researchteam_bridge.sh"
    assert cmd not in subprocess.run(["bash", str(bridge), "help"], capture_output=True, text=True).stdout
    assert subprocess.run(["bash", str(bridge), cmd], capture_output=True, text=True).returncode == 2
