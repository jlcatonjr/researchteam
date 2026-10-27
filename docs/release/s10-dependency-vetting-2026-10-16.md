# S-10 dependency vetting — agentteams v1.0.0-rc.10 through rc.14 (2026-10-16, 2026-10-17)

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

**Carried over to v1.0.0-rc.13** (tag object `44664b80`, peeled `03592ea2`; verified 2026-10-17): between
`69fe9447` and `03592ea2`, `pyproject.toml` changes only the version line, `1.0.0rc12` → `1.0.0rc13`. The
resolved set is unchanged.

**Carried over to v1.0.0-rc.14** (tag object `3a3e423e`, peeled `c22aca0e`; verified 2026-10-17): between
`03592ea2` and `c22aca0e`, `pyproject.toml` changes only the version line, `1.0.0rc13` → `1.0.0rc14`. The
resolved set is unchanged.

Constraints that installs use until the two newer releases clear the cooldown (2026-10-18 and
2026-10-23): `docs/release/constraints-2026-10-16.txt`.

**Carried over to agentteams v1.1.0-rc.2** (tag object `4ef4d4f3`, peeled `df1ab17a`; verified 2026-10-23): the
declared dependencies (`[project]` and `[project.*]` tables) are identical to v1.0.0's. A fresh OSV/GHSA query
(2026-10-23) of the `signing` set resolved under `constraints-2026-10-16.txt` (Python 3.11 and 3.13) found no
advisory, and every version in the table above is past the cooldown. agentteams requires Python >= 3.11, as
v1.0.0 did.

**Carried over to agentteams v1.1.0-rc.6** (tag object `7645e308`, peeled `0ef4404c`; verified 2026-10-26): the
declared dependencies are still identical to v1.0.0's. A fresh OSV/GHSA query (2026-10-26) of the `signing` set
resolved under `constraints-2026-10-16.txt` (Python 3.11 and 3.13) found no advisory; the resolved versions are
unchanged from the table above and all are past the cooldown.

**Not covered by this vetting: the `research` extra.** `researchteam[research]` installs `agentteams[research]`,
which also resolves anyio 4.15.1, certifi 2026.10.23, h11 0.16.0, httpcore 1.0.9, httpx 0.28.1, idna 3.20 and
pypdf 6.21.2 (OSV none, 2026-10-23). certifi 2026.10.23 (uploaded 2026-10-23) and pypdf 6.21.2 (2026-10-21) are
**inside the 14-day cooldown**. No certifi release currently clears both the cooldown and the advisory search
(2026.7.22 carries GHSA-6q48-6c7w-9gw2; 2026.10.19 clears the cooldown on 2026-11-03). This gap predates 1.1 (the
same extra resolved unvetted packages under v1.0.0); it needs its own operator decision and constraints before
`researchteam[research]` is recommended for install.

**Carried over to agentteams v1.1.0-rc.7** (tag object `2c6b25fc`, peeled `decbcda8`; verified 2026-10-26): the
declared dependencies are still identical to v1.0.0's. A fresh OSV/GHSA query (2026-10-26) of the `signing` set
resolved under `constraints-2026-10-16.txt` (Python 3.11 and 3.13) found no advisory; the resolved versions are
unchanged. The same search over the `research` extra's resolved set (anyio 4.15.1, certifi 2026.10.23, h11 0.16.0,
httpcore 1.0.9, httpx 0.28.1, idna 3.20, pypdf 6.21.2) found none either.

**The cooldown is deprecated (2026-10-26).** By operator ruling (`s10-release-cooldown-deprecated`; agentteams #299)
releases no longer wait 14 days: the known-vulnerability search is what decides. The cooldown notes above are the
record of how each pin was vetted at the time. The `research` extra gap above therefore narrows to the vulnerability
search: certifi 2026.10.23 and pypdf 6.21.2 had no OSV advisory on 2026-10-23, and a fresh search runs at each pin.
