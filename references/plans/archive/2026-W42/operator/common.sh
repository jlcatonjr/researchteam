# Shared settings for the researchteam v1.0.0 Phase R operator scripts. Sourced, not run.
set -euo pipefail

REPO="jlcatonjr/researchteam"
GH_ROOT="~/githubrepositories"
MAIN="$GH_ROOT/researchteam"                       # the main checkout (mathAgents' editable install)
AGENTTEAMS_CHECKOUT="$GH_ROOT/agentteams"
OPDIR="$MAIN/tmp/by-week/2026-W42/operator"
STATE="$OPDIR/state.env"                           # PR numbers etc. written by the scripts

# agentteams v1.0.0-rc.14 (shared policy §6 2b: researchteam rc.3), verified 2026-10-17.
AT_TAG="v1.0.0-rc.14"
AT_TAG_OBJ="3a3e423eda6e00a29b216e3047909167284daaba"   # verified 2026-10-17
AT_PEELED="c22aca0e507885d1e062a736af7fda80003d3151"    # verified: merge of rc.13 + 9cf878f
need_rc11() { [ -n "$AT_TAG_OBJ" ] && [ -n "$AT_PEELED" ] || die "on hold: waiting for agentteams $AT_TAG (the researchteam session updates common.sh, #49 and #52 when it is signed)"; }
RELEASE_FP="SHA256:IPdnLwlFdHNhr7QGKVWU40BOKyYzv2u8qxP/qxnzTNM"     # agentteams SECURITY.md "Release signers"
RELEASE_PUB="<release-key-file>"
ALLOWED_SIGNERS="$HOME/.config/agentteams/allowed_signers"

SIGNER_HOME="$HOME/.local/share/agentteams-signer"   # outside every agent write root
# Prefer the root-owned signer (01b): agentteams' signing gate refuses any install under $HOME.
SIGNER="<signer>"
[ -x "$SIGNER" ] || SIGNER="$SIGNER_HOME/bin/agentteams"
KEY_ID="op-2026"
KEYFILE="<decision-key-file>"
S10_SHA="9aa5869e8e569c9ac3a58727137418f6cf3e4e2ecef0387651b7c49adea8154b"

PIN_BRANCH="main"   # the specs and constraints are on main since #49/#65 merged
CODEX_BRANCH="fix/codex-orchestrator-only-210"
RC1_BUMP_COMMIT="ba693fe"   # CHANGELOG + docs/release-policy.md (the version comes from the tag, #57)
RC1_BRANCH="release-prep/1.0.0rc1"

say()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
die()  { printf '\033[31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }
confirm() { local a; read -r -p "$1 [y/N] " a; [ "$a" = "y" ] || [ "$a" = "Y" ] || die "stopped by operator"; }
refuse_agent() {
  [ -z "${CLAUDECODE:-}${CODEX_SANDBOX:-}" ] || die "run this in your own terminal, not inside an agent session"
  [ -t 0 ] || die "run this interactively (a terminal is required)"
}
state_set() { touch "$STATE"; grep -v "^$1=" "$STATE" > "$STATE.tmp" || true; echo "$1=$2" >> "$STATE.tmp"; mv "$STATE.tmp" "$STATE"; }
state_get() { [ -f "$STATE" ] && sed -n "s/^$1=//p" "$STATE" | tail -1; }

# Neutralised git: no hooks, no fsmonitor, no user or system config (url.insteadOf etc.).
ngit() { GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 git -c core.hooksPath=/dev/null -c core.fsmonitor=false "$@"; }

# verify_tag DIR TAG: annotated, signed by the release key (fixed-string match on git's stderr only).
verify_tag() {
  local dir="$1" tag="$2" err
  [ -f "$ALLOWED_SIGNERS" ] || die "missing $ALLOWED_SIGNERS"
  [ "$(ngit -C "$dir" cat-file -t "refs/tags/$tag")" = tag ] || die "$tag is not an annotated tag"
  err="$(ngit -C "$dir" -c gpg.format=ssh -c gpg.ssh.program=/usr/bin/ssh-keygen \
        -c gpg.ssh.allowedSignersFile="$ALLOWED_SIGNERS" tag -v "$tag" 2>&1 >/dev/null)" \
    || die "$tag: signature does not verify: $err"
  printf '%s\n' "$err" | grep -qF "Good \"git\" signature" || die "$tag: no good signature"
  printf '%s\n' "$err" | grep -qF "with RSA key $RELEASE_FP" || die "$tag: not signed by the release key $RELEASE_FP"
}
