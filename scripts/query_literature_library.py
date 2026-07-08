#!/usr/bin/env python3
"""Query a per-project literature library by lexical similarity — NAVIGATION ONLY.

Loads the committed raw term-count vectors, computes TF-IDF (IDF at query time, so nothing global is
committed), and cosine-ranks records against a free-text query. Results are candidates for a human to
inspect — they are NOT evidence, NOT a source relationship, and never anchor a claim or a link.
"absence of a candidate ≠ absence of a source." This is a LEXICAL layer; a semantic layer is a STUB.

Usage:
  python3 scripts/query_literature_library.py <project-name-or-path> "<query text>" [-k N]
Env:
  RT_ROOT=<path>   override repo root
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
from pathlib import Path

# Reuse the builder's tokenizer + project resolution so query/build stay consistent.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_literature_library import _tokenize, _resolve_project, _root  # noqa: E402


def _load(libdir: Path):
    lit = {}
    for line in (libdir / "literature.jsonl").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            r = json.loads(line)
            lit[r["key"]] = r
    vecs = {}
    for line in (libdir / "term-vectors.jsonl").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            v = json.loads(line)
            vecs[v["key"]] = v["terms"]
    return lit, vecs


def _idf(vecs: dict[str, dict]) -> dict[str, float]:
    n = len(vecs) or 1
    df: dict[str, int] = {}
    for terms in vecs.values():
        for t in terms:
            df[t] = df.get(t, 0) + 1
    return {t: math.log((1 + n) / (1 + d)) + 1.0 for t, d in df.items()}


def _tfidf(counts: dict[str, float], idf: dict[str, float]) -> dict[str, float]:
    v = {t: c * idf.get(t, math.log(2.0) + 1.0) for t, c in counts.items()}
    norm = math.sqrt(sum(w * w for w in v.values())) or 1.0
    return {t: w / norm for t, w in v.items()}


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(w * b.get(t, 0.0) for t, w in a.items())


def query(libdir: Path, q: str, k: int) -> list[tuple[str, float]]:
    lit, vecs = _load(libdir)
    idf = _idf(vecs)
    doc_vecs = {key: _tfidf({t: float(c) for t, c in terms.items()}, idf) for key, terms in vecs.items()}
    qcounts: dict[str, float] = {}
    for t in _tokenize(q):
        qcounts[t] = qcounts.get(t, 0.0) + 1.0
    qv = _tfidf(qcounts, idf)
    scored = sorted(
        ((key, _cosine(qv, dv)) for key, dv in doc_vecs.items()), key=lambda kv: (-kv[1], kv[0])
    )
    return [(key, s) for key, s in scored[:k] if s > 0.0], lit


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "-k"]
    k = 8
    if "-k" in sys.argv:
        i = sys.argv.index("-k")
        try:
            k = int(sys.argv[i + 1])
            args = [a for a in args if a != sys.argv[i + 1]]
        except (IndexError, ValueError):
            pass
    if len(args) < 2:
        sys.exit('usage: query_literature_library.py <project> "<query>" [-k N]')
    project, q = args[0], " ".join(args[1:])
    libdir = _resolve_project(_root(), project) / "references" / "library"
    if not (libdir / "term-vectors.jsonl").exists():
        sys.exit(f"[literature-library] no library at {libdir} — run build_literature_library.py first")

    hits, lit = query(libdir, q, k)
    print(f'Literature-library candidates for: "{q}"  (project: {project})')
    print("NOTE: NAVIGATION ONLY — lexical TF-IDF similarity. Candidates are NOT evidence, NOT a")
    print("      source relationship, and never anchor a claim. Absence of a candidate ≠ absence of a source.")
    print("---")
    if not hits:
        print("(no lexical overlap — try different terms; this is not evidence of absence)")
        return
    for key, score in hits:
        rec = lit.get(key, {})
        title = (rec.get("title") or "")[:70]
        print(f"  {score:.3f}  [{key}] {title}")


if __name__ == "__main__":
    main()
