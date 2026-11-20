# P1 steps 0.1 and 0.4: seam table, private-symbol inventory and draft request (read-only)

Finding for P1 steps 0.1 and 0.4 (`technical-validator`, 2026-11-20). Spot-checked against the source by the orchestrator. The request in Deliverable 3 is a draft: it has not been sent.

The engine's matching, masking, form keys and generated-file layout match upstream line for line, once `TermIndexConfig` and the function arguments carry researchteam's values. The main blocker is that upstream `term_index.py` imports `agentteams._term_text`, so a byte-identical copy under `scripts/` cannot be imported without the `agentteams` package. Separately, three behaviour points have no upstream parameter or counterpart; they are listed first under "Gaps and differences".

Sources read:
- `scripts/term_index_engine.py` (674 lines)
- `scripts/build_term_index.py`, `check_term_index.py` and `query_term_index.py` (the actual caller names)
- `references/plans/open-1119-p1-term-index-core-switch.plan.md`
- The two upstream copies: `agentteams `dev` at `b4b732f`: term_index.py` and `agentteams `dev` at `b4b732f`: _term_text.py`

Abbreviations: "TI" means upstream `term_index.py` and "TT" means upstream `_term_text.py`. "Cfg.x" means the `TermIndexConfig` field `x` (TI:143-171).

---

## Deliverable 1: seam table (step 0.1)

### 1a. Top-level names in `scripts/term_index_engine.py`

