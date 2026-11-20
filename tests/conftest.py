"""Shared test setup: no test reaches the real GitHub API, and _frozen is imported before any test runs."""
import pytest

# researchteam._frozen binds subprocess.run at import (`from subprocess import run as _run`), so that a test's
# fake of subprocess.run never reaches its git calls. But update and materialize import _frozen lazily, so a test
# file that fakes subprocess.run first made _frozen keep the fake: test_update_native_surfaces.py and
# test_materialize_surfaces.py failed when run alone. Importing it here binds the real function for every file.
import researchteam._frozen  # noqa: F401,E402


@pytest.fixture(autouse=True)
def _offline_github_api(monkeypatch):
    """Point the reviewed-commit check at a closed local port: an unanswered request means "cannot tell" (None).
    Tests that need a definite answer stub ``commit_is_reviewed`` or serve a fake API themselves."""
    monkeypatch.setenv("RESEARCHTEAM_GITHUB_API", "http://127.0.0.1:9")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
