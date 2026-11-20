#!/usr/bin/env bash
# 22 — Turn OFF the repository setting "Automatically delete head branches" (delete_branch_on_merge) for
# jlcatonjr/researchteam, and read it back. Use it at the sunset of the decision
# repo-setting:delete-branch-on-merge:jlcatonjr/researchteam (2027-02-18), at once on a HALT on branch-delete, the
# repo-setting family or that decision, or whenever you want the setting off. It has no preconditions: turning the
# setting off only restores the stricter rule (PS-2: a signed branch-delete grant or a --branch-cleanup PASS).
# OPERATOR ONLY, plain Terminal, from any directory:
#   bash ~/githubrepositories/researchteam/tmp/by-week/2026-W47/operator/22-disable-delete-branch-on-merge.sh
source "$(dirname "$0")/common.sh"
refuse_agent
GH_LOGIN="jlcatonjr"
[ "$(gh api user -q .login)" = "$GH_LOGIN" ] || die "gh is not signed in as $GH_LOGIN"
now="$(gh api "repos/$REPO" -q .delete_branch_on_merge)"
say "Repository $REPO: delete_branch_on_merge is currently $now"
if [ "$now" = "false" ]; then echo "Already off. Nothing to do."; exit 0; fi
confirm "Turn OFF automatic deletion of merged pull-request head branches for $REPO?"
gh api -X PATCH "repos/$REPO" -F delete_branch_on_merge=false -q .delete_branch_on_merge >/dev/null || die "the setting change was refused"
after="$(gh api "repos/$REPO" -q .delete_branch_on_merge)"
[ "$after" = "false" ] || die "read back delete_branch_on_merge=$after, expected false"
say "Done. Read back: delete_branch_on_merge=$after on $REPO."
echo "Tell the researchteam session. It retires the registry entry in a reviewed change."
