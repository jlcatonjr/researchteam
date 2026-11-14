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
#      RELEASE-LOCKED repos (toolchain.lock has `agentteams.tag=`): the target is instead the newest
#      VERIFIED signed tag on that tag's vX.Y line (scripts/check_toolchain.py --release-candidate /
#      --verify-tag), never `main`; no newer tag -> no-op. --force re-integrates the locked tag (soak).
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
#                            (a mirror or fork is not github.com/jlcatonjr/agentteams, so the layer-1
#                            provenance guard refuses it unless RESEARCHTEAM_ALLOW_UNVERIFIED_AGENTTEAMS=1)
#   AUTOSYNC_PR_BODY_FILE    where to write the PR body (default: ./.autosync-pr-body.md, gitignored)
# GitHub outputs (when $GITHUB_OUTPUT is set): changed=<bool>, new_sha=<sha>, old_sha=<sha>
# Exit: 0 = success (check `changed`); non-zero = a blocking gate failed (workflow must NOT open a PR).

set -uo pipefail

# >>> self-copy
# Run from a private copy. bash reads a script incrementally from its file, and in derived mode the
# layer-2 sync below REPLACES this very file; bash would then continue from the old byte offset in
# the new content and die mid-line (mathAgents run 38064339274). The copy is removed on exit.
# AUTOSYNC_GATE_REEXEC is trusted only when it names this run's own private copy; any other value is
# ignored (and never deleted). AUTOSYNC_GATE_DEPTH caps the re-exec at one hop, so a copy path that
# somehow fails the match (e.g. path normalisation) cannot loop and leak a copy per hop. Both are
# unset at once so child processes (researchteam, agentteams, a nested gate) never inherit them.
_gate_self="${AUTOSYNC_GATE_REEXEC:-}"
_gate_depth="${AUTOSYNC_GATE_DEPTH:-0}"
unset AUTOSYNC_GATE_REEXEC AUTOSYNC_GATE_DEPTH
case "$_gate_self" in
  "${TMPDIR:-/tmp}"/agentteams_autosync_gate.??????) [ "$_gate_self" = "$0" ] || _gate_self="" ;;
  *) _gate_self="" ;;
esac
if [ -z "$_gate_self" ]; then
  if [ "$_gate_depth" != "0" ]; then
    # Refuse only. $0 is never deleted here: the depth variable may be planted, and $0 the real gate.
    echo "autosync-gate: refusing a second re-exec (private copy $0 not recognised)" >&2
    exit 1
  fi
  _gate_copy="$(mktemp "${TMPDIR:-/tmp}/agentteams_autosync_gate.XXXXXX")" \
    || { echo "autosync-gate: cannot create a private copy of the gate" >&2; exit 1; }
  cp "$0" "$_gate_copy" \
    || { rm -f "$_gate_copy"; echo "autosync-gate: cannot copy the gate to $_gate_copy" >&2; exit 1; }
  shopt -s execfail  # a failed exec returns here (instead of exiting) so the copy can be removed
  AUTOSYNC_GATE_REEXEC="$_gate_copy" AUTOSYNC_GATE_DEPTH=1 exec bash "$_gate_copy" "$@"
  rm -f "$_gate_copy"
  echo "autosync-gate: cannot run the private copy $_gate_copy" >&2
  exit 1
fi
trap 'rm -f "$_gate_self"' EXIT
# <<< self-copy

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
  # Native surfaces re-rendered by `researchteam update` write the same machine-path-bearing files (S-8).
  ".claude/agents/references/delivery-receipt.json"
  ".claude/agents/references/memory-index.json"
  ".goose/recipes/references/delivery-receipt.json"
  ".goose/recipes/references/memory-index.json"
)
# Known-noise the PR BODY omits so the reviewer sees signal, not regen churn (the commit still carries
# it — a full regen produces it — but the body highlights only substantive paths).
NOISE_REGEX='(^|/)(build-log\.json|delivery-receipt\.json|memory-index\.json|security-vulnerability-watch\.(json|reference\.md)|pipeline-graph\.(md|svg)|pipeline-handoffs\.svg|architecture-graph\.(md|svg)|architecture-modules\.svg|bridge-manifest\.json)$'

# Security-boundary paths: in scope for an update, but a change to any of them must not merge on a
# routine review. They are listed first in the PR body and the job emits `sensitive=true`, which the
# workflow turns into a `security-review-required` label. Hooks, confinement, CI, executable scripts,
# agent capability declarations and ownership rules.
SENSITIVE_REGEX='^(sandbox/|\.agentteams/bin/|\.github/workflows/|\.github/actions/|\.github/agents/[^/]+\.agent\.md$|(\.github/|docs/)?CODEOWNERS$|pyproject\.toml$|\.claude/settings[^/]*\.json$|\.codex/(config\.toml|hooks\.json)$|\.goose/recipes/|\.vscode/tasks\.json$|scripts/)'

