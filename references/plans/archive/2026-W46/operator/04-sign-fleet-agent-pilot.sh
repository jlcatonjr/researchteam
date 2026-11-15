#!/bin/bash -p
# 04 — Sign researchteam's fleet-agent-pilot-2026-11 row (CONDITIONAL PASS, conditions pending) into the
# docs/fleet-agent-pilot-decision worktree. OPERATOR ONLY. Same hardened preamble as 2026-W45/16-sign-v110-pin.sh.
# The row records researchteam's conditional agreement to the fleet-agent GitHub App pilot. While its conditions
# are pending it clears nothing; the gate check below expects exactly that refusal.
# Usage (plain Terminal, from any directory; ALWAYS `/bin/bash -p <path>`, never `bash <path>`):
#   /bin/bash -p ~/githubrepositories/researchteam/tmp/by-week/2026-W46/operator/04-sign-fleet-agent-pilot.sh <40-hex head the session reports>
# It COMMITS NOTHING: the researchteam session commits the row, pushes, opens the PR and merges it under PS-2.
if [[ $- == *p* ]]; then
builtin unset -f $(builtin compgen -A function) 2>/dev/null; builtin set -euo pipefail
[[ -z "${CLAUDECODE:-}" && -z "${CLAUDE_CODE_ENTRYPOINT:-}" ]] || { echo "error: run this from a plain Terminal, not an agent session" >&2; exit 1; }
env_is_clean() {
  local n
  [[ "${PATH:-}" == /usr/bin:/bin:/usr/sbin:/sbin ]] || return 1
  [[ -z "$(builtin declare -F | /usr/bin/grep -vx 'declare -f env_is_clean')" ]] || return 1
  while IFS= read -r n; do
    case "$n" in
      HOME|TERM|PATH|_RESEARCHTEAM_SIGN_ROW_CLEAN|GIT_CONFIG_GLOBAL|GIT_CONFIG_NOSYSTEM|PWD|SHLVL|OLDPWD|_) ;;
      *) return 1 ;;
    esac
  done < <(compgen -e)
  return 0
}
if ! env_is_clean; then
  [[ "${_RESEARCHTEAM_SIGN_ROW_CLEAN:-}" != 1 ]] || { builtin echo "error: the environment is not clean even after the env -i re-exec; stopping" >&2; builtin exit 1; }
  builtin exec /usr/bin/env -i _RESEARCHTEAM_SIGN_ROW_CLEAN=1 HOME="$HOME" TERM="${TERM:-dumb}" \
    PATH=/usr/bin:/bin:/usr/sbin:/sbin /bin/bash -p "$0" "$@"
fi
unset -f env_is_clean
for v in ${!GIT_@} ${!GH_@}; do unset "$v"; done
unset GITHUB_TOKEN DEVELOPER_DIR TOOLCHAINS SDKROOT
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null PATH=/usr/bin:/bin:/usr/sbin:/sbin
GIT=(/usr/bin/git -c core.hooksPath=/dev/null -c core.fsmonitor=false)
die() { echo "error: $*" >&2; exit 1; }

HEAD_REVIEWED="${1:?usage: $0 <40-hex reviewed head of docs/fleet-agent-pilot-decision>}"
WT="$HOME/githubrepositories/researchteam-wt-fleet-pilot"
ACTION="fleet-agent-pilot-2026-11"
BR="docs/fleet-agent-pilot-decision"
TEAM=".github/agents"
SIGNER="<signer>"     # root-owned install built from agentteams tag v1.1.3; agentteams refuses a signer under $HOME
KEYFILE="<decision-key-file>"
[[ "$HEAD_REVIEWED" =~ ^[0-9a-f]{40}$ ]] || die "the head must be a full 40-hex SHA"
[[ -x "$SIGNER" ]] || die "no root-owned signer at $SIGNER"
[[ "$(/usr/bin/stat -f %Su "$SIGNER")" == root ]] || die "$SIGNER is not root-owned"
[[ -f "$KEYFILE" ]] || die "missing $KEYFILE"
[[ -d "$WT" ]] || die "no worktree at $WT"

