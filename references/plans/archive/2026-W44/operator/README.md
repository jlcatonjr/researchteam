# researchteam v1.1.0-rc.3 (pins agentteams v1.1.0-rc.11): operator scripts

Run these yourself in a plain Terminal (not an agent session). Local only; `tmp/` is gitignored.
Folder: `~/githubrepositories/researchteam/tmp/by-week/2026-W44/operator/`

| # | Run | When | Needs |
|---|---|---|---|
| 15 | `/bin/bash -p ~/githubrepositories/researchteam/tmp/by-week/2026-W44/operator/15-sign-pin-rc11.sh <reviewed head of release-prep/1.1.0rc3>` | the release-prep PR is reviewed | root-owned signer, `decision-signing-op-2026.pem` |
| 16 | `bash ~/githubrepositories/researchteam/tmp/by-week/2026-W44/operator/16-cut-rc3.sh <reviewed main SHA>` | after you merge the release-prep PR | `<release-key-file>` (release key) |

Order:
1. **15** re-verifies agentteams `v1.1.0-rc.11` (tag object `242add53…`, peeled `19ba0943…`) and the lock lines, then signs
   `pin-agentteams-v1.1.0-rc.11` into the `researchteam-wt-rc3` worktree. It commits nothing.
2. The researchteam session commits the signed row on `release-prep/1.1.0rc3` and pushes. You merge the PR.
3. **16** with the merged main SHA: it checks the lock, extras, signed rows and `## 1.1.0rc3` at that commit, fast-forwards
   `release/1.1`, signs and verifies `v1.1.0-rc.3`, pushes it and offers the GitHub pre-release. It prints the tag object
   and the peeled SHA.
4. The researchteam session relays both to vulnscan-98 for the derived dry run (`--researchteam-tag v1.1.0-rc.3`).
