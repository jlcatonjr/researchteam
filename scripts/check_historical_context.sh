#!/usr/bin/env bash
set -euo pipefail

# check_historical_context.sh
#
# Detector / closeout gate for docs/historical-context-protocol.md.
#
# A research project has a *historical-setting register* when its interpretive map
# (Projects/<project>/interpretation/interpretive-map.md, the file the interpretation-advisor
# commissions) carries a "## Historical setting" section holding a markdown table with at least
# one source row, and every row:
#   1. names the source,
#   2. gives a date (a value, a range, or the literal word "unknown" — never blank), and
#   3. gives a basis that is one of: "(per <Author Year>…)", "[editors' inference — unsourced]",
#      or "unresolved".
#
# Structural pass != verified. This script checks that the register is WELL-FORMED; it cannot
# check that a date is right or that the cited source says it. That is the claim audit's job.
#
# A project with no interpretive map is reported NO-MAP and skipped here: map presence is the
# methodology-coverage gate's concern (scripts/check_methodology_coverage.sh).
#
# Usage:
#   scripts/check_historical_context.sh [project-name]
#     no arg   -> scan every research project under Projects/
#     <name>   -> check only Projects/<name>
#
# Exit codes:
#   0  every checked map has a well-formed register (or none in scope)
#   1  at least one map lacks the section or has a deficient row  (gate FAILS)
#   2  usage / environment error
#
# Environment:
#   RT_ROOT=<path>                   override repo root (used by the test harness)
#   HISTORICAL_CONTEXT_ADVISORY=1    warn-only: report gaps but always exit 0
#   METHODOLOGY_UNITS_DIR / METHODOLOGY_MAP_PATH and brief.json "methodology_coverage" are
#   honoured exactly as in check_methodology_coverage.sh, so both gates read the same map.

ROOT_DIR="${RT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

brief_cfg() {
  [[ -f "$ROOT_DIR/brief.json" ]] || return 0
  python3 - "$ROOT_DIR/brief.json" "$1" 2>/dev/null <<'PY' || true
import json, sys
cfg = (json.load(open(sys.argv[1])).get("methodology_coverage") or {})
print(cfg.get(sys.argv[2], "") if isinstance(cfg, dict) else "")
PY
}
UNITS_REL="${METHODOLOGY_UNITS_DIR:-$(brief_cfg units_dir)}"
MAP_REL="${METHODOLOGY_MAP_PATH:-$(brief_cfg map_path)}"
DEFAULT_LAYOUT=1
[[ -n "$UNITS_REL" && "${UNITS_REL%/}" != "Projects" ]] && DEFAULT_LAYOUT=0
UNITS_REL="${UNITS_REL:-Projects}"; UNITS_REL="${UNITS_REL%/}"
MAP_REL="${MAP_REL:-interpretation/interpretive-map.md}"
PROJECTS_DIR="$ROOT_DIR/$UNITS_REL"
ADVISORY="${HISTORICAL_CONTEXT_ADVISORY:-0}"

target="${1:-}"

is_research_project() {
  local d="$1"
  [[ "$DEFAULT_LAYOUT" == "0" ]] && return 0
  [[ -f "$d/00-research-plan.md" ]] && return 0
  [[ -d "$d/references" ]] && return 0
  ls "$d"/[0-9][0-9]-*.md >/dev/null 2>&1 && return 0
  return 1
}

# Parse the "## Historical setting" register. Prints one line:
#   NOSECTION | NOROWS | OK <rows> <sourced> <inference> <unresolved> | BAD <rows> <detail>
parse_register() {
  python3 - "$1" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r"^##\s+Historical setting\b.*$", text, flags=re.I | re.M)
if not m:
    print("NOSECTION"); sys.exit()
body = text[m.end():]
nxt = re.search(r"^##\s", body, flags=re.M)
body = body[: nxt.start()] if nxt else body
rows = [l.strip() for l in body.splitlines() if l.strip().startswith("|")]
# drop the header row and the |---| separator
rows = [r for r in rows if not re.fullmatch(r"\|[\s:|-]+\|?", r)][1:]
if not rows:
    print("NOROWS"); sys.exit()
