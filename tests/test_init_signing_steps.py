"""The init next-steps note names one clearance per agent surface (materialize gates each surface)."""

from researchteam._init_cmd import SIGNED_SURFACES, _signing_steps


def test_one_signing_line_per_present_surface(tmp_path):
    for d in SIGNED_SURFACES:
        (tmp_path / d).mkdir(parents=True)
    out = _signing_steps(tmp_path)
    assert out.count("sign_security_decision.py") == len(SIGNED_SURFACES)
    for d in SIGNED_SURFACES:
        assert f"--log {d}/references/security-decisions.log.csv" in out


def test_only_present_surfaces_are_listed(tmp_path):
    (tmp_path / ".github/agents").mkdir(parents=True)
    (tmp_path / ".goose/recipes").mkdir(parents=True)
    out = _signing_steps(tmp_path)
    assert ".claude/agents" not in out
    assert out.count("sign_security_decision.py") == 2


def test_no_surface_falls_back_to_github(tmp_path):
    assert _signing_steps(tmp_path).count("--log .github/agents/") == 1
