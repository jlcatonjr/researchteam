"""User-facing install instructions name the newest stable release.

docs/researchteam-framework.md is synced to every derived repository, so a stale tag there reaches the fleet
(v1.1.1 and v1.1.2 shipped telling users to install v1.0.2). The newest stable release is the highest final
`## X.Y.Z (tag `vX.Y.Z`, ...)` heading in CHANGELOG.md, so the release-prep PR that adds that heading must move
these install lines in the same change.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
INSTALL_DOCS = ["README.md", "docs/CONTRIBUTING.md", "docs/researchteam-framework.md", "CLAUDE.md",
                "researchteam/scaffold/CLAUDE.template.md", "docs_src/getting-started.md", "docs_src/index.md"]


def newest_stable_tag() -> str:
    text = (ROOT / "CHANGELOG.md").read_text()
    versions = [tuple(int(p) for p in m.groups())
                for m in re.finditer(r"^## (\d+)\.(\d+)\.(\d+) \(tag `v\1\.\2\.\3`", text, re.M)]
    assert versions, "CHANGELOG.md has no final release heading"
    return "v%d.%d.%d" % max(versions)


@pytest.mark.parametrize("doc", INSTALL_DOCS)
def test_install_instructions_name_the_newest_stable_release(doc):
    text = (ROOT / doc).read_text()
    newest = newest_stable_tag()
    named = re.findall(r"researchteam\.git@(v\d+\.\d+\.\d+)\b", text)
    named += re.findall(r"currently `(v\d+\.\d+\.\d+)`", text)
    named += re.findall(r"tag -v (v\d+\.\d+\.\d+)\b", text)
    named += re.findall(r"--branch (v\d+\.\d+\.\d+)\b", text)
    stale = sorted(set(t for t in named if t != newest))
    assert not stale, f"{doc} names {stale}; the newest stable release (CHANGELOG.md) is {newest}"