EMPTY = {"", "-", "—", "–", "?", "tbd", "todo"}
sourced = inference = unresolved = 0
bad = []
for i, r in enumerate(rows, 1):
    cells = [c.strip() for c in r.strip("|").split("|")]
    src = cells[0] if cells else ""
    date = cells[1] if len(cells) > 1 else ""
    basis = cells[-1] if len(cells) > 2 else ""
    b = basis.lower()
    problems = []
    if src.lower() in EMPTY:
        problems.append("no source")
    if date.lower() in EMPTY:
        problems.append("no date")
    if "(per " in b:
        sourced += 1
    elif "editors' inference" in b or "editors’ inference" in b:
        inference += 1
    elif "unresolved" in b:
        unresolved += 1
    else:
        problems.append("basis not (per …)/[editors' inference — unsourced]/unresolved")
    if problems:
        bad.append(f"row {i} ({src or '?'}): {', '.join(problems)}")
if bad:
    print(f"BAD {len(rows)} " + "; ".join(bad))
else:
    print(f"OK {len(rows)} {sourced} {inference} {unresolved}")
PY
}

# Returns 0 pass/skip, 1 fail.
check_project() {
  local name="$1"
  local map="$PROJECTS_DIR/$name/$MAP_REL"
  if [[ ! -f "$map" ]]; then
    printf 'NO-MAP          %-32s skipped (run check_methodology_coverage.sh)\n' "$name"
    return 0
  fi
  local res
  res="$(parse_register "$map")"
  case "$res" in
    NOSECTION)
      printf 'MISSING-SETTING %-32s map has no "## Historical setting" section\n' "$name"
      return 1 ;;
    NOROWS)
      printf 'EMPTY-SETTING   %-32s "## Historical setting" has no table rows\n' "$name"
      return 1 ;;
    OK\ *)
      read -r _ rows src inf unr <<< "$res"
      printf 'SETTING-OK      %-32s rows=%s sourced=%s inference=%s unresolved=%s\n' \
        "$name" "$rows" "$src" "$inf" "$unr"
      return 0 ;;
    BAD\ *)
      printf 'SETTING-BAD     %-32s %s\n' "$name" "${res#BAD }"
      return 1 ;;
    *)
      printf 'ERROR           %-32s could not parse register\n' "$name"
      return 1 ;;
  esac
}

main() {
  if [[ ! -d "$PROJECTS_DIR" ]]; then
    echo "No $UNITS_REL/ directory under $ROOT_DIR; nothing to check."
    return 0
  fi

  local names=()
  if [[ -n "$target" ]]; then
    if [[ ! -d "$PROJECTS_DIR/$target" ]]; then
      echo "ERROR: project not found: $UNITS_REL/$target" >&2
      return 2
    fi
    names=("$target")
  else
    local d
    for d in "$PROJECTS_DIR"/*/; do
      [[ -d "$d" ]] || continue
      is_research_project "$d" || continue
      names+=("$(basename "$d")")
    done
  fi

  if [[ ${#names[@]} -eq 0 ]]; then
    echo "No research projects in scope; nothing to check."
    return 0
  fi

  echo "Historical-context check (root: $ROOT_DIR)"
  local failures=0 n
  for n in "${names[@]}"; do
    if ! check_project "$n"; then
      failures=$((failures + 1))
    fi
  done

  echo "---"
  echo "Projects checked: ${#names[@]}  |  register gaps: $failures"
  echo "Structural pass != verified: dates and bases still go through the claim audit."

  if [[ "$failures" -gt 0 ]]; then
    if [[ "$ADVISORY" == "1" ]]; then
      echo "ADVISORY mode: register gaps found but not blocking (exit 0)."
      echo "Remediation: see docs/historical-context-protocol.md (route to @interpretation-advisor)."
      return 0
    fi
    echo "GATE FAILED: add or repair each project's Historical setting register (docs/historical-context-protocol.md)."
    return 1
  fi

  echo "GATE PASSED: every checked map has a well-formed Historical setting register."
  return 0
}

main
