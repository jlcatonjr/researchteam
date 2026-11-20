#!/usr/bin/env bash
# 19 — Fast-forward release/1.2 to a reviewed main commit and sign researchteam v1.2.1 with the release key.
# Patch release on the 1.2 line: the verify_tag shallow-fetch fix (#227) plus docs; the agentteams pin stays v1.2.1.
# Copied from 2026-W47/16-cut-v1.2.0.sh. New here: the tagger email is fixed (the account's GitHub no-reply address),
# the release key must be registered on the account as a signing key before anything is signed
# (18-register-signing-key.sh), and GitHub's verification of the pushed tag is reported.
# OPERATOR ONLY, plain Terminal, from any directory:
#   bash <checkout>/tmp/by-week/2026-W47/operator/19-cut-v1.2.1.sh <40-hex reviewed main SHA>
# Run it after the release-prep PR has merged, with that merge commit. It checks the pin, the toolchain-group file and
# the CHANGELOG AT the given commit, requires a fast-forward of release/1.2, asks before each push, verifies the new tag
# exactly as consumers will, and offers the GitHub release. release/1.2 then equals main at that commit, so no
# merge-forward is needed.
source "$(dirname "$0")/common.sh"
refuse_agent
TAG="v1.2.1"; AT_TAG="v1.2.1"
SHA="${1:?usage: $0 <40-hex reviewed main SHA>}"
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || die "the commit must be a full 40-hex SHA"
fp="$(ssh-keygen -lf "$RELEASE_PUB" | awk '{print $2}')"
[ "$fp" = "$RELEASE_FP" ] || die "$RELEASE_PUB is $fp, not the release key $RELEASE_FP"
RT_URL="https://github.com/$REPO"
cd "$MAIN"
# Identity for the tag. The email is fixed here, not read from the checkout: it is the account's GitHub no-reply
# address, which GitHub always treats as verified (operator's choice, 2026-11-19). Every git call below runs
# neutralised (no user/system config, no hooks).
GH_LOGIN="jlcatonjr"
EMAIL="12754578+jlcatonjr@users.noreply.github.com"
NAME="$(git config user.name)"
[ -n "$NAME" ] || die "set git user.name in $MAIN first"
[ "$(gh api "users/$GH_LOGIN" -q .id)" = "${EMAIL%%+*}" ] || die "the no-reply address does not carry the account id of $GH_LOGIN"
# GitHub shows a tag as verified only if the signing key is registered on the tagger's account as a SIGNING key.
# Checked before anything is pushed or signed (public key list; no token scope needed).
SIGNING_KEYS="$(gh api "users/$GH_LOGIN/ssh_signing_keys" -q '.[].key')" || die "cannot list the signing keys of $GH_LOGIN"
registered=0
while IFS= read -r key; do
  if [ -n "$key" ] && [ "$(printf '%s\n' "$key" | ssh-keygen -lf - | awk '{print $2}')" = "$RELEASE_FP" ]; then registered=1; fi
done <<EOF_KEYS
$SIGNING_KEYS
EOF_KEYS
[ "$registered" = 1 ] || die "the release key $RELEASE_FP is not a signing key on $GH_LOGIN; run 18-register-signing-key.sh first"
ngit fetch --quiet --tags "$RT_URL" "+refs/heads/main:refs/remotes/origin/main"
ngit merge-base --is-ancestor "$SHA" refs/remotes/origin/main || die "$SHA is not on origin/main"
# The cut commit is the release-prep PR's merge commit and nothing later (@security, 2026-11-19).
PR_MERGE="$(gh pr view 229 -R "$REPO" --json mergeCommit -q .mergeCommit.oid)" || die "cannot read the merge commit of PR #229"
[ "$SHA" = "$PR_MERGE" ] || die "$SHA is not the merge commit of PR #229 (${PR_MERGE:-none})"

