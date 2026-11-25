#!/bin/bash -p
# 20 — P3 option A, step 1 of 2 for the operator: make room in the exception registry and sign the decision.
# OPERATOR ONLY. Same hardened preamble as 14-sign-release-line-1.2.sh.
#   a) retires the registry entry s10-cooldown-exempt:jlcatonjr/agentteams (redundant: the operator-signed first-party
#      toolchain group already lifts the S-10 cooldown for agentteams). It is retired in the registry, NEVER by a HALT:
#      a HALT on any s10-cooldown-exempt action would end the toolchain group.
#   b) signs the row repo-setting:delete-branch-on-merge:jlcatonjr/researchteam (PASS, relaxing, 90-day sunset) from the
#      decision spec at the reviewed head of governance/ps2-auto-branch-delete;
#   c) registers that row in the exception registry (the one active relaxing slot) and audits the registry.
# It changes NO GitHub setting (that is 21-enable-delete-branch-on-merge.sh, after the PR merges) and COMMITS NOTHING:
# the researchteam session commits the log and registry changes, pushes them to the PR, and asks for the merge.
# Usage (plain Terminal, from any directory; ALWAYS `/bin/bash -p <path>`, never `bash <path>`):
#   /bin/bash -p ~/githubrepositories/researchteam/tmp/by-week/2026-W47/operator/20-retire-sign-register.sh <40-hex head the session reports>
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

HEAD_REVIEWED="${1:?usage: $0 <40-hex reviewed head of governance/ps2-auto-branch-delete>}"
WT="$HOME/githubrepositories/researchteam-wt-ps2"
ACTION="repo-setting:delete-branch-on-merge:jlcatonjr/researchteam"
OLD_ID="s10-cooldown-exempt:jlcatonjr/agentteams@f5d9d6208ef25045"
EXPIRES="2027-02-18T23:59:59+00:00"
BR="governance/ps2-auto-branch-delete"
TEAM=".github/agents"
SIGNER="<signer>"     # root-owned install built from agentteams tag v1.1.4; agentteams refuses a signer under $HOME
KEYFILE="$HOME/.config/agentteams/keys/decision-signing-op-2026.pem"
[[ "$HEAD_REVIEWED" =~ ^[0-9a-f]{40}$ ]] || die "the head must be a full 40-hex SHA"
[[ -x "$SIGNER" ]] || die "no root-owned signer at $SIGNER"
[[ "$(/usr/bin/stat -f %Su "$SIGNER")" == root ]] || die "$SIGNER is not root-owned"
[[ -f "$KEYFILE" ]] || die "missing $KEYFILE"
PY="${SIGNER%/agentteams}/python"   # the signer install's own interpreter: root-owned, so no agent session can have changed the code it runs
[[ -x "$PY" ]] || die "no interpreter beside the signer at $PY"
[[ "$(/usr/bin/stat -f %Su "$PY")" == root ]] || die "$PY is not root-owned"
[[ -d "$WT" ]] || die "no worktree at $WT"

cd "$WT"
[[ "$("${GIT[@]}" rev-parse --abbrev-ref HEAD)" == "$BR" ]] || die "$WT is not on $BR"
[[ "$("${GIT[@]}" rev-parse HEAD)" == "$HEAD_REVIEWED" ]] || die "$BR is at $("${GIT[@]}" rev-parse HEAD), not the reviewed $HEAD_REVIEWED"
[[ -z "$("${GIT[@]}" status --porcelain)" ]] || die "$WT has uncommitted changes; stop"
log="$TEAM/references/security-decisions.log.csv"
reg="$TEAM/references/exception-registry.json"
TMP=$(/usr/bin/mktemp -d); trap 'rm -rf "$TMP"' EXIT
EMPTY="$TMP/empty"; /bin/mkdir "$EMPTY"   # signer, gate check and registry calls run from an empty cwd; the keyfile variable is never exported
SPEC="docs/release/repo-setting-delete-branch-on-merge.decision-spec.json"

