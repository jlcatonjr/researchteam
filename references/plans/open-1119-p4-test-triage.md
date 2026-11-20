# P4 step 1: static triage of the test suite (read-only)

Finding for P4 step 1 (`technical-validator`, 2026-11-20).

I read the plan first: `references/plans/open-1119-p4-unreproduced-test-failure.plan.md`. I wrote no files.

**What I read.**
- **Read in full:** `conftest.py`, `test_agentteams_provenance.py`, `test_release_lock.py`, `test_toolchain.py`, `test_scaffold_fixes.py`, `test_reviewed_commit.py`, `test_frozen_surfaces.py`, `test_drift.py`, `test_init_fetch.py`, `test_sign_key.py`, `test_trust_root_step.py`, `test_derived_workflow.py`, `test_conflict_log.py`, `test_autosync_no_pr_alert.py`, `test_doctor_informational.py`, `test_bridge_validate_hooks.py`, `test_version.py`, `test_module_entry.py`, `test_init_signing_steps.py`, `test_init_adopt.py`, `test_update_native_surfaces.py`, `test_layer1_opt_out.py`.
- **Read in part:**
  - `test_notes.py`, lines 1–577
  - `test_term_index.py`, lines 19–78, 600–760 and 805–1002
  - `test_bibliography_explorer.py`, lines 1–40, 160–189 and 240–369
  - `test_autosync_evergreen_baseline.py`, lines 20–124
  - `test_autosync_job_split.py`, lines 18–107
  - `test_materialize_surfaces.py`, lines 1–60
  - `test_update_gitignore_preserve.py`, lines 155–179
  - `test_init_personalization.py`, lines 225–249
- **Seen only through pattern searches:** `test_workflow_sync.py`, `test_docs_site.py`, `test_workflow_action_pins.py`, `test_library_query_args.py`, `test_library_query_smoke.py`, `test_marker_reader.py`, `test_citation_integrity_suite.py`, `test_literature_library_suite.py`.
- I also read the code these tests call: `researchteam/_release.py`, `_fetch.py`, `_agentteams_provenance.py`, parts of `_update_cmd.py`, `_doctor_cmd.py` and `_notes.py`, plus `scripts/check_toolchain.py`, `agentteams_autosync_gate.sh`, `bootstrap_toolchain.sh`, `claude_researchteam_bridge.sh` and `sign_security_decision.py`.

**One of the facts you gave does not hold.** No test file inserts the repository root into `sys.path`.
- Only `scripts/` gets inserted: permanently by `test_bibliography_explorer.py:21`, and temporarily (restored) by `test_term_index.py:33-48`.
- `tests/` is on `sys.path` only through pytest's default prepend mode. `test_reviewed_commit.py:86` depends on that.
- So which `researchteam` gets imported depends on how pytest is started:
  - `python -m pytest` run from the repository root puts the current directory on `sys.path`, so the checkout is imported.
  - A bare `pytest` imports whatever `researchteam` that interpreter has installed. If it has none, about 30 files fail to collect.

## Clean list (touches none of N/C/E/H/A/R/O)

- `test_init_signing_steps.py`
- `test_library_query_args.py` (only seen through searches; it loads a script by path)
- `test_marker_reader.py` (only seen through searches; its one `chdir` is restored by monkeypatch)

## Item 2: tests that touch something

Risk marks: **HIGH** = not isolated and can fail from machine state or timing; **MED** = isolated except for one plausible leak, or fails only if a specific variable is set; **LOW** = isolated, or the leak cannot change the result.

