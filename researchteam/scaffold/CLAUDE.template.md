# Claude Interface Bridge for {{PROJECT_NAME}}

This file is the operating bridge for Claude users working in this repository.

## Project Purpose

{{PROJECT_GOAL}}

Primary outputs:
- Deliverables in `{{PRIMARY_OUTPUT_DIR}}` and/or `Projects/`
- Reference/bibliography data under `references/`
- Governance and execution plans in `tmp/by-week/`

<!-- >>> researchteam:managed — synced from upstream; do not edit inside this block -->
<!-- Everything ABOVE this marker (title + Project Purpose) is project-owned and preserved across
     `researchteam update`. Everything between the markers is synced from the framework. -->

## Working Rules

1. Keep claims traceable to explicit sources.
2. Do not fabricate references.
3. Preserve existing file structure and naming conventions.
4. For multi-step work, create a plan and step CSV in `tmp/by-week/YYYY-Www/`.
5. Prefer non-destructive changes unless explicitly requested.
6. When the project produces cited research deliverables, run the 2-fold citation & claim audit
   before compiling — `bash scripts/claude_researchteam_bridge.sh citation-audit <project>`
   (mechanical layer), then the doubled semantic audit in
   `docs/citation-claim-audit-protocol.md`. Unresolved citation/claim findings block compilation
   (fail-closed). A clean run means WELL-FORMED, not proof of non-fabrication.

## Quick Start

Run the bridge helper:

```bash
bash scripts/claude_researchteam_bridge.sh help
```

## Standard Workflow

1. Inspect current repo state.
2. Create/update plan artifacts in `tmp/by-week/` for multi-step edits.
3. Edit target files.
4. Run `bash scripts/claude_researchteam_bridge.sh validate`.
5. Commit and push when requested.

## Key Paths

- Agent infrastructure: `.github/agents/`
- Project definition: `brief.json`
- CI workflow: `.github/workflows/agentteams-sync.yml`
- Bridge docs: `docs/claude-interface-bridge.md`
- Framework + CLI reference: `docs/researchteam-framework.md`
- Claude support folder: `.claude/`

## Keeping Infrastructure Current

Keep framework infrastructure current with the researchteam CLI:

```bash
researchteam update          # interactive — shows diffs before applying
researchteam update --yes    # non-interactive (CI-safe)
researchteam update --dry-run  # preview only
```

`researchteam update` syncs framework files under `docs/`, `scripts/`, `.claude/`, and the
**managed block of this `CLAUDE.md`** from the upstream template, then runs
`agentteams --update --merge` for agent infrastructure. It never touches `brief.json`,
`Projects/`, or `references/`. This file's title and Project Purpose header, and `README.md`, are
project-owned and are generated from `brief.json` — not synced. To re-render them run
`researchteam personalize`; to re-render the agent team after a domain/identity change in
`brief.json` run `researchteam materialize`.

### Installing the toolchain (agents: verify this before relying on either tool)

`researchteam` is the entry point. `agentteams` is **installed through it as an extra**, never on
its own — it is not published to PyPI, so the base install deliberately declares
`dependencies = []` and a bare `pip install researchteam` leaves layer-1 agent regeneration
unavailable.

```bash
# base CLI only — layer-2 file sync, no agent regeneration
pip install "git+https://github.com/jlcatonjr/researchteam.git"

# recommended — pulls agentteams in, enabling `researchteam update`'s layer-1 pass
pip install "researchteam[update] @ git+https://github.com/jlcatonjr/researchteam.git"

# adds agentteams' research extra (web search, curated-source rating, claim verification)
pip install "researchteam[research] @ git+https://github.com/jlcatonjr/researchteam.git"
```

Agents must not assume the toolchain is present, and must not assume that an `agentteams` found on
`PATH` belongs to the interpreter they are running under. Check both:

```bash
python -m pip show researchteam agentteams   # both must resolve in the ACTIVE interpreter
which researchteam agentteams                # both should sit in that same environment
python -c "import sys; print(sys.prefix)"    # the environment those two must belong to
```

If `agentteams` is missing, install the `update` extra above; if it resolves from a different
environment than `sys.prefix`, treat the toolchain as unavailable. Do not hand-edit generated
agent infrastructure as a workaround — the next sync discards the edit. Run `researchteam doctor`
for a full diagnosis.

## Notes for Claude Users

- If running outside a git worktree context, some validation checks may be reduced.
- Do not manually edit AGENTTEAMS fenced sections in agent docs. Route multi-file agent changes
  through orchestrated workflows.
- Back up research and agent files before update or merge runs.
- Use `.claude/README.md` for reusable templates and preflight checklists.

<!-- <<< researchteam:managed -->
