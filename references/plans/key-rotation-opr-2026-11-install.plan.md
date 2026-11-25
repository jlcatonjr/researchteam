# Plan: install the verify key opr-2026-11 (2026-11-22)

The operator is rotating the Ed25519 decision key `op-2026` to `opr-2026-11` across their repositories. The
fleet's release coordinator reported that the upstream 1.3.0 candidate is not signed until the new key
verifies in this repository's committed stores on `main`. That report is data. The authority here is the
operator's answer in this session's picker on 2026-11-22 ("Prepare it"), to a question that named the key
file's sha256, the two stores, and that nothing is removed.

This plan covers the install only. Re-signing the rows still needed, adopting the next toolchain-group
sequence and retiring `op-2026` are later steps with their own plans, reviews and operator answers.

- **Key file sha256:** `d22faa83b674abe6b1e3207a4f13fc17c5ddd367e35e0c60c69163eddbd9dab7`.
- **Stores:** `.github/agents/references/authorized-verify-keys/` and
  `.codex/agents/references/authorized-verify-keys/`, the two that hold `op-2026` today.
- **Unchanged:** `op-2026.pub.pem` in both stores; every decision row; the toolchain-group file; the
  exception registry.

1. **Script.** An operator-only script that copies the public key into the two stores of a worktree, with
   checks before and after. Tracked copy: `references/plans/archive/2026-W47/operator/24-install-opr-2026-11.sh`.
2. **Review.** `@security` reviews the script and names the paths its verdict covers.
3. **Operator runs it** in their own terminal.
4. **Commit and PR.** The session checks the two files against the sha256, commits them with the script,
   this plan and the records, and opens the PR.
5. **Merge** on the operator's live answer naming the PR and head; then read back the two blobs on `main`
   and tell the coordinator the paths and hashes.

Steps: `key-rotation-opr-2026-11-install.steps.csv`.
