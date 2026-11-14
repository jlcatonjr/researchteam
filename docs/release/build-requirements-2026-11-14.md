# S-10 re-vet: build requirements (2026-11-14)

`pyproject.toml` `[build-system]` pins these exactly. They were re-vetted on 2026-11-14 against the
PyPI JSON API (`upload_time_iso_8601`, per-release `requires_dist`) and the OSV API (`/v1/query`, PyPI,
which includes GHSA and MAL-* entries). The query is `build-requirements-2026-11-14.query.py`, run at
2026-11-14T14:05Z. The cooldown is 14 days.

| Package | Was | Now | Uploaded | Age | OSV | Note |
|---|---|---|---|---|---|---|
| setuptools | 84.1.0 | **84.2.1** | 2026-10-20 | 24d | none | latest; requires Python >= 3.10; no dependencies |
| setuptools-scm | 10.3.4 | 10.3.4 | 2026-09-23 | 51d | none | latest; needs `vcs-versioning>=2.5.0.dev0,<3`, `packaging>=20` |
| vcs-versioning | 2.5.0 | **2.6.0** | 2026-10-06 | 38d | none | latest; needs `packaging>=26.2` |
| packaging | 26.3 | 26.3 | 2026-08-04 | 101d | none | latest |

This ends the setuptools 84.1.0 exception. 84.1.0 was adopted on 2026-10-24, inside the cooldown, on
the operator's instruction, to fix GHSA-xmj3-9gf7-h52w in 84.0.0. Its comment said "Re-vet on or after
2026-11-02", and that re-vet was missed until infrastructuremanagement-40 flagged it on 2026-11-13.
vcs-versioning 2.6.0 was inside the cooldown at the 2026-10-16 vetting
(`build-requirements-2026-10-16.md`). It cleared on 2026-10-20.

**Check:** `pip wheel . --no-deps` with build isolation, which installs exactly these pins, builds
`researchteam-1.1.5.dev0+g5fd8ec3…` from the v1.1.4 tag, so setuptools-scm still derives the version.
pytest: 590 passed, 1 skipped.

`tomli` and `typing-extensions` are needed only on Python < 3.11 (typing-extensions 4.16.0 is vetted in
`s10-dependency-vetting-2026-11-13.md`).
