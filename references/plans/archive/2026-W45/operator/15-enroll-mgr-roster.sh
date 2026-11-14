#!/bin/bash -p
# 15 — Enroll infrastructure-management in researchteam's manager roster (RT-7 precondition, 2026-11-06).
# OPERATOR ONLY. An agent does not write the roster (it is on the agent deny list with the key store), so you do:
#   1. render the agent team from the branch's brief.json (authorized_managers = ["infrastructure-management"]);
#   2. keep ONLY the 13 rendered enrollment files (_build-description.json, and on each of the
#      four surfaces authorized-managers.txt, management-authority.json, management-directives.log.csv) and discard every
#      other re-render change (the pinned agentteams rc.16 would otherwise downgrade @security's fence v21 -> v20);
#   3. check the roster names exactly that one team and is_management_repo stays false;
#   4. sign management-roster-enroll:infrastructure-management (key op-2026) and check it clears agentteams' gate;
#   5. COMMIT the result as you (as @security required: the operator renders and commits the roster).
# It does not push; the researchteam session pushes, opens the PR, and merges only at CLEAN.
# Usage (plain Terminal; ALWAYS `/bin/bash -p <absolute path>`, never `bash <path>`):
#   /bin/bash -p ~/githubrepositories/researchteam/tmp/by-week/2026-W45/operator/15-enroll-mgr-roster.sh d8c0e86eccfa8cf37820a119f6103dafbf05f638
# Modelled on 12-sign-v107-pin.sh (same hardened prelude, signer and gate check).
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

HEAD_REVIEWED="${1:?usage: $0 <40-hex reviewed head of chore/enroll-infrastructure-management>}"
WT="$HOME/githubrepositories/researchteam"
BR="chore/enroll-infrastructure-management"
MANAGER="infrastructure-management"
ACTION="management-roster-enroll:$MANAGER"
SPEC="docs/release/management-roster-enroll-$MANAGER.decision-spec.json"
TEAM=".github/agents"
SURFACES=(.github/agents .claude/agents .codex/agents .goose/recipes)
RT="$WT/.venv/bin/researchteam"                       # pinned toolchain (scripts/bootstrap_toolchain.sh)
SIGNER="<signer>"     # root-owned (2026-W42/01b)
KEYFILE="<decision-key-file>"
AUTHOR="the operator <<noreply>>"
[[ "$HEAD_REVIEWED" =~ ^[0-9a-f]{40}$ ]] || die "the head must be a full 40-hex SHA"
[[ -x "$SIGNER" ]] || die "no root-owned signer at $SIGNER (2026-W42/01b)"
[[ "$(/usr/bin/stat -f %Su "$SIGNER")" == root ]] || die "$SIGNER is not root-owned"
[[ -f "$KEYFILE" ]] || die "missing $KEYFILE"
[[ -x "$RT" ]] || die "no pinned toolchain at $RT (run scripts/bootstrap_toolchain.sh)"

cd "$WT"
[[ "$("${GIT[@]}" rev-parse --abbrev-ref HEAD)" == "$BR" ]] || die "$WT is not on $BR (git checkout $BR)"
[[ "$("${GIT[@]}" rev-parse HEAD)" == "$HEAD_REVIEWED" ]] || die "$BR is at $("${GIT[@]}" rev-parse HEAD), not the reviewed $HEAD_REVIEWED"
[[ -z "$("${GIT[@]}" status --porcelain)" ]] || die "$WT has uncommitted changes; stop"
"${GIT[@]}" show "$HEAD_REVIEWED:brief.json" | /usr/bin/grep -qx "  \"authorized_managers\": \[\"$MANAGER\"\]," \
  || die "brief.json at the head does not enroll exactly $MANAGER"
log="$TEAM/references/security-decisions.log.csv"
/usr/bin/grep -qF ",$ACTION,PASS," "$log" && die "$ACTION is already in $log"
TMP=$(/usr/bin/mktemp -d); trap 'rm -rf "$TMP"' EXIT
EMPTY="$TMP/empty"; /bin/mkdir "$EMPTY"

KEEP=(.github/agents/_build-description.json)
for s in "${SURFACES[@]}"; do
  KEEP+=("$s/references/authorized-managers.txt" "$s/references/management-authority.json" "$s/references/management-directives.log.csv")
done

echo "== 1. render (researchteam update --yes, pinned toolchain)"
"$RT" update --yes > "$TMP/render.log" 2>&1 || { /usr/bin/tail -20 "$TMP/render.log"; die "the render failed; nothing kept (git checkout -- . && git clean -fd to reset)"; }
[[ "$(/usr/bin/grep -c 'Management-repository endowment is ON' "$TMP/render.log")" -ge 4 ]] \
  || die "the render did not report the management endowment on all four surfaces; see a re-run's output"

