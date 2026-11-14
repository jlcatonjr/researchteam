#!/bin/bash -p
# run-09-now.sh — researchteam v1.0.1: sign, verify, push and publish the v1.0.1 tag. Every input is filled in:
#   /bin/bash -p ~/githubrepositories/researchteam/tmp/by-week/2026-W43/operator/run-09-now.sh
# It (1) checks 09 is the reviewed script (sha256), (2) checks origin release/1.0 is still the #95 merge commit, then
# (3) runs 09 at that commit with your release key and the rc tags' tagger identity. 09 does all its own checks in a
# fresh clone, verifies the signature before asking y/N, and only then pushes v1.0.1 and publishes the release.
if [[ $- == *p* ]]; then
set -euo pipefail
D=~/githubrepositories/researchteam/tmp/by-week/2026-W43/operator
S09="$D/09-sign-release-1.0.1.sh"
S09_SHA256=370a9152e055979d9a300f911a470809487769874307109c17268addf92efd70
MERGE=b55e2307a95a2db92fe971d867a8453871183e8d      # merge of #95 into release/1.0 (parents a21e7db v1.0.0 + d7483f4)
KEY="<release-key-file>"

got=$(/usr/bin/shasum -a 256 "$S09" | /usr/bin/awk '{print $1}')
[[ "$got" == "$S09_SHA256" ]] || { echo "error: 09 is $got, not the reviewed $S09_SHA256; stop" >&2; exit 1; }
echo "ok: 09 is the reviewed script ($S09_SHA256)"
head=$(GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 /usr/bin/git ls-remote https://github.com/jlcatonjr/researchteam.git refs/heads/release/1.0 | /usr/bin/cut -f1)
[[ "$head" == "$MERGE" ]] || { echo "error: origin release/1.0 is $head, not the #95 merge $MERGE; stop" >&2; exit 1; }
echo "ok: origin release/1.0 is the #95 merge $MERGE"
export TAGGER_NAME="the operator" TAGGER_EMAIL="<noreply>"
exec /bin/bash -p "$S09" "$MERGE" "$KEY"
else
  printf 'STOP: run as /bin/bash -p %s (privileged mode); nothing was done.\n' "$0" >&2
fi
