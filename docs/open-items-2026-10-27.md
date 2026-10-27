# Open items, 2026-10-27

This updates the open items from `docs/open-items-2026-10-19.md` after the 1.1 adoption round. Since then,
Batallion, security and masterTeacher have moved to researchteam v1.1.0-rc.2 and agentteams v1.1.0-rc.7, and the
S-10 cooldown is deprecated (agentteams #299). The evidence was checked on GitHub and against local clones on
2026-10-27.

Owner codes: [OP] the operator, [RT] researchteam, [AT] agentteams, [PO] the owning repository's session.

## Closed since 2026-10-19
- **OI-2026-10-19-03:** baseAgent tagged `v1.0.1`, and its `main` pins researchteam v1.0.2.
- **OI-2026-10-19-10:** the Batallion stash cleanup was already done on 2026-10-19.

## Operator rulings (2026-10-27)
- **Autosync:** disable it on security and masterTeacher. Neither has `AGENTTEAMS_ALLOWED_SIGNERS`, and security's
  10-19 and 10-26 scheduled runs failed at the gate. Each repo is re-enabled later, after one `force=true` dispatch.
- **OI-06:** prepare researchteam 1.0.3 now, with #98 and #102 backported and the agentteams pin left at v1.0.0.
  The agentteams #249 fix goes in a later 1.0.x.
- **Plans:** remove the four orphaned `references/plans/*egyptian-cosmopolitanism*` files in a reviewed PR, with
  `@security` clearance.
- **masterTeacher:** pin moves keep its own convention (no signed rows). Its vulnscan level is `remediate`.
- **OI-04:** pin PRs merge, and the Codex files that aren't narrowed are tracked here.

## Still open

| ID | Item | Owner | State | Next action |
|---|---|---|---|---|
| OI-2026-10-19-01 | Kronos P1 packages need a vulnerability review | [PO] Batallion | Not started | Batallion writes the dossier and spec. The cooldown is deprecated, so the OSV/GHSA search is what decides. The operator signs. |
| OI-2026-10-19-02 | Codex write-policy fence unscoped (agentteams #249) | [AT] | Open, no PR | Fix it on agentteams `main` and backport it to 1.0.x. |
| OI-2026-10-19-04 | Codex agent files not narrowed under orchestrator-only: Batallion `content-enricher`, `team-builder`; security `tool-doc-researcher` | [PO] Batallion, security | Present on both `main`s | Each owning session proposes remove, narrow or adopt, and the operator chooses. |
| OI-2026-10-19-05 | Weekly autosync | [OP] | researchteam, Batallion, mathAgents disabled; baseAgent active and passing; security and masterTeacher active without the signer secret | Disable security and masterTeacher (ruling above). Record the 1.1-line re-enable condition. |
| OI-2026-10-19-06 | #98 and #102 aren't in any 1.0.x release (`release/1.0` = `v1.0.2`) | [RT], then [OP] | Backport PR opened | The operator merges the backport, then signs and tags `v1.0.3`. |
| OI-2026-10-19-07 | Batallion: 29 frozen fences to review | [PO] Batallion | Not re-checked | Batallion runs `researchteam doctor` and releases fences with `AGENTTEAMS_SHRINK_ALLOW`. |
| OI-2026-10-19-08 | Toolchain check not wired to SessionStart | [OP] | Only the example file exists | The operator merges `.claude/settings.toolchain.example.json` into `.claude/settings.json` where wanted. |
| OI-2026-10-19-09 | Kronos P1 reference GAPs; README row for the methodology guide | [PO] Batallion | Pending | `@reference-manager` closes the GAPs and `@agent-updater` adds the row. |
| OI-2026-10-19-11 | `conflict-log.csv` missing | [RT] | Fix in PR | Seed the log with its header row. |
| OI-2026-07-08 P1-2 | Literature-library suite not in CI; no query smoke test | [RT] | Fix in PR | Run the suite in `tests.yml` and add a query smoke test. |
| OI-2026-07-08 P3-12 | Orphaned egyptian-cosmopolitanism plans; doctor shows no library or citation capability | [RT] | Fix in PR | Remove the plans (ruling above); add the capability lines to doctor. |
| Dependency audit F-2, F-4, F-5, F-9 | No pandoc preflight; `create-pull-request` not SHA-pinned; ls-remote fails open on the unlocked path; single-attempt fetch | [RT] | Fix in PR | See the hardening PR. |

Not tracked as an item: agentteams `v1.1.0-rc.8` is tagged, so derived repos (now on rc.7) may move again.
