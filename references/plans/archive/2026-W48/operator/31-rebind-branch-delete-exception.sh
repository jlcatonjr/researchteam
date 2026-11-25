#!/bin/bash -p
# 31 — H3 phase 2 for the operator: move the exception-registry entry for automatic head-branch deletion from its
# row signed with the old decision key (op-2026) to the same decision's row re-signed with opr-2026-11 on 2026-11-22.
# OPERATOR ONLY. Same hardened preamble as 2026-W47/20-retire-sign-register.sh.
# It SIGNS NOTHING and reads no private key. It calls only the registry functions of the root-owned agentteams
# install, and never edits the JSON itself. It changes one file, the exception registry under .github/agents/, and
# restores it if any check fails. It changes NO GitHub setting and COMMITS NOTHING: the researchteam session commits
# the registry, pushes it to the pull request, has @security review that head and asks for the merge.
# Why: removing op-2026 (phase 3) would leave the active entry bound to a row that no longer verifies, and
# `agentteams --audit-exceptions` does not report that (plan post-1.3.0-h3-retire-op-2026, phase 1 record).
# Before running: @security's clearance exception-rebind:<action> is recorded (it names the base commit, this
# script's hash, the old entry and the new binding), and the autosync is paused (script 28, pause).
# Usage (plain Terminal, from any directory; ALWAYS `/bin/bash -p <path>`, never `bash <path>`):
#   /bin/bash -p <checkout>/tmp/by-week/2026-W48/operator/31-rebind-branch-delete-exception.sh <40-hex head the session reports>
# (the runnable copy lives under the ignored tmp/; this tracked copy is the record and holds a placeholder)
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

HEAD_REVIEWED="${1:?usage: $0 <40-hex reviewed head of chore/rebind-branch-delete-exception>}"
WT="$HOME/githubrepositories/researchteam-wt-h3"
ACTION="repo-setting:delete-branch-on-merge:jlcatonjr/researchteam"
OLD_ID="repo-setting:delete-branch-on-merge:jlcatonjr/researchteam@c4c40701ad95ad92"
OLD_BINDING="3a11d65b797a84bd50a7ca75154d7b43b658d0029ea00c0ee7a0ea1f5f64e78a"
NEW_BINDING="9e98e66d76d394d3086046fdcae23be07970cc6e8cb8234c4c4216e2313d7154"   # the 2026-11-22 row; recomputed below
NEW_KEY="opr-2026-11"; OLD_KEY="op-2026"
EXPIRES="2027-02-18T23:59:59+00:00"                 # what the operator signed; not moved
REG_SHA="06d670bb49849be76ddbdfee0378944a1fcc48e2689ec162759e65321e7412bc"   # the registry on main, read 2026-11-25
BR="chore/rebind-branch-delete-exception"
TEAM=".github/agents"
SIGNER="<signer>"     # root-owned agentteams install, 1.3.0 or later; used here only for its interpreter and library
[[ "$HEAD_REVIEWED" =~ ^[0-9a-f]{40}$ ]] || die "the head must be a full 40-hex SHA"
[[ -x "$SIGNER" ]] || die "no root-owned agentteams at $SIGNER"
[[ "$(/usr/bin/stat -f %Su "$SIGNER")" == root ]] || die "$SIGNER is not root-owned"
PY="${SIGNER%/agentteams}/python"
[[ -x "$PY" ]] || die "no interpreter beside the root-owned agentteams at $PY"
[[ "$(/usr/bin/stat -f %Su "$PY")" == root ]] || die "$PY is not root-owned"
[[ -d "$WT" ]] || die "no worktree at $WT"

cd "$WT"
[[ "$("${GIT[@]}" rev-parse --abbrev-ref HEAD)" == "$BR" ]] || die "$WT is not on $BR"
[[ "$("${GIT[@]}" rev-parse HEAD)" == "$HEAD_REVIEWED" ]] || die "$BR is at $("${GIT[@]}" rev-parse HEAD), not the reviewed $HEAD_REVIEWED"
[[ -z "$("${GIT[@]}" status --porcelain)" ]] || die "$WT has uncommitted changes; stop"
log="$TEAM/references/security-decisions.log.csv"
reg="$TEAM/references/exception-registry.json"
keys="$TEAM/references/authorized-verify-keys"
sha() { /usr/bin/shasum -a 256 "$1" | /usr/bin/cut -d' ' -f1; }
[[ "$(sha "$reg")" == "$REG_SHA" ]] || die "$reg is not the registry the clearance names ($(sha "$reg")); nothing changed"
for k in "$OLD_KEY" "$NEW_KEY"; do [[ -f "$keys/$k.pub.pem" ]] || die "$keys/$k.pub.pem is missing: both keys must be present for this step"; done
LOG_SHA="$(sha "$log")"
TMP=$(/usr/bin/mktemp -d); trap 'rm -rf "$TMP"' EXIT
EMPTY="$TMP/empty"; /bin/mkdir "$EMPTY"
/bin/cp "$reg" "$TMP/registry.before.json"
restore() { /bin/cp "$TMP/registry.before.json" "$WT/$reg"; echo "  the registry was restored to its state before this run" >&2; }

