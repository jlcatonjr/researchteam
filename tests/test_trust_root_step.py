"""The workflows' "Release trust root" step accepts the AGENTTEAMS_ALLOWED_SIGNERS secret only when it is the one
release-key line, by pinned fingerprint, so a secret holding another key can't make that key's tags verify as releases.

The step is run as written, except that the pinned fingerprint is swapped for a throwaway key's (the real release key's
private half is the operator's); two tests check the pin itself.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")
if shutil.which("ssh-keygen") is None:
    pytest.skip("ssh-keygen needed to make test keys", allow_module_level=True)

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = [ROOT / "researchteam" / "scaffold" / "agentteams-sync-derived.yml",
             ROOT / ".github" / "workflows" / "agentteams-sync.yml"]
STEP = "Release trust root (release-locked repos; operator-provisioned secret)"
# agentteams SECURITY.md "Release signers", rc.9 onward; the full value is pinned in the workflows (one place to review)
RELEASE_FP_PREFIX = "SHA256:IPdnLwlF"
PIN_RE = re.compile(r'RELEASE_FP="(SHA256:[A-Za-z0-9+/]{43})"')


def _step(workflow: Path) -> str:
    steps = yaml.safe_load(workflow.read_text())["jobs"]["autosync"]["steps"]
    return next(s["run"] for s in steps if s.get("name") == STEP)


def _pin(workflow: Path) -> str:
    pins = PIN_RE.findall(_step(workflow))
    assert len(pins) == 1
    return pins[0]


def _pubkey(tmp: Path, name: str) -> tuple[str, str]:
    key = tmp / name
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", name, "-f", str(key)], check=True)
    fp = subprocess.run(["ssh-keygen", "-l", "-E", "sha256", "-f", f"{key}.pub"], check=True,
                        capture_output=True, text=True).stdout.split()[1]
    return " ".join(Path(f"{key}.pub").read_text().split()[:2]), fp


def _run(tmp: Path, workflow: Path, secret: str, pinned: str):
    script = _step(workflow)
    gh_env = tmp / "github_env"
    gh_env.write_text("")
    env = {**os.environ, "ALLOWED_SIGNERS": secret, "RUNNER_TEMP": str(tmp), "GITHUB_ENV": str(gh_env)}
    r = subprocess.run(["bash", "-e", "-c", script.replace(_pin(workflow), pinned)], env=env,
                       capture_output=True, text=True)
    return r, gh_env.read_text()


@pytest.fixture(params=WORKFLOWS, ids=lambda p: p.name)
def workflow(request):
    return request.param


def test_the_pin_is_the_release_key(workflow):
    assert _pin(workflow).startswith(RELEASE_FP_PREFIX)


def test_both_workflows_pin_the_same_key():
    assert len({_pin(w) for w in WORKFLOWS}) == 1


def test_the_release_line_is_accepted(tmp_path, workflow):
    key, fp = _pubkey(tmp_path, "release")
    r, gh_env = _run(tmp_path, workflow, f'op@example namespaces="git" {key}\n', fp)
    assert r.returncode == 0, r.stderr
    assert gh_env == f"AGENTTEAMS_ALLOWED_SIGNERS={tmp_path}/allowed_signers\n"
    assert (tmp_path / "allowed_signers").read_text() == f'op@example namespaces="git" {key}\n'


def test_another_key_is_refused(tmp_path, workflow):
    _, fp = _pubkey(tmp_path, "release")
    other, _ = _pubkey(tmp_path, "other")
    r, gh_env = _run(tmp_path, workflow, f'op@example namespaces="git" {other}', fp)
    assert r.returncode == 1 and "not the release key" in r.stderr and gh_env == ""


def test_an_extra_line_is_refused(tmp_path, workflow):
    key, fp = _pubkey(tmp_path, "release")
    other, _ = _pubkey(tmp_path, "other")
    secret = f'op@example namespaces="git" {key}\nop@example namespaces="git" {other}\n'
    r, gh_env = _run(tmp_path, workflow, secret, fp)
    assert r.returncode == 1 and "exactly one line" in r.stderr and gh_env == ""


@pytest.mark.parametrize("shape", ["{key}", 'op@example {key}', 'op@example namespaces="file" {key}',
                                   'op@example namespaces="git" {key} trailing'])
def test_a_malformed_line_is_refused(tmp_path, workflow, shape):
    key, fp = _pubkey(tmp_path, "release")
    r, gh_env = _run(tmp_path, workflow, shape.format(key=key), fp)
    assert r.returncode == 1 and "refusing" in r.stderr and gh_env == ""


def test_no_secret_is_a_no_op(tmp_path, workflow):
    r, gh_env = _run(tmp_path, workflow, "", "SHA256:unused")
    assert r.returncode == 0 and gh_env == ""