# The agentteams pin at that commit: v1.2.1 (AT_TAG), verified HERE (signature, self-name, remote object), in the lock and
# in both extras.
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
ngit init -q "$TMP/at"
ngit -C "$TMP/at" fetch -q --no-tags "$AT_REPO_URL" "refs/tags/$AT_TAG:refs/tags/$AT_TAG" || die "agentteams $AT_TAG is not tagged"
verify_tag "$TMP/at" "$AT_TAG"
AT_OBJ="$(ngit -C "$TMP/at" rev-parse "refs/tags/$AT_TAG")"
AT_PEELED="$(ngit -C "$TMP/at" rev-parse "refs/tags/$AT_TAG^{commit}")"
[ "$(ngit ls-remote "$AT_REPO_URL" "refs/tags/$AT_TAG" | cut -f1)" = "$AT_OBJ" ] || die "remote $AT_TAG object differs from the verified one"
ngit show "$SHA:toolchain.lock" | grep -x "agentteams=jlcatonjr/agentteams@$AT_PEELED" >/dev/null || die "lock at $SHA is not pinned to $AT_TAG ($AT_PEELED)"
ngit show "$SHA:toolchain.lock" | grep -x "agentteams.tag=$AT_TAG" >/dev/null || die "lock at $SHA is not release-locked at $AT_TAG"
[ "$(ngit show "$SHA:pyproject.toml" | grep -c "jlcatonjr/agentteams@$AT_PEELED")" = 2 ] || die "the update/research extras at $SHA do not both pin $AT_PEELED"
[ "$(ngit show "$SHA:.github/agentteams-autosync-ref")" = "$AT_PEELED" ] || die "the autosync ref at $SHA is not $AT_PEELED"
LOG="$(ngit show "$SHA:.github/agents/references/security-decisions.log.csv")"
# A group-member pin move needs no per-release row (ruling R16, 2026-11-14). The rows it rests on must be present as
# PASS rows (a text check; their signatures are checked by the gate and by --verify-toolchain-pin below).
for a in release-line-agentteams-1.2 s10-release-cooldown-restored s10-first-party-releases-2026-11 management-roster-enroll:infrastructure-management; do
  printf '%s\n' "$LOG" | grep -F ",$a,PASS," >/dev/null || die "no signed $a row at $SHA"
done
ngit cat-file -e "$SHA:.agentteams/toolchain-group.json" || die "no .agentteams/toolchain-group.json at $SHA"
ngit show "$SHA:CHANGELOG.md" | grep '^## 1.2.1 ' >/dev/null || die "no '## 1.2.1' CHANGELOG entry at $SHA"
NOTES="$(ngit show "$SHA:docs/release/release-notes-v1.2.1.md")" || die "no docs/release/release-notes-v1.2.1.md at $SHA"
# The group file is what lets the pin move without a per-release row, so it must VERIFY at $SHA (signature,
# workspace binding, no HALT on s10-toolchain-group), not merely exist (@security, 2026-11-15). Run from the
# root-owned agentteams v1.1.4 install, in a detached worktree of $SHA so the workspace binding sees origin.
AGENTTEAMS_BIN="<signer>"   # root-owned install built from agentteams tag v1.1.4
[[ -x "$AGENTTEAMS_BIN" && "$(/usr/bin/stat -f %Su "$AGENTTEAMS_BIN")" == root ]] || die "no root-owned agentteams at $AGENTTEAMS_BIN"
ngit worktree add -q --detach "$TMP/rt" "$SHA" || die "cannot check out $SHA for the group-file check"
trap 'ngit worktree remove --force "$TMP/rt" 2>/dev/null; rm -rf "$TMP"' EXIT
( cd "$TMP/rt" && "$AGENTTEAMS_BIN" --verify-toolchain-pin toolchain.lock --allowed-signers "$ALLOWED_SIGNERS" \
    --output .github/agents --description brief.json ) || die "the toolchain-group pin does not verify at $SHA (must exit 0)"
# The line-move row must CLEAR at $SHA (signature, lineage, no later HALT or retraction), not merely be present as
# text (@security, 2026-11-19; C-2). Same non-consuming gate check as 14-sign-release-line-1.2.sh, from an empty cwd.
mkdir "$TMP/empty"
( cd "$TMP/empty" && "${AGENTTEAMS_BIN%/agentteams}/python" -I -P - "$TMP/rt/.github/agents" release-line-agentteams-1.2 ) <<'PY' || die "release-line-agentteams-1.2 does not clear at $SHA; nothing was pushed or signed"
import sys
from pathlib import Path
from agentteams.cli.security_gate import check_clearance
ok, why = check_clearance(Path(sys.argv[1]), action=sys.argv[2], consume=False) if "consume" in check_clearance.__code__.co_varnames else check_clearance(Path(sys.argv[1]), action=sys.argv[2])
print(f"  {sys.argv[2]}: {'clears' if ok else 'REFUSED: ' + str(why)[:200]}")
sys.exit(0 if ok else 1)
PY
ngit rev-parse -q --verify "refs/tags/$TAG" >/dev/null && die "$TAG already exists; tags are immutable. If an earlier run signed it here but did not push it, stop and tell the researchteam session; do not delete it yourself"
existing="$(ngit ls-remote "$RT_URL" refs/heads/release/1.2 | cut -f1)"
[ -n "$existing" ] || die "release/1.2 does not exist (rc.1 cut it)"
ngit fetch -q "$RT_URL" "refs/heads/release/1.2:refs/remotes/origin/release/1.2"
ngit merge-base --is-ancestor "$existing" "$SHA" || die "$SHA does not contain release/1.2 ($existing): not a fast-forward"
# The previous release must be signed and be an ancestor: v1.2.1 is v1.2.0 plus the fix and docs.
PREV_OBJ="c621290a2f45891a483e088ce33f3becbfc39a79"   # v1.2.0 tag object, verified at its cut (2026-11-19)
[ "$(ngit rev-parse "refs/tags/v1.2.0")" = "$PREV_OBJ" ] || die "local v1.2.0 is not tag object $PREV_OBJ"
[ "$(ngit ls-remote "$RT_URL" "refs/tags/v1.2.0" | cut -f1)" = "$PREV_OBJ" ] || die "remote v1.2.0 is not tag object $PREV_OBJ"
verify_tag "$MAIN" "v1.2.0"
ngit merge-base --is-ancestor "refs/tags/v1.2.0^{commit}" "$SHA" || die "$SHA does not contain v1.2.0"
# "The fix plus docs" is enforced, not just stated: every path changed since v1.2.0 must be the fix, its test, or
# documentation and records. In particular no pin, lock, workflow, agent or script file may differ.
CHANGED="$(ngit diff --no-renames --name-only "refs/tags/v1.2.0^{commit}" "$SHA")" || die "cannot list the changes since v1.2.0"
[ -n "$CHANGED" ] || die "$SHA changes nothing since v1.2.0"
printf '%s\n' "$CHANGED" | grep -qxF "researchteam/_release.py" || die "$SHA does not carry the verify_tag fix"
EXTRA="$(printf '%s\n' "$CHANGED" | grep -vxE 'CHANGELOG\.md|researchteam/_release\.py|tests/test_release_lock\.py|(docs|docs_src|references/plans|workSummaries)/.*' || true)"
[ -z "$EXTRA" ] || die "changes since v1.2.0 outside the fix and docs: $(printf '%s' "$EXTRA" | tr '\n' ' ')"

