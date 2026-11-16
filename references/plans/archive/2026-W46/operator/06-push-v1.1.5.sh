#!/usr/bin/env bash
# 06 — Resume the v1.1.5 cut after 05 stopped at the push prompt (a typed-ahead "y" made the answer "yy").
# 05 already fast-forwarded release/1.1 to 24605ba1 and signed v1.1.5 locally (object e7aed53a). This script only
# re-verifies that local tag exactly as 05 did, pushes it, and offers the GitHub release. It never re-signs.
# OPERATOR ONLY, plain Terminal, from any directory:
#   bash <checkout>/tmp/by-week/2026-W46/operator/06-push-v1.1.5.sh
source "$(dirname "$0")/common.sh"
refuse_agent
TAG="v1.1.5"
SHA="24605ba1414fef9739720825d2c4c9689285d0e1"
OBJ_EXPECTED="e7aed53ad0aecf97e7a5c4186691a4f02d902de5"
RT_URL="https://github.com/$REPO"
cd "$MAIN"
NOTES="$(ngit show "$SHA:docs/release/release-notes-v1.1.5.md")" || die "no docs/release/release-notes-v1.1.5.md at $SHA"
[ "$(ngit ls-remote "$RT_URL" refs/heads/release/1.1 | cut -f1)" = "$SHA" ] || die "remote release/1.1 is not $SHA"
[ -z "$(ngit ls-remote "$RT_URL" "refs/tags/$TAG")" ] || die "$TAG is already on origin"
OBJ="$(ngit rev-parse "refs/tags/$TAG")"; PEELED="$(ngit rev-parse "refs/tags/$TAG^{commit}")"
[ "$OBJ" = "$OBJ_EXPECTED" ] || die "local $TAG object $OBJ is not the one 05 signed ($OBJ_EXPECTED)"
[ "$PEELED" = "$SHA" ] || die "peeled $PEELED != $SHA"
verify_tag "$MAIN" "$TAG"
say "$TAG verified locally: object $OBJ, peeled $PEELED, release key"
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
echo "Tell the researchteam session."
