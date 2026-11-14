#!/usr/bin/env bash
# 00 — Back up, then discard, the stale 2026-10-12 agentteams rc8 re-render in the main checkout.
# Those 13 uncommitted files downgrade the committed rc9 state: the Q-CTX/H historical-context checks are
# removed, and the sandbox no longer protects .codex/confined-run.example.sh or AGENTS.override.md.
# HEAD does not move (mathAgents' editable install stays at 15b968b), and the researchteam/ package dir
# is not touched. Reversible: the backup holds the full patch and copies of every file.
source "$(dirname "$0")/common.sh"
refuse_agent
cd "$MAIN"
[ "$(git rev-parse HEAD)" = "15b968b55a50dae92cb2a540e35d7703cb281768" ] || die "main checkout HEAD moved; re-inspect first"
mapfile -t FILES < <(git diff --name-only)
[ "${#FILES[@]}" -gt 0 ] || { echo "nothing to discard"; exit 0; }
for f in "${FILES[@]}"; do
  case "$f" in researchteam/*) die "refusing: $f is in the package dir mathAgents imports" ;; esac
done
say "Files to discard (${#FILES[@]}):"; printf '  %s\n' "${FILES[@]}"
grep -q '"agentteams_version": "1.0.0rc8"' .github/agents/references/delivery-receipt.json \
  || die "delivery-receipt no longer says 1.0.0rc8; these are not the files I inspected"
BK="$HOME/researchteam-backups/rc8-regen-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BK"
git diff > "$BK/discarded.patch"
tar -czf "$BK/files.tgz" "${FILES[@]}"
echo "backup: $BK (restore with: git -C $MAIN apply $BK/discarded.patch)"
confirm "Discard these changes in $MAIN?"
git restore -- "${FILES[@]}"
git status --short
echo "Done. Tell the researchteam session so it can let mathAgents know (HEAD unchanged)."
