#!/usr/bin/env bash
# .codex/confined-run.example.sh - EXAMPLE: run Codex inside agentteams' launcher (Linux + macOS).
# INERT / operator-run: agentteams never runs this or edits your Codex config. Adapt and run it:
#   .codex/confined-run.example.sh                 # interactive Codex
#   .codex/confined-run.example.sh exec "..."      # any codex arguments pass through
#
# WHY CODEX'S OWN SANDBOX IS OFF: Codex's sandbox cannot nest inside sandbox/confine-run.sh (its
# sandbox setup fails inside bwrap/Seatbelt). So Codex runs with --sandbox danger-full-access
# INSIDE the launcher, and the launcher is the boundary: writes reach only the project's write roots
# and CODEX_HOME, the agentteams control plane, .agentteams and prompt roots are read-only, and
# credential dirs (including ~/.config/agentteams/keys) are masked. Run Codex this way or not at
# all: outside the launcher, danger-full-access confines nothing.
#
# PER-ROLE LIMITS (write_policy "orchestrator-only"): Codex ignores a custom agent's sandbox_mode,
# so this runner turns on the generated role gate instead: .codex/hooks.json runs
# .agentteams/bin/codex-role-gate.py before every tool call, and a spawned agent (any call Codex
# tags with agent_type) may use only the read-only agentteams_readfs tools. That is HARNESS-LEVEL,
# like Claude's tool grants: it holds only while Codex runs the hook, which this script arranges
# with --dangerously-bypass-hook-trust (the hook files are pinned and read-only in the launcher).
# Residual: Codex lets a call through when a hook TIMES OUT; the gate is kept fast for that reason.
# The launcher (OS level) keeps the ledger key and .agentteams out of reach for every role.
# agentteams cannot verify that Codex is actually launched through this script.
#
# CODEX_HOME: Codex must write its home (sessions, logs, auth), so it is writable for every agent
# command. Default: $HOME/.config/agentteams/codex-home/<project>-<hash>; override with
# AGENTTEAMS_CODEX_HOME. It must be strictly under ~/.config/agentteams/codex-home/ or outside
# ~/.config/agentteams entirely, and never $HOME, an ancestor of it, inside this project, or an
# ancestor of it. Authenticate it once, OUTSIDE the launcher:  CODEX_HOME=<that dir> codex login
# Before launch, config.toml, hooks.json, AGENTS.md and AGENTS.override.md (and the rules/ prompts/
# skills/ plugins/ dirs) are created empty if absent and then made read-only, so a confined agent
# cannot plant config, hooks, instructions or plugin code that Codex would honour on its next run,
# inside or outside the launcher.
# Its auth is readable by every agent command.
#
# EGRESS: host by default, because Codex must reach its API. Host egress lets a confined process
# reach any host, so whatever it can read (the Codex auth included) could leave the box. For a
# pinned loopback proxy instead, set CODEX_CONFINE_EGRESS=proxy and add --proxy ADDR:PORT to the
# exec line below (confine-run.sh --egress proxy; see the agentteams sandboxing guide).
#
# RUN AS THE WORKSPACE-OWNING USER, not root (on Linux, bwrap --unshare-user as root loses DAC
# over your files).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd -P)"; ROOT="$(cd "$HERE/.." && pwd -P)"; REPO_ROOT="$ROOT"
LAUNCHER="$ROOT/sandbox/confine-run.sh"
[ -x "$LAUNCHER" ] || { echo "neutral launcher missing at $LAUNCHER (is confinement emitted for this team?)" >&2; exit 1; }
[ "$(id -u)" -ne 0 ] || echo "WARNING: running as root; run as the workspace user." >&2
command -v codex >/dev/null 2>&1 || { echo "codex not found on PATH" >&2; exit 1; }
refuse(){ echo "REFUSING CODEX_HOME=$1: $2" >&2; exit 2; }
check_home(){   # path home cfg root -> refuse unless an allowed CODEX_HOME placement
  case "$1" in /*) ;; *) refuse "$1" "it must be an absolute path" ;; esac
  case "$1" in /|*//*) refuse "$1" "it must not be / or contain //" ;; esac
  case "/$1/" in */../*|*/./*) refuse "$1" "it must not contain . or .. segments" ;; esac
  case "$1/" in
    "$3/codex-home/"?*) ;;
    "$3"/*) refuse "$1" "inside ~/.config/agentteams it must be under codex-home/ (the keys and operator files stay out of reach)" ;;
  esac
  case "$2/" in "$1"/*) refuse "$1" "it is \$HOME or one of its parents" ;; esac
  case "$4/" in "$1"/*) refuse "$1" "it is this project or one of its parents" ;; esac
  case "$1/" in "$4"/*) refuse "$1" "it is inside this project; keep it outside the repo" ;; esac
}
HASH="$(printf %s "$ROOT" | { sha256sum 2>/dev/null || shasum -a 256; } | cut -c1-12)"
CODEX_HOME="${AGENTTEAMS_CODEX_HOME:-$HOME/.config/agentteams/codex-home/$(basename "$ROOT")-$HASH}"
check_home "${CODEX_HOME%/}" "$HOME" "$HOME/.config/agentteams" "$ROOT"   # BEFORE anything is created
mkdir -p "$CODEX_HOME"; CODEX_HOME="$(cd "$CODEX_HOME" && pwd -P)"
HOME_P="$(cd "$HOME" && pwd -P)"; CFG_P="$HOME_P/.config/agentteams"
[ -d "$CFG_P" ] && CFG_P="$(cd "$CFG_P" && pwd -P)"
check_home "$CODEX_HOME" "$HOME_P" "$CFG_P" "$ROOT"   # again with symlinks resolved
# Config Codex trusts on its next run: create empty if absent, then protect, so it cannot be planted.
for d in rules prompts skills plugins; do mkdir -p "$CODEX_HOME/$d"; done
[ -e "$CODEX_HOME/config.toml" ] || : > "$CODEX_HOME/config.toml"
for f in AGENTS.md AGENTS.override.md; do [ -e "$CODEX_HOME/$f" ] || : > "$CODEX_HOME/$f"; done
[ -e "$CODEX_HOME/hooks.json" ] || printf '{}\n' > "$CODEX_HOME/hooks.json"
# write_policy orchestrator-only: the role gate's files must be exactly what agentteams shipped.
sha(){ { sha256sum "$1" 2>/dev/null || shasum -a 256 "$1"; } | cut -d" " -f1; }
pin(){ if [ ! -f "$1" ] || [ -L "$1" ] || [ "$(sha "$1")" != "$2" ]; then
  echo "REFUSING: $1 is missing, a symlink, or not the pinned copy; regenerate the team with agentteams." >&2; exit 2; fi; }
pin "$ROOT/.agentteams/bin/codex-role-gate.py" 8e2a3bea7a3b0022c85db521431699506641859bcc7577360bb82031e9f874c1
pin "$ROOT/.agentteams/bin/goose-readfs-mcp.py" dc8413e8ec16298e79b5ff27e6629c792693ef88bcae4c9f9c40e85d127cab58
pin "$ROOT/.codex/hooks.json" 440226be258249e417ecd48378da09ad44551391dc2941912da4de44c5a33858
case "$ROOT" in *[\"\\]*|*[[:cntrl:]]*)
  echo "REFUSING: the project path has a quote, backslash or control character; config.toml cannot name it safely." >&2; exit 2 ;; esac
# The gate and the server run under an ABSOLUTE interpreter resolved here, outside the launcher, so no
# writable PATH entry (a project venv, say) can stand in for python3. Override: AGENTTEAMS_CODEX_PYTHON.
PY="${AGENTTEAMS_CODEX_PYTHON:-$(command -v python3 || true)}"
case "$PY" in /*) ;; *) echo "REFUSING: no absolute python3 (set AGENTTEAMS_CODEX_PYTHON)." >&2; exit 2 ;; esac
# Follow a symlinked interpreter to its target, so a link outside the project into it is caught.
n=0; while [ -L "$PY" ] && [ "$n" -lt 40 ]; do
  t="$(readlink "$PY")"; case "$t" in /*) PY="$t" ;; *) PY="$(dirname "$PY")/$t" ;; esac; n=$((n + 1)); done
PY="$(cd "$(dirname "$PY")" && pwd -P)/$(basename "$PY")"
case "$PY/" in "$ROOT"/*|"$CODEX_HOME"/*|*[\"\\]*|*[[:cntrl:]]*)
  echo "REFUSING: python3 at $PY is inside a path agents can write (or unquotable); set AGENTTEAMS_CODEX_PYTHON to an interpreter outside the project." >&2; exit 2 ;; esac
if grep -qs agentteams_readfs "$ROOT/.codex/config.toml"; then   # any form: table, dotted key, inline
  echo "REFUSING: $ROOT/.codex/config.toml mentions agentteams_readfs; only the runner may define that server." >&2; exit 2; fi
# Nested Codex config or hooks (subdir/.codex/) would apply to a session started below the root; refuse them.
# (|| true: an unreadable dir or head closing the pipe must not kill the runner under pipefail.)
# Case-insensitive (APFS resolves .CODEX to .codex); files or symlinks, and a symlinked .codex dir itself.
NESTED="$( { find "$ROOT" \( -path "$ROOT/.git" -o -path "$ROOT/.codex" \) -prune -o \
  \( \( -type f -o -type l \) \( -ipath "*/.codex/hooks.json" -o -ipath "*/.codex/config.toml" \) \) -print -o \
  \( -type l -iname .codex \) -print 2>/dev/null || true; } | head -n 5)"
if [ -n "$NESTED" ]; then
  echo "REFUSING: nested Codex config or hooks found; under write_policy orchestrator-only only $ROOT/.codex/ may hold them:" >&2
  printf '%s\n' "$NESTED" >&2; exit 2; fi
READFS_TOML="[mcp_servers.agentteams_readfs]
command = \"$PY\"
args = [\"-I\", \"-S\", \"$ROOT/.agentteams/bin/goose-readfs-mcp.py\", \"--root\", \"$ROOT\"]"
if [ ! -s "$CODEX_HOME/config.toml" ]; then printf '%s\n' "$READFS_TOML" > "$CODEX_HOME/config.toml"
elif [ "$(grep -xF -A2 -- "[mcp_servers.agentteams_readfs]" "$CODEX_HOME/config.toml")" != "$READFS_TOML" ]; then
  echo "REFUSING: $CODEX_HOME/config.toml lacks the read-only server agents need under write_policy" >&2
  echo "orchestrator-only (exactly once, as one block). Add these lines to it (outside the launcher), then rerun:" >&2
  printf '%s\n' "$READFS_TOML" >&2; exit 2; fi
if awk -v gate=1 'gate && $0 == "[mcp_servers.agentteams_readfs]" { next }
    /^[[:space:]]*(approval_policy|sandbox_mode|notify)[[:space:]]*=/ || /^[[:space:]]*\[(mcp_servers|sandbox_workspace_write|hooks|plugins)/ || /^[[:space:]]*plugins\./ { f = 1 }
    END { exit !f }' "$CODEX_HOME/config.toml"; then
  echo "WARNING: $CODEX_HOME/config.toml sets security-relevant keys; review it (it is read-only in the sandbox, but Codex honours it)." >&2
fi
SCRATCH="${CODEX_CONFINE_SCRATCH:-$(mktemp -d "${TMPDIR:-/tmp}/codex-confined.XXXXXX")}"
PROTECT=()
if [ -e "$ROOT/.agentteams" ]; then PROTECT+=( --protect "$ROOT/.agentteams" ); fi
if [ -e "$ROOT/.agentteams-status" ]; then PROTECT+=( --protect "$ROOT/.agentteams-status" ); fi
for f in config.toml hooks.json AGENTS.md AGENTS.override.md rules prompts skills plugins; do
  PROTECT+=( --protect "$CODEX_HOME/$f" ); done
EGRESS="${CODEX_CONFINE_EGRESS:-host}"
# Self-probe facts are read OUTSIDE the launcher (inside, a denied path can look absent).
PK=0; [ -n "$(ls -A "$HOME/.config/agentteams/keys" 2>/dev/null)" ] && PK=1
PA=0; [ -e "$ROOT/.agentteams" ] && PA=1
PC=0; [ -d "$ROOT/.codex" ] && PC=1
PEM=""; for p in "$HOME"/.config/agentteams/*.pem; do [ -f "$p" ] && { PEM="$p"; break; }; done
SELF_PROBE='set -u
fail(){ echo "SELF-PROBE FAILED: $1. This launch is NOT confined as expected; refusing to start Codex." >&2; exit 3; }
unwritable(){ if ( : >> "$1" ) 2>/dev/null; then fail "$1 is writable"; fi; }
if [ "$AGENTTEAMS_PROBE_KEYS" = 1 ] && [ -n "$(ls -A "$HOME/.config/agentteams/keys" 2>/dev/null)" ]; then
  fail "the signing-key dir is readable"; fi
if [ -n "$AGENTTEAMS_PROBE_PEM" ] && head -c 1 "$AGENTTEAMS_PROBE_PEM" >/dev/null 2>&1; then
  fail "a legacy signing-key file is readable"; fi
if [ "$AGENTTEAMS_PROBE_AT" = 1 ]; then
  d="$AGENTTEAMS_ROOT/.agentteams/.self-probe.$$"
  if mkdir "$d" 2>/dev/null; then rmdir "$d"; fail "$AGENTTEAMS_ROOT/.agentteams is writable"; fi; fi
if [ "$AGENTTEAMS_PROBE_CODEX" = 1 ]; then
  d="$AGENTTEAMS_ROOT/.codex/.self-probe.$$"
  if mkdir "$d" 2>/dev/null; then rmdir "$d"; fail "$AGENTTEAMS_ROOT/.codex is writable"; fi; fi
unwritable "$CODEX_HOME/config.toml"; unwritable "$CODEX_HOME/hooks.json"
if [ "$AGENTTEAMS_PROBE_GATE" = 1 ]; then
  unwritable "$AGENTTEAMS_ROOT/.codex/hooks.json"; unwritable "$AGENTTEAMS_ROOT/.agentteams/bin/codex-role-gate.py"; fi
exec codex "$@"'
exec "$LAUNCHER" --scratch "$SCRATCH" --writable "$REPO_ROOT" --writable "$CODEX_HOME" \
  ${PROTECT[@]+"${PROTECT[@]}"} --protect-prompt-roots --egress "$EGRESS" \
  --setenv CODEX_HOME="$CODEX_HOME" --setenv AGENTTEAMS_ROOT="$ROOT" --setenv AGENTTEAMS_CODEX_CONFINED=1 \
  --setenv AGENTTEAMS_PROBE_KEYS="$PK" --setenv AGENTTEAMS_PROBE_AT="$PA" --setenv AGENTTEAMS_PROBE_GATE=1 \
  --setenv AGENTTEAMS_PROBE_PEM="$PEM" --setenv AGENTTEAMS_PROBE_CODEX="$PC" --setenv AGENTTEAMS_PYTHON="$PY" --env-allow PATH --env-allow HOME \
  -- bash -c "$SELF_PROBE" codex-confined --sandbox danger-full-access --dangerously-bypass-hook-trust "$@"
