#!/bin/bash
# 33 — Sign the clearance row key-retire:op-2026 (H3 phase 3, condition C2): @security's PASS for removing the old
# decision verify key op-2026 from the .github and .codex verify-key stores, signed by the operator with opr-2026-11.
# The row is destructive (two tracked files are deleted by script 34) and relaxes and grants nothing. One run:
#   1. checks (signer, worktree at the reviewed head, spec hash, script 34's hash, both key files, no HALT on
#      key-retire or the action in any team log, the id not yet in any log, frozen-key audit);
#   2. one signing prompt (key opr-2026-11);
#   3. verification. Nothing is removed, committed or pushed; the registry and the key stores are not touched.
# If you decline at the prompt, nothing has changed. If verification fails, undo with the command the script prints.
#
# OPERATOR ONLY, plain Terminal, from any directory, ALWAYS as /bin/bash -p. HEAD is the 40-hex commit the session
# reports for branch chore/retire-op-2026:
#   CHECK_ONLY=1 /bin/bash -p <this file> <HEAD>     every check; prints the payload and declines it; changes nothing
#   /bin/bash -p <this file> <HEAD>                   the real run
# Before answering y at "Sign this payload?", check: key_id opr-2026-11; action key-retire:op-2026; derives_from
# release-policy-1.0; verdict PASS; grants [] and relaxes []; write targets [] (agentteams refuses a decision whose
# write target lies in a verify-key store, so the two files are named in the text); destructive/xrepo/bulk
# True/False/False; the derived class reads "relaxing" because the row is destructive, and "needs operator" False;
# the date in the signature values is 2026-11-26.
[[ $- == *p* ]] || { printf 'STOP: run this as /bin/bash -p <path> <HEAD>\n' >&2; exit 1; }
set -euo pipefail
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
die() { printf 'STOP: %s\n' "$*" >&2; exit 1; }
[[ -z "${CLAUDECODE:-}${CLAUDE_CODE_ENTRYPOINT:-}${CLAUDE_CODE_SSE_PORT:-}${CODEX_SANDBOX:-}" ]] || die "run this in your own terminal, not an agent session"
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

WT="$HOME/githubrepositories/researchteam-wt-h3c"
BRANCH=chore/retire-op-2026
DATE=2026-11-26
ACTION="key-retire:op-2026"
TEAM=.github/agents
SPEC=docs/release/key-retire-op-2026.decision-spec.json
SPEC_SHA=851d20fc499e5c0ea27a8b21f48ada195e7268f91fe4f4d4ec0a9ba154be22f8
S34=references/plans/archive/2026-W48/operator/34-remove-op-2026.sh
S34_SHA=c3de6b666ba1698304982036eb40ca09e0e641b5db01c88875f123148c54e57e     # the tracked copy of script 34; the spec's text names the same hash
KEY_SHA=08f69c5d0e899bd26b26deb6f9f3af9b1a65a9c5e0ee25733769cc1ea3e70e7b      # op-2026.pub.pem, the same in both stores
F1=.github/agents/references/authorized-verify-keys/op-2026.pub.pem
F2=.codex/agents/references/authorized-verify-keys/op-2026.pub.pem
PHASE2_MAIN=8e827f9311b0a4b59e16a0c27659425833fb5baf
SIGNER="<signer>"     # @ph <signer> root-owned agentteams 1.3.0 install; the real path is only in the copy the operator runs
KEY="<decision-key-file>"     # @ph <decision-key-file> the operator's opr-2026-11 private key; the real path is only in the copy the operator runs
[[ "$SIGNER" != "<"* && "$KEY" != "<"* ]] || die "this is the tracked record of the script; it has placeholders and does not run"
AT="$SIGNER"; PY="${SIGNER%/agentteams}/python"; VENV="${SIGNER%/bin/agentteams}"
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

# 0. The signer: root-owned agentteams 1.3.0 (the version toolchain.lock pins) on a root-owned base Python.
[[ -x "$AT" && -x "$PY" ]] || die "the clean signer is missing"
base=$("$PY" -I -c 'import sys; print(sys.base_prefix)')
bad=$(/usr/bin/find "$VENV" "$base" \( ! -user root -o \( ! -type l \( -perm -0020 -o -perm -0002 \) \) \) -print 2>&1 | /usr/bin/head -3) || :   # find may be cut off by head (SIGPIPE); what it printed decides
[[ -z "$bad" ]] || die "the signer or its base Python has an entry that is not root-owned or is group/world-writable: $bad"
ver=$("$AT" --version 2>&1) || die "the signer does not run"
[[ "$ver" =~ ^agentteams\ 1\.3\.0([^0-9]|$) ]] || die "the signer is not agentteams 1.3.0 ($ver)"
[[ "$("$PY" -I -c 'import agentteams; print(agentteams.__version__)')" == 1.3.0 ]] || die "the signer's library is not agentteams 1.3.0"
printf '== signer: agentteams 1.3.0, root-owned, base %s\n' "$base"

