#!/bin/bash
# P4 step 2 runner: one isolated full pytest run from a `git archive` extract of main.
# usage: run.sh <P4_DIR> <label> <python> <fwd|rev>
set -u
P4="$1"; LABEL="$2"; PY="$3"; ORDER="$4"
EX="$P4/extract"; OUT="$P4/results/$LABEL"; mkdir -p "$OUT"
cd "$EX" || exit 9
for v in RT_ROOT TERM_INDEX_ADVISORY AUTOSYNC_PR_BODY_FILE RT_TEST_AGENTTEAMS_PYTHON RESEARCHTEAM_ALLOW_UNVERIFIED_AGENTTEAMS \
         http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY GITHUB_TOKEN GH_TOKEN; do unset "$v"; done
export HOME="$P4/home" PYTHONPATH="$EX" PYTHONDONTWRITEBYTECODE=1
if [ "$ORDER" = rev ]; then FILES=$(ls tests/test_*.py | sort -r); else FILES=tests; fi
"$PY" -c "import sys,researchteam,importlib.util as u; s=u.find_spec('agentteams'); print('python',sys.executable,sys.version.split()[0]); print('researchteam',researchteam.__file__); print('agentteams',s.origin if s else None)" > "$OUT/imports.txt" 2>&1
START=$(date +%s)
"$PY" -m pytest -q -p no:cacheprovider --basetemp="$P4/tmp/$LABEL" --junitxml="$OUT/junit.xml" $FILES > "$OUT/stdout.txt" 2>&1
RC=$?
echo "$LABEL rc=$RC secs=$(( $(date +%s) - START )) $(tail -1 "$OUT/stdout.txt")" | tee -a "$P4/results/summary.txt"
rm -rf "$P4/tmp/$LABEL"
exit $RC
