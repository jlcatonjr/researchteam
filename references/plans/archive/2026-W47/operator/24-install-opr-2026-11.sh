#!/usr/bin/env bash
# 24 — Key rotation: install the operator's new Ed25519 decision verify key opr-2026-11 BESIDE op-2026 in
# researchteam's two verify-key stores that hold op-2026 today (.github and .codex). A trust-root step, so the
# operator runs it. It removes nothing and overwrites nothing; it makes no commit and pushes nothing.
# It writes into the worktree named below, on the branch named below; the session then commits the two files
# and opens the pull request, which merges only on the operator's live answer.
#   preview (checks only, writes nothing):  bash <this file>
#   install, then re-check every copy:       bash <this file> --apply
# OPERATOR ONLY, plain Terminal, from any directory. Run the tracked copy in the worktree, unmodified
# (the session gives the command with this file's sha256):
#   bash ~/githubrepositories/researchteam-wt-survey-toolkit/references/plans/archive/2026-W47/operator/24-install-opr-2026-11.sh --apply
source "$(dirname "$0")/common.sh"
refuse_agent
export LC_ALL=C
WT="$HOME/githubrepositories/researchteam-wt-survey-toolkit"
BRANCH="governance/install-opr-2026-11"
SRC="$HOME/.config/agentteams/verify-keys/opr-2026-11.pub.pem"
PEM_SHA=d22faa83b674abe6b1e3207a4f13fc17c5ddd367e35e0c60c69163eddbd9dab7
OLD_SHA=08f69c5d0e899bd26b26deb6f9f3af9b1a65a9c5e0ee25733769cc1ea3e70e7b   # op-2026: must stay, unchanged
BODY='MCowBQYDK2VwAyEA5DzYcCM9enk3NuGNz7aNepuyjXm4jNQfzxruPW637oc='
STORES=".github/agents/references/authorized-verify-keys
.codex/agents/references/authorized-verify-keys"
NEW="opr-2026-11.pub.pem"
sha() { /usr/bin/shasum -a 256 "$1" | /usr/bin/cut -d' ' -f1; }

APPLY=0
case "${1:-}" in --apply) APPLY=1 ;; "") ;; *) die "unknown argument: $1" ;; esac
[ $# -le 1 ] || die "one argument at most"

# Source: a regular file (not a link), the expected bytes, the expected Ed25519 body, three lines.
[ -f "$SRC" ] && [ ! -L "$SRC" ] || die "$SRC is missing or is a link"
[ "$(sha "$SRC")" = "$PEM_SHA" ] || die "the source key's sha256 is not $PEM_SHA"
[ "$(/usr/bin/sed -n 1p "$SRC")" = "-----BEGIN PUBLIC KEY-----" ] || die "the source is not a public key file"
[ "$(/usr/bin/sed -n 2p "$SRC")" = "$BODY" ] || die "the source key's body differs"
[ "$(/usr/bin/wc -l < "$SRC" | /usr/bin/tr -d ' ')" = 3 ] || die "the source key is not 3 lines"
say "Source ok: $PEM_SHA"

# Target: the named worktree, on the named branch, with nothing else changed.
[ -d "$WT" ] && [ ! -L "$WT" ] || die "no worktree at $WT"
[ "$(ngit -C "$WT" rev-parse --show-toplevel)" = "$WT" ] || die "$WT is not the top of a git worktree"
[ "$(ngit -C "$WT" symbolic-ref --short HEAD)" = "$BRANCH" ] || die "$WT is not on $BRANCH"
dirty="$(ngit -C "$WT" status --porcelain --untracked-files=all -- .github .codex .claude .goose)"
for s in $STORES; do dirty="$(printf '%s\n' "$dirty" | grep -vxF "?? $s/$NEW" || true)"; done
[ -z "$dirty" ] || die "the agent directories in $WT have other changes; not touching them: $dirty"

for s in $STORES; do
  d="$WT/$s"
  [ -d "$d" ] && [ ! -L "$d" ] || die "$s is missing or is a link"
  [ -f "$d/op-2026.pub.pem" ] && [ ! -L "$d/op-2026.pub.pem" ] && [ "$(sha "$d/op-2026.pub.pem")" = "$OLD_SHA" ] \
    || die "$s/op-2026.pub.pem is not the expected op-2026 key"
  if [ -e "$d/$NEW" ] || [ -L "$d/$NEW" ]; then
    [ -f "$d/$NEW" ] && [ ! -L "$d/$NEW" ] && [ "$(sha "$d/$NEW")" = "$PEM_SHA" ] \
      || die "$s/$NEW already exists with other content; not touching it"
    echo "  already installed: $s"
  elif [ "$APPLY" = 1 ]; then
    # noclobber: the write fails if anything, a dangling link included, is at the target.
    (umask 022; set -C; /bin/cat "$SRC" > "$d/$NEW") || die "$s: could not create $NEW"
    echo "  installed: $s"
  else
    echo "  would install: $s"
  fi
done

if [ "$APPLY" != 1 ]; then say "PREVIEW OK. Nothing was written. Run again with --apply."; exit 0; fi

# Re-check every copy, and that op-2026 is still beside it, unchanged.
for s in $STORES; do
  d="$WT/$s"
  [ -f "$d/$NEW" ] && [ ! -L "$d/$NEW" ] && [ "$(sha "$d/$NEW")" = "$PEM_SHA" ] || die "$s: the installed copy does not match"
  [ "$(sha "$d/op-2026.pub.pem")" = "$OLD_SHA" ] || die "$s: op-2026 changed"
  echo "  $PEM_SHA  $s/$NEW"
done
say "INSTALLED opr-2026-11 in 2 stores; op-2026 kept. Nothing was committed or pushed."
echo "Tell the researchteam session the two lines above."
