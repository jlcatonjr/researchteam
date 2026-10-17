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


PIN = "a" * 40


def _layer2_only(tmp_path, monkeypatch, local: str, remote: str, yes: bool, pinned: str | None = None,
                 accept: tuple[str, ...] = (), dry_run: bool = False, answer: str = "y") -> str:
    """Run the layer-2 sync of the advisor alone. ``pinned`` is upstream's copy at the toolchain.lock
    pin (default: the local file, i.e. un-customised); an exception instance is raised by its fetch."""
    (tmp_path / ".github" / "agents").mkdir(parents=True)
    (tmp_path / ADVISOR).write_text(local)
    (tmp_path / "toolchain.lock").write_text(f"researchteam=jlcatonjr/researchteam@{PIN}\n")
    pinned = local if pinned is None else pinned

    def fetch(repo, ref, path):
        if ref != PIN:
            return remote
        if isinstance(pinned, Exception):
            raise pinned
        return pinned

    monkeypatch.setattr(_update_cmd, "managed_files_for", lambda profile: [ADVISOR])
    monkeypatch.setattr(_update_cmd, "fetch_raw", fetch)
    monkeypatch.setattr(_update_cmd, "_sync_notes", lambda *a, **k: None)
    monkeypatch.setattr("builtins.input", lambda prompt="": answer)
    _update_cmd.run_update(tmp_path, ref="main", yes=yes, dry_run=dry_run, layer2_only=True, layer1_only=False,
                           accept_upstream=accept)
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


# --- above-notes: a customised advisor is kept (mathAgents) ------------------------------------------

PINNED = FM.replace("name: x", "name: Interpretation Advisor\ndescription: generic") + \
    "generic body v1\n\n## Project-Specific Notes\n\n> placeholder\n"
REMOTE = PINNED.replace("generic body v1", "generic body v2")
CUSTOM = FM.replace("name: x", "name: Interpretation Advisor — mathAgents\ndescription: proofs and models") + \
    "mathAgents body\n\n## Project-Specific Notes\n\nours\n"


def test_pristine_advisor_upgrades(tmp_path, monkeypatch, capsys):
    local = PINNED.replace("> placeholder", "ours")
    assert _layer2_only(tmp_path, monkeypatch, local, REMOTE, yes=True, pinned=PINNED) == REMOTE.replace("> placeholder", "ours")
    assert "customised" not in capsys.readouterr().out
    assert list((tmp_path / "tmp" / "researchteam-backups").rglob("interpretation-advisor.agent.md"))


def test_pristine_check_ignores_trailing_whitespace_before_notes_only(tmp_path):
    (tmp_path / "toolchain.lock").write_text(f"researchteam=jlcatonjr/researchteam@{PIN}\n")
    trailing = PINNED.replace("v1\n\n## Project-Specific Notes", "v1  \n\n\n## Project-Specific Notes")
    assert _update_cmd._above_notes_pristine(tmp_path, ADVISOR, trailing, PIN, PINNED) == (True, f"upstream @{PIN[:12]}")
    inner = PINNED.replace("name: Interpretation Advisor", "name: Interpretation Advisor ")
    assert _update_cmd._above_notes_pristine(tmp_path, ADVISOR, inner, PIN, PINNED)[0] is False


def test_customised_advisor_is_kept_under_yes(tmp_path, monkeypatch, capsys):
    assert _layer2_only(tmp_path, monkeypatch, CUSTOM, REMOTE, yes=True, pinned=PINNED) == CUSTOM
    out = capsys.readouterr().out
    assert (f"[above-notes] {ADVISOR}: customised locally (differs from upstream @{PIN[:12]}); "
            "kept local unchanged") in out
    assert f"--accept-upstream {ADVISOR}" in out and "1 skipped" in out
    assert not (tmp_path / "tmp" / "researchteam-backups").exists()


def test_customised_advisor_interactive_defaults_to_keep(tmp_path, monkeypatch, capsys):
    assert _layer2_only(tmp_path, monkeypatch, CUSTOM, REMOTE, yes=False, pinned=PINNED, answer="") == CUSTOM
    out = capsys.readouterr().out
    assert "approving below REPLACES it" in out and "+generic body v2" in out  # the diff is shown


