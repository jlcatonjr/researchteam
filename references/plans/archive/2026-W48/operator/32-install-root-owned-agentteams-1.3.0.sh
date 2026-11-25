#!/usr/bin/env bash
# 32 — A second root-owned agentteams install, built from the signed tag v1.3.0, beside the existing one (built
# from an earlier tag), which is left untouched. Needed because operator script 31 calls agentteams' registry and
# binding functions as 1.3.0 defines them, and toolchain.lock pins 1.3.0; the existing root-owned install is older.
# Modelled on 2026-W42/01b-install-root-owned-signer.sh. Root ownership means no agent running as you can modify
# the package or its venv. Residual, as before: the interpreter's standard library comes from Homebrew's python3.13.
# It signs nothing, reads no key, and changes nothing in any repository. Asks for your sudo password.
# Re-runnable: an existing install at the same place is checked and reused.
# OPERATOR ONLY, plain Terminal, from any directory:
#   /bin/bash <checkout>/tmp/by-week/2026-W48/operator/32-install-root-owned-agentteams-1.3.0.sh
# (the runnable copy lives under the ignored tmp/; this tracked copy is the record and holds a placeholder)
source "$(dirname "$0")/common.sh"
refuse_agent
AT_TAG="v1.3.0"
AT_TAG_OBJ="1621402d6dbaec73edb342ae48e3ecc1819316d9"
AT_PEELED="536306d2502e3db338846677f2d37489531ac8e7"
ROOT_HOME="<signer-home-1.3.0>"     # a root-owned folder outside $HOME; not recorded in the tracked copy (PS-1)
SRC="$ROOT_HOME/src-$AT_TAG"
PY="/opt/homebrew/bin/python3.13"
# The vetted versions for the signing chain: docs/release/constraints-2026-11-13.txt, read from a fixed commit of
# this repository and checked against its hash, never from the working tree.
CONSTRAINTS_COMMIT="f97e9d39661702c0cb9011df71bd9873209063d1"
CONSTRAINTS_PATH="docs/release/constraints-2026-11-13.txt"
CONSTRAINTS_SHA="3a5d948a7af99b9b7280b074669b1742a285612b1a4a21009fc1f45415337c55"
[ -x "$PY" ] || die "need $PY (brew install python@3.13)"
case "$ROOT_HOME" in "$HOME"/*|"<"*) die "ROOT_HOME must be a real folder outside your home folder" ;; esac
sg() { sudo env GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 git -c core.hooksPath=/dev/null -c core.fsmonitor=false -c safe.directory="$SRC" "$@"; }
vgit() { ngit -c safe.directory="$SRC" "$@"; }

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
ngit -C "$MAIN" cat-file -e "$CONSTRAINTS_COMMIT:$CONSTRAINTS_PATH" 2>/dev/null || ngit -C "$MAIN" fetch --quiet --no-tags "https://github.com/$REPO" "$CONSTRAINTS_COMMIT" || die "cannot find commit $CONSTRAINTS_COMMIT"
ngit -C "$MAIN" show "$CONSTRAINTS_COMMIT:$CONSTRAINTS_PATH" > "$TMP/constraints.txt" || die "cannot read $CONSTRAINTS_PATH at $CONSTRAINTS_COMMIT"
[ "$(/usr/bin/shasum -a 256 "$TMP/constraints.txt" | cut -d' ' -f1)" = "$CONSTRAINTS_SHA" ] || die "the constraints file is not the reviewed one"

say "A root-owned agentteams $AT_TAG install at $ROOT_HOME"
confirm "Create or reuse $ROOT_HOME (root-owned; asks for your sudo password)?"
sudo mkdir -p "$ROOT_HOME" && sudo chown root:wheel "$ROOT_HOME" && sudo chmod 755 "$ROOT_HOME"
if [ ! -d "$SRC/.git" ]; then
  sg clone --quiet --no-checkout --no-tags "$AT_REPO_URL.git" "$SRC"
fi
sg -C "$SRC" fetch --quiet --no-tags origin "refs/tags/$AT_TAG:refs/tags/$AT_TAG"

say "Verifying $AT_TAG in the root-owned clone"
[ "$(vgit -C "$SRC" cat-file -t "refs/tags/$AT_TAG")" = tag ] || die "$AT_TAG is not an annotated tag"
[ -f "$ALLOWED_SIGNERS" ] || die "missing $ALLOWED_SIGNERS"
err="$(vgit -C "$SRC" -c gpg.format=ssh -c gpg.ssh.program=/usr/bin/ssh-keygen \
      -c gpg.ssh.allowedSignersFile="$ALLOWED_SIGNERS" tag -v "$AT_TAG" 2>&1 >/dev/null)" || die "signature does not verify: $err"
printf '%s\n' "$err" | grep -qF "Good \"git\" signature" || die "$AT_TAG: no good signature"
printf '%s\n' "$err" | grep -qF "with RSA key $RELEASE_FP" || die "not signed by the release key $RELEASE_FP"
[ "$(vgit -C "$SRC" rev-parse "refs/tags/$AT_TAG")" = "$AT_TAG_OBJ" ] || die "tag object differs from $AT_TAG_OBJ"
[ "$(vgit -C "$SRC" rev-parse "refs/tags/$AT_TAG^{commit}")" = "$AT_PEELED" ] || die "peeled commit differs from $AT_PEELED"
[ "$(ngit ls-remote "$AT_REPO_URL.git" "refs/tags/$AT_TAG" | cut -f1)" = "$AT_TAG_OBJ" ] || die "the remote advertises a different tag object"
sg -C "$SRC" checkout --quiet --detach "$AT_PEELED"
[ "$(vgit -C "$SRC" rev-parse HEAD)" = "$AT_PEELED" ] || die "the clone is not at $AT_PEELED"
[ -z "$(vgit -C "$SRC" status --porcelain)" ] || die "the root-owned clone has local changes"
echo "verified: $AT_TAG = $AT_TAG_OBJ -> $AT_PEELED, signed by $RELEASE_FP"

say "Installing into $ROOT_HOME/venv (root-owned, interpreter copied)"
sudo cp "$TMP/constraints.txt" "$ROOT_HOME/constraints.txt"
cd /tmp
[ -x "$ROOT_HOME/venv/bin/python" ] || sudo "$PY" -m venv --copies "$ROOT_HOME/venv"
sudo env PIP_CONFIG_FILE=/dev/null "$ROOT_HOME/venv/bin/python" -m pip install --quiet --no-cache-dir \
  --constraint "$ROOT_HOME/constraints.txt" "$SRC[signing]"
sudo chown -R root:wheel "$ROOT_HOME" && sudo chmod -R go-w "$ROOT_HOME"

say "Checks"
[ "$(/usr/bin/stat -f %Su "$ROOT_HOME/venv/bin/agentteams")" = root ] || die "the install is not root-owned"
[ "$(/usr/bin/stat -f %Su "$ROOT_HOME/venv/bin/python")" = root ] || die "the interpreter is not root-owned"
[ -z "$(/usr/bin/find "$ROOT_HOME" -perm +022 ! -type l -print -quit)" ] || die "something under $ROOT_HOME is writable by group or others"
ver="$(cd /tmp && "$ROOT_HOME/venv/bin/python" -I -c 'import agentteams, cryptography; print(agentteams.__version__)')" || die "agentteams or cryptography does not import from the new install"
[ "$ver" = "1.3.0" ] || die "the new install reports agentteams $ver, not 1.3.0"
loc="$(cd /tmp && "$ROOT_HOME/venv/bin/python" -I -c 'import agentteams, os; print(os.path.realpath(agentteams.__file__))')"
case "$loc" in "$ROOT_HOME"/*) ;; *) die "agentteams imports from $loc, outside the new install" ;; esac
say "Done"
echo "  agentteams $ver, built from $AT_TAG ($AT_PEELED), root-owned."
echo "  The earlier root-owned install was not touched."
echo "Tell the researchteam session: it points script 31 at this install and gives you the next command."