| Name | Line | Class | Upstream counterpart | Parameter that carries the adapter point |
|---|---|---|---|---|
| `GENERATOR` = `"researchteam-term-index/1"` | 28 | ADAPTER | Cfg.generator (TI:162, default `"agentteams-term-index/1"`) | `generator` |
| `REGISTER_SCHEMA` = `"researchteam-term-register"` | 29 | ADAPTER | TI `RESEARCHTEAM_SCHEMA` (49), accepted through Cfg.schemas (TI:164) | `schemas` (the default also accepts `NEUTRAL_SCHEMA`) |
| `SCHEMA_VERSION` | 30 | CORE | TI `SCHEMA_VERSION` (50) | – |
| `CEILING` | 31 | CORE | TI `CEILING` (51), identical text | – |
| `DO_NOT_EDIT` (mentions `scripts/build_term_index.py` and the bridge command `term-build <project>`) | 34 | ADAPTER | Cfg.do_not_edit (TI:169) | `do_not_edit` |
| `MAX_TERMS, MAX_FORMS, MAX_FORM_CHARS, MAX_ALL_FORMS` | 36 | CORE | TI:54, same values | – |
| `MAX_FORM_WORDS, MAX_FORMS_PER_LEAD, MAX_SCOPE_PATTERNS` | 38 | CORE | TI:56, same values | – |
| `MAX_REGISTER_BYTES, MAX_DOC_BYTES` | 39 | CORE | TI:57, same values | – |
| `MAX_DEPTH` = 12 | 39 | ADAPTER (discovery) | no constant upstream; `discover(max_depth=12)` (TI:205) | `discover(..., max_depth=)` argument |
| `MISSING, FOREIGN, BAD, OK` | 40 | CORE | TI:133 | – |
| `ID_RE` | 41 | CORE | TI:134 | – |
| `SAFE_PATH` | 42 | CORE | TI:135 | – |
| `TERM_KEYS` | 43 | CORE | TI:136 | – |
| `TOP_KEYS` | 44 | CORE | TI:137 | – |
| `PRUNED_DIRS` | 46 | ADAPTER | `discover(pruned=)` (TI:204) | `discover(..., pruned=)` argument |
| `REFS_HEADING` (References / Bibliography / Works Cited / Sources) | 48 | ADAPTER | Cfg.skip_heading (TI:165), passed by `assess` to `Matcher(reg, skip_heading)` (TI:584, TT:276) and then to `mask` (TT:169, 331) | `skip_heading` |
| `HEADING` | 49 | CORE | TT `HEADING` (16) | – |
| `FENCE` | 50 | CORE | TT `FENCE` (15) | – |
| `FRONT_MATTER` | 51 | CORE | TT `FRONT_MATTER` (17). TT has a literal U+FEFF where the engine has the `\ufeff` escape; both compile to the same pattern (I found the literal U+FEFF in TT:17 by search) | – |
| `NOT_PROSE` | 54 | CORE | TT `NOT_PROSE` (20) | – |
| `BACKTICKS` | 56 | CORE | TT `BACKTICKS` (22) | – |
| `WORD` | 57 | CORE | TT `WORD` (23), imported into TI at TI:38 | – |
| `SEP` | 58 | CORE | TT `SEP` (24) | – |
| class `Assessment` | 61 | CORE | TI `Assessment` (174) | – |
| `repo_root` (reads `RT_ROOT`; the repository is the parent of `scripts/`) | 78 | ADAPTER | none | None needed: adapter only, no core code path |
| `is_research_project` (`00-research-plan.md`, a `references/` directory, or an `NN-*.md` file) | 82 | ADAPTER | none | The `is_project` argument of `discover` (TI:204), `documents` (TI:397), `assess` (TI:550) and `check_project` (TI:677), as part of the composite predicate below. Also the `required` argument of `check_project` (TI:676) |
| `is_project` (has a register, or `is_research_project`) | 89 | ADAPTER | TI `_is_nested_project` (392) covers only the register half | `is_project` argument. It must be passed explicitly; see gap 4 |
| `discover` (searches `root/"Projects"`, skips `terminology`) | 93 | ADAPTER | TI `discover(base, is_project, *, pruned, skip_dir, max_depth)` (204) | Arguments `base` (= `root/"Projects"`), `is_project`, `pruned`, `skip_dir`, `max_depth` |
| `project_arg` (strips `Projects/`) | 117 | ADAPTER | none | None needed: adapter only |
| `resolve` (finds a project under `Projects/`) | 123 | ADAPTER | none | None needed: adapter only |
| `shown` | 131 | CORE | TI `shown` (192) | – |
| `form_key` | 137 | CORE | TT `form_key` (28) | – |
| `form_keys` | 144 | CORE | TT `form_keys` (45) | – |
| `match_words` | 149 | CORE | TT `match_words` (59) | – |
| `_strings` | 154 | CORE | TI `_strings` (237) | – |
| `_check_term` | 161 | CORE | TI `_check_term` (244), identical including the "list of .bib keys" message | – |
| `_check_scope_and_allow` | 204 | CORE | TI `_check_scope_and_allow` (287) | – |
| `load_register` | 228 | CORE with adapter points (the `terminology` directory and the schema) | TI `load_register(proj, config)` (335) plus `register_text_problems` (311) | Cfg.dir_name, Cfg.schemas. The size-limit message differs; see gap 5 |
| `term_forms` | 263 | CORE | TT `term_forms` (87), reachable as `TI.term_forms` but not in `__all__` | – |
| `_ambiguities` | 269 | CORE | TI `_ambiguities` (368) | – |
| `lead_key` | 283 | CORE | TT `lead_key` (71) | – |
| `_crowded_leads` | 293 | CORE | TI `_crowded_leads` (382) | – |
| `glob_match` | 303 | CORE | TT `glob_match` (101) | – |
| `documents` | 330 | CORE with adapter points (default include, `terminology`, the nested-project predicate) | TI `documents(proj, reg, config, is_project)` (396) | Cfg.default_include, Cfg.dir_name, `is_project` argument |
| `read_document` | 348 | CORE | TI `read_document(path, root=None)` (429), which uses `read_capped` (65) | – (behaviour differs; see gaps 6 and 8) |
| `_blank` | 357 | CORE | TT `_blank` (138) | – |
| `_code_spans` | 363 | CORE | TT `_code_spans` (144) | – |
| `mask` | 386 | CORE plus the `REFS_HEADING` adapter point | TT `mask(text, skip_heading=None)` (169) | `skip_heading` |
| `quoted_spans` | 430 | CORE | TT `quoted_spans` (222) | – |
| `_paragraph_quotes` | 453 | CORE | TT `_paragraph_quotes` (253) | – |
| class `Matcher` | 463 | CORE | TT `Matcher(reg, skip_heading=None)` (263, 276) | `skip_heading`, supplied by `assess` from Cfg.skip_heading |
| `disc_violations` | 539 | CORE | TI `disc_violations` (450) | – |
| `escape` | 546 | CORE | TI `escape` (466), not in `__all__` | – |
| `_index_file` | 552 | CORE plus the adapter banner | TI `_index_file(rel, sha, occs, config)` (479) | Cfg.do_not_edit |
| `_glossary` (banner with `term-query` bridge command, line 568) | 565 | CORE plus adapter text | TI `_glossary(proj, reg, config)` (491) | Cfg.do_not_edit, Cfg.dir_name, Cfg.glossary_hint. This must be set to ``"Where each term occurs: `bash scripts/claude_researchteam_bridge.sh term-query`."`` for identical bytes |
| `_read_json(path)` | 585 | CORE | TI `_read_json(proj, rel)` (511), capped at `MAX_GENERATED_BYTES` (59) | – (see gaps 6 and 7) |
| `read_manifest` | 593 | CORE | TI `read_manifest(proj, config)` (521) | Cfg.dir_name |
| `manifest_matches` | 599 | CORE | none; the same test is inline at TI:570 | GAP: no public counterpart (gap 3) |
| `manifest_is_current` (fast path for the edit hook; `build_term_index.py:217`) | 604 | CORE | none | GAP: no counterpart (gap 3) |
| `_well_formed` | 616 | CORE | TI `_well_formed` (535) | – |
| `_reusable` | 623 | CORE | TI `_reusable(..., config)` (541) | Cfg.dir_name |
| `assess(proj, reuse=False)` | 633 | CORE with adapter points | TI `assess(proj, config, reuse=False, is_project=None)` (549) | Cfg plus `is_project`. The signature differs: `build_term_index.py:108` passes `reuse` as the second positional argument, which upstream would take as `config` |
| `stray_index_files` | 668 | CORE | TI `stray_index_files(proj, files, config)` (598) | Cfg.dir_name |

