# S-10 dependency vetting — researchteam v1.1.4 (2026-11-13)

Supersedes `s10-dependency-vetting-2026-10-16.md` for new installs. That record and
`constraints-2026-10-16.txt` stay in place, because signed decision rows cite them.

Scope: the nine third-party packages in `constraints-2026-10-16.txt`. They are what agentteams' base install
(`jsonschema>=4.20`) and its `signing` extra resolve to. researchteam is the vetting authority; agentteams ships
no constraints file. Sources: the PyPI JSON API (earliest non-yanked `upload_time_iso_8601` of each release) and
the OSV API (`/v1/query`, ecosystem PyPI), both queried 2026-11-13. Rule: the latest stable release that is at
least 14 days old and has no OSV advisory.

| Package | Previous | Version | Uploaded | Age | OSV | Verdict |
|---|---|---|---|---|---|---|
| jsonschema | 4.26.0 | 4.26.0 | 2026-01-07 | 309d | none | keep (latest) |
| attrs | 26.1.0 | 26.1.0 | 2026-03-19 | 238d | none | keep (latest) |
| jsonschema-specifications | 2025.9.1 | 2025.9.1 | 2025-09-08 | 430d | none | keep (latest) |
| referencing | 0.37.0 | 0.37.0 | 2025-10-13 | 395d | none | keep (latest) |
| rpds-py | 2026.6.3 | **2026.9.1** | 2026-10-04 | 39d | none | adopt; the 2026-10-16 cooldown hold lifts |
| cryptography (signing extra) | 50.0.0 | **50.0.2** | 2026-09-30 | 43d | none | adopt (see below) |
| cffi | 2.1.1 | 2.1.1 | 2026-08-03 | 101d | none | keep (latest) |
| pycparser | 3.0 | **3.12** | 2026-10-22 | 21d | none | adopt; the 2026-10-16 hold (3.11 inside cooldown) lifts |
| typing-extensions | 4.16.0 | 4.16.0 | 2026-07-02 | 133d | none | keep (latest) |

The previous versions also returned no OSV advisory on 2026-11-13.

**cryptography 50.0.0 was an oversight.** The 2026-10-16 record lists 50.0.0 as the latest version, but 50.0.1
(2026-08-25) and 50.0.2 (2026-09-30) had both been published by then. No hold reason was recorded, and agentteams
confirmed none was intended.

**Depends on agentteams v1.1.3.** agentteams v1.1.2 (`bbf5920f`) declares `signing = ["cryptography==50.0.0"]`.
Under this file, `pip install -c constraints-2026-11-13.txt "agentteams[signing] @ git+…@bbf5920f"` fails with
`ResolutionImpossible` (reproduced on Python 3.12). The autosync gate installs `--no-deps`, and `pip check` does
not evaluate extras, so the gate alone would not catch this. agentteams has been asked to raise the pin to 50.0.2
in v1.1.3. This set is adopted only together with that pin move.

**Install check (2026-11-13):** `pip install --only-binary=:all: --no-deps` of this set, then `pip check`, is clean
on CPython 3.12, 3.13 and 3.14 (macOS arm64), and still clean with agentteams 1.1.2 added `--no-deps`. CPython
3.11, which the autosync workflow uses, was not available locally. The workflow run is the 3.11 check. PyPI lists
cp311 wheels for rpds-py 2026.9.1 and cryptography 50.0.2, and a py3-none wheel for pycparser 3.12. rpds-py 2026.9.1
and pycparser 3.12 require Python >= 3.11 (rpds-py 2026.6.3 already did). That costs nothing: agentteams itself
requires >= 3.11, and the Python 3.10 test job installs neither agentteams nor these constraints.

**Not covered: the `research` extra**, as in the 2026-10-16 record.
