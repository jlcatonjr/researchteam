"""Tests for derived-repo project identity: manifest skip/managed sets, brief-driven
personalization, the markdown fence, and the update-path guards/reconciliation.

Pure + tmp-path only — no network, no agentteams, no git.
"""

import json

import pytest

from researchteam._manifest import (
    BRIEF_PLACEHOLDER,
    FENCE_BEGIN_MD,
    FENCE_END_MD,
    FRAMEWORK_MANAGED_FILES,
    INIT_RENDER_TEMPLATES,
    INIT_SKIP_PREFIXES,
    MANAGED_FILES,
    MERGE_STRATEGIES,
    SCHOLARLY_MANAGED_FILES,
    managed_files_for,
)
from researchteam._init_cmd import _MARKER_TEMPLATE
from researchteam._personalize import (
    _load_template,
    _render,
    _split_fence,
    is_upstream,
    run_personalize,
)


# --------------------------------------------------------------------------- manifest
def test_projects_and_identity_files_are_skipped_on_init():
    for path in (".projects/", "brief.json", "README.md", "CLAUDE.md", "Projects/"):
        assert path in INIT_SKIP_PREFIXES, f"{path} must be excluded from init extraction"


def test_readme_is_not_synced_but_claude_is_fenced():
    assert "README.md" not in MANAGED_FILES  # generated per-project, never re-synced
    assert "README.md" not in FRAMEWORK_MANAGED_FILES
    assert "CLAUDE.md" in FRAMEWORK_MANAGED_FILES
    assert MERGE_STRATEGIES.get("CLAUDE.md") == "fenced-preserve"
    assert "docs/researchteam-framework.md" in FRAMEWORK_MANAGED_FILES


def test_layer2_profile_gates_scholarly_files():
    scholarly = managed_files_for("scholarly")
    generic = managed_files_for("generic")
    default = managed_files_for(None)
    assert default == scholarly  # absent profile == scholarly (backward compatible)
    assert set(generic) == set(FRAMEWORK_MANAGED_FILES)
    assert set(generic) < set(scholarly)  # generic is a strict subset
    for f in SCHOLARLY_MANAGED_FILES:
        assert f in scholarly and f not in generic


def test_render_templates_are_registered():
    assert INIT_RENDER_TEMPLATES == {
        "README.md": "README.template.md",
        "CLAUDE.md": "CLAUDE.template.md",
    }


# --------------------------------------------------------------------------- init marker invariant
def test_init_marker_never_declares_upstream_true():
    rendered = _MARKER_TEMPLATE.format(repo="jlcatonjr/researchteam", ref="main")
    assert "is_upstream = false" in rendered
    assert "is_upstream = true" not in rendered


# --------------------------------------------------------------------------- scaffold templates
def test_brief_template_is_neutral_placeholder():
    data = json.loads(_load_template("brief.template.json"))
    assert data["project_name"] == BRIEF_PLACEHOLDER
    assert data["enforce_decision_signing"] is True
    assert data["layer2_profile"] == "scholarly"
    assert "ResearchTeam" not in data["project_name"]


def test_templates_have_no_leftover_tokens_after_render():
    brief = {
        "project_name": "WASM Study",
        "project_goal": "Study WebAssembly.",
        "deliverables": ["Notes", "Demos"],
        "output_format": "Markdown",
        "primary_output_dir": "docs/",
    }
    for name in ("README.template.md", "CLAUDE.template.md"):
        out = _render(_load_template(name), brief)
        assert "{{" not in out and "}}" not in out
        assert "WASM Study" in out


def test_claude_template_is_fenced_with_markdown_comments():
    tpl = _load_template("CLAUDE.template.md")
    assert FENCE_BEGIN_MD in tpl and FENCE_END_MD in tpl
    split = _split_fence(tpl)
    assert split is not None
    pre, managed, post = split
    # Working Rule 6 (citation-audit pointer, conflict-audit C3) lives INSIDE the managed block.
    assert "citation-claim-audit-protocol.md" in managed
    # Project identity token sits OUTSIDE the fence (project-owned, personalized).
    assert "{{PROJECT_NAME}}" in pre


# --------------------------------------------------------------------------- personalize behavior
def _seed(tmp_path, *, upstream=False, **brief_over):
    marker = "[researchteam]\nupstream = x\nref = main\n"
    marker += f"is_upstream = {'true' if upstream else 'false'}\n"
    (tmp_path / ".researchteam").write_text(marker)
    brief = {
        "project_name": "Acme Study",
        "project_goal": "Study Acme.",
        "deliverables": ["Report"],
        "output_format": "Markdown",
        "primary_output_dir": "reports/",
    }
    brief.update(brief_over)
    (tmp_path / "brief.json").write_text(json.dumps(brief))
    return tmp_path


def test_init_style_personalize_writes_project_named_files(tmp_path):
    _seed(tmp_path)
    written = run_personalize(tmp_path, force=True, quiet=True)
    assert set(written) == {"README.md", "CLAUDE.md"}
    claude = (tmp_path / "CLAUDE.md").read_text()
    readme = (tmp_path / "README.md").read_text()
    assert "Acme Study" in claude and "Acme Study" in readme
    assert _split_fence(claude) is not None  # fence preserved
    assert "researchteam:generated" in claude and "researchteam:generated" in readme
    assert "ResearchTeam produces structured" not in readme  # no framework identity leak


