#!/usr/bin/env bash
# 17 — Delete remote branches already merged into main (operator instruction, 2026-11-19: handle the listed
# leftovers; same procedure as 10-delete-merged-branches.sh, after a @security --branch-cleanup review).
# OPERATOR ONLY, plain Terminal, from any directory:
#   bash <checkout>/tmp/by-week/2026-W47/operator/17-delete-merged-branches.sh
# Each listed branch is deleted only if, at the moment of deletion, it is still at the listed commit
# (--force-with-lease), that commit is an ancestor of origin/main, and no open PR has it as head. Never touches main,
# release/**, archive/** or chore/agentteams-autosync. Lists everything and asks once before deleting.
source "$(dirname "$0")/common.sh"
refuse_agent
RT_URL="https://github.com/$REPO"
cd "$MAIN"
# branch  commit-at-review (40 hex)
BRANCHES=(
  "docs/213-pin-record-unsigned-workspaces 955e1aa7f63a356ead99dca0b28756453f2ce130"
  "docs/bibliography-explorer-closeout 01af87f0bc9878bd51d608e636a11b61d451adf0"
  "docs/pin-record-and-rule8-notes ab1510454b95bc3cbf2538ab44b3cc618a4adf00"
  "docs/ps2-merge-approval 7d57edba9d789392e8f9a71b8b04802af4112bf8"
  "docs/term-index-decision 43dad94cda81a655b9fb51346e358e7ab04e9cc6"
  "docs/term-index-placement-note b2c35b4c26aa74208d887bfe49cb11ba46a97363"
  "docs/term-index-switch-1.3 fb7250f771d9d215e7fd3516dbbfff2d44979ea6"
  "docs/v1.2.0-closeout ed550bf5e56fb1015e44cca6d95c17bf6b749e06"
  "feat/bibliography-explorer 2ef5c5799bb1f8269679deed9bfd4d2666ce1d86"
  "feat/term-index 144799e435f2914afc87ba2722f73e7bb2164287"
  "feat/term-index-followups c74f90c4eb8c4c4a140de7510ba1cb9d47d50f46"
  "fix/182-autosync-job-split 08275ebc001879204f7df2b1e52afb1f62e1cc31"
  "fix/182-open-pr-branch-checkout d9f7f23c9c3097df0c7ddf71b30888bde8718fbe"
  "fix/205-autosync-hardening a6c96d2250e6b958c2531d7eb5489a9c02413686"
  "pin/agentteams-v1.2.1 418a70769f6c8a36e363e4caad23832632fdaa89"
  "records/182-autosync-job-split 280bbf843bf50b0358261c2abc576b56f1f7cda8"
  "records/branch-cleanup 8ecfb7d3893a3117f9810bc99e77e7984fce1691"
  "records/term-index-2026-11-16 3979d6c7d5dfe498dfafe19361d9c299fa1e5553"
  "records/term-index-followups d6b5db30c5b4b8fa4c08d4c11e6679f736dcaebf"
  "records/v1.1.7-cut 8ce119abbd656159844e541b4f5a917df342cc83"
  "records/v1.1.8-cut 194ab6809277313553fb2d4d6c1c1ff96982e0a6"
  "records/v1.1.9-cut 52e71fa98ea03d700d3a115617909c7ec1337841"
  "release-prep/v1.1.7 e640e4fcfb3ab2084232b723967503549384106a"
  "release-prep/v1.1.8 d8a70529d0b8245e0f2daefe520c70d76d34b70b"
  "release-prep/v1.1.9 17286b718d2c564f6e5d877b3ad3d817957e50f9"
  "release-prep/v1.2.0 c5f7189372a41eac74134ec3ddfd13698f963eb3"
  "release-prep/v1.2.0-rc.1 f425680b8116e6772b9f0e90065b2c175bb6153c"
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
