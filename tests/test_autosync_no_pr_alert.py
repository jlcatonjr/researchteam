"""F-5: a detected autosync change that opens no PR must not pass as a quiet week."""

import subprocess
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = [ROOT / ".github" / "workflows" / "agentteams-sync.yml",
             ROOT / "researchteam" / "scaffold" / "agentteams-sync-derived.yml"]
STEP = "Fail when a detected change produced no PR"


def _steps(path):
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [s for job in doc["jobs"].values() for s in job["steps"]]


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_alert_follows_create_pull_request(path):
    steps = _steps(path)
    names = [s.get("name") for s in steps]
    i = names.index(STEP)
    cpr = steps[i - 1]
    assert cpr.get("id") == "cpr" and "create-pull-request" in cpr["uses"]
    assert steps[i]["if"] == "steps.gate.outputs.changed == 'true' && steps.cpr.outputs.pull-request-number == ''"


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
@pytest.mark.parametrize("operation,code", [("none", 0), ("", 1), ("created", 1)])
def test_alert_script(path, operation, code):
    step = next(s for s in _steps(path) if s.get("name") == STEP)
    env = {"PATH": "/usr/bin:/bin", "OPERATION": operation, "NEW_SHA": "abc123"}
    r = subprocess.run(["bash", "-c", step["run"]], env=env, capture_output=True, text=True)
    assert r.returncode == code
    assert ("::warning::" if code == 0 else "::error::") in r.stdout
