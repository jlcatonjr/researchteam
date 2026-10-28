"""OI-11: the conflict log the conflict-auditor appends to exists, with exactly the columns its doc names."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / ".github" / "agents" / "references" / "conflict-log.csv"
DOC = ROOT / ".github" / "agents" / "conflict-auditor.agent.md"


def test_conflict_log_header_matches_the_agent_doc():
    m = re.search(r"conflict-log\.csv` with columns:\s*\n`([^`]+)`", DOC.read_text(encoding="utf-8"))
    assert m, "conflict-auditor.agent.md no longer states the conflict-log columns"
    assert LOG.read_text(encoding="utf-8").splitlines() == [m.group(1)]
