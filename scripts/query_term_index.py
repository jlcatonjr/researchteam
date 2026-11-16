#!/usr/bin/env python3
"""List where a registered term occurs in a project's documents.

Purpose: the lookup for docs/term-index-protocol.md. It scans the documents afresh with
    term_index_engine.py, so its answer is current even when the committed index is stale. Read-only.
Lifecycle: UTILITY
Created: 2026-11-16

A hit is a place where a registered form appears. It is not evidence that the term is used in its
defined sense, and it is not a retrieval surface for sources (docs/retrieval-surfaces.md).

Usage:
  python3 scripts/query_term_index.py <project> "<label, variant or id>"
  python3 scripts/query_term_index.py <project> --list
Exit codes: 0 found (or listed) | 1 no such term, or no register | 2 usage or environment error
Env: RT_ROOT=<path> overrides the repository root (test harness).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import term_index_engine as engine  # noqa: E402  (sibling module: one matcher for build, check and query)


def find_term(reg: dict, query: str) -> dict | None:
    """A term by its id, or else by one of its forms. An id always wins over another term's form."""
    wanted = engine.form_key(query)
    by_id = [t for t in reg["terms"] if t["id"] == query]
    by_form = [t for t in reg["terms"] if any(engine.form_key(f) == wanted for f, _ in engine.term_forms(t))]
    return (by_id or by_form or [None])[0]


def run(argv: list[str]) -> int:
    if len(argv) != 2:
        print('usage: query_term_index.py <project> "<label, variant or id>" | --list', file=sys.stderr)
        return 2
    root = engine.repo_root()
    proj = engine.resolve(root, argv[0])
    if proj is None:
        print(f"ERROR: no project under Projects/ matches: {engine.shown(argv[0])}", file=sys.stderr)
        return 2
    a = engine.assess(proj)
    if not a.usable:
        reasons = "; ".join(msg for _, msg in a.problems) or "the project has none"
        print(f"No usable term register: {reasons}", file=sys.stderr)
        return 1
    reg, docs = a.register, a.docs
    counts: dict[str, int] = {}
    for _, occs in docs.values():
        for o in occs:
            counts[o["term"]] = counts.get(o["term"], 0) + 1
    if argv[1] == "--list":
        for term in sorted(reg["terms"], key=lambda t: engine.form_key(t["label"])):
            print(f"{counts.get(term['id'], 0):5d}  {term['id']}  ({term['label']})")
        return 0
    term = find_term(reg, argv[1])
    if term is None:
        print(f"No registered term matches: {argv[1]}", file=sys.stderr)
        return 1
    print(f"{term['label']}  [{term['id']}]")
    print(f"  {term['definition']}")
    print(f"  {counts.get(term['id'], 0)} occurrence(s). Places where a form appears, not evidence of sense.")
    for rel, (_, occs) in sorted(docs.items()):
        for o in occs:
            if o["term"] == term["id"]:
                flags = o["kind"] + (", quoted" if o["quoted"] else "")
                print(f"  {rel}:{o['line']}:{o['column']}  {o['form']}  ({flags})")
    return 0


def main(argv: list[str]) -> int:
    try:
        return run(argv)
    except OSError as exc:  # the I/O boundary: an unreadable file is an environment error
        print(f"ERROR: the query could not run ({type(exc).__name__}: {exc})", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
