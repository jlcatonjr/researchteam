#!/bin/bash -p
# 26 — Sign the standing authorization for the fleet-agent GitHub App on researchteam (Tier 1 only, no merges,
# expiring 2027-02-18), set the exception cap to two, and register the row in the exception registry. One run:
#   1. checks (signer, worktree at the reviewed head, spec hash, frozen-key audit, no HALT, registry state);
#   2. YOUR read-back of the App's installation in GitHub's settings, confirmed at a prompt;
#   3. one signing prompt (key opr-2026-11);
#   4. the registry: cap.max_active_relaxing 2 and one new active entry bound to the signed row, in one step;
#   5. verification. Nothing is committed or pushed; no GitHub setting is changed.
# If you decline at step 2 or 3, nothing has changed. If step 4 or 5 fails, undo with the command the script prints.
#
# OPERATOR ONLY, plain Terminal, from any directory, ALWAYS as /bin/bash -p. HEAD is the 40-hex commit the session
# reports for branch governance/fleet-agent-tier1:
#   CHECK_ONLY=1 /bin/bash -p <this file> <HEAD>     every check; prints the payload and declines it; changes nothing
#   /bin/bash -p <this file> <HEAD>                   the real run
# Before answering y at "Sign this payload?", check: key_id opr-2026-11; action fleet-agent-tier1:jlcatonjr/researchteam;
# derives_from release-policy-1.0; verdict PASS; grants ['fleet-agent-jlcatonjr']; relaxes that action id only; the
# date in the signature values is 2026-11-23.
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


WT="$HOME/githubrepositories/researchteam-wt-survey-toolkit"
BRANCH=governance/fleet-agent-tier1
DATE=2026-11-23
EXPIRES=2027-02-18T23:59:59+00:00
ACTION="fleet-agent-tier1:jlcatonjr/researchteam"
OTHER="repo-setting:delete-branch-on-merge:jlcatonjr/researchteam"
TEAM=.github/agents
SPEC=docs/release/fleet-agent-tier1.decision-spec.json
SPEC_SHA=109891cb775684a4f985a826dca18a7a53b3cc9aaa29216a3b44107a37445b63
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
REG="$TEAM/references/exception-registry.json"
G=(/usr/bin/git --no-pager -c core.fsmonitor=false -c core.hooksPath=/dev/null -c core.pager=cat)
sha() { /usr/bin/shasum -a 256 "$1" | /usr/bin/cut -d' ' -f1; }
UNDO="/usr/bin/git -C $WT checkout -- $LOG $REG"
[[ "$(/bin/date +%Y-%m-%d)" == "$DATE" ]] || die "today is not $DATE: the spec carries the signing day, so the session must regenerate it"

