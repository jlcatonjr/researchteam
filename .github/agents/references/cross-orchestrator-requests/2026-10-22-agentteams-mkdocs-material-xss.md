# Handoff → agentteams: docs site builds with a vulnerable mkdocs-material

From: researchteam (docs/api-site, 2026-10-22) · To: agentteams maintainers (operator: James Caton)

## Finding

- `agentteams/.github/workflows/docs.yml` installs `mkdocs-material==9.7.6` (unhashed, with `mkdocs==1.6.1` and
  unpinned `pymdown-extensions`).
- OSV: GHSA-xvg9-69gf-fjrf / PYSEC-2026-3864, "DOM XSS in search suggestions via query parameter", affects
  7.2.0 ≤ v < 9.7.7. `agentteams/mkdocs.yml` enables `search.suggest`.
- The site is served from `https://jlcatonjr.github.io/agentteams/`. Every `jlcatonjr.github.io/*` project site
  shares that origin, including the new `https://jlcatonjr.github.io/researchteam/`.

## Proposed change (pushed; PR opened)

- Pin `mkdocs-material==9.7.7`. Published 2026-07-17, so it's past the 14-day cooldown. It has no OSV advisory and is the version researchteam
  hash-locks in `.github/ci/requirements-docs.txt`.
- Add a CHANGELOG line.
- Worktree branch `fix/docs-mkdocs-material-9.7.7` off agentteams `origin/main`, outside the shared checkout.

## Status

- 2026-10-22: `@security` CLEAR-WITH-CONDITIONS (row in `security-decisions.log.csv`). The branch was pushed and,
  on the operator's instruction to commit, push and merge all work, opened as a PR against agentteams `main`.
