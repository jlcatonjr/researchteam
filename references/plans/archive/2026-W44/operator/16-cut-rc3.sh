#!/usr/bin/env bash
# 16 — Fast-forward release/1.1 to a reviewed main commit (1.1.0rc3) and sign researchteam v1.1.0-rc.3 with the release key.
# Modelled on 2026-W43/operator/15-cut-rc2.sh.
# OPERATOR ONLY, plain Terminal:
#   bash ~/githubrepositories/researchteam/tmp/by-week/2026-W44/operator/16-cut-rc3.sh <40-hex reviewed main SHA>
# Run it after the release-prep/1.1.0rc3 PR (the signed pin-agentteams-v1.1.0-rc.11 row and the 1.1.0rc3 CHANGELOG
# entry; the rc.11 pin itself is #132) has merged to main. It checks all of that AT the
# given commit, requires it to be a fast-forward of release/1.1, verifies the new tag exactly as consumers will,
# fast-forwards release/1.1, pushes the tag, and prints the tag object and peeled SHA. release/1.1 then equals main
# at that commit, so no merge-forward is needed. Derived repos move with --researchteam-tag v1.1.0-rc.3.
source "$(dirname "$0")/common.sh"
refuse_agent
TAG="v1.1.0-rc.3"; AT_TAG="v1.1.0-rc.11"
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

# The agentteams pin at that commit: rc.11 (AT_TAG), verified HERE (signature, self-name, remote object), in the lock and
# in both extras.
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
ngit init -q "$TMP/at"
ngit -C "$TMP/at" fetch -q --no-tags "$AT_REPO_URL" "refs/tags/$AT_TAG:refs/tags/$AT_TAG" || die "agentteams $AT_TAG is not tagged"
verify_tag "$TMP/at" "$AT_TAG"
AT_OBJ="$(ngit -C "$TMP/at" rev-parse "refs/tags/$AT_TAG")"
AT_PEELED="$(ngit -C "$TMP/at" rev-parse "refs/tags/$AT_TAG^{commit}")"
[ "$(ngit ls-remote "$AT_REPO_URL" "refs/tags/$AT_TAG" | cut -f1)" = "$AT_OBJ" ] || die "remote $AT_TAG object differs from the verified one"
ngit show "$SHA:toolchain.lock" | grep -qx "agentteams=jlcatonjr/agentteams@$AT_PEELED" || die "lock at $SHA is not pinned to $AT_TAG ($AT_PEELED)"
ngit show "$SHA:toolchain.lock" | grep -qx "agentteams.tag=$AT_TAG" || die "lock at $SHA is not release-locked at $AT_TAG"
[ "$(ngit show "$SHA:pyproject.toml" | grep -c "jlcatonjr/agentteams@$AT_PEELED")" = 2 ] || die "the update/research extras at $SHA do not both pin $AT_PEELED"
LOG="$(ngit show "$SHA:.github/agents/references/security-decisions.log.csv")"
for a in release-line-agentteams-1.1 s10-release-cooldown-deprecated "pin-agentteams-$AT_TAG"; do
  printf '%s\n' "$LOG" | grep -qF ",$a,PASS," || die "no signed $a row at $SHA"
done
ROW="$(printf '%s\n' "$LOG" | grep -F ",pin-agentteams-$AT_TAG,PASS,")"
printf '%s\n' "$ROW" | grep -qF "$AT_OBJ" || die "the pin row does not name tag object $AT_OBJ"
printf '%s\n' "$ROW" | grep -qF "$AT_PEELED" || die "the pin row does not name peeled $AT_PEELED"
ngit show "$SHA:CHANGELOG.md" | grep -q '^## 1.1.0rc3' || die "no '## 1.1.0rc3' CHANGELOG entry at $SHA"
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
  -c user.signingkey="$RELEASE_PUB" tag -s "$TAG" "$SHA" -m "researchteam 1.1.0rc3 — third 1.1 release candidate (release/1.1)

Pins agentteams $AT_TAG ($AT_PEELED). See CHANGELOG.md and docs/release-policy.md."
verify_tag "$MAIN" "$TAG"
[ "$(ngit describe --tags --match 'v[0-9]*' --exact-match "$SHA")" = "$TAG" ] || die "git describe does not name $TAG at $SHA"
OBJ="$(ngit rev-parse "refs/tags/$TAG")"; PEELED="$(ngit rev-parse "refs/tags/$TAG^{commit}")"
[ "$PEELED" = "$SHA" ] || die "peeled $PEELED != $SHA"
confirm "Push $TAG (object ${OBJ:0:12}) to origin?"
git -c core.hooksPath=/dev/null push --quiet "$RT_URL" "refs/tags/$TAG"
[ "$(ngit ls-remote "$RT_URL" "refs/tags/$TAG" | cut -f1)" = "$OBJ" ] || die "remote tag object differs"
if ! gh release view "$TAG" -R "$REPO" >/dev/null 2>&1; then
  read -r -p "Create a GitHub pre-release for $TAG? [y/N] " a
  [ "$a" = y ] && gh release create "$TAG" -R "$REPO" --verify-tag --prerelease --title "researchteam 1.1.0rc3" \
    --notes "Third 1.1 release candidate. Pins agentteams $AT_TAG (vulnscan remediation fixes). See CHANGELOG.md."
fi
say "Signed and pushed $TAG"
echo "  tag object : $OBJ"
echo "  peeled     : $PEELED"
echo "Tell the researchteam session (researchteam-a5); derived repos move with --researchteam-tag $TAG."
