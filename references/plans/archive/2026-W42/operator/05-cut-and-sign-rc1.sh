#!/usr/bin/env bash
# 05 — Cut release/1.0 at main (1.0.0rc1) and sign v1.0.0-rc.1 with the release key, from this terminal.
# Verifies the tag exactly as consumers will, then pushes it and prints the tag object and peeled SHA
# for agentteams and mathAgents.
source "$(dirname "$0")/common.sh"
refuse_agent
need_rc11
TAG="v1.0.0-rc.1"
fp="$(ssh-keygen -lf "$RELEASE_PUB" | awk '{print $2}')"
[ "$fp" = "$RELEASE_FP" ] || die "$RELEASE_PUB is $fp, not the release key $RELEASE_FP"
cd "$MAIN"
git fetch --quiet origin --tags
SHA="$(git rev-parse origin/main)"
git show "$SHA:pyproject.toml" | grep -qx 'dynamic = \["version"\]' || die "origin/main does not derive its version from tags (#57 not merged?)"
git show "$SHA:CHANGELOG.md" | grep -q '^## 1.0.0rc1' || die "origin/main has no 1.0.0rc1 CHANGELOG entry (run 04 first)"
git show "$SHA:toolchain.lock" | grep -qx "agentteams=jlcatonjr/agentteams@$AT_PEELED" || die "lock not pinned to $AT_PEELED"
git show "$SHA:toolchain.lock" | grep -qx "agentteams.tag=$AT_TAG" || die "lock not release-locked at $AT_TAG"
git rev-parse -q --verify "refs/tags/$TAG" >/dev/null && die "$TAG already exists; tags are immutable"
existing="$(git ls-remote origin refs/heads/release/1.0 | cut -f1)"
[ -z "$existing" ] || [ "$existing" = "$SHA" ] || die "release/1.0 exists at $existing, not $SHA"

say "release/1.0 and $TAG at $SHA"
git log -1 --format='  %h %s' "$SHA"
confirm "Cut release/1.0 and sign $TAG at ${SHA:0:12}?"
[ -n "$existing" ] || git push --quiet origin "$SHA:refs/heads/release/1.0"
git -c gpg.format=ssh -c user.signingkey="$RELEASE_PUB" -c core.hooksPath=/dev/null \
  tag -s "$TAG" "$SHA" -m "researchteam 1.0.0rc1 — first 1.0 release candidate (release/1.0)

Pins agentteams $AT_TAG ($AT_PEELED). See CHANGELOG.md and docs/release-policy.md."
verify_tag "$MAIN" "$TAG"
[ "$(git describe --tags --match 'v[0-9]*' --exact-match "$SHA")" = "$TAG" ] || die "git describe does not name $TAG at $SHA"
OBJ="$(git rev-parse "refs/tags/$TAG")"; PEELED="$(git rev-parse "refs/tags/$TAG^{commit}")"
[ "$PEELED" = "$SHA" ] || die "peeled $PEELED != $SHA"
git push --quiet origin "refs/tags/$TAG"
[ "$(ngit ls-remote origin "refs/tags/$TAG" | cut -f1)" = "$OBJ" ] || die "remote tag object differs"
state_set RC1_TAG_OBJ "$OBJ"; state_set RC1_PEELED "$PEELED"
if gh release view "$TAG" -R "$REPO" >/dev/null 2>&1; then :; else
  confirm "Create a GitHub pre-release for $TAG?" && \
    gh release create "$TAG" -R "$REPO" --verify-tag --prerelease --title "researchteam 1.0.0rc1" \
      --notes "First 1.0 release candidate. Pins agentteams $AT_TAG. See CHANGELOG.md."
fi
say "Signed and pushed $TAG"
echo "  tag object : $OBJ"
echo "  peeled     : $PEELED"
echo "Tell the researchteam session; it passes these to agentteams and mathAgents."
