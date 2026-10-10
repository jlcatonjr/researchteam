"""Drift reporting: what `researchteam update` silently left behind (OrthodoxLLM Item 2).

Three kinds of drift went unnoticed in derived repos until found by hand:

* **Frozen fences.** ``update`` pins ``--shrink-policy preserve``. When a template rewords text, the
  shrink guard reads that as lost enrichment and keeps the old body silently and permanently.
  agentteams writes a review report of every section it kept when ``AGENTTEAMS_SHRINK_REPORT`` is
  set; ``update`` now always sets it (gitignored, under ``tmp/``), prints the count, and ``doctor``
  lists the sections with how long each has been frozen. A repo can mark a pin as deliberate in
  ``.github/agents/references/intentional-pins.json`` (repo-owned, never synced)::

      {"pins": [{"section": "ref-bibtex-reference.md:content",
                 "reason": "holds filled tool docs the template would reset to placeholders"}]}

  ``section`` is ``<file>:<fence>`` exactly as the report prints it.
* **Seeded files behind upstream** (``doctor --drift``): files ``init`` seeds but ``update`` never
  syncs (``SEEDED_FILES``), compared with upstream at the pinned researchteam commit.
* **Stale bridges** (``doctor --drift``): ``agentteams --bridge-check`` per bridge.
"""
from __future__ import annotations

import datetime as _dt
import json
import re
from pathlib import Path

REPORT_STEM = "agentteams-shrink-report"
STATE_FILE = "tmp/frozen-fences.state.json"
INTENTIONAL_FILE = ".github/agents/references/intentional-pins.json"
BRIDGES_DIR = "references/bridges"
_NOTES_HEADING = re.compile(r"^## Project-Specific Notes\s*$", re.M)
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")
# A ref we will put in a raw.githubusercontent.com URL: a commit, or a plain branch/tag name.
SAFE_REF = re.compile(r"^(?:[0-9a-f]{7,40}|[A-Za-z0-9][A-Za-z0-9._/-]{0,99})$")


def clean(text: object) -> str:
    """Text from reports and repo files, safe to print: control characters (ANSI escapes) removed."""
    return _CONTROL.sub("", str(text))


def report_path(root: Path, framework: str | None = None) -> Path:
    """Where one surface's shrink review report goes (gitignored ``tmp/``)."""
    suffix = f".{framework}" if framework else ""
    return root / "tmp" / f"{REPORT_STEM}{suffix}.json"


def prepare_report(root: Path, framework: str | None = None) -> Path:
    """Remove the previous run's report for this surface and return the path for the next one.

    agentteams writes the report only when it froze something, so a stale report from an earlier
    run would otherwise survive a run that froze nothing.
    """
    path = report_path(root, framework)
    for stale in (path, path.with_suffix(".md")):
        stale.unlink(missing_ok=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_frozen(root: Path) -> list[dict]:
    """Every frozen section from the latest reports: ``{surface, section, entry, lost, all_retired}``."""
    items: list[dict] = []
    for path in sorted((root / "tmp").glob(f"{REPORT_STEM}*.json")):
        surface = path.stem[len(REPORT_STEM) + 1:] or "copilot-vscode"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for item in data if isinstance(data, list) else []:
            if not isinstance(item, dict) or "file" not in item or "fence" not in item:
                continue
            items.append({"surface": surface, "section": f"{item['file']}:{item['fence']}",
                          "entry": item.get("entry", ""), "lost": item.get("lost", []),
                          "all_retired": bool(item.get("all_retired"))})
    return items


def load_intentional(root: Path) -> dict[str, str]:
    """``{section: reason}`` from the repo's intentional-pins file; ``{}`` if absent or unreadable."""
    try:
        data = json.loads((root / INTENTIONAL_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    pins = data.get("pins") if isinstance(data, dict) else None
    return {p["section"]: str(p.get("reason", "")) for p in pins or []
            if isinstance(p, dict) and isinstance(p.get("section"), str)}


def record_first_seen(root: Path, items: list[dict], today: _dt.date | None = None) -> dict[str, str]:
    """Update the gitignored first-seen state for the current frozen set and return it.

    A section keeps its first-seen date while it stays frozen; one that thawed is dropped, so a
    later re-freeze starts a new age.
    """
    today_s = (today or _dt.date.today()).isoformat()
    path = root / STATE_FILE
    old = first_seen(root)
    state = {f"{i['surface']}|{i['section']}": old.get(f"{i['surface']}|{i['section']}", today_s)
             for i in items}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return state


def first_seen(root: Path) -> dict[str, str]:
    """``{"<surface>|<section>": first-seen ISO date}`` from the gitignored state; ``{}`` if absent."""
    try:
        data = json.loads((root / STATE_FILE).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def frozen_summary(root: Path) -> str:
    """One line for `update`'s summary, from the LATEST report of every surface (not only the surfaces
    this run rendered); records first-seen dates as a side effect."""
    items = load_frozen(root)
    record_first_seen(root, items)
    if not items:
        return "[researchteam] Frozen fences: none (the shrink guard kept no stale section)."
    intentional = load_intentional(root)
    deliberate = sum(1 for i in items if i["section"] in intentional)
    reports = sorted({str(p.relative_to(root)) for p in (root / "tmp").glob(f"{REPORT_STEM}*.md")})
    return (f"[researchteam] Frozen fences: {len(items)} section(s) kept by the shrink guard "
            f"({deliberate} marked intentional, {len(items) - deliberate} to review). "
            f"Review: {', '.join(reports) or 'tmp/'}; details: researchteam doctor.")


def age_days(since: str, today: _dt.date | None = None) -> int | None:
    try:
        return ((today or _dt.date.today()) - _dt.date.fromisoformat(since)).days
    except ValueError:
        return None


def comparable_body(text: str) -> str:
    """A seeded file's upstream-owned part: everything before its ``## Project-Specific Notes``."""
    m = _NOTES_HEADING.search(text)
    return (text[:m.start()] if m else text).rstrip()


def bridge_frameworks(root: Path) -> list[str]:
    """Frameworks with a copilot-vscode bridge recorded under ``references/bridges/``."""
    base = root / BRIDGES_DIR
    if not base.is_dir():
        return []
    return sorted(d.name.removeprefix("copilot-vscode-to-") for d in base.iterdir()
                  if d.is_dir() and d.name.startswith("copilot-vscode-to-"))


def parse_bridge_report(text: str) -> tuple[str, list[str]]:
    """``(result, changed source files)`` from a ``bridge-check.report.md``."""
    m = re.search(r"^Result:\s*(\S+)", text, re.M)
    changed: list[str] = []
    section = re.search(r"^## Changed Source Files\s*\n(.*?)(?:^## |\Z)", text, re.M | re.S)
    if section:
        changed = [ln[2:].strip() for ln in section.group(1).splitlines() if ln.startswith("- ")]
    return (m.group(1) if m else "UNKNOWN"), changed