def test_personalize_is_idempotent_on_untouched_files(tmp_path):
    _seed(tmp_path)
    run_personalize(tmp_path, force=True, quiet=True)
    before = (tmp_path / "README.md").read_text()
    run_personalize(tmp_path, force=False, quiet=True)
    assert (tmp_path / "README.md").read_text() == before


def test_personalize_refuses_to_clobber_user_edits(tmp_path):
    _seed(tmp_path)
    run_personalize(tmp_path, force=True, quiet=True)
    edited = (tmp_path / "README.md").read_text() + "\n\n## My hand-written section\n"
    (tmp_path / "README.md").write_text(edited)
    written = run_personalize(tmp_path, force=False, quiet=True)
    assert "README.md" not in written  # diverged file skipped
    assert (tmp_path / "README.md").read_text() == edited
    # ...but --force overrides
    written_forced = run_personalize(tmp_path, force=True, quiet=True)
    assert "README.md" in written_forced


def test_personalize_preserves_claude_managed_block_and_updates_header(tmp_path):
    _seed(tmp_path)
    run_personalize(tmp_path, force=True, quiet=True)
    managed_before = _split_fence((tmp_path / "CLAUDE.md").read_text())[1]
    brief = json.loads((tmp_path / "brief.json").read_text())
    brief["project_name"] = "Acme Study v2"
    (tmp_path / "brief.json").write_text(json.dumps(brief))
    run_personalize(tmp_path, force=False, quiet=True)
    after = (tmp_path / "CLAUDE.md").read_text()
    assert "Acme Study v2" in after  # header re-rendered
    assert _split_fence(after)[1] == managed_before  # managed block untouched


def test_personalize_refuses_on_upstream(tmp_path):
    _seed(tmp_path, upstream=True)
    assert is_upstream(tmp_path) is True
    with pytest.raises(SystemExit):
        run_personalize(tmp_path, force=True, quiet=True)


# --------------------------------------------------------------------------- markdown fence
def test_split_fence_recognizes_markdown_comment_fence():
    text = f"# Title\n\nProject header\n\n{FENCE_BEGIN_MD}\nmanaged body\n{FENCE_END_MD}\n"
    split = _split_fence(text)
    assert split is not None
    pre, managed, post = split
    assert "Project header" in pre
    assert "managed body" in managed
    assert post == ""


# --------------------------------------------------------------------------- update-path guards
def test_brief_placeholder_guard(tmp_path):
    from researchteam._update_cmd import _brief_has_placeholder, _read_brief_profile

    (tmp_path / "brief.json").write_text(json.dumps({"project_name": BRIEF_PLACEHOLDER}))
    assert _brief_has_placeholder(tmp_path) is True
    (tmp_path / "brief.json").write_text(json.dumps({"project_name": "Real", "layer2_profile": "generic"}))
    assert _brief_has_placeholder(tmp_path) is False
    assert _read_brief_profile(tmp_path) == "generic"


def test_descriptor_write_back_overlays_content_preserves_roster(tmp_path):
    from researchteam._update_cmd import _reconcile_manifest_back

    (tmp_path / "brief.json").write_text(
        json.dumps({"project_name": "New Name", "primary_output_dir": "out/", "deliverables": ["X"]})
    )
    agents_dir = tmp_path / ".github" / "agents"
    agents_dir.mkdir(parents=True)
    manifest = agents_dir / "_build-description.json"
    manifest.write_text(
        json.dumps(
            {
                "project_name": "Old Name",
                "primary_output_dir": "reports/",
                "selected_archetypes": ["a", "b"],
                "governance_agents": ["security"],
            }
        )
    )
    _reconcile_manifest_back(tmp_path)
    result = json.loads(manifest.read_text())
    assert result["project_name"] == "New Name"  # content overlaid from brief
    assert result["primary_output_dir"] == "out/"
    assert result["deliverables"] == ["X"]
    assert result["selected_archetypes"] == ["a", "b"]  # roster preserved
    assert result["governance_agents"] == ["security"]


# --------------------------------------------------------------------------- historical context
def test_historical_context_protocol_is_scholarly_managed():
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    for f in ("docs/historical-context-protocol.md", "scripts/check_historical_context.sh"):
        assert f in SCHOLARLY_MANAGED_FILES
        assert f not in FRAMEWORK_MANAGED_FILES
        assert (root / f).is_file(), f
    # The CLAUDE.md managed block that every derived repo receives points at the protocol, and
    # the scaffold template's block is identical to the upstream root copy.
    def block(p):
        t = (root / p).read_text(encoding="utf-8")
        return t[t.index(">>> researchteam:managed"): t.index("<<< researchteam:managed")]

    assert "docs/historical-context-protocol.md" in block("CLAUDE.md")
    assert block("CLAUDE.md") == block("researchteam/scaffold/CLAUDE.template.md")
