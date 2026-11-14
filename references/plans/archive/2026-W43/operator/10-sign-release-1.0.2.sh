#!/bin/bash -p
# 10 — Sign, verify, push and publish researchteam's PATCH release tag (v1.0.2) at the head of release/1.0.
# Usage (plain Terminal, never an agent session; ALWAYS `/bin/bash -p <absolute path>`, never `bash <path>`):
#   TAGGER_EMAIL=<e-mail> /bin/bash -p ~/githubrepositories/researchteam/tmp/by-week/2026-W43/operator/10-sign-release-1.0.2.sh \
#     <40-hex release/1.0 head> <release-key-file>
# Adapted for researchteam from agentteams-runner-ops/tag-release.sh (sha256 dc5ccfd0…4809, which signed agentteams
# v1.0.0), with the same hardening: privileged mode only; one env -i re-exec with an allowlist that is then CHECKED
# (never trusted by marker); GIT_*/GH_*/GITHUB_TOKEN/DEVELOPER_DIR/TOOLCHAINS/SDKROOT dropped; global and system git
# config ignored; absolute git, ssh-keygen and gh; tagger and credential helper passed explicitly; everything in a
# fresh clone; verification from git's stderr only, whole line, against the pinned key, BEFORE the y/N and the push.
# researchteam differences: the version comes from the tag (setuptools-scm), so the tag name is fixed (TAG below) and
# checked against the CHANGELOG; the release key is the one the commit's own researchteam/_release.py pins (there is
# no SECURITY.md); the commit must be exactly the head of origin/release/1.0; the lock and extras must pin agentteams
# v1.0.0. It opens and watches no PR.
if [[ $- == *p* ]]; then
builtin unset -f $(builtin compgen -A function) 2>/dev/null; builtin set -euo pipefail
[[ -z "${CLAUDECODE:-}" && -z "${CLAUDE_CODE_ENTRYPOINT:-}" ]] || { echo "error: run this from a plain Terminal, not an agent session" >&2; exit 1; }
env_is_clean() {
  local n
  [[ "${PATH:-}" == /usr/bin:/bin:/usr/sbin:/sbin ]] || return 1
  [[ -z "$(builtin declare -F | /usr/bin/grep -vx 'declare -f env_is_clean')" ]] || return 1
  while IFS= read -r n; do
    case "$n" in
      HOME|TERM|PATH|TAGGER_NAME|TAGGER_EMAIL|SSH_AUTH_SOCK|_RESEARCHTEAM_SIGN_RELEASE_CLEAN) ;;
      GIT_CONFIG_GLOBAL|GIT_CONFIG_NOSYSTEM|PWD|SHLVL|OLDPWD|_) ;;
      *) return 1 ;;
    esac
  done < <(compgen -e)
  return 0
}
if ! env_is_clean; then
  [[ "${_RESEARCHTEAM_SIGN_RELEASE_CLEAN:-}" != 1 ]] || { builtin echo "error: the environment is not clean even after the env -i re-exec; stopping" >&2; builtin exit 1; }
  builtin exec /usr/bin/env -i _RESEARCHTEAM_SIGN_RELEASE_CLEAN=1 HOME="$HOME" TERM="${TERM:-dumb}" \
    PATH=/usr/bin:/bin:/usr/sbin:/sbin \
    ${TAGGER_NAME:+TAGGER_NAME="$TAGGER_NAME"} ${TAGGER_EMAIL:+TAGGER_EMAIL="$TAGGER_EMAIL"} \
    ${SSH_AUTH_SOCK:+SSH_AUTH_SOCK="$SSH_AUTH_SOCK"} \
    /bin/bash -p "$0" "$@"
fi
unset -f env_is_clean
for v in ${!GIT_@} ${!GH_@}; do unset "$v"; done
unset GITHUB_TOKEN DEVELOPER_DIR TOOLCHAINS SDKROOT
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
GIT=/usr/bin/git
SSH_KEYGEN=/usr/bin/ssh-keygen
GH=""
for cand in /opt/homebrew/bin/gh /usr/local/bin/gh; do [[ -x "$cand" ]] && { GH="$cand"; break; }; done

# --- this release ---------------------------------------------------------------------------------------------------
URL="https://github.com/jlcatonjr/researchteam.git"
GH_REPO="github.com/jlcatonjr/researchteam"
TAG="v1.0.2"; VERSION="1.0.2"; LINE="release/1.0"
AT_TAG="v1.0.0"; AT_PEELED="cc5b8c9ec4efdcb479939e0c1246a0ac11913259"   # agentteams v1.0.0, verified 2026-10-19
SIGNERS="$HOME/.config/agentteams/allowed_signers"
RELEASE_FPS=("SHA256:IPdnLwlFdHNhr7QGKVWU40BOKyYzv2u8qxP/qxnzTNM")   # pinned release key (agentteams SECURITY.md)
COMMIT="${1:?usage: $0 <40-hex release/1.0 head> <ssh-signing-key-path>}"
KEY="${2:?usage: $0 <40-hex release/1.0 head> <ssh-signing-key-path>}"