### 1b. Adapter points that live in the caller scripts, not the engine

| Caller | Line | Point | Upstream counterpart / parameter |
|---|---|---|---|
| `check_term_index.py` `required()` (`.researchteam` key `term_index_require`) | 40-66 | `.researchteam` marker | TI `check_project(required=)` (676). The adapter passes `named or (require and is_research_project(proj))` (engine logic at `check_term_index.py:153`) |
| `check_term_index.py` `bib_keys` and the SRC defect | 69-76, 135-137 | `.bib` `[SRC]` source check | Cfg.source_validator (TI:166), called at TI:666-667 |
| `check_term_index.py` `freshness` / `_generated_file_problems` | 79-117 | STALE / REBUILD messages using `term-build` | TI `_freshness` (617). Messages are identical with Cfg.rebuild_hint = `"term-build"` (the default, TI:170) |
| `check_term_index.py` `usage_findings` | 120-143 | DISC / NOSRC / UNUSED / QUOTED | TI `_usage` (654), identical messages |
| `check_term_index.py` `check_project` NOREG hint (`"its terms.json is not a researchteam register"` / `"run: term-init"`) | 154 | Bridge command and message | TI `check_project` NOREG text at TI:700: `"its terms.json has no accepted schema marker"` / `"add terms.json"`. **GAP** |
| `build_term_index.py` `STARTER` uses `engine.REGISTER_SCHEMA` | 50 | Schema name | TI `RESEARCHTEAM_SCHEMA` (49); the adapter keeps an alias |
| `build_term_index.py` `cmd_init` uses `engine.MAX_DEPTH`, `PRUNED_DIRS`, `is_project`, `project_arg` | 151-163 | Discovery | Adapter only (see 1a) |

