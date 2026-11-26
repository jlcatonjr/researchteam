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

## `@security` on phase 1 (2026-11-25): CONDITIONAL PASS

Cleared: the operator's decisions and the drafting of script one. Not cleared: running script one, or any key
removal. Conditions, binding on phases 2 and 3:

- **C1, clearance before script one.** Action `exception-rebind:repo-setting:delete-branch-on-merge:jlcatonjr/researchteam`.
  It names the base `main` commit, the script's tracked path and hash, the old entry and its row hash, and the new
  binding (key `opr-2026-11`, the 2026-11-22 row, expiry 2027-02-18). No new signed row is needed: the re-signed
  row is the same operator decision. The expiry stays 2027-02-18, which is what was signed.
- **Script one** calls only the registry functions of the agentteams the lock pins, never edits the JSON by
  hand, and is run by the operator. Before it writes: both keys present; the registry's hash is the one the
  clearance names; exactly one active entry for the action; the 2026-11-22 row is the newest of its id and
  verifies; no unretracted HALT on `branch-delete`, the `repo-setting` family or the action. After it writes:
  exactly one active entry, bound to the new row, same expiry and lineage; the old entry retired with a reason
  naming the new id, not deleted; the sunset entry and the group sequence byte-identical; the count of active
  relaxing exceptions unchanged; the decisions log byte-identical; only the registry file changed; the binding
  check passes, also in a scratch copy with the old key removed; the exception audit, the integrity check, the
  frozen-key audit and the group verification pass.
- **The sunset entry is left unchanged.** It is inert history; that its row is revoked at removal is recorded
  here and nowhere in the registry.
- **C2, clearance before script two.** Action `key-retire:op-2026`. It names phase 2's merge commit with green
  CI, both key files with their hashes, script two's hash, the rows the removal revokes, and the operator's
  answers P2, P3 and P4. The deletion also has the operator's confirmation in the picker (S-4).
- **Tests that must pass before C2,** none of which the phase 1 rehearsal ran: a regeneration
  (`agentteams --update --merge`) in a scratch copy with the key removed neither restores the key nor touches the
  two key stores or the registry (a regeneration that restored it would make the autosync's trust-root gate
  refuse every sync); the runtime hooks with the key removed; the binding check on the committed registry; the
  test checks on the pull request head.
- **C3.** If the key is retired before H4 is signed, the App has no authorization in this repository from the
  removal until H4's row; the operator confirms the App is idle or suspended. H4's row is a new id under the new
  key, never a re-sign of the pilot.
- **C4.** The autosync is paused by the operator for both windows (script one also writes under
  `.github/agents/references/`), and open autosync pull requests are closed before each run. No H4 signature in
  either window.
- **C5.** The old private key is the operator's: kept offline while the older release lines may still need a
  patch, never used for a `main` row again. The session never touches it.
- **C6.** The release coordinator is told before and after, as information.
- **P2, `@security`'s view:** both cooldown rows lapse. The cooldown rests on Rule S-10's text and the first-party
  carve-out on the signed group file, so a new decision would add nothing. Two conditions: `docs/release-policy.md`
  marks the rows it cites as history, and step 16 (the cut script no longer matching a revoked row as text) is
  blocking for the next cut.
- **P4, `@security`'s view:** leave `release/1.0` to `1.2` alone. A pull request that brings `op-2026` back onto
  `main` (a forward-port from those lines, for example) is a HALT.
- The generated memory indexes mention `op-2026` until they are next rebuilt through the normal path.

## Operator's decisions (picker, 2026-11-25)

- **P2: "Let both lapse".** The two cooldown rows are not signed again. `docs/release-policy.md` marks them as
  history (step 11a), and the next cut script stops matching the old row as text (step 16, blocking for that cut).
- **P3: "Retire the key first".** The retirement does not wait for H4. From the removal until H4's row is signed
  the App has no authorization in this repository; the operator confirms it is idle or suspended before script
  two runs (condition C3).
