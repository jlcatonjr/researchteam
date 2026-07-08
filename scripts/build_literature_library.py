#!/usr/bin/env python3
"""Build a per-project vectorized literature library from that project's bibliography.

The library is a per-project store of the literature the agents deem relevant while investigating.
It vectorizes the agents' RELEVANCE TEXT (a per-source relevance summary + optional abstract), not
bare titles. Output lives under Projects/<project>/references/library/ and is user-owned.

ANTI-FABRICATION CEILING (do not soften):
- Records ship verification_state="UNVERIFIED — no human resolution performed".
- Vectors are computed by a REAL (stdlib TF-IDF) vectoriser here, NEVER authored by a model.
- "Vectorized" = a LEXICAL TF-IDF navigation layer. A semantic/dense layer is a documented STUB.
- Vector similarity is NAVIGATION, not evidence; candidates never anchor a claim (see query script).
- No network, no fetch. Deterministic: same input -> byte-identical output.

Design (see docs/literature-library-protocol.md):
- literature.jsonl  : one record per relevant source (the durable, human-meaningful data).
- term-vectors.jsonl: one line per record, RAW term counts (IDF is computed at QUERY time — so the
                      committed artifact is low-churn and a future shared-vocabulary re-fit stays
                      possible; we never commit global idf/postings).
- library-manifest.json: counts, freshness hashes, coverage statement, the honest ceiling banner.

Usage:
  python3 scripts/build_literature_library.py <project-name-or-path>
Env:
  RT_ROOT=<path>   override repo root (default: repo root inferred from this script's location)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

SCHEMA_VERSION = "1.0"
VECTOR_MODEL_ID = "researchteam-tfidf-v1"          # a real lexical method — NOT a neural embedder
VECTOR_METHOD = "lexical-baseline"
VECTOR_STATE = "lexical-operational; dense/semantic cross-language layer = STUB (deferred)"
CEILING_BANNER = (
    "A green library audit certifies STRUCTURE, not truth. Records ship UNVERIFIED; vector "
    "similarity is navigation, not evidence, and never anchors a claim; this is a LEXICAL TF-IDF "
    "layer (semantic = STUB). This is not 'semantic search over all the literature.'"
)
COVERAGE_STATEMENT = (
    "Coverage = the sources the agents surfaced and deemed relevant so far (each with acquired:true "
    "below). This is NOT a completeness proof and does NOT claim to be exhaustive."
)
INCLUSION_CRITERION = (
    "One record per source the agents deemed relevant during investigation, keyed to the project "
    "bibliography; the record's relevance summary is the vectorized text."
)
THIN_RELEVANCE_WORDS = 8    # a relevance summary below this is flagged NEEDS-ENRICHMENT by the gate

_STOPWORDS = set(
    "a an and are as at be by for from has have in into is it its of on or that the to was were "
    "with this these those which who whom whose but not no nor so than then there here their they "
    "them his her our your you we he she i also can may might will would should could".split()
)


def _root() -> Path:
    env = os.environ.get("RT_ROOT")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parent.parent


def _resolve_project(root: Path, target: str) -> Path:
    p = Path(target)
    if p.is_dir() and (p / "references").is_dir():
        return p.resolve()
    for base in (root / "Projects", root / ".projects"):
        if not base.is_dir():
            continue
        for cand in base.rglob(target):
            if cand.is_dir() and (cand / "references").is_dir():
                return cand.resolve()
    sys.exit(f"[literature-library] no project with a references/ dir matches: {target}")


# ---------------------------------------------------------------------------
# Minimal, robust BibTeX parsing (line-based assembler; tolerant of '@' in field values)
# ---------------------------------------------------------------------------
def _parse_bib(path: Path) -> list[dict]:
    entries: list[dict] = []
    cur: list[str] = []

    def flush() -> None:
        if not cur:
            return
        rec = " ".join(cur)
        m = re.match(r"\s*@([A-Za-z]+)\s*\{\s*([^,\s{}]+)", rec)
        if not m:
            cur.clear()
            return
        etype = m.group(1).lower()
        key = m.group(2).strip()
        if etype in ("string", "comment", "preamble") or not key:
            cur.clear()
            return
        ym = re.search(r"[Yy]ear\s*=\s*[{\"]?\s*(\d{4})", rec)
        entries.append(
            {
                "key": key,
                "type": etype,
                "title": _field(rec, "title"),
                "author": _field(rec, "author") or _field(rec, "editor"),
                "year": ym.group(1) if ym else "",
                "url": _field(rec, "url"),
                "doi": _field(rec, "doi"),
                "note": _field(rec, "note"),
                "abstract": _field(rec, "abstract"),
            }
        )
        cur.clear()

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if re.match(r"\s*@[A-Za-z]+\s*\{", line):
            flush()
            cur = [line]
        elif cur:
            cur.append(line)
    flush()
    return entries


def _field(rec: str, name: str) -> str:
    """Extract a BibTeX field value (handles {…}, "…", and one level of nested braces)."""
    m = re.search(name + r"\s*=\s*", rec, re.IGNORECASE)
    if not m:
        return ""
    i = m.end()
    if i >= len(rec) or rec[i] not in "{\"":
        return ""
    if rec[i] == '"':
        j = rec.find('"', i + 1)
        return rec[i + 1 : j].strip() if j > i else ""
    depth = 0
    out = []
    for ch in rec[i:]:
        if ch == "{":
            depth += 1
            if depth == 1:
                continue
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
        out.append(ch)
    return "".join(out).strip()


# ---------------------------------------------------------------------------
def _seed_relevance_from_note(note: str) -> str:
    """Seed a relevance summary from a .bib note. Honest: the whole note is used as a STARTING
    point (stamped source:seeded-from-bib-note); URLs are dropped as tokens by the tokenizer."""
    return note.strip()


_URL_ARTIFACTS = set(
    "http https www com org edu net gov uk io isbn doi url verified accessed product "
    "openview search worldcat openlibrary proquest amazon".split()
)


def _tokenize(text: str) -> list[str]:
    text = re.sub(r"https?://\S+", " ", text.lower())      # drop URLs before tokenizing (noise)
    toks = re.split(r"[^a-z]+", text)
    out = []
    for t in toks:
        if len(t) < 3 or t in _STOPWORDS or t in _URL_ARTIFACTS:
            continue
        out.append(t)
    return out


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _indexed_text(rec: dict) -> str:
    rel = rec.get("relevance", {}) or {}
    parts = [rec.get("title", ""), rel.get("summary", ""), rec.get("abstract", "") or ""]
    return " ".join(p for p in parts if p).strip()


def build(project_dir: Path) -> None:
    refs = project_dir / "references"
    bibs = sorted(refs.glob("*.bib"))
    if not bibs:
        sys.exit(f"[literature-library] no .bib under {refs}")

    bib_entries: dict[str, dict] = {}
    bib_concat = ""
    for b in bibs:
        bib_concat += b.read_text(encoding="utf-8", errors="replace")
        for e in _parse_bib(b):
            bib_entries.setdefault(e["key"], e)

    libdir = refs / "library"
    libdir.mkdir(parents=True, exist_ok=True)
    lit_path = libdir / "literature.jsonl"

    # Preserve agent-authored records; the .bib key set is the source of truth for membership.
    existing: dict[str, dict] = {}
    if lit_path.exists():
        for line in lit_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            existing[r["key"]] = r

    records: list[dict] = []
    seeded = 0
    for key in sorted(bib_entries):
        e = bib_entries[key]
        prior = existing.get(key)
        if prior:
            rec = prior
            rec["title"] = e["title"] or rec.get("title", "")
            rec["source_url"] = e["url"] or rec.get("source_url", "")
            rec["doi"] = e["doi"] or rec.get("doi", "")
        else:
            note = e.get("note", "")
            summary = _seed_relevance_from_note(note)
            rec = {
                "key": key,
                "title": e["title"],
                "authors": e["author"],
                "year": e["year"],
                "source_url": e["url"],
                "doi": e["doi"],
                # NB: source_db is NOT inferred from the URL host (that fabricates provenance).
                # It is populated only when an agent supplies it explicitly.
                "relevance": {
                    "summary": summary,
                    "deemed_by": None,
                    "investigation": None,
                    "source": "seeded-from-bib-note" if summary else "unseeded",
                },
                "abstract": e.get("abstract", ""),
                "tags": [],
                "verification_state": "UNVERIFIED — no human resolution performed",
            }
            seeded += 1
        rec["record_text_sha256"] = _sha(_indexed_text(rec))  # hash of indexed text — NOT a source-text confirmation
        records.append(rec)

    # Write literature.jsonl (stable order) + raw term-count vectors + manifest.
    with lit_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")

    tv_path = libdir / "term-vectors.jsonl"
    with tv_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            counts: dict[str, int] = {}
            for tok in _tokenize(_indexed_text(rec)):
                counts[tok] = counts.get(tok, 0) + 1
            fh.write(
                json.dumps(
                    {"key": rec["key"], "n_terms": sum(counts.values()), "terms": counts},
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            )

    manifest = {
        "artifact_type": "literature-index",
        "schema_version": SCHEMA_VERSION,
        "project": project_dir.name,
        "vector_model_id": VECTOR_MODEL_ID,
        "vector_method": VECTOR_METHOD,
        "vector_state": VECTOR_STATE,
        "record_count": len(records),
        "seeded_this_build": seeded,
        "source_bib_sha256": _sha(bib_concat),
        "records_sha256": _sha(lit_path.read_text(encoding="utf-8")),
        "inclusion_criterion": INCLUSION_CRITERION,
        "coverage_statement": COVERAGE_STATEMENT,
        "ceiling_banner": CEILING_BANNER,
    }
    (libdir / "library-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    thin = sum(
        1
        for r in records
        if len((r.get("relevance", {}) or {}).get("summary", "").split()) < THIN_RELEVANCE_WORDS
    )
    print(f"[literature-library] {project_dir.name}: {len(records)} records "
          f"({seeded} seeded this build, {thin} thin relevance → run library-check).")
    print(f"  wrote {lit_path.relative_to(project_dir)}, term-vectors.jsonl, library-manifest.json")
    print("  NOTE: " + CEILING_BANNER)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: build_literature_library.py <project-name-or-path>")
    root = _root()
    build(_resolve_project(root, sys.argv[1]))


if __name__ == "__main__":
    main()
