"""Every `uses:` in the repo's workflows and the derived-repo scaffold is pinned to a full commit SHA
with a trailing version comment, so a moved tag cannot change what CI runs (F-4)."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.y*ml")) + [
    ROOT / "researchteam" / "scaffold" / "agentteams-sync-derived.yml"]
USES = re.compile(r"^\s*(?:-\s+)?uses:\s*(\S+)(.*)$")
PINNED = re.compile(r"^[\w.-]+/[\w./-]+@[0-9a-f]{40}$")


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_actions_are_sha_pinned(path):
    uses = [m.groups() for line in path.read_text().splitlines() if (m := USES.match(line))]
    assert uses, f"{path.name}: no `uses:` lines found"
    for ref, rest in uses:
        if ref.startswith("./"):
            continue  # local action, versioned with the repo
        assert PINNED.match(ref), f"{path.name}: {ref} is not pinned to a 40-hex commit"
        assert re.search(r"#\s*v\d", rest), f"{path.name}: {ref} lacks a `# vX` version comment"
