First release candidate of the researchteam 1.3 line. It pins agentteams v1.3.0 (536306d2). This is a pre-release: derived repositories wait for v1.3.0.

- **agentteams 1.3.** `toolchain.lock` and the `update` / `research` extras move from agentteams v1.2.1 to v1.3.0, and the agent team is regenerated. The generated instruction sections say more exactly what `agentteams --verify-toolchain-pin` proves and name `@git-operations` as the owner of the pull-request lifecycle; the work-summary hook and the codex role gate are stricter. agentteams 1.3.0 needs Python 3.11 or later; researchteam itself still supports 3.10.
- **Term index: a pinned copy of agentteams' core.** `scripts/term-index-core/` holds the two core modules of the signed agentteams v1.3.0 as exact bytes, with a manifest; the engine is reduced to adapters. The copy is checked against its manifest before it runs and needs no installed agentteams. `researchteam doctor` reports a copy that does not verify as a failure, and CI compares the copy with the signed tag. Generated indexes, findings and exit codes are unchanged, except that a linked or oversized `terms.json` is refused with one combined message and a symlinked `terminology/index/` reads as stale.
- **Upgrade order.** Install the new researchteam first, then run `researchteam update`: an older researchteam does not sync the core directory.
- **Survey toolkit: the contract is version 1.** `docs/survey-toolkit.md` is frozen, and its per-study sign-off log is specified against agentteams 1.3.0's gates-only team directory. No survey tool ships yet; the tools are planned for the next minor release.
- **Concept map.** `templates/concept-map/` and `scripts/build_concept_map.py`: a reusable, interactive map of a debate, with its protocol and a skill.
- **Bibliography explorer contract 1.1:** three optional evidence columns.
- **Derived autosync workflow:** the release-locked check fetches the tag shallowly.
- **Governance.** The toolchain-group file is re-signed for this repository alone; the term-index core, its loader and the engine are paths whose pull requests need a `@security` PASS; merged pull-request heads may be deleted automatically.

`release/1.2` stays open for v1.2.N backports and keeps agentteams 1.2. Policy: `docs/release-policy.md`, "The 1.3 line". Full list and the upgrade steps: `CHANGELOG.md`.
