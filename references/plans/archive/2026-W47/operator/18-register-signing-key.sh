#!/usr/bin/env bash
# 18 — Register the release public key on the operator's GitHub account as a SIGNING key, so GitHub shows release
# tags as "Verified". Operator's choice, 2026-11-19 picker: "Prepare the script". The key is already on the account
# for authentication; GitHub keeps signing keys in a separate list, which is why tags report "unknown_key".
# OPERATOR ONLY, plain Terminal, from any directory:
#   bash <checkout>/tmp/by-week/2026-W47/operator/18-register-signing-key.sh
# It reads the PUBLIC key file only, never a private key. If the gh token lacks the admin:ssh_signing_key scope it
# asks GitHub for it (a browser confirmation), after asking you. It changes nothing in any repository and re-signs
# nothing: existing tags stay as they are.
source "$(dirname "$0")/common.sh"
refuse_agent
GH_LOGIN="jlcatonjr"
[ -f "$RELEASE_PUB" ] || die "missing $RELEASE_PUB"
fp="$(ssh-keygen -lf "$RELEASE_PUB" | awk '{print $2}')"
[ "$fp" = "$RELEASE_FP" ] || die "$RELEASE_PUB is $fp, not the release key $RELEASE_FP"
[ "$(gh api user -q .login)" = "$GH_LOGIN" ] || die "gh is not signed in as $GH_LOGIN"
is_registered() {
  local keys key
  keys="$(gh api "users/$GH_LOGIN/ssh_signing_keys" -q '.[].key')" || die "cannot list the signing keys of $GH_LOGIN"
  while IFS= read -r key; do
    if [ -n "$key" ] && [ "$(printf '%s\n' "$key" | ssh-keygen -lf - | awk '{print $2}')" = "$RELEASE_FP" ]; then return 0; fi
  done <<EOF_KEYS
$keys
EOF_KEYS
  return 1
}
if is_registered; then say "The release key $RELEASE_FP is already a signing key on $GH_LOGIN. Nothing to do."; exit 0; fi
say "Register $RELEASE_PUB ($RELEASE_FP) as a signing key on GitHub account $GH_LOGIN"
confirm "Add it as a signing key?"
if ! gh ssh-key add "$RELEASE_PUB" --type signing --title "release signing key"; then
  echo "  The gh token probably lacks the admin:ssh_signing_key scope."
  confirm "Ask GitHub to add that scope to the gh token (opens a browser confirmation)?"
  gh auth refresh -h github.com -s admin:ssh_signing_key
  gh ssh-key add "$RELEASE_PUB" --type signing --title "release signing key" || die "could not add the signing key"
fi
is_registered || die "the key was added but is not in the public signing-key list yet; run this script again in a minute"
say "Done. $RELEASE_FP is a signing key on $GH_LOGIN. Tags signed from now on can show as Verified."
echo "Tell the researchteam session."
