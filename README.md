# ResearchTeam

Conduct rigorous, source-grounded scholarly research with agent-based workflows and robust update safety.

## What is ResearchTeam?

ResearchTeam is a pip-installable framework for producing well-structured research reports with verified citations, using agent-based workflows. All claims are grounded in peer-reviewed or reputable scholarly sources, with Chicago-style citations. Once installed, a derived project can receive infrastructure updates automatically — without touching user research content.

## Installation

```bash
pip install git+https://github.com/jlcatonjr/researchteam.git
```

## Quick Start

### New project (recommended)

```bash
researchteam init my-research-project
cd my-research-project
```

`init` scaffolds a complete project directory, runs `git init`, and makes an initial commit. Edit `brief.json` to describe your project before running any agents.

### Existing clone

```bash
git clone https://github.com/jlcatonjr/researchteam.git my-research-project
cd my-research-project
```

Then follow the onboarding steps in `CLAUDE.md` or `.github/copilot-instructions.md`.

## CLI Reference

| Command | Description |
|---|---|
| `researchteam init [name]` | Scaffold a new project from the upstream template |
| `researchteam update` | Sync layer-2 files from upstream, then run agentteams update |
| `researchteam update --layer2-only` | Sync layer-2 files only; skip agentteams |
| `researchteam update --dry-run` | Preview changes without writing files |
| `researchteam update --yes` | Apply all changes without interactive prompts (for CI) |
| `researchteam status` | Show marker info and CLI version |
| `researchteam --version` | Print CLI version |

### `init` options

```
researchteam init [name] [--ref REF] [--remote URL]
```

- `name` — directory to create (defaults to current directory if empty)
- `--ref` — upstream git ref to scaffold from (default: `main`)
- `--remote` — git remote URL to set as `origin` after init

### `update` options

```
researchteam update [--yes] [--dry-run] [--layer2-only] [--ref REF]
```

- `--yes / -y` — skip interactive confirmation; required in CI
- `--dry-run` — show what would change without writing files
- `--layer2-only` — only sync layer-2 files; skip `agentteams --update --merge`
- `--ref` — override the upstream ref (default: value in `.researchteam` marker)

## Update Architecture

ResearchTeam infrastructure is split into two independently updatable layers:

| Layer | What it covers | Update mechanism |
|---|---|---|
| **Layer-1** (agentteams-managed) | `.github/agents/`, `copilot-instructions.md` | `agentteams --update --merge` |
| **Layer-2** (researchteam-managed) | `CLAUDE.md`, `docs/`, `scripts/`, `.claude/`, `README.md` | `researchteam update --layer2-only` |

**User-owned files** (`brief.json`, `Projects/`, `references/`) are never touched by either update layer.

`researchteam update` (without `--layer2-only`) runs both layers in sequence.

### Derived-repo CI

Projects created with `researchteam init` receive a `.github/workflows/agentteams-sync.yml` that runs both layers automatically on a weekly schedule and on `workflow_dispatch`. The CI:

1. Installs the `researchteam` CLI and runs `researchteam update --layer2-only --yes`
2. Installs the `agentteams` CLI and runs `agentteams --update --merge --yes`
3. Validates changed paths and fence integrity
4. Optionally opens a PR with the combined diff (manual runs with `open_pr=true`)

## Directory Structure

| Path | Purpose |
|---|---|
| `Projects/` | Primary research deliverables (active) |
| `reports/` | Optional deliverables path (create if needed) |
| `references/` | Registry, plans, and shared references |
| `tmp/by-week/` | Weekly plan and steps artifacts |
| `.github/agents/` | Agent infrastructure and governance |
| `.github/agents/references/` | Shared reference data for agents |
| `.claude/` | Claude-specific templates and checklists |
| `scripts/` | Helper scripts (bridge, validation) |
| `docs/` | Policy and bridge documentation |
| `researchteam/` | Installable CLI package (upstream repo only) |

## Agent Workflows and Orchestrator

### Orchestrator Agent
The orchestrator agent is the entry point for all agent-based workflows. It coordinates requests, enforces constitutional rules, and ensures every multi-file session closes with a consistency check. **Do not bypass the orchestrator or invoke agents directly, except for the Team Builder bootstrap flow.**

### Agent Roles
- **Orchestrator:** Coordinates all agent operations and workflow routing.
- **Domain Agents:** Specialized for research, writing, validation, reference management, and more. See `.github/copilot-instructions.md` for the full agent team list and roles.
- **Note on topology:** `.github/agents/references/pipeline-graph.md` is auto-generated from `build_team.py`. Agents declared in `copilot-instructions.md` but not yet wired into `build_team.py` (e.g., `@work-summarizer`, `@git-operations`) will not appear in the graph until the build system is updated.
- **Claude vs. Copilot/agentteams:**
  - *Claude users* use the bridge in `CLAUDE.md` and `.claude/README.md`.
  - *Copilot/agentteams users* follow `.github/copilot-instructions.md` and use `.github/agents/`.

### Fenced Regions
Fenced regions are blocks managed by agents. **Do not edit inside fenced regions manually.** User-authored content outside these regions is preserved during updates.

## Onboarding and Safety Checklist

1. **Install:** `pip install git+https://github.com/jlcatonjr/researchteam.git`
2. **Initialize:** `researchteam init my-project` (or clone directly)
3. **Edit `brief.json`** with your project name and goal.
4. **Choose your workflow:** Claude (`CLAUDE.md`) or Copilot/agentteams (`.github/copilot-instructions.md`).
5. **Run validation:** `bash scripts/validate_agentteams_update.sh` before and after infrastructure updates.
6. **Keep infrastructure current:** run `researchteam update` periodically or let the CI workflow handle it.
7. **Backup your work:** keep copies of `Projects/` and `brief.json` outside the repo.
8. **Never edit inside fenced regions or agent files manually.**

## Updating Infrastructure

```bash
# Interactive (shows diff for each changed file)
researchteam update

# Non-interactive (for scripts/CI)
researchteam update --yes

# Preview only
researchteam update --dry-run
```

See `docs/agentteams-update-policy.md` and `scripts/validate_agentteams_update.sh` for update safety rules.

## Key Docs

- `CLAUDE.md` — Claude user bridge and workflow
- `.claude/README.md` — Claude templates/checklists
- `.github/copilot-instructions.md` — Copilot/agent governance
- `.github/agents/references/pipeline-graph.md` — Agent team topology (auto-generated)
- `docs/agentteams-update-policy.md` — Update/merge policy
- `docs/agent-infrastructure-authority.md` — Path authority map

## FAQ

- **Is this a pip package?**
  - Yes. `pip install git+https://github.com/jlcatonjr/researchteam.git` gives you the `researchteam` CLI for `init` and `update`.
- **Will `researchteam update` overwrite my research?**
  - No. `brief.json`, `Projects/`, and `references/` are user-owned and never touched. Only layer-2 infrastructure files (docs, scripts, `.claude/`) are synced.
- **What are fenced regions?**
  - Agent-managed blocks delimited by `AGENTTEAMS:BEGIN/END` comments. Do not edit inside them.
- **Where do I start?**
  - `pip install git+https://github.com/jlcatonjr/researchteam.git`, then `researchteam init my-project`.
- **What if something goes wrong?**
  - Review logs and validation output, restore from backup if needed, and see `docs/agent-infrastructure-authority.md` for recovery steps.

---

For more, see the `docs/` folder and in-repo help scripts.
