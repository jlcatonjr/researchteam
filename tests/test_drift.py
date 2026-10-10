"""Drift reporting (OrthodoxLLM Item 2): frozen fences, seeded files, bridges."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from researchteam import _doctor_cmd, _drift, _update_cmd


def _report(root: Path, items: list[dict], framework: str | None = None) -> None:
    path = _drift.report_path(root, framework)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items))
    path.with_suffix(".md").write_text("# report\n")


ITEM = {"file": "references/ref-bibtex-reference.md", "fence": "content",
        "entry": "references/ref-bibtex-reference.md:content@0123456789ab", "lost": ["x"], "all_retired": False}


def test_prepare_report_removes_the_previous_runs_report(tmp_path):
    _report(tmp_path, [ITEM])
    path = _drift.prepare_report(tmp_path)
    assert path == _drift.report_path(tmp_path) and not path.exists() and not path.with_suffix(".md").exists()


def test_reports_from_every_surface_are_read(tmp_path):
    _report(tmp_path, [ITEM])
    _report(tmp_path, [dict(ITEM, file="x.md")], framework="claude")
    surfaces = sorted((i["surface"], i["section"]) for i in _drift.load_frozen(tmp_path))
    assert surfaces == [("claude", "x.md:content"), ("copilot-vscode", "references/ref-bibtex-reference.md:content")]


def test_malformed_reports_and_pins_never_raise(tmp_path):
    (tmp_path / "tmp").mkdir()
    (tmp_path / "tmp" / f"{_drift.REPORT_STEM}.json").write_text("{not json")
    (tmp_path / "tmp" / f"{_drift.REPORT_STEM}.goose.json").write_text(json.dumps([1, {"file": "x"}]))
    assert _drift.load_frozen(tmp_path) == []
    pins = tmp_path / _drift.INTENTIONAL_FILE
    pins.parent.mkdir(parents=True)
    pins.write_text(json.dumps({"pins": [{"section": 3}, "x", {"section": "a.md:content"}]}))
    assert _drift.load_intentional(tmp_path) == {"a.md:content": ""}


def test_first_seen_is_kept_while_frozen_and_reset_after_thaw(tmp_path):
    items = [{"surface": "copilot-vscode", "section": "a.md:content"}]
    d1, d2, d3 = dt.date(2026, 10, 1), dt.date(2026, 10, 9), dt.date(2026, 10, 12)
    assert _drift.record_first_seen(tmp_path, items, d1) == {"copilot-vscode|a.md:content": "2026-10-01"}
    assert _drift.record_first_seen(tmp_path, items, d2) == {"copilot-vscode|a.md:content": "2026-10-01"}
    assert _drift.record_first_seen(tmp_path, [], d2) == {}                       # thawed
    assert _drift.record_first_seen(tmp_path, items, d3) == {"copilot-vscode|a.md:content": "2026-10-12"}
    assert _drift.age_days("2026-10-01", d2) == 8 and _drift.age_days("garbage") is None


def test_update_summary_counts_intentional_and_to_review(tmp_path):
    assert "none" in _drift.frozen_summary(tmp_path)
    _report(tmp_path, [ITEM, dict(ITEM, file="b.agent.md", entry="b.agent.md:content@0123456789ab")])
    pins = tmp_path / _drift.INTENTIONAL_FILE
    pins.parent.mkdir(parents=True)
    pins.write_text(json.dumps({"pins": [{"section": "references/ref-bibtex-reference.md:content",
                                          "reason": "filled tool docs"}]}))
    line = _drift.frozen_summary(tmp_path)
    assert "2 section(s)" in line and "1 marked intentional, 1 to review" in line
    assert "tmp/agentteams-shrink-report.md" in line


def test_doctor_lists_frozen_fences_with_intent_and_release_entry(tmp_path):
    _report(tmp_path, [ITEM, dict(ITEM, file="b.agent.md", entry="b.agent.md:content@0123456789ab",
                                  all_retired=True)])
    pins = tmp_path / _drift.INTENTIONAL_FILE
    pins.parent.mkdir(parents=True)
    pins.write_text(json.dumps({"pins": [{"section": "references/ref-bibtex-reference.md:content",
                                          "reason": "filled tool docs"}]}))
    _drift.record_first_seen(tmp_path, _drift.load_frozen(tmp_path), dt.date.today())
    oks, warns = [], []
    _doctor_cmd._check_frozen_fences(tmp_path, oks.append, warns.append)
    text = "\n".join(oks + warns)
    assert "1 intentional, 1 to review" in text
    assert "intentional: filled tool docs" in text
    assert "AGENTTEAMS_SHRINK_ALLOW=b.agent.md:content@0123456789ab" in text and "safe to release" in text


def test_merge_render_asks_agentteams_for_the_report(tmp_path, monkeypatch):
    (tmp_path / "brief.json").write_text(json.dumps({"project_name": "demo"}))
    seen = {}
    monkeypatch.setattr(_update_cmd, "_preflight_agentteams", lambda: "agentteams")
    monkeypatch.setattr(_update_cmd, "_brief_has_placeholder", lambda root: False)

    class Done:
        returncode = 0

    def fake_run(cmd, cwd=None, env=None, **_):
        seen["env"] = env
        return Done()

    monkeypatch.setattr(_update_cmd.subprocess, "run", fake_run)
    monkeypatch.setattr(_update_cmd, "_reconcile_manifest_back", lambda root: None)
    _report(tmp_path, [ITEM])  # stale report from an earlier run
    _update_cmd._run_agentteams(tmp_path, yes=True, dry_run=False)
    assert seen["env"]["AGENTTEAMS_SHRINK_REPORT"] == str(_drift.report_path(tmp_path))
    assert not _drift.report_path(tmp_path).exists()  # stale report removed before the run
    _report(tmp_path, [ITEM])
    _update_cmd._run_agentteams(tmp_path, yes=True, dry_run=True)
    assert seen["env"] is None and _drift.report_path(tmp_path).exists()  # a dry run leaves the report alone
    _update_cmd._run_agentteams(tmp_path, yes=True, dry_run=False, framework="claude")
    assert seen["env"]["AGENTTEAMS_SHRINK_REPORT"] == str(_drift.report_path(tmp_path, "claude"))
    _report(tmp_path, [ITEM], framework="claude")
    _update_cmd._run_agentteams(tmp_path, yes=True, dry_run=False, overwrite=True, framework="claude")
    assert seen["env"] is None and not _drift.report_path(tmp_path, "claude").exists()  # overwrite thaws all


def test_comparable_body_ignores_project_notes():
    upstream = "---\nname: x\n---\nbody\n\n## Project-Specific Notes\n\n> placeholder\n"
    local = "---\nname: x\n---\nbody\n\n## Project-Specific Notes\n\nOur own duties.\n"
    assert _drift.comparable_body(local) == _drift.comparable_body(upstream)
    assert _drift.comparable_body("---\nname: y\n---\nbody\n") != _drift.comparable_body(upstream)


def test_seeded_file_drift_against_the_pinned_ref(tmp_path, monkeypatch):
    rel = ".github/agents/interpretation-advisor.agent.md"
    monkeypatch.setattr("researchteam._manifest.SEEDED_FILES", [rel])
    (tmp_path / "toolchain.lock").write_text(f"researchteam=jlcatonjr/researchteam@{'a' * 40}\n")
    asked = []
    monkeypatch.setattr("researchteam._fetch.fetch_raw",
                        lambda repo, ref, path: asked.append(ref) or "body v2\n## Project-Specific Notes\n")
    local = tmp_path / rel
    local.parent.mkdir(parents=True)
    local.write_text("body v1\n## Project-Specific Notes\nours\n")
    oks, warns = [], []
    _doctor_cmd._check_seeded_files(tmp_path, oks.append, warns.append)
    assert asked == ["a" * 40] and any("differs from upstream" in w for w in warns)
    local.write_text("body v2\n## Project-Specific Notes\nours\n")
    oks, warns = [], []
    _doctor_cmd._check_seeded_files(tmp_path, oks.append, warns.append)
    assert not warns and oks


def test_upstream_ref_falls_back_to_marker_then_main(tmp_path):
    assert _doctor_cmd._upstream_ref(tmp_path) == ("main", "main")
    (tmp_path / ".researchteam").write_text("[researchteam]\nref = v0.3.0\n")
    assert _doctor_cmd._upstream_ref(tmp_path) == ("v0.3.0", "marker ref")


@pytest.mark.parametrize("text, expect", [
    ("# Bridge Check Report\n\nResult: FAIL\n\n## Changed Source Files\n- agents/a.agent.md\n- agents/b.agent.md\n",
     ("FAIL", ["agents/a.agent.md", "agents/b.agent.md"])),
    ("# Bridge Check Report\n\nResult: PASS\n", ("PASS", [])),
    ("garbage", ("UNKNOWN", [])),
])
def test_bridge_report_parsing(text, expect):
    assert _drift.parse_bridge_report(text) == expect


def test_bridge_frameworks_from_recorded_bridges(tmp_path):
    for d in ("copilot-vscode-to-claude", "copilot-vscode-to-goose", "unrelated"):
        (tmp_path / _drift.BRIDGES_DIR / d).mkdir(parents=True)
    assert _drift.bridge_frameworks(tmp_path) == ["claude", "goose"]


def test_frozen_summary_is_skipped_on_a_dry_run(tmp_path, capsys):
    _update_cmd._print_frozen_summary(tmp_path, dry_run=True)
    assert capsys.readouterr().out == "" and not (tmp_path / _drift.STATE_FILE).exists()


def test_printed_hints_are_quoted_and_free_of_control_characters(tmp_path):
    evil = "x.md:content@0123456789ab'; rm -rf ~; echo '"
    _report(tmp_path, [dict(ITEM, file="x.md\x1b[2K", entry=evil)])
    pins = tmp_path / _drift.INTENTIONAL_FILE
    pins.parent.mkdir(parents=True)
    oks, warns = [], []
    _doctor_cmd._check_frozen_fences(tmp_path, oks.append, warns.append)
    line = next(w for w in warns if "Release after review" in w)
    hint = line.split("Release after review: ", 1)[1]
    import shlex
    assert shlex.split(hint) == ["AGENTTEAMS_SHRINK_ALLOW=" + evil]  # one word: nothing runs
    assert "\x1b" not in "\n".join(oks + warns)


def test_seeded_check_reports_no_match_when_every_fetch_failed(tmp_path, monkeypatch):
    monkeypatch.setattr("researchteam._manifest.SEEDED_FILES", ["a.md"])

    def boom(repo, ref, path):
        raise RuntimeError("offline")

    monkeypatch.setattr("researchteam._fetch.fetch_raw", boom)
    oks, warns = [], []
    _doctor_cmd._check_seeded_files(tmp_path, oks.append, warns.append)
    assert not oks and any("could not fetch" in w for w in warns)


def test_seeded_check_refuses_an_odd_ref(tmp_path, monkeypatch):
    monkeypatch.setattr("researchteam._manifest.SEEDED_FILES", ["a.md"])
    (tmp_path / ".researchteam").write_text("ref = ../../evil?x=1\n")
    monkeypatch.setattr("researchteam._fetch.fetch_raw", lambda *a: pytest.fail("must not fetch"))
    oks, warns = [], []
    _doctor_cmd._check_seeded_files(tmp_path, oks.append, warns.append)
    assert any("not a plain commit or name" in w for w in warns)


def test_bridges_end_to_end(tmp_path, monkeypatch):
    for fw in ("claude", "goose"):
        (tmp_path / _drift.BRIDGES_DIR / f"copilot-vscode-to-{fw}").mkdir(parents=True)
    stale = tmp_path / _drift.BRIDGES_DIR / "copilot-vscode-to-goose" / "bridge-check.report.md"
    stale.write_text("Result: PASS\n")  # an earlier run's verdict must not be reused
    monkeypatch.setattr(_update_cmd, "_preflight_agentteams", lambda: "agentteams")

    class R:
        def __init__(self, code, err=""):
            self.returncode, self.stdout, self.stderr = code, "", err

    def fake_run(cmd, cwd=None, **_):
        fw = cmd[cmd.index("--framework") + 1]
        report = tmp_path / _drift.BRIDGES_DIR / f"copilot-vscode-to-{fw}" / "bridge-check.report.md"
        if fw == "claude":
            report.write_text("Result: FAIL\n\n## Changed Source Files\n- agents/security.agent.md\n")
            return R(1)
        return R(2, "boom: no manifest")  # writes no report

    monkeypatch.setattr(_doctor_cmd.subprocess, "run", fake_run)
    oks, warns = [], []
    _doctor_cmd._check_bridges(tmp_path, oks.append, warns.append)
    claude = next(w for w in warns if "→claude" in w)
    goose = next(w for w in warns if "→goose" in w)
    assert "FAIL; changed since last merge: agents/security.agent.md" in claude and "--bridge-merge" in claude
    assert "UNKNOWN" in goose and "boom: no manifest" in goose


def test_bridges_skip_when_the_preflight_refuses(tmp_path, monkeypatch):
    (tmp_path / _drift.BRIDGES_DIR / "copilot-vscode-to-claude").mkdir(parents=True)

    def refuse():
        raise SystemExit("unreviewed agentteams")

    monkeypatch.setattr(_update_cmd, "_preflight_agentteams", refuse)
    oks, warns = [], []
    _doctor_cmd._check_bridges(tmp_path, oks.append, warns.append)
    assert any("did not pass the pre-flight" in w for w in warns)


def test_seeded_check_with_no_seeded_files(tmp_path, monkeypatch):
    monkeypatch.setattr("researchteam._manifest.SEEDED_FILES", [])
    oks, warns = [], []
    _doctor_cmd._check_seeded_files(tmp_path, oks.append, warns.append)
    assert not warns and "none" in oks[0]