def test_customised_advisor_dry_run_writes_nothing(tmp_path, monkeypatch, capsys):
    assert _layer2_only(tmp_path, monkeypatch, CUSTOM, REMOTE, yes=False, pinned=PINNED, dry_run=True) == CUSTOM
    assert f"[dry-run] Would keep: {ADVISOR}" in capsys.readouterr().out
    assert not (tmp_path / "tmp").exists()


def test_unverifiable_pin_keeps_local(tmp_path, monkeypatch, capsys):
    out = _layer2_only(tmp_path, monkeypatch, CUSTOM, REMOTE, yes=True, pinned=RuntimeError("HTTP 404"))
    assert out == CUSTOM and "not verified as un-customised: could not fetch upstream" in capsys.readouterr().out


def test_odd_pinned_ref_is_never_fetched_and_keeps_local(tmp_path, monkeypatch):
    (tmp_path / ".researchteam").write_text("ref = ../../evil?x=1\n")
    monkeypatch.setattr(_update_cmd, "fetch_raw", lambda *a: pytest.fail("must not fetch"))
    verdict, detail = _update_cmd._above_notes_pristine(tmp_path, ADVISOR, CUSTOM, "main", REMOTE)
    assert verdict is None and "not a plain commit or name" in detail


def test_accept_upstream_replaces_a_customised_advisor(tmp_path, monkeypatch):
    out = _layer2_only(tmp_path, monkeypatch, CUSTOM, REMOTE, yes=True, pinned=PINNED, accept=(f"./{ADVISOR}",))
    assert out == REMOTE.replace("> placeholder", "ours")
    backups = list((tmp_path / "tmp" / "researchteam-backups").rglob("interpretation-advisor.agent.md"))
    assert len(backups) == 1 and backups[0].read_text() == CUSTOM


def test_accept_upstream_still_refuses_a_widening_under_yes(tmp_path, monkeypatch, capsys):
    wider = REMOTE.replace("['read', 'search']", "['read', 'search', 'execute']")
    assert _layer2_only(tmp_path, monkeypatch, CUSTOM, wider, yes=True, pinned=PINNED, accept=(ADVISOR,)) == CUSTOM
    assert "WIDENS capability grants (tools: +execute)" in capsys.readouterr().out


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


# --- experts come from the brief, not the scaffold (masterTeacher 4.3) ------------------------------

import json  # noqa: E402
import re  # noqa: E402

from researchteam._manifest import MANAGED_FILES  # noqa: E402

DEFAULT_EXPERT = re.compile(r"@(topic-scoping|literature-review|main-analysis|conclusion)-expert")
CUSTOM_COMPONENTS = ("tutoring-dialogue", "subject-pedagogy")


def _brief(root: Path, slugs) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "brief.json").write_text(json.dumps({"components": [{"slug": s, "name": s} for s in slugs]}))


def test_researchteams_own_brief_keeps_every_notes_agent():
    assert _notes.agents_for(ROOT) == _notes.NOTES_AGENTS


def test_custom_components_drop_the_scaffold_experts(tmp_path):
    _brief(tmp_path, CUSTOM_COMPONENTS)
    assert _notes.agents_for(tmp_path) == ("interpretation-advisor",)
    _brief(tmp_path, ("topic-scoping", "main-analysis", "conclusion"))  # the scaffold's default brief
    assert _notes.agents_for(tmp_path) == ("interpretation-advisor", "topic-scoping-expert", "main-analysis-expert")


def test_without_a_readable_brief_every_agent_is_considered(tmp_path):
    assert _notes.agents_for(tmp_path) == _notes.NOTES_AGENTS
    (tmp_path / "brief.json").write_text("{not json")
    assert _notes.agents_for(tmp_path) == _notes.NOTES_AGENTS