| file | test (file:line) | touches | isolated? | risk | note |
|---|---|---|---|---|---|
| conftest.py | `_offline_github_api` :5 (autouse) | E,N | monkeypatch | LOW | Points `RESEARCHTEAM_GITHUB_API` at `127.0.0.1:9` and removes `GITHUB_TOKEN`/`GH_TOKEN`. Only covers api.github.com: raw.githubusercontent.com and archive downloads are not covered, and proxy variables are not cleared. |
| test_agentteams_provenance.py | `fake_agentteams`/`g` :18-70 (used by every test) | E,H | tmp_path, `-c user.*` | LOW | Real git with the user's global and system config. |
| test_agentteams_provenance.py | :85, :91, :101, :114, :122, :128, :134, :155, :165, :173, :184, :192, :200, :210, :222, :230 | E,A,N | monkeypatch PATH/PYTHONPATH, tmp_path | LOW | Runs a `--inner` subprocess under `sys.executable` with the rest of the environment inherited. The fake dist-info and package are first on PYTHONPATH, so they shadow a real agentteams. VCS cases ask port 9 and get "could not confirm". |
| test_agentteams_provenance.py | `test_an_unverifiable_install_runs_only_with_its_own_override` :285 (3 params) | E | **NOT** for `RESEARCHTEAM_ALLOW_UNVERIFIED_AGENTTEAMS` | MED | The first assertion expects a refusal with only the snapshot override set. If the session exports `…UNVERIFIED…=1`, all 3 params fail. |
| test_agentteams_provenance.py | :140, :148, :277 | E | delenv/explicit | LOW | |
| test_agentteams_provenance.py | `test_preflight_checks_the_launcher_it_will_execute` :240 | E,O | monkeypatch (PATH, sys.executable, `_VERIFIED_LAUNCHERS`) | LOW | |
| test_autosync_evergreen_baseline.py | fixture :33 plus :80, :87, :96, :106, :115 | E,N(gh) | strips GITHUB_OUTPUT, AUTOSYNC_* and tokens; neutral git config; `PATH=bin:/usr/bin:/bin`; gh stubbed; local "remote" | LOW | Well isolated. |
| test_autosync_job_split.py | `repos` :38 and the package/apply tests | E | neutral git config, TMPDIR set | LOW | |
| test_autosync_no_pr_alert.py | `test_alert_script` :34 | E | `env={PATH:/usr/bin:/bin,…}` | LOW | |
| test_bibliography_explorer.py | module level :21 | O | **NOT** (never removed) | LOW | `scripts/` stays first on `sys.path` for the whole session. Nothing in `scripts/` shadows another import. Also writes `ROOT/scripts/__pycache__`. |
| test_bibliography_explorer.py | :172, :250, :261, :272, :282, :334 | R | tmp_path outputs | LOW | :172 compares against the committed example; :358 hashes tracked files. |
| test_bridge_validate_hooks.py | `test_validate_passes_with_no_register_and_fails_on_a_stale_index` :110, `test_term_commands_dispatch` :135 | E,O | **NOT** for `RT_ROOT` | MED | `validate` clears `RT_ROOT` itself, but `term-build/check/query` (bridge :205) pass it through. If it is exported, the build writes into that root, outside tmp_path, and the assertions fail. |
| test_bridge_validate_hooks.py | :36-:69, :103, :126, :149 | E | tmp copy; :126 sets env | LOW | Uses `python3` from PATH (stdlib scripts). |
| test_citation_integrity_suite.py / test_literature_library_suite.py | :11-14 each | E,O | skipif no bash | LOW | `mktemp -d` under $TMPDIR, outside tmp_path. Timeout 300 s. No network in the scripts. |
| test_conflict_log.py | `test_conflict_log_header_matches_the_agent_doc` :10 | R | **NOT** | **HIGH** (under H1) | Reads `.github/agents/conflict-auditor.agent.md` and `references/conflict-log.csv` live. A regeneration rewrites these. |
| test_derived_workflow.py | `upstream` :38 plus :86, :93, :101, :109, :115, :124, :130 | E,O | neutral git config, PATH shim, signers env stripped or set | LOW | Local git "remote", so no network. On refusal paths the step's `mktemp -d` dir is left in $TMPDIR. |
| test_doctor_informational.py | `test_doctor_does_not_fail_without_scholarly_tooling` :67 | E | partly | LOW | Real `which("pandoc")` and a `pandoc --version` run. |
| test_doctor_informational.py | :36, :120, :138, :164 | E | patched / explicit env | LOW | |
| test_drift.py | `test_doctor_lists_frozen_fences_with_intent_and_release_entry` :112 | C | **NOT** (`date.today()`) | LOW | Only a midnight crossing could matter, and nothing asserts on the age. |
| test_drift.py | :164, :232, :244, :57, :128, :253, :281, :300, :339, :382, :432, :450 | N | fetch/subprocess patched | LOW | |
| test_frozen_surfaces.py | `test_agentteams_1_0_0_cannot_verify_an_unfreeze_so_it_refuses` :238 | E,A | skipped unless `RT_TEST_AGENTTEAMS_PYTHON` | MED | If that variable names an agentteams newer than 1.0.0, which does derive the unfreeze, the test fails. |
| test_frozen_surfaces.py | :271 (git), :296 (fetch patched), the rest | E,N | tmp_path / patched | LOW | |
| test_init_adopt.py | `test_no_repository_gets_git_init_but_no_commit` :109, `test_a_subdirectory_of_a_repository_gets_no_nested_git_init` :246 | E,O | **NOT** for where basetemp sits | LOW | Fails if pytest's basetemp is inside a git worktree. |
| test_init_adopt.py | fixture :34 and the rest | O | monkeypatch.chdir, fetch patched | LOW | :281 `example.invalid` remote is ignored, never contacted. |
| test_init_fetch.py | all | N,C,O | urlopen/fetch/sleep/chdir patched | LOW | |
| test_init_personalization.py | `test_historical_context_protocol_is_scholarly_managed` :233 | R | NOT | LOW | Compares the CLAUDE.md managed block with the template. |
| test_layer1_opt_out.py | :34, :39, :44, :55, :64 | E | patched | LOW | |
| test_library_query_smoke.py | :46-54 | E | explicit `RT_ROOT` | LOW | |
| test_materialize_surfaces.py | `calls` :21 | A | subprocess and preflight patched | LOW | |
| test_module_entry.py | :15, :22 | A | `cwd=ROOT` puts the checkout first | LOW | |
| test_notes.py | module level :445-447 | R | **NOT** | MED | Reads the live advisor at import time. A file being rewritten, or one missing its block, gives a *collection error* for the whole file. |
| test_notes.py | `test_upstream_blocks_exist_and_every_surface_carries_the_same_block` :156 (one per NOTES_AGENT) | R | **NOT** | **HIGH** (under H1) | Compares `.github`, `.claude` and `.goose` copies live. |
| test_notes.py | `test_researchteams_own_repo_is_unchanged` :560 | R | **NOT** | **HIGH** (under H1) | Copies the live surfaces and requires the sync to leave them unchanged. |
| test_notes.py | :412 (one per MANAGED_FILES), :362, :379, :423, :429 | R | NOT | MED | Read the live agent files and brief. |
| test_notes.py | :59 and the other tmp tests | C | tmp_path | LOW | Backup folder name comes from `datetime.now`. |
| test_release_lock.py | :13 module-level script load | O | — | LOW | Writes bytecode into `ROOT/scripts`. |
| test_release_lock.py | :35-:203, :272, :282, :362-:406 | N,E,H | `remote_tags`/`_git`/`verify_tag` patched; `AGENTTEAMS_ALLOWED_SIGNERS` set | LOW | No ls-remote or fetch runs for real. |
| test_release_lock.py | gate tests :320-:592 (`_gate_repo` :295) | E,O,N | partly | MED | Real bash and git with global config. Only `AUTOSYNC_GATE_REEXEC` and `GITHUB_OUTPUT` are popped; `AUTOSYNC_PR_BODY_FILE` and `GITHUB_STEP_SUMMARY` are not. If the body-file variable is set, :498, :506, :545 and :584 fail. ls-remote is shimmed (:347, :476). The `$HOME` signers fallback is never reached because :490 sets the variable. |
| test_reviewed_commit.py | `fake_api` :15, used by :49, :54, :60, :64, :72 | N,E | **NOT** for proxy variables | MED | urllib follows `http_proxy`/`HTTP_PROXY`/`ALL_PROXY`. If one is set and `no_proxy` does not cover 127.0.0.1, these 5 fail together. |
| test_reviewed_commit.py | `test_the_provenance_guard_checks_the_vcs_commit` :82 (3 params) | O,A | sys.path monkeypatched; `sys.modules.pop("agentteams","build_team")` not restored | LOW | `find_spec` imports nothing; the fake path comes first. |
| test_scaffold_fixes.py | `test_signer_appends_verified_row` :36 | A,E,C | skipped when agentteams is absent | **HIGH** locally | The one test that needs agentteams (item 3). Inherits every `AGENTTEAMS_*` variable except the signing key. |
| test_scaffold_fixes.py | :50, :59, :89-:143, :153-:210 | E | subprocess env mostly inherited | LOW | |
| test_scaffold_fixes.py | :65 | O,N | chdir and fetch patched | LOW | |
| test_scaffold_fixes.py | :212, :219, :225 | R | NOT | LOW | Read `docs/` and `.claude/skills`. |
| test_sign_key.py | :26 | E | monkeypatch | LOW | |
| test_term_index.py | `test_matching_time_grows_no_faster_than_the_input` :711 (16 shapes) | C | **NOT** (wall clock) | **HIGH/MED** | Asserts `large < 8*small + 0.25` s, best of 3. CPU contention, for example a regeneration running at the same time, can break it for one shape. |
| test_term_index.py | `test_scope_globs` :614, `test_bib_keys_are_linear` :734 | C | NOT | MED/LOW | Each asserts it runs in under 5 s. |
| test_term_index.py | `test_this_repositorys_projects_pass_the_gate` :997 | R | **NOT** | MED | Runs the gate on the live `Projects/`. Fails if a document or register changed without a rebuild. |
| test_term_index.py | `test_a_discouraged_form_seeded_into_a_real_project_fails_the_gate` :830 | R | NOT | MED | Copies the live `Projects/CodedTermIndexing`. |
| test_term_index.py | `run` :68 (all subprocess tests), :743, :807, :932 (skips if root), :862, :887, :898, :974 | E,R | `RT_ROOT` set, advisory flag stripped | LOW | |
| test_toolchain.py | `test_launcher_interpreter_follows_every_shebang_form` :161 | E | NOT | LOW | `which("python3")`. |
| test_toolchain.py | `test_probe_ignores_a_stray_egg_info_in_the_working_directory` :340 | A | monkeypatch.chdir | LOW | Probes the real interpreter's installed researchteam and agentteams metadata. |
| test_toolchain.py | :46, :62, :74, :178, :202, :215, :326 | N,E | `LOCK`, `installed` and `remote_main` patched or `--no-remote` | LOW | No real ls-remote. |
| test_toolchain.py | :116, :148, :225, :260, :275, :299, :308 | E,O | fake `.venv/bin/python`; env inherited (`*_SRC` stripped at :154) | LOW | `mktemp` under $TMPDIR, removed by a trap. |
| test_toolchain.py | :129, :139 | E | monkeypatch PATH and `sys.executable` | LOW | |
| test_toolchain.py | :29, :86, :103, :235, :283, :292, :336, :412, :431, :443 | R | NOT | LOW | |
| test_trust_root_step.py | :64-:103 | E | env set; temporary ssh-keygen keys | LOW | Never reads home. |
| test_update_gitignore_preserve.py | `test_managed_block_ignores_env_files_but_not_templates` :157 | E,H,R | **NOT** | LOW | `git check-ignore` uses the global excludes file (`~/.config/git/ignore`). |
| test_update_native_surfaces.py | `test_update_renders_native_surfaces_in_merge_mode[layer1_only=False]` :58 | **N** | **NOT** | LOW for failure; this is the hardening target | Real `fetch_raw` to raw.githubusercontent.com (item 5). |
| test_update_native_surfaces.py | :59[True], :71, :78, :86, :98, :119 | A,R | subprocess and preflight patched | LOW | |
| test_version.py | `test_source_archives_carry_the_ref` :34 | R | NOT | LOW in a checkout; **certain failure in a `git archive` extract** | `export-subst` replaces `$Format:%H$` (step 2 note below). |
| test_version.py | `test_package_reports_a_version` :30 | A | — | LOW | The version comes from installed metadata, which may be stale. |
| test_workflow_sync.py | `test_packaged_scaffold_is_the_repo_file` :54, :236 | A,R | NOT | LOW | Fails only if a stale installed `researchteam` is the one imported. |
| test_workflow_sync.py | :219, :289 | O | monkeypatch.chdir | LOW | |
| test_docs_site.py / test_workflow_action_pins.py | all | R | NOT | LOW | Read docs and workflow files only. |

