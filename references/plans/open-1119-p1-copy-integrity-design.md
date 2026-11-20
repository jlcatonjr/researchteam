# P1 step 0.3: copy-integrity design for the term-index core (design note, 2026-11-20)

**Recommendation.** Copy the upstream core files byte-identically into `scripts/term-index-core/`, with a `PINNED.json` manifest of sha256 values beside them.
One stdlib-only script, `scripts/check_term_core.py`, checks the files against the manifest without network access, and loads them under a private package name. The term index never imports an installed agentteams.
CI proves that the copy matches the manifest. Proof that the manifest matches the signed agentteams tag comes from an opt-in network test and is required at release cut.

Plan: `references/plans/open-1119-p1-term-index-core-switch.plan.md`. Option C and the 1.3.0 placement are operator rulings and are not re-decided here. All upstream facts below come from agentteams `dev` at `b4b732f`, which is unreleased and provisional.

## 1. What is copied, and where it lives

At `b4b732f` the core is two files. `term_index.py` line 37 reads `from agentteams._term_text import (...)`, and `_term_text.py` imports only `bisect` and `re`. A byte-identical copy cannot rewrite that import.

| Option | Needs from upstream | What can go wrong | Byte-identical |
|---|---|---|---|
| (a) one stdlib-only file | Merge `_term_text` into `term_index.py` (requested, not agreed) | Nothing new; N = 1 | Yes |
| (b) two files plus an import shim | Nothing | The shim depends on how CPython's import system behaves, which must be tested | Yes |
| (c) relative import (`from ._term_text import ...`) | A one-line change at line 37 | A loader that does not load the files as a package fails at import | Yes |

**Decision: the design assumes (b), because only (b) works with the code as it stands. It is built so that (a) or (c) only removes the shim step.** The same loader handles all three:

- It reads `PINNED.json` and reads each listed file's bytes once.
- It checks each hash and compiles the bytes it checked, so nothing changes between the check and the load.
- It creates a private package `_researchteam_term_core` with an empty `__path__`, so nothing is found on disk. Each file becomes a submodule of that package, registered in `sys.modules` before it runs. The `@dataclass` classes in `term_index.py` need that registration.
- Files load in manifest order. The entry module is named in the manifest.
- Under (c), the relative import resolves inside the private package with no aliasing. Under (a), N = 1.

**The shim, for (b) only.** The loader saves whatever is at `sys.modules["agentteams._term_text"]`, or notes that the key is absent. It puts the pinned `_term_text` there, runs `term_index.py`, and then restores the saved value or deletes the key in a `finally` block.

In CPython, `from agentteams._term_text import ...` returns the module already in `sys.modules` without importing the parent `agentteams` package, so an installed agentteams is never loaded. A probe on 2026-11-20 with the two `b4b732f` files confirmed this on Python 3.13 and 3.14, with and without an importable agentteams: the parent package was not imported and `term_index.Matcher` was the pinned object. Python 3.10 was not available to the probe; the L1 test in section 5 covers it in CI. Before the swap, the pinned key also replaces a real agentteams module that is already loaded. The swap lasts only for one `exec`. That is safe in the CLI, which has one thread, but not guaranteed under pytest or the edit hook; section 10, point 6 gives the form phase 1 should prefer.

After loading, the core's globals point directly at the pinned objects. The loader checks `term_index.Matcher is <pinned _term_text>.Matcher` with an explicit `raise`, not an `assert`, so `python -O` cannot remove it.

**Directory.** The directory is `scripts/term-index-core/`. Its name is not a valid Python identifier, so a normal `import` can never reach these files, even with `scripts/` on `sys.path`. Each file is added to `SCHOLARLY_MANAGED_FILES` in `researchteam/_manifest.py`. Layer-2 sync fetches each listed file one at a time from the researchteam ref, which is a verified tag's peeled commit when the repository is release-locked. A derived repository therefore receives the copy only through that list.

