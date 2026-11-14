#!/bin/bash -p
# run-08-now.sh — researchteam v1.0.0, step 3: sign, verify, push and publish the v1.0.0 tag. Every input is filled in:
#   /bin/bash -p ~/githubrepositories/researchteam/tmp/by-week/2026-W42/operator/run-08-now.sh
# It (1) checks 08 is the reviewed script (sha256), (2) checks origin release/1.0 is still the #89 merge commit, then
# (3) runs 08 at that commit with your release key and the rc tags' tagger identity. 08 does all its own checks in a
# fresh clone, verifies the signature before asking y/N, and only then pushes v1.0.0 and publishes the release.
if [[ $- == *p* ]]; then
set -euo pipefail
D=~/githubrepositories/researchteam/tmp/by-week/2026-W42/operator
S08="$D/08-sign-release.sh"
S08_SHA256=cc2a71fa1605fd8440611ae3c6aae1e5a8251d9f2e9757830b1180a8d375c6c3
MERGE=a21e7db7d632664253d4796444ee8b57069c05b2      # merge of #89 into release/1.0 (parents 3358b6c rc.3 + 5a71513)
KEY="<release-key-file>"

got=$(/usr/bin/shasum -a 256 "$S08" | /usr/bin/awk '{print $1}')
[[ "$got" == "$S08_SHA256" ]] || { echo "error: 08 is $got, not the reviewed $S08_SHA256; stop" >&2; exit 1; }
echo "ok: 08 is the reviewed script ($S08_SHA256)"
head=$(GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 /usr/bin/git ls-remote https://github.com/jlcatonjr/researchteam.git refs/heads/release/1.0 | /usr/bin/cut -f1)
[[ "$head" == "$MERGE" ]] || { echo "error: origin release/1.0 is $head, not the #89 merge $MERGE; stop" >&2; exit 1; }
echo "ok: origin release/1.0 is the #89 merge $MERGE"
export TAGGER_NAME="the operator" TAGGER_EMAIL="<noreply>"
exec /bin/bash -p "$S08" "$MERGE" "$KEY"
else
  printf 'STOP: run as /bin/bash -p %s (privileged mode); nothing was done.\n' "$0" >&2
fi
