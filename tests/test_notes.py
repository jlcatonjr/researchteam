"""OrthodoxLLM Item 1: managed advisor (above-notes) and upstream-authored Notes blocks (_notes.py)."""
from __future__ import annotations

from pathlib import Path

import pytest

from researchteam import _notes, _update_cmd
from researchteam._manifest import MERGE_STRATEGIES, SCHOLARLY_MANAGED_FILES, SEEDED_FILES, managed_files_for

ROOT = Path(__file__).resolve().parent.parent
ADVISOR = ".github/agents/interpretation-advisor.agent.md"
TEMPLATE = ".github/agents/references/methodology/_TEMPLATE.methodology.guide.md"
QUOTE = "> ⚙️ **USER-EDITABLE** — project-specific rules, overrides, and extensions for this agent.\n"

INNER = """- **Outlet perspective:** never call a news account neutral.

### Historical setting
Date every source.
"""


def _agent(notes: str, tail: str = "") -> str:
    return "---\nname: x\n---\n<!-- AGENTTEAMS:BEGIN content v=1 -->\nbody\n<!-- AGENTTEAMS:END content -->\n\n" \
           "## Project-Specific Notes\n\n" + QUOTE + notes + tail


# --- manifest ---------------------------------------------------------------------------------------

def test_advisor_and_template_are_scholarly_managed():
    assert ADVISOR in SCHOLARLY_MANAGED_FILES and TEMPLATE in SCHOLARLY_MANAGED_FILES
    assert ADVISOR not in managed_files_for("generic")
    assert MERGE_STRATEGIES[ADVISOR] == "above-notes" and TEMPLATE not in MERGE_STRATEGIES  # template: overwrite
    assert SEEDED_FILES == []


# --- above-notes ----------------------------------------------------------------------------------

def test_above_notes_takes_upstream_head_and_keeps_repo_notes():
    local = "---\nname: old\n---\nold body\n\n## Project-Specific Notes\n\nOur own rule.\n"
    remote = "---\nname: new\n---\nnew body\n\n## Project-Specific Notes\n\n> placeholder\n"
    new, diff = _update_cmd._reconcile_above_notes(ADVISOR, local, remote)
    assert new == "---\nname: new\n---\nnew body\n\n## Project-Specific Notes\n\nOur own rule.\n"
    assert any("name: new" in d for d in diff) and not any("Our own rule" in d for d in diff)


def test_above_notes_is_idempotent_and_adopts_upstream_notes_when_local_has_none():
    remote = "head\n\n## Project-Specific Notes\n\n> placeholder\n"
    assert _update_cmd._reconcile_above_notes(ADVISOR, remote, remote) == (None, [])
    new, _ = _update_cmd._reconcile_above_notes(ADVISOR, "a local file without notes\n", remote)
    assert new == remote


def test_above_notes_keeps_local_when_upstream_lacks_the_heading(capsys):
    new, warn = _update_cmd._reconcile_above_notes(ADVISOR, "local\n", "upstream without notes\n")
    assert new is None and warn and "kept local unchanged" in capsys.readouterr().out


def test_backup_lands_in_gitignored_tmp(tmp_path):
    saved = _update_cmd._backup(tmp_path, ADVISOR, "old")
    assert saved.read_text() == "old" and saved.relative_to(tmp_path).parts[:2] == ("tmp", "researchteam-backups")


# --- notes block ----------------------------------------------------------------------------------

def test_block_is_inserted_after_the_quote_and_is_idempotent():
    text = _agent("\n### Our own rule\nKeep it.\n")
    new, folded = _notes.apply_block(text, INNER)
    assert folded == []
    notes = new[new.index("## Project-Specific Notes"):]
    assert notes.index(QUOTE.strip()) < notes.index(_notes.BEGIN) < notes.index(_notes.END) < notes.index("### Our own rule")
    assert _notes.apply_block(new, INNER) == (new, [])
    assert new[:new.index("## Project-Specific Notes")] == text[:text.index("## Project-Specific Notes")]


def test_existing_block_is_replaced_and_outside_text_untouched():
    old_inner = "### Historical setting\nOld wording.\n"
    first, _ = _notes.apply_block(_agent("\n### Our own rule\nKeep it.\n"), old_inner)
    second, _ = _notes.apply_block(first, INNER)
    assert "Old wording." not in second and "Date every source." in second and "### Our own rule\nKeep it." in second


def test_first_adoption_folds_hand_copied_subsections_and_bullets():
    copied = ("\n- **Outlet perspective:** never call a news account neutral.\n\n"
              "### Historical setting\nAn older hand copy.\n\n"
              "### Our own rule\nKeep it.\n")
    new, folded = _notes.apply_block(_agent(copied), INNER)
    assert folded == ["- **Outlet perspective:** never call a news account neutral.", "Historical setting"]
    assert "An older hand copy." not in new and new.count("### Historical setting") == 1
    assert new.count("Outlet perspective") == 1 and "### Our own rule\nKeep it." in new