def test_custom_brief_sync_skips_stale_and_custom_experts(tmp_path, monkeypatch):
    _brief(tmp_path, CUSTOM_COMPONENTS)
    agents = tmp_path / ".github" / "agents"
    agents.mkdir(parents=True)
    files = {a: agents / f"{a}.agent.md" for a in ("interpretation-advisor", "topic-scoping-expert",
                                                   "tutoring-dialogue-expert")}
    for path in files.values():
        path.write_text(_agent("\n### Ours\nx\n"))
    files["interpretation-advisor"].write_text(_pristine_advisor())  # a customised one is skipped
    before = {a: p.read_text() for a, p in files.items()}
    asked = []
    monkeypatch.setattr(_update_cmd, "fetch_raw", lambda repo, ref, path: asked.append(path)
                        or (ROOT / path).read_text(encoding="utf-8"))
    _update_cmd._sync_notes(tmp_path, "abc123", yes=True, dry_run=False)
    assert asked == [_notes.source_path("interpretation-advisor")]  # no expert block is even fetched
    assert _notes.BEGIN in files["interpretation-advisor"].read_text()
    for a in ("topic-scoping-expert", "tutoring-dialogue-expert"):
        assert files[a].read_text() == before[a]
    for path in agents.iterdir():
        assert not DEFAULT_EXPERT.search(path.read_text()), path


def _shipped(rel: str) -> str:
    """The upstream-owned part of a managed file: what `update` writes into a derived repo."""
    text = (ROOT / rel).read_text(encoding="utf-8")
    if MERGE_STRATEGIES.get(rel) == "fenced-preserve":
        split = _update_cmd._split_fence(text)
        return split[1] if split else ""
    if MERGE_STRATEGIES.get(rel) == "above-notes":
        return _update_cmd._split_above_notes(text)[0]
    return text


@pytest.mark.parametrize("rel", MANAGED_FILES)
def test_managed_files_name_no_scaffold_expert(rel):
    assert not DEFAULT_EXPERT.search(_shipped(rel)), f"{rel} ships a scaffold expert handle"


@pytest.mark.parametrize("name", ["CLAUDE.template.md", "README.template.md", "brief.template.json"])
def test_scaffold_templates_name_no_scaffold_expert(name):
    text = (ROOT / "researchteam" / "scaffold" / name).read_text(encoding="utf-8")
    assert not DEFAULT_EXPERT.search(text)


def test_non_expert_notes_blocks_name_no_scaffold_expert():
    for agent in _notes.NOTES_AGENTS:
        if not agent.endswith(_notes.EXPERT_SUFFIX):
            assert not DEFAULT_EXPERT.search(_notes.extract_block((ROOT / _notes.source_path(agent)).read_text()))


def test_pristine_advisor_with_the_old_handles_upgrades_to_the_generic_text(tmp_path, monkeypatch):
    remote = (ROOT / ADVISOR).read_text(encoding="utf-8")
    old_row = ("| The interpretive **scaffolding** — how to read each school on its own terms | The literature's "
               "**themes/debates** and research-gap prose (`@literature-review-expert`) |\n")
    head, notes = _update_cmd._split_above_notes(remote)
    row = next(ln for ln in head.splitlines(keepends=True) if ln.startswith("| The interpretive **scaffolding**"))
    pinned = head.replace(row, old_row) + notes
    local = pinned.replace(_notes.NOTES_HEADING, _notes.NOTES_HEADING + "\n\nours", 1)
    out = _layer2_only(tmp_path, monkeypatch, local, remote, yes=True, pinned=pinned)
    assert out == head + _update_cmd._split_above_notes(local)[1]
    assert not DEFAULT_EXPERT.search(_update_cmd._split_above_notes(out)[0])


# --- a customised or excluded agent gets no notes block (mathAgents) -------------------------------

ADVISOR_SLUG = "interpretation-advisor"
UPSTREAM_ADVISOR = (ROOT / ADVISOR).read_text(encoding="utf-8")
_BLOCK = _notes.extract_block(UPSTREAM_ADVISOR).splitlines(keepends=True)
DUP = next("".join(_BLOCK[s:e]) for key, s, e in _notes._units(_BLOCK, "") if key.startswith("b:"))  # hand copy


