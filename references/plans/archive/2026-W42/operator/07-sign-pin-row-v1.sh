#!/bin/bash -p
# 07 — Sign the operator @security row pin-agentteams-v1.0.0 into the v1.0.0 release-prep worktree. OPERATOR ONLY.
# Usage (plain Terminal; ALWAYS `/bin/bash -p <absolute path>`, never `bash <path>`):
#   /bin/bash -p ~/githubrepositories/researchteam/tmp/by-week/2026-W42/operator/07-sign-pin-row-v1.sh <40-hex reviewed branch head>
# It checks that the worktree is on release-prep/1.0.0 at the reviewed head with a clean tree, that the
# decision spec says exactly what was reviewed (scope, tag object, peeled commit), signs it with the op-2026 key via
# the root-owned signer (as 02 did for rc.12–rc.14), and checks the row clears agentteams' security gate. It COMMITS
# NOTHING: the researchteam session commits the signed row and pushes the PR, so the signature is the only operator
# output. Hardening as in 08 / agentteams-runner-ops/tag-release.sh (privileged mode, checked env -i re-exec,
# neutralised git, absolute paths).
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

WT="$HOME/githubrepositories/researchteam-wt-v1"
BR="release-prep/1.0.0"
SPEC="docs/release/pin-agentteams-v1.0.0.decision-spec.json"
TEAM=".github/agents"
ACTION="pin-agentteams-v1.0.0"
AT_OBJ="5b0ac7746dc49106f074d1cc1e24d2aa8f506773"; AT_PEELED="cc5b8c9ec4efdcb479939e0c1246a0ac11913259"
SIGNER="<signer>"     # root-owned (01b); agentteams refuses a signer under $HOME
KEYFILE="<decision-key-file>"
HEAD_REVIEWED="${1:?usage: $0 <40-hex reviewed head of $BR>}"
[[ "$HEAD_REVIEWED" =~ ^[0-9a-f]{40}$ ]] || die "the head must be a full 40-hex SHA"
[[ -x "$SIGNER" ]] || die "no root-owned signer at $SIGNER (01b)"
[[ "$(/usr/bin/stat -f %Su "$SIGNER")" == root ]] || die "$SIGNER is not root-owned"
[[ -f "$KEYFILE" ]] || die "missing $KEYFILE"
[[ -d "$WT" ]] || die "no worktree at $WT"

cd "$WT"
[[ "$("${GIT[@]}" rev-parse --abbrev-ref HEAD)" == "$BR" ]] || die "$WT is not on $BR"
[[ "$("${GIT[@]}" rev-parse HEAD)" == "$HEAD_REVIEWED" ]] || die "$BR is at $("${GIT[@]}" rev-parse HEAD), not the reviewed $HEAD_REVIEWED"
[[ -z "$("${GIT[@]}" status --porcelain)" ]] || die "$WT has uncommitted changes; stop"
# Sign a private copy of the spec AS COMMITTED at the reviewed head (never the live worktree file, which could change
# between the check and the signature), and check that copy.
TMP=$(/usr/bin/mktemp -d); trap 'rm -rf "$TMP"' EXIT
"${GIT[@]}" show "$HEAD_REVIEWED:$SPEC" > "$TMP/spec.json" || die "no $SPEC at $HEAD_REVIEWED"
/usr/bin/grep -qF "\"action_reviewed\": \"$ACTION\"" "$TMP/spec.json" || die "the spec is not for $ACTION"
/usr/bin/grep -qF "\"scope\": \"$ACTION\"" "$TMP/spec.json" || die "the spec scope is not $ACTION"
/usr/bin/grep -qF "$AT_OBJ" "$TMP/spec.json" && /usr/bin/grep -qF "$AT_PEELED" "$TMP/spec.json" \
  || die "the spec does not name tag object $AT_OBJ and peeled $AT_PEELED"
log="$TEAM/references/security-decisions.log.csv"
/usr/bin/grep -qF ",$ACTION,PASS," "$log" && die "$log already has a $ACTION row"

echo "== $SPEC at ${HEAD_REVIEWED:0:12}"; /bin/cat "$TMP/spec.json"
read -r -p "Sign $ACTION into $TEAM with key op-2026? [y/N] " ok
[[ "$ok" == "y" ]] || { echo "stopped; nothing was signed"; exit 0; }
(cd "$TMP" && AGENTTEAMS_DECISION_ED25519_KEYFILE="$KEYFILE" "$SIGNER" --sign-decision "$TMP/spec.json" --output "$WT/$TEAM")

echo "== the row must clear agentteams' security gate"
(cd "$TMP" && "${SIGNER%/agentteams}/python" -I - "$WT/$TEAM" "$ACTION") <<'PY' || die "the signed row does not clear the gate (tell the researchteam session; do not commit)"
import sys
from pathlib import Path
from agentteams.cli.security_gate import check_clearance
ok, why = check_clearance(Path(sys.argv[1]), action=sys.argv[2])
print(f"  {sys.argv[2]}: {'clears' if ok else 'REFUSED: ' + str(why)[:200]}")
sys.exit(0 if ok else 1)
PY
"${GIT[@]}" --no-pager diff --stat
echo "Signed. Tell the researchteam session: it commits the row on $BR and pushes. Nothing was committed here."
else
  printf 'STOP: run as /bin/bash -p %s (privileged mode); nothing was done.\n' "$0" >&2
fi
