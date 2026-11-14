#!/usr/bin/env bash
# 08 — Merge researchteam PR #141 (fix/bootstrap-pip-pin: bootstrap pins pip==26.2.2, S-10) at its reviewed head.
# OPERATOR ONLY, plain Terminal:
#   bash ~/githubrepositories/researchteam/tmp/by-week/2026-W45/operator/08-merge-pr141.sh
# bootstrap script, two tests, CHANGELOG. --match-head-commit makes GitHub refuse the merge if the branch moved after review.
source "$(dirname "$0")/common.sh"
refuse_agent
PR=141
HEAD_REVIEWED="${1:-6881b99d62008fa226b37499b87a010ea809cc26}"
BR="fix/bootstrap-pip-pin"

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
echo "Tell the researchteam session it is merged. It ships to derived repos in researchteam v1.1.0-rc.5."
