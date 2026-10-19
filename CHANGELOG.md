# Changelog

researchteam follows SemVer. The version comes from signed git release tags (setuptools-scm): `v1.0.0-rc.1`
builds `1.0.0rc1`, and `v1.0.0` builds `1.0.0`. See `docs/release-policy.md`.

## 1.0.0 (tag `v1.0.0`, on `release/1.0`)

The first stable release, cut with agentteams `v1.0.0` in the joint order agentteams → researchteam →
mathAgents → baseAgent. It is `1.0.0rc3` plus the release changes below and one fix made after rc.3. By
operator ruling (2026-10-19) there is no rc.4 and no further soak.

- **agentteams pin:** `v1.0.0` (tag object `5b0ac774`, peeled `cc5b8c9e`), in the lock (release-locked) and
  both extras. The operator-signed `@security` row `pin-agentteams-v1.0.0` names the tag object and the
  peeled commit. pyproject changes only the pin lines, so the S-10 vetting carries over.
- **Self-pin:** researchteam's own advisory `researchteam=` line moves to rc.3 (`3358b6c2`), the release it
  was last verified with.
- **Render:** researchteam is re-rendered on agentteams `v1.0.0`. The change is churn only: the agentteams
  version and commit, timestamps and the live vulnerability-watch data. Machine-path files are scrubbed,
  as the autosync gate does (S-8).

### Changed after rc.3