# Print the security-boundary paths among the newline-separated paths on stdin.
sensitive_paths() { grep -E "$SENSITIVE_REGEX" || true; }

while [ $# -gt 0 ]; do
  case "$1" in
    # Test hook: classify paths from stdin with the gate's own rule, then exit (no git, no writes).
    --classify-sensitive) sensitive_paths; exit 0 ;;
    --mode) MODE="${2:-upstream}"; shift 2 ;;
    --check-only) CHECK_ONLY=1; shift ;;
    --force) FORCE=1; shift ;;
    *) echo "autosync-gate: unknown arg: $1" >&2; exit 2 ;;
  esac
done

emit() { [ -n "${GITHUB_OUTPUT:-}" ] && printf '%s\n' "$1" >> "$GITHUB_OUTPUT" || true; }
log()  { printf 'autosync-gate: %s\n' "$1"; }

lock_tag() { [ -f toolchain.lock ] && sed -n "s/^$1\.tag=//p" toolchain.lock | head -1 | tr -d '[:space:]'; }

# --- 1. SHA-GATE (first; no writes on the no-change path) -----------------------------------------
RELEASE_TAG="$(lock_tag agentteams)"
TARGET_TAG=""
if [ -n "$RELEASE_TAG" ]; then
  # Release-locked: follow the tag's release line, verified, and never fall back to main.
  log "release-locked at agentteams ${RELEASE_TAG}: following its release line (never main)."
  candidate="$(python scripts/check_toolchain.py --release-candidate agentteams)" \
    || { log "GATE FAIL: cannot read the agentteams release line"; exit 1; }
  if [ -z "$candidate" ] && [ "$FORCE" -eq 0 ]; then
    log "no newer verified release on ${RELEASE_TAG}'s line — nothing to integrate."
    emit "changed=false"; exit 0
  fi
  TARGET_TAG="${candidate:-$RELEASE_TAG}"
  new_sha="$(python scripts/check_toolchain.py --verify-tag agentteams "$TARGET_TAG")" \
    || { log "GATE FAIL: agentteams ${TARGET_TAG} did not verify as a signed release tag"; exit 1; }
  log "agentteams ${TARGET_TAG} verified: peeled commit ${new_sha}"
else
  new_sha="$(git ls-remote "$AGENTTEAMS_GIT" main 2>/dev/null | awk 'NR==1{print $1}')"
  if [ -z "$new_sha" ]; then
    # Fail closed, as the release-locked path does: an unreachable remote (or a missing `main`) must
    # not pass as a green "nothing to integrate" run.
    echo "::warning::autosync-gate: git ls-remote returned no SHA for ref 'main' at ${AGENTTEAMS_GIT}"
    log "GATE FAIL: cannot resolve upstream agentteams main via git ls-remote ($AGENTTEAMS_GIT)"
    exit 1
  fi
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
RT_TAG="$(lock_tag researchteam)"
if [ "$MODE" = "derived" ] && [ -n "$RT_TAG" ]; then
  # Release-locked researchteam: run the verified pinned researchteam, whose Layer-2 files `update`
  # syncs from that same tag (not the researchteam main the workflow installed).
  rt_pin="$(sed -n 's/^researchteam=.*@//p' toolchain.lock | head -1 | tr -d '[:space:]')"
  rt_sha="$(python scripts/check_toolchain.py --verify-tag researchteam "$RT_TAG")" \
    || { log "GATE FAIL: researchteam ${RT_TAG} did not verify as a signed release tag"; exit 1; }
  [ "$rt_sha" = "$rt_pin" ] \
    || { log "GATE FAIL: toolchain.lock pins researchteam ${rt_pin:0:7}, but ${RT_TAG} is ${rt_sha:0:7}"; exit 1; }
  log "installing researchteam ${RT_TAG} @ ${rt_sha} (release-locked)"
  python -m pip install --quiet --no-deps --force-reinstall "git+https://github.com/jlcatonjr/researchteam.git@${rt_sha}" \
    || { log "pip install of researchteam@${rt_sha} FAILED"; exit 1; }