## Item 3: the one test that needs agentteams

It is `tests/test_scaffold_fixes.py:36`, `test_signer_appends_verified_row`. It is the only test that calls `pytest.importorskip("agentteams")`. A second test, `test_frozen_surfaces.py:238`, is gated by an environment variable rather than by agentteams being present.

When agentteams **is** importable at a version other than the lock's pin, the test runs instead of skipping:

1. It runs `scripts/sign_security_decision.py --action overwrite --conditions test` as a subprocess under `sys.executable`, in a temporary workspace.
   - Only `AGENTTEAMS_DECISION_SIGNING_KEY` is replaced, with a 39-byte throwaway key. Every other `AGENTTEAMS_*` variable from the session is inherited.
   - The script imports `agentteams.cli.decision_log.sign_decision_row` and `agentteams.cli.security_gate.check_clearance` from that arbitrary version.
   - It appends an HMAC-signed PASS row and calls `check_clearance(<ws>/.github/agents, action="overwrite")`.
2. The test asserts `returncode == 0`, that the old VOID row was kept, and that the new row is a PASS with a 64-character signature.
3. It then imports `check_clearance` in the test process, sets a different key, and asserts `not ok` and that `"signature verification"` appears in the reason.

It fails if that version:
- lacks either function (the script exits 1 with "agentteams is not importable"), or
- rejects the row, for example over author rules, the key or placeholder rules, a hash-chained log or required columns (the script rolls back and exits 1), or
- words the refusal differently. The local checkout today says "…failed signature verification", which matches.

