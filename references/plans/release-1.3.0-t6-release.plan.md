# T6: release researchteam 1.3.0 (version 3, 2026-11-20, revised after two audit passes)

Target of `release-1.3.0.metaplan.md`. Covers F14, the candidate and the final. The procedure, the freeze
criteria, the cut scripts' refusals and the operator decisions are in the metaplan, section 4; this file lists
the work.

1. **Freeze review** against the criteria, after the operator's answers to D10 and D11.
2. **Release-prep PR** (after the freeze; it is the candidate's gate, not the freeze's; the lead writes the
   changelog part):
   - `CHANGELOG.md`: a 1.3.0 section, with an upgrade part (install the new researchteam first, then
     `researchteam update`; what agentteams 1.3.0 changes for a derived repository; the term-index core
     directory; the workflow scaffold), and the entry owed after PR #234 if it has merged;
   - `docs/release/release-notes-v1.3.0.md`;
   - `docs/release-policy.md`: "researchteam 1.3 pins agentteams 1.3", `release/1.3`, `release/1.2` stays open;
   - install instructions name the new release everywhere PR #156 found the old tag;
   - the tracked, scrubbed copy of the cut script.
   `@security` (it names `docs/release-policy.md` and the script) and `@conflict-auditor`.
3. **PR #156:** closed as superseded once step 2 has merged and the operator has agreed (D9).
4. **Candidate cut script** on the 1.2.1 model, plus: it creates `release/1.3` at the named commit; the
   previous release is the newest 1.2.N tag, pinned by tag object and required as an ancestor; and the refusals
   of the metaplan's section 4 step 4, the network comparison of the copied core included. `@security` reviews
   it before hand-over. The coordinator may review it as data; that review is not an approval.
5. **Operator runs it.** Read back the tag object, the peel, the branch and GitHub's verification. Check that
   `main` contains the tagged commit.
6. **Downstream dry-run pin**, reported by the coordinator. A defect: a fix PR on `main`; the next cut script
   fast-forwards `release/1.3` to that commit after the operator's live answer naming it, and signs the next
   candidate.
7. **Final cut script** (same refusals; the candidate plus fixes and release files only; it marks the release
   Latest), after the operator's go. Read-back; check that `main` contains the tagged commit, or merge forward
   by PR with the operator's live answer.
8. **Tell the coordinator** the tag object and peeled commit, and the install-first order.
9. **Afterwards:** soak and rehearsal branches go to `archive/`; work summary (`@work-summarizer`); then
   `@conflict-auditor`.

Between the candidate and the final, `main` takes only fixes for defects the candidate showed, release files
and records, each by PR with the operator's live answer.
