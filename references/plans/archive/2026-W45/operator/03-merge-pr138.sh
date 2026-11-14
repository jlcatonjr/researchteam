#!/usr/bin/env bash
# 03 — Merge researchteam PR #138 (docs/s10-cooldown-restored) once the signed s10-release-cooldown-restored row is
# committed on it. OPERATOR ONLY, plain Terminal, AFTER 02 and after the researchteam session pushes the row:
#   bash ~/githubrepositories/researchteam/tmp/by-week/2026-W45/operator/03-merge-pr138.sh <40-hex head the session reports>
# Refuses unless the head carries the signed row. --match-head-commit makes GitHub refuse the merge if the branch moved
# after review. Merge commit, as the earlier PRs did. Nothing else is changed.
source "$(dirname "$0")/common.sh"
refuse_agent
PR=138
HEAD_REVIEWED="${1:?usage: $0 <40-hex head of docs/s10-cooldown-restored, with the signed row>}"
[[ "$HEAD_REVIEWED" =~ ^[0-9a-f]{40}$ ]] || die "the head must be a full 40-hex SHA"
BR="docs/s10-cooldown-restored"
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
  | grep -qF ",s10-release-cooldown-restored,PASS," || die "no signed s10-release-cooldown-restored row at $HEAD_REVIEWED"

say "PR #$PR ($BR) at ${HEAD_REVIEWED:0:12}: open, checks green, signed row present"
gh pr view "$PR" -R "$REPO" --json title -q .title
confirm "Merge PR #$PR into main (merge commit)?"
gh pr merge "$PR" -R "$REPO" --merge --match-head-commit "$HEAD_REVIEWED"

MERGED="$(gh pr view "$PR" -R "$REPO" --json state,mergeCommit -q 'select(.state=="MERGED") | .mergeCommit.oid')"
[[ "$MERGED" =~ ^[0-9a-f]{40}$ ]] || die "PR #$PR did not report a merge commit"
say "Merged PR #$PR -> main $MERGED"
echo "Tell the researchteam session it is merged."