### Gaps and differences (most important first)

1. **Upstream cannot be copied as a standalone file.** TI:37-39 reads:
   ```python
   from agentteams._term_text import (
       WORD, Matcher, form_key, form_keys, glob_match, lead_key, mask, match_words, quoted_spans, term_forms,
   )
   ```
   This is an absolute, package-qualified import of a private module.
   - **Without `agentteams` installed:** a byte-identical `term_index.py` under `scripts/` cannot be imported as-is. The import at line 37 raises `ModuleNotFoundError: No module named 'agentteams'`. A byte-identical `_term_text.py` placed beside it does not help, because the name looked up is `agentteams._term_text`, not `_term_text`.
   - **With `agentteams` installed (for example via the `[update]` extra):** the import resolves to the installed package's `_term_text`, whatever version that is, not to a pinned copy. The pinned `term_index.py` would then run with unpinned matcher code.
   - The core is two files, and the plan's 0.1 request is "a single file that imports only the standard library".
   - Verified by reading TI:37-39.

2. **NOREG hint text has no parameter.**
   - Engine (`check_term_index.py:154`): `"its terms.json is not a researchteam register"` / `"run: term-init"`. Upstream (TI:700): `"its terms.json has no accepted schema marker"` / `"add terms.json"`.
   - The gate code (NOREG) and the exit code are unchanged; the printed line changes.
   - Verified by reading both.

3. **`manifest_matches` and `manifest_is_current` have no upstream counterpart.** These are engine lines 599 and 604; the hook uses them at `build_term_index.py:217`. The generator and register-hash test is inline at TI:570. The adapter would have to keep its own copy, built from `load_register`, `read_manifest`, `documents` and `read_document`, and pass `config.generator`. This is core logic that would stay outside the pinned copy. Verified.

4. **Upstream defaults are neutral, so any call that omits the config or `is_project` changes results.** Verified by reading both sides.
   - (a) `skip_heading=None`: References/Bibliography sections get scanned, so new occurrences and different `index/*.json` bytes. With an unchanged generator string that is STALE "differs from a fresh build"; with a different one it is REBUILD.
   - (b) `is_project=None` makes `documents()` skip only folders holding a register (TI:392, 412). The engine also skips sub-folders that look like research projects (an `NN-*.md` file, a `references/` directory or `00-research-plan.md`; engine:338, 82-86). Those documents would enter scope, giving STALE "entered the scope" and exit 1. `is_project` must be passed to every `assess` and `check_project` call.
   - (c) The default `generator` is `"agentteams-term-index/1"`: REBUILD (advisory) on every project, and byte comparison skipped.
   - (d) The default `schemas` also accepts `agentteams-term-register`, so a `terms.json` carrying that marker goes from FOREIGN to OK. Setting `schemas=(RESEARCHTEAM_SCHEMA,)` keeps current behaviour.
   - (e) `assess`'s second positional parameter is now `config` (gap noted in table 1a).
   - With researchteam's values in every field, generated bytes are identical. That covers manifest key order (engine:658-660 = TI:588-590), index layout (engine:552-562 = TI:479-488), glossary lines, `CEILING`, and the register hash (sha256 of the raw bytes on both sides). So keeping `"researchteam-term-index/1"` is consistent with the rule that the generator must change when bytes change. Verified.

5. **Message for an oversized register.**
   - Engine:236: `"terms.json is larger than 1000000 bytes"`. Upstream TI:354-355: `"terms.json is a link, not a regular file, or larger than 1000000 bytes (refused)"`.
   - Same code (SCHEMA) and status (BAD).
   - Verified.

