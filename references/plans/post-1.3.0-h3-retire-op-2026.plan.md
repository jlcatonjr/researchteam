# H3: retire the decision key `op-2026` (2026-11-25; target 2026-12-05)

Metaplan: `post-1.3.0-high-items.metaplan.md`. Earlier steps of the rotation: `key-rotation-resign-2026-11.plan.md`
(the re-signing, done) and the toolchain-group file at sequence 5, signed with `opr-2026-11` (done, 2026-11-23).

**This plan approves nothing.** Removing a verify key revokes every row it signed. That is a trust change: it
needs `@security`'s recorded clearance before it happens (C-5), the operator's own run of the script, and the
operator's live answer for the merge.

## State on `main` (read 2026-11-25)

- Verify-key stores: one under each of the four team folders (`.github`, `.claude`, `.codex`, `.goose`).
- `.github` decisions log: 37 rows. Seven rows are signed with `opr-2026-11`: the six re-signed ids and
  `release-line-agentteams-1.3`. The `.codex` log has its root row re-signed.
- `.agentteams/toolchain-group.json`: sequence 5, key `opr-2026-11`.
- Exception registry: the active entry for `repo-setting:delete-branch-on-merge:jlcatonjr/researchteam` is bound
  by hash to the row signed with `op-2026` (`decision_key_id: op-2026`). A sunset entry for
  `s10-cooldown-exempt:jlcatonjr/agentteams` is also bound to an `op-2026` row.

## Rows still signed only with `op-2026`

| Row | Still looked up? | Proposal |
|---|---|---|
| `s10-release-cooldown-restored` (2026-11-03) | Yes: the 1.3.0 cut scripts require it as a PASS row, and it is in the lineage of the sunset exemption entry | **Operator decision P2.** Session's recommendation: re-sign it. It is the record that Rule S-10's cooldown is in force; letting it lapse leaves that rule resting on a revoked row |
| `fleet-agent-pilot-2026-11` | No (one-week pilot) | Lapses, as ruled on 2026-11-22. Its replacement is H4 |
| `codex-orchestrator-only-native-render` | No | Lapses, as ruled |
| `s10-cooldown-exempt:jlcatonjr/agentteams` | No: consumed, entry sunset | Lapses; phase 1 checks that a sunset entry bound to a revoked row does not fail the registry audit |
| Pin rows, release-key and cooldown rows of the 1.0 and 1.1 lines, `release-line-agentteams-1.1` | History | Lapse. Phase 1 checks that nothing on `main` looks them up |

Phase 1 replaces the "Still looked up?" column with evidence: a search of this repository and of the installed
agentteams 1.3.0 for each action id, and the rehearsal below.

## Phases

**Phase 1, read-only (wave 1).**
1. Close step 7 of the re-sign plan with the evidence that its rows are on `main`.
2. For every `op-2026` row, search for lookups of its action id (scripts, workflows, docs that state a rule,
   agentteams 1.3.0's gates).
3. Rehearse in scratch copies of the four team folders, the group file and the registry, outside the repository,
   with the installed agentteams: remove `op-2026` from the copies' key stores and run every check the repository
   runs: the toolchain-group verification, `--verify-toolchain-pin`, the clearance of each re-signed id and of
   `release-line-agentteams-1.3`, the exception-registry audit, the frozen-key audit, `researchteam doctor`, and the
   read-only refusals of the 1.3.0 cut script. Record what fails. The copies are deleted afterwards. No key is
   read: the stores hold public keys only.
4. Read the `release/1.x` branches' key stores and logs, and say what retiring the key on `main` alone leaves
   there (decision P4).
5. `@security` reviews the findings and says what must be true before the retirement.

**Phase 2, preparation (wave 2).**
6. The operator's decisions P2, P3, P4 in the picker, with phase 1's evidence.
7. If P2 is "re-sign": a decision spec for `s10-release-cooldown-restored` in the pattern of
   `docs/release/key-rotation-2026-11/` (field for field, a note naming the replaced row), and its signing step.
8. The step that registers the branch-deletion exception again against its `opr-2026-11` row, with the same
   expiry and no second entry. The 2026-11-22 plan found that no agentteams gate does this, so it is a script;
   phase 2 first checks whether agentteams 1.3.0 added one and uses it if so.
9. One operator script: sign (if P2), re-register, remove `op-2026` from the four key stores, then run phase 1's
   checks for real and stop on any failure before anything is committed. `@security` reviews it and records the
   clearance for the retirement (C-5). The tracked copy carries placeholders for the signer and the key.

**Phase 3, the retirement (wave 3).**
10. The operator runs the script. The session verifies each check itself, commits the result on a branch and
    opens the pull request. It touches `.github/agents/` and the other team folders, so `@security`'s PASS names
    those paths (PS-2).
11. The operator's live answer; the merge; CI on `main`; a message to the release coordinator (information).
12. `release/1.x` branches as ruled in P4, each by its own pull request or left alone.

## What can go wrong

- **A needed row turns out to verify only with the old key.** Phase 1 exists to find this; the retirement does
  not start until its list is empty or the operator has ruled on each row.
- **The registry entry is left bound to a revoked row,** which would end the branch-deletion exception while the
  repository setting stays on. Step 8 and the audit in step 9 guard this; if it cannot be done cleanly, the
  alternative put to the operator is to turn the setting off and let the exception end.
- **A derived repository or another surface still trusts `op-2026` for this repository's rows.** Out of scope
  here; the coordinator is told before and after.
- **The date.** 2026-12-05 is a target. If H4 or P2 is not settled by then, the operator moves the date; the
  key is not retired with a known gap.

Steps: `post-1.3.0-h3-retire-op-2026.steps.csv`.
