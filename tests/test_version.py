"""The version comes from git release tags (setuptools-scm); masterTeacher ticket 4.5."""
import re
from pathlib import Path

import pytest

import researchteam

tomllib = pytest.importorskip("tomllib")  # Python 3.11+

ROOT = Path(__file__).resolve().parent.parent
CFG = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_version_is_dynamic_from_scm():
    assert "version" not in CFG["project"] and CFG["project"]["dynamic"] == ["version"]
    assert any(r.startswith("setuptools-scm==") for r in CFG["build-system"]["requires"])
    assert all("==" in r for r in CFG["build-system"]["requires"]), "build requirements are exact S-10 pins"


def test_only_release_tags_become_versions():
    rx = re.compile(CFG["tool"]["setuptools_scm"]["tag_regex"])
    assert rx.match("v1.0.0-rc.1").group("version") == "1.0.0-rc.1"  # normalises to 1.0.0rc1
    assert rx.match("v1.0.3").group("version") == "1.0.3"
    for tag in ("backup/pre-pull-main-20260927", "pre-agentteams-update-20260529", "v1.0", "main"):
        assert not rx.match(tag), tag
    assert "v[0-9]*" in CFG["tool"]["setuptools_scm"]["git_describe_command"]


def test_package_reports_a_version():
    assert isinstance(researchteam.__version__, str) and researchteam.__version__


def test_source_archives_carry_the_ref():
    assert "export-subst" in (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "$Format:%H$" in (ROOT / ".git_archival.txt").read_text(encoding="utf-8")
