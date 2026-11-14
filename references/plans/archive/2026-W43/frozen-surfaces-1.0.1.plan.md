# researchteam 1.0.1: frozen surfaces (agentteams shared contract) — plan

**Owner:** researchteam-a7, assigned by James (2026-10-19, in this session and confirmed in researchteam-f6's).
Reviewer and tester: researchteam-f6. Contract: agentteams `tmp/by-week/2026-W42/f3-drafts/design/frozen-surfaces-1.0.x.design.md`,
section "Shared contract with researchteam".

## Behaviour
- **The key.** `brief.json` `frozen_surfaces` is an array of unique ids from {copilot-vscode, copilot-cli, claude, goose,
  agents-md, codex, grok}. An unknown id, a duplicate or a non-array value refuses the run.
- **What a frozen surface means.** researchteam never renders into, merges into, projects into, bridges into,
  Notes-syncs or managed-syncs any path the surface owns:
  - codex: `.codex/`, `.agents/skills/`;
  - goose: `.goose/`;
  - claude: `.claude/agents/`;
  - copilot-*: `.github/agents/`;
  - grok: `.grok/`;
  - root `AGENTS.md` when codex, goose or agents-md is listed.
  `codex` maps onto the existing `--no-codex` path.
- **Belt and braces.** researchteam hashes every frozen path before layer 1 and checks it afterwards. If a frozen
  `AGENTS.md` was written by an unfrozen render (Codex or Goose blocks), researchteam restores the exact earlier bytes.
  Any other change under a frozen path fails the run closed (exit 1, so autosync opens no PR).
- **Unfreeze** (James's ruling). researchteam records the frozen set it last honoured in `.researchteam`. If the brief
  drops a surface, researchteam asks the pinned agentteams' gate, under agentteams' own interpreter, whether an
  `unfreeze-<surface>` row:
  - clears;
  - derives as needing an operator signature (constraint-relaxing, derived and never self-declared);
  - is Ed25519-signed.
  Otherwise it refuses, including when agentteams is too old to say.
- **doctor and the gate.** `doctor` reports the frozen set, the recorded set and any pending unfreeze. The autosync gate
  inherits all of this through `update`.

## Steps
1. `researchteam/_frozen.py`, then wire it into update, materialize, bridges, Notes, managed files and doctor.
2. Tests, including mathAgents-shaped (goose + codex, Goose-owned AGENTS.md) and baseAgent-shaped (codex) consumers.
3. @security and @code-hygiene review; a PR to main; review by researchteam-f6.
4. The 1.0.1 release: a cherry-pick -x of this fix, #84, #85 and #92 (docs and tests) onto release/1.0; CHANGELOG
   `## 1.0.1`; signing scripts for James; merge-forward.
