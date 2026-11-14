#!/bin/bash -p
# 02 — Sign researchteam's s10-release-cooldown-restored row (operator ruling 2026-11-03) into the
# docs/s10-cooldown-restored worktree (PR #138). OPERATOR ONLY. Modelled on 2026-W44/operator/15-sign-pin-rc11.sh.
# Usage (plain Terminal; ALWAYS `/bin/bash -p <absolute path>`, never `bash <path>`):
#   /bin/bash -p ~/githubrepositories/researchteam/tmp/by-week/2026-W45/operator/02-sign-s10-restored.sh 2b7852e0c43068e352f342ce2026596cf486ea90
# Same hardened checks as 15 (clean env re-exec; parents signed first; exactly one log line per row; the row clears
# agentteams' gate). No tag is verified: this row is a policy ruling, not a pin. It COMMITS NOTHING: the researchteam
# session commits the row on docs/s10-cooldown-restored and pushes, then hands you 03.
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

HEAD_REVIEWED="${1:?usage: $0 <40-hex reviewed head of docs/s10-cooldown-restored>}"
REPO="researchteam"
WT="$HOME/githubrepositories/researchteam-rc14"
ACTIONS=(s10-release-cooldown-restored)
BR="docs/s10-cooldown-restored"
TEAM=".github/agents"
SIGNER="<signer>"     # root-owned (2026-W42/01b); agentteams refuses a signer under $HOME
KEYFILE="<decision-key-file>"
[[ "$HEAD_REVIEWED" =~ ^[0-9a-f]{40}$ ]] || die "the head must be a full 40-hex SHA"
[[ -x "$SIGNER" ]] || die "no root-owned signer at $SIGNER (2026-W42/01b)"
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

echo "== Review first: the policy diff this row clears ($BR vs its merge base with main)"
"${GIT[@]}" --no-pager diff "$("${GIT[@]}" merge-base HEAD origin/main)" HEAD -- docs/release-policy.md
read -r -p "Is this the ruling you made on 2026-11-03? [y/N] " ok
[[ "$ok" == "y" ]] || die "stopped by operator"

signed=0
for ACTION in "${ACTIONS[@]}"; do
  SPEC="docs/release/$ACTION.decision-spec.json"
  echo; echo "== $REPO: $ACTION"
  if /usr/bin/grep -qF ",$ACTION,PASS," "$log"; then echo "  already in $log; skipped"; continue; fi
  "${GIT[@]}" show "$HEAD_REVIEWED:$SPEC" > "$TMP/$ACTION.json" 2>/dev/null || die "no $SPEC at the head"
  /usr/bin/grep -qE '<[A-Z_]+>' "$TMP/$ACTION.json" && die "$SPEC still has a placeholder"
  /usr/bin/grep -qF "\"action_reviewed\": \"$ACTION\"" "$TMP/$ACTION.json" || die "$SPEC is not for $ACTION"
  /usr/bin/grep -qF "\"scope\": \"$ACTION\"" "$TMP/$ACTION.json" || die "$SPEC scope is not $ACTION"
  # Every parent the spec derives from must already be a signed PASS row in this repo's log.
  parents="$(/usr/bin/sed -n 's/^  "derives_from": "\(.*\)",$/\1/p' "$TMP/$ACTION.json")"
  [[ -n "$parents" ]] || die "$SPEC: no derives_from parents found (every row here derives from release-policy-1.0); stop"
  IFS=';' read -r -a plist <<<"$parents"
  for p in "${plist[@]}"; do p="${p# }"; [[ -z "$p" ]] && continue
    /usr/bin/grep -qF ",$p,PASS," "$log" || die "$ACTION derives from $p, which is not signed in $log yet"
  done
  /bin/cat "$TMP/$ACTION.json"
  read -r -p "Sign $ACTION into $TEAM with key op-2026? [y/N] " ok
  [[ "$ok" == "y" ]] || { echo "  not signed"; continue; }
  n0=$(/usr/bin/wc -l < "$log")
  (cd "$EMPTY" && AGENTTEAMS_DECISION_ED25519_KEYFILE="$KEYFILE" "$SIGNER" --sign-decision "$TMP/$ACTION.json" --output "$WT/$TEAM")
  n1=$(/usr/bin/wc -l < "$log")
  echo "  log lines: before sign $n0, after sign $n1"
  [[ $((n1 - n0)) -eq 1 ]] || die "the signer changed the log by $((n1 - n0)) lines (expected 1); stop, do not commit; tell the researchteam session"
  (cd "$EMPTY" && "${SIGNER%/agentteams}/python" -I -P - "$WT/$TEAM" "$ACTION") <<'PY' || die "the $ACTION row does not clear the gate; do not commit; tell the researchteam session"
import sys
from pathlib import Path
from agentteams.cli.security_gate import check_clearance
ok, why = check_clearance(Path(sys.argv[1]), action=sys.argv[2])
print(f"  {sys.argv[2]}: {'clears' if ok else 'REFUSED: ' + str(why)[:200]}")
sys.exit(0 if ok else 1)
PY
  n2=$(/usr/bin/wc -l < "$log")
  [[ "$n2" -eq "$n1" ]] || die "the post-sign gate check changed the log ($n1 -> $n2 lines); stop, do not commit; tell the researchteam session"
  signed=$((signed + 1))
done
"${GIT[@]}" --no-pager diff --stat
echo "Signed $signed row(s). Nothing was committed here. Tell the researchteam session: it commits the row on $BR,"
echo "pushes, and gives you the new head for 03-merge-pr138.sh."
else
  printf 'STOP: run as /bin/bash -p %s (privileged mode); nothing was done.\n' "$0" >&2
fi
