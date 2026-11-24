#!/bin/bash
# 27 — Sign the line-move decision row release-line-agentteams-1.3 (researchteam's lock leaves the agentteams 1.2
# line for the 1.3 line). Non-relaxing: nothing is granted and no constraint is relaxed. One run:
#   1. checks (signer, worktree at the reviewed head, spec hash, no HALT on the action, frozen-key audit);
#   2. one signing prompt (key opr-2026-11);
#   3. verification. Nothing is committed or pushed; the registry and the lock are not touched.
# If you decline at the prompt, nothing has changed. If verification fails, undo with the command the script prints.
#
# OPERATOR ONLY, plain Terminal, from any directory, ALWAYS as /bin/bash -p. HEAD is the 40-hex commit the session
# reports for branch release/pin-agentteams-1.3:
#   CHECK_ONLY=1 /bin/bash -p <this file> <HEAD>     every check; prints the payload and declines it; changes nothing
#   /bin/bash -p <this file> <HEAD>                   the real run
# Before answering y at "Sign this payload?", check: key_id opr-2026-11; action release-line-agentteams-1.3;
# derives_from release-policy-1.0; verdict PASS; derived class non-relaxing; grants [] and relaxes []; write targets
# toolchain.lock, pyproject.toml, .github/agentteams-autosync-ref; the date in the signature values is 2026-11-24.
[[ $- == *p* ]] || { printf 'STOP: run this as /bin/bash -p <path> <HEAD>\n' >&2; exit 1; }
set -euo pipefail
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
die() { printf 'STOP: %s\n' "$*" >&2; exit 1; }
[[ -z "${CLAUDECODE:-}${CLAUDE_CODE_ENTRYPOINT:-}${CODEX_SANDBOX:-}" ]] || die "run this in your own terminal, not an agent session"
[[ -t 0 && -t 1 ]] || die "run this in a terminal"
[[ -z "${ASSUME_YES:-}" ]] || die "ASSUME_YES is refused: each signing prompt is yours to answer"
[[ -z "${CHECK_ONLY:-}" || "${CHECK_ONLY:-}" == 1 ]] || die "CHECK_ONLY must be unset or 1"
if [[ "${_RT_APPROW_CLEAN:-}" != 1 ]]; then
  exec /usr/bin/env -i _RT_APPROW_CLEAN=1 HOME="$HOME" USER="${USER:-}" LOGNAME="${LOGNAME:-}" TERM="${TERM:-xterm}" \
      CHECK_ONLY="${CHECK_ONLY:-}" PATH=/usr/bin:/bin:/usr/sbin:/sbin /bin/bash -p "$0" "$@"
fi
for v in $(compgen -e); do
  case "$v" in _RT_APPROW_CLEAN|HOME|USER|LOGNAME|TERM|CHECK_ONLY|PATH|PWD|OLDPWD|SHLVL|_) ;;
    *) die "unexpected environment variable $v in the clean stage" ;; esac
