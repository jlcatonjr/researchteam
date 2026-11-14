# Earlier sessions' hidden material (2026-11-14)

Follow-up to `docs/hidden-work-remediation-2026-11-14.md` and rule PS-1. The operator decided the four
categories in this session on 2026-11-14:

| Category | Count | Operator decision |
|---|---|---|
| A. researchteam plans and notes in ignored `tmp/by-week/` (W21-W46) | 57 | Scrub and publish to `references/plans/archive/<week>/` |
| B. Operator scripts (`tmp/by-week/<week>/operator/`, W42-W46) | 52 | Scrub and publish to `references/plans/archive/<week>/operator/` as records |
| C. Notes about other repositories (orthodoxllm, hayek-machines, healthresearch, fleet, handoffs, notices) | 27 | Move, scrubbed, to infrastructureManagement (global rule: notes about another repository live there) |
| D. Regenerable tool output (shrink reports, rt4 logs and script, hygiene list) and the 6 older stashes | 13 + 6 | Delete after `@security` / `@cleanup` clearance, recording hashes and stash SHAs |

The scrub replaces the home-directory path with `~` and every signer install path with `<signer>`. The
originals in `tmp/` stay until the published copies are merged. Every published file is scanned
(`python -m agentteams.scan`), and any high finding left is checked by hand.

Not covered by these decisions, so left for the operator:
- `tmp/by-week/2026-W42/security-seed-answer.data.md`, AI-generated text the operator pasted;
- `tmp/frozen-fences.state.json`, live tool state that stays where it is;
- the research plans and drafts already tracked under `tmp/`. They are public now and have been since the
  first commit. Some cover medical topics.

Also fixed here: the stale "PRs #160 and #161 are open" line in `workSummaries/daily/2026-11-14.md`.

Branches: `docs/hidden-material-2026-11-14` in researchteam, and a worktree branch in infrastructureManagement
(its main checkout is in use by infrastructuremanagement-40 and is left alone).