# 1. The worktree, the spec, script 34, the key files, the store, the key.
[[ -d "$WT" && ! -L "$WT" ]] || die "no worktree at $WT"
cd "$WT"
[[ "$("${G[@]}" branch --show-current)" == "$BRANCH" ]] || die "$WT is not on $BRANCH"
[[ "$("${G[@]}" rev-parse HEAD)" == "$HEAD_WANT" ]] || die "HEAD is $("${G[@]}" rev-parse HEAD), not the reviewed $HEAD_WANT"
[[ -z "$("${G[@]}" status --porcelain --untracked-files=all)" ]] || die "$WT has uncommitted changes; if an earlier run failed, undo it first: $UNDO"
"${G[@]}" merge-base --is-ancestor "$PHASE2_MAIN" HEAD || die "phase 2's merge $PHASE2_MAIN is not in $BRANCH"
[[ -f "$SPEC" && ! -L "$SPEC" && "$(sha "$SPEC")" == "$SPEC_SHA" ]] || die "$SPEC is not the reviewed $SPEC_SHA"
[[ -f "$S34" && ! -L "$S34" && "$(sha "$S34")" == "$S34_SHA" ]] || die "$S34 is not the reviewed $S34_SHA"
/usr/bin/grep -qF "\"action_reviewed\": \"$ACTION\"" "$SPEC" || die "$SPEC is not for $ACTION"
/usr/bin/grep -qF "\"scope\": \"$ACTION\"" "$SPEC" || die "$SPEC scope is not $ACTION"
/usr/bin/grep -qF '"effect_relaxes": ""' "$SPEC" || die "$SPEC relaxes something"
/usr/bin/grep -qF '"effect_grants": ""' "$SPEC" || die "$SPEC grants something"
/usr/bin/grep -qF '"effect_targets": ""' "$SPEC" || die "$SPEC declares write targets"
/usr/bin/grep -qF '"effect_destructive": "true"' "$SPEC" || die "$SPEC is not marked destructive"
/usr/bin/grep -qF '"effect_cross_repo": "false"' "$SPEC" || die "$SPEC is marked cross-repository"
/usr/bin/grep -qF '"effect_bulk": "false"' "$SPEC" || die "$SPEC is marked bulk"
/usr/bin/grep -qF '"derives_from": "release-policy-1.0"' "$SPEC" || die "$SPEC does not derive from release-policy-1.0 alone"
/usr/bin/grep -qF '"key_id": "opr-2026-11"' "$SPEC" || die "$SPEC does not name key opr-2026-11"
/usr/bin/grep -qF "\"date\": \"$DATE\"" "$SPEC" || die "$SPEC is not dated $DATE"
/usr/bin/grep -qF '"verdict": "PASS"' "$SPEC" || die "$SPEC verdict is not PASS"
for needle in "$S34" "$S34_SHA" "$KEY_SHA" "$F1" "$F2" "$PHASE2_MAIN" "Let both lapse" "Retire the key first" "Leave them alone"; do
  /usr/bin/grep -qF -- "$needle" "$SPEC" || die "$SPEC does not name $needle"
done
for f in "$F1" "$F2"; do
  [[ -f "$f" && ! -L "$f" && "$(sha "$f")" == "$KEY_SHA" ]] || die "$f is missing, a link, or not $KEY_SHA"
done
p="$TEAM/references/authorized-verify-keys/opr-2026-11.pub.pem"
[[ -f "$p" && ! -L "$p" && "$(sha "$p")" == "$PUB_SHA" ]] || die "$p is not $PUB_SHA"
[[ -f "$KEY" && ! -L "$KEY" && "$(/usr/bin/stat -f %Lp "$KEY")" == 600 ]] || die "the key file is missing, a link, or not mode 600"
TMP=$(/usr/bin/mktemp -d); trap '/bin/rm -rf "$TMP"' EXIT
/bin/chmod 700 "$TMP"; /bin/mkdir "$TMP/empty"
# No row for the id in any team log yet, and no unretracted HALT on key-retire or the action in any team log, by
# agentteams' own scan (a retraction counts only when authentic and carries evidence; lineage ancestors are followed).
(cd "$TMP/empty" && "$PY" -I -P - "$WT" "$ACTION") <<'PY' || die "the id is already recorded or a HALT stands; do not sign"
import csv, sys
from pathlib import Path
from agentteams.cli.decision_log import _assert_no_unretracted_halt
wt, action = Path(sys.argv[1]), sys.argv[2]
csv.field_size_limit(10**8)
bad = []
for rel in (".github/agents", ".claude/agents", ".codex/agents", ".goose/recipes"):
    team = wt / rel
    log = team / "references" / "security-decisions.log.csv"
    if not log.is_file():
        continue
    with open(log, newline="", encoding="utf-8") as fh:
        if any((r.get("action_reviewed") or "").strip() == action for r in csv.DictReader(fh)):
            bad.append(f"a {action} row is already in {rel}")
    for act in ("key-retire", action):
        try:
            _assert_no_unretracted_halt(team, action=act)
        except RuntimeError as exc:
            bad.append(f"HALT stands in {rel} on {act}: {str(exc)[:160]}")
