# Release prep: researchteam v1.1.4 (2026-11-13)

Operator approval: given in this session, 2026-11-13. The operator confirmed R12 (start v1.1.4) and R9 (one
fleet-wide S-10 toolchain group of agentteams, researchteam, baseAgent and mathAgents; researchteam lists the other
three; no sunset). Both were
relayed by IM (infrastructuremanagement-40, infrastructuremanagement-4d), which has no directive authority
of its own (C-4). The target was later changed, also relayed by IM-40: v1.1.4 pins **agentteams v1.1.3**
(not yet tagged), not v1.1.2. Tagging, the `release/1.1` fast-forward, merges and every signature belong to
the operator.

Base: `origin/release/1.1` = `origin/main` = v1.1.3 = `e8b8b471`. Branch: `release-prep/v1.1.4`. The superseded
local WIP from `fix/autosync-cooldown-safe-installs` was put in `git stash` (it duplicates #152/#155). On 2026-11-14 it
was pushed as branch `archive/fix-autosync-cooldown-safe-installs-wip` (`7a4e7888`) and the stash was dropped.

## Phase A (now): needs nothing from agentteams v1.1.3

1. **S-10 re-vet** of the nine third-party packages in `constraints-2026-10-16.txt`. Sources: the PyPI JSON
   API and the OSV API, queried 2026-11-13. Rule: the latest stable release that is at least 14 days old and
   has no OSV advisory. Output: `docs/release/s10-dependency-vetting-2026-11-13.md` and
   `docs/release/constraints-2026-11-13.txt`. The old files are kept, because signed rows cite them.
2. **Mirror** the new set into the gate's `AGENTTEAMS_DEPS`, bootstrap's `SIGNING_CONSTRAINTS`, and the two
   equality tests in `tests/test_toolchain.py`.
3. **Install check**: `--only-binary --no-deps` install of the new set plus `pip check` in a scratch venv.
4. **`scripts/check_toolchain.py`** docstring example: `agentteams.tag=v1.0.0` becomes a current value.
5. **`docs/release-policy.md:52`**: reword so group releases (T2) need the repo's own `@security` review
   and a verified tag, with no operator-signed row per release.
6. Tests: `pytest`, then the bridge `validate`.

## Phase B (after agentteams v1.1.3 is tagged and the group file is signed)

7. Verify the v1.1.3 tag (signature against release key `SHA256:IPdnLwlF…`, peel), then do the OSV search for
   agentteams 1.1.3 and any dependency it changes.
8. Move the pin together in `toolchain.lock` (`agentteams=`, `agentteams.tag=v1.1.3`) and in both pyproject
   extras. Write `docs/release/pin-agentteams-v1.1.3.decision-spec.json` (T2: `@security` review, no
   per-release operator row).
9. Gate wiring, as finally built (5dfe822, dbf7297, c3863d8): `agentteams --verify-toolchain-pin toolchain.lock
   --allowed-signers <file> --output .github/agents --description brief.json` on every integrating run, after a
   trust-root guard. Exit map: 0 means exempt; 2 fails upstream and passes derived with a warning and ordinary
   S-10; 1 and anything else fail. See "Review findings" below. `--description` is needed: v1.1.3 exits 1 without
   it.
10. Commit the operator-signed `.agentteams/toolchain-group.json` in the same change as step 9.
11. Regenerate (Rule 11 / self-contained group section arrives from the template); CHANGELOG 1.1.4.

## Review findings and agentteams answers (2026-11-13)

agentteams-2d's answers, relayed by IM-40 against v1.1.3 head `1b24eda5` (untagged), are data for `@security`:
- v1.1.3 pins `cryptography==50.0.2` in `[signing]`, so the Phase A set stands.
- Exit 2 means "no group file, no exemption claimed", never "verified". Exit 1 means a present file failed,
  or a group pin is bad or untagged.
- The group file's verify key loads from `.github/agents/references/authorized-verify-keys/<key_id>.pub.pem`.
- The check is read-only.
- Every group-member pin other than this repo's own needs a `NAME.tag` line.

Gate as revised (second `@security` pass: PASS-WITH-NOTES; N1-N4 fixed in the commit that follows 5dfe822):
- runs on every integrating run;
- exit 0 passes;
- exit 2 fails in upstream mode and passes in derived mode, with a `::warning::` and a PR notice that ordinary
  S-10 applies at review;
- exit 1 and any other code fail;
- an exit 0 for an untagged agentteams pin is refused;
- a lock-less derived repo claims no exemption;
- the trust-root guard refuses a moved HEAD, changes to the group file, keys or decision log (untracked and
  ignored ones included), and skip-worktree or assume-unchanged entries, and fails closed on a git error.

The guard's limit is recorded in the gate comment: it stops accidents, not a hostile candidate, because the check
runs the candidate's code. On release-locked runs, the signed-tag check is the trust anchor.

Still open:
- the `security-decisions.log.csv` row (operator's call);
- keeping the release-policy reword out of any merge until step 10;
- a tag-age (cooldown) check in the gate as a later follow-up, not in v1.1.4.

## Dropped
- "Define Rule 15": replaced upstream by a self-contained group section (agentteams template).
- "Reconcile two pip re-check dates": came unverified from SocialScienceHumanities; no such conflict here.

## Outcome (2026-11-14)

- Done: steps 1-14. The operator built a root-owned signing install from the verified v1.1.3 tag and signed the root row and the group
  file (0b94783). The pin moved (7578ff4); the re-render and CHANGELOG are in 1f3da2a, and the audit fixes follow it.
- Final `@security`: PASS-WITH-NOTES, cleared for push and PR, not for tag or merge. Its notes are fixed: the
  committed group sha256 matches the signed a38d0484…; the pin-spec wording; the CHANGELOG "1.1.2 introduced".
- `@conflict-auditor`: 7 items. Fixed: 1-4, 6 and 7. Item 5 (the `security.agent.md` "local-repository
  carve-outs" wording) is template text, passed to agentteams.
- Open, operator's choice: sign the pin-agentteams-v1.1.3 row (not required under T2); the `@security`
  verdict rows (the log's rows are operator-signed).

## Release (2026-11-14)

- On the operator's instruction, PR #159 was merged with a merge commit, `5fd8ec3b374f77e0d574cfffe4f5907eaed03ee3`. Its
  parents are `e8b8b471` and `912f9dbd`, the reviewed head, and its tree, `7f4d9f60`, is the same as `912f9dbd`'s.
  `release/1.1` was fast-forwarded to it.
- The operator signed and pushed tag `v1.1.4`, using the SSH release key; git's default GPG signer failed first. The tag object is
  `e789cd17f89e25744375ecdd6b7527023b5b26ee`, and it peels to `5fd8ec3b`. The signature is Good for
  `SHA256:IPdnLwlF…qxnzTNM`, checked with both `git verify-tag` and `check_toolchain.py --verify-tag`.
  infrastructuremanagement-4d verified it independently and made it the fleet target.
- Gap: `docs/release-policy.md` requires a `@security` row for every pin move. The log has no
  `pin-agentteams-v1.1.3` row. Its spec, `docs/release/pin-agentteams-v1.1.3.decision-spec.json`, is ready
  for the operator to sign.

## Close
`@security` review of the diff, `@conflict-auditor`, PR (no tag), PR link to infrastructuremanagement-4d, and
the tag object plus peeled SHA when the operator cuts it.
