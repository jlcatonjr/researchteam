#!/bin/bash -p
# 25 — Key rotation: re-sign researchteam's rows that are still needed with the operator's new Ed25519 decision key
# opr-2026-11, each under its same action id and with a byte-identical derives_from. One run, seven signing prompts:
#   .github/agents log: release-policy-1.0 (first: the others derive from it), s10-first-party-releases-2026-11,
#     management-roster-enroll:infrastructure-management, term-index-2026-11, release-line-agentteams-1.2,
#     repo-setting:delete-branch-on-merge:jlcatonjr/researchteam;
#   .codex/agents log:  release-policy-1.0.
# Not re-signed (operator, session picker, 2026-11-22): fleet-agent-pilot-2026-11 (lapses; a new authorization under a
# new id follows) and codex-orchestrator-only-native-render (lapses). Earlier lines' rows are history.
# NOT done here: the toolchain group file is not signed; op-2026 is not removed; nothing is committed or pushed.
# The specs and this file are modelled on the run another of the operator's repositories made for the same rotation.
#
# OPERATOR ONLY, plain Terminal, from any directory, ALWAYS as /bin/bash -p. HEAD is the 40-hex commit the session
# reports for branch governance/key-rotation-resign:
#   CHECK_ONLY=1 /bin/bash -p <this file> <HEAD>     every check; prints each payload, declines it; the key is not read
#   /bin/bash -p <this file> <HEAD>                   the real run; each "Sign this payload? [y/N]" is yours to answer
# Before each y, check: key_id opr-2026-11; the action id named in the ==== header; derives_from release-policy-1.0
# (none for release-policy-1.0 and s10-first-party-releases-2026-11); verdict PASS; the date in the signature values
# is 2026-11-22.
# If the run stops part-way, run it again: an id whose latest row is already this re-sign is skipped.
[[ $- == *p* ]] || { printf 'STOP: run this as /bin/bash -p <path> <HEAD>\n' >&2; exit 1; }
set -euo pipefail
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
die() { printf 'STOP: %s\n' "$*" >&2; exit 1; }
[[ -z "${CLAUDECODE:-}${CLAUDE_CODE_ENTRYPOINT:-}${CODEX_SANDBOX:-}" ]] || die "run this in your own terminal, not an agent session"
[[ -t 0 && -t 1 ]] || die "run this in a terminal"
[[ -z "${ASSUME_YES:-}" ]] || die "ASSUME_YES is refused: each signing prompt is yours to answer"
[[ -z "${CHECK_ONLY:-}" || "${CHECK_ONLY:-}" == 1 ]] || die "CHECK_ONLY must be unset or 1"
if [[ "${_RT_RESIGN_CLEAN:-}" != 1 ]]; then
  exec /usr/bin/env -i _RT_RESIGN_CLEAN=1 HOME="$HOME" USER="${USER:-}" LOGNAME="${LOGNAME:-}" TERM="${TERM:-xterm}" \
      CHECK_ONLY="${CHECK_ONLY:-}" PATH=/usr/bin:/bin:/usr/sbin:/sbin /bin/bash -p "$0" "$@"
fi
for v in $(compgen -e); do
  case "$v" in _RT_RESIGN_CLEAN|HOME|USER|LOGNAME|TERM|CHECK_ONLY|PATH|PWD|OLDPWD|SHLVL|_) ;;
    *) die "unexpected environment variable $v in the clean stage" ;; esac
