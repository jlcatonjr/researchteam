# API Reference — ResearchTeam

Reference for the `researchteam` package and its helper scripts.

!!! note "Supported surface"
    The supported interface is the `researchteam` **command line** ([CLI Reference](../cli-reference.md)) and the
    [bridge commands](../bridge-reference.md). Every module in the package is underscore-prefixed: the
    functions below are documented for contributors and for anyone reading a run's behaviour, and may change
    between releases. Check `CHANGELOG.md` for compatibility notes.

---

## Commands

| Module | Role |
|--------|------|
| [`cli`](cli.md) | Argument parsing, repo-root discovery, ref resolution; dispatches to the modules below |
| [`_update_cmd`](update.md) | `researchteam update` and `researchteam materialize`: layer-2 sync, agentteams render on every surface, Codex, bridges |
| [`_init_cmd`](init.md) | `researchteam init`: scaffold a project from the upstream tarball |
| [`_personalize`](personalize.md) | `researchteam personalize`: render `README.md` / `CLAUDE.md` header from `brief.json` |
| [`_doctor_cmd`](doctor.md) | `researchteam doctor`: toolchain health and drift report |

## Safety and drift

| Module | Role |
|--------|------|
| [`_frozen`](frozen.md) | Declared frozen surfaces (`frozen_surfaces` in `brief.json`): never written, proven unchanged after a run |
| [`_drift`](drift.md) | Frozen fences, seeded-file drift and bridge drift that `update` would otherwise leave silent |
| [`_notes`](notes.md) | Upstream-authored `researchteam:notes` blocks synced into agents' Project-Specific Notes |
| [`_release`](release.md) | Signed release-tag verification and release-line pins in `toolchain.lock` |
| [`_agentteams_provenance`](agentteams-provenance.md) | Refuses to render with an unreviewed `agentteams` install |

## Data and transport

| Module | Role |
|--------|------|
| [`_manifest`](manifest.md) | Upstream repo, managed-file sets per `layer2_profile`, merge strategies, fence markers |
| [`_fetch`](fetch.md) | Stdlib-only GitHub raw-file and tarball fetches |

## Scripts

| Page | Role |
|------|------|
| [`scripts`](scripts.md) | `check_toolchain.py`, `build_literature_library.py`, `query_literature_library.py`, `sign_security_decision.py` |