die() { echo "error: $*" >&2; exit 1; }
[[ "$COMMIT" =~ ^[0-9a-f]{40}$ ]] || die "the commit must be a full 40-hex SHA (the reviewed release/1.0 head)"
[[ -f "$KEY" ]] || die "signing key not found: $KEY"
[[ -f "$SIGNERS" ]] || die "no $SIGNERS"
TAGGER_NAME="${TAGGER_NAME:-jlcatonjr}"
TAGGER_EMAIL="${TAGGER_EMAIL:?set TAGGER_EMAIL to the tagger e-mail (global git config is not read)}"
[[ -n "$GH" ]] || die "gh not found at /opt/homebrew/bin/gh or /usr/local/bin/gh"
for bin in "$GIT" "$SSH_KEYGEN"; do [[ -x "$bin" ]] || die "$bin not found"; done

TMP=$(/usr/bin/mktemp -d); trap 'rm -rf "$TMP"' EXIT
CRED=(-c credential.helper= -c "credential.https://github.com.helper=!'$GH' auth git-credential")
GITX=("$GIT" -c core.hooksPath=/dev/null -c core.fsmonitor=false -c gpg.ssh.program="$SSH_KEYGEN"
      -c user.name="$TAGGER_NAME" -c user.email="$TAGGER_EMAIL" "${CRED[@]}")
"${GITX[@]}" clone -q --no-checkout "$URL" "$TMP/repo"
cd "$TMP/repo"
[[ "$("$GIT" config --get remote.origin.url)" == "$URL" ]] || die "clone remote is not $URL"
"${GITX[@]}" fetch -q origin --tags

# The commit: exactly the reviewed head of origin/release/1.0 (final tags are cut on release/1.0 only).
[[ "$("$GIT" rev-parse "origin/$LINE")" == "$COMMIT" ]] || die "origin/$LINE is $("$GIT" rev-parse "origin/$LINE"), not the reviewed $COMMIT"
"${GITX[@]}" ls-remote --exit-code --tags origin "refs/tags/$TAG" >/dev/null 2>&1 && die "tag $TAG already exists on origin (tags are immutable)"
# The release content at the commit.
"$GIT" show "$COMMIT:CHANGELOG.md" | /usr/bin/grep -q "^## $VERSION (" || die "no '## $VERSION (' section in CHANGELOG.md at $COMMIT"
"$GIT" show "$COMMIT:toolchain.lock" | /usr/bin/grep -qx "agentteams=jlcatonjr/agentteams@$AT_PEELED" || die "the lock at $COMMIT does not pin agentteams $AT_PEELED"
"$GIT" show "$COMMIT:toolchain.lock" | /usr/bin/grep -qx "agentteams.tag=$AT_TAG" || die "the lock at $COMMIT is not release-locked at agentteams $AT_TAG"
[[ "$("$GIT" show "$COMMIT:pyproject.toml" | /usr/bin/grep -c "@$AT_PEELED")" == 2 ]] || die "both extras at $COMMIT must pin $AT_PEELED"
# A patch: the previous release must be an ancestor of this commit, and this tag must not exist yet.
PREV="v1.0.1"; PREV_PEELED="b55e2307a95a2db92fe971d867a8453871183e8d"
[[ "$("$GIT" rev-parse "$PREV^{commit}")" == "$PREV_PEELED" ]] || die "$PREV is not at $PREV_PEELED in the clone"
"$GIT" merge-base --is-ancestor "$PREV_PEELED" "$COMMIT" || die "$PREV ($PREV_PEELED) is not an ancestor of $COMMIT"
! "$GIT" rev-parse -q --verify "refs/tags/$TAG" >/dev/null || die "$TAG already exists"

