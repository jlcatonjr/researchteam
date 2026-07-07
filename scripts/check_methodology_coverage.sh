#!/usr/bin/env bash
set -euo pipefail

# check_methodology_coverage.sh
#
# Detector / closeout gate for the interpretation-advisor methodology feature.
#
# A research project has *methodology coverage* when BOTH hold:
#   1. Projects/<project>/interpretation/interpretive-map.md exists (the per-project
#      scaffold the interpretation-advisor commissions), AND
#   2. every domain guide that map references (<name>.methodology.guide.md) exists on disk
#      under .github/agents/references/methodology/.
#
# The map is the project-local coverage signal; requiring the referenced guide to exist
# closes the "map points at a guide that was never written" hole. A `status: provisional`
# guide counts as covered (that is the documented interim state) but is surfaced.
#
# Usage:
#   scripts/check_methodology_coverage.sh [project-name]
#     no arg   -> scan every research project under Projects/
#     <name>   -> check only Projects/<name>
#
# Exit codes:
#   0  all checked projects are covered (or none in scope)
#   1  at least one project is missing coverage  (gate FAILS)
#   2  usage / environment error
#
# Environment:
#   RT_ROOT=<path>                     override repo root (used by the test harness)
#   METHODOLOGY_COVERAGE_ADVISORY=1    warn-only: report gaps but always exit 0

ROOT_DIR="${RT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PROJECTS_DIR="$ROOT_DIR/Projects"
GUIDE_DIR="$ROOT_DIR/.github/agents/references/methodology"
ADVISORY="${METHODOLOGY_COVERAGE_ADVISORY:-0}"

target="${1:-}"

# Is this directory a research project worth gating? (named target is always checked)
is_research_project() {
  local d="$1"
  [[ -f "$d/00-research-plan.md" ]] && return 0
  [[ -d "$d/references" ]] && return 0
  # any numbered deliverable, e.g. 01-literature-review.md
  ls "$d"/[0-9][0-9]-*.md >/dev/null 2>&1 && return 0
  return 1
}

# Extract distinct guide filenames referenced by a map file.
referenced_guides() {
  grep -oE '[A-Za-z0-9._-]+\.methodology\.guide\.md' "$1" 2>/dev/null | sort -u || true
}

guide_status() {
  # Best-effort read of the guide's status: field; "unknown" if absent.
  local g="$1"
  local s
  s="$(grep -ioE 'status:[^A-Za-z]*([Aa]ctive|[Pp]rovisional)' "$g" 2>/dev/null | head -1 | grep -ioE '(active|provisional)' | head -1 || true)"
  printf '%s' "${s:-unknown}"
}

# Check one project directory; echoes a status line; returns 0 if covered, 1 if missing.
check_project() {
  local name="$1"
  local dir="$PROJECTS_DIR/$name"
  local map="$dir/interpretation/interpretive-map.md"

  if [[ ! -f "$map" ]]; then
    printf 'MISSING-MAP    %-32s no interpretation/interpretive-map.md\n' "$name"
    return 1
  fi

  local guides
  guides="$(referenced_guides "$map")"
  if [[ -z "$guides" ]]; then
    printf 'MISSING-GUIDE  %-32s map references no .methodology.guide.md\n' "$name"
    return 1
  fi

  local missing=() statuses=()
  local g
  while IFS= read -r g; do
    [[ -z "$g" ]] && continue
    if [[ -f "$GUIDE_DIR/$g" ]]; then
      statuses+=("$g=$(guide_status "$GUIDE_DIR/$g")")
    else
      missing+=("$g")
    fi
  done <<< "$guides"

  if [[ ${#missing[@]} -gt 0 ]]; then
    printf 'MISSING-GUIDE  %-32s guide file(s) absent: %s\n' "$name" "${missing[*]}"
    return 1
  fi

  printf 'COVERED        %-32s %s\n' "$name" "${statuses[*]}"
  return 0
}

main() {
  if [[ ! -d "$PROJECTS_DIR" ]]; then
    echo "No Projects/ directory under $ROOT_DIR; nothing to check."
    return 0
  fi

  local names=()
  if [[ -n "$target" ]]; then
    if [[ ! -d "$PROJECTS_DIR/$target" ]]; then
      echo "ERROR: project not found: Projects/$target" >&2
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

  echo "Methodology-coverage check (root: $ROOT_DIR)"
  local failures=0 n
  for n in "${names[@]}"; do
    if ! check_project "$n"; then
      failures=$((failures + 1))
    fi
  done

  echo "---"
  echo "Projects checked: ${#names[@]}  |  missing coverage: $failures"

  if [[ "$failures" -gt 0 ]]; then
    if [[ "$ADVISORY" == "1" ]]; then
      echo "ADVISORY mode: coverage gaps found but not blocking (exit 0)."
      echo "Remediation: route the project to @interpretation-advisor to commission the guide + map."
      return 0
    fi
    echo "GATE FAILED: route each MISSING project to @interpretation-advisor before compiling deliverables."
    return 1
  fi

  echo "GATE PASSED: all in-scope projects have methodology coverage."
  return 0
}

main
