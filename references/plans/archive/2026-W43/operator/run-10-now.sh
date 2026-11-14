#!/bin/bash -p
# run-10-now.sh — researchteam v1.0.2: sign, verify, push and publish the v1.0.2 tag. Every input is filled in:
#   /bin/bash -p ~/githubrepositories/researchteam/tmp/by-week/2026-W43/operator/run-10-now.sh
# It (1) checks 10 is the reviewed script (sha256), (2) checks origin release/1.0 is still the #104 merge commit, then
# (3) runs 10 at that commit with your release key and the rc tags' tagger identity. 10 does all its own checks in a
# fresh clone, verifies the signature before asking y/N, and only then pushes v1.0.2 and publishes the release.
if [[ $- == *p* ]]; then
set -euo pipefail
D=~/githubrepositories/researchteam/tmp/by-week/2026-W43/operator
S10="$D/10-sign-release-1.0.2.sh"
S10_SHA256=1384cbd7251db6736c3a50a99717bbbe129963c26665c1cbe29198da3c495aca
MERGE=10a36758d7fcbb3ccc4c8a8cf1e822c375591f7e      # merge of #104 into release/1.0 (parents b55e230 v1.0.1 + 3b19d55)
KEY="<release-key-file>"

got=$(/usr/bin/shasum -a 256 "$S10" | /usr/bin/awk '{print $1}')
[[ "$got" == "$S10_SHA256" ]] || { echo "error: 10 is $got, not the reviewed $S10_SHA256; stop" >&2; exit 1; }
echo "ok: 10 is the reviewed script ($S10_SHA256)"
head=$(GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 /usr/bin/git ls-remote https://github.com/jlcatonjr/researchteam.git refs/heads/release/1.0 | /usr/bin/cut -f1)
[[ "$head" == "$MERGE" ]] || { echo "error: origin release/1.0 is $head, not the #104 merge $MERGE; stop" >&2; exit 1; }
echo "ok: origin release/1.0 is the #104 merge $MERGE"
export TAGGER_NAME="the operator" TAGGER_EMAIL="<noreply>"
exec /bin/bash -p "$S10" "$MERGE" "$KEY"
else
  printf 'STOP: run as /bin/bash -p %s (privileged mode); nothing was done.\n' "$0" >&2
fi
