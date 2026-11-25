# H4: the App authorization row (fleet agent, Tier 1) (2026-11-25)

Metaplan: `post-1.3.0-high-items.metaplan.md`. Authority on the row's content: `fleet-agent-tier1-2026-11.plan.md`
on the branch `governance/fleet-agent-tier1` (not yet on `main`). This plan only covers getting that reviewed
work signed and merged; it changes nothing in the row.

**This plan approves nothing.** The signature, the cap change and the merge are the operator's.

## State

- Branch `governance/fleet-agent-tier1`, head `25b77f2`: the decision spec, the plan and the tracked copy of
  operator script 26, all dated 2026-11-24. The script was not run on 2026-11-23 or on 2026-11-24.
- Operator ruling, picker, 2026-11-25: "Regenerate when I ask". **No session work on this branch until then.**
- `main` has moved since: seven more merges, among them a new signed row in the decisions log
  (`release-line-agentteams-1.3`).

## When the operator asks

1. Merge `main` into the branch. The decisions log on the branch must be `main`'s bytes exactly; the
   toolchain-group file (sequence 5) and the exception registry must be `main`'s.
2. Set the spec's two dates and the script's date and spec hash to the signing day the operator names. Nothing
   else in the row changes; the expiry stays 2027-02-18.
3. Checks without signing: the frozen-key audit, the registry at the default cap with one active exception, the
   group verifying at sequence 5.
4. `@security` re-reads the new head and the script (its earlier PASS named an older head).
5. The operator copy of script 26, its hash, and one command; a check-only run first.
6. After the operator's run: the session verifies the row clears, the registry holds two active entries under a
   cap of two that ends on 2027-02-18, and the log is the committed bytes plus one appended row. Commit, pull
   request, `@security` PASS naming `.github/agents/` paths, the operator's live answer, merge.
7. Carried in the steps file: the cap returns to one by an operator script on 2027-02-18 or when either
   exception ends; a pointer to the row goes into the Project-Specific Rules before the App's first write.

## Relation to H3

The 2026-11-22 ruling says the replacement for the pilot row is drafted and reviewed before `op-2026` is retired.
It is drafted and reviewed. Whether it must also be signed first is decision P3 of the metaplan. If H3's
retirement runs first, step 1 here also takes the key stores and the re-registered registry entry from `main`.

## Risk

- **The log-append hazard.** A signed row appended on a stale branch conflicts with rows appended on `main`.
  Step 1 and the "committed bytes plus one row" check in step 6 guard it; the pull request is merged promptly
  after signing, and no other log-changing pull request (H3) is merged between the signature and the merge.
- **A third lapse.** The script is dated for one day. It is generated on the day the operator will run it.

Steps: `post-1.3.0-h4-app-authorization.steps.csv`.
