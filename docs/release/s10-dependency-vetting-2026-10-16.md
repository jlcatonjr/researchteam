# S-10 dependency vetting — agentteams v1.0.0-rc.10 / rc.11 / rc.12 (2026-10-16)

Scope: every third-party package that resolves when installing agentteams `f0dcdc85` (v1.0.0-rc.10)
with the `signing` extra, the trusted signer install. The S-10 release-key exemption covers agentteams
itself only. Sources are the PyPI JSON API (`upload_time_iso_8601`) and the OSV API (`/v1/query`,
ecosystem PyPI), queried 2026-10-16. The cooldown is 14 days.

| Package | Version | Uploaded | Age | OSV | Verdict |
|---|---|---|---|---|---|
| jsonschema | 4.26.0 | 2026-01-07 | 281d | none | adopt |
| attrs | 26.1.0 | 2026-03-19 | 210d | none | adopt |
| jsonschema-specifications | 2025.9.1 | 2025-09-08 | 402d | none | adopt |
| referencing | 0.37.0 | 2025-10-13 | 367d | none | adopt |
| rpds-py | 2026.9.1 | 2026-10-04 | 11d | none | **inside cooldown**: constrain to 2026.6.3 (2026-06-30, 107d, OSV none) |
| cryptography (signing extra) | 50.0.0 | 2026-07-31 | 76d | none | adopt |
| cffi | 2.1.1 | 2026-08-03 | 73d | none | adopt |
| pycparser | 3.11 | 2026-10-09 | 6d | none | **inside cooldown**: constrain to 3.0 (2026-01-21, 267d, OSV none) |
| typing-extensions | 4.16.0 | 2026-07-02 | 105d | none | adopt (Python < 3.11 only) |

**Carried over to v1.0.0-rc.11** (tag object `dcb66d97`, peeled `ee09a037`): between `f0dcdc85` and
`ee09a037`, `pyproject.toml` changes only the version line, `1.0.0rc10` → `1.0.0rc11`. There are no
dependency, extra or constraint changes, so the table above is the resolved set for rc.11 as well.

**Carried over to v1.0.0-rc.12** (tag object `8bc1cd17`, peeled `69fe9447`): between `ee09a037` and
`69fe9447`, `pyproject.toml` changes only the version line, `1.0.0rc11` → `1.0.0rc12`. The resolved set is
unchanged.

Constraints that installs use until the two newer releases clear the cooldown (2026-10-18 and
2026-10-23): `docs/release/constraints-2026-10-16.txt`.