say "release/1.2 and $TAG at $SHA (pins agentteams $AT_TAG ${AT_PEELED:0:12})"
ngit log -1 --format='  %h %s' "$SHA"
echo "  Paths that differ from v1.2.0:"; printf '%s\n' "$CHANGED" | sed 's/^/    /'
confirm "Fast-forward release/1.2 ${existing:0:12} -> ${SHA:0:12} and sign $TAG there?"
# Pushes use your credentials (so plain git, but no hooks and an explicit URL); everything else stays neutralised.
[ "$existing" = "$SHA" ] || git -c core.hooksPath=/dev/null push --quiet "$RT_URL" "$SHA:refs/heads/release/1.2"
[ "$(ngit ls-remote "$RT_URL" refs/heads/release/1.2 | cut -f1)" = "$SHA" ] || die "remote release/1.2 is not at $SHA after the push; nothing was signed"
ngit -c user.name="$NAME" -c user.email="$EMAIL" -c gpg.format=ssh -c gpg.ssh.program=/usr/bin/ssh-keygen \
  -c user.signingkey="$RELEASE_PUB" tag -s "$TAG" "$SHA" -m "researchteam 1.2.1 — patch release on the 1.2 line (release/1.2): tag verification fetches only the tag

Pins agentteams $AT_TAG ($AT_PEELED). See CHANGELOG.md and docs/release-policy.md."
verify_tag "$MAIN" "$TAG"
[ "$(ngit describe --tags --match 'v[0-9]*' --exact-match "$SHA")" = "$TAG" ] || die "git describe does not name $TAG at $SHA"
OBJ="$(ngit rev-parse "refs/tags/$TAG")"; PEELED="$(ngit rev-parse "refs/tags/$TAG^{commit}")"
[ "$PEELED" = "$SHA" ] || die "peeled $PEELED != $SHA"
confirm "Push $TAG (object ${OBJ:0:12}) to origin?"
git -c core.hooksPath=/dev/null push --quiet "$RT_URL" "refs/tags/$TAG"
[ "$(ngit ls-remote "$RT_URL" "refs/tags/$TAG" | cut -f1)" = "$OBJ" ] || die "remote tag object differs"
if ! gh release view "$TAG" -R "$REPO" >/dev/null 2>&1; then
  drain; read -r -p "Create the GitHub release for $TAG (latest, not a pre-release)? [y/N] " a
  if [ "$a" = y ]; then
    gh release create "$TAG" -R "$REPO" --verify-tag --latest --title "researchteam 1.2.1" --notes "$NOTES" \
      || echo "  WARNING: the GitHub release was not created; the tag is signed and pushed. Tell the researchteam session."
  fi
fi
# Report only: the tag is public and immutable, so nothing here can stop or undo the release.
VERIFIED="unknown"
for _ in 1 2 3 4 5 6; do
  VERIFIED="$(gh api "repos/$REPO/git/tags/$OBJ" -q '"\(.verification.verified) (\(.verification.reason))"' 2>/dev/null || echo unknown)"
  case "$VERIFIED" in true*) break ;; esac
  sleep 10
done
say "Signed and pushed $TAG"
echo "  tag object : $OBJ"
echo "  peeled     : $PEELED"
echo "  GitHub verification : $VERIFIED"
echo "Tell the researchteam session. Derived repos take it as an ordinary patch release (see the release notes)."
