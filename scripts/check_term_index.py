#!/usr/bin/env python3
"""Gate for docs/term-index-protocol.md: is each project's term register sound and its index current?

Purpose: the read-only check. It builds the index in memory with the engine in build_term_index.py and
    compares it with the committed files. It never writes a file.
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

import json
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_term_index as engine  # noqa: E402  (sibling module: one matcher for build, check and query)


def required(root: Path) -> bool:
    """Whether .researchteam makes a term register compulsory for every research project."""
    try:
        text = (root / ".researchteam").read_text(encoding="utf-8")
    except OSError:
        return False
    return re.search(r"^\s*term_index_require\s*=\s*(true|yes|on|1)\s*$", text, re.M | re.I) is not None


def bib_keys(proj: Path) -> set[str]:
    keys: set[str] = set()
    for bib in sorted(proj.rglob("*.bib")):
        if bib.is_file() and not bib.is_symlink():
            keys |= set(re.findall(r"^\s*@\w+\s*\{\s*([^,\s{}]+)\s*,", bib.read_text(encoding="utf-8", errors="replace"), re.M))
    return keys


def freshness(proj: Path, files: dict[str, bytes]) -> tuple[list, list]:
    """Compare the committed index with a fresh one. Returns (defects, reviews)."""
    tdir = proj / "terminology"
    try:
        on_disk = json.loads((tdir / "term-index.json").read_text(encoding="utf-8"))
        fresh = json.loads(files["term-index.json"])
        old_docs = on_disk["documents"]
        if not isinstance(old_docs, dict):
            raise ValueError("documents")
    except OSError:
        return [("STALE", "no index has been built (run: term-build)")], []
    except (ValueError, KeyError, TypeError):
        return [("STALE", "term-index.json cannot be read as an index manifest (run: term-build)")], []
    changes = []
    if on_disk.get("register_sha256") != fresh["register_sha256"]:
        changes.append("the register changed")
    new_docs = fresh["documents"]
    for rel in sorted(set(old_docs) | set(new_docs)):
        if rel not in old_docs:
            changes.append(f"{rel}: entered the scope")
        elif rel not in new_docs:
            changes.append(f"{rel}: left the scope")
        elif old_docs[rel] != new_docs[rel]:
            changes.append(f"{rel}: changed")
    if changes:
        return [("STALE", f"{c} since the index was built (run: term-build)") for c in changes], []
    if on_disk.get("generator") != fresh["generator"]:
        return [], [("REBUILD", "the inputs are unchanged but the index was built by another generator "
                                "version (run: term-build)")]
    differing = sorted(rel for rel, data in files.items()
                       if not (tdir / rel).is_file() or (tdir / rel).read_bytes() != data)
    differing += sorted(engine.extra_index_files(proj, files))
    return [("STALE", f"terminology/{rel}: differs from a fresh build although the inputs are unchanged "
                      "(edited by hand, or missing; run: term-build)") for rel in differing], []


def usage(proj: Path, reg: dict, docs: dict) -> tuple[list, list]:
    defects, reviews = [], []
    allowed = {(a["term"], a["file"]) for a in reg.get("allow", [])}
    used: set[str] = set()
    quoted = 0
    for rel, (_, occs) in sorted(docs.items()):
        for o in occs:
            if o["kind"] != "discouraged":
                used.add(o["term"])
            elif o["quoted"]:
                quoted += 1
            elif (o["term"], rel) not in allowed:
                defects.append(("DISC", f"{rel}:{o['line']}:{o['column']} term '{o['term']}': a discouraged form "
                                        "outside a quotation, with no 'allow' entry"))
    known = bib_keys(proj)
    for term in reg["terms"]:
        src = term.get("source")
        if src is None:
            reviews.append(("NOSRC", f"term '{term['id']}': the definition has no 'source'"))
        elif isinstance(src, list):
            for n, key in enumerate(src, 1):
                if key not in known:
                    defects.append(("SRC", f"term '{term['id']}': source key {n} is not in the project's .bib"))
        if term["id"] not in used:
            reviews.append(("UNUSED", f"term '{term['id']}': no occurrence of the label or a variant"))
    if quoted:
        reviews.append(("QUOTED", f"{quoted} discouraged form(s) inside quotations (exempt; listed so quoting stays visible)"))
    return defects, reviews


def check_project(proj: Path, named: bool, require: bool):
    """Return (state, defects, reviews). state: checked | no-register."""
    status, reg, problems, docs, files = engine.inspect(proj)
    if status in ("missing", "foreign"):
        tdir = proj / "terminology"
        if (tdir / "term-index.json").exists() or (tdir / "index").exists():
            return "no-register", [("ORPHAN", "generated index files exist but there is no term register")], []
        if named or (require and engine.is_research_project(proj)):
            return "no-register", [("NOREG", "the project has no term register (run: term-init)")], []
        return "no-register", [], []
    if status == "bad":
        return "checked", problems, []
    defects, reviews = list(problems), []
    for part in (freshness(proj, files), usage(proj, reg, docs)):
        defects += part[0]
        reviews += part[1]
    return "checked", defects, reviews


def main(argv: list[str]) -> int:
    if len(argv) > 1 or (argv and argv[0].startswith("-")):
        print("usage: check_term_index.py [project]", file=sys.stderr)
        return 2
    root = engine.repo_root()
    advisory = os.environ.get("TERM_INDEX_ADVISORY") == "1"
    if argv:
        proj = engine.resolve(root, argv[0])
        if proj is None:
            print(f"ERROR: project not found under Projects/: {argv[0]}", file=sys.stderr)
            return 2
        targets = [proj]
    else:
        targets = engine.discover(root)
    require = required(root)
    print(f"Term-index check (root: {root})")
    print("NOTE: a clean run establishes WELL-FORMED AND CURRENT, not that terms are used in their")
    print("      defined sense. Matching finds forms, not meanings.")
    checked = n_defects = n_reviews = 0
    for proj in targets:
        state, defects, reviews = check_project(proj, bool(argv), require)
        name = proj.relative_to(root).as_posix()
        checked += state == "checked"
        n_defects += len(defects)
        n_reviews += len(reviews)
        if state == "no-register" and not defects:
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
    print(f"Projects seen: {len(targets)}  |  registers checked: {checked}  |  DEFECT: {n_defects}  |  NEEDS-REVIEW: {n_reviews}")
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


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
