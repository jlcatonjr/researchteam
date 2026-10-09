#!/usr/bin/env bash
# Test suite for scripts/check_historical_context.sh
#
# Self-contained: builds throwaway RT_ROOT fixtures under a temp dir and asserts the
# detector's exit code and a signature substring for each scenario. No network, no repo
# mutation. Runnable under bash 3.2 (macOS system bash) and modern bash.
#
#   bash scripts/tests/test_historical_context.sh
#
# Exit 0 = all scenarios pass; 1 = at least one failed.

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DETECTOR="$(cd "$HERE/.." && pwd)/check_historical_context.sh"

if [[ ! -f "$DETECTOR" ]]; then
  echo "FATAL: detector not found at $DETECTOR" >&2
  exit 1
fi

TMP_ROOT="$(mktemp -d 2>/dev/null || mktemp -d -t rt-histctx)"
trap 'rm -rf "$TMP_ROOT"' EXIT

pass=0
fail=0

HEADER='| Source | Date | Place | Occasion / audience | Text version | Basis |
|---|---|---|---|---|---|'

# make_project <root> <name> [map-body]   (no map-body -> no map file)
make_project() {
  root="$1"; name="$2"; body="${3-__none__}"
  pdir="$root/Projects/$name"
  mkdir -p "$pdir"
  echo "# plan" > "$pdir/00-research-plan.md"   # research marker
  if [[ "$body" != "__none__" ]]; then
    mkdir -p "$pdir/interpretation"
    printf '# Interpretive map\n\n%s\n\n## Vantage\n\nnot part of the register | x | y |\n' "$body" \
      > "$pdir/interpretation/interpretive-map.md"
  fi
}

assert() {
  label="$1"; exp_code="$2"; exp_sub="$3"; act_code="$4"; act_out="$5"
  if [[ "$act_code" == "$exp_code" ]] && printf '%s' "$act_out" | grep -q -- "$exp_sub"; then
    printf '  ok    %s\n' "$label"
    pass=$((pass + 1))
  else
    printf '  FAIL  %s\n        expected exit=%s substr=%q\n        got      exit=%s\n%s\n' \
      "$label" "$exp_code" "$exp_sub" "$act_code" "$act_out" >&2
    fail=$((fail + 1))
  fi
}

run() {
  local root="$1"; shift
  OUT="$(RT_ROOT="$root" bash "$DETECTOR" "$@" 2>&1)"; CODE=$?
}

echo "Historical-context detector — test scenarios"

# 1. well-formed register: one sourced row, one inference row, one unresolved row
R="$TMP_ROOT/s1"; make_project "$R" proj "## Historical setting

$HEADER
| *Mystagogia* | c. 628–630 | North Africa | monks | PG 91 | (per Louth 1996, 6) |
| *Corpus Dionysiacum* | c. 500 | Syria? | — | PTS 33 | [editors' inference — unsourced] |
| Scholia | unknown | — | — | — | unresolved |"
run "$R" proj; assert "well-formed register passes" 0 "rows=3 sourced=1 inference=1 unresolved=1" "$CODE" "$OUT"

# 2. map without the section
R="$TMP_ROOT/s2"; make_project "$R" proj "## Genealogy

- a → b (per X 2000)"
run "$R" proj; assert "missing section fails" 1 "MISSING-SETTING" "$CODE" "$OUT"

# 3. section with header but no rows
R="$TMP_ROOT/s3"; make_project "$R" proj "## Historical setting

$HEADER"
run "$R" proj; assert "empty register fails" 1 "EMPTY-SETTING" "$CODE" "$OUT"

# 4. blank date
R="$TMP_ROOT/s4"; make_project "$R" proj "## Historical setting

$HEADER
| *Ambigua* | — | Constantinople | — | PG 91 | (per Louth 1996) |"
run "$R" proj; assert "blank date fails" 1 "no date" "$CODE" "$OUT"

# 5. basis that is neither sourced, inference nor unresolved
R="$TMP_ROOT/s5"; make_project "$R" proj "## Historical setting

$HEADER
| *Ambigua* | 630s | — | — | PG 91 | well known |"
run "$R" proj; assert "unmarked basis fails" 1 "basis not" "$CODE" "$OUT"

# 6. no map -> skipped, exit 0
R="$TMP_ROOT/s6"; make_project "$R" proj
run "$R" proj; assert "no map is skipped" 0 "NO-MAP" "$CODE" "$OUT"

# 7. advisory downgrade
R="$TMP_ROOT/s7"; make_project "$R" proj "## Genealogy"
OUT="$(RT_ROOT="$R" HISTORICAL_CONTEXT_ADVISORY=1 bash "$DETECTOR" proj 2>&1)"; CODE=$?
assert "advisory downgrade exit 0" 0 "ADVISORY" "$CODE" "$OUT"

# 8. heading match is case-insensitive and allows a suffix
R="$TMP_ROOT/s8"; make_project "$R" proj "## Historical Setting (register)

$HEADER
| *Ambigua* | 630s | — | — | PG 91 | (per Louth 1996) |"
run "$R" proj; assert "heading variant passes" 0 "SETTING-OK" "$CODE" "$OUT"

# 9. nonexistent named target -> exit 2
run "$R" nope; assert "nonexistent named exit 2" 2 "not found" "$CODE" "$OUT"

# 10. configured layout via brief.json "methodology_coverage"
R="$TMP_ROOT/s10"; mkdir -p "$R/reports/dossiers/p1"
printf '{"methodology_coverage": {"units_dir": "reports/dossiers", "map_path": "interpretation.md"}}' > "$R/brief.json"
printf '## Historical setting\n\n%s\n| X | 1900 | — | — | — | (per Y 2000) |\n' "$HEADER" > "$R/reports/dossiers/p1/interpretation.md"
run "$R" p1; assert "configured layout honoured" 0 "SETTING-OK" "$CODE" "$OUT"

echo "---"
echo "Passed: $pass  Failed: $fail"
[[ "$fail" -eq 0 ]]
