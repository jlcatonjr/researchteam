#!/usr/bin/env bash
# 21 — P3 option A, step 2 of 2 for the operator: turn ON the repository setting "Automatically delete head branches"
# (delete_branch_on_merge) for jlcatonjr/researchteam, and read it back.
# Run it only AFTER the PS-2 amendment PR has merged: the script checks that origin/main carries the amendment, the
# signed decision row and its active registry entry, and refuses otherwise.
# From then on GitHub deletes a pull request's head branch when it merges. No deletion record is written and no hold
# check runs (PS-2, "Exception: automatic head-branch deletion"). Turn it off with 22-disable-delete-branch-on-merge.sh
# at the sunset (2027-02-18) or at once on a HALT on branch-delete, the repo-setting family or the decision.
# OPERATOR ONLY, plain Terminal, from any directory:
#   bash ~/githubrepositories/researchteam/tmp/by-week/2026-W47/operator/21-enable-delete-branch-on-merge.sh
source "$(dirname "$0")/common.sh"
refuse_agent
GH_LOGIN="jlcatonjr"
ACTION="repo-setting:delete-branch-on-merge:jlcatonjr/researchteam"
LOG=".github/agents/references/security-decisions.log.csv"
REG=".github/agents/references/exception-registry.json"
[ "$(gh api user -q .login)" = "$GH_LOGIN" ] || die "gh is not signed in as $GH_LOGIN"
ngit -C "$MAIN" fetch -q origin main || die "cannot fetch origin/main"
tip="$(ngit -C "$MAIN" rev-parse origin/main)"
ngit -C "$MAIN" show "$tip:.claude/CLAUDE.md" | grep -qF "$ACTION" || die "origin/main ($tip) has no PS-2 amendment naming $ACTION; merge the PR first"
ngit -C "$MAIN" show "$tip:$LOG" | grep -qF ",$ACTION,PASS," || die "origin/main ($tip) has no signed PASS row for $ACTION"
ngit -C "$MAIN" show "$tip:$REG" | python3 -c '
import json, sys
from datetime import datetime, timezone
action = sys.argv[1]
live = [e for e in json.load(sys.stdin).get("exceptions", []) if e.get("action") == action and e.get("status") == "active"]
ok = len(live) == 1 and datetime.fromisoformat(live[0]["expires"]) > datetime.now(timezone.utc)
print("  registry entry:", live[0]["id"] if live else None, "| expires:", live[0]["expires"] if live else None)
sys.exit(0 if ok else 1)' "$ACTION" || die "origin/main ($tip) has no active, unexpired registry entry for $ACTION"
if ngit -C "$MAIN" show "$tip:$LOG" | grep -E ',(branch-delete|repo-setting)[^,]*,HALT,' >/dev/null; then die "a HALT on branch-delete or repo-setting is recorded on origin/main; do not turn the setting on"; fi
now="$(gh api "repos/$REPO" -q .delete_branch_on_merge)"
say "Repository $REPO: delete_branch_on_merge is currently $now (origin/main $tip)"
if [ "$now" = "true" ]; then echo "Already on. Nothing to do."; exit 0; fi
confirm "Turn ON automatic deletion of merged pull-request head branches for $REPO?"
gh api -X PATCH "repos/$REPO" -F delete_branch_on_merge=true -q .delete_branch_on_merge >/dev/null || die "the setting change was refused"
after="$(gh api "repos/$REPO" -q .delete_branch_on_merge)"
[ "$after" = "true" ] || die "read back delete_branch_on_merge=$after, expected true"
say "Done. Read back: delete_branch_on_merge=$after on $REPO."
echo "Tell the researchteam session the read-back line above."
