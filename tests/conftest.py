"""Shared test setup: no test reaches the real GitHub API."""
import pytest


@pytest.fixture(autouse=True)
def _offline_github_api(monkeypatch):
    """Point the reviewed-commit check at a closed local port: an unanswered request means "cannot tell" (None).
    Tests that need a definite answer stub ``commit_is_reviewed`` or serve a fake API themselves."""
    monkeypatch.setenv("RESEARCHTEAM_GITHUB_API", "http://127.0.0.1:9")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