echo; echo "== researchteam: re-bind the registry entry for $ACTION"
echo "== 1) checks before anything is written"
# One program, run twice: first to check, then to apply. It is written to the private temporary folder once.
/bin/cat > "$TMP/rebind.py" <<'PY'
import csv, json, shutil, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path
import agentteams
from agentteams.cli.exception_registry import (load_registry, active_relaxing_exceptions, register_exception,
                                                retire_exception, audit_exceptions)
from agentteams.cli.sandbox_relaxation_gate import _unbound_reason, _decision_binding, SANDBOX_EXCEPTION_TTL_DAYS
from agentteams.cli.s10_exempt_gate import _split

wt, team_rel, action, old_id, old_binding, new_binding, new_key, expires, mode = sys.argv[1:10]
team = Path(wt) / team_rel
version = tuple(int(p) for p in agentteams.__version__.split(".")[:2])
assert version >= (1, 3), f"agentteams {agentteams.__version__} is older than 1.3.0"
print("  agentteams", agentteams.__version__)
csv.field_size_limit(10**8)
now = datetime.now(timezone.utc)

def rows_of(dirpath):
    with open(Path(dirpath) / "references" / "security-decisions.log.csv", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))

def standing_halts():
    """Unretracted HALT rows on branch-delete, the repo-setting family or the action, in every team log."""
    found = []
    for rel in (".github/agents", ".claude/agents", ".codex/agents", ".goose/recipes"):
        path = Path(wt) / rel / "references" / "security-decisions.log.csv"
        if not path.is_file():
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        for i, r in enumerate(rows):
            act = (r.get("action_reviewed") or "").strip()
            if (r.get("verdict") or "").strip().upper() != "HALT":
                continue
            if not (act == "branch-delete" or act.startswith("branch-delete:") or act == "repo-setting"
                    or act.startswith("repo-setting:") or act == action):
                continue
            if not any((n.get("verdict") or "").strip().upper() == "HALT-RETRACTED"
                       and (n.get("action_reviewed") or "").strip() == act for n in rows[i + 1:]):
                found.append(f"{rel}: {act}")
    return found

def new_entry(row, issued):
    return {"id": f"{action}@{row['signature'].strip()[:16]}", "action": action, "kind": "repo-setting",
            "scope": action, "relaxing": True, "effect": {"relaxes": [action]},
            "lineage": sorted(_split(row.get("derives_from") or "")), "issued": issued, "expires": expires,
            "decision_key_id": row["key_id"].strip(), "decision_sha256": _decision_binding(row)}

def without_old_key(entry):
    """The binding check in a scratch copy of the team folder with the old key removed."""
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "agents"
        shutil.copytree(team, copy)
        for pem in (copy / "references" / "authorized-verify-keys").glob("op-2026.*"):
            pem.unlink()
        return _unbound_reason(copy, entry, now=now, ttl_days=SANDBOX_EXCEPTION_TTL_DAYS)

rows = [r for r in rows_of(team) if (r.get("action_reviewed") or "") == action]
assert len(rows) == 2, f"expected two rows for {action} (old key, new key), found {len(rows)}"
row = rows[-1]
assert (row.get("verdict") or "") == "PASS" and (row.get("sig_scheme") or "") == "ed25519", "the newest row is not an Ed25519-signed PASS"
assert (row.get("key_id") or "").strip() == new_key, f"the newest row is signed with {row.get('key_id')!r}, not {new_key}"
assert _decision_binding(row) == new_binding, f"the newest row's binding is {_decision_binding(row)}, not the one the clearance names"
assert _decision_binding(rows[0]) == old_binding, "the older row's binding is not the one the registry entry names"
halts = standing_halts()
assert not halts, f"an unretracted HALT stands: {halts}"
reg = load_registry(team)

if mode == "check":
    active = active_relaxing_exceptions(reg, now=now)
    assert [e.get("id") for e in active] == [old_id], f"unexpected active set: {[e.get('id') for e in active]}"
    old = active[0]
    assert old.get("decision_sha256") == old_binding and old.get("expires") == expires, "the active entry is not the one expected"
    assert _unbound_reason(team, old, now=now, ttl_days=SANDBOX_EXCEPTION_TTL_DAYS) is None, "the current entry is already unbound"
    candidate = new_entry(row, now.isoformat())
    assert candidate["lineage"] == old.get("lineage"), f"lineage differs: {candidate['lineage']} vs {old.get('lineage')}"
    why = _unbound_reason(team, candidate, now=now, ttl_days=SANDBOX_EXCEPTION_TTL_DAYS)
    assert why is None, f"the new binding would not carry over: {why}"
    why = without_old_key(candidate)
    assert why is None, f"the new binding would not carry over once op-2026 is removed: {why}"
    print("  current entry :", old_id, "| key", old.get("decision_key_id"), "| expires", old.get("expires"))
    print("  new entry     :", candidate["id"], "| key", candidate["decision_key_id"], "| expires", candidate["expires"])
    print("  the new binding verifies now, and in a copy with op-2026 removed; no HALT stands")
    sys.exit(0)

