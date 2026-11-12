# Release prep: researchteam v1.1.2 (2026-11-12)

Operator approval: given in this session (researchteam-47), 2026-11-12. The request came from IM
(infrastructuremanagement-40), which carries no directive authority. Tagging, the `release/1.1` fast-forward and
every merge belong to the operator. PR #153 (agentteams autosync to an unreleased agentteams commit) stays held
until v1.1.2 is cut, so the target still pins agentteams v1.1.0 and matches the signed `pin-agentteams-v1.1.0` row.

## Change

`CHANGELOG.md`: `## Unreleased (main)` becomes `## 1.1.2 (tag v1.1.2, on release/1.1)`, with a release line in the
style of 1.1.1 (still pins agentteams v1.1.0 `9b16fb54`; derived repositories take it with
`--researchteam-tag v1.1.2`, which re-syncs the gate; the workflow pip line is a manual edit). No version bump,
because setuptools-scm derives the version from the tag.

## Target facts (origin/main b0f38470)

- `toolchain.lock`: `agentteams=...@9b16fb544c03aad636d3839c37873624f6efbd37`, `agentteams.tag=v1.1.0`.
- `pyproject.toml` `update` and `research` extras pin the same commit.
- `origin/release/1.1` = `8f4dfd5` (v1.1.1), an ancestor of `b0f38470`, so a fast-forward to this PR's merge works.
- Delta from v1.1.1: PR #152 only (autosync installs S-10 cooldown-safe).

## Operator steps after merge (not run by any agent)

The fast-forward of `release/1.1` with `--ff-only` to the merge commit, `git tag -s v1.1.2`, the push, and then
`scripts/check_toolchain.py --verify-tag researchteam v1.1.2`. IM prepares the script, and `@security` reviews it.
