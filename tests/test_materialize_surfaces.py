"""materialize re-renders every native surface from the same descriptor (R1)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from researchteam import _update_cmd


def _instance(tmp_path: Path, surfaces: tuple[str, ...]) -> Path:
    (tmp_path / "brief.json").write_text(json.dumps({"project_name": "demo", "project_goal": "demo goal"}))
    (tmp_path / ".github" / "agents").mkdir(parents=True)
    for d in surfaces:
        (tmp_path / d / "references").mkdir(parents=True)
        (tmp_path / d / "references" / "build-log.json").write_text("{}")
    return tmp_path


@pytest.fixture
def calls(monkeypatch):
    seen: list[list[str]] = []

    class Done:
        returncode = 0

    monkeypatch.setattr(_update_cmd, "_preflight_agentteams", lambda: "agentteams")
    def fake_run(cmd, cwd=None):
        desc = Path(cwd) / cmd[cmd.index("--description") + 1]
        seen.append(cmd + ["#content", desc.read_text()])   # capture before the temp file is removed
        return Done()

    monkeypatch.setattr(_update_cmd.subprocess, "run", fake_run)
    monkeypatch.setattr(_update_cmd, "_brief_has_placeholder", lambda root: False)
    import researchteam._personalize as p
    monkeypatch.setattr(p, "is_upstream", lambda root: False)
    monkeypatch.setattr(p, "run_personalize", lambda *a, **k: None)
    return seen


def test_all_native_surfaces_rendered_with_same_descriptor(tmp_path, calls):
    root = _instance(tmp_path, (".claude/agents", ".goose/recipes"))
    (root / ".github/agents/_build-description.json").write_text(
        json.dumps({"selected_archetypes": ["primary-producer", "visual-designer"]}))  # forces roster union
    _update_cmd.run_materialize(root, yes=True, dry_run=False)
    assert len(calls) == 3
    assert "--framework" not in calls[0]                                   # copilot-vscode first
    assert [c[c.index("--framework") + 1] for c in calls[1:]] == ["claude", "goose"]
    assert all("--overwrite" in c and "--materialize-native" in c for c in calls[1:])
    contents = {c[c.index("#content") + 1] for c in calls}
    assert len(contents) == 1 and "visual-designer" in contents.pop()      # same roster on every surface


def test_bare_bridge_dir_is_not_rendered(tmp_path, calls):
    root = _instance(tmp_path, (".claude/agents",))
    (root / ".goose" / "recipes").mkdir(parents=True)                      # no build-log: bridge only
    _update_cmd.run_materialize(root, yes=True, dry_run=False)
    assert [c[c.index("--framework") + 1] for c in calls if "--framework" in c] == ["claude"]


def test_copilot_only_keeps_single_surface(tmp_path, calls):
    root = _instance(tmp_path, (".claude/agents", ".goose/recipes"))
    _update_cmd.run_materialize(root, yes=True, dry_run=False, copilot_only=True)
    assert len(calls) == 1 and "--framework" not in calls[0]
