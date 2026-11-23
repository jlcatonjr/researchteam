# Plan: re-sign the decision rows still needed with opr-2026-11 (2026-11-22)

Second step of the operator's rotation of the Ed25519 decision key `op-2026` to `opr-2026-11`. The new verify
key is on `main` (PR #244). The fleet's release coordinator gave the rotation's rule (data): install the new key
beside the old one, re-sign every row still needed under its same action id with a byte-identical
`derives_from`, and only then retire the old key, because removing it revokes every row it signed.

**This plan approves nothing.** Which rows are re-signed is the operator's choice in the picker; every signature
is the operator's own, at a prompt, in their terminal; the merge needs their live answer naming the PR and head.

## Candidate rows (from `.github/agents/references/security-decisions.log.csv` on `main`, f95f27f)

| Action id | Signed | Derives from | Why it is still needed |
|---|---|---|---|
| `release-policy-1.0` | 2026-10-16 | (root) | root of every other lineage |
| `s10-first-party-releases-2026-11` | 2026-11-13 | (none) | parent of the first-party toolchain group |
| `management-roster-enroll:infrastructure-management` | 2026-11-06 | `release-policy-1.0` | the management roster entry |
| `fleet-agent-pilot-2026-11` | 2026-11-14 | `release-policy-1.0` | to be decided: the row describes a one-week pilot |
| `term-index-2026-11` | 2026-11-16 | `release-policy-1.0` | the term-index scripts |
| `release-line-agentteams-1.2` | 2026-11-19 | `release-policy-1.0` | the current agentteams line |
| `repo-setting:delete-branch-on-merge:jlcatonjr/researchteam` | 2026-11-20 | `release-policy-1.0` | the one active relaxing exception (to 2027-02-18) |

## The list, as ruled (operator, session picker, 2026-11-22)

- **Re-signed (six ids, seven signatures):** every row in the table except `fleet-agent-pilot-2026-11`; and
  `release-policy-1.0` again into the `.codex` log, whose root row has the same signed values.
- **`fleet-agent-pilot-2026-11` lapses.** The pilot it describes was for one week. A new authorization under a
  new id, matching the operator's later ruling on that use, is drafted and reviewed before `op-2026` is retired.
- **`codex-orchestrator-only-native-render` lapses**, in both logs: a clearance for one render of the 1.0 line.
  Nothing in this repository or in agentteams 1.2.1 looks the id up.
- **History, not re-signed:** the pin rows and the release-key and cooldown rows of earlier lines, the 1.1 line
  row, the consumed `s10-cooldown-exempt` row and the three unsigned rows. The `release/1.x` branches carry
  their own logs and key stores; whether those are touched is decided with the retirement, not here.
- **Signing day:** 2026-11-22.

## Specs

`docs/release/key-rotation-2026-11/`. Each copies its row field for field, apart from the date, the key id and
a note appended to `evidence` that names the replaced row by its `text_digest` and the first 16 characters of
its signature. `spec-row-diff.txt` in that folder records the field-by-field comparison.

## Findings that bind the later steps

- **The toolchain-group file is itself signed with `op-2026`.** Re-signing rows is not enough to retire the old
  key: the group's next sequence, signed with the new key, must be adopted first (`@security`).
- **The active exception's registry entry is bound to its exact row by hash** (agentteams 1.2.1,
  `sandbox_relaxation_gate._unbound_reason`). Appending a same-id row changes nothing now: the entry keeps
  carrying over while the old row verifies, no second entry is registered, and the expiry is unchanged. At
  retirement the entry must be registered again against the new row, by a script, because no agentteams gate
  knows this action.

## Rehearsal (2026-11-22)

In scratch copies of both team folders, with a throwaway key standing in for the new one and the signer
(agentteams 1.2.1) run by the session: the six specs sign, the root also into the `.codex` log; each re-signed
id's latest row clears with the old key present and with it removed from the copies; the two lapsing rows
clear only while the old key is present; the re-signed exception row is recorded unconsumed. The copies and
the throwaway key were deleted. Nothing real was signed. The frozen-key audit, run read-only on the worktree,
is clean.

## Steps

1. Specs and this plan, tracked on a draft PR.
2. `@security` reviews the specs and the list (which rows, and the `.codex` log).
3. The coordinator checks the specs (data in, data out).
4. The operator chooses the list in the picker where it is in doubt.
5. The signing script (`references/plans/archive/2026-W47/operator/25-resign-rows-opr-2026-11.sh`), modelled on the
   one another of the operator's repositories used; `@security` reviews it.
6. The operator runs it; the session verifies, commits the appended rows and asks for the merge.

Later, each with its own plan: the new parent row for the member added to the toolchain group and the group's
next sequence; retiring `op-2026` under a recorded clearance, with the render that re-records the exception.

Steps: `key-rotation-resign-2026-11.steps.csv`.
