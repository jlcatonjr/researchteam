#!/usr/bin/env bash
# agentteams autosync gate — the SINGLE SOURCE OF TRUTH for automatic agentteams integration.
#
# The problem it solves: agentteams is a git dependency (not on PyPI), and its version string does
# NOT move on every change (it stayed 1.0.0rc6 across 8 substantive commits). So drift can only be
# detected by the git SHA of agentteams `main`. And because a `--update --merge` refreshes threat
# intelligence, graphs, and timestamps on EVERY run, a naive "did any file change?" check is always
# true — it would open a spam PR every week. This gate keys on the agentteams SHA instead.
#
# What it does (in order):
#   1. SHA-GATE FIRST (before any install/regen): compare agentteams main HEAD to the ref recorded on
#      the evergreen PR branch (if open) or on the current branch. If unchanged -> emit changed=false
#      and exit 0 with ZERO writes. This is the whole "evergreen, not weekly spam" guarantee.
#   2. On a real change: install that EXACT SHA (reproducible + closes the ls-remote/pip TOCTOU), run
#      the researchteam regen (--shrink-policy preserve is pinned in _update_cmd), scrub machine-path
#      churn (delivery-receipt/memory-index embed absolute paths that flip to the runner path), run the
#      BLOCKING gates, record the new SHA, and emit the substantive changed paths for the auto-PR body.
#
# Auto-PR ONLY — this script never merges. The calling workflow opens/updates ONE evergreen PR that a
# human reviews and merges (policy: auto-merge disabled).
#
# Usage:
#   scripts/agentteams_autosync_gate.sh --mode {upstream|derived} [--check-only]
# Env (optional):
#   AGENTTEAMS_GIT           override the agentteams git URL
#   AUTOSYNC_PR_BODY_FILE    where to write the PR body (default: ./.autosync-pr-body.md, gitignored)
# GitHub outputs (when $GITHUB_OUTPUT is set): changed=<bool>, new_sha=<sha>, old_sha=<sha>
# Exit: 0 = success (check `changed`); non-zero = a blocking gate failed (workflow must NOT open a PR).

set -uo pipefail

MODE="upstream"
CHECK_ONLY=0
FORCE=0
AGENTTEAMS_GIT="${AGENTTEAMS_GIT:-https://github.com/jlcatonjr/agentteams.git}"
REF_FILE=".github/agentteams-autosync-ref"
EVERGREEN_BRANCH="chore/agentteams-autosync"
PR_BODY_FILE="${AUTOSYNC_PR_BODY_FILE:-.autosync-pr-body.md}"

# Machine-specific churn: these embed absolute resolved paths that regenerate to the CI runner path;
# committing them would propose a nonexistent path and guarantee reverse-churn on the next local run.
SCRUB_PATHS=(
  ".github/agents/references/delivery-receipt.json"
  ".github/agents/references/memory-index.json"
)
# Known-noise the PR BODY omits so the reviewer sees signal, not regen churn (the commit still carries
# it — a full regen produces it — but the body highlights only substantive paths).
NOISE_REGEX='(^|/)(build-log\.json|delivery-receipt\.json|memory-index\.json|security-vulnerability-watch\.(json|reference\.md)|pipeline-graph\.(md|svg)|pipeline-handoffs\.svg|architecture-graph\.(md|svg)|architecture-modules\.svg|bridge-manifest\.json)$'

while [ $# -gt 0 ]; do
  case "$1" in
    --mode) MODE="${2:-upstream}"; shift 2 ;;
    --check-only) CHECK_ONLY=1; shift ;;
    --force) FORCE=1; shift ;;
    *) echo "autosync-gate: unknown arg: $1" >&2; exit 2 ;;
  esac
done

emit() { [ -n "${GITHUB_OUTPUT:-}" ] && printf '%s\n' "$1" >> "$GITHUB_OUTPUT" || true; }
log()  { printf 'autosync-gate: %s\n' "$1"; }

# --- 1. SHA-GATE (first; no writes on the no-change path) -----------------------------------------
new_sha="$(git ls-remote "$AGENTTEAMS_GIT" main 2>/dev/null | awk 'NR==1{print $1}')"
if [ -z "$new_sha" ]; then
  log "could not reach agentteams main via git ls-remote ($AGENTTEAMS_GIT) — treating as no-op."
  emit "changed=false"; exit 0