echo "== 2. keep only the 13 rendered enrollment files"
for p in "${KEEP[@]}"; do [[ -f "$p" ]] || die "the render did not write $p"; done
"${GIT[@]}" add -- "${KEEP[@]}"
"${GIT[@]}" checkout -- .            # discard every other (unstaged) re-render change
"${GIT[@]}" clean -fdq               # and every other new file (the tree was clean before the render)
staged="$("${GIT[@]}" diff --cached --name-only | /usr/bin/sort)"
want="$(printf '%s\n' "${KEEP[@]}" | /usr/bin/sort)"
[[ "$staged" == "$want" ]] || { echo "$staged"; die "the staged set is not exactly the 13 rendered enrollment files"; }

echo "== 3. check the roster"
for s in "${SURFACES[@]}"; do
  names="$(/usr/bin/grep -vE '^[[:space:]]*(#|$)' "$s/references/authorized-managers.txt")"
  [[ "$names" == "$MANAGER" ]] || die "$s roster names [$names], not exactly $MANAGER"
  /usr/bin/grep -q '"is_management_repo": false' "$s/references/management-authority.json" || die "$s: is_management_repo is not false"
  [[ "$(/usr/bin/wc -l < "$s/references/management-directives.log.csv" | /usr/bin/tr -d ' ')" == 1 ]] || die "$s: the directives ledger is not header-only"
  echo "  $s: roster = $names; is_management_repo false; ledger empty"
done

echo "== 4. sign $ACTION"
"${GIT[@]}" show "$HEAD_REVIEWED:$SPEC" > "$TMP/spec.json" 2>/dev/null || die "no $SPEC at the head"
/usr/bin/grep -qE '<[A-Z_]+>' "$TMP/spec.json" && die "$SPEC still has a placeholder"
/usr/bin/grep -qF "\"action_reviewed\": \"$ACTION\"" "$TMP/spec.json" || die "$SPEC is not for $ACTION"
/usr/bin/grep -qF "\"scope\": \"$ACTION\"" "$TMP/spec.json" || die "$SPEC scope is not $ACTION"
/usr/bin/grep -qF ",release-policy-1.0,PASS," "$log" || die "the parent release-policy-1.0 is not signed in $log"
/bin/cat "$TMP/spec.json"
read -r -p "Sign $ACTION into $TEAM with key op-2026? [y/N] " ok
[[ "$ok" == "y" ]] || { "${GIT[@]}" reset -q; "${GIT[@]}" checkout -- .; die "not signed; the render was discarded"; }
n0=$(/usr/bin/wc -l < "$log")
(cd "$EMPTY" && AGENTTEAMS_DECISION_ED25519_KEYFILE="$KEYFILE" "$SIGNER" --sign-decision "$TMP/spec.json" --output "$WT/$TEAM")
n1=$(/usr/bin/wc -l < "$log")
[[ $((n1 - n0)) -eq 1 ]] || die "the signer changed the log by $((n1 - n0)) lines (expected 1); do not commit; tell the researchteam session"
(cd "$EMPTY" && "${SIGNER%/agentteams}/python" -I -P - "$WT/$TEAM" "$ACTION") <<'PY' || die "the row does not clear the gate; do not commit; tell the researchteam session"
import sys
from pathlib import Path
from agentteams.cli.security_gate import check_clearance
ok, why = check_clearance(Path(sys.argv[1]), action=sys.argv[2])
print(f"  {sys.argv[2]}: {'clears' if ok else 'REFUSED: ' + str(why)[:200]}")
sys.exit(0 if ok else 1)
PY
[[ "$(/usr/bin/wc -l < "$log")" -eq "$n1" ]] || die "the post-sign gate check changed the log; do not commit"

echo "== 5. commit"
"${GIT[@]}" add -- "$log"
"${GIT[@]}" --no-pager diff --cached --stat
read -r -p "Commit these 14 files as $AUTHOR? [y/N] " ok
[[ "$ok" == "y" ]] || die "not committed; the staged render and signed row are left for you to inspect"
"${GIT[@]}" -c user.name="${AUTHOR% <*}" -c user.email="$(echo "$AUTHOR" | /usr/bin/sed 's/.*<\(.*\)>/\1/')" commit -q -m \
"security: enroll infrastructure-management in the manager roster (operator render + signed row)

Rendered by the operator from brief.json authorized_managers under the pinned agentteams
(toolchain.lock); only the enrollment files are kept. Each of the four surfaces' roster names exactly
infrastructure-management and is_management_repo stays false. Signed row
management-roster-enroll:infrastructure-management (op-2026) clears agentteams' gate."
echo "Committed $("${GIT[@]}" rev-parse HEAD) on $BR. Tell the researchteam session; it pushes and opens the PR."
else
  printf 'STOP: run as /bin/bash -p %s (privileged mode); nothing was done.\n' "$0" >&2
fi
