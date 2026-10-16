# S-10 vetting: build requirements for the git-derived version (2026-10-16)

`pyproject.toml` `[build-system]` pins these exactly. Sources: the PyPI JSON API
(`upload_time_iso_8601`) and the OSV API (`/v1/query`, PyPI), queried 2026-10-16. The cooldown is 14 days.

| Package | Pinned | Uploaded | Age | OSV | Note |
|---|---|---|---|---|---|
| setuptools-scm | 10.3.4 | 2026-09-23 | 22d | none | latest |
| vcs-versioning | 2.5.0 | 2026-09-23 | 22d | none | **2.6.0 (9d) is inside the cooldown**; setuptools-scm needs `>=2.5.0.dev0,<3` |
| setuptools | 84.0.0 | 2026-08-08 | 68d | none | latest |
| packaging | 26.3 | 2026-08-04 | 72d | none | latest; vcs-versioning needs `>=26.2` |

`tomli` and `typing-extensions` are needed only on Python < 3.11. typing-extensions 4.16.0 is vetted in
`s10-dependency-vetting-2026-10-16.md`.