6. **Symbolic-link handling on read-back is stricter upstream. This can make a clean project fail.**
   - Engine: `_generated_file_problems` (`check_term_index.py:84-86`) checks only the last path component (`is_symlink()`) and then `read_bytes()`, which follows links in parent directories. `stray_index_files` returns an empty set when `terminology/index` is a link (engine:671).
   - Upstream: `_freshness` reads through `read_capped` (TI:639), which opens every component with `O_NOFOLLOW` (TI:91-99, 110) and returns `None` for any link.
   - Result: a project whose `terminology/index/` is a symbolic link to a correct copy is clean today but would get STALE "differs from a fresh build" for every index file (exit 1).
   - A symlinked sub-folder inside `index/` is already flagged as stray by both.
   - Verified by reading both. Real-world occurrence is unlikely.

7. **Capped read of generated files.**
   - Upstream `_read_json` refuses committed JSON over `MAX_GENERATED_BYTES` = 20,000,000 (TI:59, 515). A manifest that large would become "no usable index manifest" (STALE).
   - The engine reads it uncapped (engine:588).
   - `_freshness` caps each comparison at the expected length (TI:639); the outcome is the same as the engine's byte comparison.
   - Verified by reading. Not reachable for realistic projects.

8. **Document and register reads (race-only differences).**
   - **Missing file:** upstream `read_document` turns `FileNotFoundError` into `None`, which becomes a SCOPE defect (TI:446-447, exit 1). In the engine, `lstat` raises, which is exit 2 in check (`check_term_index.py:219`) and in build (`build_term_index.py:255`). This only happens if a file disappears between the walk and the read.
   - **Growing file:** upstream reads at most cap+1 bytes through the open descriptor and refuses a file that grows past the cap after `fstat`; the engine checks the size first, then reads the whole file.
   - **FIFO:** both return `None` (engine `S_ISREG` check; upstream `O_NONBLOCK` + `fstat`).
   - None of this changes a stable project. Verified by reading.

9. **Upstream does things the engine does not, and none of them changes a stable, link-free project.** Verified.
   - Per-component `O_NOFOLLOW` with `dir_fd` (TI:61-62, 91-99), `O_NONBLOCK`, `fstat`, capped reads (TI:65-132).
   - Accepts the neutral schema.
   - `region_filter` (unused, defaults to `None`).
   - `register_text_problems` split out.
   - `check_project`, `_freshness` and `_usage` moved into the core.
   - Effects on currently clean projects are limited to items 6 and 7.

10. **No difference found (verified line by line).**
    - `Matcher` (`__init__`, `_pattern`, `_hits`, `occurrences`); TT adds only `skip_heading`.
    - `mask` (only `in_refs` becomes `in_skip`), `quoted_spans`, `_paragraph_quotes`, `_code_spans`.
    - `form_key`, `form_keys`, `match_words`, `lead_key`, `glob_match`.
    - All validation messages and limits.
    - STALE / REBUILD / DISC / NOSRC / UNUSED / QUOTED / ORPHAN text, with `rebuild_hint="term-build"`.

11. **Status note.** The TI docstring (TI:3) calls the module "beta (outside SemVer in 1.3.x)". A pinned copy guards bytes, but the API may change between 1.3.x releases.

12. **The plan's state section is out of date** (TV-07):
    ```
    [TV-07] references/plans/open-1119-p1-term-index-core-switch.plan.md:17
    Expected (in source): agentteams/term_index.py exists on dev (commit b4b732f, per the caller)
    Found (in deliverable): "`agentteams/term_index.py` does not exist on `dev`."
    Authority source: caller statement; a scratch copy of the upstream term_index.py
    Recommended action: update the dated state line when the plan is next revised
    ```

---

## Deliverable 2: private-symbol inventory (step 0.4)

Method: text search with ripgrep over `researchteam/`, `scripts/` and `templates/`. Patterns used: `from agentteams`, `import agentteams`, `agentteams\.cli`, `agentteams\.[A-Za-z_]`, `-m agentteams`, `find_spec`, `importlib`. `templates/` exists but holds only `bibliography-explorer/` and has no agentteams reference.

### 2a. Underscore (private) symbols and modules

