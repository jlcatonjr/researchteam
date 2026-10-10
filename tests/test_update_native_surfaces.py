"""`researchteam update` keeps the native claude/goose surfaces current (merge mode), not only copilot-vscode.

Before, only `materialize` re-rendered `.claude/agents` / `.goose/recipes`, so the weekly autosync left every
Claude/Goose output of an agentteams change stale (agent-specific MCP blocks, sandbox settings, the gate hook).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from researchteam import _update_cmd

REPO = Path(__file__).resolve().parents[1]


def _instance(tmp_path: Path, surfaces: dict[str, object]) -> Path:
    (tmp_path / "brief.json").write_text(json.dumps({"project_name": "demo", "project_goal": "demo goal"}))
    (tmp_path / ".github" / "agents").mkdir(parents=True)
    for d, log in surfaces.items():
        (tmp_path / d / "references").mkdir(parents=True)
        text = log if isinstance(log, str) else json.dumps(log)
        (tmp_path / d / "references" / "build-log.json").write_text(text)
    return tmp_path


@pytest.fixture
def calls(monkeypatch):
    class Calls(list):
        fail_on: set[str]

    seen = Calls()
    seen.fail_on = set()
    fail_on = seen.fail_on

    class Result:
        def __init__(self, code):
            self.returncode = code

    monkeypatch.setattr(_update_cmd, "_preflight_agentteams", lambda: "agentteams")
    monkeypatch.setattr(_update_cmd, "_brief_has_placeholder", lambda root: False)

    def fake_run(cmd, cwd=None, **kwargs):
        seen.append(list(cmd))
        fw = cmd[cmd.index("--framework") + 1] if "--framework" in cmd else "copilot-vscode"
        return Result(1 if fw in fail_on and "--interop-from" not in cmd else 0)

    monkeypatch.setattr(_update_cmd.subprocess, "run", fake_run)
    return seen


def _renders(calls):
    return [c for c in calls if "--interop-from" not in c]


@pytest.mark.parametrize("layer1_only", [True, False])
def test_update_renders_native_surfaces_in_merge_mode(tmp_path, calls, monkeypatch, layer1_only):
    root = _instance(tmp_path, {".claude/agents": {"framework": "claude"}, ".goose/recipes": {"framework": "goose"}})
    monkeypatch.setattr(_update_cmd, "managed_files_for", lambda profile: [])
    _update_cmd.run_update(root, ref="main", yes=True, dry_run=False, layer2_only=False, layer1_only=layer1_only)
    renders = _renders(calls)
    assert "--framework" not in renders[0]                                  # copilot-vscode first
    assert [c[c.index("--framework") + 1] for c in renders[1:]] == ["claude", "goose"]
    for c in renders[1:]:
        assert "--merge" in c and "--materialize-native" in c and c[c.index("--shrink-policy") + 1] == "preserve"
        assert not {"--overwrite", "--prune", "--bridge-refresh"} & set(c)


@pytest.mark.parametrize("log", [{"origin": "interop", "framework": "claude"}, "{not json", "[]"])
def test_an_interop_marker_or_unreadable_log_is_not_a_native_surface(tmp_path, log):
    """agentteams treats such a log as no prior build: --materialize-native would write a native team over a bridge."""
    root = _instance(tmp_path, {".claude/agents": log, ".goose/recipes": {"framework": "goose"}})
    assert _update_cmd._native_surfaces(root) == [("goose", ".goose/recipes")]


def test_a_bare_bridge_is_not_rendered(tmp_path, calls, monkeypatch):
    root = _instance(tmp_path, {})
    (root / ".claude" / "agents").mkdir(parents=True)                     # bridge only, no build-log
    monkeypatch.setattr(_update_cmd, "managed_files_for", lambda profile: [])
    _update_cmd.run_update(root, ref="main", yes=True, dry_run=False, layer2_only=False, layer1_only=True)
    assert all("--framework" not in c for c in _renders(calls))


def test_a_failed_surface_stops_before_codex_and_reports(tmp_path, calls, capsys, monkeypatch):
    root = _instance(tmp_path, {".claude/agents": {"framework": "claude"}, ".goose/recipes": {"framework": "goose"}})
    (root / ".codex" / "agents").mkdir(parents=True)
    calls.fail_on.add("claude")
    with pytest.raises(SystemExit) as exc:
        _update_cmd.run_update(root, ref="main", yes=True, dry_run=False, layer2_only=False, layer1_only=True)
    assert exc.value.code != 0
    err = capsys.readouterr().err
    assert "FAILED on .claude/agents (claude)" in err and "not attempted: .goose/recipes (goose)" in err
    assert not any("--interop-from" in c for c in calls)                   # no codex projection after a failure


def test_the_autosync_scrubs_native_machine_path_files():
    """S-8: each native surface's delivery receipt and memory index carry absolute paths; never into an auto-PR."""
    text = (REPO / "scripts" / "agentteams_autosync_gate.sh").read_text()
    block = re.search(r"SCRUB_PATHS=\((.*?)\n\)", text, re.S).group(1)
    for surface in (".github/agents", ".claude/agents", ".goose/recipes"):
        for name in ("delivery-receipt.json", "memory-index.json"):
            assert f'"{surface}/references/{name}"' in block
