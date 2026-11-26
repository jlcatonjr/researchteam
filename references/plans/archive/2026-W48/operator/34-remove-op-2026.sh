#!/bin/bash -p
# 34 — H3 phase 3 for the operator: retire the old decision verify key op-2026 by removing its public key file from
# the two verify-key stores that hold it (.github/agents and .codex/agents). This revokes the 29 rows signed with it
# (27 in the .github log, 2 in the .codex log); see plan post-1.3.0-h3-retire-op-2026, step 11a.
# OPERATOR ONLY. Same hardened preamble as 31-rebind-branch-delete-exception.sh.
# It SIGNS NOTHING and reads no private key. It removes exactly two tracked files and restores both from git if any
# check after the removal fails. It changes NO GitHub setting, STAGES NOTHING and COMMITS NOTHING: the researchteam
# session stages the removal, commits it on chore/retire-op-2026, pushes it, has @security review that head and asks
# for the merge.
# Before running: the operator has signed and the session has committed the clearance row key-retire:op-2026
# (script 33), whose text names this script's tracked sha256 and the two files' hashes; the autosync is paused
# (script 28, pause) and stays paused until the merge; the Claude GitHub App is idle or suspended (condition C3).
# The private key op-2026 is the operator's and is not touched by this script (condition C5).
# Usage (plain Terminal, from any directory; ALWAYS `/bin/bash -p <path>`, never `bash <path>`):
#   /bin/bash -p <checkout>/tmp/by-week/2026-W48/operator/34-remove-op-2026.sh <40-hex head the session reports>
# (the runnable copy lives under the ignored tmp/; this tracked copy is the record and holds placeholders on the
# lines marked "# @ph"; the runnable copy differs from it on those lines only, which this script checks)
if [[ $- == *p* ]]; then
builtin unset -f $(builtin compgen -A function) 2>/dev/null; builtin set -euo pipefail
[[ -z "${CLAUDECODE:-}" && -z "${CLAUDE_CODE_ENTRYPOINT:-}" && -z "${CLAUDE_CODE_SSE_PORT:-}" && -z "${CODEX_SANDBOX:-}" ]] || { echo "error: run this from a plain Terminal, not an agent session" >&2; exit 1; }
[[ -t 0 && -t 1 ]] || { echo "error: run this in a terminal" >&2; exit 1; }
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

