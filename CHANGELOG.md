# Changelog

researchteam follows SemVer. The version comes from signed git release tags (setuptools-scm): `v1.0.0-rc.1`
builds `1.0.0rc1`, and `v1.0.0` builds `1.0.0`. See `docs/release-policy.md`.

## Unreleased

- **Survey toolkit, step B part 2a: the identity registry** (`scripts/survey/survey_provenance.py`,
  `survey_identity.py`, `survey_registry.py`). New bridge command `survey-registry <project>`:
  - it builds `identity.registry` from the persons of the evidence and attribution files, applying the overrides file
    (a `link` sets `identity_id`, a `merge` folds one id into another), and writes the registry's provenance record
    beside it, last; a run interrupted anywhere leaves the registry "not built";
  - `--candidates` lists possible matches (`exact`, `similar`, with the study's stop words) for a person to decide in
    the overrides file; nothing is applied and nothing is written;
  - every check of the overrides file (a named author and a reason in every row, one link or merge per alias, no
    repeated or self pairs, no `distinct` row for a linked or merged pair) refuses the build and writes nothing;
    `survey-validate` reports them too.
  The provenance record of contract 4.6 is written in one shared module (`make_record`, `check_current`,
  `write_all`, `check_output_target`), for later steps' outputs too. A record also lists a declared input that was
  absent at build, so its appearing later makes the output stale. An output and its record are written only inside
  the study's own folder (checked by path, real path and device and inode), never over the specification or a file
  it declares, never inside a declared folder or the ledger folder, and never under `.git`, `.github` or a team
  location; where the platform allows, the write is made relative to the folder that was checked. The registry holds
  the ids a merge folded in, so evidence keeps them (a merge alias must be an id of the project's rows); it records
  how many legacy exceptions the evidence is read with; a value with a control, format or line-break character
  refuses the build. The build reads only its declared inputs.
  Candidates are indexed by word; only undecided ones are listed, at most 1000 shown. A study with a vantage module, or with evidence in a plugin format,
  is refused: this version loads no project code. The batch merge (`survey-rows`) is step B part 2b. The check table
  is `references/plans/post-1.3.0-h5-step-b2-check-table.md`.
- Survey toolkit, step B part 1 follow-ups: `B.C`, `B.C.E` and `B. C.` count as BC; a century range
  (`4th-5th centuries`) reads both centuries; a number grouped by thousands (`1,750`, `1,750.5`) gives no year, while
  a list (`450,500`, `12.03.1750`) gives one from each run; quoted
  values are cut in every message, step A's included.
- **Survey toolkit, step B part 1: the row files** (`scripts/survey/survey_tables.py`, `survey_attribution.py`,
  `survey_evidence.py`). `survey-validate` now also checks every row file contract sections 4.1, 4.3 and 4.8 define
  that is present:
  - evidence rows, with the contract's rule ids (`columns`, `id-empty`, … `vocabulary`), and a legacy study's
    exceptions file (a listed breach is counted and does not fail; an exception that no longer applies is an error);
  - the attribution file of a passage or work study;
  - the registry's presence and shape ("a missing registry is itself an error"); the registry is not built yet;
  - the forbidden vocabulary, matched on folded text;
  - bucket tables, with the bucketer (`match` first and all) and the year and period rule as functions for later
    steps (a run of three or four digits, else a stated century in any of its usual spellings; a year marked BC or
    BCE is negative and not read);
  - the form and presence of a fetch-receipt citation (a row whose locator is not a `<work slug>#p<N>` locus; a
    receipt must carry the ten required keys of 4.4). Nothing re-finds a quotation yet: that is step G.
  Row files are streamed (at most 64 MiB) and opened at their resolved place under rule 1.6. Every output line
  escapes control characters, so a file cannot forge a line. Project patterns are capped in length and number, and
  every compile failure is a finding. The excused breaches and the quotations not re-found are printed on every run.
  Evidence in a `plugin` format is not read (the reader plug-in is not loaded: not implemented), and
  `survey-validate` fails for it.
  The batch merge (`survey-rows`), the identity registry (`survey-registry`) and writing a first exceptions file
  are step B part 2. The check table is `references/plans/post-1.3.0-h5-step-b-check-table.md`.
- Survey toolkit, step A follow-ups: a `parent_team` with a `..` segment says so; the example study's S0 manifest
  hash is pinned in a test; a `study.json` reached through a link inside the repository is tested to load.
- **Survey toolkit, step A** (`scripts/survey/`, against the frozen contract `docs/survey-toolkit.md`, version 1).
  The specification validator makes every check of section 3, with the path rule (1.6), and stable error ids of its
  own (the contract gives none for section 3). A JSON Schema of `study.json` (`scripts/survey/study.schema.json`)
  is generated from the validator's rule table; a test keeps the tracked file equal to the generator's output. The
  gate list, the manifest builder (6.1), the rule that turns a gate's state into "runs" or "refuses", and the
  structural checks of the ledger folder (6.2). Three bridge commands, each taking a project: `survey-validate`,
  `survey-status` and `survey-manifest <gate>`; the bridge refuses a `--root` argument. Standard library only,
  Python 3.10 to 3.13. The files, and the contract `docs/survey-toolkit.md` they cite, are synced with the
  scholarly profile.
  - **Nothing verifies a signature yet.** A gate reads `UNCLEARED` when its files changed since its manifest file
    was written (step A's stand-in for the `agentteams` sign-off request, which it does not read), and
    `UNAVAILABLE` otherwise; it never reads `CLEARED`. A team directory reached through a symbolic link (or with a
    link inside it), or a `parent_team` with one of the faults 6.2 lists, leaves the gates `UNAVAILABLE` without
    failing a command; a `parent_team` value that is no path at all is a malformed ledger. No command of this step
    is a gated stage.
  - The manifest file is written beside the ledger's log, as `<ledger>/references/<study id>.<gate>.manifest.json`.
    A manifest carries each path as declared, so a path with a `.` or empty segment is refused. Two spellings of one
    file are one file (by device and inode). Every capped read opens without following a link or blocking on a FIFO
    and checks the open file is regular. The ledger's keys and approvers are compared with a team directory only when
    it has both an approver and a verify key; one that lacks either "has neither" (6.2). A ledger inside `.git` or a
    generated team location is refused, by case-folded name and by device and inode.
  - Not in this step: the row checks of section 4 (step B), sign-off verification and the HALT scan (step F), and
    the CI gate (step H). The check table, with the points where the contract is silent, is
    `references/plans/post-1.3.0-h5-step-a-check-table.md`.

- **Docs: the release policy gives the order for moving a derived repository to a new line.** No rule changes.
  `docs/release-policy.md` told a derived repository to run `--write-lock` with both tags and did not say that a
  locked repository must first drop both `.tag=` lines (said in the 1.2.0 and 1.3.0 changelog sections), that the
  lock writer needs the new agentteams installed, or that a workspace with signed rows needs agentteams'
  `signing` extra (both said only in the 1.3.0 section). The policy now has one passage, "Moving a derived
  repository to a new line", that the 1.1, 1.2 and 1.3 line sections point to. It also covers a move within a
  line: plain researchteam is installed, and the agentteams already locked is kept. The three bullets about
  researchteam's own lock now say whose lock they mean. "Autosync and Layer 2" says the workflow is enabled,
  proposes the agentteams update as one evergreen pull request and merges nothing, and keeps the 1.0-era pause
  and the pause during the 1.3.0 cut as dated history; `docs/CONTRIBUTING.md` says the same.

## 1.3.0 (tag `v1.3.0`, on `release/1.3`)

The first release of the 1.3 line. It is `1.3.0rc1` plus: this section, the release notes, the cut record and the
operator's cut script (a tracked copy under `references/plans/`), the install instructions (below) with a new test
that guards them, and one wording correction in `docs/term-index-protocol.md`. Nothing that runs in a derived
repository differs from the candidate: no synced script, no workflow, no package code. What a derived repository
does receive differently is text: `docs/researchteam-framework.md`, `docs/term-index-protocol.md` and the install
line in the managed `CLAUDE.md` block (and its scaffold template). researchteam 1.3 pins agentteams 1.3: this release pins
agentteams **`v1.3.0`** (`536306d2`). The changes and the five upgrade notes are listed under `1.3.0rc1` below.

Derived repositories take it in this order, because an older researchteam does not sync the term-index core and
the lock writer runs the installed code:
1. Verify both signed tags first (Rule S-9): researchteam `v1.3.0` and agentteams `v1.3.0`, each in a clone,
   against the release key in `~/.config/agentteams/allowed_signers` and with repository config neutralised
   (`docs/CONTRIBUTING.md`, "Verifying a release", gives the command). Note the commit each peels to; agentteams
   `v1.3.0` peels to `536306d2502e3db338846677f2d37489531ac8e7`.
2. Install both with the interpreter that runs `check_toolchain.py` (Python 3.11 or later):
   `python3 -m pip install "researchteam[update] @ git+https://github.com/jlcatonjr/researchteam.git@<peeled commit>"`.
   The `update` extra installs agentteams at the commit above. The lock writer refuses `--tag agentteams=v1.3.0`
   while another agentteams is installed, and `researchteam update` would regenerate the team with the old one.
   A workspace with signed decision rows or a toolchain-group file also needs agentteams' `signing` extra in that
   interpreter, as `scripts/bootstrap_toolchain.sh` installs it. Without it the group file does not verify, and
   the S-10 cooldown applies to the release (seen in a downstream dry run against the candidate).
3. `researchteam update --ref v1.3.0`, then
   `python3 scripts/check_toolchain.py --write-lock --tag researchteam=v1.3.0 --tag agentteams=v1.3.0`. A locked
   repository leaves two release lines at once, researchteam 1.2 and agentteams 1.2, and `check_toolchain.py`
   refuses a cross-line `--tag` for each pin. So drop both the `researchteam.tag=` and the `agentteams.tag=` line
   from `toolchain.lock` before `--write-lock`. Both line moves are trust changes and get that repository's own
   `@security` review.

`release/1.2` stays open for `v1.2.N` backports.

- **Install instructions name the newest stable release** (reported by a derived repository, 2026-11-12).
  - **Defect:** `docs/researchteam-framework.md`, which `researchteam update` syncs to every derived repository,
    still installed `researchteam.git@v1.0.2` and called it the newest `v1.0.N`, in every release from 1.1.1 to
    1.2.1. The same stale tag was in `README.md`, `docs/CONTRIBUTING.md`, the docs site (`docs_src/`) and the
    managed `CLAUDE.md` block (and its scaffold template), and `CONTRIBUTING.md` still described the 1.1 line as
    release candidates.
  - **Fix:** they name `v1.3.0`. A repository on an older line installs that line's newest tag.
    `CONTRIBUTING.md` describes the four release branches, the backport request, the rulesets and the autosync as
    they are.
  - **Guard:** `tests/test_install_pins.py` fails when these files name any tag other than the highest final
    release heading in this file, so the release-prep pull request that adds a heading must move them too.
- **Docs: the term-index repair note names the right version.** `docs/term-index-protocol.md` said a researchteam
  "older than 1.3.0" lacks the core's file list; the candidate `1.3.0rc1` already has it, so the text now says
  "older than 1.3.0rc1".

## 1.3.0rc1 (tag `v1.3.0-rc.1`, on `release/1.3`)

The first release candidate of the 1.3 line. researchteam 1.3 pins agentteams 1.3: this candidate pins agentteams
**`v1.3.0`** (`536306d2`). `release/1.3` is cut at this commit; `release/1.2` stays open for `v1.2.N` backports and
keeps agentteams 1.2. It is a candidate: derived repositories wait for `v1.3.0`, apart from the dry-run pin check
the next repository in the release order runs against it.

**Upgrading a derived repository (at `v1.3.0`, not at this candidate).**

1. **Install the new researchteam first, then run `researchteam update`.** An older researchteam does not sync
   `scripts/term-index-core/`, and the term index refuses to run without it; `validate`, `term-check` and
   `researchteam doctor` say "upgrade researchteam first" in that state. A repository that has not yet synced the
   new engine keeps working, and doctor only warns there.
2. **The term index runs a pinned copy of agentteams' core.** It is checked against its manifest before it runs
   and needs no installed agentteams. Do not edit the files under `scripts/term-index-core/`: a changed byte stops
   `term-check`, `term-build` and `validate`, and doctor reports a failure. Two edge cases read differently (a
   linked or oversized `terms.json`; a symlinked `terminology/index/`); see the term-index entry below.
3. **agentteams 1.3.0.** The agent team is regenerated. An overwrite render (`researchteam materialize`,
   `agentteams --overwrite`) now stops before any write when it would drop agents the orchestrator routes to,
   unless they are named with `--accept-routing-loss`. A file-bound clearance checked in any team directory is
   now refused by an unretracted HALT in the repository's other team logs. Both are in agentteams' own changelog
   for 1.3.0 (its issues #392 and #578); read it before an overwrite.
4. **The autosync workflow** fetches a release tag shallowly. It reaches a repository through
   `researchteam update --workflow` and that repository's own review.
5. **Python.** researchteam still supports Python 3.10; agentteams 1.3.0 itself needs 3.11 or later, so the
   `update` and `research` extras do too.

- **Derived autosync workflow: the release-locked check fetches the tag shallowly.**
  `researchteam/scaffold/agentteams-sync-derived.yml` fetched researchteam's whole history to verify one tag. It
  now fetches with `--depth=1 --filter=tree:0` and retries once with `--depth=1`, as `verify_tag` does; a fetch
  that fails both ways fails the check. Every check after the fetch is unchanged, and no credential is involved.
  A derived repository receives the new workflow only through its own sync (`researchteam update --workflow`)
  and its own review of that change.

- **Survey toolkit: the per-study sign-off log is specified (open point 1 closed).** Section 6.2 of
  `docs/survey-toolkit.md` now gives the log's folder layout, a gates-only team dir as agentteams 1.3.0 documents
  it, and the HALT rule: an unretracted HALT in the repository's team logs binds a study's sign-off. Only an
  Ed25519 row by a key in the folder clears a gate, and a waiver file there is an error. The text says what a
  sign-off proves while its keys live in the repository; a trust root outside it is a new open point. The
  sign-off tools will require agentteams 1.3.0 or later. The contract stays version 1.

- **Governance: the term-index loader and engine join the paths that need a `@security` PASS (PS-2).**
  `scripts/check_term_core.py` decides which bytes of the pinned core run, and `scripts/term_index_engine.py` decides
  whether that loader is used, so a pull request that touches either is merged only with a `@security` PASS naming
  it (operator ruling, 2026-11-24). The projected copies of the project rules are re-synced.

- **Term index: the engine now runs a pinned copy of agentteams' term-index core.** `scripts/term-index-core/` holds
  `term_index.py` and `_term_text.py` from the signed agentteams tag `v1.3.0` as exact bytes, its MIT licence and a
  manifest (`PINNED.json`) naming the tag, the commit and each file's sha256. `scripts/term_index_engine.py` is
  reduced to adapters over that core. The core is loaded only after its bytes match the manifest, it needs no
  installed agentteams, and it may import nothing but the standard library and its own two modules.
  - `term-check`, `term-build` and `validate` refuse to run on a copy that does not match its manifest, and
    `researchteam doctor` reports a mismatch as a failure. `term-core-check` runs the check alone.
  - `python -m researchteam._term_core_upstream` compares the copy with the signed tag over the network; the
    offline check proves only that the copy matches its manifest.
  - `researchteam update` syncs the directory byte for byte, as one set that is checked against its manifest
    before anything is written, and refuses to write through a symlink.
  - CI: a new workflow, `term-core.yml`, runs the network comparison on every pull request and push that touches
    the directory or the code that checks it. It takes the comparing code from the base branch, so a pull
    request cannot pass by changing that code alone. Three limits: a pull request that edits the workflow file
    itself runs its own version of it (PS-2's `@security` PASS for workflow paths covers that); the pull request
    that introduced the job ran its own copy of the code; and the job is not a required check.
  - A repository still on the engine from before the switch gets a doctor warning, not a failure.
  - Generated indexes, findings and exit codes are unchanged, with these exceptions. A register that is a link, not
    a regular file, or larger than the size limit is refused with one combined message. A symlinked
    `terminology/index/` is now reported as `[STALE]` instead of passing.
  - `assess` takes `reuse` by keyword only.

- **Governance: `scripts/term-index-core/` joins the paths that need a `@security` PASS (PS-2).** The directory
  holds the term-index core copied from agentteams and its manifest. A pull request that touches it is merged
  only with a `@security` PASS naming it (operator ruling, 2026-11-24). The rule was in place before the
  directory landed. The projected copies of the project rules are re-synced.

- **Toolchain: agentteams v1.3.0 is pinned, the first pin on the 1.3 line.** `toolchain.lock`, the `update` and
  `research` extras and the autosync ref name `536306d`, the commit the signed tag `v1.3.0` peels to. The move off
  the 1.2 line is recorded by the operator-signed row `release-line-agentteams-1.3`; the review of the pin itself is
  `docs/release/pin-agentteams-v1.3.0.decision-spec.json`. The agent team is regenerated on all four surfaces: the
  generated instruction sections say more exactly what `agentteams --verify-toolchain-pin` proves and name
  `@git-operations` as the owner of the pull-request lifecycle, and the work-summary hook and the codex role gate
  are stricter. A derived repository receives the pin at its next sync.

- **Synced files no longer name other repositories.** Eleven files that `researchteam update` copies into every
  derived repository (eight protocol and policy documents under `docs/`, and three scripts' header comments) named
  particular derived repositories, their projects or their commits as the origin of a pattern. They now say "a
  derived research repository" or similar. No behaviour changes. A derived repository receives the new wording at
  its next sync.

- **CI: the concept-map layout and component tests now run.** `tests.yml` installs Graphviz from the runner's
  Ubuntu archive and checks that Node 20 or later is present, and fails when either is missing, so those tests no
  longer skip in CI. The pytest summary lists any test that was skipped.

- **Survey toolkit: the contract is frozen as version 1.** `docs/survey-toolkit.md` is no longer a draft. The first
  project had its S0 and S5 gates signed and merged its first evidence rows on 2026-11-23, which was the condition
  for the freeze. Ten changes that project's run brought out are taken (section 12): the frame of a passage or work
  study and its passage list (new section 4.7), the cell as the frame's unit, a registry seeded from the attribution
  file and renewed by an evidence merge (or the merge is refused), person-level rows with new row checks, no empty
  enumeration rounds, period columns named after the period attribute, an analysis-engine pin that may be a file
  only S6 covers, and a plain statement of what a re-found quotation proves. Bucket tables and the year rule are
  written down for the first time (4.8). `schema_version` is `"1"`; `"0"` is read identically. No survey tool is
  implemented yet.

- **Governance: the toolchain-group file is re-signed for this repository alone (sequence 5).**
  `.agentteams/toolchain-group.json` is now signed with the decision key `opr-2026-11` and lists this workspace only;
  the group and its `derives_from` are unchanged. The exception registry's `toolchain_group_sequence` is 5, so the
  sequence 1 file (signed with `op-2026`) is refused as a rollback. Part of the key rotation.

- **Concept map: a reusable, interactive map of a debate (#247).** `templates/concept-map/` adds a contract
  (`researchteam.concept-map`, version 1.0), an exporter (`scripts/build_concept_map.py`) and a dependency-free
  component (`concept-map.js`, `concept-map.css`). A project writes one JSON spec of actors (writers or groups, each
  tied to person ids from its register), topics (claims and findings) and typed lines (in the example: affirms,
  denies, documented, inferred). The exporter checks it fail-closed, writes the Graphviz DOT and SVG for the static
  figure, gets the layout from Graphviz and computes who each topic ties to, with direction. A line between a group
  box and a topic must say whom it speaks for (`only`) or be marked reviewed (`all_members`); until then the build
  lists it under REVIEW. The component draws the map, makes every node a focusable button and reports the selection;
  the host lists the people in its own panel. The procedure around it (drafting, a two-round independent audit, a
  second pass and an audit log) is `docs/concept-map-protocol.md`, synced to scholarly derived repositories. Like the
  bibliography explorer, the template is vendored, not synced. A `/concept-map` skill (`.claude/skills/concept-map/`)
  is hand-written in this repository and `researchteam update` does not sync it either. Tests:
  `tests/test_concept_map.py` and a Node component test; the Graphviz and Node tests skip where those programs are
  missing. First integrated by a derived project.

- **Governance: merged pull-request heads may be deleted automatically (#234).** PS-2 in `.claude/CLAUDE.md` has
  a new exception: once the operator turns on the repository setting "Automatically delete head branches", GitHub
  deletes a pull request's head branch when it merges, with no deletion record and no hold checks for that one
  deletion. The agent checks holds by hand before it asks for a merge approval, and a deleted head is restored
  from `refs/pull/<n>/head`. Every other deletion is gated as before. The exception rests on the operator-signed
  decision `repo-setting:delete-branch-on-merge:jlcatonjr/researchteam` and ends on 2027-02-18, or earlier on a
  HALT, or when the decision stops verifying or its registry entry is no longer active. Nothing switches the setting off automatically; the operator does that with a handoff script.
- **Governance: the legacy cooldown exemption for agentteams is retired (#234).** The exception registry entry
  `s10-cooldown-exempt:jlcatonjr/agentteams` is now `sunset`. It was redundant with the operator-signed
  first-party toolchain group, which still lifts the Rule S-10 cooldown for agentteams releases. The registry
  allows one active relaxing exception, and the slot now holds the decision above.
- **Bibliography explorer: contract 1.1.** `evidence.csv` may carry three optional columns, `basis`, `reporter`
  and `note`. The exporter (`scripts/build_bibliography_explorer.py`) carries them into the explorer file and the
  component shows them beside each piece of evidence. One new error: a `reporter` on a row with no `basis`. The
  change is additive: inputs written for 1.0 still export, and the file's `schema_version` is now `1.1`. A
  project that vendors the explorer takes the exporter and the component from the same commit
  (`templates/bibliography-explorer/CONTRACT.md`, section 7). This is step 2 of `docs/survey-toolkit.md`,
  section 10; no survey tool is added.
- **Docs: the cut script's identity and signing-key checks are release policy (#231).** `docs/release-policy.md`,
  "Tags", now says the cut script sets the tagger email itself (the operator account's GitHub no-reply address),
  refuses to sign unless the release key is registered as a signing key on that account, and reports GitHub's
  verification after the push. The report never stops a release, and GitHub's badge is not the consumer check:
  consumers still verify against the allowed-signers file. The checks shipped in the `v1.2.1` cut script.
- **Tests: the update and materialize tests pass when run alone (#233).** `tests/test_update_native_surfaces.py`
  and `tests/test_materialize_surfaces.py` failed when run by themselves, because `researchteam._frozen` binds
  `subprocess.run` at import and was first imported after a test had faked it. `tests/conftest.py` now imports
  it before any test runs. One test no longer reaches the network. No code under test changed.
- **Tests: characterization tests for the term index (#232).** `tests/test_term_index_characterization.py` pins
  the behaviour at the points the switch to the agentteams term-index core (1.3.0) could change.

## 1.2.1 (tag `v1.2.1`, on `release/1.2`)

A patch release on the 1.2 line. It still pins agentteams **`v1.2.1`** (`a7ab95e2`); the pin does not move in
this release. A derived repository locks agentteams separately and may be on a later `v1.2.N`.

Derived repositories take it as an ordinary patch release, in this order, because the lock writer runs the
installed code:
1. Verify the signed tag `v1.2.1` first (Rule S-9): in a clone, `git verify-tag v1.2.1` against the release key in
   `~/.config/agentteams/allowed_signers`, and note the commit it peels to.
2. Install that commit with the interpreter that runs `check_toolchain.py`:
   `python3 -m pip install "git+https://github.com/jlcatonjr/researchteam.git@<peeled commit>"`.
3. `researchteam update --ref v1.2.1`, then
   `python3 scripts/check_toolchain.py --write-lock --tag researchteam=v1.2.1 --tag agentteams=<the v1.2.N it uses>`.

- **Fix: verifying a release tag no longer downloads the pinned repository's history.** `researchteam._release`
  `verify_tag` (used by `check_toolchain.py --write-lock` and `--verify-tag`, and so by `researchteam update` on
  a release-locked pin) fetched the tag with the repository's full history under a
  300-second limit. On a slow link that timed out, and the lock could not be written. It now fetches only the
  tag object and the commit it names (`--depth=1 --filter=tree:0`, retried once with `--depth=1` alone for a git
  or a server without object filters). Every check is unchanged: an annotated tag, the fetched object equal to
  the advertised one, a good signature from a release key, and the peeled commit. Reported by the fleet's sync
  wave.
- **Docs: the pin-move record in a workspace without decision signing (#213).** No rule changes.
  `docs/agentteams-update-policy.md` said a first-party member's release needs no decision-log row only where
  the operator-signed group file lists the workspace. It now also names a workspace where decision signing is
  off and the brief lists the member in `s10_cooldown_exempt_repos`. There the record is the same `@security`
  review in the pin-move PR, and the tag is verified with `scripts/check_toolchain.py --verify-tag` or
  `git verify-tag`, because `agentteams --verify-toolchain-pin` checks nothing without a group file.

## 1.2.0 (tag `v1.2.0`, on `release/1.2`)

The first release of the 1.2 line. It is `1.2.0rc1` plus release files only (this section, the release notes and
the cut record). researchteam 1.2 pins agentteams 1.2: this release pins agentteams **`v1.2.1`** (`a7ab95e2`). The
changes are listed under `1.2.0rc1` below.

Derived repositories take it with `researchteam update --ref v1.2.0`, then
`python3 scripts/check_toolchain.py --write-lock --tag researchteam=v1.2.0 --tag agentteams=v1.2.1`. A locked
repository leaves two release lines at once, researchteam 1.1 and agentteams 1.1, and `check_toolchain.py` refuses a
cross-line `--tag` for each pin. So drop both the `researchteam.tag=` and the `agentteams.tag=` line from
`toolchain.lock` before `--write-lock`. Both line moves are trust changes and get that repository's own `@security`
review. Before moving, read the generated "GitHub
management" section against the repository's own project rules (merges into the default branch need the operator's
live approval), and give any unscoped Claude agent an explicit `tools:` line (agentteams #511). `release/1.1` stays
open for `v1.1.N` backports.

## 1.2.0rc1 (tag `v1.2.0-rc.1`, on `release/1.2`)

The first release candidate of the 1.2 line. researchteam 1.2 pins agentteams 1.2: this candidate pins agentteams
**`v1.2.1`** (`a7ab95e2`). `release/1.2` is cut at this commit; `release/1.1` stays open for `v1.1.N` backports and
keeps agentteams 1.1. It is a candidate: derived repositories wait for `v1.2.0`, apart from the dry-run pin check
the next repository in the release order runs against it. The term-index core switch is not in the 1.2 line; it
is planned for researchteam 1.3 (`docs/term-index-protocol.md`, "Planned placement").

- **agentteams 1.2 (the researchteam 1.2 line).** The agent team is regenerated with agentteams 1.2.1, and
  `toolchain.lock` and the `update` / `research` extras move from agentteams `v1.1.4` to **`v1.2.1`** (`a7ab95e2`). New in the
  rendered team: a "GitHub management" section and an "Integration-branch merge authorization" section in the
  instruction files, an updated constitutional gate hook, a work-summary stop hook (an example the operator may
  merge into `settings.json`), and new reference files. agentteams 1.2 changes an unscoped Claude agent's fallback
  grant to read-only (`Read`, `Grep`, `Glob`; agentteams #511); every agent researchteam renders already declares
  `tools:`, so no grant changes. A derived repository with its own unscoped agents must add an explicit `tools:`
  line. Policy: `docs/release-policy.md`, "The 1.2 line".
- **Merges into `main` and `release/*` need the operator's live approval** naming the PR and head, under the
  generated "GitHub management" section. Project rule PS-2 and the release policy say the same (#216). A repository
  that delegated merges to an agent session should read that section against its own project rules before it moves
  to 1.2.

- **Bibliography explorer (#210).** A reusable view of a project's people and sources: period, person, bio with
  the evidence behind each attribute, and source detail with a Chicago-style citation and summary.
  `scripts/build_bibliography_explorer.py` (with `scripts/bibtex_chicago.py`) builds one data file from a project's
  input tables and its `.bib`; `templates/bibliography-explorer/` holds the data contract, the display component and
  an invented example. Standard library only; no third-party JavaScript. `researchteam update` does not sync these
  files: a derived repository vendors them at a pinned commit (`templates/bibliography-explorer/README.md`). A clean
  export means well-formed and consistent, not that any value or citation is true.

## 1.1.9 (tag `v1.1.9`, on `release/1.1`)

A patch release on `release/1.1`. It still pins agentteams **`v1.1.4`** (`b82d78e7`). Derived repositories take it
with `researchteam update --ref v1.1.9`, then
`python3 scripts/check_toolchain.py --write-lock --tag researchteam=v1.1.9 --tag agentteams=v1.1.4`. To take the
workflow change, run `researchteam workflow-sync` (it keeps the repository's own `on:` block; add `--yes` where
there is no terminal to answer from) and give the result the repository's own `@security` review. Read the cache rule below against the repository's other
workflows.

- **Autosync and `workflow-sync`: small hardening (#205).** From this repository's `@security` reviews of #182
  and from derived repositories that took v1.1.8. No behaviour changes for a normal run.
  - `open_pr` now requires the gate's `new_sha` to be a full commit id (40 hex characters). The gate always
    emitted one; 7 to 40 was accepted.
  - `open_pr` counts changed names from the listing itself, so a name that ends in line breaks is also treated
    as sensitive.
  - The gate step reads the `force` input and the event name from `env:`; no expression is expanded inside its
    script.
  - `researchteam workflow-sync` with no answer on standard input (a script, a pipe, CI) now says that nothing
    was written and that `--yes` applies without asking. It still exits 1.
  - `scripts/check_toolchain.py --release-candidate` / `--verify-tag` (which the autosync gate's `--check-only`
    uses) now names the interpreter that cannot import researchteam and says to run with the project
    environment.
  - `docs/agentteams-update-policy.md` states a rule for every repository that runs autosync: a workflow that
    holds a write token or a secret restores no cache, and neither does a read-only one whose result gates a
    merge, a release or a publication. The read-only gate job can still write Actions caches, and no code
    change here can take that away.
  - A derived repository takes the workflow change with `researchteam workflow-sync` and its own `@security`
    review.

- **Docs: where a pin move is recorded; Working Rule 8 without a managed block.** Two points raised by derived
  repositories moving to v1.1.8. No rule changes.
  - `docs/agentteams-update-policy.md` now says where the record of a pin move goes. For a release of a
    first-party toolchain-group member it is the repository's own `@security` review in the pin-move PR: no
    decision-log row, and no decision row is signed; the signed-tag check still applies. For any other move it is a row in the decisions log, which the
    operator signs where decision signing is on. This restates `docs/release-policy.md`, "Pins".
  - `docs/term-index-protocol.md` now says that a repository whose root `CLAUDE.md` has no `researchteam:managed`
    block does not receive Working Rule 8, and how to add it.

## 1.1.8 (tag `v1.1.8`, on `release/1.1`)

A release on `release/1.1`. It still pins agentteams **`v1.1.4`** (`b82d78e7`). It is numbered as a patch release
by operator ruling (2026-11-17), but it also carries a new feature, the term register and term index; the
feature is additive and changes nothing for a repository that has no term register. Derived repositories take it
with `researchteam update --ref v1.1.8`, then
`python3 scripts/check_toolchain.py --write-lock --tag researchteam=v1.1.8 --tag agentteams=v1.1.4`. To take the
autosync workflow change (#182), run `researchteam workflow-sync` (it keeps the repository's own `on:` block) and
give the result the repository's own `@security` review; the new workflow uses two more pinned actions.
On researchteam 1.1.x the term index now takes bug fixes only (see `docs/term-index-protocol.md`, "Planned
placement").

- **Autosync: the gate job cannot write (#182).** In both autosync workflows the gate, which runs integrated
  agentteams and researchteam code, now runs in a job with `contents: read`. A new job, `open_pr`, holds the
  write token and runs no integrated code.
  - The gate job uploads one patch and the PR body as an artifact. `open_pr` checks out the run's branch, confirms it is the gate's
    commit, checks the gate's outputs, applies the patch with `git apply`, and opens the evergreen PR.
  - `open_pr` refuses a `.git` path, a symbolic link, a submodule entry and a `.gitattributes` filter. It decides
    the `security-review-required` label itself, with the repository's committed gate script; the gate job's
    answer can only add the label.
  - The PR body is passed by path, so its text no longer goes through a step output.
  - New pinned actions: `actions/upload-artifact` v7.0.2 and `actions/download-artifact` v8.0.2 (both released
    2026-10-07; OSV search 2026-11-16 found no advisory for either version).
  - Residual: the patch and the body still come from the job that runs integrated code, so the review of the
    PR's diff remains the control on its content.
  - A derived repository receives the new workflow with `researchteam workflow-sync`, which keeps its `on:`
    block. That is a workflow change, so the repository's own `@security` review applies.
- **Term register and synced term index.** Operator ruling, 2026-11-16: every project defines its terms as
  coded definitions, every appearance of a registered term is indexed, and the index is kept in sync by a
  reliable trigger.
  - Each project keeps a register at `Projects/<project>/terminology/terms.json` (one record per concept:
    preferred label, definition, accepted variants, discouraged forms, source). `scripts/build_term_index.py`,
    using the engine in `scripts/term_index_engine.py`, finds every occurrence in the project's documents by matching plain prose and writes a manifest of
    content hashes, one index file per document and a glossary beside the register.
  - `scripts/check_term_index.py` is the gate. It blocks on a malformed register, a form claimed by two
    terms, a `source` key missing from the `.bib`, an empty or unsafe scope, a stale or hand-edited index,
    index files left without a register, a missing register where one is required, and a discouraged form used outside a quotation with no recorded exception. A clean
    run means well-formed and current, not that terms are used in their defined sense.
    `scripts/query_term_index.py` lists where a term occurs.
  - New bridge commands: `term-init`, `term-build`, `term-check`, `term-query`. **`validate` now runs the
    term check** when `scripts/check_term_index.py` is present, so a stale index fails validation. A
    repository with no register is unaffected. Setting `term_index_require = true` in `.researchteam`
    makes a register compulsory for every research project; upstream sets it.
  - `.claude/settings.terms.example.json` holds optional Claude Code hooks that rebuild the index after
    edits and at session start. The operator merges them by hand. Hooks run outside the sandbox.
  - `CLAUDE.md` gains Working Rule 8. Protocol: `docs/term-index-protocol.md`. Six files join the
    scholarly managed set. After a later update changes the builder, `term-check` reports an advisory
    `[REBUILD]`; run `term-build` and commit.
  - A derived repository's CI does not run `validate` unless its owner adds the step, so there the gate is
    local. The protocol says how to add it.
  - **Follow-ups.** `researchteam workflow-sync --workflow validate` writes an opt-in, read-only workflow
    (`.github/workflows/researchteam-validate.yml`) that runs the bridge validator on pull requests and on
    pushes to `main`; `init` does not install it and `update` never touches it. `researchteam doctor`
    reports on the term index: the gate's summary, whether the rebuild hooks are wired, and whether a
    workflow runs the validator. `researchteam update` prints a reminder while a project has a register
    and the hooks are not wired. All three are advisory.
  - Research basis and audit record: `Projects/CodedTermIndexing/` and
    `references/plans/term-index-2026-11-16.design.md` (`tests/test_term_index.py`).

## 1.1.7 (tag `v1.1.7`, on `release/1.1`)

A patch release on `release/1.1`. It still pins agentteams **`v1.1.4`** (`b82d78e7`). Derived repositories take it
with `researchteam update --ref v1.1.7`, then
`python3 scripts/check_toolchain.py --write-lock --tag researchteam=v1.1.7 --tag agentteams=v1.1.4`. To take the
workflow change, run `researchteam workflow-sync` (it keeps the repository's own `on:` block) and give the result the
repository's own `@security` review.

- **Derived autosync schedule off by default; `researchteam workflow-sync` (#186).** Operator ruling, 2026-11-16.
  The derived scaffold (`researchteam/scaffold/agentteams-sync-derived.yml`) now ships with its weekly
  `schedule:` commented out, so a new derived repository runs autosync only when dispatched, and turning the weekly
  run on is a deliberate edit there. The upstream researchteam workflow keeps its schedule. The new command
  `researchteam workflow-sync [--yes] [--dry-run]` rewrites an existing repository's
  `.github/workflows/agentteams-sync.yml` from the installed scaffold but keeps that repository's own top-level
  `on:` block, so a repository running autosync keeps its schedule and one without it stays off. It shows a
  diff, asks before writing, refuses a symlinked path or a file without a block-style `on:`, and never writes
  through a link (`tests/test_workflow_sync.py`).

- **Docs: taking a scaffold change keeps the repo's `on:` block (#186).** The 1.1.5 and 1.1.6 entries and the
  v1.1.6 release notes tell an existing derived repository to copy `researchteam/scaffold/agentteams-sync-derived.yml`
  over its workflow. The scaffold up to 1.1.6 ships the weekly `schedule:` live, so a whole-file copy turns autosync back on
  in a repo that had removed it (reported by mathagents-2e through infrastructuremanagement-65). Port only the
  `permissions:` / `jobs:` changes and keep the repo's own `on:` block; `docs/agentteams-update-policy.md` now says
  so. The released entries are left as released.

## 1.1.6 (tag `v1.1.6`, on `release/1.1`)

A patch release on `release/1.1`. It pins agentteams **`v1.1.4`** (`b82d78e7`). Derived repositories take it with
`researchteam update --ref v1.1.6`, then
`python3 scripts/check_toolchain.py --write-lock --tag researchteam=v1.1.6 --tag agentteams=v1.1.4`.

- **agentteams pin v1.1.3 -> v1.1.4 (#180).** agentteams 1.1.4 pins its isolated build to `setuptools==84.2.1`
  (Rule S-10). Its installed code is 1.1.3's; only the version strings and the build requirements change. The
  `update` and `research` extras and `toolchain.lock` move together. The move rests on the first-party toolchain
  group (`agentteams --verify-toolchain-pin` passes). The same sync regenerated the agent surfaces with the PS-1 to
  PS-3 rules projection. `@security` passed it, with five conditions, all verified (OSV: no advisory on the vetted
  dependency set).
- **Autosync token scope (#179).** Both autosync workflows (`.github/workflows/agentteams-sync.yml` and the
  derived scaffold) now grant nothing at workflow level. The evergreen-PR lookup from #172 runs in its own job,
  `evergreen_pr`, with `contents: read` / `pull-requests: read`, and passes `open` to the `autosync` job as a job
  output. If the lookup fails, the gate still treats the state as unknown and uses the current branch's ref.
  `actions/checkout` now runs with `persist-credentials: false`, so the job's write token is not left in
  `.git/config` while the gate runs integrated code; the PR step authenticates with its own token input. The
  separate evergreen fetch step is gone, since `fetch-depth: 0` already fetches that branch. Derived repositories
  get the scaffold only at `init`, so an existing one copies `researchteam/scaffold/agentteams-sync-derived.yml`
  to `.github/workflows/agentteams-sync.yml` itself (a workflow change: its own `@security` review applies).
  Reported by Batallion's `@security`.

## 1.1.5 (tag `v1.1.5`, on `release/1.1`)

A patch release on `release/1.1`. It still pins agentteams **`v1.1.3`** (`cbd41a74`); moving to agentteams v1.1.4
is a separate step. Derived repositories take it with `researchteam update --ref v1.1.5`, then
`python3 scripts/check_toolchain.py --write-lock --tag researchteam=v1.1.5 --tag agentteams=v1.1.3`.

- **`researchteam update` never replaces an unfenced `CLAUDE.md` or `.gitignore` (#173).** When the local file
  had no `researchteam:managed` fence and differed from upstream, approving the interactive prompt wrote the
  whole upstream file over it, behind a diff preview cut at 50 lines. Adopting repositories lost their own
  `CLAUDE.md` this way. Approving now appends the fenced managed block below the unchanged content, as
  `researchteam adopt` does; `--yes` still keeps the file as it is. Reported through infrastructuremanagement-40.
- **The autosync gate no longer strands an update on a branch with no PR (#172).** The gate took its baseline
  from `chore/agentteams-autosync` whenever that branch existed. After a failed PR step, or a PR closed without
  merging, a re-run reported "nothing to integrate" and finished green, and no PR was ever opened. The branch's
  ref now counts only while an open PR has the branch as its head. Both workflows look that up in a step of
  its own (`AUTOSYNC_EVERGREEN_PR_OPEN`), so no token reaches the gate step; if the lookup fails, the gate warns
  and uses the current branch's ref (`tests/test_autosync_evergreen_baseline.py`). Reported through
  infrastructuremanagement-40.
- **`python -m researchteam` and `python -m researchteam.cli` run the CLI (#165).** Before this, `python -m
  researchteam.cli` imported the module, did nothing and exited 0, so a script using it silently skipped every
  step. This adds `researchteam/__main__.py` and a `__main__` guard in `cli.py` (`tests/test_module_entry.py`).
- **Docs: no `--researchteam-tag` flag.** Earlier entries say derived repositories move with
  `--researchteam-tag <tag>`, but no researchteam command has that flag. The command is `researchteam update
  --ref <tag>`, followed by `python3 scripts/check_toolchain.py --write-lock --tag researchteam=<tag> --tag
  agentteams=<agentteams tag>`, which records the release lock. Batallion and SocialScienceHumanities
  reported this through infrastructuremanagement-40. The 1.1.4 entry is corrected; older entries are left as
  released.
- **Build requirements re-vetted (S-10, 2026-11-14; #161).** setuptools `84.1.0` → `84.2.1` and vcs-versioning
  `2.5.0` → `2.6.0`, both latest, past the cooldown and OSV-clean. setuptools-scm `10.3.4` and packaging
  `26.3` stay. This ends the in-cooldown setuptools 84.1.0 exception of 2026-10-24
  (`docs/release/build-requirements-2026-11-14.md`).

## 1.1.4 (tag `v1.1.4`, on `release/1.1`)

A patch release on `release/1.1` that pins agentteams **`v1.1.3`** (`cbd41a74`) and adopts the operator-signed
first-party toolchain group. Derived repositories take it with `researchteam update --ref v1.1.4`, then
`python3 scripts/check_toolchain.py --write-lock --tag researchteam=v1.1.4 --tag agentteams=v1.1.3`.

- **agentteams pin: `v1.1.1` (`2fe79c05`) → `v1.1.3` (`cbd41a74`, tag object `1f1ffe6b`).** `toolchain.lock` and
  the `update`/`research` extras move together. agentteams 1.1.2 introduced the first-party toolchain group
  (`--verify-toolchain-pin`, `--verify-toolchain-group`, `--sign-toolchain-group`), and 1.1.3 adds its lineage
  check. researchteam skips 1.1.2. 1.1.3's declared dependencies differ from 1.1.1 only in the `signing` extra:
  `cryptography==50.0.0` → `50.0.2`.
- **First-party toolchain group (operator rulings R9, T1-T3).** `.agentteams/toolchain-group.json` is the fleet's
  operator-signed group file: sequence 1, key `op-2026`, sha256 `a38d0484…a80a`. It covers agentteams, researchteam,
  baseAgent and mathAgents across 15 workspaces. It derives from the new root row `s10-first-party-releases-2026-11`
  in `security-decisions.log.csv`. Releases of group members skip S-10's 14-day cooldown. A pin move to one needs
  this repository's own `@security` review and a verified signed tag, with no per-release operator row
  (`docs/release-policy.md`). The vulnerability search, the S-9 tag check and the latest-stable rule still apply.
  The legacy `s10-cooldown-exempt:jlcatonjr/agentteams` entry stays until it lapses on 2027-02-01.
- **The autosync gate checks group pins.** After it writes the lock, the gate runs
  `agentteams --verify-toolchain-pin toolchain.lock --allowed-signers … --output .github/agents --description brief.json`:
  - exit 0: the group exemption applies;
  - exit 2 (no group file): no exemption is claimed and ordinary S-10 applies at review. This fails in upstream
    mode (researchteam is a group member) and passes in derived mode with a `::warning::` and a PR-body notice;
  - exit 1 and any other code fail, and so does an exit 0 for an untagged agentteams pin;
  - an agentteams without the flag fails with its own message.

  Before the check, a trust-root guard refuses a regen that moves `HEAD` or touches the group file, the verify
  keys or the decision log (untracked, ignored, skip-worktree and assume-unchanged entries count too). The guard
  stops accidents, not a hostile candidate; on release-locked runs the signed-tag check is the trust anchor.
- **S-10 re-vet (2026-11-13), `docs/release/constraints-2026-11-13.txt`:** rpds-py `2026.6.3` → `2026.9.1` (the
  cooldown hold lifts), cryptography `50.0.0` → `50.0.2` (50.0.0 was an oversight, not a hold), and pycparser `3.0` →
  `3.12`. The other six are unchanged and already latest, and OSV is clean for all nine. The gate and
  `bootstrap_toolchain.sh` use the new set, and the 2026-10-16 files stay because signed rows cite them.
- **Re-render with v1.1.3.** The constitution gains the self-contained "First-party toolchain group" rule on every
  surface. `@security`'s S-10 bullet becomes the toolchain-group form (`jlcatonjr/agentteams`, `baseagent`,
  `mathagents`), and the dangling "Rule 15" citations are gone. The exception registry records
  `toolchain_group_sequence: 1`, and the `AGENTS.md` install line moves to v1.1.3. Derived data is regenerated
  (memory index, build logs, vulnerability intel, bridge-manifest hashes).
- `scripts/check_toolchain.py`: the lock-format example now reads `v1.1.3`.

## 1.1.3 (tag `v1.1.3`, on `release/1.1`)

A patch release on `release/1.1` that pins agentteams **`v1.1.1`** (`2fe79c05`). Derived repositories take it with
`--researchteam-tag v1.1.3`.

- **agentteams pin: `v1.1.0` (`9b16fb54`) → `v1.1.1` (`2fe79c05`).** `toolchain.lock` and the `update`/`research`
  extras move together, and the lock records `agentteams.tag=v1.1.1`. agentteams 1.1.1 is 1.1.1-rc.2 plus release
  files: Claude teams get model defaults (orchestrator `claude-fable-5-2`, every other agent `opus`), and operator
  signing finds its key from the spec's `key_id`. Its declared dependencies are unchanged from 1.1.0. The re-render
  (Autosync run 43442533987, `--mode upstream`) changes no rule text on the four `@security` surfaces (only their
  vulnerability intel), moves the `AGENTS.md` install line, and regenerates derived data (build logs, memory index,
  bridge-manifest hashes, delivery receipt). S-10's local-repository carve-out for `jlcatonjr/agentteams` is present
  on all four.
- **Claude model defaults adopted.** All 33 front-mattered `.claude/agents/*.md` files gain a `model:` line
  (`orchestrator.md` → `claude-fable-5-2`, the others → `opus`) via infrastructureManagement's
  `scripts/operator/65-adopt-claude-model-lines.py`, one added line per file. `model` is a privileged key, so
  `--update --merge` only reports it, and researchteam's `--bridge-merge` does not re-emit the 18 bridge stubs
  (it does not pass the `bridge:copilot-vscode-to-claude:subagents` feature), so the lines are added once here and
  kept afterwards.
- **The autosync gate installs agentteams' signing backend, so CI renders keep operator-signed relaxations**
  (found 2026-11-12 in Autosync run 43324602697, PR #153).
  - **Defect:** the gate's vetted set left out `cryptography`/`cffi`/`pycparser`. Without them agentteams cannot
    verify an Ed25519-signed decision row, so it fails closed (correctly) and drops the relaxation that row
    authorizes. The CI render of the four `@security` surfaces therefore lost the S-10 carve-out for
    `jlcatonjr/agentteams` (registry entry active until 2027-02-01), while a `bootstrap_toolchain.sh` venv, which
    requires `cryptography`, kept it. The two renders differed, and every autosync PR over-tightened S-10.
  - **Fix:** `AGENTTEAMS_DEPS` is now the full vetted set from `docs/release/constraints-2026-10-16.txt`,
    including `cryptography==50.0.0`, `cffi==2.1.1` and `pycparser==3.0` (still `--only-binary=:all: --no-deps`).
    The gate fails before the regen if `cryptography` is not importable. Tests require the full set and cover the
    failure.

## 1.1.2 (tag `v1.1.2`, on `release/1.1`)

A patch release on `release/1.1`. It still pins agentteams `v1.1.0` (`9b16fb54`). Derived repositories take it with
`--researchteam-tag v1.1.2`, which re-syncs `scripts/agentteams_autosync_gate.sh`; the derived workflow's pip line
is a manual edit (see below).

- **Autosync installs are S-10 cooldown-safe** (request from infrastructureManagement, 2026-11-12; found in
  Batallion).
  - **Defect:** the autosync workflows (`.github/workflows/agentteams-sync.yml` and the derived
    `scaffold/agentteams-sync-derived.yml`) ran `pip install --upgrade pip`, which installs the newest pip. The
    gate also installed agentteams with its `jsonschema>=4.20` chain resolved unconstrained. In a derived
    repository under the 14-day cooldown, either could install a release published days earlier.
  - **Fix:** both workflows install `pip==26.2.2`. `scripts/agentteams_autosync_gate.sh` installs the vetted
    base set from `docs/release/constraints-2026-10-16.txt` (embedded as `AGENTTEAMS_DEPS`, because derived
    repositories do not receive that file) with `--only-binary=:all: --no-deps`. It then installs agentteams
    `--no-deps` and runs `pip check`. If an agentteams commit needs a dependency outside the set, the gate
    fails, so no PR opens and nothing unvetted is installed.
  - **Reach in existing derived repositories:** `researchteam update` syncs the gate script but not
    `.github/workflows/agentteams-sync.yml`, which a derived repository receives from
    `scaffold/agentteams-sync-derived.yml` only at `init`/`adopt` and owns afterwards. A release therefore
    brings the gate fix, but an existing repository keeps `pip install --upgrade pip` until its team edits that
    line to `python -m pip install "pip==26.2.2"` (the scaffold is the reference), or re-adopts.
  - **rpds-py hold:** the set keeps rpds-py at 2026.6.3, below the latest stable 2026.9.1 (past the cooldown
    since 2026-10-18, OSV none on 2026-11-12). See the vetting doc for the reason.

## 1.1.1 (tag `v1.1.1`, on `release/1.1`)

A patch release on `release/1.1`. It still pins agentteams `v1.1.0`. Derived repositories take it with
`--researchteam-tag v1.1.1`, which also re-syncs `scripts/check_toolchain.py`.

- **A final-release lock is no longer offered a release candidate** (agentteams row 691; found by
  infrastructureManagement on 2026-11-09).
  - **Defect:** `researchteam._release.newest_on_line` kept every tag on the line that sorted after the locked
    one, and `v1.1.1-rc.1` sorts after `v1.1.0`. So `check_toolchain.py --release-candidate` offered a stable
    lock a release candidate, and the autosync gate integrated it: baseAgent #324 moved `v1.1.0` to
    `v1.1.1-rc.1`. That broke the latest-stable rule.
  - **Fix:** from a final release, only final releases are candidates now. From a release candidate, newer
    candidates and finals stay eligible, and a newer final always wins over a candidate.
  - **New:** `is_prerelease(tag)`, and `newest_on_line(..., include_prerelease=None)`. The opt-in is
    `check_toolchain.py --release-candidate NAME --include-prerelease`, which the gate never passes. A
    deliberate rc pin (`--write-lock --tag name=<rc>`, with its own signed row) is unchanged.
  - **Compatibility:** `check_toolchain.py` applies the same rule itself when the installed researchteam is
    older than 1.1.1, so a re-synced script is safe on its own.
  - **Tests:** stable→rc refused, stable→newer stable past candidates, rc→final, rc→rc, the opt-in, and the
    older-package path.

## 1.1.0 (tag `v1.1.0`, on `release/1.1`)

The first stable 1.1 release, cut with agentteams `v1.1.0` in the coordinated order agentteams → researchteam →
derived repositories. It is `1.1.0rc5` plus the changes below. agentteams `v1.1.0` is its `v1.1.0-rc.17` code plus
release files only, and researchteam's checks against rc.17 (coordinated-release step RT-4) and v1.1.0 were green.
Derived repositories take it by pinning this tag (`--researchteam-tag v1.1.0`). It also carries every 1.0.4 fix
(merged forward, #146).

- **The pin moves to the signed agentteams `v1.1.0`** (tag object `093c38fd`, peeled `9b16fb54`; was
  `v1.1.0-rc.16`, `a036d09f`), in `toolchain.lock` (release-locked) and both extras. agentteams' declared
  dependencies are unchanged from rc.16 and rc.17, and OSV lists nothing for agentteams 1.1.0 or the installed set.
  The advisory researchteam self-pin moves to `903cfd1a`. Rows: `pin-agentteams-v1.1.0`.
- **Render:** researchteam is re-rendered on agentteams `v1.1.0`. One rule text changes, in the Copilot
  `@security` agent (`.github/agents`): the file-deletion rule no longer points to agentteams' Operator Decision
  Query, which is on agentteams `main` only and is deferred to 1.2 by operator ruling (2026-11-09). The Claude,
  Codex and Goose `@security` agents already lacked the pointer. Explicit operator confirmation for every
  deletion is still required. That agent's `security_rules_invariant` fence reads `v=20` where `main`'s render
  read `v=21`; the 1.1 line numbers that fence differently. S-10's local-repository carve-out is present on all
  four surfaces.
  The rest is churn: timestamps, vulnerability-watch data and build logs. Machine-path files are scrubbed (S-8).
- **infrastructure-management is an authorized manager team** (#148). `brief.json` lists
  `authorized_managers: ["infrastructure-management"]`, and each of the four surfaces' roster names exactly that
  team, with `is_management_repo` false and an empty directives ledger. A management directive still needs a valid
  HMAC signature and an exact, non-destructive task scope (C-4). The operator rendered and committed the roster.
  Rows: `management-roster-enroll:infrastructure-management`.
- **`researchteam init` names one signing step per agent surface** (#142). `materialize` gates each surface on
  its own decisions log, so the next-steps note now prints one `sign_security_decision.py --log <surface>/…` line
  for each surface the new project has, in place of a single clearance that left the others uncleared.

- **`researchteam init --adopt` scaffolds into a non-empty directory** (#59; masterTeacher handoff ticket 4.6). It is
  in 1.1.0 by operator ruling of 2026-11-06.
  - **Never overwrites.** No existing file is changed. `README.md`, `brief.json` and everything under `docs/` stay
    byte-identical.
  - **One exception.** An existing `CLAUDE.md` or `.gitignore` with no `researchteam:managed` block gets the block
    appended below its unchanged content, so the framework's rules reach Claude sessions and `update` can keep them
    current.
  - **Symlinks.** Paths that are symlinks are never written through. New files are created with
    `O_EXCL | O_NOFOLLOW`, so even a dangling link is refused at the moment of the write.
  - **Fails before writing.** A symlinked or non-regular key file, an unreadable `brief.json`, or a non-UTF-8
    `CLAUDE.md` / `.gitignore` is refused with nothing written. The `.researchteam` marker is written last, so a
    failed run can be retried.
  - **Git.** It runs `git init` only when the directory is not already inside a repository, and it never stages or
    commits, so uncommitted work is never swept into a scaffold commit. Inside an enclosing repository, `--remote`
    is ignored.
  - **Adopt report.** It lists the files added, kept, appended to and in conflict. It warns about kept files on paths
    the framework manages, because `researchteam update` or `materialize` will replace those later.
  - masterTeacher can retire `tools/bootstrap_researchteam.sh`, its move-aside workaround.

- **The bootstrap pins pip** (S-10; found by mathAgents, 2026-11-03). `scripts/bootstrap_toolchain.sh` upgraded pip to
  the newest release, which on 2026-11-03 was pip 26.3, published 2026-11-02 and so inside the 14-day cooldown. It now
  installs `pip==26.2.2`, the latest stable release past the cooldown, which has no OSV advisory. A test keeps the pin.

## 1.1.0rc5 (tag `v1.1.0-rc.5`, on `release/1.1`)

The fifth 1.1 release candidate. It moves agentteams to `v1.1.0-rc.16`, which closes the S-10 gap noted under 1.1.0rc4.
Derived repositories take it by pinning this tag (`--researchteam-tag v1.1.0-rc.5`).

- **The pin moves to the signed agentteams `v1.1.0-rc.16`** (tag object `75df2268`, peeled `a036d09f`), in
  `toolchain.lock` and both extras. In a governed project, rc.16 authorizes S-10's local-repository carve-out against
  `.github/agents` on every surface (agentteams #378/#379), so one signed `s10-cooldown-exempt:<owner/name>` row now
  covers Copilot, Claude, Goose and Codex. researchteam's Claude, Goose and Codex `@security` agents now name
  `jlcatonjr/agentteams` too. They use the registry entry the existing row created, so no new row was needed. The
  sandbox-relaxation, WASM-widen and adopt-merge gates stay per-surface. agentteams' declared dependencies are
  unchanged from rc.15, and OSV lists nothing for 1.1.0rc16. Rows: `pin-agentteams-v1.1.0-rc.16`.

## 1.1.0rc4 (tag `v1.1.0-rc.4`, on `release/1.1`)

The fourth 1.1 release candidate. It moves agentteams to `v1.1.0-rc.15`, which brings back the S-10 release cooldown
with two carve-outs, makes renders honour `frozen_surfaces`, and adds baseAgent's cross-surface fixes. Derived
repositories take it by pinning this tag (`--researchteam-tag v1.1.0-rc.4`).

- **The pin moves to the signed agentteams `v1.1.0-rc.15`** (tag object `167c8933`, peeled `9900fbd3`), in
  `toolchain.lock` and both extras (#139; supersedes the unmerged rc.14 pin #137 and the rc.12 autosync #136). Since
  rc.11 agentteams adds:
  - Project-Specific Rules projected onto every instruction surface;
  - `references/agent-surface-matrix.md` (now allowed in `validate_agentteams_update.sh`'s update scope);
  - a read-only `--query-index`;
  - renders that never write a path a frozen surface owns;
  - the restored S-10 cooldown (fence v20).
  
  Its declared dependencies are unchanged apart from the research extra's `pypdf>=6.21.2` floor, a CVE remediation
  since rc.12. The fresh OSV/GHSA search found nothing. Rows: `pin-agentteams-v1.1.0-rc.15`.
- **The S-10 release cooldown is in force again** (operator ruling 2026-11-03, signed row
  `s10-release-cooldown-restored`, #138), reversing the 2026-10-26 deprecation. It has two carve-outs:
  - **Vulnerability remediation.** A release that fixes a vulnerability that `pip-audit`, `npm audit`, `cargo audit` or
    an OSV.dev query found may be adopted inside the cooldown.
  - **Local interdependent repositories.** The cooldown does not apply to releases of this toolchain's own
    repositories.
  
  `docs/release-policy.md` is updated to match.
- **researchteam exempts `jlcatonjr/agentteams` from the cooldown** (`brief.json` `s10_cooldown_exempt_repos`, signed
  row `s10-cooldown-exempt:jlcatonjr/agentteams`; a 90-day sunset, re-checked on every render). Known gap: in rc.15
  only the Copilot surface's `@security` names it. The Claude, Goose and Codex surfaces read their own decision logs and
  still apply the cooldown to agentteams. That is stricter than intended, never looser. agentteams' fix (one canonical
  governance log for S-10) is planned for `v1.1.0-rc.16`, and needs no new row here.
- **Managed docs, from mathAgents' 2026-10-28 handoff.**
  - `docs/agentteams-update-policy.md` gains *Derived Repositories*: in a derived repo, an update is a refresh plus
    a projection to every unfrozen surface; a repo can state its own procedure in `CLAUDE.md` after the managed
    block; and a paused schedule means dispatch only.
  - `docs/retrieval-surfaces.md` no longer names one fixed bridge pair.

## 1.1.0rc3 (tag `v1.1.0-rc.3`, on `release/1.1`)

The third 1.1 release candidate. It moves agentteams to `v1.1.0-rc.11`, so derived repositories can take the
vulnscan-executor fixes by pinning this tag (`--researchteam-tag v1.1.0-rc.3`).

- **The pin moves to the signed agentteams `v1.1.0-rc.11`** (tag object `242add53`, peeled `19ba0943`), in
  `toolchain.lock` and both extras (#132, via the agentteams C1 rollout). rc.8–rc.11 change only vulnscan's remediation
  pipeline (daily agent, gateway, executor). They add goose 1.54 wire compatibility, repo aliases, `close-superseded`
  with a merge digest, the handoff gate, git-lfs, `agent.reasoning`, refusal of `includeIf.*` git config, and `open-pr`
  reuse of an open PR that carries the same change. The only rendered change is the `@security`
  agent's vulnscan S-VM text and the vulnerability-watch references. agentteams' declared dependencies are unchanged, and
  the fresh OSV/GHSA search found nothing (pypdf is now 6.21.4). Rows: `pin-agentteams-v1.1.0-rc.11`.
- **The autosync fails loudly instead of quietly (#127, #129; dependency-audit F-5).** The unlocked gate path fails when
  `git ls-remote` cannot resolve agentteams `main`. A detected change that opens no PR now fails the run, unless
  `create-pull-request` reports `none`. Existing derived repos copy the new workflow step from
  `researchteam/scaffold/agentteams-sync-derived.yml` by hand, because the scaffold isn't synced.
- **Other hardening from the 2026-10-27 open items (#127).** GitHub Actions are SHA-pinned in both workflows, and a
  test enforces it (F-4). `fetch_raw` and `fetch_tarball` retry once on a network error (F-9). `doctor` reports pandoc
  and the scholarly tooling, for information only (F-2, P3-12). The literature-library suite and an end-to-end
  retrieval smoke test run under pytest (P1-2), and `conflict-log.csv` is seeded (OI-2026-10-19-11).
- **Docs and housekeeping.** The stale-fact audit was refreshed for the 1.1 line (#124). The orphaned
  egyptian-cosmopolitanism plans were removed (#125). The 1.0.3 entry was merged forward (#128).

## 1.1.0rc2 (tag `v1.1.0-rc.2`, on `release/1.1`)

The second 1.1 release candidate. It moves agentteams to `v1.1.0-rc.7` and retires the S-10 release cooldown, so derived
repositories that pin this tag get the deprecation (their gates refuse rc.7 until researchteam pins it).

- **The pin moves to the signed agentteams `v1.1.0-rc.7`** (tag object `2c6b25fc`, peeled `decbcda8`), in `toolchain.lock`
  and both extras, by the autosync gate (`--write-lock --sync-extras`). It brings agentteams #299 (the S-10 cooldown is
  deprecated; the rendered `@security` rule is now fence v17 on every surface) and #296 (root-brief `sandbox/` sync;
  researchteam's `sandbox/` files already match the rc.7 templates). Rows: `pin-agentteams-v1.1.0-rc.7`.
- **The S-10 release cooldown is deprecated** (operator ruling 2026-10-26, signed row `s10-release-cooldown-deprecated`).
  A release is adopted once its exact version passes the known-vulnerability search and, for a release-key tag, the
  signature checks; every pin row still records that search. `docs/release-policy.md` and the vetting record are
  updated; the earlier cooldown exemptions stay in the log as history. This closes the `research` extra's cooldown gap
  noted under 1.1.0rc1; its packages had no OSV advisory.
- **Correction to the signed `s10-release-cooldown-deprecated` row:** its text says the deprecation ships in agentteams
  "v1.0.3+/v1.1.0-rc.7+". On the 1.0 line it ships in **v1.0.4** (v1.0.3 predates the ruling and carries only #296).
  The row is signed and stays as is; what it authorizes is unaffected. Pin v1.0.4 or later for the deprecation on 1.0.

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

## 1.0.4 (tag `v1.0.4`, on `release/1.0`)

A patch release on `release/1.0`. It moves agentteams to `v1.0.7` and brings the 1.0 line up to the S-10 policy the
1.1 line adopted in 1.1.0rc4 and rc5. Derived repositories that stay on 1.0 take it by pinning this tag
(`--researchteam-tag v1.0.4`).

- **The pin moves to the signed agentteams `v1.0.7`** (tag object `37531c96`, peeled `8b934600`; was `v1.0.0`,
  `cc5b8c9e`), in `toolchain.lock` and both extras. agentteams' declared dependencies are unchanged from `v1.0.0`,
  and OSV lists nothing for the installed set. The advisory researchteam self-pin moves to `v1.0.3` (`2764f7c8`).
  Rows: `pin-agentteams-v1.0.7`.
- **S-10 cooldown restored, with the local-repository carve-out.** The 14-day release cooldown is back in force.
  It never blocks fixing a vulnerability, and it does not apply to releases of the operator's local,
  interdependent repositories. `brief.json` now lists `s10_cooldown_exempt_repos: ["jlcatonjr/agentteams"]`. The
  decisions log and `exception-registry.json` now match `main`'s: the log is append-only, and it already holds
  the signed `s10-release-cooldown-restored` and `s10-cooldown-exempt:jlcatonjr/agentteams` rows, so neither is
  signed again. The `@security` agents on all four surfaces (Copilot, Claude, Goose, Codex) name
  `jlcatonjr/agentteams` in Rule S-10, and a HALT in any one surface's own log still removes it there.
- **The bootstrap pins pip** (#141). `scripts/bootstrap_toolchain.sh` installs `pip==26.2.2` in place of the
  newest pip, which on 2026-11-03 was inside the cooldown.

## 1.0.3 (tag `v1.0.3`, on `release/1.0`)

A patch release on `release/1.0` that backports two fixes from `main`. The agentteams pin is unchanged (`v1.0.0`,
`cc5b8c9e`), so there is no new pin row. The agentteams #249 fix (the Codex write-policy fence) is not in any
agentteams 1.0.x release yet, so it goes in a later 1.0.x (operator ruling 2026-10-27).

- **Frozen Goose owns its extras (#98).** agentteams' Goose emitter writes `.goosehints`,
  `scripts/goose-run-resilient.py`, `scripts/goose-openrouter-route-proxy.py` and
  `scripts/goose-coordination-mcp.py` outside `.goose/`. researchteam skipped the Goose render and every bridge
  while `goose` is frozen, so nothing wrote these files. A frozen `goose` now owns them too, so a write to any of them fails closed.
- **The release trust root accepts only the release key (#102).** The "Release trust root" step in both
  `.github/workflows/agentteams-sync.yml` and the derived scaffold wrote whatever `AGENTTEAMS_ALLOWED_SIGNERS`
  held. It now requires exactly one `<principal> namespaces="git" <type> <key>` line whose key matches the
  pinned release-key fingerprint (`RELEASE_FP`), and fails closed otherwise. Rotating the key is a reviewed edit
  to `RELEASE_FP`, never a secret change. Existing derived repos must hand-copy the step from
  `researchteam/scaffold/agentteams-sync-derived.yml`, because that file isn't synced
  (`docs/agentteams-update-policy.md`).

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