cd "$WT"
[[ "$("${GIT[@]}" rev-parse --abbrev-ref HEAD)" == "$BR" ]] || die "$WT is not on $BR"
[[ "$("${GIT[@]}" rev-parse HEAD)" == "$HEAD_REVIEWED" ]] || die "$BR is at $("${GIT[@]}" rev-parse HEAD), not the reviewed $HEAD_REVIEWED"
[[ -z "$("${GIT[@]}" status --porcelain)" ]] || die "$WT has uncommitted changes; stop"
log="$TEAM/references/security-decisions.log.csv"
TMP=$(/usr/bin/mktemp -d); trap 'rm -rf "$TMP"' EXIT
EMPTY="$TMP/empty"; /bin/mkdir "$EMPTY"   # signer and gate check run from an empty cwd; the keyfile variable is never exported
SPEC="docs/release/$ACTION.decision-spec.json"

echo; echo "== researchteam: $ACTION"
if /usr/bin/grep -qF ",$ACTION," "$log"; then echo "  already in $log; nothing to sign"; exit 0; fi
"${GIT[@]}" show "$HEAD_REVIEWED:$SPEC" > "$TMP/spec.json" 2>/dev/null || die "no $SPEC at the head"
/usr/bin/grep -qE '<[A-Z_]+>' "$TMP/spec.json" && die "$SPEC still has a placeholder"
/usr/bin/grep -qF "\"action_reviewed\": \"$ACTION\"" "$TMP/spec.json" || die "$SPEC is not for $ACTION"
/usr/bin/grep -qF "\"scope\": \"$ACTION\"" "$TMP/spec.json" || die "$SPEC scope is not $ACTION"
/usr/bin/grep -qF '"verdict": "CONDITIONAL PASS"' "$TMP/spec.json" || die "$SPEC verdict is not CONDITIONAL PASS"
/usr/bin/grep -qF '"conditions_verified": "pending"' "$TMP/spec.json" || die "$SPEC conditions_verified is not pending"
/usr/bin/grep -qF '"derives_from": "release-policy-1.0"' "$TMP/spec.json" || die "$SPEC does not derive from release-policy-1.0 alone"
/usr/bin/grep -qF ",release-policy-1.0,PASS," "$log" || die "release-policy-1.0 is not signed in $log"
/bin/cat "$TMP/spec.json"
read -r -p "Sign $ACTION (CONDITIONAL PASS, conditions pending) into $TEAM with key op-2026? [y/N] " ok
[[ "$ok" == "y" ]] || { echo "  not signed; nothing changed"; exit 0; }
n0=$(/usr/bin/wc -l < "$log")
(cd "$EMPTY" && AGENTTEAMS_DECISION_ED25519_KEYFILE="$KEYFILE" "$SIGNER" --sign-decision "$TMP/spec.json" --output "$WT/$TEAM")
n1=$(/usr/bin/wc -l < "$log")
echo "  log lines: before sign $n0, after sign $n1"
[[ $((n1 - n0)) -eq 1 ]] || die "the signer changed the log by $((n1 - n0)) lines (expected 1); stop, do not commit; tell the researchteam session"
# Expected gate result: REFUSED for unverified conditions, and for no other reason (a signature or lineage
# failure would give a different reason).
(cd "$EMPTY" && "${SIGNER%/agentteams}/python" -I -P - "$WT/$TEAM" "$ACTION") <<'PY' || die "unexpected gate result for $ACTION; do not commit; tell the researchteam session"
import sys
from pathlib import Path
from agentteams.cli.security_gate import check_clearance
ok, why = check_clearance(Path(sys.argv[1]), action=sys.argv[2], consume=False) if "consume" in check_clearance.__code__.co_varnames else check_clearance(Path(sys.argv[1]), action=sys.argv[2])
print(f"  {sys.argv[2]}: {'CLEARS (not expected while pending)' if ok else 'refused: ' + str(why)[:200]}")
sys.exit(0 if (not ok and "unverified conditions" in str(why)) else 1)
PY
n2=$(/usr/bin/wc -l < "$log")
[[ "$n2" -eq "$n1" ]] || die "the post-sign gate check changed the log ($n1 -> $n2 lines); stop, do not commit; tell the researchteam session"
"${GIT[@]}" --no-pager diff --stat
echo "Signed 1 row. Nothing was committed here. Tell the researchteam session: it commits the row on $BR,"
echo "pushes, opens the PR and merges it under PS-2."
else
  printf 'STOP: run as /bin/bash -p %s (privileged mode); nothing was done.\n' "$0" >&2
fi
