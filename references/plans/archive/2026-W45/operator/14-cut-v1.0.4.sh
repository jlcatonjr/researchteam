#!/usr/bin/env bash
# 14 — Sign researchteam v1.0.4 with the release key on the #144 merge commit on release/1.0. Modelled on 11-cut-rc5.sh.
# OPERATOR ONLY, plain Terminal:
#   bash ~/githubrepositories/researchteam/tmp/by-week/2026-W45/operator/14-cut-v1.0.4.sh <40-hex #144 merge commit>
# Run it after 13. It checks AT the given commit: the commit is the tip of release/1.0, the agentteams v1.0.7 pin
# (verified here), the signed rows and the 1.0.4 CHANGELOG entry. It then signs the tag, verifies it exactly as
# consumers will, pushes it, and offers a GitHub release marked Latest (as 1.0.3 was). release/1.0 is not moved:
# the merge already put the commit there. Derived repos on the 1.0 line move with --researchteam-tag v1.0.4.
source "$(dirname "$0")/common.sh"
refuse_agent
TAG="v1.0.4"; AT_TAG="v1.0.7"; BASE="release/1.0"
SHA="${1:?usage: $0 <40-hex #144 merge commit>}"
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || die "the commit must be a full 40-hex SHA"
fp="$(ssh-keygen -lf "$RELEASE_PUB" | awk '{print $2}')"
[ "$fp" = "$RELEASE_FP" ] || die "$RELEASE_PUB is $fp, not the release key $RELEASE_FP"
RT_URL="https://github.com/$REPO"
cd "$MAIN"
# Identity for the tag, read once; every git call below runs neutralised (no user/system config, no hooks).
NAME="$(git config user.name)"; EMAIL="$(git config user.email)"
[ -n "$NAME" ] && [ -n "$EMAIL" ] || die "set git user.name / user.email in $MAIN first"
ngit fetch --quiet --tags "$RT_URL" "+refs/heads/$BASE:refs/remotes/origin/$BASE"
tip="$(ngit ls-remote "$RT_URL" "refs/heads/$BASE" | cut -f1)"
[ "$tip" = "$SHA" ] || die "$BASE is at $tip, not $SHA (run 13 first, or pass its merge commit)"

# The agentteams pin at that commit: v1.0.7 (AT_TAG), verified HERE (signature, self-name, remote object), in the lock
# and in both extras.
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
ngit show "$SHA:brief.json" | grep -F '"jlcatonjr/agentteams"' >/dev/null || die "brief.json at $SHA does not list jlcatonjr/agentteams in s10_cooldown_exempt_repos"
LOG="$(ngit show "$SHA:.github/agents/references/security-decisions.log.csv")"
for a in release-policy-1.0 s10-release-cooldown-restored s10-cooldown-exempt:jlcatonjr/agentteams "pin-agentteams-$AT_TAG"; do
  printf '%s\n' "$LOG" | grep -F ",$a,PASS," >/dev/null || die "no signed $a row at $SHA"
done
ROW="$(printf '%s\n' "$LOG" | grep -F ",pin-agentteams-$AT_TAG,PASS,")"
printf '%s\n' "$ROW" | grep -F "$AT_OBJ" >/dev/null || die "the pin row does not name tag object $AT_OBJ"
printf '%s\n' "$ROW" | grep -F "$AT_PEELED" >/dev/null || die "the pin row does not name peeled $AT_PEELED"
ngit show "$SHA:CHANGELOG.md" | grep '^## 1.0.4 ' >/dev/null || die "no '## 1.0.4' CHANGELOG entry at $SHA"
ngit rev-parse -q --verify "refs/tags/$TAG" >/dev/null && die "$TAG already exists; tags are immutable"
ngit merge-base --is-ancestor "$(ngit rev-parse 'refs/tags/v1.0.3^{commit}')" "$SHA" || die "$SHA does not contain v1.0.3"

say "$TAG at $SHA on $BASE (pins agentteams $AT_TAG ${AT_PEELED:0:12})"
ngit log -1 --format='  %h %s' "$SHA"
confirm "Sign $TAG at ${SHA:0:12}?"
ngit -c user.name="$NAME" -c user.email="$EMAIL" -c gpg.format=ssh -c gpg.ssh.program=/usr/bin/ssh-keygen \
  -c user.signingkey="$RELEASE_PUB" tag -s "$TAG" "$SHA" -m "researchteam 1.0.4 — patch release on release/1.0

Pins agentteams $AT_TAG ($AT_PEELED). Restores the S-10 cooldown with the local-repository carve-out
(s10_cooldown_exempt_repos: jlcatonjr/agentteams) and pins pip in the bootstrap. See CHANGELOG.md and docs/release-policy.md."
verify_tag "$MAIN" "$TAG"
[ "$(ngit describe --tags --match 'v[0-9]*' --exact-match "$SHA")" = "$TAG" ] || die "git describe does not name $TAG at $SHA"
OBJ="$(ngit rev-parse "refs/tags/$TAG")"; PEELED="$(ngit rev-parse "refs/tags/$TAG^{commit}")"
[ "$PEELED" = "$SHA" ] || die "peeled $PEELED != $SHA"
confirm "Push $TAG (object ${OBJ:0:12}) to origin?"
git -c core.hooksPath=/dev/null push --quiet "$RT_URL" "refs/tags/$TAG"
[ "$(ngit ls-remote "$RT_URL" "refs/tags/$TAG" | cut -f1)" = "$OBJ" ] || die "remote tag object differs"
if ! gh release view "$TAG" -R "$REPO" >/dev/null 2>&1; then
  read -r -p "Create the GitHub release for $TAG (marked Latest, as 1.0.3)? [y/N] " a
  [ "$a" = y ] && gh release create "$TAG" -R "$REPO" --verify-tag --latest --title "researchteam 1.0.4" \
    --notes "Patch release on release/1.0. Pins agentteams $AT_TAG; restores the S-10 cooldown with the local-repository carve-out (jlcatonjr/agentteams); pins pip in the bootstrap. See CHANGELOG.md."
fi
say "Signed and pushed $TAG"
echo "  tag object : $OBJ"
echo "  peeled     : $PEELED"
echo "Tell the researchteam session; derived repos on the 1.0 line move with --researchteam-tag $TAG."
