"""The docs site (mkdocs.yml, docs_src/) stays in step with the package and the CLI parser."""
import ast
import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs_src"
SITE_URL = "https://jlcatonjr.github.io/researchteam/"


def _nav_files(node) -> list[str]:
    if isinstance(node, str):
        return [node]
    if isinstance(node, list):
        return [f for item in node for f in _nav_files(item)]
    if isinstance(node, dict):
        return [f for value in node.values() for f in _nav_files(value)]
    return []


CONFIG = yaml.safe_load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
NAV = _nav_files(CONFIG["nav"])


def test_site_config_matches_the_published_location():
    assert CONFIG["docs_dir"] == "docs_src" and CONFIG["site_dir"] == "_site"
    assert CONFIG["site_url"] == SITE_URL


def test_every_nav_entry_exists():
    missing = [f for f in NAV if not (DOCS / f).is_file()]
    assert not missing, f"mkdocs nav points at missing pages: {missing}"


def test_every_module_has_an_api_page_in_the_nav():
    """researchteam/_update_cmd.py -> api-reference/update.md, _agentteams_provenance -> agentteams-provenance."""
    pages = {f for f in NAV if f.startswith("api-reference/")}
    for mod in sorted((ROOT / "researchteam").glob("*.py")):
        if mod.name == "__init__.py":
            continue
        slug = mod.stem.lstrip("_").removesuffix("_cmd").replace("_", "-")
        assert f"api-reference/{slug}.md" in pages, f"{mod.name} has no API reference page in mkdocs.yml"


def _cli_surface() -> tuple[list[str], list[str]]:
    """Subcommand names and option strings declared in researchteam/cli.py."""
    tree = ast.parse((ROOT / "researchteam" / "cli.py").read_text(encoding="utf-8"))
    commands, options = [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            literals = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            if node.func.attr == "add_parser":
                commands += literals[:1]
            elif node.func.attr == "add_argument":
                options += [s for s in literals if s.startswith("-")]
    return commands, options


def test_cli_reference_covers_every_command_and_flag():
    text = (DOCS / "cli-reference.md").read_text(encoding="utf-8")
    commands, options = _cli_surface()
    assert commands, "parsed no subcommands from cli.py"
    missing = [c for c in commands if f"## `{c}`" not in text]
    missing += [o for o in options if not re.search(rf"`{re.escape(o)}[ `,]", text)]
    assert not missing, f"docs_src/cli-reference.md is missing: {missing}"


def test_readme_links_the_site_at_the_top():
    head = (ROOT / "README.md").read_text(encoding="utf-8").split("\n## ", 1)[0]
    assert SITE_URL in head and f"{SITE_URL}api-reference/" in head


def test_docs_workflow_is_pinned_and_hash_locked():
    wf = (ROOT / ".github" / "workflows" / "docs.yml").read_text(encoding="utf-8")
    uses = re.findall(r"uses:\s*(\S+)", wf)
    assert uses and all(re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", u) for u in uses), uses
    assert "--require-hashes" in wf and "mkdocs build --strict" in wf
    reqs = (ROOT / ".github" / "ci" / "requirements-docs.txt").read_text(encoding="utf-8")
    pins = re.findall(r"^([a-z0-9-]+)==(\S+) \\$", reqs, re.M)
    assert ("mkdocs-material", "9.7.7") in pins and all("--hash=sha256:" in reqs for _ in pins)
