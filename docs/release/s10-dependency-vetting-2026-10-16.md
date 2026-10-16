# S-10 dependency vetting — agentteams v1.0.0-rc.10 (2026-10-16)

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

Constraints that installs use until the two newer releases clear the cooldown (2026-10-18 and
2026-10-23): `docs/release/constraints-2026-10-16.txt`.
