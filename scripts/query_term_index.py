#!/usr/bin/env python3
"""List where a registered term occurs in a project's documents.

Purpose: the lookup for docs/term-index-protocol.md. It scans the documents afresh with the engine in
    build_term_index.py, so its answer is current even when the committed index is stale. Read-only.
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

import build_term_index as engine  # noqa: E402  (sibling module: one matcher for build, check and query)


def find_term(reg: dict, query: str) -> dict | None:
    wanted = engine.norm(query)
    for term in reg["terms"]:
        if term["id"] == query or any(engine.norm(form) == wanted for form, _ in engine.term_forms(term)):
            return term
    return None


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print('usage: query_term_index.py <project> "<label, variant or id>" | --list', file=sys.stderr)
        return 2
    root = engine.repo_root()
    proj = engine.resolve(root, argv[0])
    if proj is None:
        print(f"ERROR: project not found under Projects/: {argv[0]}", file=sys.stderr)
        return 2
    status, reg, problems, docs, _ = engine.inspect(proj)
    if status != "ok":
        print("No usable term register: " + ("; ".join(msg for _, msg in problems) or "run term-init"), file=sys.stderr)
        return 1
    counts: dict[str, int] = {}
    for _, occs in docs.values():
        for o in occs:
            counts[o["term"]] = counts.get(o["term"], 0) + 1
    if argv[1] == "--list":
        for term in sorted(reg["terms"], key=lambda t: engine.norm(t["label"])):
            print(f"{counts.get(term['id'], 0):5d}  {term['id']}  ({term['label']})")
        return 0
    term = find_term(reg, argv[1])
    if term is None:
        print(f"No registered term matches: {argv[1]}", file=sys.stderr)
        return 1
    print(f"{term['label']}  [{term['id']}]")
    print(f"  {term['definition']}")
    print(f"  {counts.get(term['id'], 0)} occurrence(s). Places where a registered form appears, not evidence of sense.")
    for rel, (_, occs) in sorted(docs.items()):
        for o in occs:
            if o["term"] == term["id"]:
                flags = o["kind"] + (", quoted" if o["quoted"] else "")
                print(f"  {rel}:{o['line']}:{o['column']}  {o['form']}  ({flags})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
