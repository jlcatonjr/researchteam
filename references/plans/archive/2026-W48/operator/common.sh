# Shared settings for the 2026-W48 researchteam operator scripts (copied from 2026-W47/operator). Sourced, not run.
set -euo pipefail
# Tools come from fixed places, never from an inherited PATH.
export PATH=/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/usr/local/bin

REPO="jlcatonjr/researchteam"
AT_REPO_URL="https://github.com/jlcatonjr/agentteams"
GH_ROOT="$HOME/githubrepositories"
MAIN="$GH_ROOT/researchteam"                          # the main checkout (used only for fetch and the tag)
RELEASE_FP="SHA256:IPdnLwlFdHNhr7QGKVWU40BOKyYzv2u8qxP/qxnzTNM"   # agentteams SECURITY.md "Release signers"
RELEASE_PUB="<release-key-file>"
ALLOWED_SIGNERS="$HOME/.config/agentteams/allowed_signers"

say()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
die()  { printf '\033[31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }
# Discard keys typed ahead during a slow step (signing, pushing), so a prompt reads only what follows it.
drain() { local junk; while read -r -s -t 1 -n 10000 junk 2>/dev/null; do :; done; }
confirm() { local a; drain; read -r -p "$1 [y/N] " a; [ "$a" = "y" ] || [ "$a" = "Y" ] || die "stopped by operator"; }
refuse_agent() {
  [ -z "${CLAUDECODE:-}${CLAUDE_CODE_ENTRYPOINT:-}${CLAUDE_CODE_SSE_PORT:-}${CODEX_SANDBOX:-}" ] || die "run this in your own terminal, not inside an agent session"
  [ "${TERM_PROGRAM:-}" != vscode ] || die "run this in a plain Terminal window, not an editor's terminal"
  [ -t 0 ] || die "run this interactively (a terminal is required)"
}
# run_log NAME: copy everything this run prints into a new file beside the script (an ignored path), so the record
# survives a failure after a push. One file per run; never overwritten.
run_log() {
  local dir; dir="$(cd "$(dirname "$0")" && pwd)/logs"
  mkdir -p "$dir"
  RUN_LOG="$dir/$1.$(date -u +%Y%m%dT%H%M%SZ).$$.log"
  [ ! -e "$RUN_LOG" ] || die "$RUN_LOG already exists"
  exec > >(tee -a "$RUN_LOG") 2>&1
  printf 'run log: %s\n' "$RUN_LOG"
}
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
