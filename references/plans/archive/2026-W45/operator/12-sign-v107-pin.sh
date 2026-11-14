#!/bin/bash -p
# 12 — Sign researchteam's pin-agentteams-v1.0.7 row into the release-prep/1.0.4 worktree (PR #144, base release/1.0).
# OPERATOR ONLY. Modelled on 09-sign-rc16-pin.sh (same hardened checks; the pin's tag re-verified here against the lock
# lines and the spec's object/peeled values; exactly one log line; the row clears agentteams' gate). Its parents are all
# already signed in this log (taken from main). Usage (plain Terminal; ALWAYS `/bin/bash -p <absolute path>`, never `bash <path>`):
#   /bin/bash -p ~/githubrepositories/researchteam/tmp/by-week/2026-W45/operator/12-sign-v107-pin.sh <40-hex head the session reports>
# It COMMITS NOTHING: the researchteam session commits the row, pushes, and gives you 13.
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


HEAD_REVIEWED="${1:?usage: $0 <40-hex reviewed head of release-prep/1.0.4>}"
REPO="researchteam"
WT="$HOME/githubrepositories/researchteam-1.0.4"
ACTIONS=(pin-agentteams-v1.0.7)
BR="release-prep/1.0.4"
TEAM=".github/agents"
AT_V100="cc5b8c9ec4efdcb479939e0c1246a0ac11913259"   # agentteams v1.0.0 (dependency baseline)
RELEASE_FP="SHA256:IPdnLwlFdHNhr7QGKVWU40BOKyYzv2u8qxP/qxnzTNM"
ALLOWED_SIGNERS="$HOME/.config/agentteams/allowed_signers"
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

# verify_release_tag URL TAG [DEPS_BASELINE]: as consumers verify; sets V_OBJ / V_PEELED.
verify_release_tag() {
  local url="$1" tag="$2" base="${3:-}" at="$TMP/v-$2" err named remote
  [[ -f "$ALLOWED_SIGNERS" ]] || die "missing $ALLOWED_SIGNERS"
  "${GIT[@]}" init -q "$at"
  "${GIT[@]}" -C "$at" fetch -q --no-tags "$url" "refs/tags/$tag:refs/tags/$tag" ${base:+"$base"} || die "cannot fetch $tag from $url"
  [[ "$("${GIT[@]}" -C "$at" cat-file -t "refs/tags/$tag")" == tag ]] || die "$tag is not an annotated tag"
  err="$("${GIT[@]}" -C "$at" -c gpg.format=ssh -c gpg.ssh.program=/usr/bin/ssh-keygen \
        -c gpg.ssh.allowedSignersFile="$ALLOWED_SIGNERS" tag -v "$tag" 2>&1 >/dev/null)" || die "$tag does not verify: $err"
  /usr/bin/grep -qF "Good \"git\" signature" <<<"$err" || die "$tag: no good signature"
  /usr/bin/grep -qF "with RSA key $RELEASE_FP" <<<"$err" || die "$tag: not signed by the release key"
  V_OBJ="$("${GIT[@]}" -C "$at" rev-parse "refs/tags/$tag")"
  V_PEELED="$("${GIT[@]}" -C "$at" rev-parse "refs/tags/$tag^{commit}")"
  named="$("${GIT[@]}" -C "$at" cat-file tag "$V_OBJ" | /usr/bin/sed -n 's/^tag //p')"
  [[ "$named" == "$tag" ]] || die "the tag object names itself $named"
  remote="$("${GIT[@]}" ls-remote "$url" "refs/tags/$tag" | /usr/bin/cut -f1)"
  [[ "$remote" == "$V_OBJ" ]] || die "remote advertises $remote, verified object is $V_OBJ"
  if [[ -n "$base" ]]; then
    deps() { "${GIT[@]}" -C "$at" show "$1:pyproject.toml" | /usr/bin/awk '/^\[/{inproj = ($0 ~ /^\[project(\.|\])/)} inproj' | /usr/bin/grep -vE '^(version|description|readme|name) *=' | /usr/bin/grep -vE '^ *#'; }
    # 1.0 line: agentteams' declared dependencies must be exactly v1.0.0's (no exceptions).
    /usr/bin/diff <(deps "$base") <(deps "$V_PEELED") >/dev/null \
      || die "agentteams' declared dependencies changed since v1.0.0: new S-10 vetting needed"
    echo "  dependencies: identical to v1.0.0"
  fi
  if [[ "$url" == */researchteam ]]; then  # the exemption relies on this
    "${GIT[@]}" -C "$at" show "$V_PEELED:pyproject.toml" | /usr/bin/grep -qx 'dependencies = \[\]' \
      || die "researchteam $tag declares runtime dependencies; the 1.1 exemption does not cover them"
  fi
  echo "  verified $tag: object $V_OBJ, peeled $V_PEELED"
}

