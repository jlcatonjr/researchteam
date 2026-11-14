# Shared settings for the 2026-W45 researchteam operator scripts (copied from 2026-W44/operator). Sourced, not run.
set -euo pipefail

REPO="jlcatonjr/researchteam"
AT_REPO_URL="https://github.com/jlcatonjr/agentteams"
GH_ROOT="~/githubrepositories"
MAIN="$GH_ROOT/researchteam"                          # the main checkout (used only for fetch)
SIGN_WT="$GH_ROOT/researchteam-rc14"                  # worktree holding docs/s10-cooldown-restored (PR #138)
SIGN_BR="docs/s10-cooldown-restored"
AT_TAG=""   # no agentteams tag is used by these scripts
AT_V100="cc5b8c9ec4efdcb479939e0c1246a0ac11913259"     # agentteams v1.0.0 peeled (vetted dependency baseline)
RELEASE_FP="SHA256:IPdnLwlFdHNhr7QGKVWU40BOKyYzv2u8qxP/qxnzTNM"   # agentteams SECURITY.md "Release signers"
RELEASE_PUB="<release-key-file>"
ALLOWED_SIGNERS="$HOME/.config/agentteams/allowed_signers"

say()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
die()  { printf '\033[31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }
confirm() { local a; read -r -p "$1 [y/N] " a; [ "$a" = "y" ] || [ "$a" = "Y" ] || die "stopped by operator"; }
refuse_agent() {
  [ -z "${CLAUDECODE:-}${CLAUDE_CODE_ENTRYPOINT:-}${CODEX_SANDBOX:-}" ] || die "run this in your own terminal, not inside an agent session"
  [ -t 0 ] || die "run this interactively (a terminal is required)"
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