echo; echo "== researchteam: $ACTION"
if /usr/bin/grep -qF ",$ACTION," "$log"; then echo "  already in $log; nothing to sign"; exit 0; fi
"${GIT[@]}" show "$HEAD_REVIEWED:$SPEC" > "$TMP/spec.json" 2>/dev/null || die "no $SPEC at the head"
/usr/bin/grep -qE '<[A-Z_]+>' "$TMP/spec.json" && die "$SPEC still has a placeholder"
/usr/bin/grep -qF "\"action_reviewed\": \"$ACTION\"" "$TMP/spec.json" || die "$SPEC is not for $ACTION"
/usr/bin/grep -qF "\"scope\": \"$ACTION\"" "$TMP/spec.json" || die "$SPEC scope is not $ACTION"
/usr/bin/grep -qF "\"effect_relaxes\": \"$ACTION\"" "$TMP/spec.json" || die "$SPEC does not relax exactly $ACTION"
/usr/bin/grep -qF '"effect_grants": ""' "$TMP/spec.json" || die "$SPEC grants something; it must grant nothing"
/usr/bin/grep -qF '"effect_targets": ""' "$TMP/spec.json" || die "$SPEC names a target; it must name none"
/usr/bin/grep -qF '"effect_destructive": "true"' "$TMP/spec.json" || die "$SPEC is not marked destructive"
/usr/bin/grep -qF '"verdict": "PASS"' "$TMP/spec.json" || die "$SPEC verdict is not PASS"
/usr/bin/grep -qF 'expiring 2027-02-18' "$TMP/spec.json" || die "$SPEC does not state the sunset 2027-02-18"
/usr/bin/grep -qF '"conditions_verified": "operator ruling: automatic head-branch deletion, with the s10 exemption retired' "$TMP/spec.json" || die "$SPEC conditions_verified does not cite the operator ruling"
/usr/bin/grep -qF '"derives_from": "release-policy-1.0"' "$TMP/spec.json" || die "$SPEC does not derive from release-policy-1.0 alone"
/usr/bin/grep -qF ",release-policy-1.0,PASS," "$log" || die "release-policy-1.0 is not signed in $log"
"${GIT[@]}" show "$HEAD_REVIEWED:.claude/CLAUDE.md" | /usr/bin/grep -qF "$ACTION" || die ".claude/CLAUDE.md at the head does not carry the PS-2 amendment naming $ACTION"

# --- a) retire the redundant exemption (registry only; never a HALT) -------------------------------------------
echo; echo "== a) exception registry before:"
(cd "$EMPTY" && "$PY" -I -P - "$WT/$TEAM" "$OLD_ID") <<'PY' || die "the registry is not in the expected state; nothing changed; tell the researchteam session"
import sys
from pathlib import Path
from agentteams.cli.exception_registry import load_registry, active_relaxing_exceptions
root, old = Path(sys.argv[1]), sys.argv[2]
reg = load_registry(root)
active = [e.get("id") for e in active_relaxing_exceptions(reg)]
print("  active relaxing exceptions:", active, "| toolchain_group_sequence:", reg.get("toolchain_group_sequence"))
sys.exit(0 if active == [old] else 1)
PY
group_covers_agentteams() {   # the operator-signed toolchain group must VERIFY and list agentteams (not merely exist)
  (cd "$EMPTY" && "$PY" -I -P - "$WT/$TEAM") <<'PY'
import sys
from pathlib import Path
from agentteams.cli.s10_exempt_gate import _signed_group
group = _signed_group({"team_id": "researchteam"}, Path(sys.argv[1]), consume=False)
print("  verified toolchain group:", group)
sys.exit(0 if group and "jlcatonjr/agentteams" in group else 1)
PY
}
group_covers_agentteams || die "the signed toolchain group does not verify or does not list jlcatonjr/agentteams: the s10 exemption is NOT redundant; nothing changed; stop"
echo "  The verified toolchain group lists jlcatonjr/agentteams, so the cooldown stays lifted for it without this entry."
read -r -p "Retire $OLD_ID in the registry (status: sunset)? [y/N] " ok
[[ "$ok" == "y" ]] || { echo "  not retired; nothing changed"; exit 0; }
(cd "$EMPTY" && "$PY" -I -P - "$WT/$TEAM" "$OLD_ID" "$ACTION") <<'PY' || die "retiring failed; undo: git -C $WT checkout -- $reg $log ; tell the researchteam session"
import sys
from pathlib import Path
from agentteams.cli.exception_registry import retire_exception, load_registry, active_relaxing_exceptions
root, old, new = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
seq = load_registry(root).get("toolchain_group_sequence")
retire_exception(root, old, reason=f"redundant with the operator-signed first-party toolchain group; slot released for {new} (operator ruling 2026-11-20)")
reg = load_registry(root)
assert reg.get("toolchain_group_sequence") == seq, "toolchain_group_sequence changed"
assert active_relaxing_exceptions(reg) == [], "an active relaxing exception remains"
print("  retired; active relaxing exceptions now: []")
PY

