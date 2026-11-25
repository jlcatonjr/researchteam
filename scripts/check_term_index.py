#!/usr/bin/env python3
"""Gate for docs/term-index-protocol.md: is each project's term register sound and its index current?

Purpose: the read-only check. It builds the index in memory with term_index_engine.py and
    compares it with the committed files (the comparison is the pinned core's). It never writes a file.
    Importing the engine checks the pinned core against scripts/term-index-core/PINNED.json first; a copy
    that does not verify stops the check with exit 2.
Lifecycle: UTILITY
Created: 2026-11-16

CEILING (do not soften): a clean run establishes WELL-FORMED AND CURRENT, never CONSISTENT IN MEANING.
Matching finds forms. It cannot tell whether a term is used in its defined sense.

Usage:
  python3 scripts/check_term_index.py [project]
    no argument  check every project under Projects/
    <project>    check one project, by its path under Projects/ or its directory name
Result lines are code-tagged; the codes are defined in docs/term-index-protocol.md.
Exit codes: 0 no DEFECT (or advisory mode) | 1 at least one DEFECT | 2 usage or environment error
Env:
  RT_ROOT=<path>           override the repository root (test harness)
  TERM_INDEX_ADVISORY=1    report DEFECTs but exit 0
A repository that sets `term_index_require = true` in .researchteam makes a missing register a DEFECT
for every research project. Without it, a missing register is a DEFECT only for a named project.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import term_index_engine as engine  # noqa: E402  (sibling module: one matcher for build, check and query)

REQUIRE_KEY = "term_index_require"
TRUE_VALUES, FALSE_VALUES = {"true", "yes", "on", "1"}, {"false", "no", "off", "0"}


def required(root: Path) -> bool:
    """Whether .researchteam makes a term register compulsory for every research project.

    Follows the grammar of researchteam's own marker reader (_personalize.read_marker): the first
    occurrence of a key wins, a trailing ` #comment` is dropped, one pair of surrounding quotes is
    stripped. A missing marker or key means no. A value that is neither yes nor no raises ValueError,
    and an unreadable marker raises OSError, so a mistake cannot switch the requirement off unnoticed.
    """
    marker = root / ".researchteam"
    if not marker.exists():
        return False
    for line in marker.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if "=" not in s or s.startswith(("[", "#")):
            continue
        key, _, value = s.partition("=")
        if key.strip() != REQUIRE_KEY:
            continue
        value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if value.lower() in TRUE_VALUES:
            return True
        if value.lower() in FALSE_VALUES:
            return False
        raise ValueError(f"{REQUIRE_KEY} in .researchteam must be true or false")
    return False


def bib_keys(proj: Path) -> set[str]:
    """Citation keys in every .bib file under the project. A repository-level bibliography is not consulted."""
    keys: set[str] = set()
    for bib in sorted(proj.rglob("*.bib")):
        if bib.is_file() and not bib.is_symlink():
            text = bib.read_text(encoding="utf-8", errors="replace")
            keys |= set(re.findall(r"^[ \t]*@\w+[ \t]*\{[ \t]*([^,\s{}]+)[ \t]*,", text, re.M))
    return keys


def source_check(proj: Path):
    """The `[SRC]` check the core runs for each term whose `source` is a list of keys: every key must be in a
    .bib file under the project. The keys are read once, before the core runs, as they always were."""
    known = bib_keys(proj)

    def validate(_proj: Path, term: dict) -> list:
        return [("SRC", f"term '{term['id']}': source key {n} is not in the project's .bib")
                for n, key in enumerate(term["source"], 1) if key not in known]
    return validate


def check_project(proj: Path, named: bool, require: bool) -> tuple[bool, list, list]:
    """Return (a register was checked, defects, reviews).

    A missing or foreign register is handled here, so the NOREG hint names researchteam's command; the core
    checks only a register that loads (design note, section 10, point 10). The register is read twice, the
    documents once.
    """
    status = engine.load_register(proj).status
    if status in (engine.MISSING, engine.FOREIGN):
        tdir = proj / "terminology"
        if (tdir / "term-index.json").exists() or (tdir / "index").exists():
            return False, [("ORPHAN", "generated index files exist but there is no term register")], []
        if named or (require and engine.is_research_project(proj)):
            hint = "its terms.json is not a researchteam register" if status == engine.FOREIGN else "run: term-init"
            return False, [("NOREG", f"the project has no term register ({hint})")], []
        return False, [], []
    validator = source_check(proj) if status == engine.OK else None
    return engine.check_register(proj, source_validator=validator)


def run(argv: list[str]) -> int:
    if len(argv) > 1 or (argv and argv[0].startswith("-")):
        print("usage: check_term_index.py [project]", file=sys.stderr)
        return 2
    root = engine.repo_root()
    advisory = os.environ.get("TERM_INDEX_ADVISORY") == "1"
    if not argv:
        targets = engine.discover(root)
    else:
        proj = engine.resolve(root, argv[0])
        if proj is None:
            print(f"ERROR: no project under Projects/ matches: {engine.shown(argv[0])}", file=sys.stderr)
            return 2
        targets = [proj]
    require = required(root)
    print("Term-index check")
    print("NOTE: a clean run establishes WELL-FORMED AND CURRENT, not that terms are used in their")
    print("      defined sense. Matching finds forms, not meanings.")
    checked = n_defects = n_reviews = 0
    for proj in targets:
        was_checked, defects, reviews = check_project(proj, bool(argv), require)
        name = engine.shown(proj.relative_to(root).as_posix())
        checked += was_checked
        n_defects += len(defects)
        n_reviews += len(reviews)
        if not was_checked and not defects:
            if engine.is_research_project(proj):
                print(f"\n=== {name}\n  NEEDS-REGISTER   no term register (run: term-init)")
            continue
        print(f"\n=== {name}")
        for code, msg in defects:
            print(f"  DEFECT[{code}]".ljust(18) + msg)
        for code, msg in reviews:
            print(f"  NEEDS-REVIEW[{code}]".ljust(23) + msg)
        if not defects and not reviews:
            print("  OK")
    print("\n---")
    print(f"Projects seen: {len(targets)}  |  registers checked: {checked}  |  DEFECT: {n_defects}  |  "
          f"NEEDS-REVIEW: {n_reviews}")
    if n_defects:
        if advisory:
            print("ADVISORY MODE (TERM_INDEX_ADVISORY=1): defects found but not blocking (exit 0).")
            return 0
        print("GATE FAILED: see docs/term-index-protocol.md.")
        return 1
    if not checked:
        print("NOTHING CHECKED: no project has a term register. This is not a pass.")
        return 0
    print("PASS (no DEFECT). NEEDS-REVIEW items are advisory.")
    return 0


def main(argv: list[str]) -> int:
    try:
        return run(argv)
    except (OSError, ValueError) as exc:  # the I/O boundary: an unreadable file is an environment error
        print(f"ERROR: the check could not run ({type(exc).__name__}: {exc})", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
