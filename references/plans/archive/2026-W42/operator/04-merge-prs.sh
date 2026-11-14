#!/usr/bin/env bash
# 04 — Merge the Phase R PRs in order, each pinned to its reviewed head SHA (--match-head-commit):
#   signing PR (02) -> #56 -> #57 version from git -> 4.3 experts PR -> #49 pin -> #52 release lock (retargets to main)
#   -> the rc.11 render PR (opened by the researchteam session after 02)
# then rebuild #53 (1.0.0rc1) as its single bump commit on the new main, and merge it.
# #51, #50, #54 and #55 are already merged and are skipped.
# Each merge shows the PR, its checks and head SHA, and asks before merging. Re-runnable: merged PRs are skipped.
source "$(dirname "$0")/common.sh"
refuse_agent
# `04-merge-prs.sh early` merges only #51 and #50, which are independent of the agentteams pin and can land
# before rc.11. #52 is stacked on #49, so it waits for the rc.11 pin like #49 does.
if [ "${1:-}" = early ]; then
  EARLY=1; shift
else
  EARLY=0; need_rc11
fi
SIGN_PR="${1:-$(state_get SIGN_PR)}"
RENDER_PR="${2:-$(state_get RENDER_PR)}"

merge_pr() {
  local n="$1" st sha base
  st="$(gh pr view "$n" -R "$REPO" --json state -q .state)"
  [ "$st" = MERGED ] && { echo "#$n already merged"; return; }
  [ "$st" = OPEN ] || die "#$n is $st"
  for _ in $(seq 1 30); do
    m="$(gh pr view "$n" -R "$REPO" --json mergeable -q .mergeable)"; [ "$m" != UNKNOWN ] && break; sleep 5
  done
  [ "$m" = MERGEABLE ] || die "#$n is $m (conflicts?) — ask the researchteam session to rebase it"
  sha="$(gh pr view "$n" -R "$REPO" --json headRefOid -q .headRefOid)"
  base="$(gh pr view "$n" -R "$REPO" --json baseRefName -q .baseRefName)"
  say "#$n  $(gh pr view "$n" -R "$REPO" --json title -q .title)"
  echo "head $sha -> base $base"
  gh pr checks "$n" -R "$REPO" || echo "(checks above: failing or pending — look before you merge)"
  confirm "Merge #$n at $sha?"
  [ "$(gh pr view "$n" -R "$REPO" --json isDraft -q .isDraft)" = true ] && gh pr ready "$n" -R "$REPO"
  gh pr merge "$n" -R "$REPO" --merge --match-head-commit "$sha" --delete-branch
}

if [ "$EARLY" -eq 1 ]; then
  merge_pr 51
  merge_pr 50
  echo "Early merges done. The rest waits for agentteams $AT_TAG."; exit 0
fi
[ -n "$SIGN_PR" ] || die "no signing PR number (run 02, or pass it as the first argument)"
[ -n "$RENDER_PR" ] || die "no rc.11 render PR yet: after 02, ask the researchteam session to render (or pass it as the second argument)"
merge_pr "$SIGN_PR"
merge_pr 51
merge_pr 50
merge_pr 56
merge_pr 57                       # version from git tags (setuptools-scm)
EXPERTS_PR="$(state_get EXPERTS_PR)"; [ -n "$EXPERTS_PR" ] || die "no masterTeacher 4.3 PR recorded yet (ask the researchteam session)"
merge_pr "$EXPERTS_PR"            # expert handles from the brief (masterTeacher 4.3)
merge_pr 49
# #52 was stacked on #49's branch; GitHub retargets it to main when that branch is deleted.
[ "$(gh pr view 52 -R "$REPO" --json baseRefName -q .baseRefName)" = main ] || gh pr edit 52 -R "$REPO" --base main
merge_pr 52
merge_pr "$RENDER_PR"

say "Rebuilding #53 ($RC1_BRANCH) as one bump commit on the new main"
git -C "$MAIN" fetch --quiet origin
TMPWT="$(mktemp -d)/rc1"
git -C "$MAIN" worktree add --quiet --detach "$TMPWT" origin/main
( cd "$TMPWT"
  git cherry-pick "$RC1_BUMP_COMMIT" >/dev/null
  grep -q '^## 1.0.0rc1' CHANGELOG.md || die "the rc.1 CHANGELOG commit did not apply"
  python3 -m pytest -q 2>&1 | tail -1
  git push --quiet --force-with-lease="$RC1_BRANCH" origin "HEAD:refs/heads/$RC1_BRANCH" )
git -C "$MAIN" worktree remove --force "$TMPWT"
gh pr ready 53 -R "$REPO" || true
echo "waiting for #53's checks…"; gh pr checks 53 -R "$REPO" --watch || true
merge_pr 53
echo "All merged. Next: 05-cut-and-sign-rc1.sh"
