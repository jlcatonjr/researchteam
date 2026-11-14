#!/usr/bin/env bash
# 01b — Root-owned trusted signer in <signer> (agentteams SECURITY.md, "Signing from a trusted
# install"). Needed because agentteams' signing gate counts all of $HOME as agent-writable (your user-level
# ~/.claude/settings.json makes $HOME look like a project root), and the 01 install lives under $HOME.
# Root ownership means no agent running as you can modify the signer's package or venv.
# Residual: the interpreter's stdlib comes from Homebrew's python3.13 under /opt/homebrew, which you own.
# Asks for your sudo password. Re-runnable: an existing verified install is reused.
source "$(dirname "$0")/common.sh"
refuse_agent
need_rc11
ROOT_SIGNER_HOME="<signer>"
SRC="$ROOT_SIGNER_HOME/src-$AT_TAG"
PY="/opt/homebrew/bin/python3.13"
[ -x "$PY" ] || die "need $PY (brew install python@3.13)"
sg() { sudo env GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 git -c core.hooksPath=/dev/null -c core.fsmonitor=false -c safe.directory="$SRC" "$@"; }

say "Creating $ROOT_SIGNER_HOME (root-owned)"
sudo mkdir -p "$ROOT_SIGNER_HOME" && sudo chown root:wheel "$ROOT_SIGNER_HOME" && sudo chmod 755 "$ROOT_SIGNER_HOME"
if [ ! -d "$SRC/.git" ]; then
  sg clone --quiet --no-checkout --no-tags https://github.com/jlcatonjr/agentteams.git "$SRC"
fi
sg -C "$SRC" fetch --quiet --no-tags origin "refs/tags/$AT_TAG:refs/tags/$AT_TAG"

say "Verifying $AT_TAG in the root-owned clone"
vgit() { ngit -c safe.directory="$SRC" "$@"; }
[ "$(vgit -C "$SRC" cat-file -t "refs/tags/$AT_TAG")" = tag ] || die "$AT_TAG is not an annotated tag"
err="$(vgit -C "$SRC" -c gpg.format=ssh -c gpg.ssh.program=/usr/bin/ssh-keygen \
      -c gpg.ssh.allowedSignersFile="$ALLOWED_SIGNERS" tag -v "$AT_TAG" 2>&1 >/dev/null)" || die "signature does not verify: $err"
printf '%s\n' "$err" | grep -qF "with RSA key $RELEASE_FP" || die "not signed by the release key"
[ "$(vgit -C "$SRC" rev-parse "refs/tags/$AT_TAG")" = "$AT_TAG_OBJ" ] || die "tag object differs from $AT_TAG_OBJ"
[ "$(vgit -C "$SRC" rev-parse "refs/tags/$AT_TAG^{commit}")" = "$AT_PEELED" ] || die "peeled commit differs from $AT_PEELED"
[ "$(ngit ls-remote https://github.com/jlcatonjr/agentteams.git "refs/tags/$AT_TAG" | cut -f1)" = "$AT_TAG_OBJ" ] || die "remote advertises a different tag object"
sg -C "$SRC" checkout --quiet --detach "$AT_PEELED"
echo "verified: $AT_TAG = $AT_TAG_OBJ -> $AT_PEELED, signed by $RELEASE_FP"

say "Installing into $ROOT_SIGNER_HOME/venv (root-owned, interpreter copied)"
git -C "$MAIN" fetch --quiet origin
git -C "$MAIN" show "origin/$PIN_BRANCH:docs/release/constraints-2026-10-16.txt" | sudo tee "$ROOT_SIGNER_HOME/constraints.txt" >/dev/null
cd /tmp
[ -x "$ROOT_SIGNER_HOME/venv/bin/python" ] || sudo "$PY" -m venv --copies "$ROOT_SIGNER_HOME/venv"
sudo env PIP_CONFIG_FILE=/dev/null "$ROOT_SIGNER_HOME/venv/bin/python" -m pip install --quiet --no-cache-dir \
  --constraint "$ROOT_SIGNER_HOME/constraints.txt" "$SRC[signing]"
sudo chown -R root:wheel "$ROOT_SIGNER_HOME" && sudo chmod -R go-w "$ROOT_SIGNER_HOME"
"$ROOT_SIGNER_HOME/venv/bin/agentteams" --version
echo "Root-owned signer ready: $ROOT_SIGNER_HOME/venv/bin/agentteams"
echo "Next: bash $(dirname "$0")/02-decision-signing.sh   (it now uses this signer)"