done
[[ -z "$(declare -F | /usr/bin/grep -v -E ' die$')" ]] || die "an unexpected shell function exists in the clean stage"
CHECK_ONLY="${CHECK_ONLY:-}"
[[ $# -eq 1 && "$1" =~ ^[0-9a-f]{40}$ ]] || die "give the reviewed head as one full 40-hex SHA"
HEAD_WANT="$1"

WT="$HOME/githubrepositories/researchteam-wt-pin13"
BRANCH=release/pin-agentteams-1.3
DATE=2026-11-24
ACTION="release-line-agentteams-1.3"
TEAM=.github/agents
SPEC=docs/release/release-line-agentteams-1.3.decision-spec.json
SPEC_SHA=cad0ea53f19ff2b2c0fe99254d954bc03ecb4e98f2e6f097c353a0d9abc92d71
VENV="<signer>"                # root-owned install built from agentteams tag v1.2.1 on python.org 3.13; the real path is only in the copy the operator runs
BASEPY=/Library/Frameworks/Python.framework/Versions/3.13
KEY="<decision-key-file>"      # the operator's opr-2026-11 private key; the real path is only in the copy the operator runs
[[ "$VENV" != "<"* && "$KEY" != "<"* ]] || die "this is the tracked record of the script; it has placeholders and does not run"
AT="$VENV/bin/agentteams"; PY="$VENV/bin/python"
PUB_SHA=d22faa83b674abe6b1e3207a4f13fc17c5ddd367e35e0c60c69163eddbd9dab7
AUDIT_SRC="$HOME/githubrepositories/infrastructureManagement/scripts/frozen_key_audit.py"
AUDIT_SHA=b85de5e31c74124f6722fd84f4590db70cd23b8a5a9bd46939d051ff0f6697a6
BASE_SRC="$HOME/githubrepositories/infrastructureManagement/references/frozen-key-baseline-2026-11-21b.json"
BASE_SHA=7406903c1172d90864f009f5b8dc4761e82115a8cbc2bb5d9c0b70e983f6cf56
LOG="$TEAM/references/security-decisions.log.csv"
G=(/usr/bin/git --no-pager -c core.fsmonitor=false -c core.hooksPath=/dev/null -c core.pager=cat)
sha() { /usr/bin/shasum -a 256 "$1" | /usr/bin/cut -d' ' -f1; }
UNDO="/usr/bin/git -c core.hooksPath=/dev/null -C $WT checkout -- $LOG"
[[ "$(/bin/date +%Y-%m-%d)" == "$DATE" ]] || die "today is not $DATE: the spec carries the signing day, so the session must regenerate it"

# 0. The signer: root-owned agentteams 1.2.1 on the root-owned python.org 3.13.
[[ -x "$AT" && -x "$PY" ]] || die "the clean signer is missing"
bad=$(/usr/bin/find "$VENV" "$BASEPY" \( ! -user root -o \( ! -type l \( -perm -0020 -o -perm -0002 \) \) \) -print 2>&1 | /usr/bin/head -3)
[[ -z "$bad" ]] || die "the signer or its base Python has an entry that is not root-owned or is group/world-writable: $bad"
"$AT" --version | /usr/bin/grep -q -E '^agentteams 1\.2\.1([^0-9]|$)' || die "the signer is not agentteams 1.2.1"
base=$("$PY" -I -c 'import sys; print(sys.base_prefix)')
[[ "$base" == "$BASEPY" ]] || die "the signer's base Python is $base, not $BASEPY"
printf '== signer: agentteams 1.2.1, root-owned, base %s\n' "$base"

# 1. The worktree, the spec, the store, the key.
[[ -d "$WT" && ! -L "$WT" ]] || die "no worktree at $WT"
cd "$WT"
[[ "$("${G[@]}" branch --show-current)" == "$BRANCH" ]] || die "$WT is not on $BRANCH"
[[ "$("${G[@]}" rev-parse HEAD)" == "$HEAD_WANT" ]] || die "HEAD is $("${G[@]}" rev-parse HEAD), not the reviewed $HEAD_WANT"
[[ -z "$("${G[@]}" status --porcelain --untracked-files=all)" ]] || die "$WT has uncommitted changes; if an earlier run failed, undo it first: $UNDO"
[[ -f "$SPEC" && ! -L "$SPEC" && "$(sha "$SPEC")" == "$SPEC_SHA" ]] || die "$SPEC is not the reviewed $SPEC_SHA"
/usr/bin/grep -qF "\"action_reviewed\": \"$ACTION\"" "$SPEC" || die "$SPEC is not for $ACTION"
/usr/bin/grep -qF "\"scope\": \"$ACTION\"" "$SPEC" || die "$SPEC scope is not $ACTION"
/usr/bin/grep -qF '"effect_relaxes": ""' "$SPEC" || die "$SPEC relaxes something"
/usr/bin/grep -qF '"effect_grants": ""' "$SPEC" || die "$SPEC grants something"
/usr/bin/grep -qF '"effect_targets": "toolchain.lock; pyproject.toml; .github/agentteams-autosync-ref"' "$SPEC" || die "$SPEC write targets are not the three pin files"
/usr/bin/grep -qF '"effect_destructive": "false"' "$SPEC" || die "$SPEC is marked destructive"
/usr/bin/grep -qF '"effect_cross_repo": "false"' "$SPEC" || die "$SPEC is marked cross-repository"
/usr/bin/grep -qF '"effect_bulk": "false"' "$SPEC" || die "$SPEC is marked bulk"
/usr/bin/grep -qF '"derives_from": "release-policy-1.0"' "$SPEC" || die "$SPEC does not derive from release-policy-1.0 alone"
/usr/bin/grep -qF '"key_id": "opr-2026-11"' "$SPEC" || die "$SPEC does not name key opr-2026-11"
/usr/bin/grep -qF "\"date\": \"$DATE\"" "$SPEC" || die "$SPEC is not dated $DATE"
/usr/bin/grep -qF '"verdict": "PASS"' "$SPEC" || die "$SPEC verdict is not PASS"
p="$TEAM/references/authorized-verify-keys/opr-2026-11.pub.pem"
[[ -f "$p" && ! -L "$p" && "$(sha "$p")" == "$PUB_SHA" ]] || die "$p is not $PUB_SHA"
[[ -f "$KEY" && ! -L "$KEY" && "$(/usr/bin/stat -f %Lp "$KEY")" == 600 ]] || die "the key file is missing, a link, or not mode 600"
/usr/bin/grep -qF ",$ACTION," "$LOG" && die "a row for $ACTION is already in $LOG; nothing to do"
"$PY" -I -c 'import csv,sys
csv.field_size_limit(10**8)
bad=[r.get("action_reviewed") for r in csv.DictReader(open(sys.argv[1],newline="",encoding="utf-8"))
     if (r.get("verdict") or "").strip().upper()=="HALT" and any(k in ((r.get("action_reviewed") or "")+" "+(r.get("scope") or "")).lower() for k in ("release-line-agentteams","release-policy-1.0"))]
print("  HALT rows naming the release line or its parent:", bad or "none"); sys.exit(1 if bad else 0)' "$LOG" || die "a HALT naming the release line or its parent is recorded; do not sign"
printf '== inputs OK: head %s\n' "${HEAD_WANT:0:8}"

# 2. The frozen-key audit (fail-closed preflight), from private copies checked by hash.
TMP=$(/usr/bin/mktemp -d); trap '/bin/rm -rf "$TMP"' EXIT
/bin/chmod 700 "$TMP"
[[ -f "$AUDIT_SRC" && ! -L "$AUDIT_SRC" && -f "$BASE_SRC" && ! -L "$BASE_SRC" ]] || die "the frozen-key audit or its baseline is missing"
/bin/cp "$AUDIT_SRC" "$TMP/frozen_key_audit.py"; /bin/cp "$BASE_SRC" "$TMP/baseline.json"
[[ "$(sha "$TMP/frozen_key_audit.py")" == "$AUDIT_SHA" ]] || die "the frozen-key audit is not the pinned $AUDIT_SHA"
[[ "$(sha "$TMP/baseline.json")" == "$BASE_SHA" ]] || die "the frozen-key baseline is not the pinned $BASE_SHA"
"$BASEPY/bin/python3" -I "$TMP/frozen_key_audit.py" --check "$TMP/baseline.json" "$WT" \
  || die "the frozen-key audit did not pass (exit $?); nothing was signed; paste this output to the session"
printf '== frozen-key audit: clean\n'

if [[ "$CHECK_ONLY" == 1 ]]; then
  printf '\n================ %s (CHECK_ONLY: the payload is shown and declined)\n' "$ACTION"
  printf 'n\n' | AGENTTEAMS_DECISION_ED25519_KEYFILE="$KEY" "$AT" --sign-decision "$SPEC" --output "$TEAM" || true
  [[ -z "$("${G[@]}" status --porcelain --untracked-files=all)" ]] || die "CHECK_ONLY changed the worktree; undo: $UNDO"
  printf '\nCHECK_ONLY: every check passed; nothing was signed and the worktree is unchanged.\n'; exit 0
fi

# 3. Sign (one prompt from agentteams).
n0=$(/usr/bin/wc -l < "$LOG")
printf '\n================ %s  (into %s)\n' "$ACTION" "$LOG"
AGENTTEAMS_DECISION_ED25519_KEYFILE="$KEY" "$AT" --sign-decision "$SPEC" --output "$TEAM" \
  || die "signing failed or was declined; if $LOG changed, undo: $UNDO"
n1=$(/usr/bin/wc -l < "$LOG")
[[ $((n1 - n0)) -eq 1 ]] || die "the signer changed the log by $((n1 - n0)) lines (expected 1); do not commit; undo: $UNDO"

# 4. Verify.
"$PY" -I - "$TEAM" "$ACTION" "$LOG" "$SPEC" <<'PYEOF' || die "verification failed; do not commit; undo: $UNDO ; paste this output to the session"
import csv, json, subprocess, sys
from pathlib import Path
from agentteams.cli.security_gate import check_clearance
team, action, log = sys.argv[1], sys.argv[2], sys.argv[3]
git = ["/usr/bin/git", "--no-pager", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null"]
old = subprocess.run(git + ["show", f"HEAD:{log}"], capture_output=True, check=True).stdout.replace(b"\r", b"")
new = Path(log).read_bytes().replace(b"\r", b"")
csv.field_size_limit(10**8)
rows = [r for r in csv.DictReader(open(log, newline="", encoding="utf-8")) if (r.get("action_reviewed") or "") == action]
one = len(rows) == 1 and rows[0].get("key_id") == "opr-2026-11" and rows[0].get("sig_scheme") == "ed25519" \
    and rows[0].get("derives_from") == "release-policy-1.0" and not (rows[0].get("effect_relaxes") or "").strip() \
    and not (rows[0].get("effect_grants") or "").strip()
spec = json.load(open(sys.argv[4], encoding="utf-8"))
same = one and all((rows[0].get(k) or "") == (spec.get(k) or "") for k in
                   ("date", "scope", "verdict", "conditions", "conditions_verified", "effect_targets", "derives_from"))
ok, why = check_clearance(Path(team), action=action)
print(f"   {action}: {'CLEARED' if ok else 'NOT CLEARED: ' + str(why)[:200]} | one opr-2026-11 row, non-relaxing: {one} | row equals the spec: {same} | log is the committed bytes plus appended rows: {new.startswith(old)}")
sys.exit(0 if ok and one and same and new.startswith(old) else 1)
PYEOF
out=$("$AT" --verify-toolchain-group --output "$TEAM" --description brief.json 2>&1) \
  || { printf '%s\n' "$out"; die "the toolchain group no longer verifies; do not commit; undo: $UNDO"; }
printf '%s\n' "$out" | /usr/bin/tail -1
changed="$("${G[@]}" status --porcelain --untracked-files=all)"
[[ "$changed" == " M $LOG" ]] || die "unexpected changes in the worktree (expected only $LOG): $changed ; do not commit; undo: $UNDO"
"${G[@]}" diff --stat
printf '== done: 1 row signed; nothing committed or pushed. Paste this output into the researchteam session.\n'
