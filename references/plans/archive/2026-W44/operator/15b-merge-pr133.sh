#!/usr/bin/env bash
# 15b — Merge researchteam PR #133 (release-prep/1.1.0rc3) at its reviewed head, then print the merged main SHA for 16.
# OPERATOR ONLY, plain Terminal:
#   bash ~/githubrepositories/researchteam/tmp/by-week/2026-W44/operator/15b-merge-pr133.sh
# --match-head-commit makes GitHub refuse the merge if the branch moved after review. Uses a merge commit, as the
# earlier PRs did. Nothing else is changed.
source "$(dirname "$0")/common.sh"
refuse_agent
PR=133
HEAD_REVIEWED="d99b1d60b2923cc7452cef4711fb732cd9d87b4e"   # spec + CHANGELOG (00f513f) + signed pin row
BR="release-prep/1.1.0rc3"
RT_URL="https://github.com/$REPO"

read -r state head ref mstate < <(gh pr view "$PR" -R "$REPO" --json state,headRefOid,headRefName,mergeStateStatus \
  -q '"\(.state) \(.headRefOid) \(.headRefName) \(.mergeStateStatus)"')
[ "$state" = OPEN ] || die "PR #$PR is $state, not OPEN"
[ "$ref" = "$BR" ] || die "PR #$PR head branch is $ref, not $BR"
[ "$head" = "$HEAD_REVIEWED" ] || die "PR #$PR head is $head, not the reviewed $HEAD_REVIEWED"
[ "$mstate" = CLEAN ] || die "PR #$PR merge state is $mstate (need CLEAN: checks green, no conflicts)"
# The signed row must be in the tree being merged.
ngit -C "$MAIN" fetch -q "$RT_URL" "refs/heads/$BR"
ngit -C "$MAIN" show "$HEAD_REVIEWED:.github/agents/references/security-decisions.log.csv" \
  | grep -qF ",pin-agentteams-v1.1.0-rc.11,PASS," || die "no signed pin-agentteams-v1.1.0-rc.11 row at $HEAD_REVIEWED"

say "PR #$PR ($BR) at ${HEAD_REVIEWED:0:12}: open, checks green, signed row present"
gh pr view "$PR" -R "$REPO" --json title -q .title
confirm "Merge PR #$PR into main (merge commit)?"
gh pr merge "$PR" -R "$REPO" --merge --match-head-commit "$HEAD_REVIEWED"

MERGED="$(gh pr view "$PR" -R "$REPO" --json state,mergeCommit -q 'select(.state=="MERGED") | .mergeCommit.oid')"
[[ "$MERGED" =~ ^[0-9a-f]{40}$ ]] || die "PR #$PR did not report a merge commit"
say "Merged PR #$PR -> main $MERGED"
echo "Next (cut and sign v1.1.0-rc.3):"
echo "  bash ~/githubrepositories/researchteam/tmp/by-week/2026-W44/operator/16-cut-rc3.sh $MERGED"