def _pristine_advisor(notes: str = "\n### Ours\nx\n") -> str:
    """researchteam's advisor above Notes (un-customised) with a repo's own Notes below."""
    return _update_cmd._split_above_notes(UPSTREAM_ADVISOR)[0] + _notes.NOTES_HEADING + "\n\n" + QUOTE + notes


def _advisor_surfaces(root: Path, github: str, pinned=UPSTREAM_ADVISOR, brief: dict | None = None) -> dict:
    """The advisor on .github, .claude and .goose (each holding a hand copy the sync would fold), and
    upstream fetches: ``main`` serves researchteam's advisor, the toolchain.lock pin serves ``pinned``."""
    files = {root / ADVISOR: github,
             root / ".claude" / "agents" / f"{ADVISOR_SLUG}.md": _agent("\n" + DUP),
             root / ".goose" / "recipes" / f"{ADVISOR_SLUG}.yaml":
                 "title: x\ninstructions: |\n  ## Role\n\n  ## Project-Specific Notes\n\n  > USER-EDITABLE\n\n"
                 + "".join("  " + ln if ln.strip() else ln for ln in DUP.splitlines(keepends=True)) + "prompt: go\n"}
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    (root / "toolchain.lock").write_text(f"researchteam=jlcatonjr/researchteam@{PIN}\n")
    _brief(root, ())
    if brief is not None:
        (root / "brief.json").write_text(json.dumps(brief))
    return {p: p.read_bytes() for p in files}


def _upstream(pinned=UPSTREAM_ADVISOR):
    def fetch(repo, ref, path):
        if ref == PIN and isinstance(pinned, Exception):
            raise pinned
        return pinned if ref == PIN else UPSTREAM_ADVISOR
    return fetch


def _unchanged(root: Path, before: dict) -> None:
    assert {p: p.read_bytes() for p in before} == before
    assert not (root / "tmp").exists()  # no backup either


@pytest.mark.parametrize("dry_run", [False, True])
def test_customised_advisor_gets_no_notes_block_on_any_surface(tmp_path, monkeypatch, capsys, dry_run):
    custom = CUSTOM.replace("ours\n", QUOTE + "\n" + DUP)  # its Notes also hold a foldable hand copy
    before = _advisor_surfaces(tmp_path, custom)
    monkeypatch.setattr(_update_cmd, "fetch_raw", _upstream(PINNED))
    _update_cmd._sync_notes(tmp_path, "main", yes=True, dry_run=dry_run)
    _unchanged(tmp_path, before)
    out = capsys.readouterr().out
    assert (f"[notes] {ADVISOR_SLUG}: customised locally (differs from upstream @{PIN[:12]}); "
            "researchteam notes block not synced (left unchanged)") in out
    assert "Would sync" not in out and out.count("[notes]") == 1


def test_excluded_advisor_is_skipped_before_any_fetch(tmp_path, monkeypatch, capsys):
    before = _advisor_surfaces(tmp_path, _pristine_advisor(),
                               brief={"researchteam_notes": {"exclude": [ADVISOR_SLUG, "no-such-agent"]}})
    monkeypatch.setattr(_notes, "NOTES_AGENTS", (ADVISOR_SLUG,))
    monkeypatch.setattr(_update_cmd, "fetch_raw", lambda *a: pytest.fail("must not fetch"))
    _update_cmd._sync_notes(tmp_path, "main", yes=True, dry_run=False)
    _unchanged(tmp_path, before)
    out = capsys.readouterr().out
    assert f"[notes] {ADVISOR_SLUG}: excluded by brief.json researchteam_notes.exclude" in out
    assert "'no-such-agent' is not a researchteam notes agent; ignored" in out


