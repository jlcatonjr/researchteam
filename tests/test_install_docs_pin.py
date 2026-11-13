"""Install docs name the newest stable release, so a synced doc never pins users to an old line.

`docs/researchteam-framework.md` is synced to every derived repository, and README, CONTRIBUTING and the CLAUDE.md
managed block show the same install. They pinned `v1.0.2` well after `v1.1.2` shipped (found by legalResearch,
2026-11-12). The newest stable release is the first CHANGELOG heading with a final tag, written by the release-prep PR
before the tag is cut, so that PR must move these references too.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ["docs/researchteam-framework.md", "README.md", "docs/CONTRIBUTING.md", "CLAUDE.md",
        "researchteam/scaffold/CLAUDE.template.md"]


def newest_stable_tag() -> str:
    for line in (ROOT / "CHANGELOG.md").read_text().splitlines():
        m = re.match(r"## (\d+\.\d+\.\d+) \(tag `(v\d+\.\d+\.\d+)`", line)
        if m:
            assert m.group(2) == f"v{m.group(1)}", line
            return m.group(2)
    raise AssertionError("CHANGELOG.md has no released stable heading")


def test_install_docs_pin_the_newest_stable_tag():
    tag = newest_stable_tag()
    seen = 0
    for rel in DOCS:
        text = (ROOT / rel).read_text()
        refs = re.findall(r"researchteam\.git@(v[0-9][^\s\"'`)]*)", text)
        refs += re.findall(r"(?:--branch |tag -v |--researchteam-tag |researchteam-|currently )`?(v\d[^\s`;),]*)", text)
        assert all(r == tag for r in refs), (rel, sorted(set(refs)), tag)
        seen += len(refs)
    assert seen >= 10, seen  # the references are still there to check


def test_framework_doc_names_the_newest_stable_tag_in_prose():
    text = (ROOT / "docs" / "researchteam-framework.md").read_text()
    assert f"signed `{newest_stable_tag()}` tag" in text
