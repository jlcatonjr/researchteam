#!/usr/bin/env bash
# Test suite for scripts/check_methodology_coverage.sh
#
# Self-contained: builds throwaway RT_ROOT fixtures under a temp dir and asserts the
# detector's exit code and a signature substring for each scenario. No network, no repo
# mutation. Runnable under bash 3.2 (macOS system bash) and modern bash.
#
#   bash scripts/tests/test_methodology_coverage.sh
#
# Exit 0 = all scenarios pass; 1 = at least one failed.

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DETECTOR="$(cd "$HERE/.." && pwd)/check_methodology_coverage.sh"

if [[ ! -f "$DETECTOR" ]]; then
  echo "FATAL: detector not found at $DETECTOR" >&2
  exit 1
fi

TMP_ROOT="$(mktemp -d 2>/dev/null || mktemp -d -t rt-methcov)"
trap 'rm -rf "$TMP_ROOT"' EXIT

pass=0
fail=0

# make_project <root> <name> [--map "guideRef"] [--guide "file=status"] [--plain]
# Builds Projects/<name> with a research marker, and optionally a map + guide.
make_project() {
  root="$1"; name="$2"; shift 2
  pdir="$root/Projects/$name"
  mkdir -p "$pdir"
  echo "# plan" > "$pdir/00-research-plan.md"   # research marker
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --map)
        mkdir -p "$pdir/interpretation"
        printf 'Interpretive map referencing %s\n' "$2" > "$pdir/interpretation/interpretive-map.md"
        shift 2 ;;
      --map-noref)
        mkdir -p "$pdir/interpretation"
        echo "Interpretive map with no guide reference" > "$pdir/interpretation/interpretive-map.md"
        shift 1 ;;
      --guide)
        gdir="$root/.github/agents/references/methodology"
        mkdir -p "$gdir"
        gfile="${2%%=*}"; gstatus="${2#*=}"
        printf '# guide\nstatus: %s\n' "$gstatus" > "$gdir/$gfile"
        shift 2 ;;
      *) shift 1 ;;
    esac
  done
}

# assert <label> <expected_exit> <expected_substr> <actual_exit> <actual_out>
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

run() {  # run <RT_ROOT> [args...] -> sets OUT, CODE
  local root="$1"; shift
  OUT="$(RT_ROOT="$root" bash "$DETECTOR" "$@" 2>&1)"; CODE=$?
}
run_advisory() {
  local root="$1"; shift
  OUT="$(RT_ROOT="$root" METHODOLOGY_COVERAGE_ADVISORY=1 bash "$DETECTOR" "$@" 2>&1)"; CODE=$?
}

echo "Methodology-coverage detector — test scenarios"

# 1. COVERED, active
R="$TMP_ROOT/s1"; make_project "$R" proj --map "econ-cycles.methodology.guide.md" --guide "econ-cycles.methodology.guide.md=active"
run "$R" proj;  assert "COVERED active"            0 "COVERED" "$CODE" "$OUT"

# 2. COVERED, provisional (must still pass)
R="$TMP_ROOT/s2"; make_project "$R" proj --map "g.methodology.guide.md" --guide "g.methodology.guide.md=provisional"
run "$R" proj;  assert "COVERED provisional passes" 0 "provisional" "$CODE" "$OUT"

# 3. COVERED, unknown status (guide file present, no status: line)
R="$TMP_ROOT/s3"; make_project "$R" proj --map "g.methodology.guide.md"
gdir="$R/.github/agents/references/methodology"; mkdir -p "$gdir"; echo "# guide no status" > "$gdir/g.methodology.guide.md"
run "$R" proj;  assert "COVERED unknown status"    0 "unknown" "$CODE" "$OUT"

# 4. MISSING-MAP
R="$TMP_ROOT/s4"; make_project "$R" proj
run "$R" proj;  assert "MISSING-MAP exit 1"        1 "MISSING-MAP" "$CODE" "$OUT"

# 5. MISSING-GUIDE (map references a guide file that is absent)
R="$TMP_ROOT/s5"; make_project "$R" proj --map "absent.methodology.guide.md"
run "$R" proj;  assert "MISSING-GUIDE absent file" 1 "MISSING-GUIDE" "$CODE" "$OUT"

# 6. MISSING-GUIDE (map references no guide at all)
R="$TMP_ROOT/s6"; make_project "$R" proj --map-noref
run "$R" proj;  assert "MISSING-GUIDE no reference" 1 "references no" "$CODE" "$OUT"

# 7. named vs scan-all: scan-all skips a non-research dir
R="$TMP_ROOT/s7"; make_project "$R" real --map "g.methodology.guide.md" --guide "g.methodology.guide.md=active"
mkdir -p "$R/Projects/scratch"; echo "notes" > "$R/Projects/scratch/notes.txt"   # not a research project
run "$R";       assert "scan-all skips non-research" 0 "Projects checked: 1" "$CODE" "$OUT"

# 8. named target is always checked even if it looks non-research — here it IS research and covered
run "$R" real;  assert "named target check"        0 "COVERED" "$CODE" "$OUT"

# 9. nonexistent named target -> exit 2
run "$R" does-not-exist; assert "nonexistent named exit 2" 2 "not found" "$CODE" "$OUT"

# 10. empty root (no Projects/) -> exit 0
R="$TMP_ROOT/s10"; mkdir -p "$R"
run "$R";       assert "empty root exit 0"         0 "nothing to check" "$CODE" "$OUT"

# 11. advisory downgrade: a MISSING project exits 0 under advisory env
R="$TMP_ROOT/s11"; make_project "$R" proj
run_advisory "$R" proj; assert "advisory downgrade exit 0" 0 "ADVISORY" "$CODE" "$OUT"

echo "---"
echo "Passed: $pass  Failed: $fail"
[[ "$fail" -eq 0 ]]
