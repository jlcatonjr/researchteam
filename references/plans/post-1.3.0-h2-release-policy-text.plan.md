# H2: `docs/release-policy.md`, the line-move lock step and the autosync section (2026-11-25)

Metaplan: `post-1.3.0-high-items.metaplan.md`. Source: two advisory findings of `@conflict-auditor` on pull
request #261 (2026-11-24), carried forward at the 1.3.0 close-out.

**Problem.**
1. The policy tells a derived repository to move to a new line with `--write-lock --tag researchteam=<tag>
   --tag agentteams=<tag>` and does not say that a locked repository must first drop both `.tag=` lines from
   `toolchain.lock`. `scripts/check_toolchain.py` refuses a cross-line `--tag` under an existing lock. The 1.2.0
   and 1.3.0 changelog sections say so; the policy, which is what a downstream team reads for a move, does not.
2. "Autosync and Layer 2" still says the schedule stays disabled until researchteam v1.0.1 is tagged. The
   workflow is active; it is paused only while a release is cut (done for 1.3.0 with an operator script).
3. The policy does not say that the lock writer needs the new agentteams installed, nor that a workspace with
   signed rows needs agentteams' `signing` extra. Both were confirmed by the downstream dry runs of 2026-11-24.

**Change.** Text only, in `docs/release-policy.md`:
- one "Moving a derived repository to a new line" passage under "Versions and branches" that the 1.1, 1.2 and 1.3
  line sections point to, with the order: verify both tags; install both at the tags' commits (with the `signing`
  extra where rows or a group file are signed); `researchteam update --ref <tag>`; drop both `.tag=` lines;
  `--write-lock` with both tags; the repository's own `@security` review of two line moves;
- the autosync section rewritten to the present procedure (active; paused by the operator for a cut; resumed
  after the final tag), keeping the release-lock sentence.
The 1.0-era statements that are history are moved into a dated sentence, not deleted without trace.

**Not changed.** No rule changes. `docs/release-policy.md` is not a synced file and not a PS-2 path; the section
"Operator-only and delegated actions" is not touched.

**Checks.** Each new sentence is traced to code or to a record: `scripts/check_toolchain.py` (the refusals),
`scripts/bootstrap_toolchain.sh` (the extra), the 1.3.0 changelog section, the workflow file. `@technical-validator`
checks those traces; `@conflict-auditor` compares the result with `CHANGELOG.md`, `docs/CONTRIBUTING.md` and
`docs/agentteams-update-policy.md`. Full test suite and `validate`.

Steps: `post-1.3.0-h2-release-policy-text.steps.csv`.