## 2. Where the hashes live

**Decision: in `scripts/term-index-core/PINNED.json`, synced by the same list, so a copy and its hashes always come from the same researchteam commit.**

```json
{"format": "researchteam-pinned-copy/1",
 "upstream": {"repository": "jlcatonjr/agentteams", "tag": "v1.3.x", "commit": "<40-hex peeled>"},
 "entry": "term_index",
 "files": [{"upstream_path": "agentteams/_term_text.py",
            "local_path": "scripts/term-index-core/_term_text.py", "sha256": "<64-hex>"}, ...]}
```

Local paths must sit inside the directory: no `..`, no absolute paths, no symbolic links.

The hashes are not in `toolchain.lock`, for three reasons:
- The lock is repository-owned and never synced, so its hash would drift from the synced copy.
- A derived repository may pin a different agentteams patch, and its autosync rewrites the lock.
- The lock records what the toolchain was verified with. The manifest records where the copied bytes came from.

## 3. The no-network comparison

**Decision: `scripts/check_term_core.py`.** It is both the command and the loader the adapters import, so they share one hash routine. It imports no network module and never fetches.

- **Output:** one line per file (`[term-core] OK <path>` or `[term-core] MISMATCH <path>: sha256 <12 hex>, expected <12 hex> (agentteams <tag> <upstream_path>)`), then a summary line naming the tag, the short commit and the counts.
- **Exit 0:** every file matches.
- **Exit 1:** a file is mismatched, missing or a symbolic link, or a `.py` file in the directory is not listed in the manifest.
- **Exit 2:** the manifest is unreadable or malformed.

**Where it runs:**
- **Bridge `validate`:** `run_term_index_check` runs the core check first. Its "both files or neither" presence test is extended to cover the core directory.
- **`term-build`, `term-check` and `term-query`:** these run it implicitly at import. A failure exits 2 and prints the check's lines.
- **The edit hook:** it writes nothing and reports the failure.
- **An optional bridge command, `term-core-check`.**

Cost does not decide where it runs. Hashing two files of tens of kilobytes takes well under a millisecond, which is negligible beside a scan. Checking at import is what makes the mechanism fail closed. There is no override, and `TERM_INDEX_ADVISORY` does not soften it. To repair a failure, run `git checkout` on the directory, or `researchteam update` with a researchteam that knows the directory (section 10, point 1).

## 4. How `researchteam doctor` reports it

A new `_check_term_core(root, ok, warn, fail)` follows `_check_toolchain`:
- It runs the script under `sys.executable` with a timeout, passes each line through `_printable`, and relays it.
- It stays silent where the gate script is absent. `_check_scholarly_tooling` already reports that, and the manifest is added to its list.

**Decision: a mismatch is `[FAIL]`, unlike the informational term-index check.** It means the code that runs is not the code researchteam shipped, which is the same class of problem as "agentteams installed but not runnable". This is listed as an open question.

There are two `ok` lines: the pinned tag and commit, and "the term index uses the pinned copy, never the installed agentteams". If the manifest tag and the lock's `agentteams.tag` are on different `vX.Y` lines, doctor prints a `warn`.

## 5. The equality test

| Layer | Where | Proves | Does not prove |
|---|---|---|---|
| L1 `tests/test_term_core_pin.py` | CI, always, offline | The copy matches the manifest. The manifest is well formed. The loader works with no agentteams, with a dummy `agentteams` whose `_term_text` raises, and with a real module already in `sys.modules` (restored afterwards) | That the manifest matches upstream |
| L1 characterization tests (step 0.2) | CI | The adapter and the pinned core give unchanged results | That the core is upstream's |
| L2 upstream-equality test | Skipped unless `RT_NETWORK_TESTS=1` (the installed-package form is a convenience only; section 10, point 8) | Network source: the tag verifies (`_release.verify_tag`) and peels to the manifest commit, and `git show <commit>:<upstream_path>` has the manifest hash. Installed source: the installed files (read, not imported) match | Nothing in CI, where it is always skipped |
| L3 release cut | The cut script and the pin PR, mandatory, failing closed | L2's network form, at the moment provenance is attested | Edits made after the cut |