fi
# agentteams' runtime dependencies are held to S-10 too. The base install declares only `jsonschema>=4.20`,
# which resolves to the first six packages below on Python 3.11-3.12 (typing-extensions is unused from 3.13). The
# last three are agentteams' [signing] backend: without cryptography the render cannot verify an operator-signed
# (Ed25519) decision row, fails closed, and silently drops the relaxation it authorizes (the S-10 carve-out for
# jlcatonjr/agentteams), so a CI render would differ from a bootstrap_toolchain.sh one. These
# are the vetted versions in upstream docs/release/constraints-2026-11-13.txt, which derived repositories do
# not receive; tests/test_toolchain.py keeps the two equal. Everything installs --no-deps, so pip resolves no
# runtime dependency on its own. (Building agentteams from git still installs its exact-pinned [build-system]
# backend, setuptools, which has no dependencies.) `pip check` then fails the gate if this agentteams commit
# needs a package or version outside the set, so a new dependency is vetted here first, never installed unvetted.
AGENTTEAMS_DEPS='jsonschema==4.26.0
attrs==26.1.0
jsonschema-specifications==2025.9.1
referencing==0.37.0
rpds-py==2026.9.1
typing-extensions==4.16.0
cryptography==50.0.2
cffi==2.1.1
pycparser==3.12'
log "installing agentteams' vetted dependency set (no-deps)"
# --only-binary: a missing wheel must fail, not build from source (rpds-py would fetch an unpinned maturin).
# shellcheck disable=SC2086  # fixed literal list above; word splitting is intended
python -m pip install --quiet --only-binary=:all: --no-deps $AGENTTEAMS_DEPS || {
  log "pip install of agentteams' vetted dependency set FAILED"; exit 1; }
python -c "import cryptography" 2>/dev/null || {
  log "GATE FAIL: cryptography is not importable, so every signed-row check would fail closed and drop its relaxation"
  exit 1; }
log "installing agentteams @ ${new_sha} (pinned; closes ls-remote/pip TOCTOU)"
python -m pip install --quiet --no-deps "git+${AGENTTEAMS_GIT}@${new_sha}" || {
  log "pip install of agentteams@${new_sha} FAILED"; exit 1; }
python -m pip check || {
  echo "::error::autosync-gate: agentteams@${new_sha} needs a dependency outside the S-10 vetted set (AGENTTEAMS_DEPS)"
  log "GATE FAIL: agentteams@${new_sha} needs a dependency outside the S-10 vetted set (AGENTTEAMS_DEPS); vet it first"
  exit 1; }
command -v agentteams >/dev/null 2>&1 || { log "agentteams not on PATH after install"; exit 1; }

# Recorded before the regen: the toolchain-group trust-root guard (section 4) refuses a regen that moves HEAD.
pre_regen_head="$(git rev-parse HEAD 2>/dev/null || true)"
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
  # Update runs always enforce the scope allowlist, even if the caller exported the skip switch.
  VALIDATION_SKIP_SCOPE=0 bash scripts/validate_agentteams_update.sh || { log "GATE FAIL: validate_agentteams_update"; exit 1; }
fi
# Detector unit tests are UPSTREAM-ONLY (fixtures are never synced into research repos).
if [ "$MODE" = "upstream" ]; then
  for t in test_methodology_coverage test_historical_context test_citation_integrity test_literature_library; do
    [ -f "scripts/tests/${t}.sh" ] && { bash "scripts/tests/${t}.sh" || { log "GATE FAIL: ${t}"; exit 1; }; }
  done
fi

# --- 4. Record the integrated SHA + emit the substantive-change summary --------------------------
printf '%s\n' "$new_sha" > "$REF_FILE"
# Pin the toolchain this green sync was verified with (researchteam + agentteams commits of the
# interpreter that just ran it), so bootstrap_toolchain.sh and the SessionStart check follow it.
# Advisory: a lock that cannot be written (no recorded commit) never fails the sync, unless the repo is
# release-locked, where it fails closed.
lock_note=""
if [ -f scripts/check_toolchain.py ]; then
  # No --python: pin the interpreter behind `researchteam`, the one that just ran the sync.
  # A release-locked lock is rewritten only with the verified tag; check_toolchain refuses anything else.
  lock_args=(--write-lock); [ -n "$TARGET_TAG" ] && lock_args+=(--tag "agentteams=${TARGET_TAG}")
  # Upstream only: researchteam's own pyproject `update`/`research` extras must name the lock's agentteams
  # commit (release policy, Pins). A derived repo's pyproject.toml is project-owned and never rewritten.
  [ "$MODE" = upstream ] && lock_args+=(--sync-extras)
  if lock_out="$(python scripts/check_toolchain.py "${lock_args[@]}" 2>&1)"; then
    log "$lock_out"
  else
    log "toolchain.lock not written: $lock_out"; lock_note="$lock_out"
    # Release-locked: an unrecorded pin move would ship a commit the lock does not name. Fail closed.
    [ -n "$TARGET_TAG" ] && { log "GATE FAIL: release-locked toolchain.lock could not record ${TARGET_TAG}"; exit 1; }
  fi
