#!/usr/bin/env bash
# 00 — Finish step 3 of agentteams' open-and-merge-fix-prs.handoff.sh: merge agentteams PR #371 (S-10 local-repos
# carve-out). The handoff stopped only because it polled CI before GitHub registered checks on the updated branch.
# #370 (freeze fix) is already merged as 2c76b4f. OPERATOR ONLY, plain Terminal:
#   bash ~/githubrepositories/researchteam/tmp/by-week/2026-W45/operator/00-finish-agentteams-pr371.sh
set -euo pipefail
GH=(gh --repo jlcatonjr/agentteams)
PR=371
HEAD_REVIEWED="267d5eef098e25f86502470a5c83c7318961fa54"   # head after the handoff's update-branch
[ -z "${CLAUDECODE:-}${CLAUDE_CODE_ENTRYPOINT:-}" ] || { echo "run this in your own terminal" >&2; exit 1; }
read -r state head < <("${GH[@]}" pr view $PR --json state,headRefOid -q '"\(.state) \(.headRefOid)"')
[ "$state" = OPEN ] || { echo "#$PR is $state" >&2; exit 1; }
[ "$head" = "$HEAD_REVIEWED" ] || { echo "#$PR head moved to $head (expected $HEAD_REVIEWED); stop and tell the agentteams session" >&2; exit 1; }
echo "Waiting for CI on #$PR at ${HEAD_REVIEWED:0:10} (Ctrl-C to stop)…"
for i in $(seq 1 30); do [ -n "$("${GH[@]}" pr checks $PR 2>/dev/null)" ] && break; sleep 10; done
"${GH[@]}" pr checks $PR --watch --fail-fast || { echo "CI failed on #$PR; not merging" >&2; exit 1; }
"${GH[@]}" pr view $PR --json title,mergeStateStatus -q '"#'$PR' \(.title)  state=\(.mergeStateStatus)"'
read -r -p "Merge #$PR into main (merge commit, branch kept)? [y/N] " a; [ "${a:-N}" = y ] || { echo "stopped"; exit 1; }
"${GH[@]}" pr merge $PR --merge --match-head-commit "$HEAD_REVIEWED"
echo "Merged. Tell agentteams' session; it builds the rc.15 and v1.0.6 release branches."
