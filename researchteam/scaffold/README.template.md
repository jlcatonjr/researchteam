# {{PROJECT_NAME}}

{{PROJECT_GOAL}}

## Deliverables

{{DELIVERABLES}}

- **Output format:** {{OUTPUT_FORMAT}}
- **Primary output directory:** `{{PRIMARY_OUTPUT_DIR}}`

## Repository layout

| Path | Purpose |
|---|---|
| `{{PRIMARY_OUTPUT_DIR}}` | Primary deliverables authored by this project |
| `Projects/` | Working project deliverables (active) |
| `references/` | Bibliography, registries, and shared references |
| `.github/agents/` | Agent team infrastructure (generated from `brief.json`) |
| `.claude/` | Claude bridge templates and checklists |
| `docs/` | Project + framework documentation |
| `tmp/by-week/` | Weekly plan and step artifacts |

## Working with the agent team

- **Claude users:** start from [`CLAUDE.md`](CLAUDE.md).
- **Copilot / agentteams users:** start from [`.github/copilot-instructions.md`](.github/copilot-instructions.md).

The agent team is generated from [`brief.json`](brief.json). Edit `brief.json` to describe this
project, then regenerate the team (see below). Do not hand-edit files under `.github/agents/**` —
they are generated and the next sync discards manual edits.

## Keeping the team in sync with the brief

This repository was scaffolded with the **researchteam** framework and receives infrastructure
updates without touching your research content.

- `researchteam update` — sync framework files from upstream and merge agent infrastructure.
- `researchteam materialize` — **re-render** the agent team from `brief.json` after you change
  the project's identity or domain (a plain `update` deliberately preserves enriched bodies and
  will not re-brand them).
- `researchteam personalize` — regenerate this `README.md` and `CLAUDE.md`'s project header from
  `brief.json`.

Full command reference, installation, the two-layer update model, and CI details live in
[`docs/researchteam-framework.md`](docs/researchteam-framework.md).

`brief.json`, `Projects/`, and `references/` are user-owned and are never overwritten by an
update.