done
[[ -z "$(declare -F | /usr/bin/grep -v -E ' die$')" ]] || die "an unexpected shell function exists in the clean stage"
CHECK_ONLY="${CHECK_ONLY:-}"
[[ $# -eq 1 && "$1" =~ ^[0-9a-f]{40}$ ]] || die "give the reviewed head as one full 40-hex SHA"
HEAD_WANT="$1"

WT="$HOME/githubrepositories/researchteam-wt-survey-toolkit"
BRANCH=governance/key-rotation-resign
DATE=2026-11-22
VENV="<signer>"                # root-owned install built from agentteams tag v1.2.1 on python.org 3.13; the real path is only in the copy the operator ran
BASEPY=/Library/Frameworks/Python.framework/Versions/3.13
AT="$VENV/bin/agentteams"; PY="$VENV/bin/python"
KEY="<decision-key-file>"      # the operator's opr-2026-11 private key; the real path is only in the copy the operator ran
[[ "$VENV" != "<"* && "$KEY" != "<"* ]] || die "this is the tracked record of the script (run on 2026-11-22 at head fc242f3, sha256 8cab1c65...808fd9); it has placeholders and does not run"
PUB_SHA=d22faa83b674abe6b1e3207a4f13fc17c5ddd367e35e0c60c69163eddbd9dab7
# The frozen-key audit is run from the coordinating repository's checkout, pinned by hash; it is not vendored here.
AUDIT_SRC="$HOME/githubrepositories/infrastructureManagement/scripts/frozen_key_audit.py"
AUDIT_SHA=b85de5e31c74124f6722fd84f4590db70cd23b8a5a9bd46939d051ff0f6697a6
BASE_SRC="$HOME/githubrepositories/infrastructureManagement/references/frozen-key-baseline-2026-11-21b.json"
BASE_SHA=7406903c1172d90864f009f5b8dc4761e82115a8cbc2bb5d9c0b70e983f6cf56
S=docs/release/key-rotation-2026-11
# team dir | spec (without .decision-spec.json) | spec sha256 | action id
PLAN=(
".github/agents|release-policy-1.0|5717cbe058659f8d9d1a6517c45eed4868802a93b516523a04c0535ef4a95f4a|release-policy-1.0"
".github/agents|s10-first-party-releases-2026-11|557770db958ad1e43515c38f9bff1bd2ff0f9f0d561851369e7cf25b7ebd4d33|s10-first-party-releases-2026-11"
".github/agents|management-roster-enroll-infrastructure-management|7bbfdc8f9391a1c443eb473c972d0768a744ff0b2a738bca8d4854f805a5c05a|management-roster-enroll:infrastructure-management"
".github/agents|term-index-2026-11|a5a81efee346849a39121db588bae52e7e71253d511d42b2b66769f6bba9e27c|term-index-2026-11"
".github/agents|release-line-agentteams-1.2|11357235904b0962348f512bf4ba1495d575b92628188dbeb438f9ee23b746ec|release-line-agentteams-1.2"
".github/agents|repo-setting-delete-branch-on-merge-jlcatonjr-researchteam|0b3ca3bdfdd091a592538187a24bdefc5323c8c3398226b3e4c183a80dbf753b|repo-setting:delete-branch-on-merge:jlcatonjr/researchteam"
".codex/agents|release-policy-1.0|5717cbe058659f8d9d1a6517c45eed4868802a93b516523a04c0535ef4a95f4a|release-policy-1.0"
)
LOGS=(.github/agents/references/security-decisions.log.csv .codex/agents/references/security-decisions.log.csv)
G=(/usr/bin/git --no-pager -c core.fsmonitor=false -c core.hooksPath=/dev/null -c core.pager=cat)
sha() { /usr/bin/shasum -a 256 "$1" | /usr/bin/cut -d' ' -f1; }
[[ "$(/bin/date +%Y-%m-%d)" == "$DATE" ]] || die "today is not $DATE: the specs carry the signing day, so the session must regenerate them"

# 0. The signer: root-owned agentteams 1.2.1 on the root-owned python.org 3.13.
[[ -x "$AT" && -x "$PY" ]] || die "the clean signer $VENV is missing"
bad=$(/usr/bin/find "$VENV" "$BASEPY" \( ! -user root -o \( ! -type l \( -perm -0020 -o -perm -0002 \) \) \) -print 2>&1 | /usr/bin/head -3)
[[ -z "$bad" ]] || die "the signer or its base Python has an entry that is not root-owned or is group/world-writable: $bad"
"$AT" --version | /usr/bin/grep -q '^agentteams 1\.2\.1' || die "$AT is not agentteams 1.2.1"
base=$("$PY" -I -c 'import sys; print(sys.base_prefix)')
[[ "$base" == "$BASEPY" ]] || die "the signer's base Python is $base, not $BASEPY"
printf '== signer: agentteams 1.2.1, root-owned, base %s\n' "$base"

# 1. The worktree, the specs, the stores and the key.
[[ -d "$WT" && ! -L "$WT" ]] || die "no worktree at $WT"
cd "$WT"
[[ "$("${G[@]}" branch --show-current)" == "$BRANCH" ]] || die "$WT is not on $BRANCH"
[[ "$("${G[@]}" rev-parse HEAD)" == "$HEAD_WANT" ]] || die "HEAD is $("${G[@]}" rev-parse HEAD), not the reviewed $HEAD_WANT"
# Clean, or (resuming after a part-run) only the two logs modified, each its committed bytes plus appended rows.
dirty=$("${G[@]}" status --porcelain --untracked-files=all)
if [[ -n "$dirty" ]]; then
  while IFS= read -r line; do
    case "$line" in
      " M .github/agents/references/security-decisions.log.csv"|" M .codex/agents/references/security-decisions.log.csv") ;;
      *) die "the worktree has an unexpected change: $line" ;;
    esac
  done <<<"$dirty"
  for l in "${LOGS[@]}"; do
    "$PY" -I -c 'import subprocess,sys
