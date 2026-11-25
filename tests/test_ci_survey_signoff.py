"""The `survey sign-off` CI job installs what the repository has vetted, and nothing else.

.github/ci/requirements-agentteams.txt must name exactly the versions of docs/release/constraints-2026-11-13.txt
(the S-10 vetted set for agentteams' signing chain) plus the one build requirement agentteams pins, each with
hashes; and the job must take the agentteams commit from toolchain.lock, never a branch or a tag.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQ = ROOT / ".github" / "ci" / "requirements-agentteams.txt"
CONSTRAINTS = ROOT / "docs" / "release" / "constraints-2026-11-13.txt"
WORKFLOW = ROOT / ".github" / "workflows" / "tests.yml"
BUILD_ONLY = {"setuptools": "84.2.1"}


def _pins(text):
    return dict(re.findall(r"^([A-Za-z0-9_.-]+)==([^\s\\]+)", text, re.M))


def test_the_locked_versions_are_the_vetted_ones():
    locked = _pins(REQ.read_text(encoding="utf-8"))
    vetted = _pins(CONSTRAINTS.read_text(encoding="utf-8"))
    assert locked == {**vetted, **BUILD_ONLY}


def test_every_requirement_is_hash_locked():
    blocks = re.split(r"\n(?=[A-Za-z0-9_.-]+==)", REQ.read_text(encoding="utf-8"))
    reqs = [b for b in blocks if re.match(r"[A-Za-z0-9_.-]+==", b)]
    assert len(reqs) == len(_pins(REQ.read_text(encoding="utf-8")))
    for block in reqs:
        assert re.search(r"--hash=sha256:[0-9a-f]{64}", block), block.splitlines()[0]
        assert not re.search(r"--hash=(?!sha256:[0-9a-f]{64}\b)", block)


def test_the_job_installs_agentteams_only_at_the_locked_commit():
    text = WORKFLOW.read_text(encoding="utf-8")
    job = text[text.index("  survey-signoff:"):]
    assert "grep -E '^agentteams=' toolchain.lock" in job
    assert "git+https://github.com/jlcatonjr/agentteams@${sha}" in job
    assert "[0-9a-f]{40}" in job
    assert "--no-deps" in job and "--no-build-isolation" in job
    assert job.count("--require-hashes") == 2
    # no other source of agentteams, and no branch or tag
    assert len(re.findall(r"agentteams\s*@\s*git\+", job)) == 1
    assert not re.search(r"agentteams(\.git)?@(main|v\d)", job)
    assert "secrets." not in job and "permissions:" not in job


def test_a_skipped_signoff_test_fails_the_job():
    text = WORKFLOW.read_text(encoding="utf-8")
    job = text[text.index("  survey-signoff:"):]
    assert "tests/test_survey_verify.py tests/test_survey_gates.py" in job
    assert "skipped" in job and "exit 1" in job
