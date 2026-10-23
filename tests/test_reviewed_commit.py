"""A commit counts as reviewed only when it is on main or a release/* branch: GitHub serves a fork's commits
under the parent repository's URL, so a URL alone proves nothing."""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from researchteam import _agentteams_provenance, _fetch, cli

ON_MAIN, ON_RELEASE, FORK_ONLY = "a" * 40, "b" * 40, "c" * 40


@pytest.fixture
def fake_api(monkeypatch):
    """A local GitHub API: compare and branches answers keyed by path; anything else is a 500."""
    answers: dict[str, tuple[int, object]] = {
        f"/repos/o/r/compare/main...{ON_MAIN}": (200, {"status": "behind"}),
        f"/repos/o/r/compare/main...{ON_RELEASE}": (200, {"status": "diverged"}),
        f"/repos/o/r/compare/main...{FORK_ONLY}": (200, {"status": "ahead"}),
        "/repos/o/r/branches?per_page=100": (200, [{"name": "main"}, {"name": "release/1.0"}, {"name": "feat"}]),
        f"/repos/o/r/compare/release/1.0...{ON_RELEASE}": (200, {"status": "identical"}),
        f"/repos/o/r/compare/release/1.0...{FORK_ONLY}": (200, {"status": "diverged"}),
    }
    seen: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append(self.path)
            code, body = answers.get(self.path, (500, {}))
            data = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("RESEARCHTEAM_GITHUB_API", f"http://127.0.0.1:{server.server_port}")
    yield answers, seen
    server.shutdown()


def test_a_commit_on_main_is_reviewed_with_one_request(fake_api):
    _answers, seen = fake_api
    assert _fetch.commit_is_reviewed("o/r", ON_MAIN) is True and len(seen) == 1


def test_a_release_tag_commit_is_reviewed_through_its_release_branch(fake_api):
    _answers, seen = fake_api
    assert _fetch.commit_is_reviewed("o/r", ON_RELEASE) is True
    assert not any("compare/feat" in p for p in seen), "only main and release/* count"


def test_a_fork_only_commit_is_not_reviewed(fake_api):
    assert _fetch.commit_is_reviewed("o/r", FORK_ONLY) is False


def test_an_unknown_commit_is_not_reviewed(fake_api):
    answers, _seen = fake_api
    unknown = "d" * 40
    answers[f"/repos/o/r/compare/main...{unknown}"] = (404, {})
    answers[f"/repos/o/r/compare/release/1.0...{unknown}"] = (404, {})
    assert _fetch.commit_is_reviewed("o/r", unknown) is False


def test_server_errors_and_offline_mean_cannot_tell(fake_api, monkeypatch):
    assert _fetch.commit_is_reviewed("o/r", "e" * 40) is None  # 500s
    monkeypatch.setenv("RESEARCHTEAM_GITHUB_API", "http://127.0.0.1:9")
    assert _fetch.commit_is_reviewed("o/r", ON_MAIN) is None


def test_a_non_hex_ref_is_not_a_commit():
    assert _fetch.commit_is_reviewed("o/r", "main") is False


@pytest.mark.parametrize("reviewed, code, says", [(True, 0, ""), (False, 1, "REFUSED"), (None, 0, "could not confirm")])
def test_the_provenance_guard_checks_the_vcs_commit(tmp_path, monkeypatch, capfd, reviewed, code, says):
    """inner() runs in-process here so the reviewed answer can be stubbed (check() would re-run it under the
    launcher's interpreter)."""
    from test_agentteams_provenance import fake_agentteams  # tests/ is on sys.path (pytest prepend mode)
    monkeypatch.delenv(_agentteams_provenance.ALLOW_UNVERIFIED_ENV, raising=False)
    *_, launcher, env = fake_agentteams(tmp_path, install="vcs", git_repo=False)
    monkeypatch.setattr(sys, "path", env["PYTHONPATH"].split(":") + sys.path)
    import importlib
    importlib.invalidate_caches()
    for mod in ("agentteams", "build_team"):
        sys.modules.pop(mod, None)
    asked = []
    monkeypatch.setattr(_agentteams_provenance._fetch, "commit_is_reviewed",
                        lambda repo, sha: asked.append((repo, sha)) or reviewed)
    import importlib.metadata as md
    monkeypatch.setattr(_agentteams_provenance.metadata, "distribution",
                        lambda name: md.PathDistribution(tmp_path / "site dir" / "agentteams-9.9.dist-info"))
    assert _agentteams_provenance.inner(str(launcher)) == code
    out, err = capfd.readouterr()
    assert asked == [("jlcatonjr/agentteams", "c" * 40)] and says in out + err, out + err


@pytest.mark.parametrize("ref, reviewed, exits", [("0c72a18", False, True), ("0c72a18", None, False),
                                                  ("0c72a18", True, False), ("main", False, False)])
def test_update_checks_a_commit_ref(monkeypatch, capsys, ref, reviewed, exits):
    monkeypatch.setattr(_fetch, "commit_is_reviewed", lambda repo, sha: reviewed)
    if exits:
        with pytest.raises(SystemExit, match="refusing commit"):
            cli._check_commit_ref(ref)
    else:
        cli._check_commit_ref(ref)
        assert ("WARNING" in capsys.readouterr().err) == (reviewed is None and ref != "main")
