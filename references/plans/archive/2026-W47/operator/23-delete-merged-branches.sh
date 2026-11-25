#!/usr/bin/env bash
# 23 — Delete remote branches already merged into main (plan P3 step 4, 2026-11-20: the heads of pull requests
# merged before the automatic-deletion setting was on; same procedure as 17-delete-merged-branches.sh, after a
# @security --branch-cleanup review). Left off on purpose: the four docs/survey-toolkit-* branches (operator
# answer, 2026-11-20) and feat/explorer-contract-1.1 (another session's branch and worktree).
# OPERATOR ONLY, plain Terminal, from any directory:
#   bash <checkout>/tmp/by-week/2026-W47/operator/23-delete-merged-branches.sh
# Each listed branch is deleted only if, at the moment of deletion, it is still at the listed commit
# (--force-with-lease), that commit is an ancestor of origin/main, and no open PR has it as head. Never touches main,
# release/**, archive/** or chore/agentteams-autosync. Lists everything and asks once before deleting.
source "$(dirname "$0")/common.sh"
refuse_agent
RT_URL="https://github.com/$REPO"
cd "$MAIN"
# branch  commit-at-review (40 hex)
BRANCHES=(
  "docs/release-policy-tag-checks 45003ced9ef1de44688ee8e87c03680ffe0618bf"
  "fix/verify-tag-shallow-fetch 0a37b1afaf4d386ee071a19849cb5ac4ea966e74"
  "governance/ps2-auto-branch-delete 52d0b78c738f8690f89f50fe40e120584586d3b1"
  "plans/open-items-2026-11-19 73d6174c12da3a28f9b03f7fc7ac509db7d82fa8"
  "records/open-items-2026-11-20 0603b57bf2465a84cbef643387f0d5fa25c12465"
  "records/post-1.2-housekeeping ac9f8e280204eedcdb861113efbce39148024978"
  "records/v1.2.1-cut d5c8940e163eaf404af7a7c6da40d874f025c76b"
  "release-prep/v1.2.1 48776227bc5a2a6a63fad3cb3157389654c7f579"
  "test/update-native-surfaces-offline 8542e2b2439c5a9fe43a11609744ec7b088d627b"
  "tests/term-index-characterization ff8ab84be39d8fcf6db161df4a28d3e7034a5e78"
)
ngit fetch -q "$RT_URL" "+refs/heads/main:refs/remotes/origin/main"
open_heads="$(gh pr list -R "$REPO" --state open --limit 200 --json headRefName -q '.[].headRefName')" \
  || die "cannot list open PRs; nothing deleted"
todo=()
for entry in "${BRANCHES[@]}"; do
  b="${entry% *}"; sha="${entry#* }"
  case "$b" in main|release/*|archive/*|chore/agentteams-autosync) die "refusing protected branch $b" ;; esac
  now="$(ngit ls-remote "$RT_URL" "refs/heads/$b" | cut -f1)"
  if [ -z "$now" ]; then echo "  gone already: $b"; continue; fi
  if [ "$now" != "$sha" ]; then echo "  SKIP $b: moved to ${now:0:12} since review (${sha:0:12})"; continue; fi
  if printf '%s\n' "$open_heads" | grep -qxF "$b"; then echo "  SKIP $b: head of an open PR"; continue; fi
  ngit cat-file -e "$sha^{commit}" 2>/dev/null || ngit fetch -q "$RT_URL" "$sha" 2>/dev/null || true
  if ! ngit merge-base --is-ancestor "$sha" refs/remotes/origin/main; then echo "  SKIP $b: not merged into main"; continue; fi
  todo+=("$b $sha")
done
[ "${#todo[@]}" -gt 0 ] || { say "Nothing to delete."; exit 0; }
say "${#todo[@]} merged branch(es) to delete from $REPO:"
for e in "${todo[@]}"; do echo "  ${e% *}  (${e#* })"; done
confirm "Delete these ${#todo[@]} remote branches?"
deleted=0
for e in "${todo[@]}"; do
  b="${e% *}"; sha="${e#* }"
  if git -c core.hooksPath=/dev/null push --quiet --force-with-lease="refs/heads/$b:$sha" "$RT_URL" ":refs/heads/$b"; then
    deleted=$((deleted + 1)); echo "  deleted $b"
  else
    echo "  FAILED $b (moved or protected); left in place"
  fi
done
say "Deleted $deleted of ${#todo[@]}. Tell the researchteam session."
