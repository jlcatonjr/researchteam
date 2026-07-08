#!/usr/bin/env bash
# Test suite for the per-project literature library (build + integrity gate).
# Self-contained throwaway RT_ROOT fixtures; needs python3 (the build/gate use it). Runs under
# bash 3.2 (macOS system bash) and modern bash.
#
#   bash scripts/tests/test_literature_library.sh
# Exit 0 = all pass; 1 = a failure; 2 = python3 missing (skip).

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS="$(cd "$HERE/.." && pwd)"
BUILD="$SCRIPTS/build_literature_library.py"
GATE="$SCRIPTS/check_literature_library_integrity.sh"

command -v python3 >/dev/null 2>&1 || { echo "python3 not found — skipping"; exit 0; }

TMP_ROOT="$(mktemp -d 2>/dev/null || mktemp -d -t rt-litlib-test)"
trap 'rm -rf "$TMP_ROOT"' EXIT
pass=0; fail=0

mkfile() { mkdir -p "$(dirname "$1")"; cat > "$1"; }

# assert <label> <exp_exit> <exp_substr> <act_exit> <act_out>
assert() {
  local label="$1" ec="$2" sub="$3" ac="$4" out="$5"
  if [ "$ac" = "$ec" ] && printf '%s' "$out" | grep -q -- "$sub"; then
    printf '  ok    %s\n' "$label"; pass=$((pass + 1))
  else
    printf '  FAIL  %s\n        want exit=%s substr=%s; got exit=%s\n%s\n' "$label" "$ec" "$sub" "$ac" "$out" >&2
    fail=$((fail + 1))
  fi
}
gate() { OUT="$(RT_ROOT="$1" bash "$GATE" "$2" 2>&1)"; CODE=$?; }
gate_adv() { OUT="$(RT_ROOT="$1" LITERATURE_LIBRARY_ADVISORY=1 bash "$GATE" "$2" 2>&1)"; CODE=$?; }
gate_signoff() { OUT="$(RT_ROOT="$1" LIBRARY_HUMAN_SIGNOFF=1 bash "$GATE" "$2" 2>&1)"; CODE=$?; }
build() { RT_ROOT="$1" python3 "$BUILD" "$2" >/dev/null 2>&1; }

echo "Literature-library — test scenarios"

# 1. No library yet -> NEEDS-BUILD, exit 0
R="$TMP_ROOT/s1"
mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@article{A2000, author = {A, A.}, title = {Search frictions in labor markets}, year = {2000}, url = {https://example.org/a}, note = {Foundational treatment of matching frictions and unemployment dynamics; the project's core reference.}}
EOF
gate "$R" P; assert "no library -> NEEDS-BUILD"      0 "NEEDS-BUILD" "$CODE" "$OUT"

# 2. Build -> gate PASS (seeded relevance -> NEEDS-ENRICHMENT advisory), exit 0
build "$R" P
gate "$R" P
assert "built library gate PASS"                     0 "PASS" "$CODE" "$OUT"
assert "seeded record -> NEEDS-ENRICHMENT"           0 "NEEDS-ENRICHMENT" "$CODE" "$OUT"

# 3. Stale: change the .bib after build -> DEFECT[STALE], exit 1
printf '@misc{B2001, author={B,B.}, title={Second}, year={2001}, url={https://example.org/b}, note={A relevant secondary source added later in the investigation for comparison and context.}}\n' >> "$R/Projects/P/references/bibliography.bib"
gate "$R" P; assert "stale index -> DEFECT[STALE]"   1 "DEFECT\[STALE\]" "$CODE" "$OUT"
gate_adv "$R" P; assert "stale advisory downgrade"   0 "ADVISORY" "$CODE" "$OUT"
build "$R" P   # re-freshen

# 4. Missing source link -> DEFECT[LINK], exit 1
R="$TMP_ROOT/s4"
mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@book{NoLink1999, author = {C, C.}, title = {A book with no link at all}, year = {1999}, note = {Discusses the institutional development central to the project's argument over several chapters.}}
EOF
build "$R" P
gate "$R" P; assert "missing source link -> DEFECT[LINK]" 1 "DEFECT\[LINK\]" "$CODE" "$OUT"

# 5. Self-attestation without signoff -> DEFECT[ATTEST]; with signoff -> exit 0
R="$TMP_ROOT/s5"
mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@article{D2010, author = {D, D.}, title = {A well-linked article on the topic}, year = {2010}, url = {https://example.org/d}, note = {A substantive, relevant analysis the project builds on directly in its main argument.}}
EOF
build "$R" P
# flip the record's verification_state to a self-attested value, then rebuild (preserves it, refreshes hash)
python3 - "$R/Projects/P/references/library/literature.jsonl" <<'PY'
import sys, json
p = sys.argv[1]
rows = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
rows[0]["verification_state"] = "resolved"
open(p, "w", encoding="utf-8").write("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows))
PY
build "$R" P
gate "$R" P;         assert "self-attested -> DEFECT[ATTEST]"     1 "DEFECT\[ATTEST\]" "$CODE" "$OUT"
gate_signoff "$R" P; assert "signoff permits attested state"      0 "PASS" "$CODE" "$OUT"

# 6. Determinism: build twice, term-vectors byte-identical
R="$TMP_ROOT/s6"
mkfile "$R/Projects/P/references/bibliography.bib" <<'EOF'
@article{E2005, author = {E, E.}, title = {Determinism check}, year = {2005}, url = {https://example.org/e}, note = {Relevant methodological reference used to frame the project's empirical strategy and scope.}}
EOF
build "$R" P
cp "$R/Projects/P/references/library/term-vectors.jsonl" "$TMP_ROOT/tv1"
build "$R" P
if diff -q "$TMP_ROOT/tv1" "$R/Projects/P/references/library/term-vectors.jsonl" >/dev/null; then
  printf '  ok    %s\n' "determinism (identical term-vectors twice)"; pass=$((pass + 1))
else
  printf '  FAIL  %s\n' "determinism (term-vectors differ)" >&2; fail=$((fail + 1))
fi

# 7. Manifest carries the honest ceiling banner + coverage disclaimer
grep -q "navigation, not evidence" "$R/Projects/P/references/library/library-manifest.json" \
  && grep -qi "not.*exhaustive\|not.*completeness" "$R/Projects/P/references/library/library-manifest.json" \
  && { printf '  ok    %s\n' "manifest ceiling + coverage disclaimer"; pass=$((pass + 1)); } \
  || { printf '  FAIL  %s\n' "manifest missing ceiling/coverage" >&2; fail=$((fail + 1)); }

echo "---"
echo "Passed: $pass  Failed: $fail"
[ "$fail" -eq 0 ]
