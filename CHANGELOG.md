# Changelog

researchteam follows SemVer. The version comes from signed git release tags (setuptools-scm): `v1.0.0-rc.1`
builds `1.0.0rc1`, and `v1.0.0` builds `1.0.0`. See `docs/release-policy.md`.

## 1.1.0rc1 (tag `v1.1.0-rc.1`, on `release/1.1`)

The first 1.1 release candidate. researchteam 1.1 supports agentteams 1.1, which adds dependency-vulnerability
scanning (`python -m agentteams.vulnscan`) and per-project scanning intent in the brief. `release/1.1` is cut from
`main` here; `release/1.0` stays open for `v1.0.N` backports. Derived repositories move to 1.1 only by pinning this
tag (`--researchteam-tag v1.1.0-rc.1`), keeping the order agentteams → researchteam → derived.

### agentteams 1.1 (#114, #115, #116, #120)
- **The pin is the signed agentteams `v1.1.0-rc.6`** (tag object `7645e308`, peeled `0ef4404c`), in
  `toolchain.lock` (release-locked on the 1.1 line) and in both the `update` and `research` extras (#120). It
  includes agentteams' rc.4 security fixes (Copilot agent-file bypass, DLP secrets failing closed, goose recipe
  hidden-key check), rc.5 (Linux agent mode) and rc.6 (prefixed requirements scanned, macOS gate-8 fix). The line
  first moved to `v1.1.0-rc.2` (#116). Every move is covered by operator-signed `@security` rows:
  `release-line-agentteams-1.1` (the trust change from the 1.0 to the 1.1 line) and `s10-release-key-exemption-1.1`
  (the 14-day cooldown is waived for verified 1.1-line release-key tags only; third-party packages keep it, with a
  fresh OSV/GHSA search at every pin) (#115), and one pin row per tag (`pin-agentteams-v1.1.0-rc.2`,
  `pin-agentteams-v1.1.0-rc.6`). The rc.2 render refreshed the Claude and Codex orchestrators'
  `available_workflows` (held by the shrink guard since a hand-splice) and the team builder, which now asks for a
  scanning level.
- **Known gap:** the `research` extra is outside the S-10 vetting; it resolves packages inside the cooldown
  (`docs/release/s10-dependency-vetting-2026-10-16.md`). Use the `update` extra, or decide constraints first.
- **The upstream lock and extras move together.** `check_toolchain.py --write-lock --sync-extras` also points the
  `update`/`research` extras in researchteam's own `pyproject.toml` at the new agentteams commit, and refuses to
  write the lock when an extra cannot follow (another repository). The autosync gate passes it in `--mode
  upstream` only; a derived repository's `pyproject.toml` is never rewritten. `pyproject.toml` is now a
  security-relevant path in the gate's PR body.
- **`toolchain.lock` keeps its comments.** `--write-lock` rewrites an existing lock in place, so a project's own
  policy header and notes between pins survive (mathAgents' header was replaced before). Only a new lock gets the
  fixed header.
- **Dependency-scanning intent.** `brief.json` and the scaffold brief carry `"vulnerability_scanning": {"level":
  "scan"}` (agentteams 1.1). `researchteam init --vulnscan-level off|scan` sets it; `remediate` stays an operator
  choice (`agentteams --set-vulnscan`, which edits only that block of the user-owned brief).
- **Docs.** The release policy gains the 1.1 line (`release/1.1`, the line-move row, the 1.1 S-10 exemption); the
  pyproject comment and the update policy no longer name a pinned version, so they cannot go stale.

### Documentation site (#111)
- **Documentation site.** An MkDocs Material site (`mkdocs.yml`, `docs_src/`) with a CLI reference, a bridge
  reference and a per-module API reference, deployed to GitHub Pages at https://jlcatonjr.github.io/researchteam/
  by `.github/workflows/docs.yml` (pinned actions, hash-locked build dependencies in
  `.github/ci/requirements-docs.txt`, strict build with anchor checks on pull requests, deploy from `main` only),
  the same pipeline as agentteams. The README links it at the top. `tests/test_docs_site.py` keeps the site in
  step with the code, in both directions: a module without a page, a public name missing from its page, a CLI
  command or flag missing from the CLI reference (or documented but gone), and bridge commands that differ from
  the bridge reference all fail it. These files stay in this repository: none is synced by `update`, and `init`
  now skips `mkdocs.yml`, `docs_src/` and `.github/ci/requirements-docs.txt`, as it already skipped
  `.github/workflows/`.

### Fixes found while writing and auditing the API reference (#111)

- **`init --ref <commit>` works.** The help promised a SHA, but only branch and tag archives were tried. A 7–40 hex
  ref now falls through to the commit archive, and the marker records the full SHA. Fetch failures are a
  one-line error and exit 1 (was a traceback), and a ref with `.`/`..` segments, a `refs/pull/` head or other
  unsafe text is refused first.
- **Commits must be reviewed history.** GitHub serves every commit in a repository's fork network under the
  parent's URLs, so a SHA alone does not prove a commit was reviewed. `init --ref <commit>` now requires the
  commit to be on `main` or a `release/*` branch (asked through the GitHub API; refused when that cannot be
  confirmed). `update` with a commit ref refuses one GitHub says is on neither and warns when GitHub cannot
  answer. A `GITHUB_TOKEN` or `GH_TOKEN` raises GitHub's limit of 60 unauthenticated requests an hour.
- **`init` writes nothing until the archive checks out.** The download and a check of every member happen
  before the directory is created, so a failed fetch no longer leaves an empty directory. An archive with an
  absolute or `..` member is refused whole. Extraction confirms every destination is inside the target, and
  link members are skipped with a warning. A later failure names the incomplete project; nothing is deleted.
- **One `.researchteam` reader.** `update`'s fetch ref and the drift / pristine-check ref could disagree on
  `ref=foo` or `ref = "foo"`. `ref`, `layer1` and `is_upstream` are now all read by `_personalize.read_marker`:
  first occurrence wins, a trailing ` #comment` is dropped, and one pair of quotes is stripped. Note:
  `is_upstream = "true"` now counts as true. `update` refuses an unsafe resolved ref.
- **The agentteams provenance guard refuses unverifiable installs.** A VCS install now passes only from
  `github.com/jlcatonjr/agentteams`. A fork or mirror, a remote archive install, or an index install (agentteams
  is not on PyPI) is refused unless `RESEARCHTEAM_ALLOW_UNVERIFIED_AGENTTEAMS=1`, and so is an agentteams commit
  that GitHub reports is not on its `main` or a `release/*` branch (a fork's commit installed through the upstream
  URL); when GitHub cannot answer, the install runs with a warning. URLs with an unexpected port are not treated as
  the canonical repository. This includes a non-default
  `AGENTTEAMS_GIT` in the autosync gate. `RESEARCHTEAM_ALLOW_AGENTTEAMS_SNAPSHOT` still covers local snapshots
  only.
- **`library-query -k N`** no longer drops query words or a project name equal to `N`. A missing, non-integer
  or < 1 value is a usage error, and every usage error exits 2.
- **Removed `open-reader` / `open-summary`** from the bridge. They printed fixed `Projects/ZeldaTimeline/` paths
  that no derived repo has. Derived repos lose them on their next sync, and a call now prints the help and
  exits 2.

### CI
- The docs build pins certifi 2026.10.19, which fixes the critical GHSA-6q48-6c7w-9gw2, adopted inside the S-10
  cooldown on the operator's instruction (#112, #118). setuptools 84.1.0 for the test build (#117).

## 1.0.2 (tag `v1.0.2`, on `release/1.0`)

A patch release on `release/1.0` with two fixes found during Batallion's v1.0.0 sync. The agentteams pin is
unchanged (`v1.0.0`, `cc5b8c9e`), so there is no new pin row.

- **Bootstrap installs `agentteams[signing]` (#100).** `scripts/bootstrap_toolchain.sh` installed agentteams
  without its `signing` extra, so every Ed25519 gate check in a derived repo's `.venv` failed closed. It now
  installs the extra under the S-10 vetted `cryptography==50.0.0`, `cffi==2.1.1` and `pycparser==3.0`
  (embedded, because derived repos don't receive `docs/release/`; a test keeps them equal to
  `docs/release/constraints-2026-10-16.txt`), and fails if `cryptography` still isn't importable.
- **`CLAUDE.md` managed block (#101).** The layer-1 pass is described as skipped under `layer1 = off`, and a
  release-locked `toolchain.lock` as syncing layer 2 from the verified tag. The `docs/release-policy.md` link
  points upstream, since derived repos don't receive that file.

## 1.0.1 (tag `v1.0.1`, on `release/1.0`)

A patch release on `release/1.0`. It fixes the 1.0.0 known limitation, so consumers can resume the AgentTeams
Autosync once they pin 1.0.1. The agentteams pin is unchanged (`v1.0.0`, `cc5b8c9e`), so there is no new pin row.

- **Frozen surfaces (#94).** `brief.json` `frozen_surfaces` is the contract shared with agentteams 1.0.x.
  - It takes ids from `copilot-vscode`, `copilot-cli`, `claude`, `goose`, `agents-md`, `codex` and `grok`. An
    unknown id, a duplicate or a non-array value refuses the run.
  - researchteam never renders, merges, projects, bridges, Notes-syncs or managed-syncs into a listed surface's
    paths. `codex` behaves like `--no-codex`.
  - The root `AGENTS.md` is frozen when `codex`, `goose` or `agents-md` is listed. While it is frozen, **no
    bridge is refreshed**, because every `--bridge-merge` writes `AGENTS.md`.
  - `update` and `materialize` check every frozen path on every exit. A frozen `AGENTS.md` that an unfrozen
    render wrote is restored; any other change fails the run closed.
  - An unfreeze is constraint-relaxing. It needs an Ed25519-signed `unfreeze-<surface>` decision row that the
    pinned agentteams itself derives as relaxing. agentteams v1.0.0 can't make that derivation, so every
    unfreeze refuses until agentteams 1.0.x.
  - `doctor` reports the frozen set and any pending unfreeze.
  - Known limitation: a reviewed commit that removes a surface and its `.researchteam` record together isn't
    caught here. agentteams' freeze manifest covers it.
- **Environment files ignored (#85).** The managed `.gitignore` block ignores `.env`, `.env.*` and `*.env`, and
  allows `.env.example` and `.env.template`.
- **Docs (#84, part of #92).** A neutral release-lock example; collaborators need `allowed_signers` too. The
  citation-audit protocol, the orchestrator's notes and the bridge help now describe the defect classes
  added in 1.0.0 (#87), exit 2 and `--bib`. Two more citation-integrity scenarios.
- **Self-pin:** the advisory `researchteam=` line moves to `v1.0.0` (`a21e7db7`).

## 1.0.0 (tag `v1.0.0`, on `release/1.0`)

The first stable release, cut with agentteams `v1.0.0` in the joint order agentteams → researchteam →
mathAgents → baseAgent. It is `1.0.0rc3` plus the release changes below and one fix made after rc.3. By
operator ruling (2026-10-18) there is no rc.4 and no further soak.

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
  - This change was not in an RC. It ships in 1.0.0 by operator ruling (2026-10-18), because the defect was a
    false PASS on the anti-fabrication gate. CI runs its 57 scenarios. Backported by `cherry-pick -x` of
    `f8b7523`.

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