fi
# Baseline = the ref recorded on the OPEN evergreen PR branch if it exists (so an already-integrated
# SHA does not re-fire weekly while the PR waits to be merged), else the ref on the current branch.
old_sha=""
if git show "origin/${EVERGREEN_BRANCH}:${REF_FILE}" >/dev/null 2>&1; then
  old_sha="$(git show "origin/${EVERGREEN_BRANCH}:${REF_FILE}" 2>/dev/null | tr -d '[:space:]')"
elif [ -f "$REF_FILE" ]; then
  old_sha="$(tr -d '[:space:]' < "$REF_FILE")"
fi
emit "new_sha=$new_sha"
emit "old_sha=$old_sha"
if [ "$new_sha" = "$old_sha" ] && [ "$FORCE" -eq 0 ]; then
  log "agentteams up-to-date (${new_sha}) — nothing to integrate."
  emit "changed=false"; exit 0
fi
[ "$FORCE" -eq 1 ] && log "forced run (--force): integrating ${new_sha} regardless of the recorded ref."
log "agentteams update detected: ${old_sha:-<none>} -> ${new_sha}"
if [ "$CHECK_ONLY" -eq 1 ]; then
  emit "changed=true"; exit 0
fi

# --- 2. Integrate exactly that SHA ---------------------------------------------------------------
log "installing agentteams @ ${new_sha} (pinned; closes ls-remote/pip TOCTOU)"
python -m pip install --quiet "git+${AGENTTEAMS_GIT}@${new_sha}" || {
  log "pip install of agentteams@${new_sha} FAILED"; exit 1; }
command -v agentteams >/dev/null 2>&1 || { log "agentteams not on PATH after install"; exit 1; }

log "running researchteam regen (mode=${MODE})"
if [ "$MODE" = "derived" ]; then
  researchteam update --yes || { log "researchteam update FAILED"; exit 1; }
else
  researchteam update --layer1-only --yes || { log "researchteam update --layer1-only FAILED"; exit 1; }
fi

# Scrub machine-path churn so the PR never proposes a runner path.
for p in "${SCRUB_PATHS[@]}"; do git checkout -- "$p" 2>/dev/null || true; done

# --- 3. BLOCKING gates (a failure means NO PR) ---------------------------------------------------
if [ -d ".github/agents/.github" ]; then log "GATE FAIL: forbidden nested mirror .github/agents/.github"; exit 1; fi
if [ -f scripts/validate_agentteams_update.sh ]; then
  bash scripts/validate_agentteams_update.sh || { log "GATE FAIL: validate_agentteams_update"; exit 1; }
fi
# Detector unit tests are UPSTREAM-ONLY (fixtures are never synced into research repos).
if [ "$MODE" = "upstream" ]; then
  for t in test_methodology_coverage test_citation_integrity test_literature_library; do
    [ -f "scripts/tests/${t}.sh" ] && { bash "scripts/tests/${t}.sh" || { log "GATE FAIL: ${t}"; exit 1; }; }
  done
fi

# --- 4. Record the integrated SHA + emit the substantive-change summary --------------------------
printf '%s\n' "$new_sha" > "$REF_FILE"

git add -A >/dev/null 2>&1 || true
substantive="$(git diff --cached --name-only 2>/dev/null | grep -Ev "$NOISE_REGEX" | grep -v '\.agentteams-backups/' || true)"
{
  echo "## Automatic agentteams integration"
  echo
  echo "agentteams \`main\` advanced — integrating the pinned SHA."
  echo
  echo "- **agentteams:** \`${old_sha:-<none>}\` → \`${new_sha}\`"
  echo "- **mode:** ${MODE}"
  echo
  if [ -n "$substantive" ]; then
    echo "**Substantive changed paths** (regen state-churn — graphs / threat-intel / build-log /"
    echo "delivery-receipt / memory-index — omitted for review clarity):"
    echo
    printf '%s\n' "$substantive" | sed 's/^/- `/; s/$/`/'
  else
    echo "_No substantive (non-churn) paths changed — this is a churn-only refresh._"
  fi
  echo
  echo "Gates passed in-job (validate + forbidden-path$( [ "$MODE" = upstream ] && echo ' + detector tests')). "
  echo "Auto-PR only — review and merge to integrate. Machine-path files (delivery-receipt, memory-index)"
  echo "were scrubbed so no runner path is proposed."
} > "$PR_BODY_FILE"
[ -n "${GITHUB_STEP_SUMMARY:-}" ] && cat "$PR_BODY_FILE" >> "$GITHUB_STEP_SUMMARY" || true

emit "changed=true"
log "integration ready (agentteams ${new_sha}); PR body -> ${PR_BODY_FILE}"
exit 0
