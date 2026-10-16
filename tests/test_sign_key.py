"""The operator HMAC key must be >= 32 bytes and not a placeholder (agentteams 1.0.0rc12; masterTeacher 4.1)."""
import importlib.util
import secrets
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location("sign_security_decision", ROOT / "scripts" / "sign_security_decision.py")
ssd = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ssd)


def test_a_generated_key_is_accepted():
    assert ssd.key_problem(secrets.token_hex(32)) == ""


@pytest.mark.parametrize("key, why", [
    ("", "not set"), ("...", "placeholder"), ("changeme-changeme-changeme-changeme", "placeholder"),
    ("a" * 40, "placeholder"), ("<your key here>" + "x" * 30, "placeholder"), ("s3cr3tk3y", "shorter than 32"),
])
def test_short_or_placeholder_keys_are_refused(key, why):
    assert why in ssd.key_problem(key)


def test_refused_before_agentteams_is_imported(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("AGENTTEAMS_DECISION_SIGNING_KEY", "short")
    monkeypatch.setattr("sys.argv", ["x", "--action", "overwrite", "--conditions", "c", "--log", str(tmp_path / "l.csv")])
    assert ssd.main() == 1
    assert "shorter than 32 bytes" in capsys.readouterr().err
