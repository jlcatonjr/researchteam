#!/usr/bin/env bash
# Fail-closed integrity gate for a per-project literature library.
# (Named check_literature_library_integrity.sh — NOT check_library_integrity.sh — to avoid clobbering
#  the OrthodoxLLM instance-local, domain-specific gate of that name via researchteam update.)
#
# A GREEN result certifies STRUCTURE, not truth. It enforces the anti-fabrication ceiling and the
# relevance-capture obligation; it does NOT prove any source is real, relevant, or exhaustive.
#
# DEFECT (blocking; exit 1 unless advisory):
#   - index stale (literature.jsonl / .bib changed since the manifest was built)
#   - a record with no source link (no url and no doi)
#   - a record whose key is not in the project .bib (orphan)
#   - self-attestation: verification_state "resolved"/"attested" without LIBRARY_HUMAN_SIGNOFF=1
#   - manifest missing the coverage disclaimer or the navigation-not-evidence ceiling banner
# NEEDS-ENRICHMENT (advisory; never blocks): a record whose relevance is seeded/absent/thin — an
#   agent must author/confirm "why this source is relevant" (the "deemed relevant via investigation"
#   obligation). This is the loop that builds the library out as agents investigate.
#
# Usage:   scripts/check_literature_library_integrity.sh <project-name-or-path>
# Exit:    0 clear/advisory (or no library yet) | 1 blocking DEFECT | 2 usage/env error
# Env:     RT_ROOT override; LITERATURE_LIBRARY_ADVISORY=1 downgrades DEFECT; LIBRARY_HUMAN_SIGNOFF=1
#          permits human-attested resolution states.
set -uo pipefail

ROOT_DIR="${RT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
ADVISORY="${LITERATURE_LIBRARY_ADVISORY:-0}"
SIGNOFF="${LIBRARY_HUMAN_SIGNOFF:-0}"
target="${1:-}"
[ -n "$target" ] || { echo "usage: check_literature_library_integrity.sh <project>" >&2; exit 2; }

python3 - "$ROOT_DIR" "$target" "$ADVISORY" "$SIGNOFF" <<'PY'
import sys, json, hashlib, re
from pathlib import Path

root, target = Path(sys.argv[1]), sys.argv[2]
advisory = sys.argv[3] == "1"
signoff = sys.argv[4] == "1"
THIN = 8

def resolve(root, target):
    p = Path(target)
    if p.is_dir() and (p / "references").is_dir():
        return p
    for base in (root / "Projects", root / ".projects"):
        if base.is_dir():
            for c in base.rglob(target):
                if c.is_dir() and (c / "references").is_dir():
                    return c
    return None

def sha(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()

proj = resolve(root, target)
if proj is None:
    print(f"ERROR: no project matches: {target}", file=sys.stderr); sys.exit(2)

refs = proj / "references"
libdir = refs / "library"
name = proj.name
print(f"Literature-library integrity check: {name}")
print("NOTE: green = STRUCTURE, not truth. Vector similarity is navigation, not evidence.")

if not (libdir / "library-manifest.json").exists():
    print("  NEEDS-BUILD     no library yet — run build_literature_library.py (advisory, exit 0)")
    sys.exit(0)

manifest = json.loads((libdir / "library-manifest.json").read_text(encoding="utf-8"))
lit_text = (libdir / "literature.jsonl").read_text(encoding="utf-8")
records = [json.loads(l) for l in lit_text.splitlines() if l.strip()]
bib_keys = set()
bib_concat = ""
for b in sorted(refs.glob("*.bib")):
    bib_concat += b.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"@[A-Za-z]+\s*\{\s*([^,\s{}]+)", bib_concat):
        bib_keys.add(m.group(1))

defects, review = [], []

# Freshness
if manifest.get("records_sha256") != sha(lit_text):
    defects.append("DEFECT[STALE]    literature.jsonl changed since build — rebuild the library")
if manifest.get("source_bib_sha256") != sha(bib_concat):
    defects.append("DEFECT[STALE]    project .bib changed since build — rebuild the library")

# Manifest honesty banners
cov = (manifest.get("coverage_statement") or "").lower()
if not ("not" in cov and ("exhaustive" in cov or "completeness" in cov)):
    defects.append("DEFECT[COVERAGE] manifest coverage_statement must disclaim completeness/exhaustiveness")
ban = (manifest.get("ceiling_banner") or "").lower()
if "navigation" not in ban or "not truth" not in ban:
    defects.append("DEFECT[CEILING]  manifest ceiling_banner missing (navigation-not-evidence / not-truth)")

# Per record
for r in records:
    key = r.get("key", "?")
    vs = str(r.get("verification_state", "")).lower()
    if not r.get("source_url") and not r.get("doi"):
        defects.append(f"DEFECT[LINK]     {key}: record has no source link (no url and no doi)")
    if key not in bib_keys:
        defects.append(f"DEFECT[ORPHAN]   {key}: not present in the project .bib")
    if ("resolv" in vs or "attest" in vs) and not signoff:
        defects.append(f"DEFECT[ATTEST]   {key}: self-attested '{vs[:24]}' without LIBRARY_HUMAN_SIGNOFF=1")
    rel = r.get("relevance", {}) or {}
    summ = (rel.get("summary") or "").strip()
    src = rel.get("source", "")
    if src in ("seeded-from-bib-note", "unseeded", "") or len(summ.split()) < THIN:
        review.append(f"NEEDS-ENRICHMENT {key}: relevance is {src or 'absent'} — an agent must author/confirm why it's relevant")

for d in defects: print("  " + d)
for w in review: print("  " + w)
print("---")
print(f"Records: {len(records)}  |  DEFECT: {len(defects)}  |  NEEDS-ENRICHMENT: {len(review)}")

if defects:
    if advisory:
        print("ADVISORY mode: DEFECT(s) present but not blocking (exit 0).")
        sys.exit(0)
    print("GATE FAILED: resolve DEFECT(s) before relying on the library.")
    sys.exit(1)
if review:
    print("PASS (no DEFECT). NEEDS-ENRICHMENT is advisory — agents author relevance as they investigate.")
    sys.exit(0)
print("PASS: structurally sound. (WELL-FORMED, not RESOLVED — records still ship UNVERIFIED.)")
sys.exit(0)
PY
