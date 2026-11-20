#!/bin/bash
# P4 step 2 series: 20 forward runs (10 per interpreter) then 5 with the test files in reverse order (3 + 2).
# One run at a time. The smoke run already made counts as forward run 1 on the CI-like interpreter.
# usage: series.sh <P4_DIR> <python with agentteams importable> <python without agentteams>
P4="$1"; AT="$2"; BREW="$3"
mv "$P4/results/smoke-brew" "$P4/results/fwd-noat-01" 2>/dev/null
sed -i '' 's/^smoke-brew /fwd-noat-01 /' "$P4/results/summary.txt"
for i in 02 03 04 05 06 07 08 09 10; do "$P4/run.sh" "$P4" "fwd-noat-$i" "$BREW" fwd; done
for i in 01 02 03 04 05 06 07 08 09 10; do "$P4/run.sh" "$P4" "fwd-at-$i" "$AT" fwd; done
for i in 01 02 03; do "$P4/run.sh" "$P4" "rev-noat-$i" "$BREW" rev; done
for i in 01 02; do "$P4/run.sh" "$P4" "rev-at-$i" "$AT" rev; done
echo SERIES-DONE >> "$P4/results/summary.txt"
