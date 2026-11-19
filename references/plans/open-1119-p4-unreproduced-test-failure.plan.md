# P4: the test failure that did not recur

Written 2026-11-19 by the researchteam agent session, for the agent that takes this over.

## Goal
Either name and fix the test that failed once, or close the item with evidence that it does not recur.

## What is known
- One full local `pytest` run on an early head of PR #214 (the agentteams v1.2.1 pin, 2026-11-19) reported a
  single failure. Its name was not captured.
- Three later full local runs and every CI run since (`tests (3.10)`, `tests (3.13)`) passed.
- The local environment at that time was behind the lock (old agentteams in `.venv`), and the team was being
  regenerated in the same checkout. `.venv` has since been rebuilt and matches `toolchain.lock`.
- 14 of the 37 test files touch the network, the clock, the environment or the home directory.

## Hypotheses, most likely first
1. A test read files that the regeneration was rewriting at that moment (a race with the session's own work).
2. A test depended on the stale local environment (old agentteams) and no longer can.
3. A test depends on the network (a tag lookup or the GitHub API) and met a timeout or a rate limit.
4. A test depends on the date or on an environment variable the agent session sets.

## Steps
1. **Static triage, read-only.** For each of the 14 files, list which tests use the network, the clock, the
   environment or the home directory, and whether each is isolated (monkeypatch, tmp path, skip marker).
   Output: a table with a risk mark per test.
2. **Repeat runs on `main`, isolated, after step 1.**
   - Run from an extract outside the repository (`git archive` of `main`, unpacked in scratch), not from a
     worktree, so the repository's `.git` is not written.
   - Confirm first that the interpreter imports the code under test from the extract, not the installed
     package.
   - Point `HOME` at a scratch directory for the runs, unless step 1 shows a test needs the real release
     signers file; then copy only that public file in.
   - 20 full runs, one at a time, each with `--junitxml` and `-p no:cacheprovider`; then 5 with the test
     files in reverse order. No new dependency (S-10). Do not run while another track is using the GitHub
     API heavily.
3. **Decide.**
   - A failure is captured: a fix PR of its own (isolate the test or fix the code), with `@code-hygiene`,
     and `@security` if a gate or signing test is involved. The operator's live approval for the merge.
   - Nothing fails: harden only a test that step 1 shows writing to the real home directory or reaching the
     real network with no skip marker. If there is none, close as not reproducible.
4. **Record** the runs, the table and the decision in the work summary; delete the scratch files.

## Cut after audit
Re-creating the original conditions (an early head of PR #214, old agentteams, a regeneration running). The
exact head is not known, the old environment is gone, and a wrong directory would regenerate the real team.

## Limits
A fixed budget: step 2 once. If nothing fails, the item closes; it is not retried without new evidence.

## Done when
A fix is merged, or the work summary records the runs and closes the item.
