# Helper scripts — ResearchTeam

Command-line scripts under `scripts/` that researchteam ships to derived repositories as layer-2 managed files (see [`manifest.md`](manifest.md)). `check_toolchain.py` and `sign_security_decision.py` are in the framework set every repo receives; `build_literature_library.py` and `query_literature_library.py` are in the scholarly set. This page covers their arguments, environment variables, exit codes and output files.

> *Sources: `scripts/check_toolchain.py`, `scripts/build_literature_library.py`, `scripts/query_literature_library.py`, `scripts/sign_security_decision.py`*

> **Stability.** These scripts are managed files: `researchteam update` overwrites them from upstream, so local edits do not survive. Their command lines are used by other tooling (the SessionStart hook, `researchteam doctor`, the autosync gate); internal functions may change between releases.

---

## `check_toolchain.py`

> *Source: `scripts/check_toolchain.py`*

Checks whether the installed `researchteam` and `agentteams` are the commits pinned in `toolchain.lock`, and optionally whether upstream `main` has moved past the pin. It prints short `[toolchain] …` lines. Used by the SessionStart hook in `.claude/settings.toolchain.example.json` (its stdout becomes session context), by `scripts/bootstrap_toolchain.sh`, and by `researchteam doctor`. The autosync gate uses `--write-lock` to record what a green sync was verified with. Standard library only.

### Usage

```text
python3 scripts/check_toolchain.py [--python PATH] [--no-remote] [--strict]
                                   [--write-lock [--tag NAME=TAG ...]]
                                   [--release-candidate NAME]
                                   [--verify-tag NAME TAG]
```

| Argument | Meaning |
|----------|---------|
| `--python PATH` | Interpreter to inspect. |
| `--no-remote` | Skip the comparison with upstream `main` (`git ls-remote`). |
| `--strict` | Exit 1 when a pin does not match (see exit codes). |
| `--write-lock` | Record the installed commits in `toolchain.lock`. |
| `--tag NAME=TAG` | With `--write-lock`: the verified release tag that the installed `NAME` commit is. Repeatable. `NAME` is `researchteam` or `agentteams`. |
| `--release-candidate NAME` | Print the newest tag on `NAME`'s locked release line if it is newer than the locked tag; prints nothing when `NAME` is not release-locked. |
| `--verify-tag NAME TAG` | Verify `TAG` in `NAME`'s pinned repository and print its peeled commit. |

`--release-candidate` and `--verify-tag` are handled first and ignore the other options. Otherwise, `--write-lock` takes precedence over the default check.

**Interpreter selection** (first match wins): `--python PATH`; `<repo>/.venv/bin/python`; the interpreter behind the `researchteam` on `PATH`, read from its shebang (direct path, `/usr/bin/env` form, or pip's `sh`/`bash` trampoline). Package records are read by running that interpreter with `-I` (isolated mode).

**Repository root** is the parent of the script's own directory, not the working directory. `toolchain.lock` and `pyproject.toml` are read from there.

### `toolchain.lock` format

One pin per line; `#` comments allowed.

```text
researchteam=jlcatonjr/researchteam@<40-hex sha>
agentteams=jlcatonjr/agentteams@<40-hex sha>
agentteams.tag=v1.0.0               # optional: release-locked
```

A pin is valid only if its repository is the allowed one (`jlcatonjr/researchteam` or `jlcatonjr/agentteams`) and its commit is 40 lowercase hex characters. A pin with a `<name>.tag` line is release-locked: `--write-lock` moves it only to a newer verified tag on the same `vX.Y` line, never to an untagged commit. `--write-lock` writes a fixed comment header followed by the two pins (and any tags).

### Default check

1. No `toolchain.lock`: prints `[toolchain] no toolchain.lock yet; …` and exits 0.
2. For every git-installed `agentteams` requirement in the repo's `pyproject.toml` whose repository or ref differs from the `agentteams` pin, prints `[toolchain] MISMATCH: …`.
3. No interpreter found, or it cannot be inspected: prints a line suggesting `bash scripts/bootstrap_toolchain.sh`.
4. For each package: a problem if the pin is invalid, the package is not installed, its install records no commit (index or plain local-folder install), or its commit differs from the pin. A match from an editable checkout with uncommitted changes is a note. For pins that are not release-locked and unless `--no-remote`, a note when upstream `main` differs from the pin.
5. Prints `[toolchain] OK: researchteam and agentteams match toolchain.lock (<python>)` when there are no problems and no notes. Otherwise prints each problem as `[toolchain] BEHIND: …` (pyproject mismatches were already printed), each note as `[toolchain] note: …`, and, if there were problems, the bootstrap hint.

An install's commit comes from its `direct_url.json`: `vcs_info.commit_id` for a git install, or `git rev-parse HEAD` in the checkout for an editable install (with `git status --porcelain --untracked-files=no` for the dirty flag).

### Exit codes

| Mode | 0 | 1 | 2 |
|------|---|---|---|
| Default | Always, unless `--strict` | `--strict` and a problem was found, or `--strict` and no interpreter could be found or inspected | — |
| `--write-lock` | Lock written (prints `updated` or `unchanged` with the short commits) | Interpreter cannot be inspected; a package is not installed; a package has no recorded 40-hex commit or is from a dirty checkout; a pin would name a disallowed repo; a release lock would be broken or a `--tag` cannot be verified | A `--tag` value is malformed |
| `--release-candidate` / `--verify-tag` | Answer printed (or no candidate) | `researchteam._release` is not importable; `NAME` has no valid pin; release verification failed | — |

argparse usage errors exit 2.

### Output files

- `toolchain.lock` at the repository root, written only with `--write-lock`.

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
- A new record is seeded with `relevance.summary` set to the entry's `note` field, `relevance.source` set to `seeded-from-bib-note` (or `unseeded` when there is no note), `deemed_by` and `investigation` set to `null`, and empty `tags`. `source_db` is never inferred from the URL.
- Every record gets `record_text_sha256`, the SHA-256 of its indexed text.
- Tokenizing lower-cases the text, removes URLs, splits on non-letters, and drops tokens shorter than 3 characters, stopwords and URL-related words.
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
