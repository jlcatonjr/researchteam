# H3: retire the decision key `op-2026` (2026-11-25; target 2026-12-05)

Metaplan: `post-1.3.0-high-items.metaplan.md`. Earlier steps of the rotation: `key-rotation-resign-2026-11.plan.md`
(the re-signing, done) and the toolchain-group file at sequence 5, signed with `opr-2026-11` (done, 2026-11-23).

**This plan approves nothing.** Removing a verify key revokes every row it signed. That is a trust change: it
needs `@security`'s recorded clearance before it happens (C-5), the operator's own run of the script, and the
operator's live answer for the merge.

## State on `main` (read 2026-11-25)

- Verify-key stores: `op-2026` is in two of them, under `.github/agents/` and `.codex/agents/`. The `.claude` and
  `.goose` stores hold no key. The backup folders under `.github/agents/` are checked in phase 1 and the result
  recorded.
- `.github` decisions log: 37 rows; 27 signed with `op-2026`, 7 with `opr-2026-11` (the six re-signed ids and
  `release-line-agentteams-1.3`), 3 unsigned. The `.codex` log has three rows: its root row signed with each key,
  and `codex-orchestrator-only-native-render` with `op-2026`.
- `.agentteams/toolchain-group.json`: sequence 5, key `opr-2026-11`.
- Exception registry: the active entry for `repo-setting:delete-branch-on-merge:jlcatonjr/researchteam` is bound
  by hash to the row signed with `op-2026`. A sunset entry for `s10-cooldown-exempt:jlcatonjr/agentteams` is also
  bound to an `op-2026` row, and its recorded lineage names `s10-release-cooldown-restored`.

## Rows still signed only with `op-2026`

| Row | Still looked up? | Proposal |
|---|---|---|
| `s10-release-cooldown-restored` (2026-11-03) and `s10-release-cooldown-deprecated` (2026-10-26), which is in its `derives_from` | Only as text: the 1.3.0 cut scripts search the log for a PASS line with the first id, which still matches after the key is gone. No active registry entry has either in its lineage | **Operator decision P2.** Session's recommendation, reversed by the audit: both lapse, as the 2026-11-22 ruling already placed "the cooldown rows of earlier lines" in history. The first cannot be re-signed field for field, because its lineage would point at a revoked row. If the operator wants the cooldown's record under the new key, that is a new decision with its own id and lineage, not a re-sign. Either way the next cut script stops requiring the old id, or checks signatures |
| `fleet-agent-pilot-2026-11` | No (one-week pilot) | Lapses, as ruled on 2026-11-22. Its replacement is H4 |
| `codex-orchestrator-only-native-render`, in both logs | No | Lapses, as ruled |
| `s10-cooldown-exempt:jlcatonjr/agentteams` | No: consumed, entry sunset | Lapses; phase 1 checks that a sunset entry bound to a revoked row does not fail the registry audit |
| Pin rows, release-key and cooldown rows of the 1.0 and 1.1 lines, `release-line-agentteams-1.1` | History | Lapse. Phase 1 checks that nothing on `main` looks them up |

Phase 1 replaces the "Still looked up?" column with evidence: a search of this repository and of the installed
agentteams 1.3.0 for each action id, and the rehearsal below.

## Phases