elif [ -n "$TARGET_TAG" ]; then
  log "GATE FAIL: release-locked, but scripts/check_toolchain.py is missing"; exit 1
fi

# First-party toolchain group (operator rulings T2/R9). Runs on every integrating run, after the lock is written.
# 1. Trust-root guard: the candidate agentteams has just run (the regen), so it could have altered what the check
#    trusts. HEAD must not have moved, and the group file, the operator verify keys and the signed decision log
#    must be exactly as committed (untracked, gitignored, skip-worktree and assume-unchanged entries count too).
#    An autosync run never changes them legitimately. This stops accidents and a careless regen, not a hostile
#    candidate: the check runs that candidate's code. On release-locked runs the signed-tag check (section 1)
#    is what makes the candidate trustworthy, and an exit 0 for an untagged agentteams pin is refused below.
# 2. `agentteams --verify-toolchain-pin` (read-only, agentteams >= v1.1.2; an agentteams without it fails on its
#    own message) maps its exit code as follows:
#      0  every group pin verified: the S-10 toolchain-group exemption applies.
#      2  no group file, so no exemption is claimed and the ordinary S-10 rules apply (the 14-day cooldown, plus a
#         pin row where policy needs one). Never "verified". In upstream mode it fails: researchteam is a group
#         member and must carry the file. In derived mode it passes with a ::warning:: and a PR-body notice.
#      1  a present group file or a group pin failed (refused, bad pin, a group pin without NAME.tag): hard fail.
#      *  anything else: hard fail.
GROUP_TRUST_PATHS=(.agentteams/toolchain-group.json .github/agents/references/authorized-verify-keys
                   .github/agents/references/security-decisions.log.csv)
group_note=""
group_fail() { echo "::error::autosync-gate: $1"; log "GATE FAIL: $1"; exit 1; }
# Fail closed: a git error must never read as "nothing changed".
head_now="$(git rev-parse HEAD 2>/dev/null)" || group_fail "trust-root guard: cannot read HEAD"
[ -n "$pre_regen_head" ] && [ "$head_now" = "$pre_regen_head" ] \
  || group_fail "the regen moved HEAD (${pre_regen_head:-<none>} -> ${head_now}); a regen never commits"
tampered="$(git status --porcelain --ignored -- "${GROUP_TRUST_PATHS[@]}")" \
  || group_fail "trust-root guard: git status failed"
[ -z "$tampered" ] || { printf '%s\n' "$tampered"; group_fail "the regen changed the toolchain-group trust root"; }
# Skip-worktree (S) and assume-unchanged (lowercase) entries are invisible to `git status`.
flags="$(git ls-files -v -- "${GROUP_TRUST_PATHS[@]}")" || group_fail "trust-root guard: git ls-files failed"
hidden="$(printf '%s\n' "$flags" | grep -E '^([a-z]|S) ' || true)"
[ -z "$hidden" ] || { printf '%s\n' "$hidden"; group_fail "trust-root files are marked skip-worktree/assume-unchanged"; }

if [ ! -f toolchain.lock ]; then
  # A lock-less derived repo pins nothing, so there is no group pin to verify and no exemption to claim.
  [ "$MODE" = "upstream" ] && group_fail "no toolchain.lock in upstream mode"
  log "no toolchain.lock: no group pins; no S-10 exemption claimed"
  group_note="no toolchain.lock: no S-10 exemption claimed"
