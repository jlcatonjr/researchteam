#!/usr/bin/env bash
# 05 — Fast-forward release/1.1 to a reviewed main commit and sign researchteam v1.1.5 with the release key.
# Patch release: #172 (autosync stranded branch), #173 (unfenced CLAUDE.md append), #165, #161. Copied from
# 2026-W45/19-cut-v1.1.1.sh. The agentteams pin stays v1.1.3.
# OPERATOR ONLY, plain Terminal, from any directory:
#   bash <checkout>/tmp/by-week/2026-W46/operator/05-cut-v1.1.5.sh <40-hex reviewed main SHA>
# Run it after the release-prep PR has merged, with that merge commit. It checks the pin, the toolchain-group file and
# the CHANGELOG AT the given commit, requires a fast-forward of release/1.1, asks before each push, verifies the new tag
# exactly as consumers will, and offers the GitHub release. release/1.1 then equals main at that commit, so no
# merge-forward is needed.
source "$(dirname "$0")/common.sh"
refuse_agent
TAG="v1.1.5"; AT_TAG="v1.1.3"
SHA="${1:?usage: $0 <40-hex reviewed main SHA>}"
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || die "the commit must be a full 40-hex SHA"
fp="$(ssh-keygen -lf "$RELEASE_PUB" | awk '{print $2}')"
[ "$fp" = "$RELEASE_FP" ] || die "$RELEASE_PUB is $fp, not the release key $RELEASE_FP"
RT_URL="https://github.com/$REPO"
cd "$MAIN"
# Identity for the tag, read once; every git call below runs neutralised (no user/system config, no hooks).
NAME="$(git config user.name)"; EMAIL="$(git config user.email)"
[ -n "$NAME" ] && [ -n "$EMAIL" ] || die "set git user.name / user.email in $MAIN first"
ngit fetch --quiet --tags "$RT_URL" "+refs/heads/main:refs/remotes/origin/main"
ngit merge-base --is-ancestor "$SHA" refs/remotes/origin/main || die "$SHA is not on origin/main"

# The agentteams pin at that commit: v1.1.3 (AT_TAG), verified HERE (signature, self-name, remote object), in the lock and
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
LOG="$(ngit show "$SHA:.github/agents/references/security-decisions.log.csv")"
# A group-member pin move needs no per-release row (ruling R16, 2026-11-14). The rows it rests on must be present as
# PASS rows (a text check; their signatures are checked by the gate and by --verify-toolchain-pin below).
for a in release-line-agentteams-1.1 s10-release-cooldown-restored s10-first-party-releases-2026-11 management-roster-enroll:infrastructure-management; do
  printf '%s\n' "$LOG" | grep -F ",$a,PASS," >/dev/null || die "no signed $a row at $SHA"
done
ngit cat-file -e "$SHA:.agentteams/toolchain-group.json" || die "no .agentteams/toolchain-group.json at $SHA"
ngit show "$SHA:CHANGELOG.md" | grep '^## 1.1.5 ' >/dev/null || die "no '## 1.1.5' CHANGELOG entry at $SHA"
NOTES="$(ngit show "$SHA:docs/release/release-notes-v1.1.5.md")" || die "no docs/release/release-notes-v1.1.5.md at $SHA"
# The group file is what lets the pin move without a per-release row, so it must VERIFY at $SHA (signature,
# workspace binding, no HALT on s10-toolchain-group), not merely exist (@security, 2026-11-15). Run from the
# root-owned agentteams v1.1.3 install, in a detached worktree of $SHA so the workspace binding sees origin.
AGENTTEAMS_BIN="<signer>"   # root-owned install built from agentteams tag v1.1.3
[[ -x "$AGENTTEAMS_BIN" && "$(/usr/bin/stat -f %Su "$AGENTTEAMS_BIN")" == root ]] || die "no root-owned agentteams at $AGENTTEAMS_BIN"
ngit worktree add -q --detach "$TMP/rt" "$SHA" || die "cannot check out $SHA for the group-file check"
trap 'ngit worktree remove --force "$TMP/rt" 2>/dev/null; rm -rf "$TMP"' EXIT
( cd "$TMP/rt" && "$AGENTTEAMS_BIN" --verify-toolchain-pin toolchain.lock --allowed-signers "$ALLOWED_SIGNERS" \
    --output .github/agents --description brief.json ) || die "the toolchain-group pin does not verify at $SHA (must exit 0)"
ngit rev-parse -q --verify "refs/tags/$TAG" >/dev/null && die "$TAG already exists; tags are immutable"
existing="$(ngit ls-remote "$RT_URL" refs/heads/release/1.1 | cut -f1)"
[ -n "$existing" ] || die "release/1.1 does not exist (rc.1 cut it)"
ngit fetch -q "$RT_URL" "refs/heads/release/1.1:refs/remotes/origin/release/1.1"
ngit merge-base --is-ancestor "$existing" "$SHA" || die "$SHA does not contain release/1.1 ($existing): not a fast-forward"

say "release/1.1 and $TAG at $SHA (pins agentteams $AT_TAG ${AT_PEELED:0:12})"
ngit log -1 --format='  %h %s' "$SHA"
confirm "Fast-forward release/1.1 ${existing:0:12} -> ${SHA:0:12} and sign $TAG there?"
# Pushes use your credentials (so plain git, but no hooks and an explicit URL); everything else stays neutralised.
[ "$existing" = "$SHA" ] || git -c core.hooksPath=/dev/null push --quiet "$RT_URL" "$SHA:refs/heads/release/1.1"
ngit -c user.name="$NAME" -c user.email="$EMAIL" -c gpg.format=ssh -c gpg.ssh.program=/usr/bin/ssh-keygen \
  -c user.signingkey="$RELEASE_PUB" tag -s "$TAG" "$SHA" -m "researchteam 1.1.5 — patch release (release/1.1): autosync stranded-branch fix (#172), unfenced CLAUDE.md append (#173)

Pins agentteams $AT_TAG ($AT_PEELED). See CHANGELOG.md and docs/release-policy.md."
verify_tag "$MAIN" "$TAG"
[ "$(ngit describe --tags --match 'v[0-9]*' --exact-match "$SHA")" = "$TAG" ] || die "git describe does not name $TAG at $SHA"
OBJ="$(ngit rev-parse "refs/tags/$TAG")"; PEELED="$(ngit rev-parse "refs/tags/$TAG^{commit}")"
[ "$PEELED" = "$SHA" ] || die "peeled $PEELED != $SHA"
confirm "Push $TAG (object ${OBJ:0:12}) to origin?"
git -c core.hooksPath=/dev/null push --quiet "$RT_URL" "refs/tags/$TAG"
[ "$(ngit ls-remote "$RT_URL" "refs/tags/$TAG" | cut -f1)" = "$OBJ" ] || die "remote tag object differs"
if ! gh release view "$TAG" -R "$REPO" >/dev/null 2>&1; then
  read -r -p "Create the GitHub release for $TAG (latest, not a pre-release)? [y/N] " a
  [ "$a" = y ] && gh release create "$TAG" -R "$REPO" --verify-tag --latest --title "researchteam 1.1.5" \
    --notes "$NOTES"
fi
say "Signed and pushed $TAG"
echo "  tag object : $OBJ"
echo "  peeled     : $PEELED"
echo "Tell the researchteam session. Derived repos move with: researchteam update --ref $TAG"
