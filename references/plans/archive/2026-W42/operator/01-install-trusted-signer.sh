#!/usr/bin/env bash
# 01 — Build the trusted agentteams install that signs decisions (agentteams SECURITY.md, "Signing from a
# trusted install"): clone the verified rc.10 tag outside every write root, then pipx-install it with the
# `signing` extra under S-10-vetted constraints (docs/release/constraints-2026-10-16.txt, PR #49).
source "$(dirname "$0")/common.sh"
refuse_agent
need_rc11
command -v pipx >/dev/null || die "pipx not found (brew install pipx)"
SRC="$SIGNER_HOME/src-$AT_TAG"
(umask 077; mkdir -p "$SIGNER_HOME")
if [ ! -d "$SRC/.git" ]; then
  say "Cloning agentteams (no checkout yet)"
  ngit clone --quiet --no-checkout --no-tags https://github.com/jlcatonjr/agentteams.git "$SRC"
fi
ngit -C "$SRC" fetch --quiet --no-tags origin "refs/tags/$AT_TAG:refs/tags/$AT_TAG"
say "Verifying $AT_TAG"
verify_tag "$SRC" "$AT_TAG"
[ "$(ngit -C "$SRC" rev-parse "refs/tags/$AT_TAG")" = "$AT_TAG_OBJ" ] || die "tag object differs from $AT_TAG_OBJ"
[ "$(ngit -C "$SRC" rev-parse "refs/tags/$AT_TAG^{commit}")" = "$AT_PEELED" ] || die "peeled commit differs from $AT_PEELED"
[ "$(ngit ls-remote https://github.com/jlcatonjr/agentteams.git "refs/tags/$AT_TAG" | cut -f1)" = "$AT_TAG_OBJ" ] \
  || die "remote advertises a different tag object"
ngit -C "$SRC" checkout --quiet --detach "$AT_PEELED"
echo "verified: $AT_TAG = $AT_TAG_OBJ -> $AT_PEELED, signed by $RELEASE_FP"
git -C "$MAIN" fetch --quiet origin
git -C "$MAIN" show "origin/$PIN_BRANCH:docs/release/constraints-2026-10-16.txt" > "$SIGNER_HOME/constraints.txt"
say "Installing (pipx, PIPX_HOME=$SIGNER_HOME/pipx)"
cd /tmp   # never install or run the signer from inside a project or the install
PIPX_HOME="$SIGNER_HOME/pipx" PIPX_BIN_DIR="$SIGNER_HOME/bin" \
  pipx install --force "$SRC[signing]" --pip-args="--constraint $SIGNER_HOME/constraints.txt"
"$SIGNER" --version
echo "Signer ready: $SIGNER"