Between cuts, a PR that changes both a copy and the manifest passes CI. Only L3 catches it.

## 6. Threats, and what the mechanism does not cover

- **Anyone who can merge to researchteam** can change a copy and its manifest together. The manifest therefore protects against drift and accidental edits. It does not establish provenance. For a derived repository, provenance comes from the S-9 signed-tag check, which fixes the researchteam commit that layer-2 sync reads. A repository that is not release-locked syncs from `main` and has no such anchor.
- **A derived repository can edit its synced copy and its manifest together.** The check catches an edit to one without the other. `researchteam update` overwrites both. A partial sync, where one fetch fails, leaves a mismatch, and the check fails closed.
- **A derived repository may have a different agentteams installed.** That has no effect, because the installed package is never imported. If agentteams' own tooling is run on the same project, it writes `agentteams-term-index/1`, and the gate reports `[REBUILD]`, so the change is visible.
- **The upstream module is beta, outside SemVer in 1.3.x.** The byte pin stops silent change. Moving the core pin is a researchteam PR that re-runs L2, L3, the 0.2 tests and the seam review. The autosync's lock move never touches the copy.
- **Not covered:** whether the upstream code is correct, the interpreter, and the adapters, which get ordinary review.

## 7. What the adapter must pass

Every call to the core must pass the following.

- **Config:** `TermIndexConfig(generator="researchteam-term-index/1", schemas=(RESEARCHTEAM_SCHEMA,), skip_heading=<REFS_HEADING>, glossary_hint=<the term-query bridge line>, do_not_edit=<current banner>, rebuild_hint="term-build", source_validator=<the .bib check>)`.
- **`is_project`:** the composite predicate, on every `discover`, `documents`, `assess` and `check_project` call.
- **`assess(proj, config, reuse=...)` by keyword.** `build_term_index.py:108` passes `reuse` positionally, so that call must be fixed. The adapter wraps the core with keyword-only signatures, and a test asserts that no bare core alias is exported.

Three gaps stay outside the pin:
- **NOREG hint text:** the adapter keeps handling the MISSING and FOREIGN cases itself, as `check_term_index.py:148-154` does today, and calls the core only for registers that load. Ask upstream for a `noreg_hint` field.
- **`manifest_matches` and `manifest_is_current`:** these stay in the adapter, built from public core functions with `config.generator`. The 0.2 tests cover them, not the hash. Ask upstream to export them.
- **A symlinked `terminology/index/`:** accept upstream's stricter behaviour, mark it "allowed to change" in 0.2, and record it in the changelog, unless upstream calls it unintended.

The register-size message (gap 5) and the differences that occur only under races (gaps 7 and 8) are accepted as they are.

## 8. Provisional inputs: re-check at the signed 1.3.x tag

`b4b732f` may change, so this note pins no hash. Before phase 1 builds anything, re-check the following against the signed 1.3.x tag:
- the form of line 37, which decides between (a), (b) and (c);
- the file list;
- that every import is from the standard library, and that no other or lazy `agentteams` import exists;
- whether `@dataclass` is still used;
- the `TermIndexConfig` field names and defaults;
- the signatures of `assess`, `check_project`, `discover` and `documents`;
- `RESEARCHTEAM_SCHEMA` and `SCHEMA_VERSION`;
- generated-byte equality, by running the 0.2 tests and `term-check` on every project under `Projects/`;
- the status of the three gaps;
- the beta notice and `STABILITY.md`;
- the upstream paths;
- the tag signature and the peeled commit.

## 9. Open questions

