# Open Items: researchteam v1.0.2 and Batallion (2026-10-19)

The next entry in the historic open-items list after [`open-items-2026-07-08.md`](open-items-2026-07-08.md). It
records what is **still incomplete** at the close of the researchteam-51 session, which:
- synced Batallion to the v1.0.0 release and then to v1.0.2;
- fixed the upstream findings that sync surfaced;
- cut researchteam v1.0.2;
- finished Batallion's Kronos vendoring.

Every status was checked live on 2026-10-19. Ownership tags follow the 2026-07-08 list: **[RT]** researchteam
maintainer · **[PO]** project owner · **[AT]** upstream agentteams · **[OP]** operator decision or operator-only
action.

## Done this session, for context
- **researchteam:**
  - #100: bootstrap installs `agentteams[signing]` under the S-10 pins.
  - #101: `CLAUDE.md` managed-block accuracy.
  - #103: `scripts/validate.d/` hook, v1.1 line.
  - #107: docs.
  - **v1.0.2** tagged: object `5e5aeca5…`, peeled `10a36758…`, merged forward in #108, announced.
  - The stale `chore/agentteams-autosync` branch was deleted after `@security` cleared it. Restore SHA
    `86ec0ea4df1fa3275274ace6c324cc276dea8cea`.
- **Batallion:**
  - #11 and #12: v1.0.0 sync, Codex and Grok teams.
  - #18: pin v1.0.2, with a signed row.
  - #21: Kronos inference core, with the signed row `vendor-kronos-inference-core`.
  - #22: Kronos loader CI guard.
  - #23: tracks the 50 agentteams team files that its `*.json`/`*.csv` data rules hid.
- **agentteams:** #249 filed.

## Open items: one report each
| ID | Item | Owner | Status | Report |
|---|---|---|---|---|
| OI-2026-10-19-01 | Kronos P1 data and competitor packages (`yfinance`, `akshare`, `statsforecast`, Chronos runtime) need an S-10 review before P1 step 5 | [PO] Batallion | Not started; blocks P1 step 5 and steps 7–14 | [01](open-items/2026-10-19/01-kronos-p1-data-package-s10.md) |
| OI-2026-10-19-02 | The Codex render's `codex_write_policy` fence in the shared `AGENTS.md` is unscoped, so Grok reads it | [AT] agentteams | Filed as #249; no owner yet | [02](open-items/2026-10-19/02-agentteams-249-codex-fence-scope.md) |
| OI-2026-10-19-03 | baseAgent's move to researchteam v1.0.2 isn't finished | [PO] baseAgent | Pinned on `release/1.0` (#166); `v1.0.1` not tagged; `main` still v1.0.0. **2026-10-20:** `v1.0.1` tagged; `main` pins v1.0.2; #167/#163 still open | [03](open-items/2026-10-19/03-baseagent-v1.0.2-pin.md) |
| OI-2026-10-19-04 | Batallion has two Codex agent files outside the native render (`content-enricher`, `team-builder`) that aren't restricted under orchestrator-only | [PO] Batallion | Not started; needs an operator choice | [04](open-items/2026-10-19/04-batallion-codex-unnarrowed-agents.md) |
| OI-2026-10-19-05 | Turning the weekly autosync back on (operator ruling); mathAgents' schedule was active on a v1.0.0 pin, and failing | [OP] | Decision pending. The mathAgents schedule was disabled 2026-10-19 by the operator. **2026-10-20:** baseAgent's autosync is active again (dispatch succeeded; #173 merged) | [05](open-items/2026-10-19/05-autosync-resume.md) |

## Smaller carry-overs (no separate report)
- **OI-2026-10-19-06 [RT]:** researchteam **#98** (frozen Goose owns `.goosehints` and its scripts) and **#102**
  (pinned-fingerprint trust root) are on `main`. Per Jim's ruling, they ship in the patch after 1.0.2, alongside
  agentteams 1.0.x, which should also carry the #249 fix.
- **OI-2026-10-19-07 [PO]:** Batallion `doctor` lists **29 frozen fences to review** (the shrink guard kept them).
  It prints the release command for each one: `AGENTTEAMS_SHRINK_ALLOW=<file>:<fence>@<hash>`.
- **OI-2026-10-19-08 [OP]:** in Batallion, as elsewhere, the toolchain check isn't wired to SessionStart. Merge
  `.claude/settings.toolchain.example.json` into `.claude/settings.json`; this is an operator step.
- **OI-2026-10-19-09 [PO]:** Kronos P1 still has open `@reference-manager` GAPs (steps CSV row 6), and the
  provisional `financial-forecast-evaluation` methodology guide still needs its README index row, through
  `@agent-updater`, because that README is fenced.
- ✅ **OI-2026-10-19-10 [OP], resolved 2026-10-19:** the duplicate stash (`0b2befe9`) had already been dropped by another session. The operator's `stash drop stash@{0}` then removed the older "rc8 churn pre-branch (kept)" stash (`051d0b02`) by position. researchteam-51 restored it with `git stash store` the same hour. Lesson: name a stash by its commit, not its position. Originally: Batallion `stash@{0}` ("duplicate v1.0.2 pin move") holds only copies of files now
  committed in #20. Drop it with `git -C ~/githubrepositories/Batallion stash drop stash@{0}`.
- **OI-2026-10-19-11 [RT]:** `@conflict-auditor` asks for findings to be logged in
  `.github/agents/references/conflict-log.csv`, which doesn't exist in researchteam. Create it, or change the
  agent's instruction.

## Notes for whoever picks these up
- **Signing in a worktree:** since Batallion #23, fresh worktrees include the agentteams team files, so copying
  them in is no longer needed. The signing scripts still refuse anything but the reviewed head and a clean tree.
- **Stashing near another session's work:** `git stash -u` in a checkout that another session is writing in
  will sweep up that session's untracked work. That happened once today, and the files were restored. Use a
  separate worktree instead.
