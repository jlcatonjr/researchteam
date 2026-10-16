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
    monkeypatch.setattr(_update_cmd, "_require_p5a", lambda exe: None)
    def fake_run(cmd, cwd=None, **_):
        if "--description" in cmd:
            desc = Path(cwd) / cmd[cmd.index("--description") + 1]
            cmd = cmd + ["#content", desc.read_text()]         # capture before the temp file is removed
        seen.append(cmd)
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
    calls[:] = [c for c in calls if "--interop-from" not in c]
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


def _renders(calls):
    return [c for c in calls if "--overwrite" in c and "--interop-from" not in c]


def test_adopt_orphans_reaches_every_surface(tmp_path, calls):
    root = _instance(tmp_path, (".claude/agents", ".goose/recipes"))
    _update_cmd.run_materialize(root, yes=True, dry_run=False, adopt_orphans=True)
    assert len(_renders(calls)) == 3 and all("--adopt-orphans" in c for c in _renders(calls))



def test_user_regions_carried_by_default_discarded_on_request(tmp_path, calls):
    root = _instance(tmp_path, (".claude/agents", ".goose/recipes"))
    _update_cmd.run_materialize(root, yes=True, dry_run=False)
    assert not any("--discard-user-regions" in c for c in calls)            # P5a carries them by default
    calls.clear()
    _update_cmd.run_materialize(root, yes=True, dry_run=False, discard_user_regions=True)
    assert len(_renders(calls)) == 3 and all("--discard-user-regions" in c for c in _renders(calls))
    assert not any("--discard-user-regions" in c for c in calls if "--interop-from" in c)


def test_pre_p5a_agentteams_stops_materialize_before_any_render(tmp_path, calls, monkeypatch):
    root = _instance(tmp_path, (".claude/agents",))
    def refuse(exe):
        raise SystemExit("predates agentteams P5a")
    monkeypatch.setattr(_update_cmd, "_require_p5a", refuse)
    with pytest.raises(SystemExit, match="P5a"):
        _update_cmd.run_materialize(root, yes=True, dry_run=False)
    assert calls == []

def _codex_orchestrator_only(root: Path) -> None:
    brief = json.loads((root / "brief.json").read_text())
    brief.update({"write_policy": "orchestrator-only", "write_policy_frameworks": ["codex"],
                  "privilege_profile": "confined"})
    (root / "brief.json").write_text(json.dumps(brief))


def test_codex_without_orchestrator_only_fails_before_agentteams(tmp_path, calls):
    root = _instance(tmp_path, (".claude/agents",))
    (root / ".codex" / "agents").mkdir(parents=True)
    (root / ".claude" / "skills").mkdir(parents=True)
    with pytest.raises(SystemExit, match=r"agentteams #210 refuses .* Nothing under \.codex was changed"):
        _update_cmd.run_materialize(root, yes=True, dry_run=False)
    assert not any("--interop-from" in c for c in calls)          # neither agents nor skills projected
    assert not any("codex" in c for c in calls)                   # no codex render either
    assert len(_renders(calls)) == 2                              # the other surfaces were rendered first


def test_codex_refusal_is_reported_not_fatal_in_dry_run(tmp_path, calls, capsys):
    root = _instance(tmp_path, ())
    (root / ".codex" / "agents").mkdir(parents=True)
    _update_cmd._refresh_codex(root, dry_run=True)
    assert "agentteams #210 refuses" in capsys.readouterr().out
    assert calls == []


def test_codex_under_orchestrator_only_renders_natively(tmp_path, calls):
    root = _instance(tmp_path, ())
    _codex_orchestrator_only(root)
    (root / ".codex" / "agents").mkdir(parents=True)
    (root / ".claude" / "skills").mkdir(parents=True)
    _update_cmd._refresh_codex(root, dry_run=False)
    codex = [c for c in calls if "--framework" in c and c[c.index("--framework") + 1] == "codex"]
    assert len(codex) == 2
    assert "--materialize-native" in codex[0] and "--interop-from" not in codex[0]   # native, not projected
    assert "--interop-skills-only" in codex[1]                    # skills projection survives #210
    assert not any("--interop-from" in c and ".github/agents" in c for c in calls)


def test_no_codex_surface_or_opt_out_skips_codex(tmp_path, calls):
    root = _instance(tmp_path, (".claude/agents",))
    _update_cmd.run_materialize(root, yes=True, dry_run=False)             # no .codex dir: no-op
    (root / ".codex" / "agents").mkdir(parents=True)
    _update_cmd.run_materialize(root, yes=True, dry_run=False, codex=False)  # opted out: no refusal
    assert not any("codex" in c for c in calls)


