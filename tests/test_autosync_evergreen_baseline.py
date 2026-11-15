"""#172: the autosync gate trusts the evergreen branch's ref only while an open PR has it as head.

A branch left behind by a failed PR step (or a PR closed without merging) must not count as "already
integrated", or the re-run reports up-to-date and the update never gets a PR. Offline: the "agentteams"
remote and the repository's origin are local git repositories; `gh` is a stub on PATH.
"""

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "agentteams_autosync_gate.sh"
REF_FILE = ".github/agentteams-autosync-ref"
BRANCH = "chore/agentteams-autosync"
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
           "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
                          env={**os.environ, **GIT_ENV}).stdout.strip()


def _commit(repo, msg):
    _git(repo, "commit", "-q", "--allow-empty", "-m", msg)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def setup(tmp_path):
    """origin main records OLD; origin's evergreen branch records NEW (= agentteams main)."""
    at = tmp_path / "agentteams"
    at.mkdir()
    _git(at, "init", "-q", "-b", "main")
    new = _commit(at, "agentteams main")
    old = "0" * 40

    origin = tmp_path / "origin"
    origin.mkdir()
    _git(origin, "init", "-q", "-b", "main")
    (origin / ".github").mkdir()
    (origin / REF_FILE).write_text(old + "\n")
    _git(origin, "add", "-A")
    _commit(origin, "main")
    _git(origin, "checkout", "-q", "-b", BRANCH)
    (origin / REF_FILE).write_text(new + "\n")
    _git(origin, "commit", "-q", "-am", "stranded autosync")
    _git(origin, "checkout", "-q", "main")

    repo = tmp_path / "repo"
    _git(tmp_path, "clone", "-q", str(origin), str(repo))
    (repo / "scripts").mkdir()
    (repo / "scripts" / "agentteams_autosync_gate.sh").write_text(GATE.read_text())

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    env = {k: v for k, v in os.environ.items()
           if k not in {"GITHUB_OUTPUT", "AUTOSYNC_GATE_REEXEC", "AUTOSYNC_GATE_DEPTH", "AUTOSYNC_EVERGREEN_PR_OPEN",
                        "GH_TOKEN", "GITHUB_TOKEN"}}
    env.update(GIT_ENV, TMPDIR=str(tmp_path), AGENTTEAMS_GIT=str(at),
               PATH=f"{bin_dir}{os.pathsep}/usr/bin:/bin")
    return repo, env, bin_dir, old, new


def _gh_stub(bin_dir, body):
    stub = bin_dir / "gh"
    stub.write_text("#!/usr/bin/env bash\n" + body)
    stub.chmod(0o755)


def _run(repo, env):
    return subprocess.run(["bash", "scripts/agentteams_autosync_gate.sh", "--mode", "upstream", "--check-only"],
                          cwd=repo, env=env, capture_output=True, text=True)


def test_open_pr_keeps_the_evergreen_baseline(setup):
    repo, env, _bin, _old, new = setup
    r = _run(repo, {**env, "AUTOSYNC_EVERGREEN_PR_OPEN": "true"})
    assert r.returncode == 0, r.stderr
    assert f"up-to-date ({new})" in r.stdout


def test_stranded_branch_without_an_open_pr_is_detected_again(setup):
    repo, env, _bin, old, new = setup
    r = _run(repo, {**env, "AUTOSYNC_EVERGREEN_PR_OPEN": "false"})
    assert r.returncode == 0, r.stderr
    assert "no open PR has it as head" in r.stdout
    assert f"update detected: {old} -> {new}" in r.stdout


@pytest.mark.parametrize("answer,expect", [("1", "up-to-date"), ("0", "update detected")])
def test_gh_lookup_when_the_caller_does_not_say(setup, answer, expect):
    repo, env, bin_dir, _old, _new = setup
    _gh_stub(bin_dir, f'[ "$1 $2" = "pr list" ] && echo {answer} && exit 0\nexit 9\n')
    r = _run(repo, env)
    assert r.returncode == 0, r.stderr
    assert expect in r.stdout


@pytest.mark.parametrize("stub", ["exit 1\n", "echo not-a-number\n", "exit 127\n"],
                         ids=["gh-fails", "gh-garbage", "gh-missing"])
def test_unknown_pr_state_errs_toward_detecting_the_change(setup, stub):
    repo, env, bin_dir, old, new = setup
    _gh_stub(bin_dir, stub)  # always stubbed, so a gh on the runner's PATH is never called
    r = _run(repo, env)
    assert r.returncode == 0, r.stderr
    assert "::warning::" in r.stdout
    assert f"update detected: {old} -> {new}" in r.stdout


def test_no_evergreen_branch_needs_no_lookup(setup):
    repo, env, bin_dir, old, new = setup
    _git(repo, "update-ref", "-d", f"refs/remotes/origin/{BRANCH}")
    _gh_stub(bin_dir, "echo called >&2; exit 9\n")
    r = _run(repo, env)
    assert r.returncode == 0, r.stderr
    assert "called" not in r.stderr and "::warning::" not in r.stdout
    assert f"update detected: {old} -> {new}" in r.stdout


@pytest.mark.parametrize("path", [ROOT / ".github" / "workflows" / "agentteams-sync.yml",
                                  ROOT / "researchteam" / "scaffold" / "agentteams-sync-derived.yml"],
                         ids=lambda p: p.name)
def test_workflows_look_up_the_pr_outside_the_gate_step(path):
    yaml = pytest.importorskip("yaml")
    steps = [s for job in yaml.safe_load(path.read_text())["jobs"].values() for s in job["steps"]]
    lookup = next(s for s in steps if s.get("id") == "evergreen")
    gate = next(s for s in steps if s.get("id") == "gate")
    assert "GH_TOKEN" in lookup["env"] and "gh pr list --head chore/agentteams-autosync" in lookup["run"]
    assert gate["env"]["AUTOSYNC_EVERGREEN_PR_OPEN"] == "${{ steps.evergreen.outputs.open }}"
    assert not {"GH_TOKEN", "GITHUB_TOKEN"} & set(gate["env"]), "no token may reach the gate step"
    assert steps.index(lookup) < steps.index(gate)
