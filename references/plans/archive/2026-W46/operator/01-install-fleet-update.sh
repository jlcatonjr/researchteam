#!/usr/bin/env bash
# 01 — Install the reviewed fleet-update.sh (agentteams-07 APPROVED 2026-11-09) and prepare its pinned venv.
# OPERATOR ONLY, plain Terminal:
#   bash ~/githubrepositories/researchteam/tmp/by-week/2026-W46/operator/01-install-fleet-update.sh
# It:
#   1. backs up ~/.local/bin/fleet-update.sh to fleet-update.sh.bak-20261109;
#   2. installs the reviewed revision;
#   3. runs --prepare (verifies agentteams on the v1.1 line, prints the skip plan, builds
#      ~/.local/share/agentteams-fleet/venv; no fleet run).
# The crontab line is NOT changed. It keeps calling ~/.local/bin/fleet-update.sh, Mondays 09:30.
# If you paused the cron, re-enable it yourself after reviewing the output.
set -euo pipefail
[ -z "${CLAUDECODE:-}${CLAUDE_CODE_ENTRYPOINT:-}" ] || { echo "run this in your own terminal, not an agent session" >&2; exit 1; }
SRC="~/githubrepositories/researchteam/tmp/by-week/2026-W46/handoffs/fleet-update.proposed.sh"
DST="$HOME/.local/bin/fleet-update.sh"
BAK="$DST.bak-20261109"
REVIEWED_SHA256="13710863add92ed7e794fcc1fba780822dab278fb5f8b239819c94572ef99222"

[ -f "$SRC" ] || { echo "missing $SRC" >&2; exit 1; }
got="$(shasum -a 256 "$SRC" | cut -d' ' -f1)"
[ "$got" = "$REVIEWED_SHA256" ] || { echo "$SRC changed since review (sha256 $got, reviewed $REVIEWED_SHA256); stop" >&2; exit 1; }
bash -n "$SRC"

echo "== 1. back up"
if [ -f "$BAK" ]; then echo "  $BAK exists; keeping it"; else cp -p "$DST" "$BAK"; echo "  $DST -> $BAK"; fi

echo "== 2. install"
read -r -p "Install the reviewed fleet-update.sh over $DST? [y/N] " a; [ "$a" = y ] || { echo "stopped"; exit 1; }
install -m 0755 "$SRC" "$DST"
echo "  installed (sha256 $got)"

echo "== 3. prepare (verify release, skip plan, build venv; no fleet run)"
"$DST" --prepare
echo
echo "Done. Check the skip plan above. Next, optionally preview the fleet with no writes:"
echo "  $DST --dry-run"
echo "To roll back:  cp -p \"$BAK\" \"$DST\""
echo "crontab is unchanged:"; crontab -l | grep -n fleet-update || true
