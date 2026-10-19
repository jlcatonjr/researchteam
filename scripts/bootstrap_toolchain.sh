#!/usr/bin/env bash
# bootstrap_toolchain.sh — build .venv with the researchteam / agentteams commits pinned in
# toolchain.lock, so every user of this repository runs the toolchain it was last verified with.
# Managed by researchteam (layer 2); adapted from OrthodoxLLM a291cf2.
#
#   bash scripts/bootstrap_toolchain.sh            # install the pinned commits from GitHub
#   bash scripts/bootstrap_toolchain.sh --local    # editable installs from local checkouts:
#                                                  #   RESEARCHTEAM_SRC / AGENTTEAMS_SRC, or the first
#                                                  #   of ../<name> and ../../<name> that exists
#
# Afterwards: `source .venv/bin/activate`, or call .venv/bin/researchteam directly; researchteam
# runs the agentteams installed beside it, so the pinned one is used either way.
# researchteam is installed WITHOUT its [update] extra: that extra pins the agentteams commit researchteam
# was released with, which can differ from (and would conflict with) the agentteams this lock pins.
# agentteams IS installed with its [signing] extra: without cryptography every Ed25519 gate check (signed
# decision rows, pin moves) fails closed in this .venv.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCK="$ROOT/toolchain.lock"
VENV="$ROOT/.venv"
PY="${PYTHON:-python3}"

# S-10 vetted versions for the [signing] chain (upstream docs/release/constraints-2026-10-16.txt, which derived
# repositories do not receive; tests/test_toolchain.py keeps these lines equal to it). agentteams pins only
# cryptography itself; cffi and pycparser would otherwise resolve to whatever is newest at install time.
SIGNING_CONSTRAINTS='cryptography==50.0.0
cffi==2.1.1
pycparser==3.0'

pin() {  # pin <name> -> owner/repo@sha
  grep -E "^$1=" "$LOCK" | head -1 | cut -d= -f2-
}

local_src() {  # local_src <name> <env value> -> checkout path
  local name="$1" given="$2" cand
  if [[ -n "$given" ]]; then printf '%s\n' "$given"; return; fi
  for cand in "$ROOT/../$name" "$ROOT/../../$name"; do
    [[ -d "$cand/.git" ]] && { (cd "$cand" && pwd); return; }
  done
  echo "bootstrap: no local $name checkout found; set $(printf '%s' "$name" | tr a-z A-Z)_SRC" >&2
  exit 2
}

if [[ "${1:-}" == "--local" ]]; then
  RT_SRC="$(local_src researchteam "${RESEARCHTEAM_SRC:-}")"
  AT_SRC="$(local_src agentteams "${AGENTTEAMS_SRC:-}")"
else
  [[ -f "$LOCK" ]] || { echo "bootstrap: toolchain.lock not found at $LOCK (the AgentTeams Autosync writes it; or use --local)" >&2; exit 2; }
  RT="$(pin researchteam)"; AT="$(pin agentteams)"
  # Install only from the two upstream repositories, at a full commit: pip runs a package's build
  # code, so an edited lock must not be able to point the bootstrap anywhere else.
  [[ "$RT" =~ ^jlcatonjr/researchteam@[0-9a-f]{40}$ ]] \
    || { echo "bootstrap: toolchain.lock researchteam= must be jlcatonjr/researchteam@<40-hex sha>, got '$RT'" >&2; exit 2; }
  [[ "$AT" =~ ^jlcatonjr/agentteams@[0-9a-f]{40}$ ]] \
    || { echo "bootstrap: toolchain.lock agentteams= must be jlcatonjr/agentteams@<40-hex sha>, got '$AT'" >&2; exit 2; }
fi

if [[ ! -x "$VENV/bin/python" ]]; then
  echo "[bootstrap] creating $VENV"
  "$PY" -m venv "$VENV"
fi
"$VENV/bin/python" -m pip install -q --upgrade pip

CONSTRAINTS="$(mktemp)"
trap 'rm -f "$CONSTRAINTS"' EXIT
printf '%s\n' "$SIGNING_CONSTRAINTS" > "$CONSTRAINTS"

if [[ "${1:-}" == "--local" ]]; then
  echo "[bootstrap] editable installs: $AT_SRC[signing], $RT_SRC"
  "$VENV/bin/python" -m pip install -q -c "$CONSTRAINTS" -e "$AT_SRC[signing]" -e "$RT_SRC"
  echo "[bootstrap] note: --local follows your checkouts, not toolchain.lock; check_toolchain.py reports any difference."
else
  for spec in "agentteams|$AT|[signing]" "researchteam|$RT|"; do
    IFS='|' read -r name pin extra <<< "$spec"
    url="$name @ git+https://github.com/${pin%@*}@${pin#*@}"
    echo "[bootstrap] $name$extra @ ${pin#*@}"
    # 1) dependencies, with the extra (a no-op once present); 2) the pinned commit itself. pip treats a
    # same-version package as already satisfied, so without --force-reinstall a lock bump between two commits
    # with the same version (e.g. an agentteams RC string, or an older researchteam) would keep the old commit.
    "$VENV/bin/python" -m pip install -q -c "$CONSTRAINTS" "$name$extra @ ${url#* @ }"
    "$VENV/bin/python" -m pip install -q --force-reinstall --no-deps "$url"
  done
fi

"$VENV/bin/python" -c "import cryptography" 2>/dev/null \
  || { echo "bootstrap: cryptography is not importable in $VENV; agentteams[signing] did not install, so every signed-row gate check would fail closed" >&2; exit 1; }

if [[ "${1:-}" == "--local" ]]; then
  "$VENV/bin/python" "$ROOT/scripts/check_toolchain.py" --python "$VENV/bin/python" --no-remote
else
  # The pinned install must now match toolchain.lock exactly; fail loudly if it does not.
  "$VENV/bin/python" "$ROOT/scripts/check_toolchain.py" --python "$VENV/bin/python" --no-remote --strict \
    || { echo "bootstrap: the installed toolchain does not match toolchain.lock (see above)" >&2; exit 1; }
fi
echo "[bootstrap] done. Activate with: source .venv/bin/activate"