- **P4: "Leave them alone".** `release/1.0`, `1.1` and `1.2` keep trusting `op-2026`. Nothing is opened against
  them.

## Phase 2, script one (2026-11-25)

- Tracked copy: `references/plans/archive/2026-W48/operator/31-rebind-branch-delete-exception.sh`, on the branch
  `chore/rebind-branch-delete-exception` (head `73b4206`, one commit on `main` `f97e9d3`).
- It signs nothing and needs no private key. It retires the entry bound to the `op-2026` row with a reason and
  registers the same exception against the 2026-11-22 row, through agentteams' registry functions, and restores
  the registry if any check fails.
- The new entry's `issued` is the time of the run: agentteams refuses an entry issued before its row was signed,
  and the old entry was issued on 2026-11-21, a day before the re-signed row.
- Rehearsed in a scratch export of `main` with agentteams 1.3.0: the check passes; the change retires
  `…@c4c40701ad95ad92` and registers `…@dc79fe00692848c4` (key `opr-2026-11`, expiry unchanged); the binding
  verifies, also in a copy with `op-2026` removed; the decisions log is byte-identical; a second run refuses.
- `@security` reviewed it for the clearance of condition C1 (next section).

## Clearance for script one (`@security`, 2026-11-25): CONDITIONAL PASS, conditions operational

Recorded here and on the branch's pull request before hand-over, as `@security` ruled for this step (it is not
destructive, the file is tracked, and no gate looks the clearance up; an unsigned log row would not count while
decision signing is active).

- Action: `exception-rebind:repo-setting:delete-branch-on-merge:jlcatonjr/researchteam`.
- Base `main` commit `f97e9d39661702c0cb9011df71bd9873209063d1`; reviewed head
  `0341dd4d6e15c9b2286c48e49bd708cd9afad340` of `chore/rebind-branch-delete-exception`.
- Script `references/plans/archive/2026-W48/operator/31-rebind-branch-delete-exception.sh`, sha256
  `f3633962676553f8d26ea2f28edad03d03e98d8fa603ca14c24da75c13aa114d`. The operator's copy differs in the one
  line that names the root-owned install; the session checks that by diff.
- Old entry `…@c4c40701ad95ad92`, binding `3a11d65b797a84bd50a7ca75154d7b43b658d0029ea00c0ee7a0ea1f5f64e78a`.
- New binding: key `opr-2026-11`, `decision_sha256`
  `9e98e66d76d394d3086046fdcae23be07970cc6e8cb8234c4c4216e2313d7154`, expiry `2027-02-18T23:59:59+00:00`.
- Registry sha256 before: `06d670bb49849be76ddbdfee0378944a1fcc48e2689ec162759e65321e7412bc`.
- Still to hold at the run: the autosync paused and no autosync pull request open; no App-authorization
  signature in the window; afterwards the session runs the integrity check, the frozen-key audit, the exception
  audit and the binding check on the result and posts the outputs on the pull request; on any failure the
  registry is restored from git and nothing is committed; the merge needs `@security`'s PASS naming
  `.github/agents/`.
- The first review (head `73b4206`) required three fixes, all made: the HALT scan is agentteams' own, in every
  team log; the agentteams version must be exactly 1.3.0; the registry's hash is checked again just before the
  change and interrupts are ignored until the checks after it have run. One small gap is accepted: if `git
  status` itself fails after the change, the script stops without restoring; `git checkout` of the file recovers.
- **How the removal's clearance will be recorded (C2):** a row the operator signs with `opr-2026-11`, committed
  before script two runs and checked by it; the picker confirmation of the deletion as well.

## Finding: the root-owned install is older than the lock (2026-11-25)

- The operator's root-owned agentteams install reports 1.2.1. Script 31 needs 1.3.0, the version `toolchain.lock`
  pins: tried in a scratch copy against 1.2.1, the binding check fails (its arguments differ), so the version
  check is doing its job.