# 0. The signer: root-owned agentteams 1.2.1 on the root-owned python.org 3.13.
[[ -x "$AT" && -x "$PY" ]] || die "the clean signer is missing"
bad=$(/usr/bin/find "$VENV" "$BASEPY" \( ! -user root -o \( ! -type l \( -perm -0020 -o -perm -0002 \) \) \) -print 2>&1 | /usr/bin/head -3)
[[ -z "$bad" ]] || die "the signer or its base Python has an entry that is not root-owned or is group/world-writable: $bad"
"$AT" --version | /usr/bin/grep -q '^agentteams 1\.2\.1' || die "the signer is not agentteams 1.2.1"
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
/usr/bin/grep -qF "\"effect_relaxes\": \"$ACTION\"" "$SPEC" || die "$SPEC does not relax exactly $ACTION"
/usr/bin/grep -qF '"effect_grants": "fleet-agent-jlcatonjr"' "$SPEC" || die "$SPEC does not grant exactly fleet-agent-jlcatonjr"
/usr/bin/grep -qF '"derives_from": "release-policy-1.0"' "$SPEC" || die "$SPEC does not derive from release-policy-1.0 alone"
/usr/bin/grep -qF '"key_id": "opr-2026-11"' "$SPEC" || die "$SPEC does not name key opr-2026-11"
/usr/bin/grep -qF "\"date\": \"$DATE\"" "$SPEC" || die "$SPEC is not dated $DATE"
/usr/bin/grep -qF '"verdict": "PASS"' "$SPEC" || die "$SPEC verdict is not PASS"
/usr/bin/grep -qF "expiring ${EXPIRES%%T*}" "$SPEC" || die "$SPEC does not state the expiry ${EXPIRES%%T*}"
p="$TEAM/references/authorized-verify-keys/opr-2026-11.pub.pem"
[[ -f "$p" && ! -L "$p" && "$(sha "$p")" == "$PUB_SHA" ]] || die "$p is not $PUB_SHA"
[[ -f "$KEY" && ! -L "$KEY" && "$(/usr/bin/stat -f %Lp "$KEY")" == 600 ]] || die "the key file is missing, a link, or not mode 600"
/usr/bin/grep -qF ",$ACTION," "$LOG" && die "a row for $ACTION is already in $LOG; nothing to do"
if /usr/bin/grep -E ',fleet-agent[^,]*,HALT,' "$LOG" >/dev/null; then die "a HALT on a fleet-agent action is recorded; do not sign"; fi
(cd / && "$PY" -I -P - "$WT/$TEAM" "$OTHER") <<'PYEOF' || die "the registry is not in the expected state (cap at the default, exactly one active relaxing exception: branch deletion); nothing changed"
import sys
from pathlib import Path
from agentteams.cli.exception_registry import load_registry, active_relaxing_exceptions, audit_exceptions, _configured_cap
root, other = Path(sys.argv[1]), sys.argv[2]
reg = load_registry(root)
active = [e.get("action") for e in active_relaxing_exceptions(reg)]
problems = audit_exceptions(root)
print("  registry: cap", _configured_cap(reg), "| active relaxing:", active, "| audit:", "clean" if not problems else problems)
sys.exit(0 if _configured_cap(reg) == 1 and active == [other] and not problems else 1)
PYEOF
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
  printf '\nCHECK_ONLY: every check passed; nothing was signed, the key was not read, the registry is unchanged.\n'; exit 0
fi

# 3. Your read-back of the App's installation. The session cannot read it; the row rests on this answer.
printf '\n== Read the installation now: GitHub > Settings > Applications > Installed GitHub Apps > fleet-agent-jlcatonjr > Configure.\n'
printf '   It must show, and nothing more:\n'
printf '     Repository permissions: Contents read and write; Issues read and write; Pull requests read and write;\n'
printf '                             Checks read; Actions read; Metadata read.\n'
printf '     Repository access: selected repositories, with jlcatonjr/researchteam among them.\n'
read -r -p "Does the installation show exactly those permissions, and list jlcatonjr/researchteam? [y/N] " ok
[[ "$ok" == "y" ]] || { printf 'Not confirmed. Nothing was signed and nothing changed. Tell the session what the page shows.\n'; exit 0; }

# 4. Sign (one prompt from agentteams), then set the cap and register in one step.
n0=$(/usr/bin/wc -l < "$LOG")
printf '\n================ %s  (into %s)\n' "$ACTION" "$LOG"
AGENTTEAMS_DECISION_ED25519_KEYFILE="$KEY" "$AT" --sign-decision "$SPEC" --output "$TEAM" \
  || die "signing failed or was declined; if $LOG changed, undo: $UNDO"
n1=$(/usr/bin/wc -l < "$LOG")
[[ $((n1 - n0)) -eq 1 ]] || die "the signer changed the log by $((n1 - n0)) lines (expected 1); do not commit; undo: $UNDO"
(cd / && "$PY" -I -P - "$WT/$TEAM" "$ACTION" "$EXPIRES" "$OTHER") <<'PYEOF' || die "setting the cap or registering failed; do not commit; undo: $UNDO ; paste this output to the session"
import csv, sys
from datetime import datetime, timezone
from pathlib import Path
from agentteams.cli.exception_registry import (register_exception, audit_exceptions, load_registry, write_registry,
                                               active_relaxing_exceptions, _configured_cap)
from agentteams.cli.s10_exempt_gate import _decision_binding, _split
from agentteams.cli.effect_classifier import derive_effect_class, requires_operator_signature
root, action, expires, other = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
csv.field_size_limit(10**8)
with open(root / "references" / "security-decisions.log.csv", newline="", encoding="utf-8") as fh:
    rows = [r for r in csv.DictReader(fh) if (r.get("action_reviewed") or "") == action]