**Unverified:** whether any given agentteams version's `check_clearance` reads home-directory config.

In CI, and under `/opt/homebrew/bin/python3`, the test is skipped. That fits a failure that showed once and never came back.

## Item 4: top five candidates

1. **`test_scaffold_fixes.py:36` (hypotheses 2 and 5).**
   - **Would fail if:** the run used the other repository's virtualenv, where agentteams is an editable install of the local checkout on whatever branch it had then (around PR #214), and that code's signer or gate API, its acceptance of the row, or its refusal wording differed.
   - Every later run in CI or under Homebrew's python skips this test, so it would never fail again.
2. **`test_notes.py:156` (one per agent) and `test_notes.py:560`, plus the import-time read at :445-447 (hypothesis 1).**
   - **Would fail if:** the regeneration had rewritten a canonical `.github/agents/*.agent.md`, or its `.claude` or `.goose` copy, but had not yet written the Notes blocks, which go last.
   - One out-of-sync agent gives exactly one parametrized failure. A file read mid-write at import gives "1 error", which is easy to report as one failure.
3. **`test_conflict_log.py:10` (hypothesis 1).**
   - **Would fail if:** `conflict-auditor.agent.md` was truncated or mid-render, or was re-rendered without the "with columns:" line, or `conflict-log.csv` was touched while the test read it.