def test_update_layer1_refreshes_codex_after_the_merge(tmp_path, calls):
    root = _instance(tmp_path, ())
    _codex_orchestrator_only(root)
    (root / ".codex" / "agents").mkdir(parents=True)
    _update_cmd.run_update(root, ref="main", yes=True, dry_run=False, layer2_only=False, layer1_only=True)
    merge = [c for c in calls if "--merge" in c]
    codex = [c for c in merge if "codex" in c]
    assert codex and calls.index(codex[0]) > calls.index(merge[0])
    assert not any("--interop-from" in c for c in calls)


def test_codex_leftovers_are_named_not_deleted(tmp_path, capsys):
    agents = tmp_path / ".codex" / "agents"
    (agents / "references").mkdir(parents=True)
    for name in ("orchestrator.toml", "navigator.toml", "tool-pandoc.toml"):
        (agents / name).write_text("name = 'x'\n")
    log = agents / "references" / "build-log.json"
    log.write_text(json.dumps({"origin": "interop", "file_hashes": {"orchestrator.toml": "x"}}))
    assert _update_cmd._warn_codex_leftovers(tmp_path) == []  # a projection's record: no comparison
    log.write_text(json.dumps({"file_hashes": {"orchestrator.toml": "a", "navigator.toml": "b",
                                               "../../.agents/skills/tool-pandoc/SKILL.md": "c"}}))
    assert _update_cmd._warn_codex_leftovers(tmp_path) == ["tool-pandoc.toml"]
    assert "tool-pandoc.toml" in capsys.readouterr().err
    assert (agents / "tool-pandoc.toml").exists()


def test_codex_roster_agents_are_not_leftovers(tmp_path):
    agents = tmp_path / ".codex" / "agents"
    (agents / "references").mkdir(parents=True)
    for name in ("orchestrator.toml", "interpretation-advisor.toml", "tool-pandoc.toml"):
        (agents / name).write_text("name = 'x'\n")
    (agents / "references" / "build-log.json").write_text(json.dumps(
        {"file_hashes": {"orchestrator.toml": "a"}, "agent_slug_list": ["orchestrator", "interpretation-advisor"]}))
    assert _update_cmd._warn_codex_leftovers(tmp_path) == ["tool-pandoc.toml"]


@pytest.mark.parametrize("layer1_only", [True, False])
def test_update_no_codex_never_refreshes_codex(tmp_path, calls, monkeypatch, capsys, layer1_only):
    # Frozen Codex (release policy section 5): no orchestrator-only switch, so a refresh would refuse.
    root = _instance(tmp_path, ())
    (root / ".codex" / "agents").mkdir(parents=True)
    (root / ".claude" / "skills").mkdir(parents=True)
    monkeypatch.setattr(_update_cmd, "managed_files_for", lambda profile: [])
    monkeypatch.setattr(_update_cmd, "_sync_notes", lambda *a, **k: None)
    monkeypatch.setattr(_update_cmd, "_refresh_codex", lambda *a, **k: pytest.fail("_refresh_codex called"))
    _update_cmd.run_update(root, ref="main", yes=True, dry_run=False, layer2_only=False,
                           layer1_only=layer1_only, codex=False)
    assert not any("codex" in c for c in calls)                   # no render, no skills projection
    out = capsys.readouterr().out
    assert out.count("Codex surface left unchanged") == 1


@pytest.mark.parametrize("layer1_only", [True, False])
def test_update_without_no_codex_still_refreshes_codex(tmp_path, calls, monkeypatch, layer1_only):
    root = _instance(tmp_path, ())
    monkeypatch.setattr(_update_cmd, "managed_files_for", lambda profile: [])
    monkeypatch.setattr(_update_cmd, "_sync_notes", lambda *a, **k: None)
    refreshed: list[bool] = []
    monkeypatch.setattr(_update_cmd, "_refresh_codex", lambda root, dry_run: refreshed.append(dry_run))
    _update_cmd.run_update(root, ref="main", yes=True, dry_run=False, layer2_only=False,
                           layer1_only=layer1_only)
    assert refreshed == [False]


def test_codex_refusal_offers_no_codex(tmp_path, calls):
    root = _instance(tmp_path, ())
    (root / ".codex" / "agents").mkdir(parents=True)
    with pytest.raises(SystemExit) as exc:
        _update_cmd._refresh_codex(root, dry_run=False)
    assert "--no-codex" in str(exc.value) and "orchestrator-only" in str(exc.value)


@pytest.mark.parametrize("argv, codex", [(["update"], True), (["update", "--no-codex"], False)])
def test_cli_update_plumbs_no_codex(tmp_path, monkeypatch, argv, codex):
    from researchteam import cli
    seen: dict = {}
    monkeypatch.setattr(cli, "_find_repo_root", lambda require_marker=False: tmp_path)
    monkeypatch.setattr(cli, "_read_marker_ref", lambda root: "main")
    monkeypatch.setattr(_update_cmd, "run_update", lambda root, **kw: seen.update(kw))
    monkeypatch.setattr("sys.argv", ["researchteam", *argv])
    cli.main()
    assert seen["codex"] is codex
