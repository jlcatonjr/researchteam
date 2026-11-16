#!/usr/bin/env bash
# 07 — Create the GitHub release page for the already-pushed v1.1.5 tag (06's release prompt got "h", not "y").
# Creates no tag: --verify-tag refuses unless v1.1.5 already exists on origin. Checks the remote tag is the one 05 signed.
# OPERATOR ONLY, plain Terminal, from any directory:
#   bash ~/githubrepositories/researchteam/tmp/by-week/2026-W46/operator/07-release-page-v1.1.5.sh
source "$(dirname "$0")/common.sh"
refuse_agent
TAG="v1.1.5"
SHA="24605ba1414fef9739720825d2c4c9689285d0e1"
OBJ="e7aed53ad0aecf97e7a5c4186691a4f02d902de5"
RT_URL="https://github.com/$REPO"
cd "$MAIN"
[ "$(ngit ls-remote "$RT_URL" "refs/tags/$TAG" | cut -f1)" = "$OBJ" ] || die "origin's $TAG is not object $OBJ"
gh release view "$TAG" -R "$REPO" >/dev/null 2>&1 && die "the release for $TAG already exists"
NOTES="$(ngit show "$SHA:docs/release/release-notes-v1.1.5.md")" || die "no docs/release/release-notes-v1.1.5.md at $SHA"
printf 'Release notes:\n%s\n\n' "$NOTES"
confirm "Create the GitHub release for $TAG (latest, not a pre-release)?"
gh release create "$TAG" -R "$REPO" --verify-tag --latest --title "researchteam 1.1.5" --notes "$NOTES"
gh release view "$TAG" -R "$REPO" --json tagName,isDraft,isPrerelease,url
say "Release page for $TAG created. Tell the researchteam session."
