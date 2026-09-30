#!/usr/bin/env bash
# .goose/confined-run.example.sh — EXAMPLE: run goose CONFINED on Linux. INERT / operator-run.
#
# goose has NO native OS sandbox on Linux; the boundary is the framework-neutral bwrap
# launcher sandbox/confine-run.sh. This wrapper adds the goose-specific settings a confined
# goose needs (agentteams never runs this or edits your live config — adapt and run it yourself):
#   * writable XDG state/data/cache dirs  (else goose panics creating its log on a ro root)
#   * GOOSE_DISABLE_KEYRING=1             (the SecretService keyring is unreachable in-sandbox;
#                                          without it goose sends no auth header)
#   * the provider key injected as an env INPUT via --env-allow (by NAME — never hardcoded;
#     the vault/keyring stays masked). Set the key env var (default OPENROUTER_API_KEY).
#     PS NOTE: --env-allow keeps the value off THIS wrapper's and confine-run.sh's argv, but
#     the launcher forwards it to bwrap via --setenv, so the cleartext IS visible in `ps`/
#     /proc/PID/cmdline of the bwrap process on a SHARED host. Run on a single-tenant box (or
#     a hidepid=2 /proc). This is a launcher-level limitation (bwrap has no env-from-fd).
#
# RUN AS THE WORKSPACE-OWNING USER, not root: bwrap --unshare-user as root loses DAC over
# your uid's files (a 0750 home dir becomes untraversable and the bind fails).
#
# EGRESS (honest): the bare default (deny) CONFINES writes but CANNOT reach the LLM (offline).
#   * secure + functional: GOOSE_CONFINE_EGRESS=proxy — a pinned sole-egress netns
#     (operator root, OOB; see the agentteams sandboxing guide). Egress reaches only the LLM.
#   * GOOSE_CONFINE_EGRESS=host opens egress to the whole host: a live key can then be
#     EXFILTRATED anywhere. NEVER run --egress host while a live provider key is present —
#     this script REFUSES that combination unless you set GOOSE_CONFINE_ACCEPT_OPEN_EGRESS=1
#     on a trusted, single-tenant box. Confinement bounds T6; it does not close it.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO_ROOT="$(cd "$HERE/.." && pwd)"
LAUNCHER="$REPO_ROOT/sandbox/confine-run.sh"
[ -x "$LAUNCHER" ] || { echo "neutral launcher missing at $LAUNCHER (is confinement emitted for this team?)" >&2; exit 1; }
[ "$(id -u)" -ne 0 ] || echo "WARNING: running as root — bwrap will lose DAC over your files; run as the workspace user." >&2
SCRATCH="${GOOSE_CONFINE_SCRATCH:-/tmp/goose-confined-$USER}"; mkdir -p "$SCRATCH/state" "$SCRATCH/data" "$SCRATCH/cache"
KEY_ENV="${GOOSE_KEY_ENV:-OPENROUTER_API_KEY}"   # provider key env var, injected by NAME (ps-safe)
: "${!KEY_ENV:?set $KEY_ENV in your environment (the credential is injected as an input, not read from the keyring)}"
export "$KEY_ENV"   # export by name so --env-allow forwards the VALUE via env, never on argv
EGRESS="${GOOSE_CONFINE_EGRESS:-deny}"
if [ "$EGRESS" = host ] && [ -z "${GOOSE_CONFINE_ACCEPT_OPEN_EGRESS:-}" ]; then
  echo "REFUSING --egress host with a live $KEY_ENV: open egress + a live key is a key-exfiltration channel." >&2
  echo "Use GOOSE_CONFINE_EGRESS=proxy (a pinned sole-egress netns; see the sandboxing guide)," >&2
  echo "or set GOOSE_CONFINE_ACCEPT_OPEN_EGRESS=1 to accept the risk on a trusted single-tenant box." >&2
  exit 2
fi
exec "$LAUNCHER" --scratch "$SCRATCH" --writable "$REPO_ROOT" --egress "$EGRESS" \
  --setenv XDG_STATE_HOME="$SCRATCH/state" --setenv XDG_DATA_HOME="$SCRATCH/data" --setenv XDG_CACHE_HOME="$SCRATCH/cache" \
  --setenv GOOSE_DISABLE_KEYRING=1 --env-allow "$KEY_ENV" \
  -- goose run "$@"
