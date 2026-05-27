#!/usr/bin/env bash
# agentteams hook-guard (Phase 3)
# Records a notice when a Claude hook fires for a bridged governance
# agent slug. Refuses re-entry beyond AGENTTEAMS_HOOK_MAX_DEPTH (default 2)
# to bound any agent → write → hook cascade.
set -u

event="${1:-unknown-event}"
slug="${2:-unknown-slug}"

max_depth="${AGENTTEAMS_HOOK_MAX_DEPTH:-2}"
current_depth="${AGENTTEAMS_HOOK_DEPTH:-0}"

if [ "$current_depth" -ge "$max_depth" ]; then
  # Silent no-op; do NOT escalate (exit 0 lets Claude continue).
  exit 0
fi

# Locate project root from script location: .claude/hook-guard.sh ⇒ root = parent of .claude
script_dir="$(cd "$(dirname "$0")" && pwd)"
project_root="$(dirname "$script_dir")"
notice_dir="$project_root/.claude/hook-notices"
mkdir -p "$notice_dir"
date_stamp="$(date -u +%Y-%m-%d)"
ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "[$ts] event=$event slug=$slug depth=$current_depth" >> "$notice_dir/$date_stamp.log"

# Increment depth for any downstream invocation triggered by this hook.
export AGENTTEAMS_HOOK_DEPTH="$((current_depth + 1))"
exit 0