old=subprocess.run(["/usr/bin/git","--no-pager","-c","core.fsmonitor=false","-c","core.hooksPath=/dev/null","show","HEAD:"+sys.argv[1]],capture_output=True,check=True).stdout.replace(b"\r",b"")
new=open(sys.argv[1],"rb").read().replace(b"\r",b"")
sys.exit(0 if new.startswith(old) else 1)' "$l" || die "$l is not its committed bytes plus appended rows"
  done
  printf '== resuming: a log holds appended rows from an earlier part-run\n'
fi
for e in "${PLAN[@]}"; do IFS='|' read -r d id want aid <<<"$e"
  f="$S/$id.decision-spec.json"
  [[ -f "$f" && ! -L "$f" && "$(sha "$f")" == "$want" ]] || die "$f is not the reviewed $want"
  /usr/bin/grep -qF "\"action_reviewed\": \"$aid\"" "$f" || die "$f is not for $aid"
  /usr/bin/grep -qF '"key_id": "opr-2026-11"' "$f" || die "$f does not name key opr-2026-11"
  /usr/bin/grep -qF "\"date\": \"$DATE\"" "$f" || die "$f is not dated $DATE"
done
for d in .github/agents .codex/agents; do
  p="$d/references/authorized-verify-keys"
  [[ -f "$p/opr-2026-11.pub.pem" && ! -L "$p/opr-2026-11.pub.pem" && "$(sha "$p/opr-2026-11.pub.pem")" == "$PUB_SHA" ]] \
    || die "$p/opr-2026-11.pub.pem is not $PUB_SHA"
  [[ -z "$("${G[@]}" status --porcelain --untracked-files=all -- "$p")" ]] || die "$p differs from the commit"
done
[[ -f "$KEY" && ! -L "$KEY" && "$(/usr/bin/stat -f %Lp "$KEY")" == 600 ]] || die "$KEY is missing, a link, or not mode 600"
if [[ "$CHECK_ONLY" == 1 ]]; then
  printf '== CHECK_ONLY: the private key is not read (presence and mode 600 checked only)\n'
