#!/usr/bin/env python3
"""Briefing library — the literature library's short-lived record class, for dated external claims.

A *briefing* is a handful of dated, attributed claims about one topic, built from outside sources (for example
by ``agentteams.research.build_briefing``). Unlike the literature library (``build_literature_library.py``),
which is committed, keyed to a project's ``.bib`` and holds the agents' relevance judgements, a briefing
library is:

- **kept out of version control**: the store is a directory the caller names, and every command refuses a
  store that git would track (``DEFECT[TRACKED]``);
- **perishable**: each record carries ``as_of`` and ``expires`` (reported and contested claims 7 days, web 30,
  scholarly 365; :data:`TTL_DAYS`), ``ingest`` prunes expired records, and ``query`` never returns them;
- **external claims, not relevance**: the indexed text is the claim itself.

It keeps the literature library's layout and its honest ceiling: ``literature.jsonl`` (records),
``term-vectors.jsonl`` (raw term counts, IDF at query time) and ``library-manifest.json``
(``artifact_type: "briefing-index"``). Records ship UNVERIFIED. A rated outlet is provenance, not truth; a
claim that survived a critic is "survived", never "verified"; lexical similarity is navigation, not evidence.

Usage:
  python3 scripts/briefing_library.py ingest <store> <briefing.json> [--as-of YYYY-MM-DD]
  python3 scripts/briefing_library.py check  <store> [--as-of YYYY-MM-DD]
  python3 scripts/briefing_library.py query  <store> "<terms>" [-k N] [--as-of YYYY-MM-DD]

``briefing.json`` is ``{"topic": str, "claims": [{claim, source_domain, attribution, published_at, kind,
single_source, sensitive}, ...], "critic_label": str?}``, the shape of ``agentteams.research.Briefing``.
Exit codes: 0 ok (or advisory only), 1 DEFECT, 2 usage or a refused store.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_literature_library import CEILING_BANNER, VECTOR_METHOD, VECTOR_MODEL_ID, _sha, _tokenize  # noqa: E402
from query_literature_library import _cosine, _idf, _tfidf  # noqa: E402

SCHEMA_VERSION = "1.0"
RECORD_CLASS = "briefing"
ARTIFACT_TYPE = "briefing-index"
UNVERIFIED = "UNVERIFIED — no human resolution performed"
TTL_DAYS = {"reported": 7, "contested": 7, "web": 30, "scholarly": 365}
CLAIM_MAX = 240
ATTRIBUTION_MAX = 120
TOPIC_MAX = 120
COVERAGE_STATEMENT = (
    "Coverage = the claims a briefing run surfaced and a critic did not refute, from sources found for each "
    "topic. This is NOT a completeness proof and does NOT claim to be exhaustive; claims expire."
)
_DOMAIN = re.compile(r"^[a-z0-9.-]{3,253}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MARKUP = re.compile(r"https?://|www\.|\]\(|[<>`*#|\\]")
FIELDS = ("key", "record_class", "topic", "claim", "source_domain", "attribution", "published_at", "kind",
          "single_source", "sensitive", "as_of", "expires", "verification_state", "record_text_sha256")


def _today(as_of: str | None) -> str:
    if as_of is None:
        return _dt.date.today().isoformat()
    if not _DATE.match(as_of):
        _usage(f"--as-of must be YYYY-MM-DD, got {as_of!r}")
    return as_of


def _expires(as_of: str, kind: str) -> str:
    return (_dt.date.fromisoformat(as_of) + _dt.timedelta(days=TTL_DAYS[kind])).isoformat()


def _tracked_reason(store: Path) -> str | None:
    """Why ``store`` may not hold briefings, or None. Outside any git work tree is fine; inside one, git must
    ignore it (a probe path under it) and track nothing beneath it."""
    probe_dir = store
    while not probe_dir.exists() and probe_dir != probe_dir.parent:
        probe_dir = probe_dir.parent                     # the nearest existing ancestor decides
    inside = subprocess.run(["git", "-C", str(probe_dir), "rev-parse", "--is-inside-work-tree"],
                            capture_output=True, text=True)
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return None
    ignored = subprocess.run(["git", "-C", str(probe_dir), "check-ignore", "-q", str(store / "probe")])
    if ignored.returncode != 0:
        return f"{store} is inside a git work tree and not ignored; briefings must never be committed"
    if store.exists():
        tracked = subprocess.run(["git", "-C", str(store), "ls-files", "."], capture_output=True, text=True)
        if tracked.stdout.strip():
            return f"{store} has git-tracked files; briefings must never be committed"
    return None


def _clean_claim(raw: object, topic: str, as_of: str) -> dict | None:
    """A validated briefing record from one claim of a briefing, or None if it breaks the schema."""
    if not isinstance(raw, dict):
        return None
    claim, domain, attr = raw.get("claim"), raw.get("source_domain"), raw.get("attribution")
    kind, published = raw.get("kind"), raw.get("published_at")
    if not (isinstance(claim, str) and 0 < len(claim.strip()) <= CLAIM_MAX and isinstance(domain, str)
            and _DOMAIN.match(domain) and isinstance(attr, str) and 0 < len(attr) <= ATTRIBUTION_MAX
            and kind in TTL_DAYS and (published is None or isinstance(published, str) and len(published) <= 32)
            and isinstance(raw.get("single_source"), bool) and isinstance(raw.get("sensitive"), bool)):
        return None
    for text in (claim, attr, published or ""):
        if "\n" in text or _MARKUP.search(text):
            return None
    claim = " ".join(claim.split())
    rec = {"key": hashlib.sha256(f"{topic}\x00{domain}\x00{claim}".encode("utf-8")).hexdigest()[:16],
           "record_class": RECORD_CLASS, "topic": topic, "claim": claim, "source_domain": domain,
           "attribution": attr, "published_at": published, "kind": kind,
           "single_source": raw["single_source"], "sensitive": raw["sensitive"],
           "as_of": as_of, "expires": _expires(as_of, kind), "verification_state": UNVERIFIED}
    rec["record_text_sha256"] = _sha(claim)
    return rec


def _schema_problem(r: dict) -> str | None:
    """Why a stored record is malformed, or None."""
    if set(r) != set(FIELDS):
        return "fields differ from the briefing schema"
    if r["record_class"] != RECORD_CLASS or r["kind"] not in TTL_DAYS:
        return "unknown record class or kind"
    if r["verification_state"] != UNVERIFIED:
        return "verification_state must stay UNVERIFIED"
    if not (_DATE.match(str(r["as_of"])) and _DATE.match(str(r["expires"]))):
        return "as_of/expires are not dates"
    if r["expires"] > _expires(r["as_of"], r["kind"]):
        return f"TTL longer than {TTL_DAYS[r['kind']]} days for {r['kind']}"
    if _clean_claim({k: r[k] for k in ("claim", "source_domain", "attribution", "published_at", "kind",
                                       "single_source", "sensitive")}, r["topic"], r["as_of"]) is None:
        return "claim fields fail validation"
    if r["record_text_sha256"] != _sha(r["claim"]):
        return "record_text_sha256 does not match the claim"
    return None


def _load(store: Path) -> list[dict]:
    path = store / "literature.jsonl"
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write(store: Path, records: list[dict]) -> None:
    store.mkdir(mode=0o700, parents=True, exist_ok=True)
    records = sorted(records, key=lambda r: (r["topic"], r["key"]))
    lit = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records)
    vecs = ""
    for r in records:
        counts: dict[str, int] = {}
        for tok in _tokenize(r["claim"]):
            counts[tok] = counts.get(tok, 0) + 1
        vecs += json.dumps({"key": r["key"], "n_terms": sum(counts.values()), "terms": counts},
                           ensure_ascii=False, sort_keys=True) + "\n"
    manifest = {"artifact_type": ARTIFACT_TYPE, "schema_version": SCHEMA_VERSION, "record_class": RECORD_CLASS,
                "vector_model_id": VECTOR_MODEL_ID, "vector_method": VECTOR_METHOD, "record_count": len(records),
                "topics": sorted({r["topic"] for r in records}), "ttl_days": TTL_DAYS,
                "records_sha256": _sha(lit), "coverage_statement": COVERAGE_STATEMENT,
                "ceiling_banner": CEILING_BANNER}
    for name, text in (("literature.jsonl", lit), ("term-vectors.jsonl", vecs),
                       ("library-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2,
                                                            sort_keys=True) + "\n")):
        tmp = store / f".{name}.tmp"
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, store / name)


def ingest(store: Path, briefing_path: Path, as_of: str) -> int:
    reason = _tracked_reason(store)
    if reason:
        print(f"[briefing-library] refused: {reason}", file=sys.stderr)
        return 2
    data = json.loads(briefing_path.read_text(encoding="utf-8"))
    topic = data.get("topic") if isinstance(data, dict) else None
    if not (isinstance(topic, str) and 0 < len(topic) <= TOPIC_MAX and "\n" not in topic
            and not _MARKUP.search(topic) and isinstance(data.get("claims"), list)):
        print("[briefing-library] refused: not a briefing (topic and claims)", file=sys.stderr)
        return 2
    new = [r for r in (_clean_claim(c, topic, as_of) for c in data["claims"]) if r is not None]
    rejected = len(data["claims"]) - len(new)
    kept = [r for r in _load(store) if r.get("topic") != topic and r.get("expires", "") > as_of]
    pruned = len(_load(store)) - len(kept) - sum(1 for r in _load(store) if r.get("topic") == topic)
    seen, merged = set(), []
    for r in kept + new:
        if r["key"] not in seen:
            seen.add(r["key"])
            merged.append(r)
    _write(store, merged)
    print(f"[briefing-library] {topic!r}: {len(new)} records ingested, {rejected} rejected, "
          f"{max(pruned, 0)} expired pruned; {len(merged)} records in the store.")
    print("  NOTE: " + CEILING_BANNER)
    return 0


def check(store: Path, as_of: str) -> int:
    print(f"Briefing-library integrity check: {store.name}")
    print("NOTE: green = STRUCTURE, not truth. Claims expire; similarity is navigation, not evidence.")
    defects, advisory = [], []
    reason = _tracked_reason(store)
    if reason:
        defects.append(f"DEFECT[TRACKED]  {reason}")
    manifest_path = store / "library-manifest.json"
    if not manifest_path.is_file():
        print("  NEEDS-BUILD     no briefing library yet (advisory, exit 0)" if not defects else "")
        for d in defects:
            print("  " + d)
        return 1 if defects else 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    lit = (store / "literature.jsonl").read_text(encoding="utf-8") if (store / "literature.jsonl").is_file() else ""
    if manifest.get("artifact_type") != ARTIFACT_TYPE:
        defects.append("DEFECT[SCHEMA]   manifest artifact_type is not briefing-index")
    if manifest.get("records_sha256") != _sha(lit):
        defects.append("DEFECT[STALE]    literature.jsonl changed outside ingest")
    banner = (manifest.get("ceiling_banner") or "").lower()
    if "navigation" not in banner or "not truth" not in banner:
        defects.append("DEFECT[CEILING]  manifest ceiling_banner missing (navigation-not-evidence / not-truth)")
    records = [json.loads(line) for line in lit.splitlines() if line.strip()]
    for r in records:
        problem = _schema_problem(r) if isinstance(r, dict) else "not an object"
        if problem:
            defects.append(f"DEFECT[SCHEMA]   {r.get('key', '?') if isinstance(r, dict) else '?'}: {problem}")
        elif r["expires"] <= as_of:
            advisory.append(f"EXPIRED          {r['key']}: expired {r['expires']} (ingest prunes; query skips)")
    for line in defects + advisory:
        print("  " + line)
    print("---")
    print(f"Records: {len(records)}  |  DEFECT: {len(defects)}  |  EXPIRED: {len(advisory)}")
    if defects:
        print("GATE FAILED: resolve DEFECT(s) before relying on the briefing library.")
        return 1
    print("PASS: structurally sound. (WELL-FORMED, not RESOLVED — records ship UNVERIFIED.)")
    return 0


def query(store: Path, q: str, k: int, as_of: str) -> int:
    reason = _tracked_reason(store)
    if reason:
        print(f"[briefing-library] refused: {reason}", file=sys.stderr)
        return 2
    records = {r["key"]: r for r in _load(store) if r.get("expires", "") > as_of}
    vecs = {}
    vec_path = store / "term-vectors.jsonl"
    if vec_path.is_file():
        for line in vec_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                v = json.loads(line)
                if v["key"] in records:
                    vecs[v["key"]] = v["terms"]
    idf = _idf(vecs)
    qcounts: dict[str, float] = {}
    for t in _tokenize(q):
        qcounts[t] = qcounts.get(t, 0.0) + 1.0
    qv = _tfidf(qcounts, idf)
    scored = sorted(((key, _cosine(qv, _tfidf({t: float(c) for t, c in terms.items()}, idf)))
                     for key, terms in vecs.items()), key=lambda kv: (-kv[1], kv[0]))
    hits = [(key, s) for key, s in scored[:k] if s > 0.0]
    print(f'Briefing candidates for: "{q}"')
    print("NOTE: NAVIGATION ONLY — lexical TF-IDF over unexpired claims. Not evidence; claims are UNVERIFIED.")
    print("---")
    if not hits:
        print("(no lexical overlap among unexpired claims — this is not evidence of absence)")
    for key, score in hits:
        r = records[key]
        print(f"  {score:.3f}  [{key}] {r['claim'][:90]}  ({r['attribution']}; {r['kind']}"
              f"{'; single source' if r['single_source'] else ''})")
    return 0


USAGE = __doc__.split("Usage:\n", 1)[1].split("\n\n", 1)[0]


def _usage(msg: str = "") -> None:
    print(f"{msg}\nusage:\n{USAGE}" if msg else f"usage:\n{USAGE}", file=sys.stderr)
    sys.exit(2)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    as_of = None
    if "--as-of" in args:
        i = args.index("--as-of")
        if i + 1 >= len(args):
            _usage("--as-of needs a date")
        as_of = args[i + 1]
        del args[i:i + 2]
    k = 8
    if "-k" in args:
        i = args.index("-k")
        try:
            k = int(args[i + 1])
        except (IndexError, ValueError):
            _usage("-k needs a whole number")
        if k < 1:
            _usage("-k must be at least 1")
        del args[i:i + 2]
    if not args or args[0] not in ("ingest", "check", "query"):
        _usage()
    today = _today(as_of)
    cmd = args[0]
    if cmd == "ingest" and len(args) == 3:
        return ingest(Path(args[1]).resolve(), Path(args[2]), today)
    if cmd == "check" and len(args) == 2:
        return check(Path(args[1]).resolve(), today)
    if cmd == "query" and len(args) >= 3:
        return query(Path(args[1]).resolve(), " ".join(args[2:]), k, today)
    _usage()
    return 2


if __name__ == "__main__":
    sys.exit(main())