- **The citation audit no longer reports PASS without checking (#87).** `scripts/check_citation_integrity.sh`
  (`bridge citation-audit`), the fail-closed gate before compiling cited deliverables, could print PASS and
  exit 0 in two cases:
  - **No writable temp dir.** This happens in a sandboxed agent, for example. The audit now honours
    `TMPDIR` and exits **2** ("nothing was checked") when it can't write its work or output.
  - **The bibliography is outside the project.** This includes the scaffold default
    `references/bibliography.bib`. The DUP, META, LINK, CU, RM and REFURL checks never ran. The audit now
    looks for `--bib PATH` first, then the project's own `*.bib`, then the repo-level `references/*.bib`.
  - **Intended behaviour change:** a deliverable that cites sources but has no `.bib` anywhere now gives
    `DEFECT[NOBIB]` (exit 1), and an audit that passed vacuously may now report real defects.
  - This change was not in an RC. It ships in 1.0.0 by operator ruling (2026-10-19), because the defect was a
    false PASS on the anti-fabrication gate. CI runs its 57 scenarios. Backported by `cherry-pick -x`.

### Known limitation

- **The managed autosync gate does not honour frozen Codex and Goose surfaces.** The fix ships in
  researchteam 1.0.1. Keep the AgentTeams Autosync paused until consumers pin 1.0.1.

### Held for 1.0.1 (on `main`)

- #84 (update-policy docs) and #85: the managed `.gitignore` block will ignore `.env`, `.env.*` and `*.env`,
  and allow `.env.example` and `.env.template`. Until then, derived repos keep their own env-file ignore lines.

## 1.0.0rc3 (tag `v1.0.0-rc.3`, on `release/1.0`)

The third release candidate, required by the shared release policy (§6, 2b) once agentteams cut `v1.0.0-rc.14`.

- **agentteams pin:** `v1.0.0-rc.14` (peeled `c22aca0e`), in the lock (release-locked) and both extras. rc.14
  changes agentteams' proposal runner, MCP grant revocation and the integrity check for a clean Claude team.
  pyproject changes only the version line, so the S-10 vetting carries over. researchteam is re-rendered on
  rc.14 (churn only).
- **Notes sync leaves bespoke agents alone (#79; mathAgents).** An agent whose upstream-owned part is
  customised (the same check as #50), or that `brief.json` lists under `researchteam_notes.exclude`, is
  skipped on every surface and left byte-identical. A malformed `researchteam_notes` syncs no Notes block
  at all until it is fixed.
- **Derived repos verify a release-locked researchteam before installing it (#77, #78).** The derived
  workflow's trust-root step now runs first. For a lock with `researchteam.tag`, the runner's own `git`
  checks that the tag is in researchteam's refs, is annotated, verifies against `AGENTTEAMS_ALLOWED_SIGNERS`
  and peels to the locked commit. Only then is that commit installed. The derived workflow isn't synced, so
  derived repos adopt this step in their first release-lock PR.
- **CI runs the tests (#75, #76).** `.github/workflows/tests.yml` runs pytest and the bridge validator on
  `main` and `release/**`, on Python 3.10 and 3.13. The actions are SHA-pinned and the test dependencies are
  hash-locked and S-10-vetted.

## 1.0.0rc2 (tag `v1.0.0-rc.2`, on `release/1.0`)

The second release candidate. The joint soak moved to agentteams `v1.0.0-rc.13` (operator ruling 2026-10-17),
so it tests exactly what ships.

- **agentteams pin:** `v1.0.0-rc.13` (peeled `03592ea2`), in the lock (release-locked) and both extras. rc.13
  changes only agentteams' macOS proposal runner, which researchteam does not use. pyproject changes only the
  version line, so the S-10 vetting carries over. researchteam is re-rendered on rc.13.
- **The rc.1 soak's findings (#70):**
  - `check_toolchain`'s version probe runs isolated (`python -I`), so an editable build's `*.egg-info` can no
    longer make a release-locked `--write-lock` fail closed;
  - the upstream sync workflow installs the commit being synced, not `main`.
- Closing-audit fixes for rc.1. researchteam's own `toolchain.lock` self-pin moves to the rc.1 commit
  (advisory; no `researchteam.tag` upstream). The autosync ref records agentteams rc.12. The release policy
  states the frozen-Codex exception (shared policy §5) and the upstream self-pin rule. Doc wording is
  corrected.
- Note for operators: once a decisions log is migrated to the signing schema and `enforce_decision_signing`
  is on, older **unsigned** rows (such as researchteam's own `commit-scaffold-fixes` from 2026-09-30) no
  longer clear any action. Sign a fresh row instead.

## 1.0.0rc1 (tag `v1.0.0-rc.1`, on `release/1.0`)

The first 1.0 release candidate. It is cut jointly with agentteams `v1.0.0-rc.12`, mathAgents and baseAgent
under the shared v1.0.0 release policy. The 1.x line supports agentteams 1.x.

### Release-locked pins (#49, #67, formerly #52)
- The agentteams pin moves to the signed `v1.0.0-rc.12` (peeled `69fe9447`), in `toolchain.lock` and in
  both the `update` and `research` extras. `check_toolchain.py` fails when an extra and the lock disagree.
- A `<name>.tag=vX.Y.Z` line in `toolchain.lock` release-locks that pin. The autosync gate then follows
  the newest verified signed tag on the `vX.Y` line, never `main`. It never rewrites a locked pin to an
  untagged commit, and it fails closed when verification or the lock write fails.
- Tag verification (`researchteam/_release.py`) requires all of these:
  - an annotated tag;
  - `git tag -v` passing against `allowed_signers`, with repository, global and system git config
    neutralised;
  - a pinned release-key fingerprint, read from git's stderr only;
  - the tag object the remote advertises.
- `researchteam update` syncs Layer 2 from the lock's verified researchteam tag instead of `main`.
- The S-10 release-key cooldown exemption and the dependency vetting (rc.10, carried over to rc.11 and rc.12) are
  recorded under `docs/release/`.

### Fixes
- `update` no longer replaces a derived repo's customised `interpretation-advisor.agent.md`. It compares
  against the template at the repo's pinned researchteam commit, keeps customised files under `--yes`, and
  adds `--accept-upstream PATH` (#50; reported by mathAgents).
- Codex is orchestrator-only (agentteams #210). `brief.json` sets `write_policy: orchestrator-only` for
  codex with a confined `privilege_profile`. The interop projection path now fails fast with a clear
  message instead of agentteams' opaque refusal. Skills still project (#51). After a native render,
  `update` names any `.codex/agents` agent file the render didn't generate, such as the stale projected
  `tool-pandoc.toml`, which is removed in the rc.12 render (#56, #63).

### Versioning and derived repos
- The version is derived from git release tags (setuptools-scm). A commit between tags builds the next
  version as `.devN`, so `pip install --upgrade` always sees a change. Build requirements are S-10-vetted
  exact pins (#57; masterTeacher 4.5).
- Expert handles in upstream-shipped text and Notes sync follow the derived repo's own components (masterTeacher 4.3).

- `scripts/sign_security_decision.py` refuses an HMAC key under 32 bytes or that looks like a placeholder,
  matching agentteams 1.0.0rc12 (#60; masterTeacher 4.1).
- `update` warns when `brief.json` omits fields the native surfaces infer by scanning the repo
  (`retrieval_integration`, `tools`), because the surfaces' rosters can then differ. This is a known 1.0
  limitation; one scan rule for every surface is planned for 1.0.1 (#62, #61; masterTeacher 4.4).

- `researchteam update --no-codex` leaves Codex unchanged, for repos that keep Codex frozen in 1.0 because
  their roster has adopted agents (shared policy §5) (#64).

### Signing and the rc.12 render
- Operator decision signing is set up: the `op-2026` Ed25519 verify key is provisioned, the decisions log
  is migrated to the signing schema with `text_digest`, and six operator-signed rows are recorded
  (release-policy-1.0, the S-10 exemption, the rc.12 pin, and the #210 Codex decision on two teams) (#65).
- `enforce_decision_signing` is back on for every surface. It had been off since #48, until keys and a
  signing workflow existed; an unsigned authorizing row is now refused (#66).
- researchteam is rendered on agentteams rc.12. Codex is native and orchestrator-only, the stale projected
  `tool-pandoc.toml` is removed, and the Codex interpretation-advisor is synced from `.github` once (#66).

### Hygiene and review
- Drift and above-notes now split at the same CRLF-safe Notes heading, and the package has one lock
  parser (#54, #67).
- CODEOWNERS routes the release trust paths (pins, tag verification, signed decisions, verify keys) to
  the operator (#55).

### Since 0.2.0
- Toolchain pinning per repository, and the agentteams beside researchteam is run (#35, #39).
- Drift reporting: frozen fences, seeded-file drift and stale bridges (#36, #43).
- The managed interpretation-advisor and upstream-authored Notes blocks (#38).
- The historical-context protocol, its detector and advisor duties (#30).
- Native claude/goose surfaces stay current in merge mode, and bridges refresh after layer 1 (#34, #42).
- The autosync gate runs from a private copy, admits every surface layer 1 writes, and flags
  security-boundary paths (#31, #33).
- `layer1 = off` for hand-maintained repos (#41).
- Renders continue under orchestrator-only writes (#45, #46).
- `materialize` renders only reviewed agentteams code (#29).
