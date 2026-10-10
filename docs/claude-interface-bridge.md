# Claude Interface Bridge

This document explains how Claude users can operate the ResearchTeam repository consistently.

## Bridge Components

1. Root guidance: `CLAUDE.md`
2. Command bridge: `scripts/claude_researchteam_bridge.sh`
3. Claude support folder: `.claude/`
4. Existing validator: `scripts/validate_agentteams_update.sh`
5. Authority map: `docs/agent-infrastructure-authority.md`

## Prerequisites

- Bash shell
- Local clone of this repository
- Optional: git initialized and authenticated for push workflows

## Usage

From repository root:

```bash
bash scripts/claude_researchteam_bridge.sh help
```

### Status

```bash
bash scripts/claude_researchteam_bridge.sh status
```

Shows branch, short HEAD hash, and concise working-tree status.

### Validation

```bash
bash scripts/claude_researchteam_bridge.sh validate
```

Runs `scripts/validate_agentteams_update.sh` for ordinary edits, with `VALIDATION_SKIP_SCOPE=1`:
fence and placeholder checks run, but the update-run scope allowlist is skipped, because derived
repos legitimately change files outside it. After an update run, call
`bash scripts/validate_agentteams_update.sh` directly so that the scope allowlist is enforced.

The checks cover tracked changes (staged or not) and new untracked files that `.gitignore` doesn't
exclude. So `validate` also runs the fence and placeholder checks on a new, uncommitted markdown file.
The validator is a drift check: it catches an update that writes outside its scope. It is not a
control against a compromised upstream.

### Reader and Summary Paths

```bash
bash scripts/claude_researchteam_bridge.sh open-reader
bash scripts/claude_researchteam_bridge.sh open-summary
bash scripts/claude_researchteam_bridge.sh open-claude-dir
```

### Claude Support Folder

The `.claude/` folder contains:

- `README.md` with usage notes
- `prompts/research-report.prompt.md` starter prompt template
- `checklists/research-task-preflight.md` checklist for multi-step work

### Weekly Plan Directory

```bash
bash scripts/claude_researchteam_bridge.sh plan-path
```

Returns the current `tmp/by-week/YYYY-Www/` path.

## Recommended Claude Workflow

1. Run `status`.
2. For multi-step tasks, create plan artifacts in current weekly directory.
3. Perform edits.
4. Run `validate`.
5. Commit/push if requested.

## Notes

- Active source-of-truth agent files are in `.github/agents/`.
- `.codex/agents/*.toml` (OpenAI Codex) and `.goose/recipes/` (Goose) are generated projections of that team; regenerate rather than edit. See `.codex/README.md`.
- Backup snapshots in `.github/agents/.agentteams-backups/` are archival.
- Do not manually edit AGENTTEAMS fenced sections in agent docs; use orchestrated update workflows.
- Back up research and agent files before update or merge operations.
- Project-specific reader and summary HTML files are located inside each project directory under `Projects/`.
- Keep `CLAUDE.md` as the top-level entry point and `.claude/` as structured support content.
- Root `CLAUDE.md` and `.claude/README.md` are researchteam-owned: researchteam writes them, and
  `researchteam update` syncs `.claude/README.md` to derived repos. They carry no
  `AGENTTEAMS-BRIDGE` fence on purpose, so `--bridge-merge` reports them as "skipped (no fence)".
  That skip is the documented `--bridge-merge` contract, not drift. The bridge pointers live in the
  fenced `.claude/agent-team.md` and `.claude/quickstart-snippet.md`. Never run `--bridge-refresh`
  to "fix" the skip: it overwrites both files wholesale (see agentteams
  `references/bridge-refresh-safety.md`).
