"""The derived autosync workflow verifies the locked researchteam tag with the runner's own git, then
installs exactly that commit, before the gate runs any researchteam code (release policy §3)."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")
if shutil.which("ssh-keygen") is None:
    pytest.skip("ssh-keygen needed to sign a test tag", allow_module_level=True)

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / "researchteam" / "scaffold" / "agentteams-sync-derived.yml"
TAG = "v1.0.0-rc.9"
CLEAN_GIT = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}


def _step(name: str) -> str:
    steps = yaml.safe_load(WORKFLOW.read_text())["jobs"]["autosync"]["steps"]
    return next(s["run"] for s in steps if s.get("name") == name)


def _git(repo: Path, *args: str, **env: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True,
                          env={**os.environ, **CLEAN_GIT, **env}).stdout.strip()


def _key(tmp: Path, name: str) -> Path:
    key = tmp / name
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", name, "-f", str(key)], check=True)
    return key


@pytest.fixture
def upstream(tmp_path):
    """A stand-in researchteam remote with a release tag signed by a 'release' key; returns (url, sha, signers)."""
    repo = tmp_path / "researchteam"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "release")
    release = _key(tmp_path, "release")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "-c", "gpg.format=ssh",
         "-c", f"user.signingkey={release}", "tag", "-s", TAG, "-m", TAG)
    signers = tmp_path / "allowed_signers"
    signers.write_text("t@t " + (release.with_suffix(".pub")).read_text())
    return str(repo), _git(repo, "rev-parse", f"{TAG}^{{commit}}"), signers


def _run(tmp_path: Path, lock: str | None, rt_git: str, signers: Path | None):
    work = tmp_path / "derived"
    work.mkdir(exist_ok=True)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    log = tmp_path / "pip.log"
    log.unlink(missing_ok=True)
    (bin_dir / "python").write_text(f"#!/bin/sh\necho \"$*\" >> {log}\n")
    (bin_dir / "researchteam").write_text("#!/bin/sh\necho researchteam 1.0\n")
    for f in bin_dir.iterdir():
        f.chmod(0o755)
    if lock is not None:
        (work / "toolchain.lock").write_text(lock)
    env = {k: v for k, v in os.environ.items() if k != "AGENTTEAMS_ALLOWED_SIGNERS"}
    env.update(PATH=f"{bin_dir}:{os.environ['PATH']}", RESEARCHTEAM_GIT=rt_git, **CLEAN_GIT)
    if signers is not None:
        env["AGENTTEAMS_ALLOWED_SIGNERS"] = str(signers)
    r = subprocess.run(["bash", "-e", "-c", _step("Install ResearchTeam CLI")], cwd=work, env=env,
                       capture_output=True, text=True)
    installs = [c for c in (log.read_text().splitlines() if log.exists() else []) if "install git+" in c]
    return r, installs


def _lock(sha: str, tag: str = TAG) -> str:
    return f"researchteam=jlcatonjr/researchteam@{sha}\nresearchteam.tag={tag}\n"


def test_trust_root_step_runs_before_the_install():
    steps = [s.get("name") for s in yaml.safe_load(WORKFLOW.read_text())["jobs"]["autosync"]["steps"]]
    assert steps.index("Release trust root (release-locked repos; operator-provisioned secret)") < \
        steps.index("Install ResearchTeam CLI")


def test_a_verified_tag_installs_exactly_the_locked_commit(tmp_path, upstream):
    url, sha, signers = upstream
    r, installs = _run(tmp_path, _lock(sha), url, signers)
    assert r.returncode == 0, r.stderr
    assert installs == [f"-m pip install git+{url}@{sha}"] and "verified" in r.stdout


@pytest.mark.parametrize("lock", [None, "researchteam=jlcatonjr/researchteam@" + "a" * 40 + "\n"])
def test_an_unlocked_repo_keeps_main_and_needs_no_signers(tmp_path, upstream, lock):
    url, _, _ = upstream
    r, installs = _run(tmp_path, lock, url, None)
    assert r.returncode == 0, r.stderr
    assert installs == [f"-m pip install git+{url}"]


def test_a_tag_signed_by_another_key_is_refused(tmp_path, upstream):
    url, sha, _ = upstream
    other = tmp_path / "other_signers"
    other.write_text("t@t " + _key(tmp_path, "intruder").with_suffix(".pub").read_text())
    r, installs = _run(tmp_path, _lock(sha), url, other)
    assert r.returncode == 1 and "does not verify" in r.stderr and installs == []


def test_a_lock_sha_that_is_not_the_tags_commit_is_refused(tmp_path, upstream):
    url, _, signers = upstream
    r, installs = _run(tmp_path, _lock("b" * 40), url, signers)
    assert r.returncode == 1 and "peels to" in r.stderr and installs == []


def test_a_lightweight_or_missing_tag_is_refused(tmp_path, upstream):
    url, sha, signers = upstream
    _git(Path(url), "tag", "v1.0.0-rc.10")  # lightweight
    r, installs = _run(tmp_path, _lock(sha, "v1.0.0-rc.10"), url, signers)
    assert r.returncode == 1 and "not an annotated tag" in r.stderr and installs == []
    r, installs = _run(tmp_path, _lock(sha, "v9.9.9"), url, signers)
    assert r.returncode == 1 and "not found" in r.stderr and installs == []


def test_no_allowed_signers_fails_closed(tmp_path, upstream):
    url, sha, _ = upstream
    r, installs = _run(tmp_path, _lock(sha), url, None)
    assert r.returncode == 1 and "AGENTTEAMS_ALLOWED_SIGNERS" in r.stderr and installs == []


@pytest.mark.parametrize("lock", [
    "researchteam=attacker/researchteam@" + "a" * 40 + "\nresearchteam.tag=v1.0.0-rc.9\n",
    "researchteam=jlcatonjr/researchteam@main\nresearchteam.tag=v1.0.0-rc.9\n",
    "researchteam=jlcatonjr/researchteam@" + "a" * 40 + "\nresearchteam.tag=main\n",
])
def test_malformed_locked_pins_fail_closed(tmp_path, upstream, lock):
    url, _, signers = upstream
    r, installs = _run(tmp_path, lock, url, signers)
    assert r.returncode == 1 and "release-locked" in r.stderr and installs == []