signed=0
for ACTION in "${ACTIONS[@]}"; do
  SLUG="${ACTION//:/-}"; SLUG="${SLUG//\//-}"   # file names cannot hold : or /
  SPEC="docs/release/$SLUG.decision-spec.json"
  echo; echo "== $REPO: $ACTION"
  if /usr/bin/grep -qF ",$ACTION,PASS," "$log"; then echo "  already in $log; skipped"; continue; fi
  "${GIT[@]}" show "$HEAD_REVIEWED:$SPEC" > "$TMP/$SLUG.json" 2>/dev/null || die "no $SPEC at the head"
  /usr/bin/grep -qE '<[A-Z_]+>' "$TMP/$SLUG.json" && die "$SPEC still has a placeholder"
  /usr/bin/grep -qF "\"action_reviewed\": \"$ACTION\"" "$TMP/$SLUG.json" || die "$SPEC is not for $ACTION"
  /usr/bin/grep -qF "\"scope\": \"$ACTION\"" "$TMP/$SLUG.json" || die "$SPEC scope is not $ACTION"
  # Every parent the spec derives from must already be a signed PASS row in this repo's log.
  parents="$(/usr/bin/sed -n 's/^  "derives_from": "\(.*\)",$/\1/p' "$TMP/$SLUG.json")"
  [[ -n "$parents" ]] || die "$SPEC: no derives_from parents found (every row here derives from release-policy-1.0); stop"
  IFS=';' read -r -a plist <<<"$parents"
  for p in "${plist[@]}"; do p="${p# }"; [[ -z "$p" ]] && continue
    /usr/bin/grep -qF ",$p,PASS," "$log" || die "$ACTION derives from $p, which is not signed in $log yet"
  done
  case "$ACTION" in
    pin-agentteams-*)   TAG="${ACTION#pin-agentteams-}";   verify_release_tag "https://github.com/jlcatonjr/agentteams" "$TAG" "$AT_V100" ;;
    pin-researchteam-*) TAG="${ACTION#pin-researchteam-}"; verify_release_tag "https://github.com/jlcatonjr/researchteam" "$TAG" ;;
    *) TAG="" ;;
  esac
  if [[ -n "$TAG" ]]; then
    PKG="${ACTION#pin-}"; PKG="${PKG%-v1.*}"
    "${GIT[@]}" show "$HEAD_REVIEWED:toolchain.lock" | /usr/bin/grep -qx "$PKG=jlcatonjr/$PKG@$V_PEELED" \
      || die "toolchain.lock at the head does not pin $PKG to the verified $V_PEELED"
    "${GIT[@]}" show "$HEAD_REVIEWED:toolchain.lock" | /usr/bin/grep -qx "$PKG.tag=$TAG" \
      || die "toolchain.lock at the head does not release-lock $PKG at $TAG"
    /usr/bin/grep -qF "$TAG object $V_OBJ peeled $V_PEELED" "$TMP/$SLUG.json" \
      || die "$SPEC conditions_verified does not name the verified tag object $V_OBJ and peeled $V_PEELED"
    /usr/bin/grep -qF "(tag object $V_OBJ," "$TMP/$SLUG.json" || die "$SPEC conditions do not name tag object $V_OBJ"
    /usr/bin/grep -qF -- "-> $V_PEELED ($TAG)" "$TMP/$SLUG.json" || die "$SPEC evidence does not name peeled $V_PEELED"
  fi
  /bin/cat "$TMP/$SLUG.json"
  read -r -p "Sign $ACTION into $TEAM with key op-2026? [y/N] " ok
  [[ "$ok" == "y" ]] || { echo "  not signed"; continue; }
  n0=$(/usr/bin/wc -l < "$log")
  (cd "$EMPTY" && AGENTTEAMS_DECISION_ED25519_KEYFILE="$KEYFILE" "$SIGNER" --sign-decision "$TMP/$SLUG.json" --output "$WT/$TEAM")
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
echo "Signed $signed row(s). Nothing was committed here. Tell the researchteam session: it commits them on $BR,"
echo "pushes, and gives you the new head for 13-merge-pr144.sh."
else
  printf 'STOP: run as /bin/bash -p %s (privileged mode); nothing was done.\n' "$0" >&2
fi
