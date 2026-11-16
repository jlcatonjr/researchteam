#!/usr/bin/env python3
"""Gate for docs/term-index-protocol.md: is each project's term register sound and its index current?

Purpose: the read-only check. It builds the index in memory with term_index_engine.py and
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


def _generated_file_problems(proj: Path, files: dict[str, bytes], compare_bytes: bool) -> list[str]:
    """Generated files that are missing, are not regular files, or (optionally) differ from a fresh build."""
    tdir, out = proj / "terminology", []
    for rel, data in sorted(files.items()):
        path = tdir / rel
        if path.is_symlink() or not path.is_file():
            out.append(f"terminology/{engine.shown(rel)}: missing")
        elif compare_bytes and path.read_bytes() != data:
            out.append(f"terminology/{engine.shown(rel)}: differs from a fresh build although the inputs are unchanged")
    out += [f"terminology/{engine.shown(rel)}: not a file the builder writes"
            for rel in sorted(engine.stray_index_files(proj, files))]
    return out


def freshness(proj: Path, a: engine.Assessment) -> tuple[list, list]:
    """Compare the committed index with the fresh one in `a`. Returns (defects, reviews)."""
    old = engine.read_manifest(proj)
    if old is None:
        return [("STALE", "no usable index manifest (run: term-build)")], []
    changes = [] if old.get("register_sha256") == a.register_sha256 else ["the register changed"]
    old_docs, new_docs = old["documents"], a.manifest["documents"]
    for rel in sorted(set(old_docs) | set(new_docs)):
        name = engine.shown(rel)
        if rel not in old_docs:
            changes.append(f"{name}: entered the scope")
        elif rel not in new_docs:
            changes.append(f"{name}: left the scope")
        elif old_docs[rel] != new_docs[rel]:
            changes.append(f"{name}: changed")
    if changes:
        return [("STALE", f"{c} since the index was built (run: term-build)") for c in changes], []
    same_generator = old.get("generator") == a.manifest["generator"]
    # A different generator may write different bytes for the same inputs, so only then is the byte
    # comparison skipped. A missing or stray generated file is a defect either way.
    defects = [("STALE", f"{msg} (edited by hand, or incomplete; run: term-build)")
               for msg in _generated_file_problems(proj, a.files, compare_bytes=same_generator)]
    reviews = [] if same_generator else [
        ("REBUILD", "the inputs are unchanged but the index was built by another generator version (run: term-build)")]
    return defects, reviews


def usage_findings(proj: Path, a: engine.Assessment) -> tuple[list, list]:
    defects, reviews = [], []
    used: set[str] = set()
    quoted = 0
    for rel, (_, occs) in sorted(a.docs.items()):
        used |= {o["term"] for o in occs if o["kind"] != "discouraged"}
        quoted += sum(1 for o in occs if o["kind"] == "discouraged" and o["quoted"])
        for o in engine.disc_violations(a.register, rel, occs):
            defects.append(("DISC", f"{engine.shown(rel)}:{o['line']}:{o['column']} term '{o['term']}': a "
                                    "discouraged form outside a quotation, with no 'allow' entry"))
    known = bib_keys(proj)
    for term in a.register["terms"]:
        src = term.get("source")
        if src is None:
            reviews.append(("NOSRC", f"term '{term['id']}': the definition has no 'source'"))
        elif isinstance(src, list):
            defects += [("SRC", f"term '{term['id']}': source key {n} is not in the project's .bib")
                        for n, key in enumerate(src, 1) if key not in known]
        if term["id"] not in used:
            reviews.append(("UNUSED", f"term '{term['id']}': no occurrence of the label or a variant"))
    if quoted:
        reviews.append(("QUOTED", f"{quoted} discouraged form(s) inside quotations (exempt; listed so that "
                                  "quoting stays visible)"))
    return defects, reviews


def check_project(proj: Path, named: bool, require: bool) -> tuple[bool, list, list]:
    """Return (a register was checked, defects, reviews)."""
    a = engine.assess(proj)
    if a.status in (engine.MISSING, engine.FOREIGN):
        tdir = proj / "terminology"
        if (tdir / "term-index.json").exists() or (tdir / "index").exists():
            return False, [("ORPHAN", "generated index files exist but there is no term register")], []
        if named or (require and engine.is_research_project(proj)):
            hint = "its terms.json is not a researchteam register" if a.status == engine.FOREIGN else "run: term-init"
            return False, [("NOREG", f"the project has no term register ({hint})")], []
        return False, [], []
    if a.status == engine.BAD:
        return True, a.problems, []
    fresh_defects, fresh_reviews = freshness(proj, a)
    usage_defects, usage_reviews = usage_findings(proj, a)
    return True, a.problems + fresh_defects + usage_defects, fresh_reviews + usage_reviews


def run(argv: list[str]) -> int:
    if len(argv) > 1 or (argv and argv[0].startswith("-")):
        print("usage: check_term_index.py [project]", file=sys.stderr)
        return 2
    root = engine.repo_root()
    advisory = os.environ.get("TERM_INDEX_ADVISORY") == "1"
    targets = engine.discover(root)
    if argv:
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