4. **`test_term_index.py:711` (16 shapes), plus :614 and :734 (timing, the closest fit for hypothesis 4).**
   - **Would fail if:** CPU contention, for example from the regeneration running at the same moment, made the best of three runs on the large input slower than 8 × small + 0.25 s for one shape, or pushed a glob or bib-key check over 5 s.
   - Each shape is its own test, so one failure is plausible.
5. **`test_term_index.py:997`, `test_this_repositorys_projects_pass_the_gate` (hypothesis 1, live tree).**
   - **Would fail if:** a document or term register under `Projects/` was edited in the session's working tree without `term-build`. It reports STALE until someone rebuilds.

**Environment-variable cases (hypothesis 4).** These fail only if the session exported the variable, and most would fail in groups rather than alone:
- `RESEARCHTEAM_ALLOW_UNVERIFIED_AGENTTEAMS=1`: 3 provenance params fail.
- `RT_TEST_AGENTTEAMS_PYTHON`: the frozen-surfaces test at :238 fails.
- `AUTOSYNC_PR_BODY_FILE`: 4 gate tests fail.
- `RT_ROOT`: 2 bridge tests fail.
- A proxy without `no_proxy` covering 127.0.0.1: 5 reviewed-commit tests fail.

**Hypothesis 3 (network timeout or rate limit) has no viable candidate.** The GitHub API is pinned to `127.0.0.1:9`. Every ls-remote or fetch is patched or shimmed. The one real request (item 5) catches its own errors.

