#!/usr/bin/env bash
# 02 — Set up decision signing in researchteam and sign the Phase R rows, on a new PR branch.
#   1. Provision your existing Ed25519 key op-2026 (the one agentteams uses) as a verify key in the
#      .github/agents and .codex/agents team dirs. Only the PUBLIC key is written into the repo.
#   2. Migrate .github/agents' decisions log to the signing schema. This turns signing on: every live
#      unsigned PASS row stops clearing (the dry-run lists them first).
#   3. Sign, each with an interactive y/N review:
#        .github/agents: release-policy-1.0 (root), s10-release-key-exemption, pin-agentteams-$AT_TAG,
#                        codex-orchestrator-only-native-render (#210)
#        .codex/agents:  release-policy-1.0, codex-orchestrator-only-native-render
#   4. Commit (keys, logs, specs), push release-prep/decision-signing, and open the PR. It merges FIRST.
# Needs 01 (the trusted signer). Run it in your own terminal.
source "$(dirname "$0")/common.sh"
refuse_agent
need_rc11
[ -x "$SIGNER" ] || die "no trusted signer at $SIGNER; run 01b-install-root-owned-signer.sh first"
case "$SIGNER" in "$HOME"/*) die "the signer $SIGNER is under \$HOME, which agentteams refuses; run 01b-install-root-owned-signer.sh" ;; esac
[ -f "$KEYFILE" ] || die "missing private key $KEYFILE"
WT="$GH_ROOT/researchteam-wt-signing"
BR="release-prep/decision-signing"
TEAMS=(.github/agents .codex/agents)

git -C "$MAIN" fetch --quiet origin
if [ "${1:-}" = "--resign" ]; then
  # The first pass (2026-10-16) put prose in `scope`, which agentteams reads as the list of action ids a row
  # authorizes, so no row cleared its own action. Rebuild the unmerged branch from main and sign again.
  confirm "Discard the unmerged signing branch $BR (PR rows never reached main) and rebuild it from origin/main?"
  [ -d "$WT" ] && git -C "$MAIN" worktree remove --force "$WT"
  git -C "$MAIN" branch -f "$BR" origin/main
  git -C "$MAIN" worktree add --quiet "$WT" "$BR"
  RESIGN=1
fi
if [ ! -d "$WT" ]; then
  git -C "$MAIN" worktree add --quiet -b "$BR" "$WT" origin/main
fi
cd "$WT"
# Resumable: a previous run may have left the keys, the migrated log, its backup and the specs here.
unexpected="$(git status --porcelain | awk '{print $2}' | grep -vE '^(\.github/agents/references/(authorized-verify-keys/|security-decisions\.log\.csv)|\.codex/agents/references/(authorized-verify-keys/|security-decisions\.log\.csv)|\.github/agents/\.agentteams-backups/|docs/release/)' || true)"
[ -z "$unexpected" ] || die "$WT has unexpected changes; inspect them first:
$unexpected"

say "1. Verify keys"
for t in "${TEAMS[@]}"; do
  [ -f "$t/references/build-log.json" ] || die "$t is not a team dir"
  dest="$t/references/authorized-verify-keys/$KEY_ID.pub.pem"
  if [ ! -f "$dest" ]; then
    (umask 022; openssl pkey -in "$KEYFILE" -pubout -out "$dest")
    echo "  wrote $dest"
  fi
done
ref="$AGENTTEAMS_CHECKOUT/.github/agents/references/authorized-verify-keys/$KEY_ID.pub.pem"
if [ -f "$ref" ]; then
  cmp -s "$ref" ".github/agents/references/authorized-verify-keys/$KEY_ID.pub.pem" \
    && echo "  matches agentteams' committed $KEY_ID.pub.pem" \
    || die "the derived public key differs from agentteams' $KEY_ID.pub.pem; stop and check which key is current"
fi

say "2. Migrate .github/agents decisions log (dry-run first)"
if head -1 .github/agents/references/security-decisions.log.csv | tr ',' '\n' | grep -qx text_digest; then
  echo "  already migrated (text_digest column present); skipping"
else
  (cd /tmp && "$SIGNER" --migrate-decision-log --output "$WT/.github/agents" --dry-run)
  confirm "Migrate the log for real (unsigned PASS rows stop clearing)?"
  (cd /tmp && "$SIGNER" --migrate-decision-log --output "$WT/.github/agents" --yes)
fi
# rc.11 binds conditions and evidence through text_digest; a relaxing row is refused without the column.
head -1 .github/agents/references/security-decisions.log.csv | tr ',' '\n' | grep -qx text_digest \
  || die "the migrated log has no text_digest column; is $SIGNER agentteams $AT_TAG?"

say "3. Decision specs"
mkdir -p docs/release
for f in release-policy-1.0.decision-spec.json s10-release-key-exemption.decision-spec.json \
         s10-release-key-exemption.conditions.txt; do
  git show "origin/$PIN_BRANCH:docs/release/$f" > "docs/release/$f"
done
git show "origin/$PIN_BRANCH:docs/release/codex-210-orchestrator-only.decision-spec.json" \
  > docs/release/codex-210-orchestrator-only.decision-spec.json
got="$(shasum -a 256 docs/release/s10-release-key-exemption.conditions.txt | cut -d' ' -f1)"
[ "$got" = "$S10_SHA" ] || die "S-10 conditions text hash $got != $S10_SHA"
cat > docs/release/pin-agentteams-$AT_TAG.decision-spec.json <<JSON
{
  "timestamp": "$(date -u +%Y-%m-%d)",
  "date": "$(date -u +%Y-%m-%d)",
  "requesting_agent": "security",
  "author": "operator",
  "action_reviewed": "pin-agentteams-$AT_TAG",
  "verdict": "PASS",
  "scope": "pin-agentteams-$AT_TAG",
  "conditions": "Pin = peeled commit of the verified signed tag $AT_TAG (tag object $AT_TAG_OBJ, release key $RELEASE_FP). S-10 exemption applies to agentteams itself; resolved third-party packages vetted in docs/release/s10-dependency-vetting-2026-10-16.md (no OSV advisories; rpds-py and pycparser constrained).",
  "conditions_verified": "tag $AT_TAG object $AT_TAG_OBJ peeled $AT_PEELED; git tag -v good signature $RELEASE_FP; remote advertisement matches",
  "evidence": "researchteam PR #80 (rc.3); S-10 vetting carried over (pyproject: version line only); Scope: toolchain.lock and the update/research extras: agentteams -> $AT_PEELED",
  "derives_from": "release-policy-1.0; s10-release-key-exemption",
  "effect_grants": "",
  "effect_targets": "toolchain.lock; pyproject.toml",
  "effect_relaxes": "",
  "effect_destructive": "false",
  "effect_cross_repo": "false",
  "effect_bulk": "false",
  "key_id": "$KEY_ID"
}
JSON

say "4. Sign (you review each row; answer y to sign it)"
export AGENTTEAMS_DECISION_ED25519_KEYFILE="$KEYFILE" AT_TAG
sign() {
  local action log="$WT/$2/references/security-decisions.log.csv"
  action="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["action_reviewed"])' "$WT/docs/release/$1")"
  echo; echo "--- $1 -> $2"
  if [ -f "$log" ] && python3 -c 'import csv,sys; sys.exit(0 if any((r.get("action_reviewed") or "").strip()==sys.argv[2] and (r.get("signature") or "").strip() for r in csv.DictReader(open(sys.argv[1], newline=""))) else 1)' "$log" "$action"; then
    echo "  already signed in $2; skipping"; return
  fi
  (cd /tmp && "$SIGNER" --sign-decision "$WT/docs/release/$1" --output "$WT/$2")
}
sign release-policy-1.0.decision-spec.json                .github/agents
sign s10-release-key-exemption.decision-spec.json         .github/agents
sign pin-agentteams-$AT_TAG.decision-spec.json       .github/agents
sign codex-210-orchestrator-only.decision-spec.json       .github/agents
sign release-policy-1.0.decision-spec.json                .codex/agents
sign codex-210-orchestrator-only.decision-spec.json       .codex/agents
unset AGENTTEAMS_DECISION_ED25519_KEYFILE

say "5. Check: every row must clear the security gate"
(cd /tmp && "${SIGNER%/agentteams}/python" - "$WT") <<'PY' || die "a signed row does not clear the gate; do not commit (tell the researchteam session)"
import sys
from pathlib import Path
from agentteams.cli.security_gate import check_clearance
wt = Path(sys.argv[1]); bad = 0
for team, act in [(".github/agents", "release-policy-1.0"), (".github/agents", "s10-release-key-exemption"),
                  (".github/agents", f"pin-agentteams-{__import__('os').environ.get('AT_TAG', '')}"),
                  (".github/agents", "codex-orchestrator-only-native-render"),
                  (".codex/agents", "release-policy-1.0"), (".codex/agents", "codex-orchestrator-only-native-render")]:
    ok, why = check_clearance(wt / team, action=act)
    print(f"  {team:15} {act:42} {'clears' if ok else 'REFUSED: ' + str(why)[:160]}")
    bad += not ok
sys.exit(1 if bad else 0)
PY

for t in "${TEAMS[@]}"; do (cd /tmp && "$SIGNER" --verify-integrity --output "$WT/$t") | tail -4 || true; done
git status --short

confirm "Commit, push $BR and open the PR?"
git add -A .github/agents/references .codex/agents/references docs/release
# --no-verify: the pre-commit hook re-renders the team whenever agent infrastructure is staged.
git commit --quiet --no-verify -m "chore(security): provision verify key $KEY_ID; signed Phase R decision rows

Operator-signed (Ed25519) rows: release-policy-1.0, s10-release-key-exemption (conditions sha256
$S10_SHA), pin-agentteams-$AT_TAG, codex-orchestrator-only-native-render (#210). The
.github/agents decisions log is migrated to the signing schema."
git push --quiet --force-with-lease -u origin "$BR"
url="$(gh pr view "$BR" -R "$REPO" --json url,state -q 'select(.state=="OPEN") | .url' 2>/dev/null || true)"
[ -n "$url" ] || url="$(gh pr create -R "$REPO" --base main --head "$BR" \
  --title "chore(security): verify key $KEY_ID + signed Phase R decision rows" \
  --body "Operator-signed decision rows for the joint v1.0.0 cut. **Merge first**, before #51, #49, #52, #50 and #53. Written by tmp/by-week/2026-W42/operator/02-decision-signing.sh.")"
echo "$url"; state_set SIGN_PR "${url##*/}"
