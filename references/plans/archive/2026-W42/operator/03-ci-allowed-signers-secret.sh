#!/usr/bin/env bash
# 03 — Store the release-key allowed_signers line as the repo secret AGENTTEAMS_ALLOWED_SIGNERS, so
# release-locked CI runs can verify tags (PR #52; runners have no ~/.config/agentteams/allowed_signers).
# Only the line whose key fingerprint is the release key is stored.
# Usage: 03-ci-allowed-signers-secret.sh [owner/repo ...]   (default: jlcatonjr/researchteam)
source "$(dirname "$0")/common.sh"
refuse_agent
[ "$#" -gt 0 ] || set -- "$REPO"
line=""
while IFS= read -r l; do
  case "$l" in ''|'#'*) continue ;; esac
  key="$(printf '%s\n' "$l" | grep -oE '(ssh|ecdsa|sk)-[A-Za-z0-9@.-]+ +[A-Za-z0-9+/=]+' | head -1)" || continue
  fp="$(printf '%s\n' "$key" | ssh-keygen -lf - 2>/dev/null | awk '{print $2}')"
  [ "$fp" = "$RELEASE_FP" ] && { line="$l"; break; }
done < "$ALLOWED_SIGNERS"
[ -n "$line" ] || die "no line for $RELEASE_FP in $ALLOWED_SIGNERS"
echo "line: ${line:0:60}… ($RELEASE_FP)"
for r in "$@"; do
  confirm "Set AGENTTEAMS_ALLOWED_SIGNERS on $r?"
  printf '%s\n' "$line" | gh secret set AGENTTEAMS_ALLOWED_SIGNERS -R "$r"
done
