"""frozen_surfaces: the shared agentteams/researchteam contract (researchteam 1.0.1)."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from researchteam import _frozen, _update_cmd


def _repo(tmp_path: Path, frozen=None, recorded: str | None = None) -> Path:
    brief = {"project_name": "demo"}
    if frozen is not None:
        brief["frozen_surfaces"] = frozen
    (tmp_path / "brief.json").write_text(json.dumps(brief))
    marker = "[researchteam]\nref = main\n" + (f"frozen_surfaces = {recorded}\n" if recorded is not None else "")
    (tmp_path / ".researchteam").write_text(marker)
    for d in (".github/agents", ".claude/agents", ".goose/recipes", ".codex/agents"):
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
        (tmp_path / d / "a.md").write_text("original\n")
    (tmp_path / "AGENTS.md").write_text("agents original\n")
    return tmp_path


# --- the key -----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("value, expect", [(None, set()), ([], set()), (["goose", "codex"], {"goose", "codex"})])
def test_valid_values(tmp_path, value, expect):
    assert _frozen.load(_repo(tmp_path, value)) == expect


@pytest.mark.parametrize("value, needle", [
    ("goose", "must be a JSON array"),
    (["goose", "nope"], "unknown id"),
    (["goose", "goose"], "duplicates"),
    ([1], "unknown id"),
])
def test_invalid_values_refuse(tmp_path, value, needle):
    with pytest.raises(_frozen.FrozenSurfacesError, match=needle):
        _frozen.load(_repo(tmp_path, value))


def test_unreadable_brief_refuses(tmp_path):
    (tmp_path / "brief.json").write_text("{not json")
    with pytest.raises(_frozen.FrozenSurfacesError):
        _frozen.load(tmp_path)


@pytest.mark.parametrize("frozen, agents_md", [({"codex"}, True), ({"goose"}, True), ({"agents-md"}, True),
                                               ({"claude"}, False), ({"copilot-vscode"}, False)])
def test_agents_md_freezes_with_any_owner(frozen, agents_md):
    assert ("AGENTS.md" in _frozen.owned_paths(frozenset(frozen))) is agents_md


def test_is_frozen_path():
    f = frozenset({"goose", "claude"})
    assert _frozen.is_frozen_path(".goose/recipes/x.yaml", f) and _frozen.is_frozen_path("./.claude/agents/a.md", f)
    assert _frozen.is_frozen_path("AGENTS.md", f)
    assert not _frozen.is_frozen_path(".claude/README.md", f) and not _frozen.is_frozen_path(".github/agents/a.md", f)
    assert not _frozen.is_frozen_path(".goosefoo/x", f)


def test_record_round_trip(tmp_path):
    root = _repo(tmp_path)
    assert _frozen.recorded(root) == set()
    assert _frozen.record(root, frozenset({"goose", "codex"})) and _frozen.recorded(root) == {"goose", "codex"}
    assert not _frozen.record(root, frozenset({"goose", "codex"}))  # unchanged: no write
    assert _frozen.record(root, frozenset()) and _frozen.recorded(root) == set()
    assert "ref = main" in (root / ".researchteam").read_text()


# --- the guard around update ---------------------------------------------------------------------------------

def _run(monkeypatch, root, body, **kw):
    monkeypatch.setattr(_update_cmd, "_run_update_body", body)
    _update_cmd.run_update(root, ref="main", yes=True, dry_run=False, layer2_only=False, **kw)


def test_a_write_under_a_frozen_surface_fails_closed(tmp_path, monkeypatch):
    root = _repo(tmp_path, ["goose"])
    def body(root_, **kw):
        (root_ / ".goose" / "recipes" / "a.md").write_text("rendered\n")
    with pytest.raises(SystemExit, match="FAILED CLOSED"):
        _run(monkeypatch, root, body)


def test_a_frozen_agents_md_written_by_an_unfrozen_render_is_restored(tmp_path, monkeypatch):
    root = _repo(tmp_path, ["codex"])
    def body(root_, **kw):
        (root_ / "AGENTS.md").write_text("goose render rewrote it\n")
        (root_ / ".goose" / "recipes" / "a.md").write_text("goose is not frozen\n")
    _run(monkeypatch, root, body)
    assert (root / "AGENTS.md").read_text() == "agents original\n"
    assert (root / ".goose" / "recipes" / "a.md").read_text() == "goose is not frozen\n"
    assert _frozen.recorded(root) == {"codex"}


def test_codex_listed_means_no_codex(tmp_path, monkeypatch):
    root = _repo(tmp_path, ["codex"])
    seen = {}
    _run(monkeypatch, root, lambda *a, **kw: seen.setdefault("codex", kw["codex"]))
    assert seen["codex"] is False


def test_unfreeze_refuses_without_a_verified_relaxing_row(tmp_path, monkeypatch):
    root = _repo(tmp_path, [], recorded="goose")
    monkeypatch.setattr(_update_cmd, "_resolve_agentteams", lambda: ("agentteams", "x"))
    monkeypatch.setattr(_frozen, "verify_unfreeze", lambda r, s, e: (False, "no clearing unfreeze-goose row"))
    with pytest.raises(SystemExit, match="Refusing to render into goose"):
        _run(monkeypatch, root, lambda *a, **kw: pytest.fail("must not run"))
    assert _frozen.recorded(root) == {"goose"}  # unchanged


def test_unfreeze_proceeds_only_when_agentteams_verifies_it(tmp_path, monkeypatch, capsys):
    root = _repo(tmp_path, [], recorded="goose")
    monkeypatch.setattr(_update_cmd, "_resolve_agentteams", lambda: ("agentteams", "x"))
    monkeypatch.setattr(_frozen, "verify_unfreeze", lambda r, s, e: (True, "clears; constraint-relaxing; Ed25519"))
    _run(monkeypatch, root, lambda *a, **kw: None)
    assert "unfreeze-goose: verified" in capsys.readouterr().out and _frozen.recorded(root) == set()


def test_invalid_key_refuses_before_anything(tmp_path, monkeypatch):
    root = _repo(tmp_path, ["goose", "goose"])
    with pytest.raises(SystemExit, match="Nothing was changed"):
        _run(monkeypatch, root, lambda *a, **kw: pytest.fail("must not run"))


# --- each write path honours the frozen set -----------------------------------------------------------------

@pytest.fixture
def frozen(monkeypatch):
    def set_(*ids):
        monkeypatch.setattr(_update_cmd, "_FROZEN", frozenset(ids))
    return set_


def test_copilot_render_is_skipped(tmp_path, frozen, monkeypatch):
    frozen("copilot-vscode")
    monkeypatch.setattr(_update_cmd.subprocess, "run", lambda *a, **k: pytest.fail("no render"))
    _update_cmd._run_agentteams(tmp_path, yes=True, dry_run=False)


def test_native_render_skips_frozen_surfaces(tmp_path, frozen, monkeypatch):
    frozen("goose")
    monkeypatch.setattr(_update_cmd, "_native_surfaces", lambda root: [("claude", ".claude/agents"), ("goose", ".goose/recipes")])
    monkeypatch.setattr(_update_cmd, "_warn_scan_divergence", lambda root: None)
    rendered = []
    monkeypatch.setattr(_update_cmd, "_run_agentteams", lambda root, **k: rendered.append(k["framework"]))
    _update_cmd._render_native_surfaces(tmp_path, yes=True, dry_run=False, overwrite=False)
    assert rendered == ["claude"]


def _bridges(tmp_path, monkeypatch):
    for fw in ("claude", "goose"):
        (tmp_path / "references" / "bridges" / f"copilot-vscode-to-{fw}").mkdir(parents=True)
    seen = []

    class R:
        returncode, stdout, stderr = 0, "", ""

    monkeypatch.setattr(_update_cmd, "_preflight_agentteams", lambda: "agentteams")
    monkeypatch.setattr(_update_cmd.subprocess, "run", lambda cmd, **k: seen.append(cmd[cmd.index("--framework") + 1]) or R())
    return seen


def test_bridges_skip_a_frozen_target(tmp_path, frozen, monkeypatch):
    frozen("claude")
    seen = _bridges(tmp_path, monkeypatch)
    _update_cmd._merge_bridges(tmp_path, dry_run=False)
    assert seen == ["goose"]


def test_no_bridge_runs_while_agents_md_is_frozen(tmp_path, frozen, monkeypatch):
    frozen("codex")  # baseAgent-shaped: codex frozen -> AGENTS.md frozen; every bridge merge writes AGENTS.md
    seen = _bridges(tmp_path, monkeypatch)
    _update_cmd._merge_bridges(tmp_path, dry_run=False)
    assert seen == []


def test_mathagents_shaped_consumer(tmp_path, monkeypatch):
    """goose + codex frozen (mathAgents): no Goose render, no Codex, no bridges, AGENTS.md untouched."""
    root = _repo(tmp_path, ["goose", "codex"])
    calls = []
    monkeypatch.setattr(_update_cmd, "_native_surfaces", lambda r: [("claude", ".claude/agents"), ("goose", ".goose/recipes")])
    monkeypatch.setattr(_update_cmd, "_warn_scan_divergence", lambda r: None)
    monkeypatch.setattr(_update_cmd, "_preflight_agentteams", lambda: "agentteams")
    monkeypatch.setattr(_update_cmd, "_reconcile_manifest_back", lambda r: None)

    class R:
        returncode, stdout, stderr = 0, "", ""

    def fake_run(cmd, **k):
        calls.append(cmd)
        if "--framework" in cmd and cmd[cmd.index("--framework") + 1] == "claude":
            (root / ".claude" / "agents" / "a.md").write_text("claude re-rendered\n")
        return R()

    monkeypatch.setattr(_update_cmd.subprocess, "run", fake_run)
    monkeypatch.setattr(_update_cmd, "_print_frozen_summary", lambda *a, **k: None)
    _update_cmd.run_update(root, ref="main", yes=True, dry_run=False, layer2_only=False, layer1_only=True)
    frameworks = [c[c.index("--framework") + 1] for c in calls if "--framework" in c]
    assert "goose" not in frameworks and "codex" not in frameworks and "--bridge-merge" not in sum(calls, [])
    assert (root / "AGENTS.md").read_text() == "agents original\n"
    assert (root / ".goose" / "recipes" / "a.md").read_text() == "original\n"


def test_doctor_reports_frozen_and_pending_unfreeze(tmp_path):
    from researchteam._doctor_cmd import _check_frozen_surfaces
    root = _repo(tmp_path, ["codex"], recorded="codex, goose")
    oks, warns, fails = [], [], []
    _check_frozen_surfaces(root, oks.append, warns.append, fails.append)
    assert any("codex" in o and "AGENTS.md" in o for o in oks)
    assert any("unfreeze pending: goose" in w for w in warns) and not fails
    (root / "brief.json").write_text(json.dumps({"frozen_surfaces": "codex"}))
    _check_frozen_surfaces(root, oks.append, warns.append, fails.append)
    assert fails and "JSON array" in fails[-1]


# --- verification by the pinned agentteams itself ----------------------------------------------------------

def test_agentteams_1_0_0_cannot_verify_an_unfreeze_so_it_refuses(tmp_path):
    """agentteams v1.0.0 derives a bare unfreeze row as non-relaxing (Rule 15 gap), so researchteam refuses."""
    py = os.environ.get("RT_TEST_AGENTTEAMS_PYTHON")
    if not py:
        pytest.skip("set RT_TEST_AGENTTEAMS_PYTHON to an interpreter with agentteams installed")
    launcher = tmp_path / "agentteams"
    launcher.write_text(f"#!{py}\n")
    launcher.chmod(0o755)
    (tmp_path / ".github" / "agents" / "references").mkdir(parents=True)
    ok, why = _frozen.verify_unfreeze(tmp_path, "goose", str(launcher))
    assert not ok and "does not derive an unfreeze" in why



def test_the_check_and_restore_run_even_when_the_body_exits(tmp_path, monkeypatch):
    root = _repo(tmp_path, ["codex"])
    def body(root_, **kw):
        (root_ / "AGENTS.md").write_text("written, then the run failed\n")
        raise SystemExit(2)
    with pytest.raises(SystemExit):
        _run(monkeypatch, root, body)
    assert (root / "AGENTS.md").read_text() == "agents original\n"
    assert _update_cmd._FROZEN == frozenset()          # never leaks into a later call
    assert _frozen.recorded(root) == set()             # a failed run records nothing


def test_dry_run_records_nothing(tmp_path, monkeypatch):
    root = _repo(tmp_path, ["goose"])
    monkeypatch.setattr(_update_cmd, "_run_update_body", lambda *a, **kw: None)
    _update_cmd.run_update(root, ref="main", yes=True, dry_run=True, layer2_only=False)
    assert _frozen.recorded(root) == set()


def test_unfreeze_by_editing_both_working_files_is_still_caught(tmp_path, monkeypatch):
    import subprocess
    root = _repo(tmp_path, ["goose"], recorded="goose")
    for args in (["init", "-q"], ["add", "-A"], ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x"]):
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)
    (root / "brief.json").write_text(json.dumps({"project_name": "demo", "frozen_surfaces": []}))
    (root / ".researchteam").write_text("[researchteam]\nref = main\n")       # record dropped too
    monkeypatch.setattr(_update_cmd, "_resolve_agentteams", lambda: ("agentteams", "x"))
    monkeypatch.setattr(_frozen, "verify_unfreeze", lambda r, s, e: (False, "no row"))
    with pytest.raises(SystemExit, match="Refusing to render into goose"):
        _run(monkeypatch, root, lambda *a, **kw: pytest.fail("must not run"))


def test_materialize_is_guarded_too(tmp_path, monkeypatch):
    root = _repo(tmp_path, ["claude", "codex"])
    seen = {}
    def body(root_, **kw):
        seen.update(kw)
        (root_ / ".claude" / "agents" / "a.md").write_text("overwritten\n")
    monkeypatch.setattr(_update_cmd, "_run_materialize_body", body)
    with pytest.raises(SystemExit, match="FAILED CLOSED"):
        _update_cmd.run_materialize(root, yes=True, dry_run=False)
    assert seen["codex"] is False


def test_layer2_managed_and_notes_skip_frozen_paths(tmp_path, monkeypatch, frozen):
    frozen("copilot-vscode")
    assert _update_cmd._is_frozen(".github/agents/interpretation-advisor.agent.md")
    assert not _update_cmd._is_frozen("docs/researchteam-framework.md")
    rel = ".github/agents/interpretation-advisor.agent.md"
    monkeypatch.setattr(_update_cmd, "managed_files_for", lambda profile: [rel])
    monkeypatch.setattr(_update_cmd, "fetch_raw", lambda *a: pytest.fail("a frozen managed file must not be fetched"))
    monkeypatch.setattr(_update_cmd, "_sync_notes", lambda *a, **k: None)
    root = _repo(tmp_path)
    _update_cmd._run_update_body(root, ref="main", yes=True, dry_run=False, layer2_only=True)
