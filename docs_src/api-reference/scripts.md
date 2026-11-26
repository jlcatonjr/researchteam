# Helper scripts — ResearchTeam

Command-line scripts under `scripts/` that researchteam ships to derived repositories as layer-2 managed files (see [`manifest.md`](manifest.md)). `check_toolchain.py` and `sign_security_decision.py` are in the framework set every repo receives; `build_literature_library.py`, `query_literature_library.py` the four term-index scripts and the survey toolkit (`scripts/survey/`) are in the scholarly set. This page covers their arguments, environment variables, exit codes and output files.

> *Sources: `scripts/check_toolchain.py`, `scripts/build_literature_library.py`, `scripts/query_literature_library.py`, `scripts/sign_security_decision.py`, `scripts/term_index_engine.py`, `scripts/build_term_index.py`, `scripts/check_term_index.py`, `scripts/query_term_index.py`, `scripts/survey/`*

> **Stability.** The supported interface is each script's command line ([Bridge reference](../bridge-reference.md)); internals may change between releases.

---

## `check_toolchain.py`

> *Source: `scripts/check_toolchain.py`*

Checks whether the installed `researchteam` and `agentteams` are the commits pinned in `toolchain.lock`, and optionally whether upstream `main` has moved past the pin. It prints short `[toolchain] …` lines. Used by the SessionStart hook in `.claude/settings.toolchain.example.json` (its stdout becomes session context), by `scripts/bootstrap_toolchain.sh`, and by `researchteam doctor`. The autosync gate uses `--write-lock` to record what a green sync was verified with. Standard library only.

### Usage

```text
python3 scripts/check_toolchain.py [--python PATH] [--no-remote] [--strict]
                                   [--write-lock [--tag NAME=TAG ...] [--sync-extras]]
                                   [--release-candidate NAME [--include-prerelease]]
                                   [--verify-tag NAME TAG]
```

| Argument | Meaning |
|----------|---------|
| `--python PATH` | Interpreter to inspect. |
| `--no-remote` | Skip the comparison with upstream `main` (`git ls-remote`). |
| `--strict` | Exit 1 when a pin does not match (see exit codes). |
| `--write-lock` | Record the installed commits in `toolchain.lock`. |
| `--tag NAME=TAG` | With `--write-lock`: the verified release tag that the installed `NAME` commit is. Repeatable. `NAME` is `researchteam` or `agentteams`. |
| `--sync-extras` | With `--write-lock`: also point every `agentteams … @ git+https://github.com/<lock repo>[.git]@<ref>` requirement in the repository's own `pyproject.toml` at the new agentteams commit (only the ref changes; a requirement without a ref gains one). The autosync gate passes it in `--mode upstream` only: a derived repository's `pyproject.toml` is project-owned. A requirement from another repository is never rewritten, and then the lock is not written either. |
| `--release-candidate NAME` | Print the newest tag on `NAME`'s locked release line if it is newer than the locked tag; prints nothing when `NAME` is not release-locked. From a final-release lock only final releases are candidates (latest-stable rule); from a release-candidate lock, newer candidates and the final are. With an installed researchteam older than 1.1.1 the script applies the same rule itself. |
| `--include-prerelease` | With `--release-candidate`: also offer release candidates to a final-release lock. The autosync gate never passes it; adopting a candidate still needs a recorded `@security` clearance. |
| `--verify-tag NAME TAG` | Verify `TAG` in `NAME`'s pinned repository and print its peeled commit. |

`--release-candidate` and `--verify-tag` are handled first and ignore the other options. Otherwise, `--write-lock` takes precedence over the default check.