else
  group_signers="${AGENTTEAMS_ALLOWED_SIGNERS:-$HOME/.config/agentteams/allowed_signers}"
  # argparse also exits 2 on an unknown flag, so an agentteams too old for the check is reported on its own.
  # The help text is captured first: under pipefail, `--help | grep -q` can fail on SIGPIPE after a match.
  at_help="$(agentteams --help 2>/dev/null || true)"
  case "$at_help" in *--verify-toolchain-pin*) ;; *) false ;; esac \
    || group_fail "this agentteams has no --verify-toolchain-pin (added in agentteams v1.1.2)"
  log "verifying toolchain-group pins in toolchain.lock (agentteams --verify-toolchain-pin)"
  pin_rc=0
  agentteams --verify-toolchain-pin toolchain.lock --allowed-signers "$group_signers" --output .github/agents \
    || pin_rc=$?
  # An agentteams pin with no agentteams.tag line can never verify (it exits 1), so a 0 there is not genuine.
  if [ "$pin_rc" -eq 0 ] && grep -q '^agentteams=' toolchain.lock && [ -z "$(lock_tag agentteams)" ]; then
    group_fail "--verify-toolchain-pin exited 0 for an untagged agentteams pin, which cannot verify"
  fi
  case "$pin_rc" in
    0) log "toolchain-group pins verified: the S-10 toolchain-group exemption applies"
       group_note="verified (the S-10 toolchain-group exemption applies)" ;;
    2) [ "$MODE" = "upstream" ] && group_fail "no .agentteams/toolchain-group.json, but researchteam is a group member (exit 2)"
       echo "::warning::autosync-gate: no toolchain-group file: no exemption claimed; ordinary S-10 rules apply"
       log "no toolchain-group file (exit 2): no exemption claimed; the ordinary S-10 rules apply"
       group_note="**no group file: no toolchain-group exemption claimed.** The ordinary S-10 rules apply at review: each pinned release clears the 14-day cooldown unless another recorded carve-out covers it, and carries a pin row where policy needs one" ;;
    1) group_fail "a toolchain-group pin or the group file did not verify (exit 1)" ;;
    *) group_fail "agentteams --verify-toolchain-pin exited ${pin_rc}" ;;
  esac
fi

git add -A >/dev/null 2>&1 || true
staged="$(git -c core.quotePath=false diff --cached --name-only 2>/dev/null)"
substantive="$(printf '%s\n' "$staged" | grep -Ev "$NOISE_REGEX" | grep -v '\.agentteams-backups/' | sed '/^$/d' || true)"
# Security-boundary paths are called out first, whatever the churn filter says.
sensitive="$(printf '%s\n' "$staged" | sensitive_paths)"
# toolchain.lock decides what code bootstrap installs. Its commit moves every sync (routine), but a
# change of the pinned REPOSITORY is security-relevant (check_toolchain/bootstrap refuse it anyway).
if printf '%s\n' "$staged" | grep -qx 'toolchain.lock'; then
  lock_repos() { grep -E '^(researchteam|agentteams)=' | sed 's/@.*//' | sort; }
  if [ "$(git show HEAD:toolchain.lock 2>/dev/null | lock_repos)" != "$(lock_repos < toolchain.lock)" ]; then
    sensitive="$(printf '%s\n%s\n' "$sensitive" "toolchain.lock (pinned repository changed)" | sed '/^$/d')"
  fi
  # A release tag decides which line the next run follows; dropping or rewinding one is a trust change.
  lock_tag_lines() { grep -E '^(researchteam|agentteams)\.tag=' | sort; }
  if [ "$(git show HEAD:toolchain.lock 2>/dev/null | lock_tag_lines)" != "$(lock_tag_lines < toolchain.lock)" ]; then
    sensitive="$(printf '%s\n%s\n' "$sensitive" "toolchain.lock (release tag changed)" | sed '/^$/d')"
  fi
fi
if [ -n "$sensitive" ]; then emit "sensitive=true"; else emit "sensitive=false"; fi
{
  echo "## Automatic agentteams integration"
  echo
  if [ -n "$sensitive" ]; then
    echo "> [!WARNING]"
    echo "> **Security-boundary paths changed — \`@security\` review required before merge:**"
    printf '%s\n' "$sensitive" | sed 's/^/> - `/; s/$/`/'
    echo
  fi
  if [ -n "$TARGET_TAG" ]; then
    echo "agentteams release line \`${RELEASE_TAG}\` → verified signed tag \`${TARGET_TAG}\` — integrating its peeled SHA."
  else
    echo "agentteams \`main\` advanced — integrating the pinned SHA."
  fi
  echo
  echo "- **agentteams:** \`${old_sha:-<none>}\` → \`${new_sha}\`${TARGET_TAG:+ (${TARGET_TAG})}"
  echo "- **mode:** ${MODE}"
  if [ -f toolchain.lock ]; then
    echo "- **toolchain.lock:** $(grep -E '^(researchteam|agentteams)=' toolchain.lock | sed 's/=.*@\(.\{7\}\).*/ \1/' | paste -sd, - | sed 's/,/, /g')"
  fi
  [ -n "$lock_note" ] && echo "- **toolchain.lock not updated:** ${lock_note}"
  [ -n "$group_note" ] && echo "- **toolchain group:** ${group_note}"
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