# --- b) sign the decision row -----------------------------------------------------------------------------------
echo; echo "== b) the decision to sign:"
/bin/cat "$TMP/spec.json"
read -r -p "Sign $ACTION (PASS, relaxing, sunset 2027-02-18) into $TEAM with key op-2026? [y/N] " ok
[[ "$ok" == "y" ]] || { echo "  not signed. The registry edit above is uncommitted: undo it with  git -C $WT checkout -- $reg"; exit 0; }
n0=$(/usr/bin/wc -l < "$log")
(cd "$EMPTY" && AGENTTEAMS_DECISION_ED25519_KEYFILE="$KEYFILE" "$SIGNER" --sign-decision "$TMP/spec.json" --output "$WT/$TEAM") || die "signing failed; undo: git -C $WT checkout -- $reg $log ; tell the researchteam session"
n1=$(/usr/bin/wc -l < "$log")
echo "  log lines: before sign $n0, after sign $n1"
[[ $((n1 - n0)) -eq 1 ]] || die "the signer changed the log by $((n1 - n0)) lines (expected 1); do not commit; undo: git -C $WT checkout -- $reg $log ; tell the researchteam session"

# --- c) register the signed row (cap-checked) and audit -----------------------------------------------------------
echo; echo "== c) register and audit:"
(cd "$EMPTY" && "$PY" -I -P - "$WT/$TEAM" "$ACTION" "$EXPIRES") <<'PY' || die "registering failed; do not commit; undo: git -C $WT checkout -- $reg $log ; tell the researchteam session"
import csv, sys
from datetime import datetime, timezone
from pathlib import Path
from agentteams.cli.exception_registry import register_exception, audit_exceptions, load_registry, active_relaxing_exceptions
from agentteams.cli.s10_exempt_gate import _decision_binding, _split
from agentteams.cli.effect_classifier import derive_effect_class, requires_operator_signature
root, action, expires = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
csv.field_size_limit(10**8)
with open(root / "references" / "security-decisions.log.csv", newline="", encoding="utf-8") as fh:
    rows = [r for r in csv.DictReader(fh) if (r.get("action_reviewed") or "") == action]
assert len(rows) == 1, f"expected exactly one row for {action}, found {len(rows)}"
row = rows[0]
assert (row.get("verdict") or "") == "PASS" and (row.get("sig_scheme") or "") == "ed25519" and (row.get("signature") or "").strip(), "the row is not an Ed25519-signed PASS"
assert (row.get("key_id") or "") == "op-2026", "the row is not signed with op-2026"
needs = requires_operator_signature(row, kind="decision")
print("  effect class:", derive_effect_class(row, kind="decision"), "| needs operator signature:", needs)
assert needs, "the signed row is not classified as needing the operator's signature"
seq = load_registry(root).get("toolchain_group_sequence")
entry_id = f"{action}@{row['signature'].strip()[:16]}"
register_exception(root, {
    "id": entry_id, "action": action, "kind": "repo-setting", "scope": action, "relaxing": True,
    "effect": {"relaxes": [action]},
    "lineage": sorted(_split(row.get("derives_from") or "")),
    "issued": datetime.now(timezone.utc).isoformat(),
    "expires": expires,
    "decision_key_id": row["key_id"].strip(),
    "decision_sha256": _decision_binding(row),
})
reg = load_registry(root)
assert reg.get("toolchain_group_sequence") == seq, "toolchain_group_sequence changed"
active = [e.get("id") for e in active_relaxing_exceptions(reg)]
assert active == [entry_id], f"unexpected active set: {active}"
problems = audit_exceptions(root)
print("  registered:", entry_id, "| expires:", expires)
print("  audit:", "clean" if not problems else problems)
sys.exit(0 if not problems else 1)
PY
n2=$(/usr/bin/wc -l < "$log")
[[ "$n2" -eq "$n1" ]] || die "registering changed the log ($n1 -> $n2 lines); do not commit; undo: git -C $WT checkout -- $reg $log ; tell the researchteam session"
group_covers_agentteams || die "after the change the toolchain group no longer verifies or no longer lists jlcatonjr/agentteams; do not commit; undo: git -C $WT checkout -- $reg $log ; tell the researchteam session"
changed="$("${GIT[@]}" status --porcelain)"
[[ "$changed" == " M $reg"$'\n'" M $log" ]] || die "unexpected changes in the worktree (expected only $log and $reg): $changed ; do not commit; undo: git -C $WT checkout -- $reg $log ; tell the researchteam session"
"${GIT[@]}" --no-pager diff --stat
echo "Done: 1 exemption retired, 1 row signed, 1 registry entry active. Nothing was committed and no setting was changed."
echo "Tell the researchteam session: it commits the log and the registry on $BR, pushes them to the PR, has @security"
echo "review that head, and asks you to approve the merge. The setting is turned on afterwards with script 21."
else
  printf 'STOP: run as /bin/bash -p %s (privileged mode); nothing was done.\n' "$0" >&2
fi
