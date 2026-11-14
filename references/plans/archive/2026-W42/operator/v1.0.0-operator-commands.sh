#!/bin/sh
# researchteam v1.0.0 — the operator commands, in order. Run each line yourself in a plain Terminal (not an agent
# session), only when the researchteam session says that step is ready. This file only lists them; it runs nothing.
echo "Read the steps in this file; run each command yourself when the researchteam session says it is ready."
exit 0

# 0. Check the two scripts are the reviewed ones (sha256 from the researchteam session, @security CLEAR):
shasum -a 256 ~/githubrepositories/researchteam/tmp/by-week/2026-W42/operator/07-sign-pin-row-v1.sh \
              ~/githubrepositories/researchteam/tmp/by-week/2026-W42/operator/08-sign-release.sh

# 1. Sign the @security pin row into the release-prep worktree at the reviewed head (commits nothing):
/bin/bash -p ~/githubrepositories/researchteam/tmp/by-week/2026-W42/operator/07-sign-pin-row-v1.sh e915f49ead931d8c3151de113d6babfe6ef2fff0

# 2. (session) commits the row, CI goes green, you approve the merge of #89; the session reports the merge commit.

# 3. Sign, verify, push and publish v1.0.0 at that merge commit (replace <MERGE_SHA> with the 40-hex the session gives):
TAGGER_NAME="James Caton" TAGGER_EMAIL=jamescaton@users.noreply.github.com /bin/bash -p ~/githubrepositories/researchteam/tmp/by-week/2026-W42/operator/08-sign-release.sh <MERGE_SHA> "<release-key-file>"
