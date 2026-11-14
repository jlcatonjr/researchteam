#!/usr/bin/env bash
# 06 — Sign a release candidate at the head of release/1.0 (rc.2 onward; rc.1 used 05).
# Usage: 06-sign-rc.sh v1.0.0-rc.N
# release/1.0 must already hold the backport (a regular merge or cherry-pick -x PR) and a matching CHANGELOG entry.
# Verifies the tag as consumers will, pushes it, creates the GitHub pre-release, and prints the tag object and the
# peeled SHA. Afterwards the researchteam session merges release/1.0 forward into main (release policy).
source "$(dirname "$0")/common.sh"
refuse_agent
need_rc11
TAG="${1:-}"
[[ "$TAG" =~ ^v1\.0\.0-rc\.([0-9]+)$ ]] || die "usage: $0 v1.0.0-rc.N"
VER="1.0.0rc${BASH_REMATCH[1]}"
fp="$(ssh-keygen -lf "$RELEASE_PUB" | awk '{print $2}')"
[ "$fp" = "$RELEASE_FP" ] || die "$RELEASE_PUB is $fp, not the release key $RELEASE_FP"
cd "$MAIN"
git fetch --quiet origin --tags
SHA="$(git rev-parse origin/release/1.0)"
git show "$SHA:CHANGELOG.md" | grep -q "^## $VER " || die "release/1.0 has no '## $VER' CHANGELOG entry (backport first)"
git show "$SHA:toolchain.lock" | grep -qx "agentteams=jlcatonjr/agentteams@$AT_PEELED" || die "release/1.0's lock does not pin agentteams $AT_PEELED"
git show "$SHA:toolchain.lock" | grep -qx "agentteams.tag=$AT_TAG" || die "release/1.0's lock is not release-locked at $AT_TAG"
git show "$SHA:pyproject.toml" | grep -q "@$AT_PEELED" || die "release/1.0's extras do not pin $AT_PEELED"
git rev-parse -q --verify "refs/tags/$TAG" >/dev/null && die "$TAG already exists; tags are immutable"

say "$TAG at release/1.0 $SHA"
git log -1 --format='  %h %s' "$SHA"
confirm "Sign $TAG at ${SHA:0:12}?"
git -c gpg.format=ssh -c user.signingkey="$RELEASE_PUB" -c core.hooksPath=/dev/null \
  tag -s "$TAG" "$SHA" -m "researchteam $VER (release/1.0)

Pins agentteams $AT_TAG ($AT_PEELED). See CHANGELOG.md and docs/release-policy.md."
verify_tag "$MAIN" "$TAG"
OBJ="$(git rev-parse "refs/tags/$TAG")"; PEELED="$(git rev-parse "refs/tags/$TAG^{commit}")"
[ "$PEELED" = "$SHA" ] || die "peeled $PEELED != $SHA"
git push --quiet origin "refs/tags/$TAG"
[ "$(ngit ls-remote origin "refs/tags/$TAG" | cut -f1)" = "$OBJ" ] || die "remote tag object differs"
state_set "TAG_${TAG//[.-]/_}" "$OBJ $PEELED"
if ! gh release view "$TAG" -R "$REPO" >/dev/null 2>&1; then
  confirm "Create a GitHub pre-release for $TAG?" && \
    gh release create "$TAG" -R "$REPO" --verify-tag --prerelease --title "researchteam $VER" \
      --notes "Release candidate on release/1.0. Pins agentteams $AT_TAG. See CHANGELOG.md."
fi
say "Signed and pushed $TAG"
echo "  tag object : $OBJ"
echo "  peeled     : $PEELED"
echo "Tell the researchteam session: it verifies, merges release/1.0 forward into main, and announces."
