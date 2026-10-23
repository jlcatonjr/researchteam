# Getting Started

## Install

`researchteam` is the entry point. `agentteams` is installed **through it as an extra**, never on its own: it is
not published to PyPI, so the base install declares no dependencies and a bare install leaves layer-1 agent
regeneration unavailable.

```bash
# base CLI only — layer-2 file sync, no agent regeneration
pip install "researchteam @ git+https://github.com/jlcatonjr/researchteam.git@v1.0.2"

# recommended — pulls agentteams in, enabling the layer-1 (agent-team) pass
pip install "researchteam[update] @ git+https://github.com/jlcatonjr/researchteam.git@v1.0.2"

# adds agentteams' research extra (web search, curated-source rating, claim verification)
pip install "researchteam[research] @ git+https://github.com/jlcatonjr/researchteam.git@v1.0.2"
```

These install the signed `v1.0.2` tag. For a verified install (a separate checkout of the tag, its signature
checked with repository config neutralised), see
[`docs/CONTRIBUTING.md`](https://github.com/jlcatonjr/researchteam/blob/main/docs/CONTRIBUTING.md).

Check that both tools resolve in the **active** interpreter:

```bash
python -m pip show researchteam agentteams
researchteam doctor
```

## Create a project

```bash
researchteam init my-research-project
cd my-research-project
```

`init` scaffolds a complete project directory, seeds a neutral placeholder `brief.json`, generates a
project-specific `README.md` / `CLAUDE.md`, runs `git init`, and makes an initial commit. Then:

1. Edit `brief.json` to describe your project (name, goal, `layer2_profile`, components, …).
2. Run `researchteam personalize` to regenerate `README.md` and `CLAUDE.md`'s header from the brief.
3. Run `researchteam materialize` to re-render the agent team so agent bodies reflect your domain and identity.
4. Choose your workflow: Claude (`CLAUDE.md`) or Copilot (`.github/copilot-instructions.md`).
5. Run `bash scripts/claude_researchteam_bridge.sh validate`.

## Keep it current

```bash
researchteam update            # interactive — shows a diff for each changed file
researchteam update --yes      # non-interactive (CI)
researchteam update --dry-run  # preview only
```

Projects created with `init` also receive `.github/workflows/agentteams-sync.yml`, which runs both layers on a
weekly schedule and on `workflow_dispatch`.

## Pinned toolchain

`toolchain.lock` records the researchteam and agentteams commits a derived repo was last synced and verified
with. To run exactly that pair:

```bash
bash scripts/bootstrap_toolchain.sh          # .venv with the pinned commits (gitignored)
python3 scripts/check_toolchain.py           # installed vs toolchain.lock vs upstream main
```

See [`scripts`](api-reference/scripts.md) for `check_toolchain.py`'s flags and the lock format.
