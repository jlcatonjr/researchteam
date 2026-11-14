#!/usr/bin/env bash
# 02 — Switch the weekly fleet cron to report-only (operator ruling 2026-11-09).
# OPERATOR ONLY, plain Terminal:
#   bash ~/githubrepositories/researchteam/tmp/by-week/2026-W46/operator/02-fleet-cron-dry-run.sh
# Changes exactly one crontab line:
#   30 9 * * 1 ~/.local/bin/fleet-update.sh >> …/runner.log 2>&1
#   30 9 * * 1 ~/.local/bin/fleet-update.sh --dry-run >> …/runner.log 2>&1
# In --dry-run, agentteams' fleet passes --dry-run to every target, takes no snapshot, writes no diff and makes no
# commit (fleet.py: "Dry-run: report intent; no diff (nothing written)"). Each workspace is reported as WOULD-UPDATE.
# The previous crontab is saved first; restore it with: crontab ~/.local/logs/fleet/crontab.bak-20261109
set -euo pipefail
[ -z "${CLAUDECODE:-}${CLAUDE_CODE_ENTRYPOINT:-}" ] || { echo "run this in your own terminal, not an agent session" >&2; exit 1; }
BAK="$HOME/.local/logs/fleet/crontab.bak-20261109"
OLD='30 9 * * 1 ~/.local/bin/fleet-update.sh >> ~/.local/logs/fleet/runner.log 2>&1'
NEW='30 9 * * 1 ~/.local/bin/fleet-update.sh --dry-run >> ~/.local/logs/fleet/runner.log 2>&1'

cur="$(crontab -l)"
if printf '%s\n' "$cur" | grep -qxF -- "$NEW"; then echo "already report-only; nothing to do"; exit 0; fi
[ "$(printf '%s\n' "$cur" | grep -cxF -- "$OLD")" = 1 ] || { echo "the expected fleet line was not found exactly once; stop (no change)" >&2; printf '%s\n' "$cur" | grep -n fleet >&2 || true; exit 1; }
[ -f "$BAK" ] || printf '%s\n' "$cur" > "$BAK"
echo "saved current crontab to $BAK"
echo "- $OLD"
echo "+ $NEW"
read -r -p "Apply this crontab change? [y/N] " a; [ "$a" = y ] || { echo "stopped; no change"; exit 1; }
printf '%s\n' "$cur" | awk -v old="$OLD" -v new="$NEW" '$0 == old { print new; next } { print }' | crontab -
crontab -l | grep -n fleet-update
echo "Done. To preview now: ~/.local/bin/fleet-update.sh --dry-run"