HEAD_REVIEWED="${1:?usage: $0 <40-hex reviewed head of chore/retire-op-2026, with the signed key-retire:op-2026 row committed>}"
WT="$HOME/githubrepositories/researchteam-wt-h3c"
BR="chore/retire-op-2026"
REPO="jlcatonjr/researchteam"
ACTION="key-retire:op-2026"
OLD_KEY="op-2026"; NEW_KEY="opr-2026-11"
KEY_SHA="08f69c5d0e899bd26b26deb6f9f3af9b1a65a9c5e0ee25733769cc1ea3e70e7b"     # op-2026.pub.pem, the same in both stores
NEW_PUB_SHA="d22faa83b674abe6b1e3207a4f13fc17c5ddd367e35e0c60c69163eddbd9dab7"  # opr-2026-11.pub.pem
PHASE2_MAIN="8e827f9311b0a4b59e16a0c27659425833fb5baf"                          # phase 2's merge on main (#275)
F1=".github/agents/references/authorized-verify-keys/op-2026.pub.pem"
F2=".codex/agents/references/authorized-verify-keys/op-2026.pub.pem"
SELF_REL="references/plans/archive/2026-W48/operator/34-remove-op-2026.sh"
BIND_ACTION="repo-setting:delete-branch-on-merge:jlcatonjr/researchteam"
BIND_SHA="9e98e66d76d394d3086046fdcae23be07970cc6e8cb8234c4c4216e2313d7154"    # the 2026-11-22 row (opr-2026-11)
AUTOSYNC_WF=".github/workflows/agentteams-sync.yml"
AUTOSYNC_HEAD="chore/agentteams-autosync"
GH=/opt/homebrew/bin/gh
AUDIT_SRC="$HOME/githubrepositories/infrastructureManagement/scripts/frozen_key_audit.py"
AUDIT_SHA=b85de5e31c74124f6722fd84f4590db70cd23b8a5a9bd46939d051ff0f6697a6
BASE_SRC="$HOME/githubrepositories/infrastructureManagement/references/frozen-key-baseline-2026-11-21b.json"
BASE_SHA=7406903c1172d90864f009f5b8dc4761e82115a8cbc2bb5d9c0b70e983f6cf56
SIGNER="<signer>"     # @ph <signer> root-owned agentteams 1.3.0 install; used here only for its CLI, interpreter and library
ALLOWED_SIGNERS="<allowed-signers-file>"     # @ph <allowed-signers-file> the operator's ssh allowed-signers file (release key)
[[ "$SIGNER" != "<"* && "$ALLOWED_SIGNERS" != "<"* ]] || die "this is the tracked record of the script; it has placeholders and does not run"
[[ "$HEAD_REVIEWED" =~ ^[0-9a-f]{40}$ ]] || die "the head must be a full 40-hex SHA"
[[ -x "$SIGNER" ]] || die "no root-owned agentteams at $SIGNER"
[[ "$(/usr/bin/stat -f %Su "$SIGNER")" == root ]] || die "$SIGNER is not root-owned"
PY="${SIGNER%/agentteams}/python"
[[ -x "$PY" ]] || die "no interpreter beside the root-owned agentteams at $PY"
[[ "$(/usr/bin/stat -f %Su "$PY")" == root ]] || die "$PY is not root-owned"
# The checks below import the whole library: every entry of the install and of its base Python must be root-owned
# and not group/world-writable (the same check as script 33).
VENV="${SIGNER%/bin/agentteams}"
base=$("$PY" -I -c 'import sys; print(sys.base_prefix)')
bad=$(/usr/bin/find "$VENV" "$base" \( ! -user root -o \( ! -type l \( -perm -0020 -o -perm -0002 \) \) \) -print 2>&1 | /usr/bin/head -3) || :   # find may be cut off by head (SIGPIPE); what it printed decides
[[ -z "$bad" ]] || die "the root-owned agentteams or its base Python has an entry that is not root-owned or is group/world-writable: $bad"
ver=$("$SIGNER" --version 2>&1) || die "the root-owned agentteams does not run"
[[ "$ver" =~ ^agentteams\ 1\.3\.0([^0-9]|$) ]] || die "the root-owned agentteams is $ver, not 1.3.0, the version toolchain.lock pins"
[[ -f "$ALLOWED_SIGNERS" && ! -L "$ALLOWED_SIGNERS" ]] || die "the allowed-signers file is missing or a link"
[[ -x "$GH" ]] || die "no gh at $GH"
[[ -d "$WT" && ! -L "$WT" ]] || die "no worktree at $WT"
SELF_PATH="$0"; [[ "$SELF_PATH" == /* ]] || SELF_PATH="$PWD/$SELF_PATH"
[[ -f "$SELF_PATH" ]] || die "cannot find this script at $SELF_PATH"

cd "$WT"
sha() { /usr/bin/shasum -a 256 "$1" | /usr/bin/cut -d' ' -f1; }
[[ "$("${GIT[@]}" rev-parse --abbrev-ref HEAD)" == "$BR" ]] || die "$WT is not on $BR"
[[ "$("${GIT[@]}" rev-parse HEAD)" == "$HEAD_REVIEWED" ]] || die "$BR is at $("${GIT[@]}" rev-parse HEAD), not the reviewed $HEAD_REVIEWED"
[[ -z "$("${GIT[@]}" status --porcelain --untracked-files=all)" ]] || die "$WT has uncommitted changes; stop"
"${GIT[@]}" merge-base --is-ancestor "$PHASE2_MAIN" HEAD || die "phase 2's merge $PHASE2_MAIN is not in $BR"
# Since phase 2's merge, the branch changes exactly the spec, scripts 33 and 34, and the decisions log, and the log
# by exactly one appended row (the signed key-retire:op-2026 row).
LOG_REL=".github/agents/references/security-decisions.log.csv"
want="$(printf '%s\n' docs/release/key-retire-op-2026.decision-spec.json references/plans/archive/2026-W48/operator/33-sign-key-retire-clearance.sh "$SELF_REL" "$LOG_REL" | LC_ALL=C /usr/bin/sort)"
got="$("${GIT[@]}" diff --no-renames --name-only "$PHASE2_MAIN" HEAD)" || die "cannot list the branch's changes since $PHASE2_MAIN"
got="$(printf '%s\n' "$got" | LC_ALL=C /usr/bin/sort)"
[[ "$got" == "$want" ]] || die "the branch's changes since $PHASE2_MAIN are not exactly the allowlist (spec, scripts 33 and 34, the decisions log): $got"
[[ "$("${GIT[@]}" diff --no-renames --numstat "$PHASE2_MAIN" HEAD -- "$LOG_REL")" == $'1\t0\t'"$LOG_REL" ]] || die "the decisions log does not differ from $PHASE2_MAIN by exactly one added line"
n_base=$("${GIT[@]}" cat-file -s "$PHASE2_MAIN:$LOG_REL")
/usr/bin/cmp -s <("${GIT[@]}" show "$PHASE2_MAIN:$LOG_REL") <("${GIT[@]}" show "HEAD:$LOG_REL" | /usr/bin/head -c "$n_base") \
  || die "the decisions log at HEAD does not begin with the log at $PHASE2_MAIN: the row is not appended"
[[ "$("${GIT[@]}" show "HEAD:$LOG_REL" | /usr/bin/wc -l)" -eq $(( $("${GIT[@]}" show "$PHASE2_MAIN:$LOG_REL" | /usr/bin/wc -l) + 1 )) ]] || die "the decisions log does not have exactly one more row than at $PHASE2_MAIN"
for f in "$F1" "$F2"; do
  [[ -f "$f" && ! -L "$f" && "$(sha "$f")" == "$KEY_SHA" ]] || die "$f is missing, a link, or not the expected $KEY_SHA; nothing changed"
  [[ -f "${f%/*}/$NEW_KEY.pub.pem" && "$(sha "${f%/*}/$NEW_KEY.pub.pem")" == "$NEW_PUB_SHA" ]] || die "${f%/*}/$NEW_KEY.pub.pem is not $NEW_PUB_SHA; nothing changed"
done
TMP=$(/usr/bin/mktemp -d); trap '/bin/rm -rf "$TMP"' EXIT
/bin/chmod 700 "$TMP"
EMPTY="$TMP/empty"; /bin/mkdir "$EMPTY"

# This script, as run, must be its tracked copy at the reviewed head once the "# @ph" lines are put back to their
# placeholders. The signed row names the tracked copy's sha256.
SELF_SHA="$(cd "$EMPTY" && "$PY" -I -P - "$SELF_PATH" <<'PY'
import hashlib, re, sys
text = open(sys.argv[1], encoding="utf-8").read()
norm = re.sub(r'(?m)^([A-Z_]+)="[^"\n]*"(\s+# @ph (<[a-z-]+>) .*)$', r'\1="\3"\2', text)
print(hashlib.sha256(norm.encode("utf-8")).hexdigest())
PY
)" || die "cannot compute this script's tracked hash"
TRACKED_SHA="$("${GIT[@]}" show "HEAD:$SELF_REL" | /usr/bin/shasum -a 256 | /usr/bin/cut -d' ' -f1)" || die "no $SELF_REL at HEAD"
[[ "$SELF_SHA" == "$TRACKED_SHA" ]] || die "this script differs from $SELF_REL at HEAD on more than its placeholder lines ($SELF_SHA vs $TRACKED_SHA)"

LOGS_BEFORE="$(sha .github/agents/references/security-decisions.log.csv) $(sha .codex/agents/references/security-decisions.log.csv) $(sha .github/agents/references/exception-registry.json) $(sha .agentteams/toolchain-group.json)"
restore() {
  "${GIT[@]}" checkout HEAD -- "$F1" "$F2" \
    && [[ "$(sha "$WT/$F1")" == "$KEY_SHA" && "$(sha "$WT/$F2")" == "$KEY_SHA" ]] \
    && echo "  both op-2026.pub.pem files were restored from git" >&2 \
    || echo "  RESTORE FAILED: run  git -C $WT checkout HEAD -- $F1 $F2" >&2
}

echo; echo "== researchteam: retire the decision verify key $OLD_KEY (H3 phase 3)"
echo "== 1) checks before anything is removed"
# One program, run in two modes: "before" (the key present) and "after" (the key removed).
/bin/cat > "$TMP/check.py" <<'PY'
import csv, shutil, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path
import agentteams
from agentteams.cli.security_gate import check_clearance
from agentteams.cli.decision_log import _assert_no_unretracted_halt
from agentteams.cli.exception_registry import load_registry, active_relaxing_exceptions
from agentteams.cli.sandbox_relaxation_gate import _unbound_reason, SANDBOX_EXCEPTION_TTL_DAYS

(wt, action, self_sha, key_sha, f1, f2, phase2, bind_action, bind_sha, old_key, new_key, mode) = sys.argv[1:13]
assert agentteams.__version__ == "1.3.0", f"agentteams is {agentteams.__version__}; this script was reviewed against 1.3.0"
root = Path(wt)
gh_team, codex_team = root / ".github/agents", root / ".codex/agents"
csv.field_size_limit(10**8)
now = datetime.now(timezone.utc)
bad = []

def rows_of(team):
    with open(team / "references" / "security-decisions.log.csv", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))

# a) No unretracted HALT on key-retire or the action, in every team log (agentteams' own scan: a retraction counts
#    only when authentic and carries evidence; lineage ancestors are followed).
for rel in (".github/agents", ".claude/agents", ".codex/agents", ".goose/recipes"):
    team = root / rel
    if not (team / "references" / "security-decisions.log.csv").is_file():
        continue
    for act in ("key-retire", action):
        try:
            _assert_no_unretracted_halt(team, action=act)
        except RuntimeError as exc:
            bad.append(f"HALT stands in {rel} on {act}: {str(exc)[:160]}")

# b) The clearance row: exactly one, signed with the new key, a destructive non-relaxing PASS on exactly the two
#    files, whose text names this script's tracked hash, the files' hash and phase 2's merge; and it clears.
#    (effect_targets is empty: agentteams refuses a decision whose write target lies in a verify-key store, so the
#    files are named in the text.)
rows = [r for r in rows_of(gh_team) if (r.get("action_reviewed") or "").strip() == action]
if len(rows) != 1:
    bad.append(f"expected one {action} row in the .github log, found {len(rows)}")
else:
    r = rows[0]
    text = " ".join((r.get(k) or "") for k in ("conditions", "conditions_verified", "evidence"))
    want = {"verdict": "PASS", "key_id": new_key, "sig_scheme": "ed25519", "scope": action,
            "effect_destructive": "true", "effect_relaxes": "", "effect_grants": "",
            "effect_targets": "", "effect_cross_repo": "false", "effect_bulk": "false",
            "derives_from": "release-policy-1.0"}
    for k, v in want.items():
        if (r.get(k) or "").strip() != v:
            bad.append(f"the {action} row has {k}={(r.get(k) or '').strip()!r}, expected {v!r}")
    for needle, what in ((self_sha, "this script's tracked sha256"), (key_sha, "the key files' sha256"),
                         (f1, "the .github key file"), (f2, "the .codex key file"), (phase2, "phase 2's merge commit")):
        if needle not in text:
            bad.append(f"the {action} row's text does not name {what} ({needle})")
for t in (root / ".claude/agents", codex_team, root / ".goose/recipes"):
    if (t / "references" / "security-decisions.log.csv").is_file() and \
            any((x.get("action_reviewed") or "").strip() == action for x in rows_of(t)):
        bad.append(f"a {action} row is also in {t.relative_to(root)}")

# c) Clearances (non-consuming): the action itself, the six re-signed ids and the 1.3 line in .github, and the
#    re-signed release-policy-1.0 in .codex. All must clear with the key present and with it removed.
for team, act in [(gh_team, action)] + [(gh_team, a) for a in (
        "release-policy-1.0", "management-roster-enroll:infrastructure-management", "s10-first-party-releases-2026-11",
        "term-index-2026-11", "release-line-agentteams-1.2", bind_action, "release-line-agentteams-1.3")] + \
        [(codex_team, "release-policy-1.0")]:
    ok, why = check_clearance(team, action=act)
    print(f"  {team.relative_to(root)}: {act}: {'clears' if ok else 'REFUSED: ' + str(why)[:200]}")
    if not ok:
        bad.append(f"{act} does not clear in {team.relative_to(root)}")

# d) The registry binding (what --audit-exceptions does not check): exactly one active entry for the branch-deletion
#    exception, bound to the opr-2026-11 row, and bound in fact.
def binding_problems(team, label):
    out = []
    active = [e for e in active_relaxing_exceptions(load_registry(team), now=now) if e.get("action") == bind_action]
    if len(active) != 1:
        return [f"expected one active registry entry for {bind_action}, found {len(active)}"]
    e = active[0]
    if e.get("decision_key_id") != new_key or e.get("decision_sha256") != bind_sha:
        out.append(f"the active entry {e.get('id')} is bound to key {e.get('decision_key_id')} / {e.get('decision_sha256')}")
    why = _unbound_reason(team, e, now=now, ttl_days=SANDBOX_EXCEPTION_TTL_DAYS)
    if why is not None:
        out.append(f"the active entry {e.get('id')} is not bound: {why}")
    else:
        print(f"  registry ({label}): {e.get('id')} bound to the {new_key} row; expires {e.get('expires')}")
    return out
bad += binding_problems(gh_team, ".github/agents")

if mode == "before":
    # The same binding in a scratch copy of the team folder with the old key removed (what the removal will leave).
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "agents"
        shutil.copytree(gh_team, copy)
        (copy / "references" / "authorized-verify-keys" / f"{old_key}.pub.pem").unlink()
        bad += [f"(copy without {old_key}) {p}" for p in binding_problems(copy, f"a copy without {old_key}")]
else:
    # No verify-key store of any team folder (backups included) still holds the old key, under any name.
    import hashlib
    for rel in (".github/agents", ".claude/agents", ".codex/agents", ".goose/recipes"):
        for pem in (root / rel).glob("**/authorized-verify-keys/*"):
            if not pem.is_file():
                continue
            if pem.name.lower().startswith(old_key + ".") or hashlib.sha256(pem.read_bytes()).hexdigest() == key_sha:
                bad.append(f"{pem.relative_to(root)} still holds {old_key}")
    # The removal took effect: a row signed only with the old key, with no later row, no longer clears.
    ok, why = check_clearance(gh_team, action="release-line-agentteams-1.1")
    print(f"  .github/agents: release-line-agentteams-1.1 (signed only with {old_key}): {'STILL CLEARS' if ok else 'refused, as expected'}")
    if ok:
        bad.append(f"release-line-agentteams-1.1 still clears: {old_key} is still trusted somewhere")

for b in bad:
    print("  FAIL:", b)
sys.exit(1 if bad else 0)
PY
check() { (cd "$EMPTY" && "$PY" -I -P "$TMP/check.py" "$WT" "$ACTION" "$TRACKED_SHA" "$KEY_SHA" "$F1" "$F2" "$PHASE2_MAIN" "$BIND_ACTION" "$BIND_SHA" "$OLD_KEY" "$NEW_KEY" "$1"); }
check before || die "a check before the removal failed; nothing changed; tell the researchteam session"

# The autosync is paused (condition C4) and no autosync pull request is open. Read from GitHub; any failure stops.
wf_state="$("$GH" workflow list --all -R "$REPO" --json path,state --jq ".[] | select(.path==\"$AUTOSYNC_WF\") | .state")" \
  || die "cannot read the autosync workflow's state; nothing changed"
[[ "$wf_state" == disabled_manually ]] || die "the autosync workflow is '${wf_state:-not found}', not disabled_manually: pause it first (script 28 pause); nothing changed"
n_open="$("$GH" pr list -R "$REPO" --head "$AUTOSYNC_HEAD" --state open --json number --jq length)" \
  || die "cannot list open autosync pull requests; nothing changed"
[[ "$n_open" == 0 ]] || die "$n_open autosync pull request(s) open from $AUTOSYNC_HEAD: close them first; nothing changed"
echo "  autosync: $wf_state; open autosync pull requests: 0"

# The other read-only checks the repository runs, with the key still present (so a failure after the removal is
# known to be the removal's).
at() { "$SIGNER" "$@"; }
gate_checks() {
  local out t
  for t in .github/agents .codex/agents; do
    out=$(at --audit-exceptions --output "$t" 2>&1) || { printf '%s\n' "$out"; echo "  FAIL: --audit-exceptions ($t)"; return 1; }
    printf '  %s: %s\n' "$t" "$(printf '%s\n' "$out" | /usr/bin/tail -1)"
    out=$(at --verify-integrity --output "$t" 2>&1) || { printf '%s\n' "$out"; echo "  FAIL: --verify-integrity ($t)"; return 1; }
    printf '  %s: --verify-integrity exit 0\n' "$t"
  done
  out=$(at --verify-toolchain-group --output .github/agents --description brief.json 2>&1) \
    || { printf '%s\n' "$out"; echo "  FAIL: --verify-toolchain-group"; return 1; }
  printf '  %s\n' "$(printf '%s\n' "$out" | /usr/bin/head -1)"
  out=$(at --verify-toolchain-pin toolchain.lock --allowed-signers "$ALLOWED_SIGNERS" --output .github/agents --description brief.json 2>&1) \
    || { printf '%s\n' "$out"; echo "  FAIL: --verify-toolchain-pin"; return 1; }
  printf '  %s\n' "$(printf '%s\n' "$out" | /usr/bin/tail -1)"
  /bin/cp "$AUDIT_SRC" "$TMP/frozen_key_audit.py" && /bin/cp "$BASE_SRC" "$TMP/baseline.json" || { echo "  FAIL: the frozen-key audit or its baseline is missing"; return 1; }
  [[ "$(sha "$TMP/frozen_key_audit.py")" == "$AUDIT_SHA" && "$(sha "$TMP/baseline.json")" == "$BASE_SHA" ]] \
    || { echo "  FAIL: the frozen-key audit or its baseline is not the pinned copy"; return 1; }
  out=$( (cd "$EMPTY" && "$PY" -I "$TMP/frozen_key_audit.py" --check "$TMP/baseline.json" "$WT") 2>&1) \
    || { printf '%s\n' "$out"; echo "  FAIL: the frozen-key audit"; return 1; }
  echo "  frozen-key audit: clean"
}
gate_checks || die "a repository check fails with the key still present; nothing changed; tell the researchteam session"

echo; echo "== 2) the change"
echo "  This deletes two tracked files (nothing is staged or committed):"
echo "    $F1"
echo "    $F2"
echo "  Every row signed only with $OLD_KEY stops verifying: 29 rows (27 in the .github log, 2 in the .codex log)."
echo "  Among them fleet-agent-pilot-2026-11, the Claude GitHub App authorization pilot: it lapses, and the App has no"
echo "  authorization in this repository until H4's row is signed (condition C3)."
read -r -p "Is the Claude GitHub App idle or suspended in this repository? [y/N] " ok
[[ "$ok" == "y" ]] || { echo "  nothing changed (condition C3 is not met)"; exit 0; }
read -r -p "Delete both $OLD_KEY.pub.pem files now? [y/N] " ok
[[ "$ok" == "y" ]] || { echo "  nothing changed"; exit 0; }
# The worktree may have changed while the questions waited; and from here to the end of the checks an interrupt must
# not leave the stores half-changed, so INT, TERM and HUP are ignored until then.
[[ "$("${GIT[@]}" rev-parse HEAD)" == "$HEAD_REVIEWED" && -z "$("${GIT[@]}" status --porcelain --untracked-files=all)" ]] \
  || die "the worktree changed while the questions waited; nothing changed by this script"
for f in "$F1" "$F2"; do [[ -f "$f" && ! -L "$f" && "$(sha "$f")" == "$KEY_SHA" ]] || die "$f changed while the questions waited; nothing changed by this script"; done
trap '' INT TERM HUP
/bin/rm -f -- "$WT/$F1" "$WT/$F2" || { restore; die "the removal failed; tell the researchteam session"; }

echo; echo "== 3) checks after"
[[ ! -e "$F1" && ! -e "$F2" ]] || { restore; die "a key file is still there after the removal"; }
check after || { restore; die "a check after the removal failed; tell the researchteam session"; }
gate_checks || { restore; die "a repository check failed after the removal; tell the researchteam session"; }
[[ "$(sha .github/agents/references/security-decisions.log.csv) $(sha .codex/agents/references/security-decisions.log.csv) $(sha .github/agents/references/exception-registry.json) $(sha .agentteams/toolchain-group.json)" == "$LOGS_BEFORE" ]] \
  || { restore; die "a decisions log, the registry or the group file changed during the run"; }
changed="$("${GIT[@]}" status --porcelain --untracked-files=all)" || { restore; die "git status failed"; }
[[ "$changed" == " D $F1"$'\n'" D $F2" || "$changed" == " D $F2"$'\n'" D $F1" ]] \
  || { restore; die "unexpected changes in the worktree (expected only the two deletions): $changed"; }
"${GIT[@]}" --no-pager diff --stat
trap - INT TERM HUP
echo "  If this run is ever cut off part-way: git -C $WT checkout HEAD -- $F1 $F2  puts both files back."
echo "Done: $OLD_KEY removed from the .github and .codex verify-key stores; every check passed. Nothing was signed,"
echo "staged, committed or pushed."
echo "Tell the researchteam session: 'script 34 done at ${HEAD_REVIEWED:0:12}' and paste this output. It stages the two"
echo "deletions, commits them on $BR, pushes, has @security review that head and asks you to approve the merge."
echo "The autosync stays paused until that merge."
else
  printf 'STOP: run as /bin/bash -p %s (privileged mode); nothing was done.\n' "$0" >&2
  exit 1
fi
