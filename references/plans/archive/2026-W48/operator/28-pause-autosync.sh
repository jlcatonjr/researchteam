#!/bin/bash
# 28 — Pause or resume the AgentTeams Autosync workflow of jlcatonjr/researchteam for the 1.3.0 freeze
# (operator ruling, 2026-11-24: paused from the freeze to the final). It changes one thing: whether the workflow
# agentteams-sync.yml is enabled. No file, branch, tag, ruleset, secret or key is touched.
#
# Why: from the freeze to the final, an upstream agentteams patch release would move toolchain.lock but not the
# copied term-index core, and the core comparison would then fail on the autosync's pull request.
#
# OPERATOR ONLY, plain Terminal, from any directory:
#   /bin/bash <this file> pause      disables the workflow, then reads its state back
#   /bin/bash <this file> resume     enables it again (after v1.3.0 is final), then reads its state back
#   /bin/bash <this file> status     reads the state only
# Enabling or disabling a workflow is a repository setting, so the agent session does not do it (PS-2).
set -euo pipefail
export PATH=/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/usr/local/bin
die() { printf 'STOP: %s\n' "$*" >&2; exit 1; }
[[ -z "${CLAUDECODE:-}${CLAUDE_CODE_ENTRYPOINT:-}${CODEX_SANDBOX:-}" ]] || die "run this in your own terminal, not an agent session"
REPO=jlcatonjr/researchteam
WF=agentteams-sync.yml
[[ $# -eq 1 ]] || die "usage: /bin/bash $0 pause|resume|status"
command -v gh >/dev/null || die "gh is not on PATH"
state() { gh api "repos/$REPO/actions/workflows/$WF" --jq '.name + ": " + .state'; }
printf 'before: %s\n' "$(state)"
case "$1" in
  pause)  gh workflow disable "$WF" -R "$REPO" ;;
  resume) gh workflow enable "$WF" -R "$REPO" ;;
  status) ;;
  *) die "usage: /bin/bash $0 pause|resume|status" ;;
esac
printf 'after:  %s\n' "$(state)"
case "$1" in
  pause)  [[ "$(state)" == *": disabled_manually" ]] || die "the workflow is not disabled; paste this output into the researchteam session" ;;
  resume) [[ "$(state)" == *": active" ]] || die "the workflow is not active; paste this output into the researchteam session" ;;
esac
printf '== done (%s). Paste this output into the researchteam session.\n' "$1"
