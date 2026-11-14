#!/usr/bin/env bash
# 01 — Merge researchteam PR #131 (docs/managed-docs-mathagents-handoff) at its reviewed head.
# OPERATOR ONLY, plain Terminal:
#   bash ~/githubrepositories/researchteam/tmp/by-week/2026-W45/operator/01-merge-pr131.sh
# Docs only (mathAgents' managed-docs hand-off). researchteam-25 merged main into the branch to clear the CHANGELOG
# conflict; pytest 473 passed / 7 skipped, bridge validate passes. --match-head-commit makes GitHub refuse the merge if
# the branch moved after review. Uses a merge commit, as the earlier PRs did. Nothing else is changed.
source "$(dirname "$0")/common.sh"
refuse_agent
PR=131
HEAD_REVIEWED="6f45277a8fb3e1fd0e0b588d967ad9c80f8849d5"
BR="docs/managed-docs-mathagents-handoff"

read -r state head ref mstate < <(gh pr view "$PR" -R "$REPO" --json state,headRefOid,headRefName,mergeStateStatus \
  -q '"\(.state) \(.headRefOid) \(.headRefName) \(.mergeStateStatus)"')
[ "$state" = OPEN ] || die "PR #$PR is $state, not OPEN"
[ "$ref" = "$BR" ] || die "PR #$PR head branch is $ref, not $BR"
[ "$head" = "$HEAD_REVIEWED" ] || die "PR #$PR head is $head, not the reviewed $HEAD_REVIEWED"
[ "$mstate" = CLEAN ] || die "PR #$PR merge state is $mstate (need CLEAN: checks green, no conflicts)"

say "PR #$PR ($BR) at ${HEAD_REVIEWED:0:12}: open, checks green"
gh pr view "$PR" -R "$REPO" --json title,files -q '.title, (.files[] | "  \(.path) +\(.additions)/-\(.deletions)")'
confirm "Merge PR #$PR into main (merge commit)?"
gh pr merge "$PR" -R "$REPO" --merge --match-head-commit "$HEAD_REVIEWED"

MERGED="$(gh pr view "$PR" -R "$REPO" --json state,mergeCommit -q 'select(.state=="MERGED") | .mergeCommit.oid')"
[[ "$MERGED" =~ ^[0-9a-f]{40}$ ]] || die "PR #$PR did not report a merge commit"
say "Merged PR #$PR -> main $MERGED"
echo "Tell the researchteam session it is merged. Next: 02-sign-s10-restored.sh"