def test_notes_section_ends_at_the_next_level_two_heading():
    text = _agent("\n### Ours\nx\n", tail="\n## Another section\n\n### Historical setting\nnot in Notes\n")
    new, folded = _notes.apply_block(text, INNER)
    assert folded == [] and "### Historical setting\nnot in Notes" in new  # outside Notes: never folded


def test_goose_recipe_gets_an_indented_block_that_stays_valid_yaml():
    yaml = pytest.importorskip("yaml")
    recipe = ("version: 1.0.0\ntitle: x\ninstructions: |\n  ## Role\n\n  body\n\n"
              "  ## Project-Specific Notes\n\n  > USER-EDITABLE\n\n"
              "  ### Historical setting\n  hand copy\n\n"
              "  ## Delegation & references (Goose)\n\n  load recipes\nprompt: go\n")
    new, folded = _notes.apply_block(recipe, INNER, indent="  ")
    data = yaml.safe_load(new)
    ins = data["instructions"]
    assert folded == ["Historical setting"] and "hand copy" not in ins
    assert ins.index(_notes.BEGIN) < ins.index("Date every source.") < ins.index("## Delegation & references (Goose)")
    assert data["prompt"] == "go"


def test_unreconcilable_inputs_raise_notes_error():
    with pytest.raises(_notes.NotesError):
        _notes.apply_block("no notes here\n", INNER)
    bad = "## Project-Specific Notes\n\n" + _notes.BEGIN + "\n## Not allowed\n" + _notes.END + "\n"
    with pytest.raises(_notes.NotesError):
        _notes.extract_block(bad)
    with pytest.raises(_notes.NotesError):
        _notes.apply_block("## Project-Specific Notes\n\n" + _notes.BEGIN + "\nno end\n", INNER)


# --- end to end ------------------------------------------------------------------------------------

def test_sync_writes_every_surface_and_backs_up(tmp_path, monkeypatch):
    agent = "main-analysis-expert"
    src = tmp_path / _notes.source_path(agent)
    src.parent.mkdir(parents=True)
    src.write_text(_notes.apply_block(_agent(""), INNER)[0])
    claude = tmp_path / ".claude" / "agents" / f"{agent}.md"
    claude.parent.mkdir(parents=True)
    claude.write_text(_agent("\n### Historical setting\nhand copy\n"))
    monkeypatch.setattr(_notes, "NOTES_AGENTS", (agent,))
    _update_cmd._sync_notes(tmp_path, None, yes=True, dry_run=False)
    assert _notes.extract_block(claude.read_text()) == INNER and "hand copy" not in claude.read_text()
    assert list((tmp_path / "tmp" / "researchteam-backups").rglob(f"{agent}.md"))


def test_derived_sync_reads_blocks_from_upstream_at_the_ref(tmp_path, monkeypatch):
    agent = "topic-scoping-expert"
    local = tmp_path / _notes.source_path(agent)
    local.parent.mkdir(parents=True)
    local.write_text(_agent("\n### Ours\nx\n"))
    asked = []
    monkeypatch.setattr(_notes, "NOTES_AGENTS", (agent,))
    monkeypatch.setattr(_update_cmd, "fetch_raw",
                        lambda repo, ref, path: asked.append((ref, path)) or _notes.apply_block(_agent(""), INNER)[0])
    _update_cmd._sync_notes(tmp_path, "abc123", yes=True, dry_run=True)
    assert asked == [("abc123", _notes.source_path(agent))] and _notes.BEGIN not in local.read_text()  # dry run
    _update_cmd._sync_notes(tmp_path, "abc123", yes=True, dry_run=False)
    assert _notes.extract_block(local.read_text()) == INNER and "### Ours\nx" in local.read_text()


# --- upstream invariants ---------------------------------------------------------------------------

@pytest.mark.parametrize("agent", _notes.NOTES_AGENTS)
def test_upstream_blocks_exist_and_every_surface_carries_the_same_block(agent):
    inner = _notes.extract_block((ROOT / _notes.source_path(agent)).read_text(encoding="utf-8"))
    assert inner and inner.strip()
    for path, indent in _notes.surfaces(ROOT, agent):
        text = path.read_text(encoding="utf-8")
        if f"{indent}## Project-Specific Notes" not in text:
            continue  # a surface without a Notes section is reported and skipped by the sync
        assert _notes.apply_block(text, inner, indent)[0] == text, f"{path} is out of sync with upstream"


# --- audit follow-ups -------------------------------------------------------------------------------

FM = "---\nname: x\ntools: ['read', 'search']\nagents: ['a']\nhandoffs:\n  - label: L\n    agent: a\n---\n"


def test_grant_widening_is_detected_and_narrowing_is_not():
    wider = FM.replace("['read', 'search']", "['read', 'search', 'execute']").replace("agent: a\n", "agent: b\n")
    assert _update_cmd._grant_widening(FM + "body", wider + "body") == ["tools: +execute", "handoffs: +b"]
    narrower = FM.replace("['read', 'search']", "['read']")
    assert _update_cmd._grant_widening(FM + "body", narrower + "body") == []