print("  id recorded or HALT standing:", bad or "none")
sys.exit(1 if bad else 0)
PY
printf '== inputs OK: head %s\n' "${HEAD_WANT:0:8}"

# 2. The frozen-key audit (fail-closed preflight), from private copies checked by hash.
[[ -f "$AUDIT_SRC" && ! -L "$AUDIT_SRC" && -f "$BASE_SRC" && ! -L "$BASE_SRC" ]] || die "the frozen-key audit or its baseline is missing"
/bin/cp "$AUDIT_SRC" "$TMP/frozen_key_audit.py"; /bin/cp "$BASE_SRC" "$TMP/baseline.json"
[[ "$(sha "$TMP/frozen_key_audit.py")" == "$AUDIT_SHA" ]] || die "the frozen-key audit is not the pinned $AUDIT_SHA"
[[ "$(sha "$TMP/baseline.json")" == "$BASE_SHA" ]] || die "the frozen-key baseline is not the pinned $BASE_SHA"
(cd "$TMP/empty" && "$PY" -I "$TMP/frozen_key_audit.py" --check "$TMP/baseline.json" "$WT") \
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
(cd "$TMP/empty" && "$PY" -I -P - "$WT/$TEAM" "$ACTION" "$WT/$LOG" "$WT/$SPEC" "$WT") <<'PYEOF' || die "verification failed; do not commit; undo: $UNDO ; paste this output to the session"
import csv, json, subprocess, sys
from pathlib import Path
from agentteams.cli.security_gate import check_clearance
team, action, log, spec_path, wt = sys.argv[1:6]
git = ["/usr/bin/git", "--no-pager", "-C", wt, "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null"]
old = subprocess.run(git + ["show", "HEAD:.github/agents/references/security-decisions.log.csv"], capture_output=True, check=True).stdout.replace(b"\r", b"")
new = Path(log).read_bytes().replace(b"\r", b"")
csv.field_size_limit(10**8)
with open(log, newline="", encoding="utf-8") as fh:
    rows = [r for r in csv.DictReader(fh) if (r.get("action_reviewed") or "") == action]
one = len(rows) == 1 and rows[0].get("key_id") == "opr-2026-11" and rows[0].get("sig_scheme") == "ed25519" \
    and rows[0].get("derives_from") == "release-policy-1.0" and rows[0].get("verdict") == "PASS" \
    and (rows[0].get("effect_destructive") or "") == "true" and not (rows[0].get("effect_relaxes") or "").strip() \
    and not (rows[0].get("effect_grants") or "").strip() and not (rows[0].get("effect_targets") or "").strip()
spec = json.load(open(spec_path, encoding="utf-8"))
same = one and all((rows[0].get(k) or "") == (spec.get(k) or "") for k in
                   ("timestamp", "date", "requesting_agent", "author", "scope", "verdict", "conditions",
                    "conditions_verified", "evidence", "effect_targets", "effect_relaxes", "effect_grants",
                    "effect_destructive", "effect_cross_repo", "effect_bulk", "derives_from"))
ok, why = check_clearance(Path(team), action=action)
print(f"   {action}: {'CLEARS' if ok else 'NOT CLEARED: ' + str(why)[:200]} | one opr-2026-11 destructive row, relaxes and grants nothing: {one} | row equals the spec: {same} | log is the committed bytes plus one appended row: {new.startswith(old)}")
sys.exit(0 if ok and one and same and new.startswith(old) else 1)
PYEOF
out=$("$AT" --verify-integrity --output "$TEAM" 2>&1) \
  || { printf '%s\n' "$out"; die "--verify-integrity fails after signing; do not commit; undo: $UNDO"; }
printf '== --verify-integrity (%s): exit 0\n' "$TEAM"
out=$("$AT" --verify-toolchain-group --output "$TEAM" --description brief.json 2>&1) \
  || { printf '%s\n' "$out"; die "the toolchain group no longer verifies; do not commit; undo: $UNDO"; }
printf '%s\n' "$out" | /usr/bin/head -1
for f in "$F1" "$F2"; do [[ "$(sha "$f")" == "$KEY_SHA" ]] || die "$f changed; do not commit"; done
changed="$("${G[@]}" status --porcelain --untracked-files=all)"
[[ "$changed" == " M $LOG" ]] || die "unexpected changes in the worktree (expected only $LOG): $changed ; do not commit; undo: $UNDO"
"${G[@]}" diff --stat
printf '== done: 1 row signed; nothing removed, committed or pushed. Paste this output into the researchteam session.\n'
printf '   The session commits the row on %s and reports the new head for script 34.\n' "$BRANCH"