**Phase 1, read-only on everything that carries trust (starts with wave 1).** Its only tracked writes are plan
records.
1. Close step 7 of the re-sign plan with the evidence that its rows are on `main`.
2. For every `op-2026` row, in both logs, search for lookups of its action id (scripts, workflows, documents
   that state a rule, agentteams 1.3.0's gates).
3. Rehearse in scratch copies, outside the repository, of the team folders, the group file and the registry,
   with the agentteams the lock pins (after H1): remove `op-2026` from the copies' two key stores and run every
   check the repository runs: the toolchain-group verification, `--verify-toolchain-pin`, the clearance of each
   re-signed id and of `release-line-agentteams-1.3`, the exception-registry audit, the frozen-key audit,
   `researchteam doctor`, and the read-only refusals of the 1.3.0 cut script. Record what fails. The copies are
   deleted afterwards. No private key is involved: the stores hold public keys only.
4. Read the `release/1.x` branches' key stores and logs, and say what retiring the key on `main` alone leaves
   there (decision P4).
5. `@security` reviews the findings and says what must be true before each of the two later steps.

**Phase 2, the registry entry moves to the new row (first pull request).** Verifiable while the old key is
still present, so a failure here costs nothing.
6. The operator's decisions P2, P3 and P4 in the picker, with phase 1's evidence.
7. The step that registers the branch-deletion exception again against its `opr-2026-11` row: same expiry, no
   second entry, keyed on that action id so that any other entry (H4's, if it is there) and the cap are left as
   they are. The 2026-11-22 plan found that no agentteams gate does this; phase 2 first checks whether agentteams
   1.3.0 added one and uses it if so, and otherwise it is a script. If P2 asked for a new cooldown decision, its
   spec and signature are part of this step.
8. `@security` reviews operator script one and records a clearance for the re-registration before it runs: the
   entry it replaces is a trust record. The script does the step above, then the registry audit and the
   clearance checks, stopping on any failure before anything is committed. The tracked copy carries placeholders for the
   signer and the key.
9. The operator runs it; the session verifies, commits on a branch, opens the pull request; `@security`'s PASS
   names the paths (PS-2); the operator's live answer; the merge; CI on `main`.

**Phase 3, the key is removed (second pull request).** Only after phase 2's merge is green on `main`.
10. `@security` records the clearance for the removal before it happens (C-5), naming the `main` commit it
    applies to and the two files removed.
11. Operator script two: remove `op-2026` from the two key stores, then run phase 1's checks for real, stopping
    on any failure and restoring the two files if one fails. The autosync is paused by the operator from this run
    until the merge, so that no automated pull request is built on a half-changed trust state.
12. The session verifies each check itself, commits, opens the pull request; `@security`'s PASS names the paths;
    the operator's live answer; the merge; CI on `main`; a message to the release coordinator (information).
13. `release/1.x` branches as ruled in P4: left alone, or the removal recorded as a change to carry in the next
    tagged release on that line. No pull request is opened against a `release/*` branch for it.
14. Recorded, not done by the session: what the operator does with the old private key. The plan states only
    that the session never reads, moves or deletes it.

## What can go wrong

- **A needed row turns out to verify only with the old key.** Phase 1 exists to find this; the retirement does
  not start until its list is empty or the operator has ruled on each row.
- **The registry entry is left bound to a revoked row,** which would end the branch-deletion exception while the
  repository setting stays on. Phase 2 moves the entry first and proves it while the old key still verifies; if
  it cannot be done cleanly, the alternative put to the operator is to turn the setting off and let the exception
  end (decision P5).
- **H3 and H4 both change the registry and the log.** One of them at a time: no H4 signature between an H3
  script run and its merge, and the other way round. The H4 plan states the same rule.
- **A derived repository or another surface still trusts `op-2026` for this repository's rows.** Out of scope
  here; the coordinator is told before and after.
- **The date.** 2026-12-05 is a target. If P2 or P3 is not answered by then, the operator moves the date. P3 may
  be answered "retire before H4 is signed"; what is not done is retiring with a question unanswered.

Steps: `post-1.3.0-h3-retire-op-2026.steps.csv`.

## Phase 1 record (2026-11-25; read-only, rehearsed in a scratch copy of `main` at `61c1962`, deleted afterwards)

**Step 1.** The seven re-signed rows reached `main` through pull request #245 (merge `1933260`); the 1.3 line row
through #254 (merge `c92fc56`). Step 7 of the re-sign plan is closed.

**Step 2, lookups.** No `op-2026` row's action id is looked up by code in this repository or in agentteams 1.3.0.
- agentteams takes the newest row of an id when it checks a clearance, and an ancestor in `derives_from` only has
  to exist as a row; ancestors are not signature-checked. So no row that must keep clearing depends on an
  `op-2026` signature: the newest rows of the seven re-signed ids, of `release-line-agentteams-1.3` and of the
  toolchain group's parent all carry `opr-2026-11`.
- `s10-release-cooldown-restored` is matched as text only, by the 1.3.0 cut scripts; the match still succeeds
  with the key gone. `s10-release-cooldown-deprecated` appears in documents and history only.
- The pin rows, the release-key exemption rows, `release-line-agentteams-1.1`, `fleet-agent-pilot-2026-11` and
  `codex-orchestrator-only-native-render` appear in documents and archived operator scripts only.

**Step 3, rehearsal.** `op-2026` removed from the two stores that hold it (`.github`, `.codex`); the `.claude` and
`.goose` stores hold no key; the backup folders are ignored by git and hold no key file.

| Check | With the key | Key removed |
|---|---|---|
| `--verify-toolchain-pin`, `--verify-toolchain-group` | exit 0 (sequence 5) | exit 0 |
| Clearance of the seven re-signed ids, `release-line-agentteams-1.3`, the `.codex` root row | clear | clear |
| Clearance of every id signed only with `op-2026` | clear, apart from two refused for other reasons | refused: no verify key |
| `--audit-exceptions`, `--verify-integrity`, the frozen-key audit | exit 0 | exit 0 |
| `researchteam doctor`, `validate` | exit 0 | exit 0 |
| Key and log tests (four files) | 109 passed, 1 skipped | the same |
| Registry binding, checked directly | both entries bound | **both entries bound to a row that no longer verifies** |

**The finding that matters.** Removing the key ends the binding of the active branch-deletion entry, and no
check the repository runs reports it: `--audit-exceptions` looks at lapse and the cap, not at the binding, and
still prints "healthy". The re-registration of phase 2 is therefore required, and its success is checked with the
binding check directly, not with the audit.

**What the re-registration writes.** agentteams 1.3.0 has no command for it and no gate for the `repo-setting`
kind. A script calls its registry functions: the entry's `decision_key_id` becomes `opr-2026-11`, its
`decision_sha256` the hash of the 2026-11-22 row, and its `id` changes with the signature, so the old entry is
retired in the same step or there would be two. Tried in memory with the key removed: the re-bound entry passes
the binding check.

**Step 4, release branches.** `release/1.0`, `1.1` and `1.2` hold only `op-2026`: every signed row there, and on
1.1 and 1.2 the group file (sequence 1), depend on it. The key cannot be removed there without breaking them.
`release/1.3` equals `main`'s state at the tag and holds both keys.

**Questions phase 1 adds for the operator and `@security`.**
- The sunset entry (`s10-cooldown-exempt:jlcatonjr/agentteams`) also becomes unbound, silently. Leave it, or note
  in the entry that its row is revoked?
- The re-bound entry's expiry: the entry says 2027-02-18; the re-signed row's own 90 days would run to
  2027-02-20. The plan keeps 2027-02-18, the earlier date.
- Whether agentteams' audit should check bindings is a request for agentteams, sent as information.
