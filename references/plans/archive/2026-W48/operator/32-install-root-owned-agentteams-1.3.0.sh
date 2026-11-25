#!/usr/bin/env bash
# 32 — A second root-owned agentteams install, built from the signed tag v1.3.0, beside the existing one (built
# from an earlier tag), which is left untouched. Needed because operator script 31 calls agentteams' registry and
# binding functions as 1.3.0 defines them, and toolchain.lock pins 1.3.0; the existing root-owned install is older.
# Modelled on 2026-W42/01b-install-root-owned-signer.sh, with the defects @security found in that model closed
# (2026-11-25): nothing run as root starts in a world-writable folder or with your environment; an existing folder
# is trusted only if everything in it is already root-owned and not writable by others; the interpreter is the
# root-owned framework build, not Homebrew's (whose standard library you can write).
# Root ownership means no agent running as you can modify the package, its venv or the interpreter under it.
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
PY_HOME="/Library/Frameworks/Python.framework/Versions/3.13"   # the python.org framework build, root-owned
PY="$PY_HOME/bin/python3.13"
# The vetted versions for the signing chain: docs/release/constraints-2026-11-13.txt, read from a fixed commit of
# this repository and checked against its hash, never from the working tree.
CONSTRAINTS_COMMIT="f97e9d39661702c0cb9011df71bd9873209063d1"
CONSTRAINTS_PATH="docs/release/constraints-2026-11-13.txt"
CONSTRAINTS_SHA="3a5d948a7af99b9b7280b074669b1742a285612b1a4a21009fc1f45415337c55"
case "$ROOT_HOME" in /*) ;; *) die "ROOT_HOME must be an absolute path (the tracked copy holds a placeholder and does not run)" ;; esac
case "$ROOT_HOME/" in "$HOME"/*) die "ROOT_HOME must be outside your home folder" ;; esac
case "$ROOT_HOME" in *..*|*//*|*[[:space:]]*) die "ROOT_HOME must be a plain path without spaces" ;; esac
# Everything run as root gets an empty environment and root's own home: no variable, user site-packages or pip
# configuration of yours reaches it. Nothing run as root starts in /tmp or in a folder you can write.
asroot() { sudo /usr/bin/env -i PATH=/usr/bin:/bin HOME=/var/root GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 PIP_CONFIG_FILE=/dev/null "$@"; }
sg() { asroot /usr/bin/git -c core.hooksPath=/dev/null -c core.fsmonitor=false -c safe.directory="$SRC" "$@"; }
vgit() { ngit -c safe.directory="$SRC" "$@"; }
owner() { /usr/bin/stat -f %Su "$1"; }
# loose DIR: the first thing under DIR that is not owned by root (links included), or that is writable by group or
# others (a link's own mode is not meaningful, so only its owner is tested). Run as root, so nothing is skipped as
# unreadable. It is always called inside $(...), where an exit would end only that subshell, so a failed find is
# reported as output: the caller sees a non-empty answer and stops.
loose() {
  local out
  out="$(asroot /usr/bin/find "$1" \( ! -user root -o \( ! -type l -perm +022 \) \) -print)" || { printf 'cannot inspect %s\n' "$1"; return 1; }
  printf '%s\n' "$out" | /usr/bin/head -1
}
# rooted DIR: DIR and every folder above it is a real folder owned by root and not writable by group or others, so
# no part of the path can be swapped by a process running as you.
rooted() {
  local d="$1"
  while :; do
    [ -d "$d" ] && [ ! -L "$d" ] || die "$d must be an existing folder, not a link"
    [ "$(owner "$d")" = root ] || die "$d is not root-owned"
    [ -z "$(/usr/bin/find "$d" -maxdepth 0 -perm +022 -print)" ] || die "$d is writable by group or others"
    [ "$d" = / ] && break
    d="$(/usr/bin/dirname "$d")"
  done
}
# links_inside DIR ALLOWED...: every link under DIR resolves inside one of the ALLOWED folders.
links_inside() {
  asroot "$PY" -I -c 'import os, sys
root, allowed = sys.argv[1], [os.path.realpath(a) + os.sep for a in sys.argv[2:]]
bad = []
for d, dirs, files in os.walk(root, followlinks=False):
    for n in dirs + files:
        p = os.path.join(d, n)
        if os.path.islink(p) and not any((os.path.realpath(p) + os.sep).startswith(a) for a in allowed):
            bad.append(p)
print("\n".join(bad[:5])); sys.exit(1 if bad else 0)' "$@" || die "a link under $1 points outside the allowed folders; nothing was installed"
}
cd /
echo "The checks below run as root and ask for your sudo password."
[ -x "$PY" ] && [ ! -L "$PY_HOME" ] || die "need the python.org Python 3.13 at $PY"
rooted "$PY_HOME"
[ -z "$(loose "$PY_HOME")" ] || die "something under $PY_HOME is not root-owned or is writable by others: $(loose "$PY_HOME")"
links_inside "$PY_HOME" /Library/Frameworks/Python.framework
rooted "$(/usr/bin/dirname "$ROOT_HOME")"
[ ! -L "$ROOT_HOME" ] || die "$ROOT_HOME is a link"

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
ngit -C "$MAIN" cat-file -e "$CONSTRAINTS_COMMIT:$CONSTRAINTS_PATH" 2>/dev/null || ngit -C "$MAIN" fetch --quiet --no-tags "https://github.com/$REPO" "$CONSTRAINTS_COMMIT" || die "cannot find commit $CONSTRAINTS_COMMIT"
ngit -C "$MAIN" show "$CONSTRAINTS_COMMIT:$CONSTRAINTS_PATH" > "$TMP/constraints.txt" || die "cannot read $CONSTRAINTS_PATH at $CONSTRAINTS_COMMIT"
[ "$(/usr/bin/shasum -a 256 "$TMP/constraints.txt" | cut -d' ' -f1)" = "$CONSTRAINTS_SHA" ] || die "the constraints file is not the reviewed one"

say "A root-owned agentteams $AT_TAG install at $ROOT_HOME"
confirm "Create or reuse $ROOT_HOME (root-owned; asks for your sudo password)?"
asroot /bin/mkdir -p "$ROOT_HOME" && asroot /usr/sbin/chown root:wheel "$ROOT_HOME" && asroot /bin/chmod 755 "$ROOT_HOME"
rooted "$ROOT_HOME"
# An existing folder is reused only if nothing in it could have been planted: a clone's own .git/config, or a
# venv's interpreter, would otherwise be run as root below. Links count: each must be root's and stay inside.
[ -z "$(loose "$ROOT_HOME")" ] || die "$ROOT_HOME already holds something not root-owned or writable by others ($(loose "$ROOT_HOME")); nothing was installed; tell the researchteam session"
links_inside "$ROOT_HOME" "$ROOT_HOME" /Library/Frameworks/Python.framework
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
asroot /bin/cp "$TMP/constraints.txt" "$ROOT_HOME/constraints.txt"
[ "$(/usr/bin/shasum -a 256 "$ROOT_HOME/constraints.txt" | cut -d' ' -f1)" = "$CONSTRAINTS_SHA" ] || die "the copied constraints file differs"
cd /
[ -x "$ROOT_HOME/venv/bin/python" ] || asroot "$PY" -I -m venv --copies "$ROOT_HOME/venv"
# The package's build backend runs as root here, on the source verified above. The build tool is the one
# agentteams' pyproject.toml pins at this tag (setuptools==84.2.1), installed first by hash, and the build then
# runs without pip's isolated build environment, so nothing unpinned is downloaded and run as root. Every dependency
# must come as a wheel (--only-binary), so no other package's build code runs either; the local source still builds
# (rehearsed as an ordinary user in a scratch folder on 2026-11-25: agentteams 1.3.0, wheels only).
# S-10 for setuptools 84.2.1: released 2026-10-20 (past the 14-day cooldown); no advisory listed by PyPI on
# 2026-11-25; the wheel's sha256 below is PyPI's for setuptools-84.2.1-py3-none-any.whl.
grep -qF 'requires = ["setuptools==84.2.1"]' "$SRC/pyproject.toml" || die "agentteams at $AT_TAG does not pin setuptools==84.2.1 as its only build requirement; stop"
# Written by root straight into the root-owned folder and checked against a fixed hash: no file you can write is
# compared with or copied from.
BUILD_REQ_SHA="0d5ab27e0fa2cc72eeb7a0b3fa12dba6f34bbc8df2c7dac705c08aafb18c20d7"
printf 'setuptools==84.2.1 --hash=sha256:ca140b45d5325a9478f880e351484f62fef15f336462e449ca0c03c873d589c2\n' | asroot /usr/bin/tee "$ROOT_HOME/build-requirements.txt" >/dev/null
[ "$(/usr/bin/shasum -a 256 "$ROOT_HOME/build-requirements.txt" | cut -d' ' -f1)" = "$BUILD_REQ_SHA" ] || die "the build requirements file is not the reviewed one"
asroot "$ROOT_HOME/venv/bin/python" -I -m pip --isolated --disable-pip-version-check install --quiet --no-cache-dir \
  --require-hashes --only-binary :all: -r "$ROOT_HOME/build-requirements.txt"
asroot "$ROOT_HOME/venv/bin/python" -I -m pip --isolated --disable-pip-version-check install --quiet --no-cache-dir \
  --no-build-isolation --only-binary :all: --constraint "$ROOT_HOME/constraints.txt" "$SRC[signing]"
asroot /usr/sbin/chown -R root:wheel "$ROOT_HOME" && asroot /bin/chmod -R go-w "$ROOT_HOME"

say "Checks"
[ "$(owner "$ROOT_HOME/venv/bin/agentteams")" = root ] || die "the install is not root-owned"
[ "$(owner "$ROOT_HOME/venv/bin/python")" = root ] || die "the interpreter is not root-owned"
[ -z "$(loose "$ROOT_HOME")" ] || die "something under $ROOT_HOME is not root-owned or is writable by group or others: $(loose "$ROOT_HOME")"
links_inside "$ROOT_HOME" "$ROOT_HOME" /Library/Frameworks/Python.framework
ver="$(cd / && "$ROOT_HOME/venv/bin/python" -I -c 'import agentteams, cryptography; print(agentteams.__version__)')" || die "agentteams or cryptography does not import from the new install"
[ "$ver" = "1.3.0" ] || die "the new install reports agentteams $ver, not 1.3.0"
loc="$(cd / && "$ROOT_HOME/venv/bin/python" -I -c 'import agentteams, os; print(os.path.realpath(agentteams.__file__))')"
case "$loc" in "$ROOT_HOME"/*) ;; *) die "agentteams imports from $loc, outside the new install" ;; esac
say "Done"
echo "  agentteams $ver, built from $AT_TAG ($AT_PEELED), root-owned."
echo "  The earlier root-owned install was not touched."
echo "Tell the researchteam session: it points script 31 at this install and gives you the next command."
