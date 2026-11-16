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


# --------------------------------------------------------------------------- term-index step
def _with_term_check(repo: Path) -> Path:
    for name in ("build_term_index.py", "check_term_index.py"):
        shutil.copy(ROOT / "scripts" / name, repo / "scripts")
    return repo


def _project(repo: Path, text: str) -> Path:
    proj = repo / "Projects" / "Demo"
    (proj / "terminology").mkdir(parents=True)
    (proj / "01-review.md").write_text(text)
    (proj / "terminology" / "terms.json").write_text(
        '{"schema": "researchteam-term-register", "terms": '
        '[{"id": "t", "label": "term register", "definition": "d", "source": "project definition"}]}')
    return proj


def test_term_check_is_skipped_when_the_script_is_absent(tmp_path):
    repo = _repo(tmp_path)
    _project(repo, "A term register.\n")  # generic-profile repository: no check script
    r = _validate(repo)
    assert r.returncode == 0 and "check_term_index" not in r.stdout and "Validation completed." in r.stdout


def test_validate_passes_with_no_register_and_fails_on_a_stale_index(tmp_path):
    repo = _with_term_check(_repo(tmp_path))
    r = _validate(repo)
    assert r.returncode == 0 and "NOTHING CHECKED" in r.stdout and "Validation completed." in r.stdout
    proj = _project(repo, "A term register.\n")
    stale = _validate(repo)
    assert stale.returncode == 1 and "DEFECT[STALE]" in stale.stdout
    assert "Term-index check failed" in stale.stderr and "Validation completed." not in stale.stdout
    built = subprocess.run(["bash", str(repo / "scripts" / "claude_researchteam_bridge.sh"), "term-build", "Demo"],
                           capture_output=True, text=True)
    assert built.returncode == 0, built.stdout + built.stderr
    assert _validate(repo).returncode == 0
    (proj / "01-review.md").write_text("A term register, edited.\n")
    assert _validate(repo).returncode == 1


def test_validate_ignores_the_advisory_switch(tmp_path):
    import os

    repo = _with_term_check(_repo(tmp_path))
    _project(repo, "A term register.\n")
    r = subprocess.run(["bash", str(repo / "scripts" / "claude_researchteam_bridge.sh"), "validate"],
                       capture_output=True, text=True, env={**os.environ, "TERM_INDEX_ADVISORY": "1"})
    assert r.returncode == 1 and "ADVISORY MODE" not in r.stdout


def test_term_commands_dispatch(tmp_path):
    repo = _with_term_check(_repo(tmp_path))
    shutil.copy(ROOT / "scripts" / "query_term_index.py", repo / "scripts")
    _project(repo, "A term register.\n")
    bridge = ["bash", str(repo / "scripts" / "claude_researchteam_bridge.sh")]
    assert subprocess.run(bridge + ["term-build"], capture_output=True, text=True).returncode == 0
    check = subprocess.run(bridge + ["term-check", "Demo"], capture_output=True, text=True)
    assert check.returncode == 0 and "PASS (no DEFECT)" in check.stdout
    query = subprocess.run(bridge + ["term-query", "Demo", "term register"], capture_output=True, text=True)
    assert query.returncode == 0 and "01-review.md:1:3" in query.stdout
    again = subprocess.run(bridge + ["term-init", "Demo"], capture_output=True, text=True)
    assert again.returncode == 1