@pytest.mark.parametrize("cfg", [{"exclude": ADVISOR_SLUG}, {"exclude": [ADVISOR_SLUG, 3]}, [ADVISOR_SLUG]])
def test_malformed_exclude_syncs_nothing(tmp_path, monkeypatch, capsys, cfg):
    before = _advisor_surfaces(tmp_path, _pristine_advisor(), brief={"researchteam_notes": cfg})
    assert _notes.excluded(tmp_path)[0] is None
    monkeypatch.setattr(_update_cmd, "fetch_raw", lambda *a: pytest.fail("must not fetch"))
    _update_cmd._sync_notes(tmp_path, "main", yes=True, dry_run=False)
    _unchanged(tmp_path, before)
    assert 'brief.json "researchteam_notes" must be {"exclude"' in capsys.readouterr().out


@pytest.mark.parametrize("dry_run", [False, True])
def test_pristine_advisor_still_gets_the_block_everywhere(tmp_path, monkeypatch, capsys, dry_run):
    before = _advisor_surfaces(tmp_path, _pristine_advisor("\n" + DUP))
    monkeypatch.setattr(_update_cmd, "fetch_raw", _upstream())
    _update_cmd._sync_notes(tmp_path, "main", yes=True, dry_run=dry_run)
    out = capsys.readouterr().out
    assert "customised" not in out
    if dry_run:
        _unchanged(tmp_path, before)
        assert out.count("[dry-run] Would sync upstream Notes into") == 3
        return
    for path in before:
        text = path.read_text()
        assert _notes.BEGIN in text and text.count(DUP.splitlines()[0].strip()) == 1, path  # duplicate folded


def test_advisor_just_upgraded_to_the_ref_is_not_customised(tmp_path, monkeypatch):
    # the layer-2 pass may have moved the head to upstream@ref, past the pin: still researchteam's own
    _advisor_surfaces(tmp_path, _pristine_advisor())
    monkeypatch.setattr(_update_cmd, "fetch_raw", _upstream(PINNED))
    _update_cmd._sync_notes(tmp_path, "main", yes=True, dry_run=False)
    assert _notes.BEGIN in (tmp_path / ADVISOR).read_text()


@pytest.mark.parametrize("unverifiable", ["fetch", "ref"])
def test_unverifiable_advisor_gets_no_notes_block(tmp_path, monkeypatch, capsys, unverifiable):
    before = _advisor_surfaces(tmp_path, _pristine_advisor().replace("Advisor", "Advisor (local)", 1))
    if unverifiable == "ref":
        (tmp_path / "toolchain.lock").unlink()
        (tmp_path / ".researchteam").write_text("ref = ../../evil?x=1\n")
        before[tmp_path / ".researchteam"] = (tmp_path / ".researchteam").read_bytes()
    monkeypatch.setattr(_update_cmd, "fetch_raw", _upstream(RuntimeError("HTTP 404")))
    _update_cmd._sync_notes(tmp_path, "main", yes=True, dry_run=False)
    _unchanged(tmp_path, before)
    out = capsys.readouterr().out
    assert f"[notes] {ADVISOR_SLUG}: not verified as un-customised (" in out
    assert ("could not fetch upstream" if unverifiable == "fetch" else "not a plain commit or name") in out


def test_researchteams_own_repo_is_unchanged(tmp_path, monkeypatch, capsys):
    assert _notes.excluded(ROOT) == (set(), [])
    for name in ("brief.json", ".researchteam", "toolchain.lock"):
        (tmp_path / name).write_text((ROOT / name).read_text(encoding="utf-8"))
    before = {}
    for agent in _notes.NOTES_AGENTS:
        for path, _ in _notes.surfaces(ROOT, agent):
            dest = tmp_path / path.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(path.read_bytes())
            before[dest] = dest.read_bytes()
    assert tmp_path / ADVISOR in before
    monkeypatch.setattr(_update_cmd, "fetch_raw", lambda repo, ref, path: (ROOT / path).read_text(encoding="utf-8"))
    _update_cmd._sync_notes(tmp_path, None, yes=True, dry_run=False)  # upstream's own layer-1 pass
    _update_cmd._sync_notes(tmp_path, "main", yes=True, dry_run=False)  # and a layer-2 run against itself
    _unchanged(tmp_path, before)
    assert "not synced" not in capsys.readouterr().out  # (a Notes-less .claude stub is reported as before)
