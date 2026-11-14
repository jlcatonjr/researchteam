#!/bin/bash -p
# run-07-now.sh — researchteam v1.0.0, step 1: sign the @security pin row. Every input is filled in; just run it:
#   /bin/bash -p ~/githubrepositories/researchteam/tmp/by-week/2026-W42/operator/run-07-now.sh
# It (1) checks 07 is the reviewed script (sha256), (2) checks PR #89's head on GitHub is still the reviewed commit,
# then (3) runs 07 at that commit. 07 shows the spec, asks y/N, signs, checks the gate, and commits nothing.
if [[ $- == *p* ]]; then
set -euo pipefail
D=~/githubrepositories/researchteam/tmp/by-week/2026-W42/operator
S07="$D/07-sign-pin-row-v1.sh"
S07_SHA256=faa2c7b7bbe5ecad1951d394c03904f8fc0d8d798eef594f5fee281e31f6d4fb
HEAD_REVIEWED=e915f49ead931d8c3151de113d6babfe6ef2fff0
PR=89
GH=""; for c in /opt/homebrew/bin/gh /usr/local/bin/gh; do [[ -x "$c" ]] && { GH="$c"; break; }; done
[[ -n "$GH" ]] || { echo "error: gh not found" >&2; exit 1; }

got=$(/usr/bin/shasum -a 256 "$S07" | /usr/bin/awk '{print $1}')
[[ "$got" == "$S07_SHA256" ]] || { echo "error: 07 is $got, not the reviewed $S07_SHA256; stop" >&2; exit 1; }
echo "ok: 07 is the reviewed script ($S07_SHA256)"
head=$(/usr/bin/env -u GH_TOKEN -u GITHUB_TOKEN "$GH" pr view "$PR" -R github.com/jlcatonjr/researchteam --json headRefOid --jq .headRefOid)
[[ "$head" == "$HEAD_REVIEWED" ]] || { echo "error: #$PR head is $head, not the reviewed $HEAD_REVIEWED; stop" >&2; exit 1; }
echo "ok: #$PR head is the reviewed $HEAD_REVIEWED"
exec /bin/bash -p "$S07" "$HEAD_REVIEWED"
else
  printf 'STOP: run as /bin/bash -p %s (privileged mode); nothing was done.\n' "$0" >&2
fi