**The stale-researchteam half of hypothesis 5 is unlikely.** Importing an installed researchteam instead of the checkout would cause many failures or collection errors, not one. The only tests that would single it out are `test_workflow_sync.py:54` and :236.

## Item 5: home-directory and network hardening targets

**The release signers file.** No test needs the real `~/.config/agentteams/allowed_signers`. Every path that could read it is overridden:
- `_release.allowed_signers_path` reads `AGENTTEAMS_ALLOWED_SIGNERS`, which fixtures set; `test_release_lock.py:97` points it at a missing file on purpose.
- The gate's `$HOME` fallback is never reached: `_gate_group_run` sets the variable at :490, and the install-gate runs exit before that point.
- The derived-workflow tests remove or set the variable.
- The trust-root step uses `ALLOWED_SIGNERS`.

So a scratch HOME makes no test fail or skip because of the signers file. Two caveats I could not check:
- A scratch HOME also removes the global git config and excludes file. That is harmless here, because every commit passes `-c user.*`.
- It also hides Homebrew python's per-user site-packages under `~/Library/Python`. If pytest or pyyaml were installed there with `--user`, they would disappear.

**Writes to the real home directory:** none found. Writes that land outside tmp_path but not in home:
- bytecode in `ROOT/scripts/__pycache__`;
- `mktemp` directories in $TMPDIR;
- in CI, an append to `GITHUB_STEP_SUMMARY`;
- if `RT_ROOT` is exported, the term-build writes from the bridge tests.

**Real network with no skip marker: exactly one test**, `tests/test_update_native_surfaces.py:58`, the `test_update_renders_native_surfaces_in_merge_mode[layer1_only=False]` case.
- `run_update` runs its layer-2 pass, then `_update_cmd._sync_notes`, which calls the unpatched `fetch_raw`.
- That sends a GET to `https://raw.githubusercontent.com/jlcatonjr/researchteam/main/.github/agents/<agent>.agent.md` for every NOTES_AGENT. The test brief has no `components`, so all of them are fetched.
- Errors are caught, so the test cannot fail. But if the network hangs, it can stall about 41.5 s per agent (two 20 s attempts plus a 1.5 s pause).
- The fix: patch `_update_cmd.fetch_raw` (or `_sync_notes`) in the `calls` fixture at :29. The conftest gap is the same one: it covers only api.github.com.
- Every other request in the suite goes to loopback or to a local git path.

**For the step-2 runs:**
- `test_version.py:34` will fail every time in a `git archive` extract, because `.gitattributes` marks `.git_archival.txt` `export-subst`. Either expect that failure or restore the file's `$Format` text before the runs.
- Unset these first: `RT_ROOT`, `TERM_INDEX_ADVISORY`, `AUTOSYNC_PR_BODY_FILE`, `RESEARCHTEAM_ALLOW_*`, `RT_TEST_AGENTTEAMS_PYTHON` and the proxy variables.
- Keep pytest's basetemp outside every git worktree.
- Record which interpreter ran, and whether `agentteams` was importable in it, because that decides whether candidate 1 runs at all.
