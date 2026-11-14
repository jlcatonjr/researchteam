#!/usr/bin/env bash
# 13 — Merge researchteam PR #144 (release-prep/1.0.4 -> release/1.0: agentteams v1.0.7 pin, S-10 restored with the
# local-repo carve-out, pip pin, 1.0.4 CHANGELOG) once the signed pin-agentteams-v1.0.7 row is committed on it.
# Modelled on 10-merge-pr143.sh. OPERATOR ONLY, plain Terminal, AFTER 12:
#   bash ~/githubrepositories/researchteam/tmp/by-week/2026-W45/operator/13-merge-pr144.sh <40-hex head the session reports>
# Refuses unless the PR's base is release/1.0, the head carries the signed rows, and it pins the verified v1.0.7 commit.
# --match-head-commit makes GitHub refuse the merge if the branch moved after review. Merge commit, as 1.0.3 (#126) was.
source "$(dirname "$0")/common.sh"
refuse_agent
PR=144
HEAD_REVIEWED="${1:?usage: $0 <40-hex head of release-prep/1.0.4, with the signed row>}"
[[ "$HEAD_REVIEWED" =~ ^[0-9a-f]{40}$ ]] || die "the head must be a full 40-hex SHA"
BR="release-prep/1.0.4"; BASE="release/1.0"
RT_URL="https://github.com/$REPO"

read -r state head ref base mstate < <(gh pr view "$PR" -R "$REPO" --json state,headRefOid,headRefName,baseRefName,mergeStateStatus \
  -q '"\(.state) \(.headRefOid) \(.headRefName) \(.baseRefName) \(.mergeStateStatus)"')
[ "$state" = OPEN ] || die "PR #$PR is $state, not OPEN"
[ "$ref" = "$BR" ] || die "PR #$PR head branch is $ref, not $BR"
[ "$base" = "$BASE" ] || die "PR #$PR base is $base, not $BASE"
[ "$head" = "$HEAD_REVIEWED" ] || die "PR #$PR head is $head, not the reviewed $HEAD_REVIEWED"
[ "$mstate" = CLEAN ] || die "PR #$PR merge state is $mstate (need CLEAN: checks green, no conflicts)"
# The signed rows and the verified pin must be in the tree being merged.
ngit -C "$MAIN" fetch -q "$RT_URL" "refs/heads/$BR"
for a in release-policy-1.0 s10-release-cooldown-restored s10-cooldown-exempt:jlcatonjr/agentteams pin-agentteams-v1.0.7; do
  ngit -C "$MAIN" show "$HEAD_REVIEWED:.github/agents/references/security-decisions.log.csv" \
    | grep -F ",$a,PASS," >/dev/null || die "no signed $a row at $HEAD_REVIEWED"
done
ngit -C "$MAIN" show "$HEAD_REVIEWED:toolchain.lock" | grep -x 'agentteams=jlcatonjr/agentteams@8b934600b554d14c1bd02adebe519a4999473c13' >/dev/null \
  || die "toolchain.lock at $HEAD_REVIEWED does not pin the verified v1.0.7 commit 8b934600"

say "PR #$PR ($BR -> $BASE) at ${HEAD_REVIEWED:0:12}: open, checks green, signed rows present, v1.0.7 pinned"
gh pr view "$PR" -R "$REPO" --json title -q .title
confirm "Merge PR #$PR into $BASE (merge commit)?"
gh pr merge "$PR" -R "$REPO" --merge --match-head-commit "$HEAD_REVIEWED"

MERGED="$(gh pr view "$PR" -R "$REPO" --json state,mergeCommit -q 'select(.state=="MERGED") | .mergeCommit.oid')"
[[ "$MERGED" =~ ^[0-9a-f]{40}$ ]] || die "PR #$PR did not report a merge commit"
say "Merged PR #$PR -> $BASE $MERGED"
echo "Tell the researchteam session it is merged. Next: 14-cut-v1.0.4.sh with the merge commit above."