# The key: pinned here, pinned by the commit's own researchteam/_release.py, and listed in allowed_signers.
KEY_FP=$("$SSH_KEYGEN" -lf "$KEY" | /usr/bin/awk '{print $2}')
pinned=""; for fp in "${RELEASE_FPS[@]}"; do [[ "$KEY_FP" == "$fp" ]] && pinned=1; done
[[ -n "$pinned" ]] || die "key $KEY_FP is not a pinned release key (${RELEASE_FPS[*]})"
"$GIT" show "$COMMIT:researchteam/_release.py" | /usr/bin/grep -qF "\"$KEY_FP\"" || die "researchteam/_release.py at $COMMIT does not pin $KEY_FP"
LISTED=""
while IFS= read -r entry; do
  [[ -z "${entry// }" || "$entry" =~ ^[[:space:]]*# ]] && continue
  key_part=$(printf '%s\n' "$entry" | /usr/bin/grep -o -E '(ssh-(rsa|ed25519)|ecdsa-sha2-[a-z0-9]+|sk-[a-z0-9@.-]+) [A-Za-z0-9+/=]+' | /usr/bin/head -1 || true)
  [[ -n "$key_part" ]] || continue
  printf '%s\n' "$key_part" > "$TMP/k.pub"
  [[ "$("$SSH_KEYGEN" -lf "$TMP/k.pub" | /usr/bin/awk '{print $2}')" == "$KEY_FP" ]] && { LISTED=1; break; }
done < "$SIGNERS"
[[ -n "$LISTED" ]] || die "key $KEY_FP is not in $SIGNERS (comment lines are ignored)"

echo "release:      $TAG  (version $VERSION from the tag, commit ${COMMIT:0:12}, line $LINE)"
echo "pins:         agentteams $AT_TAG ($AT_PEELED)"
echo "release key:  $KEY_FP (pinned; _release.py and allowed_signers agree)"
echo "tagger:       $TAGGER_NAME <$TAGGER_EMAIL>"
"$GIT" --no-pager log -1 --format='commit:       %h %s' "$COMMIT"

"${GITX[@]}" -c gpg.format=ssh -c user.signingkey="$KEY" tag -s "$TAG" "$COMMIT" \
  -m "researchteam $VERSION (release/1.0)" -m "Pins agentteams $AT_TAG ($AT_PEELED). See CHANGELOG.md and docs/release-policy.md."
echo "signed $TAG (local clone only)"
STATUS=$("${GITX[@]}" -c gpg.ssh.allowedSignersFile="$SIGNERS" tag -v "$TAG" 2>&1 >/dev/null) \
  || { echo "$STATUS" >&2; die "verification of $TAG failed; it was NOT pushed (the clone is discarded)"; }
good=""
while IFS= read -r line; do [[ "$line" == 'Good "git" signature for '*" key $KEY_FP" ]] && good=1; done <<<"$STATUS"
[[ -n "$good" ]] || { echo "$STATUS" >&2; die "$TAG did not verify with $KEY_FP; NOT pushed"; }
[[ "$("$GIT" cat-file -t "refs/tags/$TAG")" == tag ]] || die "$TAG is not annotated; NOT pushed"
[[ "$("$GIT" rev-parse "$TAG^{commit}")" == "$COMMIT" ]] || die "$TAG does not point at $COMMIT; NOT pushed"
# setuptools-scm takes the version from the tag: with this tag, describe must give exactly v1.0.2 at the commit.
[[ "$("$GIT" describe --tags --exact-match --match 'v[0-9]*' "$COMMIT")" == "$TAG" ]] || die "git describe at $COMMIT is not $TAG; the built version would not be $VERSION; NOT pushed"
OBJ=$("$GIT" rev-parse "refs/tags/$TAG")
echo "verified $TAG: Good signature, $KEY_FP; builds $VERSION"

# Release notes: the CHANGELOG section for this version, plus a link to the file.
/usr/bin/awk -v h="## $VERSION (" 'index($0,h)==1{s=1; next} s && /^## /{exit} s' <("$GIT" show "$COMMIT:CHANGELOG.md") > "$TMP/notes.md"
[[ -s "$TMP/notes.md" ]] || die "empty CHANGELOG section for $VERSION (not pushed)"
printf '\nFull changes: [CHANGELOG.md](https://github.com/jlcatonjr/researchteam/blob/%s/CHANGELOG.md)\n' "$TAG" >> "$TMP/notes.md"

read -r -p "Push $TAG to origin and publish the GitHub release (latest, not a pre-release)? [y/N] " ok
[[ "$ok" == "y" ]] || { echo "not pushed; the temporary clone and its tag are discarded"; exit 0; }
"${GITX[@]}" push origin "refs/tags/$TAG"
[[ "$("${GITX[@]}" ls-remote origin "refs/tags/$TAG" | /usr/bin/cut -f1)" == "$OBJ" ]] || die "the remote tag object differs from $OBJ"
"$GH" release create "$TAG" -R "$GH_REPO" --verify-tag --latest --title "researchteam $VERSION" --notes-file "$TMP/notes.md"
echo "done: $TAG published"
echo "  tag object : $OBJ"
echo "  peeled     : $COMMIT"
echo "Tell the researchteam session: it merges release/1.0 forward into main and announces."
else
  printf 'STOP: run as /bin/bash -p %s (privileged mode); nothing was done.\n' "$0" >&2
fi