1. Upstream: will it ship (a) a single file, (c) a relative import, or neither?
2. Upstream: will it add a `noreg_hint` field, a public `manifest_is_current`, and say whether the symbolic-link refusal is intended?
3. Upstream: does `TermIndexConfig` stay stable within 1.3.x, even though the module is beta?
4. Operator: should doctor report a mismatch as `[FAIL]` or as `[warn]`?
5. Operator: should `scripts/term-index-core/` join PS-2's list of paths that need a `@security` PASS?
6. Operator: at each researchteam release, must the core pin equal the lock's agentteams commit, or only share its `vX.Y` line?

## 10. Additions after the adversarial review (2026-11-20)

The review's verdict was CONDITIONAL. Points 1 to 4 were blocking for using this note as the phase-1 basis;
they are adopted here and bind phase 1. Where a point contradicts an earlier section, this section wins.

1. **Repair needs a new enough researchteam.** The list of synced files comes from the installed
   researchteam, not from the ref being synced. An older researchteam syncing a 1.3 ref receives the new
   adapters but not `scripts/term-index-core/`, and re-running the sync changes nothing. So a failure message
   names the installed researchteam version and tells the user to upgrade it first
   (`bash scripts/bootstrap_toolchain.sh`, or pip at the locked tag), then run `researchteam update`.
2. **Bytes, not text.** Layer-2 sync today decodes what it fetches and writes text. Files under
   `scripts/term-index-core/` are fetched and written as bytes, and `.gitattributes` marks them `-text`, so
   no line-ending conversion can break a hash.
3. **Each move of the core pin is an S-10 adoption.** The upstream module declares itself beta, and the
   vulnerability scanner sees installed packages, not a copied file. A pin move therefore carries a
   vulnerability search on agentteams at that tag and a recorded `@security` clearance for the beta module.
   The first-party toolchain group lifts only the cooldown. At every researchteam release the manifest's
   commit equals the lock's agentteams commit, so the coverage of the lock covers the copy. (This is the
   proposed answer to open question 6; it is the operator's to confirm.)
4. **Close the gap between cuts.** A repository that is not release-locked syncs from `main`, so a PR that
   changes a copy and the manifest together would reach it before any cut. A CI job filtered to
   `scripts/term-index-core/**` runs the network form of L2 on every such pull request, and the operator is
   asked to add that directory to PS-2's list of paths that need a `@security` PASS. (Proposed answer to
   open question 5; adding a CI job and changing PS-2 both need their own reviews.)
5. **Loading twice in one process.** Tests load the scripts in-process. The loader's cache key is the
   resolved directory plus the manifest's sha256, and L1's tests that expect a failure run in a subprocess.
6. **A shim that changes no process-wide state.** Preferred over the `sys.modules` swap, if it tests clean
   on 3.10 to 3.14: give `term_index`'s own globals a `__builtins__` mapping whose `__import__` returns the
   pinned module for `agentteams._term_text`. It also covers a lazy import added upstream later. The
   `sys.modules` swap, probed on 3.13 and 3.14, stays as the fallback.
7. **Loader details.** Compile with `dont_inherit=True`. Open each file with `O_NOFOLLOW` and check it with
   `fstat` on the same descriptor. Give the modules a loader whose `get_source` returns the checked bytes,
   so tracebacks show what ran.
8. **Only the network form proves upstream equality.** Comparing with an installed package is circular if
   the copy was taken from that install. L2 and L3 are satisfied only by the signed tag.
9. **Doctor.** The precedent for a check that can fail is `_check_frozen_surfaces(root, ok, warn, fail)`.
   When the lock has no `agentteams.tag=` (the pin PR drops and rewrites it), doctor prints the manifest's
   tag and says the lock names none. When the core check fails, the term-index check stays quiet, so one
   fault is reported once.
10. **The NOREG gap.** The adapter branches on MISSING and FOREIGN from `load_register`, which reads only
    the register, and calls the core's `check_project` only for a register that loads. No document is
    scanned twice, and no private core function is used.

