#!/usr/bin/env bash
# 05 — Merge researchteam PR #139 (chore/agentteams-1.1.0-rc.15) once the signed s10-cooldown-exempt:jlcatonjr/agentteams
# and pin-agentteams-v1.1.0-rc.15 rows and the re-render are committed on it. OPERATOR ONLY, plain Terminal, AFTER 04:
#   bash ~/githubrepositories/researchteam/tmp/by-week/2026-W45/operator/05-merge-rc15-pin.sh <40-hex head the session reports>
# Refuses unless the head carries both signed rows and pins the verified rc.15 commit. --match-head-commit makes GitHub refuse the merge if the branch moved
# after review. Merge commit, as the earlier PRs did. Nothing else is changed.
source "$(dirname "$0")/common.sh"
refuse_agent
PR=139
HEAD_REVIEWED="${1:?usage: $0 <40-hex head of chore/agentteams-1.1.0-rc.15, with both signed rows>}"
[[ "$HEAD_REVIEWED" =~ ^[0-9a-f]{40}$ ]] || die "the head must be a full 40-hex SHA"
BR="chore/agentteams-1.1.0-rc.15"
RT_URL="https://github.com/$REPO"

read -r state head ref mstate < <(gh pr view "$PR" -R "$REPO" --json state,headRefOid,headRefName,mergeStateStatus \
  -q '"\(.state) \(.headRefOid) \(.headRefName) \(.mergeStateStatus)"')
[ "$state" = OPEN ] || die "PR #$PR is $state, not OPEN"
[ "$ref" = "$BR" ] || die "PR #$PR head branch is $ref, not $BR"
[ "$head" = "$HEAD_REVIEWED" ] || die "PR #$PR head is $head, not the reviewed $HEAD_REVIEWED"
[ "$mstate" = CLEAN ] || die "PR #$PR merge state is $mstate (need CLEAN: checks green, no conflicts)"
# Both signed rows and the verified pin must be in the tree being merged.
ngit -C "$MAIN" fetch -q "$RT_URL" "refs/heads/$BR"
for a in s10-cooldown-exempt:jlcatonjr/agentteams pin-agentteams-v1.1.0-rc.15; do
  ngit -C "$MAIN" show "$HEAD_REVIEWED:.github/agents/references/security-decisions.log.csv" \
    | grep -qF ",$a,PASS," || die "no signed $a row at $HEAD_REVIEWED"
done
ngit -C "$MAIN" show "$HEAD_REVIEWED:toolchain.lock" | grep -qx 'agentteams=jlcatonjr/agentteams@9900fbd3cee54d977f045b5ca0406ac5379ac541' \
  || die "toolchain.lock at $HEAD_REVIEWED does not pin the verified rc.15 commit 9900fbd3"

say "PR #$PR ($BR) at ${HEAD_REVIEWED:0:12}: open, checks green, both signed rows present, rc.15 pinned"
gh pr view "$PR" -R "$REPO" --json title -q .title
confirm "Merge PR #$PR into main (merge commit)?"
gh pr merge "$PR" -R "$REPO" --merge --match-head-commit "$HEAD_REVIEWED"

MERGED="$(gh pr view "$PR" -R "$REPO" --json state,mergeCommit -q 'select(.state=="MERGED") | .mergeCommit.oid')"
[[ "$MERGED" =~ ^[0-9a-f]{40}$ ]] || die "PR #$PR did not report a merge commit"
say "Merged PR #$PR -> main $MERGED"
echo "Tell the researchteam session it is merged. Next: cut researchteam v1.1.0-rc.4."
