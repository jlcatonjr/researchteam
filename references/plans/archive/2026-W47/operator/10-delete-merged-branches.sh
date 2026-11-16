#!/usr/bin/env bash
# 10 — Delete remote branches already merged into main (operator grant, 2026-11-16 picker: "Script, after @security").
# OPERATOR ONLY, plain Terminal, from any directory:
#   bash <checkout>/tmp/by-week/2026-W47/operator/10-delete-merged-branches.sh
# Each listed branch is deleted only if, at the moment of deletion, it is still at the listed commit
# (--force-with-lease), that commit is an ancestor of origin/main, and no open PR has it as head. Never touches main,
# release/**, archive/** or chore/agentteams-autosync. Lists everything and asks once before deleting.
source "$(dirname "$0")/common.sh"
refuse_agent
RT_URL="https://github.com/$REPO"
cd "$MAIN"
# branch  commit-at-review (40 hex)
BRANCHES=(
  "chore/agentteams-v1.1.1 65f56044d928fe70fa99acc043aae0c38ae89cdf"
  "chore/build-system-revet-2026-11-14 4bd7130e85c5ef7dc130ad29814730f3dc55c030"
  "docs/fleet-agent-pilot-decision c81d5df1cfc30b1043a6e140612de37dff3e0280"
  "docs/hidden-material-2026-11-14 274f8d8e4487cc93dd60ac01db19f1f948ddea09"
  "docs/open-items-plans-2026-11-14 e42a03675407dbb1d09c6430e344eea27c0d2675"
  "docs/pin-v1.1.1-effect-targets fa3ed3b279f7933f4778b6f379808fe45a11a871"
  "docs/ps2-repo-management-delegation 1277786ff8809c9c19826935493caefd60bb4e0e"
  "docs/ps3-operator-interface 1e008cd3b4c82a0c9e8f8a7eed2cabb600c2540e"
  "docs/public-session-record-2026-11-14 2494458c6ff804bbf390561ba58d14aa359c6ab7"
  "docs/scaffold-copy-keeps-schedule ac0b910be46618d2927cde0185b78b6fc7fb8355"
  "docs/session-close-2026-11-14 ef77cc9953133027fa107bbd9f6571fe8f9f1084"
  "docs/work-summary-2026-11-14-close 6fb7c8c9b3fda7339f7fe70d76e9b890158d4389"
  "docs/work-summary-2026-11-14-rt47 07e6260f8123d5bd909139e1b9730cc355725852"
  "fix/186-schedule-off-by-default 2542f13880fca650f46edcdb1ede37a069ad29b0"
  "fix/autosync-gate-signing-deps 4a62526642612ed47d32df4f0b0e1355d596708b"
  "fix/autosync-install-pinning 06631c639889a74276e053c465a01f9dc20866d9"
  "fix/autosync-readonly-lookup e574938e0f2d0d7f0a6432ff2ca0a20804c623e9"
  "fix/autosync-stranded-branch d78a26a53684043f0e5d0181cbbad6d81148a952"
  "fix/p5-python-m-entry 6a64c2488070e996e6a84f8aa029309edca704e6"
  "fix/update-unfenced-append 05dd6e1adbb980c4cc9e1547a8b8ff30283fe326"
  "records/fix-179 46e477fa656c87e23bc6e3b349591bc0fbc6d6b1"
  "records/fix-186 bec018afe1cd6cf42e89b678b871f233996c11ba"
  "records/v1.1.5-cut a11df7ce9af9ed6cacb8afbc3e9defca906a4292"
  "records/v1.1.6-cut 0d61246d4fa990c8c2a02d825682cd49c1716b85"
  "release-prep/v1.1.2 51cf028b25af6eb381f541d1b15e2b05703bb180"
  "release-prep/v1.1.4 912f9dbd568f18fb2dda735b5923c1810660360e"
  "release-prep/v1.1.5 ce31d837ddd7d35f471a835f66c3df8915366421"
  "release-prep/v1.1.6 a1876a5af8b18b6f4d95a9954e2a2f3aa267fea7"
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
