#!/bin/bash
# set-allowed-signers-secret.sh — set the AGENTTEAMS_ALLOWED_SIGNERS Actions secret in every derived repo that lacks it.
# Run from a plain Terminal (bash, not zsh):
#   /bin/bash ~/githubrepositories/researchteam/tmp/by-week/2026-W43/operator/set-allowed-signers-secret.sh
# You enter the value ONCE: paste the allowed_signers line(s), then press Enter on an empty line. Or press Enter right
# away to use ~/.config/agentteams/allowed_signers (the file that verified researchteam v1.0.1).
# Every key is checked with ssh-keygen and the release fingerprint must be present. Each repo's status is shown and you
# confirm once (y/N) before anything is written. Repos that already have the secret are skipped unless you pass --all.
set -euo pipefail
OWNER="jlcatonjr"
REPOS=(agenticExperimentation OrthodoxLLM SocialScienceHumanities biographies legalResearch baseAgent Batallion mathAgents)
RELEASE_FP="SHA256:IPdnLwlFdHNhr7QGKVWU40BOKyYzv2u8qxP/qxnzTNM"
DEFAULT_FILE="$HOME/.config/agentteams/allowed_signers"
FORCE_ALL=""; [[ "${1:-}" == "--all" ]] && FORCE_ALL=1
die() { echo "error: $*" >&2; exit 1; }
command -v gh >/dev/null || die "gh is not installed"
gh auth status >/dev/null 2>&1 || die "gh is not logged in (gh auth login)"

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
echo "Paste the allowed_signers line(s), then press Enter on an empty line."
echo "Or press Enter now to use $DEFAULT_FILE."
VALUE=""
while IFS= read -r line; do
  [[ -z "$line" ]] && break
  VALUE+="$line"$'\n'
done
if [[ -z "$VALUE" ]]; then
  [[ -s "$DEFAULT_FILE" ]] || die "no value entered and $DEFAULT_FILE is missing or empty"
  VALUE=$(cat "$DEFAULT_FILE")$'\n'
  echo "using $DEFAULT_FILE"
fi
printf '%s' "$VALUE" > "$TMP/allowed_signers"

# Check every non-comment line holds a valid public key, and that the release key is one of them.
found=""; n=0
while IFS= read -r entry; do
  [[ -z "${entry// }" || "$entry" =~ ^[[:space:]]*# ]] && continue
  key=$(printf '%s\n' "$entry" | grep -o -E '(ssh-(rsa|ed25519)|ecdsa-sha2-[a-z0-9]+|sk-[a-z0-9@.-]+) [A-Za-z0-9+/=]+' | head -1 || true)
  [[ -n "$key" ]] || die "this line has no public key: $entry"
  printf '%s\n' "$key" > "$TMP/k.pub"
  fp=$(ssh-keygen -lf "$TMP/k.pub" 2>/dev/null | awk '{print $2}') || die "ssh-keygen rejects the key on: $entry"
  [[ -n "$fp" ]] || die "ssh-keygen rejects the key on: $entry"
  echo "  key: $fp"
  [[ "$fp" == "$RELEASE_FP" ]] && found=1
  n=$((n+1))
done < "$TMP/allowed_signers"
(( n > 0 )) || die "no keys found"
[[ -n "$found" ]] || die "the release key $RELEASE_FP is not in the value; nothing was set"
grep -qi 'PRIVATE KEY' "$TMP/allowed_signers" && die "the value contains a PRIVATE KEY; nothing was set"

echo
TARGETS=()
for r in "${REPOS[@]}"; do
  if gh secret list -R "$OWNER/$r" 2>/dev/null | grep -q '^AGENTTEAMS_ALLOWED_SIGNERS\b'; then
    if [[ -n "$FORCE_ALL" ]]; then echo "  $r: has it (will overwrite, --all)"; TARGETS+=("$r")
    else echo "  $r: already set, skipping"; fi
  else
    echo "  $r: missing, will set"; TARGETS+=("$r")
  fi
done
(( ${#TARGETS[@]} > 0 )) || { echo "nothing to do"; exit 0; }

echo
read -r -p "Set AGENTTEAMS_ALLOWED_SIGNERS ($n key(s)) in ${#TARGETS[@]} repo(s): ${TARGETS[*]}? [y/N] " ok
[[ "$ok" == "y" ]] || { echo "stopped; nothing was set"; exit 0; }
for r in "${TARGETS[@]}"; do
  gh secret set AGENTTEAMS_ALLOWED_SIGNERS -R "$OWNER/$r" < "$TMP/allowed_signers"   # stdin: never on the command line
  gh secret list -R "$OWNER/$r" | grep -q '^AGENTTEAMS_ALLOWED_SIGNERS\b' && echo "  ok: $r" || echo "  FAILED: $r" >&2
done
echo "done"