# mode == "apply"
before = json.loads(json.dumps(reg))
others_before = [e for e in before.get("exceptions", []) if e.get("id") != old_id]
candidate = new_entry(row, now.isoformat())
retire_exception(team, old_id, reason=f"re-bound to the same decision's row re-signed with {new_key} on 2026-11-22: "
                                       f"{candidate['id']} (key rotation; expiry unchanged)")
register_exception(team, candidate, now=now)
reg = load_registry(team)
assert {k: v for k, v in reg.items() if k != "exceptions"} == {k: v for k, v in before.items() if k != "exceptions"}, "a top-level registry field changed"
entries = reg.get("exceptions", [])
assert len(entries) == len(before.get("exceptions", [])) + 1, "the registry did not gain exactly one entry"
assert [e for e in entries if e.get("id") not in (old_id, candidate["id"])] == others_before, "another entry changed"
old_now = [e for e in entries if e.get("id") == old_id]
assert len(old_now) == 1 and old_now[0].get("status") == "sunset" and candidate["id"] in (old_now[0].get("retired_reason") or ""), "the old entry is not retired with a reason naming the new id"
active = active_relaxing_exceptions(reg, now=now)
assert [e.get("id") for e in active] == [candidate["id"]], f"unexpected active set: {[e.get('id') for e in active]}"
new = active[0]
assert new.get("expires") == expires and new.get("decision_key_id") == new_key and new.get("decision_sha256") == new_binding
assert new.get("lineage") == [e for e in before["exceptions"] if e.get("id") == old_id][0].get("lineage"), "lineage changed"
why = _unbound_reason(team, new, now=now, ttl_days=SANDBOX_EXCEPTION_TTL_DAYS)
assert why is None, f"the re-bound entry does not carry over: {why}"
why = without_old_key(new)
assert why is None, f"the re-bound entry does not carry over once op-2026 is removed: {why}"
problems = audit_exceptions(team)
assert not problems, f"the registry audit reports: {problems}"
print("  retired :", old_id)
print("  active  :", new["id"], "| key", new["decision_key_id"], "| expires", new["expires"])
print("  the binding verifies now, and in a copy with op-2026 removed; registry audit clean; active relaxing exceptions: 1")
PY
rebind() { (cd "$EMPTY" && "$PY" -I -P "$TMP/rebind.py" "$WT" "$TEAM" "$ACTION" "$OLD_ID" "$OLD_BINDING" "$NEW_BINDING" "$NEW_KEY" "$EXPIRES" "$1"); }
rebind check || die "a check before the change failed; nothing changed; tell the researchteam session"
group_verifies() {   # the operator-signed toolchain group must still VERIFY
  (cd "$EMPTY" && "$PY" -I -P - "$WT/$TEAM") <<'PY'
import sys
from pathlib import Path
from agentteams.cli.s10_exempt_gate import _signed_group
group = _signed_group({"team_id": "researchteam"}, Path(sys.argv[1]), consume=False)
print("  verified toolchain group:", group)
sys.exit(0 if group else 1)
PY
}
group_verifies || die "the signed toolchain group does not verify before the change; nothing changed; stop"

echo; echo "== 2) the change"
read -r -p "Retire the entry bound to the $OLD_KEY row and register the same exception against the $NEW_KEY row (expiry unchanged, $EXPIRES)? [y/N] " ok
[[ "$ok" == "y" ]] || { echo "  nothing changed"; exit 0; }
rebind apply || { restore; die "the re-binding or one of its checks failed; tell the researchteam session"; }

echo; echo "== 3) checks after"
[[ "$(sha "$log")" == "$LOG_SHA" ]] || { restore; die "the decisions log changed; do not commit; tell the researchteam session"; }
group_verifies || { restore; die "after the change the toolchain group no longer verifies; tell the researchteam session"; }
changed="$("${GIT[@]}" status --porcelain)"
[[ "$changed" == " M $reg" ]] || { restore; die "unexpected changes in the worktree (expected only $reg): $changed"; }
"${GIT[@]}" --no-pager diff --stat
echo "  registry sha256 now: $(sha "$reg")"
echo "Done: 1 entry retired, 1 entry registered against the $NEW_KEY row. Nothing was signed, committed or pushed."
echo "Tell the researchteam session: it commits the registry on $BR, pushes it, has @security review that head and"
echo "asks you to approve the merge. The autosync stays paused until that merge."
else
  printf 'STOP: run as /bin/bash -p %s (privileged mode); nothing was done.\n' "$0" >&2
fi
