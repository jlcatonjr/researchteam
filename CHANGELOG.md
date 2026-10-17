# Changelog

researchteam follows SemVer. The version comes from signed git release tags (setuptools-scm): `v1.0.0-rc.1`
builds `1.0.0rc1`, and `v1.0.0` builds `1.0.0`. See `docs/release-policy.md`.

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