- The 1.3.0 cut scripts (29, 30) ran their pin verification and clearance check with that 1.2.1 install. Both
  passed and nothing suggests a wrong result, but it means the release was checked by the previous agentteams,
  not the one it pins. Recorded here; the next cut script names the version it expects.
- Operator ruling (picker, 2026-11-25): **"Build a root-owned 1.3.0".** A second root-owned install, built from
  the signed tag `v1.3.0`, beside the existing one, which is not touched. Where it is installed is not recorded
  (PS-1).

## Script 32 drafted here, then withdrawn (2026-11-25)

- The session first drafted its own build script (script 32, branch `chore/root-owned-agentteams-1.3.0`).
  `@security` refused it three times and it was rewritten each time; it was never handed to the operator.
- While it was under review the session told `@security` and the operator that the install in use had been built
  by an older script of this repository. That was wrong, and what was concluded from it is withdrawn. Read from the
  install itself: it is root-owned throughout and was built on 2026-11-21 by the managing repository's own reviewed
  procedure.
- Building the trusted install is the managing repository's procedure, with its own review, so script 32 was
  withdrawn. The branch stays as the record of the draft and its reviews. The operator's ruling stands and was
  carried out by asking the managing repository's session, which the operator named in the picker, for a 1.3.0
  build by that procedure.
- Script 31 needs agentteams 1.3.0 and waited for that install. Scripts 29 and 30 ran their checks with the 1.2.1
  install; that fact stands as recorded.
- Order for the operator: script 28 `pause`; then script 31.
- **Lesson for the session:** a claim about how something outside this repository was built is checked against
  the thing itself before it is given to a reviewer or to the operator.

## The root-owned agentteams 1.3.0 install exists (2026-11-25)

- The managing repository's session built it by its own reviewed procedure (its script and clearance are in that
  repository's records) and the operator ran it. Where it is installed is not recorded here (PS-1).
- Checked by this session, read-only: the install is root-owned throughout, it reports the agentteams version
  `toolchain.lock` pins (1.3.0), and it has what script 31 uses.
- The operator's copy of script 31 now names it. It differs from the tracked copy (sha256 `f3633962…`) in that
  one line only, checked by diff.
- Rehearsed with that interpreter, under an empty environment, in a scratch export of the reviewed head
  `0341dd4`: the check passes and the change gives the expected entry (`…@dc79fe00692848c4`, key `opr-2026-11`,
  expiry unchanged), with the binding verifying also without the old key.
- At hand-over: the worktree is clean at `0341dd4`; the registry there has the hash the clearance names; no
  autosync pull request is open; the autosync is enabled and is paused by the operator first (condition C4).

## Phase 2 done (2026-11-26)

- The operator paused the autosync, then ran script 31 with agentteams 1.3.0. Its checks before and after passed.
  It retired `…@c4c40701ad95ad92` and registered `…@dc79fe00692848c4` (key `opr-2026-11`, expiry
  `2027-02-18T23:59:59+00:00`). Nothing was signed. Registry sha256 after the run:
  `0e7044b4a8ec152d033e144fe528c9504b85283f98934049cb43cf07038d921b`.
- The session checked the result read-only with the pinned agentteams: the file's hash; a diff of 21 added lines
  in that one file; the new entry's binding equal to the `opr-2026-11` row's; the binding check passing now and in
  a copy without the old key; no HALT on `branch-delete`, the `repo-setting` family or the action; the exception
  audit clean; the decisions log unchanged. The outputs are on pull request #275.
- `@security` PASS at `e900602`, naming `.github/agents/references/exception-registry.json`. Merged as `8e827f9`
  after the operator's answer "Merge #275 at e900602"; the merge's tree equals that head; CI on `main` green.
- The autosync is still paused. Phase 3 needs it paused from script two's run to its merge (C4); whether it is
  resumed in between is the operator's choice.
- `docs/release-policy.md` now marks the two cooldown rows it cites as history (P2; part of step 11a).
- Next: the remaining tests of step 11a in a scratch copy without the key, then the clearance for the removal
  (C2), script two, and the operator's run.