**Interpreter selection** (first match wins): `--python PATH`; `<repo>/.venv/bin/python`; the interpreter behind the `researchteam` on `PATH`, read from its shebang (direct path, `/usr/bin/env` form, or pip's `sh`/`bash` trampoline). Package records are read by running that interpreter with `-I` (isolated mode).

**Repository root** is the parent of the script's own directory, not the working directory. `toolchain.lock` and `pyproject.toml` are read from there.

### `toolchain.lock` format

One pin per line. Only whole-line `#` comments are allowed: an inline `#` after a value becomes part of that value. The `agentteams.tag` line below is optional; its presence makes the `agentteams` pin release-locked.

```text
researchteam=jlcatonjr/researchteam@<40-hex sha>
agentteams=jlcatonjr/agentteams@<40-hex sha>
agentteams.tag=v1.0.0
```

A pin is valid only if its repository is the allowed one (`jlcatonjr/researchteam` or `jlcatonjr/agentteams`) and its commit is 40 lowercase hex characters. A pin with a `<name>.tag` line is release-locked: `--write-lock` moves it only to a verified tag on the same `vX.Y` line that is not older than the locked tag, never to an untagged commit. A new lock gets a fixed comment header followed by the two pins (and any tags). An existing lock is rewritten in place: every comment (a project's own policy header, notes between pins) keeps its text and position, pins keep their order, a missing pin or tag line is added, and the tag line of a pin that is no longer release-locked is removed.

### Default check

1. No `toolchain.lock`: prints `[toolchain] no toolchain.lock yet; …` and exits 0.
2. For every git-installed `agentteams` requirement in the repo's `pyproject.toml` whose repository or ref differs from the `agentteams` pin, prints `[toolchain] MISMATCH: …`.
3. No interpreter found, or it cannot be inspected: prints a line suggesting `bash scripts/bootstrap_toolchain.sh`.
4. For each package: a problem if the pin is invalid, the package is not installed, its install records no commit (index or plain local-folder install), or its commit differs from the pin. A match from an editable checkout with uncommitted changes is a note. For valid, installed, not-release-locked pins, unless `--no-remote`, a note when upstream `main` differs from the pin.
5. Prints `[toolchain] OK: researchteam and agentteams match toolchain.lock (<python>)` when there are no problems and no notes. Otherwise prints each problem as `[toolchain] BEHIND: …` (pyproject mismatches were already printed), each note as `[toolchain] note: …`, and, if there were problems, the bootstrap hint.

An install's commit comes from its `direct_url.json`: `vcs_info.commit_id` for a git install, or `git rev-parse HEAD` in the checkout for an editable install (with `git status --porcelain --untracked-files=no` for the dirty flag).

### Exit codes

| Mode | 0 | 1 | 2 |
|------|---|---|---|
| Default | Always, unless `--strict` | `--strict` and a problem was found, or `--strict` and no interpreter could be found or inspected | — |
| `--write-lock` | Lock written (prints `updated` or `unchanged` with the short commits) | Interpreter cannot be inspected; a package is not installed; a package has no recorded 40-hex commit or is from a dirty checkout; a pin would name a disallowed repo; a release lock would be broken or a `--tag` cannot be verified; with `--sync-extras`, an extra that cannot follow the lock (`MISMATCH` lines) | A `--tag` value is malformed |
| `--release-candidate` / `--verify-tag` | Answer printed (or no candidate) | `researchteam._release` is not importable; `NAME` has no valid pin; release verification failed | — |

argparse usage errors exit 2.

### Output files

- `toolchain.lock` at the repository root, written only with `--write-lock`.
- `pyproject.toml` at the repository root, only with `--write-lock --sync-extras` and only when an extra's ref changes.

---

## `build_literature_library.py`

> *Source: `scripts/build_literature_library.py`*

Builds a per-project literature library from the project's bibliography. One record is kept per BibTeX entry, and the indexed text of each record (title, relevance summary, abstract) is turned into raw term counts by a standard-library tokenizer. It does no network access and is deterministic: the same input produces byte-identical output. See `docs/literature-library-protocol.md`.

Limits stated by the script: records are written with `verification_state` set to `"UNVERIFIED — no human resolution performed"`; vectors are computed by code, not authored by a model; the layer is lexical TF-IDF, and the semantic/dense layer is a stub; similarity is for navigation, not evidence.

### Usage

```text
python3 scripts/build_literature_library.py <project-name-or-path>
```

Exactly one positional argument is accepted. It is resolved as follows: if it is a directory containing `references/`, it is used; otherwise the script searches recursively under `<root>/Projects/` and then `<root>/.projects/` for a directory with that name that contains `references/`.

### Environment

| Variable | Effect |
|----------|--------|
| `RT_ROOT` | Repository root used for project lookup. Default: the parent of the script's directory. |

### Behaviour

- Reads every `references/*.bib` file (sorted). The first entry seen for a key wins; `@string`, `@comment` and `@preamble` are ignored.
- Existing records in `literature.jsonl` are kept, with `title`, `source_url` and `doi` refreshed from the `.bib` when the `.bib` has a value. Records whose key is no longer in the `.bib` are dropped.
- A new record is seeded with `relevance.summary` set to the entry's `note` field, `relevance.source` set to `seeded-from-bib-note` (or `unseeded` when there is no note), `deemed_by` and `investigation` set to `null`, empty `tags`, and `verification_state` set to `"UNVERIFIED — no human resolution performed"`; existing records keep their stored `verification_state`. `source_db` is never inferred from the URL.
- Every record gets `record_text_sha256`, the SHA-256 of its indexed text.
- Tokenizing lower-cases the text, removes `http(s)://` URLs, splits on any character other than ASCII `a-z`, and drops tokens shorter than 3 characters, stopwords and URL-related words.
- Prints a summary with the record count, the number seeded this build, and the number with a relevance summary under 8 words.

### Output files

All under `<project>/references/library/` (created if needed):

| File | Contents |
|------|----------|
| `literature.jsonl` | One JSON record per source, sorted by key, keys sorted. |
| `term-vectors.jsonl` | One line per record: `key`, `n_terms`, and raw `terms` counts. IDF is not stored; it is computed at query time. |
| `library-manifest.json` | `artifact_type` (`literature-index`), `schema_version` (`1.0`), `project`, `vector_model_id` (`researchteam-tfidf-v1`), `vector_method` (`lexical-baseline`), `vector_state`, `record_count`, `seeded_this_build`, `source_bib_sha256`, `records_sha256`, `inclusion_criterion`, `coverage_statement`, `ceiling_banner`. |

### Exit codes

| Code | Cause |
|------|-------|
| 0 | Library written. |
| 1 | Wrong number of arguments (usage message); no matching project with a `references/` directory; no `.bib` file under `references/`. |

A malformed line in an existing `literature.jsonl` raises `json.JSONDecodeError`.

---

## `query_literature_library.py`

> *Source: `scripts/query_literature_library.py`*

Ranks the records of a library built by `build_literature_library.py` against a free-text query. It loads `term-vectors.jsonl`, computes IDF over the library as `ln((1 + N) / (1 + df)) + 1`, weights and L2-normalizes the record and query vectors, and sorts by cosine similarity (ties broken by key). Results are navigation candidates only; they are not evidence. It imports the tokenizer and project resolution from `build_literature_library.py`, so both scripts tokenize the same way.

### Usage

```text
python3 scripts/query_literature_library.py <project-name-or-path> "<query text>" [-k N]
```

| Argument | Meaning |
|----------|---------|
| `<project-name-or-path>` | Resolved as in `build_literature_library.py`. |
| `<query text>` | All remaining positional arguments, joined with spaces. |
| `-k N` | Maximum number of results. Default `8`. `N` must be a whole number, at least `1`. |

The arguments are read from `sys.argv` directly (no argparse). The first `-k` and the one argument after it are removed by position, so a query word or project name equal to the `-k` value is kept. A missing or non-integer value prints `-k needs a whole number`, and a value below 1 prints `-k must be at least 1`; each is followed by the usage line on stderr, and the script exits 2.

The usage line (the `USAGE` constant):

```text
usage: query_literature_library.py <project> "<query>" [-k N]
```

### Environment

| Variable | Effect |
|----------|--------|
| `RT_ROOT` | Repository root used for project lookup. |

### Output

Prints a header with the query and project, a navigation-only notice, then one line per result with a positive score: `  <score to 3 decimals>  [<key>] <first 70 characters of the title>`. With no positive score it prints `(no lexical overlap — try different terms; this is not evidence of absence)`. It writes no files.

### Exit codes

| Code | Cause |
|------|-------|
| 0 | Results printed, including the no-overlap case. |
| 1 | No matching project; no `references/library/term-vectors.jsonl` (asks you to run the build script first). |
| 2 | Usage error, with the usage line on stderr: fewer than two positional arguments, or a missing, non-integer or below-1 `-k` value. |

### Functions

| Name | Behaviour |
|------|-----------|
| `query(libdir: Path, q: str, k: int) -> tuple[list[tuple[str, float]], dict]` | `(hits, lit)`: up to `k` `(key, score)` pairs with a positive score, best first, and the loaded literature records keyed by citation key. |
| `USAGE` | `'usage: query_literature_library.py <project> "<query>" [-k N]'`. |
| `_usage(msg: str = "") -> None` | Print `msg` (when given) and `USAGE` to stderr, then `sys.exit(2)`. |

---

## `term_index_engine.py`, `build_term_index.py`, `check_term_index.py`, `query_term_index.py`

> *Sources: `scripts/term_index_engine.py`, `scripts/build_term_index.py`, `scripts/check_term_index.py`, `scripts/query_term_index.py`*

The term register and its occurrence index. `term_index_engine.py` is researchteam's adapter layer over the pinned agentteams term-index core in `scripts/term-index-core/` (register validation, document scope, matching, rendering and the comparison with the committed index are the core's); it is imported, not run, and it writes nothing. Importing it first runs `check_term_core.py`'s offline check, and a copy that does not verify stops every command with exit 2. `build_term_index.py` holds the commands that write. All three commands import the engine, so they read a register and match text the same way. Standard library only; no network calls and no child processes. The finding codes, the register format and the ceiling are defined in the [Term Index protocol](https://github.com/jlcatonjr/researchteam/blob/main/docs/term-index-protocol.md) and are not repeated here.

### Usage

```text
python3 scripts/build_term_index.py build [project]
python3 scripts/build_term_index.py init <project>
python3 scripts/build_term_index.py hook            # Claude Code hook; JSON payload on stdin
python3 scripts/check_term_index.py [project]
python3 scripts/query_term_index.py <project> "<label, variant or id>" | --list
```

| Argument | Meaning |
|----------|---------|
| `project` | A project's path under `Projects/`, or its directory name when that is unique. Omitted: every project (`build` takes every project that has a register). |
| `init <project>` | Writes a starter `terminology/terms.json` in an existing directory under `Projects/`. Refuses when `terminology/` already holds files or is not a plain directory, and refuses a directory the index never searches: one that only holds other projects, a folder inside a project, a path through a symbolic link, a pruned name, or one more than twelve levels down. |
| `hook` | Reads `tool_input.file_path` or `tool_input.notebook_path` from the payload, only to choose which project to rebuild. A payload with no path (a shell command, a session start) rebuilds every project whose files changed. A malformed payload, or a path outside every project, does nothing. A payload whose `tool_input` is not an object counts as having no path. |
| `--list` | Lists every registered term with its occurrence count. |

### Environment

| Variable | Meaning |
|----------|---------|
| `RT_ROOT` | Repository root to use in place of the one inferred from the script's location (test harness). |
| `TERM_INDEX_ADVISORY=1` | `check_term_index.py` reports defects and exits 0, printing an `ADVISORY MODE` line. The bridge `validate` command clears it. |

`check_term_index.py` also reads `term_index_require` from `.researchteam`.

### Exit codes

| Script | 0 | 1 | 2 |
|--------|---|---|---|
| `build_term_index.py build` / `init` | Done | A register defect, or nothing written | Usage error, project not found, or an unreadable or unwritable path |
| `build_term_index.py hook` | Done, or nothing to do | — | Feedback for the agent on stderr: a defect in the file just edited |
| `check_term_index.py` | No defect, or advisory mode, or nothing to check | At least one defect (an unreadable register is one) | Usage error, project not found, an unreadable document or `.bib`, or an invalid `term_index_require` value |
| `query_term_index.py` | Found | No such term, or no usable register | Usage error, project not found, or an unreadable document |

Every command above also exits 2, printing the core check's lines, when the pinned core does not verify or cannot load.

### Output files

All under `<project>/terminology/`: `term-index.json` (manifest: generator version, SHA-256 of the register and of each indexed document), `index/<document path>.json` (that document's occurrences, one per line) and `glossary.md` (a reading view of the register). They hold no timestamps and no absolute paths, so the same inputs give the same bytes. `check_term_index.py` and `query_term_index.py` write nothing.

---

## `check_term_core.py` and `scripts/term-index-core/`

> *Source: `scripts/check_term_core.py`*

`scripts/term-index-core/` holds agentteams' `term_index.py` and `_term_text.py`, byte for byte as the signed agentteams tag has them, its `LICENSE` (MIT), and `PINNED.json`: the tag, its peeled commit and each file's sha256. `check_term_core.py` is the offline check of those bytes and the loader the engine imports. Standard library only; no network, no child process, nothing written.

```text
python3 scripts/check_term_core.py        # or: bash scripts/claude_researchteam_bridge.sh term-core-check
```

| Exit | Meaning |
|------|---------|
| 0 | Every listed file matches its hash, and no unlisted code file is in the directory. |
| 1 | A file is mismatched, missing, a symbolic link or not a regular file, or a code file (`.py`, `.pyc` and the like) is not listed. |
| 2 | `PINNED.json` is missing, unreadable or malformed, or the directory is missing or a symbolic link. |

Output: one line per file (`[term-core] OK <path>`, `[term-core] MISMATCH <path>: sha256 <12 hex>, expected <12 hex> (agentteams <tag> <upstream path>)`, `MISSING`, `LINK`, `REFUSED`, `UNLISTED`), then a summary, `[term-core] SUMMARY agentteams <tag> (<12-hex commit>): <n> of <m> files match; ...`, whose prefix is stable (`researchteam doctor` reads the tag from it). A failure adds the repair: restore from git, or upgrade researchteam first and then run `researchteam update` (an older researchteam does not sync this directory).

A pass proves the copy matches the manifest, not that the manifest matches upstream; that is `python -m researchteam._term_core_upstream`, against the signed tag (see [`term-core-upstream.md`](term-core-upstream.md)).

---

## `scripts/survey/`: the survey toolkit, step A

> *Source: `scripts/survey/`*

The specification validator, the gates and the ledger checks of the position-survey contract
([`docs/survey-toolkit.md`](https://github.com/jlcatonjr/researchteam/blob/main/docs/survey-toolkit.md), version 1,
sections 3, 6.1, 6.2 and 7). Standard library only, Python 3.10 to 3.13; no network, no clock. The only child
process is `survey_verify.py`'s agentteams check (step F).
The modules import one another by file name, and each command puts its own folder on `sys.path`, so the bridge runs
them with `python3 -B -I`.

| File | Role |
|------|------|
| `survey_core.py` | Findings (error id, place, message), folded text (rule 1.10), canonical JSON and the manifest's file hashing (6.1), the repository root, the path rule (1.6), the command-line helper |
| `survey_spec.py` | The rule table of `study.json`, the shape walker, the checks beyond shape (`SEMANTIC_RULES`), and the loader that also checks files and gate coverage |
| `survey_ledger.py` | The structural checks of the ledger folder (6.2) that need no signature |
| `survey_gates.py` | The gate list, the manifest builder, the three states, sign-off verification (`verify_signoff`, step F), `require_gate` and `stage_decision` (runs or refuses, 6.1) |
| `survey_schema.py`, `study.schema.json` | The JSON Schema (2020-12) of `study.json`, generated from the rule table; `--check` exits 1 when the tracked file differs |
| `survey_validate.py`, `survey_status.py`, `survey_manifest.py` | The three commands |
| `survey_tables.py` | Step B. The shared CSV reader of section 4, the bucket-table checks and bucketer (4.8), and the year and period rule |
| `survey_attribution.py` | Step B. The attribution file's checks (4.3) |
| `survey_provenance.py` | Step B part 2. The provenance record of 4.6 (`make_record`, `gate_entries`, `check_record_shape`, `check_current`, which also treats a recorded-absent input that is now there as stale), where an output may go (`check_output_target`: only inside the study's own folder, never a declared or covered file or inside a declared folder, not in the ledger folder, and never under `.git`, `.github` or a team location) and the one way outputs are written (`write_all`: every target checked, temporary files in the same folders, mode 0644, every target checked again, then `os.replace` in order; on Linux and macOS relative to a descriptor on the checked folder) |
| `survey_identity.py` | Step B part 2. The project's persons, the overrides file's checks (4.4), the registry's rows, stop words and candidates |
| `survey_registry.py` | Step B part 2. The `survey-registry` command |
| `survey_rows.py` | Step B part 2b. The `survey-rows` command: the batch merge, and `--draft-exceptions` |
| `survey_codes.py` | Step C. The codes and adjudications files' checks (4.2) and raw agreement between passes A and B |
| `survey_agreement.py` | Step C. The `survey-agreement` command |
| `survey_final.py` | Step C part 2. Final codes (4.2 lines 397-400; operator decisions D3, D4), the rollup's rules and columns (lines 403-422; D5), placing a path in the study's folder, and reading a merged id as its person through the overrides file's recorded merges (`merged_persons`, `authors`; step D ruling D, shared by the rollup and the frame) |
| `survey_finalize.py`, `survey_rollup.py` | Step C part 2. The `survey-finalize` and `survey-rollup` commands; `survey_finalize.py` also holds the final-codes loader both later stages share (`load_final`) and the writer of several outputs at once (`write_outputs`) |
| `survey_cells.py` | Step D. The frame of a passage or work study (4.7): cells, columns, outcome cells, the period, attribute evidence, the cell checks, the cells `not-on-question` leaves out, and the passage list |
| `survey_changelog.py` | Step D. The frame-change log (4.4): its entries' shape, the frame's hash, the check that the frame is the last entry's, and the entry a changed frame needs |
| `survey_frame.py` | Step D. The `survey-frame` command |
| `survey_evidence.py` | Step B. The evidence row checks with the rule ids of 4.1, the legacy exceptions, the forbidden vocabulary (5.3), the registry read, the receipt-citation check (5.4) and the re-find seam (`refind_quotation`, step G) |
| `survey_verify.py` | Step F: sign-off verification through agentteams, reached only as a child process (`sys.executable -I -c` with one fixed snippet, an allowlisted environment and an empty `HOME`); it imports no agentteams code |

### The identity registry (step B part 2)

`survey-registry <project>` builds `identity.registry` from the persons of the evidence file and, in a passage or
work study, the attribution file (4.4), applying the overrides file: a `link` sets `identity_id`, a `merge` folds the
alias into its target's row (`merged_from`, `;`-separated; the registry holds those ids too). It writes the
registry, then its record (`<registry>.provenance.json`, canonical JSON of 4.6's fields), last; no state an
interruption leaves reads as built wrongly. Without a vantage module the identity source is the project's own
persons (5.2), so every override target is a project person and `display_name` is the `person_id`. Override errors:
`overrides-columns`, `overrides-empty`, `overrides-decision`, `overrides-alias`, `overrides-target`,
`overrides-self`, `overrides-repeat`, `overrides-second`, `overrides-conflict`, `overrides-chain`,
`overrides-shared-identity`; `survey-validate` reports them too. A registry value with a control character or line
break, or a format character such as a bidirectional override, refuses the build (`registry-value`). A merge alias must be an id of the project's rows; the registry holds merged ids, so rows keep it. `--candidates` lists the undecided pairs of persons whose folded names are
equal (`exact`) or share a word that is not a stop word (`similar`), at most 1000; a pair an override row names is
decided and not listed. It writes nothing. A study with a vantage module (`identity-vantage`) or plugin evidence is
refused: this version does not load project code.

### Codes and agreement (step C, part 1)

`survey-validate` also checks each coded outcome's codes file and adjudications file (4.2). Codes rows: the pass is
`A`, `B` or `final`; the outcome is declared with source `codes` and names this file; the code is a level code, an NA
code or the missing value; a code other than the missing value has evidence and a basis (`own` or `reported`); a
reported code has a reporter; every evidence id exists and belongs to the coded unit's author; one row per unit,
outcome and pass; a `final` row needs both passes unless it is the adjudication of a missing pass; every row has a
coder (rule 1.3); the unit is an attribution unit (or, in an author study, a registry person) and `person_id` its
author. Adjudications: checked like codes rows, with a coder and a note; none for a unit on which A and B agree; where a
pass is missing the note begins `missing pass: A, ` or `missing pass: B, ` and gives a reason; one per unit. Ids:
`codes-*`, `adjudication-*`. `survey-agreement <project>` prints, per coded outcome in declared order,
`<outcome>: n=… raw=… kappa=… AC1=…` and the units with one pass only, by the operator's definitions of 2026-11-25
(`survey_codes.statistics`): over the units with both passes, every code its own category, κ unweighted, AC1 with q
the number of codes the specification allows; exact fractions, three decimals rounded half to even, `undefined` where
a statistic is. It writes nothing. Finalising and the rollup are not in this version.

### Final codes and the rollup (step C, part 2)

`survey-finalize <project> --out <path>` writes the final codes of every coded outcome to a file of its own (operator
decision D2), with a provenance record beside it listing every file read (those read only to check them included),
gate S5 and the legacy exceptions (D6). Neither this command nor `survey-rollup` reads a fetch receipt: they run the
row checks without the 5.4 citation check, since no final code or rollup cell rests on a receipt; `survey-validate`,
`survey-rows` and the later quotation step keep that check. The passes file is only read. For each unit of
the study (the attribution file's units; in an author study the registry's persons) and each coded outcome: agreed
passes give pass A's row with `coder` `agreed`, `level` empty and `note` `agreed` or `agreed; evidence differed` (the
evidence ids compared as sets); a disagreement, or a unit with one pass, the adjudication's coder, basis, reporter,
evidence and note (D3); without one, or for a unit with no pass at all (D4), nothing is written and the units are
listed (`final-no-adjudication`, `final-no-pass`). A `final` row the codes file already holds must equal the derived
row cell for cell; one that differs (`final-differs`) or has no derived row (`final-extra`) refuses (O2). Rows are in
the outcomes' declared order, then code-point order of `unit_id`.

`survey-rollup <project> <final file> --out <path>` reads a `survey-finalize` output whose bytes are what
`survey-finalize` gives from the study's inputs, in every status, and whose record matches its inputs (in a draft
study a record that does not is reported and the stage runs; O3), and rolls its final codes up to the author: only
counted, not excluded units, each counted for its author, a merged id read as the surviving person it was merged
into through the overrides file's recorded `merge` rows (the rows stay as written; the frame reads ids the same
way); NA codes and the missing value skipped; `single-code` (a conflict is an error,
`rollup-conflict`), `mixed-if-conflict`, `max-order`, `any-present` (two codes at the deciding `order` are an error
too); nothing left gives the missing value. Columns: `person_id`, each `unit.rollup_by` key, `author_kind`, each
rolled-up outcome and `<outcome>__types` where `unit.rollup_types` is set (the distinct values, in the order the
attribute declares its levels, joined with `;`; O1). Rows are in code-point order of `person_id`, then of the
`rollup_by` values. It refuses in an author study. Its record lists every file read: the final file and its record,
and every file finalising lists. Both commands write through `check_output_target` and `write_all` with every file
read guarded; an output named as a record (`.provenance.json`) is refused, and so is a record path holding anything
but this output's record; an existing output is "unchanged" when identical and refused otherwise.

### The frame (step D, part 1)

`survey-frame <project> <final file> --out <frame> --passages <path>` writes the frame of a passage or work study and
its passage list (4.7). Where the study declares `not-on-question`, it also writes the dropped list, at the frame's
path with `.csv` replaced by `.dropped.csv`; that list has its header only when nothing is dropped. Each output has a
provenance record listing gates S5 and S6, every file read (the frame-change log among them) and the legacy
exceptions. Its input is a current `survey-finalize` output, checked as the rollup checks it.

- A cell is an author and one value of each `unit.rollup_by` attribute, made by its counted passages. A merged id
  counts as the person it was merged into, through the overrides file's recorded merges, as in `survey-rollup`; the
  rows stay as written.
- Columns, outcome cells, the period and attribute evidence follow 4.7, and every cell is checked before anything is
  written.
- The frame must be the frame-change log's last entry (4.4). Without the change arguments, nothing is written and
  the entry the log needs is printed.
- With `--change-id`, `--date`, `--reason` and `--results-seen yes|no`, the entry is appended in the same guarded
  write as the frame and its lists. The author gives the four facts; the tool computes the hash and the unit lists.
  An id already in the log is refused, and so is a log whose last line has no line feed. The log grows by exactly one
  line, has no record of its own, and every record lists it as it stands after the append. With those arguments and
  an unchanged frame, no entry is written.
- When the log's last entry names the new frame, the command replaces its own earlier frame, passage list and
  dropped list at the same paths. Only files whose record beside them is this command's, for this study, are
  replaced. Every other command still refuses to write over an output with other bytes
  (`write_outputs(..., replace=True)` is passed only here).
- With an unchanged frame, a changed passage list or dropped list is also replaced without a new log entry: the log's
  last entry still names the frame, and the log follows the frame file alone (4.4, line 472).
- It refuses in an author study, where a bucketer is a plug-in, where the identity source is a vantage module, and
  where the evidence is in a plug-in format.
- It does not run post-steps (4.5): it checks each step's path, then the gates that cover it, and refuses. Running
  them is part 2; when it comes, it will not be a sandbox.
- Frame, passage list and dropped list are CSV with every cell quoted and LF line endings. The frame and the dropped
  list are in code-point order of `unit_id`, the passage list in evidence-file order.

### The batch merge (step B part 2b)

`survey-rows <project> <batch>` merges a batch of evidence rows into the evidence file (4.1, 4.4). The batch is a
path relative to the study's folder (or `repo:`-rooted) that must lie inside it, be a regular file other than the
evidence file, and have exactly the evidence columns; an empty batch is refused (`batch-place`, `batch-empty`, and
the row-file ids). The merged file is the evidence file's bytes as they are with the batch's rows appended in batch
order; every check of 4.1, 4.3 and 4.8 runs over it, no legacy exception covers a batch row, and a merge into a
`plugin` format is refused. The registry must be built (its record current) and a build over the merged file must
give its present rows, which also finds a registry edited by hand. Then the evidence file is written and the
registry's renewed record, last; an interruption between them leaves the registry not built. Row files are read as strict CSV; the merged file must read back, cell for cell, as the file's rows and then the batch's; a batch is read without following a link; a batch cell may hold a TAB or a line break in a text column but no control, format or line-separator character in an identifier column, no lone CR, and no other control or format character (`batch-control`); the files read are checked again just before writing, so two merges at once cannot lose one. `--draft-exceptions`
prints a legacy study's current breaches as a first exceptions file, `id,rule`, and writes nothing.

### Row files (step B)

`survey-validate` also checks every row file sections 4.1, 4.3 and 4.8 define that is present: the evidence file
(with the registry it needs: "a missing registry is itself an error"), the attribution file, the legacy exceptions,
the vocabulary file and the bucket tables. Evidence errors carry the rule ids of 4.1 (`columns`, `id-empty`,
`id-duplicate`, `attribute-kind`, `person-unknown`, `unit-id`, `unit-unknown`, `unit-person`, `id-separator`,
`tier-unknown`, `counted-quote`, `counted-citation`, `counted-basis`, `reported-reporter`, `own-reporter`, `ne-quote`,
`ne-note`, `vocabulary`). The other ids are the toolkit's own: `registry-missing`, `registry-columns`,
`registry-person`, `vocabulary-file`, `evidence-plugin`, `cell-nul`, `locator-missing`; `exceptions-columns`, `exceptions-rule`,
`exceptions-unlistable`, `exceptions-id`, `exceptions-duplicate`, `exceptions-stale`; `receipts-undeclared`,
`receipt-url`, `receipt-missing`, `receipt-malformed`; `attribution-columns`, `attribution-unit-empty`,
`attribution-unit-duplicate`, `attribution-unit-is-person`, `attribution-person-empty`, `attribution-separator`,
`attribution-status`, `attribution-author-kind`, `attribution-passage-attribute`, `attribution-author-kinds`;
`table-columns`, `table-empty`, `table-row`, `table-pattern`, `table-bucket`, `table-fallback`.

In a legacy study a breach listed in `evidence.legacy_exceptions` is counted and does not fail, and a counted row
that predates receipts (no receipt, no url, no locator) is printed as `REPORTED`, not an error (5.4); a receipt that
is there and broken is an error. Every run, failing or not, prints how many rows it read, how many exceptions it was
read with, the excused breaches by rule, and how many counted quotations were not re-found. Row files are streamed
(`MAX_CSV_BYTES`, 64 MiB) and opened at their resolved place under rule 1.6; project patterns are capped
(`MAX_PATTERN_CHARS`, `MAX_PATTERNS`, `MAX_MATCH_CHARS`); every output line escapes control characters, and a quoted value is cut at `MAX_QUOTED_CHARS` (200) characters. The caps bound the size of a pattern and of the text it is searched in, not the time a search takes: a project's own pattern can still be slow, and the files that hold patterns (the vocabulary file, the bucket tables) are covered by gate S0. Evidence in a `plugin` format is not checked: this
version does not load the reader plug-in, and says so as an error. Nothing re-finds a quotation yet (step G); the
count of counted quotations not re-found is printed. The batch merge (`survey-rows`) and the registry
(`survey-registry`) are not in this version.

### Usage

```text
python3 -B -I scripts/survey/survey_validate.py [--root DIR] <project>
python3 -B -I scripts/survey/survey_status.py   [--root DIR] <project>
python3 -B -I scripts/survey/survey_manifest.py [--root DIR] <project> <gate>
python3 scripts/survey/survey_schema.py [--check]
```

`<project>` names `Projects/<project>/study.json`. `--root` is the repository root (default: the repository the
script sits in); it must hold `.git`. It exists for tests: the bridge refuses it and always works on its own
repository. `<gate>` is `S0`, `S5`, `S6` or `S8`.

### Errors

Each error is one line, `ERROR [<id>] <where>: <message>`, where `<where>` is a file and a JSON pointer. The ids are
the toolkit's own (section 3 gives none) and stable; the check table
(`references/plans/post-1.3.0-h5-step-a-check-table.md`) maps each to its contract line. Shape: `type`, `required`,
`unknown-key`, `enum`, `pattern`, `empty`, `min-items`, `minimum`, `maximum`, and the conditionals
`saturation-fields`, `reader-missing`, `reader-unexpected`, `present-code-missing`, `present-code-unexpected`.
Paths: `path-empty`, `path-absolute`, `path-dotdot`, `path-outside`, and the toolkit's own refusals
`path-backslash`, `path-nul` and `path-segment` (a `.` or empty segment), so that a manifest carries each path as
declared. JSON: `json` (including nesting too deep to read), `json-duplicate-key`, `too-large`. Beyond shape: the
ids of `SEMANTIC_RULES`. Ledger: `ledger-form`, `ledger-link`, `ledger-location`, `ledger-missing`,
`ledger-layout`, `ledger-privilege`, `ledger-log`, `ledger-keys`, `ledger-keys-empty`, `ledger-approvers`,
`ledger-approvers-empty`, `ledger-waiver`, `ledger-parity`, `ledger-scheme` (step F). Manifest files: `manifest-malformed`.

The specification and every JSON file are read only up to `MAX_JSON_BYTES` (16 MiB), the ledger's log up to
`MAX_LOG_BYTES` (64 MiB); a larger file is refused unread. Each such read opens with `O_NOFOLLOW` and `O_NONBLOCK`
and checks by `fstat` that the open file is regular, so a key or approver file that is a link, FIFO or device, or a
key store that is not a plain directory, is never read.

The ledger's approvers and keys are compared with a team directory (each generated location, and `parent_team`) only
when that team names an approver and has a verify key; a team that lacks either "has neither" (6.2), and the folder
is then the only place they live. A link inside a team directory where the comparison reads leaves the gates
`UNAVAILABLE` instead.

### Gate states

Since step F, a gate reads `CLEARED` when its request (the manifest file `survey-manifest` wrote) is exactly the
manifest built now, the row that decides passes the tools' own rules, and agentteams 1.3.0 or later, run as a child
process of the same interpreter, clears the action. The tools' rules on that row: it names the action exactly; it is
a `PASS`, or a `CONDITIONAL PASS` whose conditions are verified; it is not marked as signed from a checkout; its
`derives_from`, `scope` and `effect_*` columns are empty; its `key_id` is a plain stem naming a key file in the
folder; its author is on the folder's approver list. Every row of the folder's log must be `ed25519`
(`ledger-scheme`). The order of the states, and the reasons, are in the docstring of `survey_gates.gate_status` and
in the check table `references/plans/post-1.3.0-h6-step-f-check-table.md`. In short:

- a request whose manifest changed since it was written is `UNCLEARED`, decided first;
- a malformed ledger folder or manifest file, anything that would stop the HALT scan of 6.2 (a team directory
  reached through a symbolic link, a `parent_team` with one of the faults 6.2 lists, more than one git root above the
  folder, a team log that cannot be read), or a HALT row on `survey-signoff` or `survey-signoff/<gate>` in any
  scanned log, or on any id that contains that name once letter case, separators and format characters are set
  aside, except a study's exact scope or action (the interim rule: signed or not, retracted or not), leaves the gate
  `UNAVAILABLE`;
- no request is `UNCLEARED`, also when the manifest cannot be built;
- otherwise agentteams absent (always on Python 3.10), older than 1.3.0, or without `cryptography` is `UNAVAILABLE`,
  decided before the tools' rules on the row (rule 1.7);
- a deciding row that fails the tools' rules is `UNCLEARED`;
- an answer from agentteams in any way but one well-formed JSON line is `UNAVAILABLE`.

Reasons that stop the HALT scan are printed and do not make `survey-status` or `survey-validate` fail. A
`parent_team` value that is no path at all (not a string, empty, a NUL, `repo:`-rooted, a backslash or a `.`
segment) is a malformed ledger (`ledger-privilege`). A gate the specification does not declare is shown as
`NOT DECLARED`. `survey-status` also prints where the verifying agentteams is installed (inside or outside the work
tree), what a sign-off proves (6.2), and the two gaps no tool can close. Every value read from a log is escaped.

A gated stage calls `survey_gates.require_gate`: a `blocking` gate runs the stage only when `CLEARED`; a `build-only`
gate runs it in every state and records the state, except that a malformed ledger folder refuses both (operator
decision, 2026-11-25).

### Output files

Only `survey-manifest` writes: `<ledger folder>/references/<study id>.<gate>.manifest.json`, beside the log,
canonical JSON, mode 0644, replaced atomically after a last check that no component of its folder is a link. It refuses, writing nothing, when the specification or the ledger is malformed, the gate is not declared,
a covered file is missing or not a regular file, or the path holds something other than a well-formed manifest of
this gate. `survey_schema.py` without `--check` writes `study.schema.json`.

### Exit codes

| Script | 0 | 1 | 2 |
|--------|---|---|---|
| `survey_validate.py` | Well-formed | Any error | Usage error, no project, no `.git` at the root |
| `survey_status.py` | Printed, whatever the states (including `UNAVAILABLE` for a reason the HALT scan cannot be made) | The specification, a manifest file or the ledger is malformed | As above |
| `survey_manifest.py` | Written, or unchanged | Refused | As above, or an unknown gate |

---

## `sign_security_decision.py`

> *Source: `scripts/sign_security_decision.py`*

Operator-only. Appends an HMAC-signed `PASS` row to the agentteams security decisions log, then asks the agentteams gate to verify it. With `enforce_decision_signing: true` (the scaffold default), agentteams refuses unsigned clearances, so this is how a person authorizes a routine destructive action such as the `overwrite` pass run by `researchteam materialize`. It does not produce the Ed25519 rows needed for constraint-relaxing exceptions; those come from `agentteams --sign-decision`.

### Usage

```text
python scripts/sign_security_decision.py --action ACTION --conditions TEXT [--log PATH]
```

| Argument | Meaning |
|----------|---------|
| `--action` (required) | agentteams action id, for example `overwrite` or `prune`. Written to `action_reviewed`. |
| `--conditions` (required) | What was reviewed and why it is cleared. Written as `operator-signed: <TEXT>`. |
| `--log PATH` | Decisions log. Default `.github/agents/references/security-decisions.log.csv`, relative to the working directory. |

**Example** (from the script and `init`'s next-steps output):

```bash
export AGENTTEAMS_DECISION_SIGNING_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
python scripts/sign_security_decision.py --action overwrite --conditions "first render"
researchteam materialize --yes        # same shell: verification needs the key too
```

### Environment

| Variable | Requirement |
|----------|-------------|
| `AGENTTEAMS_DECISION_SIGNING_KEY` | Required. Must be set in the operator's shell, never in a repository file or an agent's environment. Rejected when unset, when shorter than 32 bytes (UTF-8), or when it looks like a placeholder: after stripping and lower-casing it equals or starts with `...`, `changeme`, `change-me`, `secret`, `placeholder`, `xxx`, `todo`, `your-key` or `<`, or has two or fewer distinct characters. |

### Behaviour

1. Validates the key.
2. Imports `sign_decision_row` and `check_clearance` from agentteams.
3. Requires the log to exist and its parent directory to be named `references`.
4. Requires the columns `timestamp`, `requesting_agent`, `action_reviewed`, `verdict`, `conditions`, `conditions_verified`. Refuses a hash-chained log (one with a `prev_digest` column). Adds a `signature` column if missing; existing rows keep an empty signature.
5. Builds the row: UTC `timestamp` (`%Y-%m-%dT%H:%M:%SZ`), `requesting_agent` `security`, `verdict` `PASS`, `conditions_verified` `verified`, other columns empty, and `signature` from `sign_decision_row`.
6. Rewrites the log atomically (temp file in the same directory, then `os.replace`).
7. Calls `check_clearance(<agents dir>, action=ACTION)`. If the gate rejects the row, the log is rewritten atomically with its original columns and rows.

### Exit codes

| Code | Cause |
|------|-------|
| 0 | Row appended and accepted by the gate. |
| 1 | Key unusable; agentteams not importable in this interpreter; log not found or not under a `references/` directory; required columns missing; log is hash-chained; gate rejected the row (log restored). |
| 2 | argparse usage error (for example a missing `--action`). |

### Output files

- The decisions log given by `--log`, rewritten in place.

---

## See Also

- [`index.md`](index.md) — API reference overview.
- [`manifest.md`](manifest.md) — which managed set ships each script.
- [`doctor.md`](doctor.md) — runs `check_toolchain.py --python <sys.executable>`.
- [`release.md`](release.md) — tag verification used by `--write-lock --tag`, `--release-candidate` and `--verify-tag`.
- [`update.md`](update.md) — syncs these scripts; `materialize` consumes the signed clearance.
- [`init.md`](init.md) — next-steps output that points at `sign_security_decision.py`.
- [`../cli-reference.md`](../cli-reference.md) — command-line reference.