assert len(rows) == 1, f"expected exactly one row for {action}, found {len(rows)}"
row = rows[0]
assert row.get("verdict") == "PASS" and row.get("sig_scheme") == "ed25519" and (row.get("signature") or "").strip(), "the row is not an Ed25519-signed PASS"
assert row.get("key_id") == "opr-2026-11", "the row is not signed with opr-2026-11"
assert requires_operator_signature(row, kind="decision"), "the signed row is not classified as needing the operator's signature"
print("  effect class:", derive_effect_class(row, kind="decision"))
before = load_registry(root)
seq = before.get("toolchain_group_sequence")
kept = [e for e in before["exceptions"]]
assert _configured_cap(before) == 1 and [e.get("action") for e in active_relaxing_exceptions(before)] == [other]
before["cap"] = {"max_active_relaxing": 2}
write_registry(root, before)
entry_id = f"{action}@{row['signature'].strip()[:16]}"
register_exception(root, {
    "id": entry_id, "action": action, "kind": "fleet-agent-tier1", "scope": action, "relaxing": True,
    "effect": {"relaxes": [action], "grants": ["fleet-agent-jlcatonjr"]},
    "lineage": sorted(_split(row.get("derives_from") or "")),
    "issued": datetime.now(timezone.utc).isoformat(),
    "expires": expires,
    "decision_key_id": row["key_id"].strip(),
    "decision_sha256": _decision_binding(row),
})
reg = load_registry(root)
assert reg.get("toolchain_group_sequence") == seq, "toolchain_group_sequence changed"
assert _configured_cap(reg) == 2, "the cap is not 2"
assert reg["exceptions"][:len(kept)] == kept, "an existing registry entry changed"
assert len(reg["exceptions"]) == len(kept) + 1, "the registry did not gain exactly one entry"
active = sorted(e.get("action") for e in active_relaxing_exceptions(reg))
assert active == sorted([action, other]), f"unexpected active set: {active}"
problems = audit_exceptions(root)
print("  cap: 2 | registered:", entry_id, "| expires:", expires, "| active:", active)
print("  audit:", "clean" if not problems else problems)
sys.exit(0 if not problems else 1)
PYEOF

# 5. Verify.
[[ "$(/usr/bin/wc -l < "$LOG")" -eq "$n1" ]] || die "registering changed the log; do not commit; undo: $UNDO"
"$PY" -I - "$TEAM" "$ACTION" "$LOG" <<'PYEOF' || die "verification failed; do not commit; undo: $UNDO ; paste this output to the session"
import subprocess, sys
from pathlib import Path
from agentteams.cli.security_gate import check_clearance
team, action, log = sys.argv[1], sys.argv[2], sys.argv[3]
git = ["/usr/bin/git", "--no-pager", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null"]
old = subprocess.run(git + ["show", f"HEAD:{log}"], capture_output=True, check=True).stdout.replace(b"\r", b"")
new = Path(log).read_bytes().replace(b"\r", b"")
ok, why = check_clearance(Path(team), action=action)
print(f"   {action}: {'CLEARED' if ok else 'NOT CLEARED: ' + str(why)[:200]} | log is the committed bytes plus appended rows: {new.startswith(old)}")
sys.exit(0 if ok and new.startswith(old) else 1)
PYEOF
out=$("$AT" --verify-toolchain-group --output "$TEAM" --description brief.json 2>&1) \
  || { printf '%s\n' "$out"; die "the toolchain group no longer verifies; do not commit; undo: $UNDO"; }
printf '%s\n' "$out" | /usr/bin/tail -1
changed="$("${G[@]}" status --porcelain --untracked-files=all)"
[[ "$changed" == " M $LOG"$'\n'" M $REG" ]] || die "unexpected changes in the worktree (expected only $LOG and $REG): $changed ; do not commit; undo: $UNDO"
"${G[@]}" diff --stat
printf '== done: 1 row signed, cap 2, 2 active exceptions; nothing committed or pushed. Paste this output into the researchteam session.\n'
