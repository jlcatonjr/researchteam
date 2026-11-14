# researchteam v1.0.0 Phase R — operator scripts

> **rc.12 verified (2026-10-16): the hold is lifted.** agentteams `v1.0.0-rc.12`: tag object `8bc1cd17`,
> peeled `69fe9447`. #49 and #52 are re-pointed. Already done: 00, 03, and the merges of #50, #51, #54, #55,
> #56, #57, #58, #60 and #62.
>
> **Order now:** `01` → `02` → *tell the researchteam session* (it renders on rc.12 and opens the render PR)
> → `04` → `05`.

Run these yourself, in order, in a plain terminal. They refuse to run inside an agent session. Each one
stops at a y/N prompt before anything irreversible or outward-facing. They're local only: `tmp/` is
gitignored.

| # | Script | What it does | Needs |
|---|---|---|---|
| 00 | `00-discard-rc8-regen.sh` | Backs up the stale rc8 re-render in the main checkout to `~/researchteam-backups/`, then discards it. HEAD stays at 15b968b. | (optional, independent) |
| 01 | `01-install-trusted-signer.sh` | Clones and verifies agentteams `v1.0.0-rc.10`, then pipx-installs the signer into `~/.local/share/agentteams-signer` under the S-10 constraints. | `allowed_signers`, pipx |
| 02 | `02-decision-signing.sh` | Provisions the `op-2026` verify key, migrates the log, signs 6 decision rows, and opens the signing PR. | 01; `<decision-key-file>` |
| 03 | `03-ci-allowed-signers-secret.sh [repo…]` | Sets the `AGENTTEAMS_ALLOWED_SIGNERS` secret. To include mathAgents, pass both repos: `jlcatonjr/researchteam jlcatonjr/mathAgents`. | gh auth |
| 04 | `04-merge-prs.sh` | Merges the signing PR, #56, #49, #52 and the rc.11 render PR, then rebuilds #53 (1.0.0rc1) and merges it. Every merge is pinned to its head SHA. | 02 + render PR |
| 05 | `05-cut-and-sign-rc1.sh` | Cuts `release/1.0`, signs, verifies and pushes `v1.0.0-rc.1`, and prints the tag object and peeled SHA. | 04; `<release-key-file>` |

After 00, 02, 04 and 05, tell the researchteam session. It updates the plan and notifies agentteams and mathAgents.
If a step stops with an error, nothing after it has run, and re-running is safe: done steps are skipped
or refused, never repeated.
