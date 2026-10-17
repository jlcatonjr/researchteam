"""The derived autosync workflow installs the pinned researchteam when the lock is release-locked."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")
ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / "researchteam" / "scaffold" / "agentteams-sync-derived.yml"
SHA = "a515fcee5512722521a43e26137ccdfa2e63b6b3"


def _install_step() -> str:
    steps = yaml.safe_load(WORKFLOW.read_text())["jobs"]["autosync"]["steps"]
    return next(s["run"] for s in steps if s.get("name") == "Install ResearchTeam CLI")


def _run(tmp_path: Path, lock: str | None) -> tuple[subprocess.CompletedProcess, list[str]]:
    """Run the step with `python` and `researchteam` stubbed; return the result and pip install args."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "pip.log"
    (bin_dir / "python").write_text(f"#!/bin/sh\necho \"$*\" >> {log}\n")
    (bin_dir / "researchteam").write_text("#!/bin/sh\necho researchteam 1.0\n")
    for f in bin_dir.iterdir():
        f.chmod(0o755)
    if lock is not None:
        (tmp_path / "toolchain.lock").write_text(lock)
    env = dict(os.environ, PATH=f"{bin_dir}:/usr/bin:/bin")
    r = subprocess.run(["bash", "-e", "-c", _install_step()], cwd=tmp_path, env=env, capture_output=True, text=True)
    calls = log.read_text().splitlines() if log.exists() else []
    return r, [c for c in calls if "researchteam.git" in c]


def test_release_locked_repo_installs_the_locked_commit(tmp_path):
    r, installs = _run(tmp_path, f"researchteam=jlcatonjr/researchteam@{SHA}\nresearchteam.tag=v1.0.0-rc.2\n")
    assert r.returncode == 0, r.stderr
    assert installs == [f"-m pip install git+https://github.com/jlcatonjr/researchteam.git@{SHA}"]


@pytest.mark.parametrize("lock", [None, f"researchteam=jlcatonjr/researchteam@{SHA}\n"])
def test_unlocked_repo_keeps_main(tmp_path, lock):
    r, installs = _run(tmp_path, lock)
    assert r.returncode == 0, r.stderr
    assert installs == ["-m pip install git+https://github.com/jlcatonjr/researchteam.git"]


@pytest.mark.parametrize("pin", ["attacker/researchteam@" + SHA, "jlcatonjr/researchteam@main",
                                 "jlcatonjr/researchteam@" + SHA[:12], ""])
def test_a_locked_but_malformed_pin_fails_closed(tmp_path, pin):
    r, installs = _run(tmp_path, f"researchteam={pin}\nresearchteam.tag=v1.0.0-rc.2\n")
    assert r.returncode == 1 and "release-locked" in r.stderr and installs == []
