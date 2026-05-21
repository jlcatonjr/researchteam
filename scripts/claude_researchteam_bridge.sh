#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

cmd="${1:-help}"

print_help() {
  cat <<'EOF'
Claude ResearchTeam Bridge

Usage:
  bash scripts/claude_researchteam_bridge.sh <command>

Commands:
  help          Show this help message
  status        Show git status and current branch
  validate      Run repository validator (if available)
  open-reader   Print path to main Zelda research guide
  open-summary  Print path to Zelda summary document
  open-claude-dir Print path to Claude support folder
  plan-path     Print current ISO-week plan directory path
EOF
}

command_status() {
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "[git] branch: $(git rev-parse --abbrev-ref HEAD)"
    echo "[git] head:   $(git rev-parse --short HEAD)"
    echo "[git] status:"
    git status --short
  else
    echo "Not inside a git worktree."
  fi
}

command_validate() {
  if [[ -x "scripts/validate_agentteams_update.sh" ]]; then
    echo "Running scripts/validate_agentteams_update.sh ..."
    bash scripts/validate_agentteams_update.sh
    echo "Validation completed."
  else
    echo "Validator not found at scripts/validate_agentteams_update.sh"
    exit 1
  fi
}

command_open_reader() {
  echo "$ROOT_DIR/Projects/ZeldaTimeline/ZeldaTimelineReader.html"
}

command_open_summary() {
  echo "$ROOT_DIR/Projects/ZeldaTimeline/ZeldaTimelineSummary.html"
}

command_open_claude_dir() {
  echo "$ROOT_DIR/.claude"
}

command_plan_path() {
  week="$(date +%G-W%V)"
  echo "$ROOT_DIR/tmp/by-week/$week"
}

case "$cmd" in
  help)
    print_help
    ;;
  status)
    command_status
    ;;
  validate)
    command_validate
    ;;
  open-reader)
    command_open_reader
    ;;
  open-summary)
    command_open_summary
    ;;
  open-claude-dir)
    command_open_claude_dir
    ;;
  plan-path)
    command_plan_path
    ;;
  *)
    echo "Unknown command: $cmd"
    echo
    print_help
    exit 2
    ;;
esac