def _layer2_only(tmp_path, monkeypatch, local: str, remote: str, yes: bool) -> str:
    (tmp_path / ".github" / "agents").mkdir(parents=True)
    (tmp_path / ADVISOR).write_text(local)
    monkeypatch.setattr(_update_cmd, "managed_files_for", lambda profile: [ADVISOR])
    monkeypatch.setattr(_update_cmd, "fetch_raw", lambda repo, ref, path: remote)
    monkeypatch.setattr(_update_cmd, "_sync_notes", lambda *a, **k: None)
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")
    _update_cmd.run_update(tmp_path, ref="main", yes=yes, dry_run=False, layer2_only=True, layer1_only=False)
    return (tmp_path / ADVISOR).read_text()


def test_unattended_update_refuses_a_widening_advisor(tmp_path, monkeypatch, capsys):
    local = FM + "old body\n\n## Project-Specific Notes\n\nours\n"
    remote = FM.replace("['read', 'search']", "['read', 'search', 'execute']") + "new body\n\n## Project-Specific Notes\n"
    assert _layer2_only(tmp_path, monkeypatch, local, remote, yes=True) == local
    assert "WIDENS capability grants (tools: +execute)" in capsys.readouterr().out
    assert not (tmp_path / "tmp" / "researchteam-backups").exists()


def test_update_replaces_advisor_head_backs_up_and_keeps_notes(tmp_path, monkeypatch, capsys):
    local = FM + "old body\n\n## Project-Specific Notes\n\nours\n"
    remote = FM + "new body\n\n## Project-Specific Notes\n\n> placeholder\n"
    assert _layer2_only(tmp_path, monkeypatch, local, remote, yes=True) == FM + "new body\n\n## Project-Specific Notes\n\nours\n"
    backups = list((tmp_path / "tmp" / "researchteam-backups").rglob("interpretation-advisor.agent.md"))
    assert len(backups) == 1 and backups[0].read_text() == local
    assert "+new body" in capsys.readouterr().out  # the diff is shown even unattended


def test_upstream_layer1_run_propagates_its_own_blocks(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(_update_cmd, "_run_agentteams", lambda *a, **k: None)
    monkeypatch.setattr(_update_cmd, "_refresh_codex", lambda *a, **k: None)
    monkeypatch.setattr(_update_cmd, "_sync_notes", lambda root, ref, **k: calls.append(ref))
    import researchteam._personalize as p
    monkeypatch.setattr(p, "is_upstream", lambda root: True)
    _update_cmd.run_update(tmp_path, ref="main", yes=True, dry_run=False, layer2_only=False, layer1_only=True)
    assert calls == [None]  # reads the repo's own .github blocks
    monkeypatch.setattr(p, "is_upstream", lambda root: False)
    _update_cmd.run_update(tmp_path, ref="main", yes=True, dry_run=False, layer2_only=False, layer1_only=True)
    assert calls == [None]  # derived repos get blocks only from the layer-2 sync


def test_goose_notes_as_the_last_section_stop_at_the_next_yaml_key():
    yaml = pytest.importorskip("yaml")
    recipe = ("title: x\ninstructions: |\n  ## Role\n\n  ## Project-Specific Notes\n\n  > USER-EDITABLE\n"
              "extensions:\n  - type: builtin\n    name: developer\n")
    new, folded = _notes.apply_block(recipe, INNER, indent="  ")
    data = yaml.safe_load(new)
    assert folded == [] and "Date every source." in data["instructions"]
    assert data["extensions"] == [{"type": "builtin", "name": "developer"}]


def test_notes_without_a_quote_and_without_a_final_newline():
    text = "body\n\n## Project-Specific Notes\n### Ours\nx"
    new, _ = _notes.apply_block(text, INNER)
    assert new.endswith("### Ours\nx\n") and new.index(_notes.BEGIN) < new.index("### Ours")
    assert _notes.apply_block(new, INNER)[0] == new


def test_repo_text_outside_the_block_keeps_its_blank_lines():
    own = "\n### Ours\n\n\n\nspaced on purpose\n"
    new, _ = _notes.apply_block(_agent(own), INNER)
    assert "### Ours\n\n\n\nspaced on purpose\n" in new


def test_indented_level_two_heading_in_a_block_is_refused():
    bad = "## Project-Specific Notes\n\n" + _notes.BEGIN + "\n  ## sneaky\n" + _notes.END + "\n"
    with pytest.raises(_notes.NotesError):
        _notes.extract_block(bad)


def test_surfaces_skip_symlinks_that_leave_the_repo(tmp_path):
    outside = tmp_path / "outside.md"
    outside.write_text("x")
    root = tmp_path / "repo"
    (root / ".claude" / "agents").mkdir(parents=True)
    (root / ".claude" / "agents" / "main-analysis-expert.md").symlink_to(outside)
    assert _notes.surfaces(root, "main-analysis-expert") == []
