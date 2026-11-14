# Build-system re-vet (2026-11-14)

The operator ruled, relayed by infrastructuremanagement-40 and confirmed by "proceed according to your
recommendation", that this goes in a separate PR after v1.1.4. The pins in `pyproject.toml` `[build-system]` are
setuptools 84.1.0 (an in-cooldown exception from 2026-10-24, overdue for re-vet since 2026-11-02) and
vcs-versioning 2.5.0. Both have newer releases that are past the cooldown.

Branch: `chore/build-system-revet-2026-11-14`, from `origin/main` = `5fd8ec3b` (v1.1.4).

1. Re-vet the four build requirements: PyPI dates, `requires_dist`, OSV. Output:
   `docs/release/build-requirements-2026-11-14.md` and its query script.
2. Move the pins: setuptools 84.2.1, vcs-versioning 2.6.0. Update the comment.
3. Build check: an isolated `pip wheel .` and the version derived from the tag. Then pytest.
4. Add a CHANGELOG entry under Unreleased.
5. `@security` review, then commit, push and open a PR. No tag: the change ships with the next release.