else
  have=$("$PY" -I -c 'import sys
from cryptography.hazmat.primitives import serialization as s
k=s.load_pem_private_key(open(sys.argv[1],"rb").read(),None)
sys.stdout.buffer.write(k.public_key().public_bytes(s.Encoding.PEM,s.PublicFormat.SubjectPublicKeyInfo))' "$KEY" 2>/dev/null \
        | /usr/bin/shasum -a 256 | /usr/bin/cut -d' ' -f1)
  empty=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855   # sha256 of no output: the key could not be loaded without a passphrase
  if [[ "$have" == "$empty" ]]; then
    printf '== the key file is passphrase-protected or unreadable here, so it is not compared now; step 4 checks every new row against the committed public key\n'
  else
    [[ "$have" == "$PUB_SHA" ]] || die "$KEY is not the private key for the committed opr-2026-11 public key"
    printf '== the key matches the committed opr-2026-11 public key %s\n' "${PUB_SHA:0:12}"
  fi
fi
printf '== inputs OK: head %s, 6 specs, 7 signatures\n' "${HEAD_WANT:0:8}"

# 2. The frozen-key audit (fail-closed preflight), from private copies checked by hash. 0 clean, 1 forged?, 2 could not run.
TMP=$(/usr/bin/mktemp -d); trap '/bin/rm -rf "$TMP"' EXIT
/bin/chmod 700 "$TMP"
[[ -f "$AUDIT_SRC" && ! -L "$AUDIT_SRC" && -f "$BASE_SRC" && ! -L "$BASE_SRC" ]] || die "the frozen-key audit or its baseline is missing"
/bin/cp "$AUDIT_SRC" "$TMP/frozen_key_audit.py"; /bin/cp "$BASE_SRC" "$TMP/baseline.json"
[[ "$(sha "$TMP/frozen_key_audit.py")" == "$AUDIT_SHA" ]] || die "the frozen-key audit is not the pinned $AUDIT_SHA"
[[ "$(sha "$TMP/baseline.json")" == "$BASE_SHA" ]] || die "the frozen-key baseline is not the pinned $BASE_SHA"
"$BASEPY/bin/python3" -I "$TMP/frozen_key_audit.py" --check "$TMP/baseline.json" "$WT" \
  || die "the frozen-key audit did not pass (exit $?); nothing was signed; paste this output to the session"
printf '== frozen-key audit: clean\n'

# 3. Sign. An id whose latest row is already this re-sign (key opr-2026-11, dated today) is skipped (resume).
for l in "${LOGS[@]}"; do /bin/cp -p "$l" "$TMP/before-${l//\//_}"; done
done_already() {  # $1 team dir, $2 action id
  "$PY" -I -c 'import csv,sys
rows=[r for r in csv.DictReader(open(sys.argv[1]+"/references/security-decisions.log.csv",newline="")) if r.get("action_reviewed")==sys.argv[2]]
sys.exit(0 if rows and rows[-1].get("key_id")=="opr-2026-11" and rows[-1].get("date")==sys.argv[3] else 1)' "$1" "$2" "$DATE"
}
for e in "${PLAN[@]}"; do IFS='|' read -r d id want aid <<<"$e"
  if done_already "$d" "$aid"; then printf '\n== already signed, skipped: %s (%s)\n' "$aid" "$d"; continue; fi
  printf '\n================ %s  (into %s/references/security-decisions.log.csv)\n' "$aid" "$d"
  if [[ "$CHECK_ONLY" == 1 ]]; then
    printf 'n\n' | AGENTTEAMS_DECISION_ED25519_KEYFILE="$KEY" "$AT" --sign-decision "$S/$id.decision-spec.json" --output "$d" || true
  else
    AGENTTEAMS_DECISION_ED25519_KEYFILE="$KEY" "$AT" --sign-decision "$S/$id.decision-spec.json" --output "$d" \
      || die "signing $aid failed or was declined; rows signed before it stay in the log, uncommitted. Run again to resume, or paste this output to the session"
  fi
done
if [[ "$CHECK_ONLY" == 1 ]]; then
  for l in "${LOGS[@]}"; do /usr/bin/cmp -s "$TMP/before-${l//\//_}" "$l" || die "CHECK_ONLY changed $l; restore it with git checkout"; done
  printf '\nCHECK_ONLY: every check passed; nothing was signed and the key was not read.\n'; exit 0
fi

# 4. Verify: each log is its committed bytes plus appended rows only; exactly the expected ids were appended; each id's
#    latest row is the re-sign, clears, and has the derives_from of the row it replaces; the registry is untouched.
"$PY" -I - <<'EOF' || die "verification failed (the rows stay in the logs, uncommitted; paste this output to the session)"
import csv, subprocess, sys
from pathlib import Path
from agentteams.cli.security_gate import check_clearance
want = {".github/agents": ["release-policy-1.0", "s10-first-party-releases-2026-11",
                           "management-roster-enroll:infrastructure-management", "term-index-2026-11",
                           "release-line-agentteams-1.2", "repo-setting:delete-branch-on-merge:jlcatonjr/researchteam"],
        ".codex/agents": ["release-policy-1.0"]}
git = ["/usr/bin/git", "--no-pager", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null"]
bad = 0
for d, ids in want.items():
    log = f"{d}/references/security-decisions.log.csv"
    old = subprocess.run(git + ["show", f"HEAD:{log}"], capture_output=True, check=True).stdout.replace(b"\r", b"")
    new = Path(log).read_bytes().replace(b"\r", b"")
    if not new.startswith(old):
        print(f"   {log}: the committed log is not a byte prefix of the new one"); bad += 1; continue
    rows = list(csv.DictReader(open(log, newline="")))
    oldrows = list(csv.DictReader(old.decode("utf-8").splitlines(keepends=True)))
    extra = [r["action_reviewed"] for r in rows[len(oldrows):]]
    if sorted(extra) != sorted(ids):
        print(f"   {log}: appended {extra}, expected {ids}"); bad += 1
    for a in ids:
        prev = [r for r in oldrows if r["action_reviewed"] == a][-1]
        cur = [r for r in rows if r["action_reviewed"] == a][-1]
        ok, why = check_clearance(Path(d), action=a)
        same = cur.get("derives_from", "") == prev.get("derives_from", "")
        spent = (cur.get("consumed") or "").strip()
        print(f"   {d} {a}: {'CLEARED' if ok else 'NOT CLEARED: ' + str(why)[:200]} | key {cur.get('key_id')} | "
              f"derives_from identical: {same} | consumed: {spent or 'no'}")
        bad += (not ok) + (not same) + (cur.get("key_id") != "opr-2026-11") + bool(spent)
reg = ".github/agents/references/exception-registry.json"
if subprocess.run(git + ["diff", "--quiet", "HEAD", "--", reg, ".agentteams"]).returncode != 0:
    print(f"   {reg} or .agentteams changed; they must not"); bad += 1
sys.exit(1 if bad else 0)
EOF
out=$("$AT" --verify-toolchain-group --output .github/agents --description brief.json 2>&1) \
  || { printf '%s\n' "$out"; die "the toolchain group no longer verifies (paste this output to the session)"; }
printf '%s\n' "$out" | /usr/bin/tail -1
dirty=$("${G[@]}" status --porcelain --untracked-files=all)
while IFS= read -r line; do
  case "$line" in
    " M .github/agents/references/security-decisions.log.csv"|" M .codex/agents/references/security-decisions.log.csv") ;;
    *) die "after signing, the worktree has an unexpected change: $line" ;;
  esac
done <<<"$dirty"
"${G[@]}" diff --stat
printf '== done: 7 rows signed with opr-2026-11; nothing committed or pushed. Paste this output into the researchteam session.\n'