| File:line | Symbol | What researchteam uses it for | Public replacement needed |
|---|---|---|---|
| `researchteam/_frozen.py:173`. This is inside the `_VERIFY` code string (lines 168-209), which `verify_unfreeze` runs as `[py, "-I", "-c", _VERIFY, ...]` under agentteams' interpreter (line 222) | `agentteams.cli.security_gate._latest_security_decision` | Fetches the newest decision row for `unfreeze-<surface>`, to confirm it requires an operator signature (line 200) and is Ed25519-signed (`sig_scheme` / `signature`, line 204) | `latest_decision(team: Path, action: str) -> dict \| None`: the newest decision row (not a waiver) for exactly `action`, with documented stable keys including `verdict`, `sig_scheme` and `signature`. Alternatively one call, `verify_signed_relaxing_decision(team, action) -> tuple[bool, str]` |
| `researchteam/_frozen.py:192` (same code string) | `agentteams.cli.security_gate._latest_security_waiver` | Refuses an unfreeze when a waiver exists for the action, because the gate accepts a waiver before checking row signatures (comment at lines 189-190) | `latest_waiver(team: Path, action: str) -> dict \| None`: the newest waiver row for exactly `action`, or `None` |
| Future `scripts/term_index.py:37` (TI:37) | module `agentteams._term_text` | Matcher, masking, form keys and globs that the copied core depends on | Either fold it into the single copyable file, or a public module that is stdlib-only and loadable without the `agentteams` package. Contract: the copyable core imports nothing outside the standard library |

### 2b. Non-underscore symbols reached through `agentteams.cli.*`

| File:line | Import | Used at |
|---|---|---|
| `researchteam/_frozen.py:173` | `agentteams.cli.security_gate.check_clearance` | `_frozen.py:186` |
| `researchteam/_frozen.py:174` | `agentteams.cli.effect_classifier.RELAXING`, `derive_effect_class`, `requires_operator_signature` | `_frozen.py:183`, `200` |
| `scripts/sign_security_decision.py:80` | `agentteams.cli.decision_log.sign_decision_row` | `sign_security_decision.py:113` |
| `scripts/sign_security_decision.py:81` | `agentteams.cli.security_gate.check_clearance` | `sign_security_decision.py:117` |

### 2c. Other non-public dependencies (not imports)

- `researchteam/_agentteams_provenance.py:55`: `ENTRY_MODULES = ("build_team", "agentteams")`. Line 111 locates the top-level module `build_team` with `importlib.util.find_spec`, without importing it. This relies on agentteams' console-script entry `build_team:main` remaining a top-level module.
- `researchteam/_update_cmd.py:1337`: user-facing message text naming `agentteams.write_policy.apply`. It is text only, not an import.

---

## Deliverable 3: draft message to the fleet coordinator (agentteams lane)

> From the researchteam session (plan P1, steps 0.1 and 0.4), a request for the agentteams lane.
>
> We compared researchteam's scripts/term_index_engine.py with term_index.py and _term_text.py at agentteams dev b4b732f. With TermIndexConfig set to our values, the matcher, masking, form keys and generated bytes are the same. Before 1.3.0 is cut, please consider:
>
> 1. term_index.py line 37 imports agentteams._term_text. We plan a sha256-pinned copy under scripts/, used where agentteams is not installed. We ask that the copyable core be one file that imports only the standard library and loads without the agentteams package.
> 2. The NOREG hint text has no parameter (ours: "its terms.json is not a researchteam register", "run: term-init").
> 3. manifest_matches and manifest_is_current (our edit hook's fast path) have no upstream counterpart.
> 4. read_capped marks every index file STALE when terminology/index/ is a symbolic link; our engine accepts that. Is that intended?
> 5. We need public equivalents of _latest_security_decision and _latest_security_waiver (agentteams.cli.security_gate, used in researchteam/_frozen.py). Please also say whether check_clearance, derive_effect_class, requires_operator_signature, RELAXING and sign_decision_row, which we import through agentteams.cli.*, are public API.

(About 175 words.)
