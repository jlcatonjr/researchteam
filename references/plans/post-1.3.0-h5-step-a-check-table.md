# H5 step A: check table (survey toolkit against `docs/survey-toolkit.md`, version 1)

Plan: `post-1.3.0-h5-survey-tools-a-d.plan.md`, step A. One row per check, error, rule id or output shape in step
A's scope (contract sections 1, 3, 6.1, the structural part of 6.2, and 7 for `survey-validate`, `survey-status`
and `survey-manifest`). Line numbers are those of `docs/survey-toolkit.md` at the commit this branch was cut from.
Error ids are the toolkit's own: the contract gives ids only for the evidence rules of 4.1 (step B), none for
section 3 or 6. Tests are in `tests/test_survey_core.py` (core), `tests/test_survey_spec.py` (spec) and
`tests/test_survey_gates.py` (gates); a test name with `[...]` is one parametrized case.

"Silent" marks a behaviour the contract does not fix: step A takes the narrowest safe reading (usually a refusal)
and the point is listed under *Proposed contract changes* at the end.

## Rules that hold everywhere (section 1)

| Section, line | What is checked | Error id or message | Test |
|---|---|---|---|
| 1.2, 28 | A violation exits non-zero and writes nothing | exit 1; `REFUSED` | gates `test_manifest_refuses_and_writes_nothing`, `test_validate_and_status_write_nothing` |
| 1.4, 33 | No tool writes a sign-off | `survey-manifest` writes no ledger row | gates `test_manifest_writes_the_file_and_prints_what_the_operator_signs` |
| 1.5, 36 | Same inputs, byte-identical outputs; no clock | manifest bytes equal across runs and repositories | gates `test_manifest_is_deterministic`; spec `test_the_schema_generator_is_deterministic` |
| 1.6, 40 | Relative to the study folder, or `repo:`-rooted | — | core `test_paths_are_study_relative_or_repo_rooted` |
| 1.6, 41 | Absolute path | `path-absolute` | core `test_path_rule_errors[/etc/passwd-...]`; spec `test_paths_in_the_specification_follow_rule_1_6` |
| 1.6, 41 | `..` segment | `path-dotdot` | core `test_path_rule_errors[../x-...]`; spec `test_paths_in_the_specification_follow_rule_1_6` |
| 1.6, 41 | Resolves outside the repository through a link | `path-outside` | core `test_a_path_that_leaves_the_repository_through_a_link_is_an_error` |
| 1.6, 42 | In a draft as much as in an active study | `path-dotdot` in a draft | spec `test_a_draft_is_held_to_the_path_rule_too` |
| 1.6, 43 | Two paths are the same file when they resolve to the same place, however each is written: an existing file by device and inode (`file_identity`), so two spellings on a case-insensitive file system are one file; a missing one by its real path | — | core `test_paths_are_study_relative_or_repo_rooted`, `test_two_spellings_on_a_case_insensitive_file_system_are_one_file` (skipped on a case-sensitive file system), `test_a_place_that_does_not_exist_is_identified_by_its_real_path`; spec `test_coverage_is_judged_on_resolved_paths`; gates `test_the_manifest_is_exactly_the_6_1_object`, `test_repeats_are_removed_by_file_identity_not_spelling` |
| 1.6 (proposal 12) | A backslash in a path | `path-backslash` | core `test_path_rule_errors[sub\\f.csv-...]` |
| 1.6 (proposal 12) | A NUL in a path | `path-nul` | core `test_path_rule_errors[sub/\x00f.csv-...]` |
| 1.6, 6.1 804 (proposal 2) | A `.` or empty segment (doubled or trailing slash): refused, so a manifest carries the path as declared | `path-segment` | core `test_path_rule_errors[./sub/f.csv-...]` and three more; spec `test_dot_segments_in_a_declared_path_are_refused` |
| 1.6 (silent) | `repo:` with nothing after it | `path-empty` | core `test_path_rule_errors[repo:-...]` |
| 1.7, 44 | Standard library only; Python 3.10 grammar | — | core `test_the_code_is_python_3_10_syntax_and_standard_library_only` |
| 1.8, 47 | Invented example study only | fixture `tests/fixtures/survey/example/` | spec `test_the_invented_example_study_is_valid` |
| 1.10, 53 | Folded text, with and without spaces, pinned on a fixed sample | `cavat-il ete sur ? marz` | core `test_fold_pins_a_fixed_sample` |
| plan | The Unicode database is reported | `environment: python …, unicodedata …` | core `test_environment_reports_the_unicode_database`; gates `test_status_prints_hash_state_enforce_and_mode_and_the_environment` |

## The specification: loading and shape (section 3)

| Section, line | What is checked | Error id or message | Test |
|---|---|---|---|
| 3, 79 | Location `Projects/<project>/study.json` | exit 2 `no specification at …` | gates `test_manifest_usage_errors_exit_2[absent-S0]` |
| 3, 79 | A project name is matched whole (a trailing line feed does not pass) | exit 2 | spec `test_a_project_name_with_a_trailing_line_feed_is_refused` |
| (proposal 15) | A specification over `MAX_JSON_BYTES` (16 MiB) is not read | `too-large` | spec `test_a_specification_over_the_cap_is_not_read` |
| (proposal 15) | JSON nested too deeply to parse | `json` | core `test_json_nested_too_deeply_is_a_finding_not_a_crash` |
| 3, 80 | Unknown keys at every level (not inside `analysis`, `merges`, `strata`, `exclude_from_rollup`) | `unknown-key` | spec `test_shared_invalid_specifications_fail_with_the_named_rule[unknown-key--*]` |
| 3, 80 | `schema_version` `"1"` or `"0"`, read identically | `enum` | spec `[enum--schema-version-2]`, `test_schema_version_0_is_read_like_1` |
| 3, 83 | A draft only by `status` | — | spec `test_a_draft_may_name_files_that_do_not_exist_yet` |
| 3, 85 | A JSON Schema (2020-12) published beside the validator | `scripts/survey/study.schema.json` | spec `test_the_tracked_schema_is_the_generators_output`, `test_every_rule_table_field_appears_in_the_schema`, `test_the_schemas_required_and_enum_sets_equal_the_rule_tables` (no schema library needed) |
| 3, 86 | A shared set of valid and invalid specifications | `tests/fixtures/survey/specs/` | spec `test_shared_valid_specifications_pass_the_shape_checks`, `test_shared_invalid_specifications_fail_with_the_named_rule`, `test_a_json_schema_library_gives_the_same_verdict` (skipped without a library) |
| 3, 89 | `slug` pattern | `pattern` | spec `[pattern--id-not-slug]` |
| 3, 91-179 | Types | `type` | spec `[type--cuts-string]`, `[type--window-float]`, `[type--vantage-module-string]`, `[type--analysis-array]` |
| 3, 91-179 | Required fields | `required` | spec `[required--no-signoffs]`, `[required--no-frame-change-log]`, `[required--level-label]` |
| 3, 91-179 | Enumerations of values | `enum` | spec `[enum--status]`, `[enum--enforce]`, `[enum--bucketer-kind]`, `[enum--basis]` |
| 3, 115-116 | `rounds_without_new` ≥ 1; `min_new_share` 0..1 | `minimum`, `maximum` | spec `[minimum--rounds-zero]`, `[maximum--share-above-one]` |
| 3, 122 | `reader` required when `format` is `plugin` | `reader-missing` | spec `[reader-missing--plugin-format]`, `test_each_check_beyond_shape_is_triggered[reader-missing]` |
| 3, 136 | At least 2 levels | `min-items` | spec `[min-items--one-level]` |
| 3, 141 | `present_code` required for `any-present` | `present-code-missing` | spec `[present-code-missing--any-present]` |
| 3, 167 | Gates only `S0`, `S5`, `S6`, `S8` | `unknown-key` | spec `[unknown-key--gate-s3]` |
| 3, 173-176 | Bucketer and plug-in shapes | `unknown-key`, `pattern`, `empty` | spec `[unknown-key--bucketer-foreign-field]`, `[pattern--plugin-attr]`, `[empty--plugin-version]` |
| 3, 181 | ≥1 enumeration, outcome, attribute, cut; ≥2 labels | `min-items` | spec `[min-items--no-enumerations]`, `[min-items--one-label]` |
| 3, 182 | A level set has ≥1 level; each `exclude_from_rollup` list ≥1 value | `min-items` | spec `[min-items--empty-exclude-list]` |
| 3, 183 | `title`, `question`, every path, a plug-in's `version` not empty | `empty` | spec `[empty--title]`, `[empty--path]`, `[empty--plugin-version]` |
| 3, 184 | Plug-in `attr` pattern | `pattern` | spec `[pattern--plugin-attr]` |
| 3, 184 | A bucketer carries only the fields of its own kind | `unknown-key` | spec `[unknown-key--bucketer-foreign-field]` |
| (proposal 13) | A key given twice in one JSON object; `NaN` | `json-duplicate-key`, `json` | spec `test_malformed_json_and_duplicate_keys_are_errors`; core `test_strict_json_refuses_duplicate_keys_and_nan` |

## Checks beyond shape (section 3, lines 186-227)

Every id below is triggered by `test_each_check_beyond_shape_is_triggered[<id>]` in `tests/test_survey_spec.py`,
which also runs `survey-validate` and checks exit 1; `test_every_semantic_rule_has_a_case` proves the list is
complete against `SEMANTIC_RULES`.

| Line | What is checked | Error id |
|---|---|---|
| 188 | A key used twice among outcomes and attributes | `key-duplicate` |
| 188 | A level code used twice within an outcome | `level-duplicate` |
| 189 | `max-order` without `ordinal` | `max-order-scale` |
| 189 | `max-order` with a level without `order` | `max-order-order` |
| 190 | A merge source that is not a level or NA code | `merge-source` |
| 191 | `cuts` not strictly ascending | `cuts-order` |
| 191 | `labels` not one longer than `cuts` | `labels-count` |
| 191-192 | A `strata` key that is not a period number 1..n | `strata-key` |
| 193 | A passage or work study with no `codes` outcome | `codes-outcome-missing` |
| 194 | `counted_tiers` not a subset of `tiers` | `counted-tiers-subset` |
| 194 | `not_established_tier` not in `tiers` | `ne-tier-undeclared` |
| 194 | `not_established_tier` counted | `ne-tier-counted` |
| 195 | `any-present` without a `present_code` | `present-code-missing` |
| 195 | A `present_code` that is not a level code | `present-code-level` |
| 196 | A `present_code` on any other rollup | `present-code-unexpected` |
| 197 | An `exclude_from_rollup` key that is not a `passage_attributes` key | `exclude-key` |
| 197-198 | A value that is not one of its level codes | `exclude-value` |
| 198, 210 | A level code `mixed`; an NA or missing code `mixed` | `mixed-code` |
| 199 | `any-present` on an ordinal outcome with a level without `order` | `any-present-order` |
| 200 | `rollup_types` not a `passage_attributes` key | `rollup-types-key` |
| 200 | A `rollup_by` entry not a `passage_attributes` key | `rollup-by-key` |
| 201 | More than one `period` attribute | `period-multiple` |
| 201-202 | A `period` attribute without a `period` bucketer, or the reverse | `period-bucketer` |
| 203-206 | Two frame columns with the same name (every example of the contract is a case of `test_frame_column_collisions_from_the_contract_examples`) | `frame-column-duplicate` |
| 207 | `match: "all"` on an attribute that is not `flags` | `match-all` |
| 207-208 | `match: "first"` on a flags attribute | `match-first-flags` |
| 208 | A `fallback` on a flags attribute | `fallback-flags` |
| 209 | Level, NA and missing codes not all different | `outcome-codes-distinct` |
| 210 | An attribute whose `missing` is one of its levels or flags | `attribute-missing` |
| 211 | A `|` in a level code of a `rollup_by` level set | `rollup-by-pipe` |
| 212 | A passage or work study with an exclusion rule other than `not-on-question` | `exclude-rule-cells` |
| 214 | A passage or work study without `unit.attribution` | `attribution-missing` |
| 215 | `saturation` without both fields | `saturation-fields` |
| 216 | `legacy-unrecorded` in a study that is not `legacy` | `legacy-unrecorded-status` |
| 217-219 | A referenced input file that does not exist, unless `draft`; the six that may be absent | `file-missing` (also `test_files_that_a_stage_writes_may_be_absent`, `test_a_draft_may_name_files_that_do_not_exist_yet`) |
| 220-222 | A plug-in, bucket table, vocabulary or stop-words file not covered by S0, judged by file identity | `not-covered-s0` (also `test_coverage_is_judged_on_resolved_paths`, and `test_plugin_files_must_be_covered_by_s0[reader]`, `[bucketer]`, `[vantage]` for `/evidence/reader/file`, `/attributes/*/bucketer/plugin/file`, `/vantage/module/file`) |
| 223 | Evidence that cites a fetch receipt when `evidence.receipts` is not declared | **not implemented: step B.** 5.4 (lines 770-772) decides what citing is: a row whose `locator` is not a text-store locus (`<work slug>#p<N>`) is checked against the fetch receipt for its `url` and quote. The check reads evidence rows, which step B reads |
| 224 | `legacy_exceptions` in a study that is not `legacy` | `legacy-exceptions-status` |
| 224-225 | `legacy_exceptions` naming a file no gate covers | `legacy-exceptions-uncovered` |
| 226 | A `post_steps` file that no gate covers | `post-step-uncovered` |
| 227 (proposal 8) | A gate that covers no file, in every status | `covers-empty` |
| 227 | A `covers` path that does not exist, unless `draft` | `covers-missing` |
| 803 (proposal 6) | A `covers` path that exists but is not a regular file | `covers-not-file` |
| 122 (proposal 5) | `evidence.reader` when `format` is not `plugin` | `reader-unexpected` (also spec `[reader-unexpected--csv-format]`) |
| 4.8 690, 207-208 (proposal 7) | A flags attribute's table bucketer without `match` (its default would be `first`) | `match-missing-flags` |

## Gates and manifests (6.1)

| Section, line | What is checked | Error id or message | Test |
|---|---|---|---|
| 6.1, 786-791 | The gate list S0, S5, S6, S8, defined once (`survey_core.GATES`) | `GATES`; exit 2 on another | gates `test_manifest_usage_errors_exit_2[tidebell-S1]`, `test_the_gate_names_have_one_definition` |
| 6.1, 796-800 | Manifest fields `kind, gate, project, mode, schema_version, files` | — | gates `test_the_manifest_is_exactly_the_6_1_object`, `test_the_manifest_carries_schema_version_0_and_the_mode` |
| 6.1, 803 | Specification first, `covers` in declared order, repeats removed (by file identity) | — | gates `test_covers_keep_their_declared_order`, `test_a_repeat_of_the_specification_in_covers_is_removed`, `test_the_manifest_is_exactly_the_6_1_object`, `test_repeats_are_removed_by_file_identity_not_spelling` |
| 6.1, 804-805 | Entry `{path, sha256}`: the repository-relative path as declared (the declared text, after the study folder or with `repo:` removed; never normalised), forward slashes, lower-case hex | — | gates `test_the_manifest_is_exactly_the_6_1_object`, `test_manifest_paths_are_carried_as_declared` |
| 6.1, 807 | Files hashed in chunks; a CRLF split across two chunks still becomes LF | — | core `test_hashing_in_chunks_keeps_a_crlf_split_across_chunks` |
| 6.1, 806 | Canonical JSON | — | core `test_canonical_json_sorts_keys_has_no_white_space_and_one_line_feed` |
| 6.1, 807-809 | CRLF→LF for text files by the fixed suffix list, case-sensitive | — | core `test_text_is_by_suffix_alone_case_sensitive`, `test_text_files_hash_with_crlf_made_lf_and_others_as_they_are`; gates `test_crlf_in_a_covered_text_file_does_not_change_the_manifest` |
| 6.1, 810-811 | Gate identity = SHA-256 of the manifest file's bytes, shown by every command | `manifest_sha256=` | gates `test_status_prints_hash_state_enforce_and_mode_and_the_environment`, `test_manifest_writes_the_file_and_prints_what_the_operator_signs` |
| 6.1, 815 | `CLEARED` | **not reachable in step A** (no verification; seam `survey_gates.verify_signoff`) | gates `test_no_gate_ever_reads_cleared_in_this_version`, `test_the_verification_seam_says_why_it_cannot_clear` |
| 6.1, 816-817 | `UNAVAILABLE`: signatures cannot be verified; ledger malformed | `UNAVAILABLE` with the reason | gates `test_before_any_request_a_declared_gate_is_unavailable`, `test_a_malformed_ledger_leaves_every_gate_unavailable` |
| 6.1, 817-818; 1.5, 38-39 | Files changed since a request: `UNCLEARED` whether or not signatures can be verified. A request is an `agentteams` record (rule 1.5: "the date in a sign-off request, which is a field of `agentteams`"), which step A does not read. **Step A's stand-in:** the manifest file `survey-manifest` last wrote; a gate whose manifest now differs from it, or one of whose listed files is gone, is `UNCLEARED`, and the reason says it is the stored file that was compared. Step F must revisit the order (a code comment in `gate_status` says so): `CLEARED` is "a valid signature exists for the current manifest hash" (815) | `UNCLEARED` | gates `test_a_change_to_a_covered_file_after_the_request_is_uncleared`, `test_an_edit_to_the_specification_unclears_every_requested_gate`, `test_a_covered_file_removed_after_the_request_is_uncleared`, `test_uncleared_holds_even_when_the_ledger_is_malformed` |
| 6.1, 820-821 | Undeclared gate: refuses, except in a legacy study (records `NOT DECLARED`) | `stage_decision` | gates `test_stage_decision_follows_the_6_1_table[NOT DECLARED-*]` |
| 6.1, 823-826 | `blocking` / `build-only` × states | `stage_decision` | gates `test_stage_decision_follows_the_6_1_table`, `test_stage_decision_refuses_unknown_values` |
| 6.1, 828-829 | `mode` written into the manifest | — | gates `test_the_manifest_is_exactly_the_6_1_object` |
| (silent) | A manifest file that is not canonical JSON of the 6.1 shape, for this gate and project | `manifest-malformed` | gates `test_a_malformed_manifest_file`, `test_status_exits_non_zero_only_when_something_is_malformed[manifest]` |

## Sign-offs: the ledger folder's structure (6.2)

| Section, line | What is checked | Error id or message | Test |
|---|---|---|---|
| 6.2, 833-834 | Scope `survey-signoff/<gate>/<study id>`, action `<scope>:sha256-<hash>` | printed by `survey-manifest` | gates `test_scope_and_action_are_the_6_2_names`, `test_manifest_writes_the_file_and_prints_what_the_operator_signs` |
| 6.2, 835 (proposal 1) | The manifest file goes beside the log: `<ledger>/references/<study id>.<gate>.manifest.json`, mode 0644, written atomically after a last check for links | — | gates `test_manifest_writes_the_file_and_prints_what_the_operator_signs`, `test_the_manifest_file_is_mode_0644`, `test_manifest_refuses_when_the_folder_becomes_a_link_before_writing` |
| 6.2, 838 | `signoffs.ledger` is `agentteams-clearance:<path>` | `ledger-form` | gates `test_the_ledger_value[ledger-ledger-form]` and two more |
| (proposal 10) | The ledger folder inside `.git/` or at (or under) a generated team location, compared by case-folded name (`.GIT/`, `.Claude/agents`) and by device and inode against the existing `.git` and team folders | `ledger-location` | gates `test_a_ledger_inside_git_or_a_team_location_is_refused` (three cases), `test_reserved_locations_are_compared_by_case_folded_name`, `test_ordinary_locations_are_not_reserved`, `test_reserved_locations_are_compared_by_identity_on_disk` (skipped on a case-sensitive file system) |
| 6.2, 857-858 | `<path>` under rule 1.6, `repo:` allowed | path ids | gates `test_the_ledger_value[…path-absolute]`, `[…path-dotdot]`, `test_a_repo_rooted_ledger` |
| 6.2, 858-859 | No component is a symbolic link | `ledger-link` | gates `test_no_component_of_the_ledger_path_is_a_link` |
| 6.2, 849 | The folder exists | `ledger-missing` | gates `test_the_ledger_value[agentteams-clearance:absent-ledger-missing]` |
| 6.2, 850 | `references/` | `ledger-layout` | gates `test_structural_errors_of_the_ledger_folder[…ledger-layout]` |
| 6.2, 851 | `agent-privilege.json`, a JSON object | `ledger-privilege` | gates `[…ledger-privilege]` (two cases) |
| 6.2, 852 | `security-decisions.log.csv` with the signature columns; readable; rows as wide as the header | `ledger-log` | gates `[…ledger-log]` (four cases) |
| 6.2, 853 | `authorized-verify-keys/<key_id>.pub.pem`; another name in the store (proposal 11) | `ledger-keys`, `ledger-keys-empty` | gates `[…ledger-keys]` (three cases), `[…ledger-keys-empty]` |
| 6.2, 853-854 | A key or approver file is read only when it is a regular file (not a link, FIFO or device); a store is listed only when it is a plain directory | `ledger-keys`, `ledger-approvers` | gates `test_a_symlinked_key_file_is_not_read`, `test_a_fifo_key_file_is_not_opened` (skipped without `os.mkfifo`), `test_a_symlinked_key_store_is_not_listed`, `test_a_symlinked_approver_list_is_not_read` |
| 6.2, 853-854 | Every capped read opens with `O_NOFOLLOW` and `O_NONBLOCK` (where the platform has them) and decides regular-file-ness and size by `fstat` on the open descriptor | `NotARegularFile` / `OSError` | core `test_read_capped_refuses_a_link_without_following_it`, `test_read_capped_refuses_a_fifo_without_blocking` (skipped without `os.mkfifo`), `test_read_capped_refuses_a_directory` |
| (proposal 15) | The log over `MAX_LOG_BYTES` (64 MiB) and a JSON file over `MAX_JSON_BYTES` are not read | `ledger-log`, `ledger-privilege` | gates `test_the_ledger_log_and_json_files_are_size_capped` |
| 6.2, 854 | `security-approvers.txt` | `ledger-approvers`, `ledger-approvers-empty` | gates `[…ledger-approvers]`, `[…ledger-approvers-empty]` |
| 6.2, 866-868 | A waivers log in the folder is an error; gates `UNAVAILABLE` | `ledger-waiver` | gates `[…ledger-waiver]`, `test_a_malformed_ledger_leaves_every_gate_unavailable` |
| 6.2, 869-873 | Lines 870-873: "Where the repository's own team directory has an approver list that names at least one approver, or at least one verify key, the folder's list names the same approvers and the folder's keys are the same files, and a difference is an error. A team directory with only the comment-only list `agentteams` generates, or with no key file, has neither; the folder is then the only place they live." So a team directory that lacks either kind has neither, and nothing is compared; when it has both (an approver named and a key file), both are compared. Not compared when the folder already has errors (the reason is reported); a team file that cannot be read is reported, not skipped | `ledger-parity` | gates `test_the_team_is_compared_only_when_it_has_both_approvers_and_a_key` (four cases: both, approvers only, keys only, neither), `test_the_folder_names_the_same_approvers_and_keys_as_the_team`, `test_different_key_files_are_a_parity_error`, `test_a_team_with_only_a_comment_list_and_no_key_has_neither`, `test_the_parent_team_is_compared_too`, `test_the_comparison_is_not_made_on_a_malformed_ledger_and_says_so`, `test_an_unreadable_team_list_is_reported_not_skipped` |
| 6.2, 902-904, 910-913 | The causes the text lists (a `parent_team` that is absolute, leaves the repository, is not a team directory, names the folder itself, declares a parent of its own; and a team directory reached through a symbolic link) leave every gate `UNAVAILABLE`, with the reason. That they do not also count as a malformed ledger (so `survey-validate` passes and `survey-status` exits 0) is a reading: the text does not decide the exit status (proposal 20) | reason printed per gate and as `ledger note:` | gates `test_parent_team_rules_leave_the_gates_unavailable_and_are_not_errors` (seven cases), `test_a_sound_parent_team` |
| (proposals 20, 12, 2) | A `parent_team` value that is none of those causes but no usable path at all (not a string, empty, a NUL, `repo:`-rooted, a backslash, a `.` or empty segment): a bad value in the folder's own `agent-privilege.json`, so a malformed ledger | `ledger-privilege` | gates `test_a_parent_team_value_that_is_no_path_is_a_malformed_ledger` (nine cases) |
| 6.2, 911, 926, 941-942 | A team directory reached through a symbolic link, at any component of its generated location, or a link inside it where the comparison reads (`references/`, the key store, the approver list, the privilege file), also inside `parent_team`: leaves every gate `UNAVAILABLE` with the reason (proposal 20 on the exit status); the comparison is not redirected and not made | reason | gates `test_a_team_directory_reached_through_a_link_leaves_the_gates_unavailable`, `test_a_link_inside_a_generated_team_dir_leaves_the_gates_unavailable`, `test_parent_team_rules_leave_the_gates_unavailable_and_are_not_errors[inner-link-…]` |
| 6.2, 861-865 | A sign-off row is Ed25519, key in the folder, author on the list; latest matching row | **not implemented** (needs signature verification; step F, seam `verify_signoff`) | — |
| 6.2, 881-886 | Signing and verifying with `agentteams` | **not implemented** (step F); `survey-manifest` prints the `--check-clearance` command | gates `test_manifest_writes_the_file_and_prints_what_the_operator_signs` |
| 6.2, 889-892 | Conditional verdicts, consumed PASS, replaced keys | **not implemented** (step F) | — |
| 6.2, 894-910 | The HALT scan of the folder's log, the generated team logs and `parent_team`'s log; retractions | **not implemented** (step F: retractions are judged under each log's own signing rules). Step A checks only the structure the scan relies on (a linked team dir, an unusable `parent_team`), as UNAVAILABLE reasons | — |
| 6.2, 910-913 | A team log that cannot be read or parsed leaves the gate `UNAVAILABLE` | **not implemented** for the team logs (step F); implemented for the folder's own log (`ledger-log`) | — |
| 6.2, 915-917 | `agentteams` 1.3.0 or later, else `UNAVAILABLE` | **not implemented** (step F); every gate is `UNAVAILABLE` or `UNCLEARED` in step A anyway | — |

## Commands (section 7)

| Section, line | What is checked | Error id or message | Test |
|---|---|---|---|
| 7, 921 | Bridge commands, each taking a project | `survey-validate`, `survey-status`, `survey-manifest` | gates `test_the_bridge_runs_the_three_commands_isolated`, `test_the_bridge_needs_a_project` |
| plan | The bridge refuses clearly without `scripts/survey/` | exit 1, message names `scripts/survey/` | gates `test_the_bridge_refuses_clearly_without_the_survey_tools` |
| review | The bridge works on its own repository only: a `--root` argument is refused | exit 2 | gates `test_the_bridge_refuses_a_root_option` |
| 10, 989 | The tools and their contract reach a derived repository with the scholarly profile (`docs/survey-toolkit.md` is synced) | — | spec `test_the_survey_files_are_scholarly_managed` |
| 7, 925 | `survey-validate` checks the specification, every row file present and the ledger's folder; writes nothing | exit 0 / 1 | spec `test_each_check_beyond_shape_is_triggered`; gates `test_structural_errors_of_the_ledger_folder`, `test_validate_and_status_write_nothing` |
| 7, 925 | "every row file present": the row checks of section 4 | **not implemented** (step B); `survey-validate` says so in one line | — |
| 7, 926 | `survey-status` prints hash, state, `enforce`, `mode`; exit 0 whatever the states | — | gates `test_status_prints_hash_state_enforce_and_mode_and_the_environment`, `test_status_exits_0_whatever_the_states` |
| 7, 926 | Non-zero only when a specification, manifest or ledger is malformed | exit 1 | gates `test_status_exits_non_zero_only_when_something_is_malformed` (three cases) |
| 7, 927 | `survey-manifest <gate>` writes the manifest and prints what the operator signs | `<ledger>/references/<study id>.<gate>.manifest.json` | gates `test_manifest_writes_the_file_and_prints_what_the_operator_signs` |
| 7, 941-943 | CI: `survey-validate` fails the build; gate state never does | **not implemented** (step H; a CI change is a PS-2 path) | — |

## Proposed contract changes (behaviours the contract does not fix, or fixes ambiguously)

1. **Where the manifest file goes and what it is called** (6.2, line 835: "a per-study log beside the manifests").
   The log is a file, `<ledger>/references/security-decisions.log.csv` (line 852), so "beside" it is read as the
   same directory: `<ledger>/references/<study id>.<gate>.manifest.json`. The other reading, `<ledger>/` beside
   `references/`, takes "log" to mean the folder; the sentence was written before the folder's layout was settled
   (2026-11-24), so the text does not decide it firmly. The literal reading was kept, and it also puts the files
   the operator signs inside the folder a repository protects from agent writes. The name is the toolkit's.
   Propose fixing both.
2. **Paths "as declared": adds an error to rule 1.6** (6.1, line 804). A manifest carries the declared text, joined
   to the study folder or with `repo:` removed, never normalised. A `.` or empty segment (doubled or trailing slash)
   is refused (`path-segment`), an error rule 1.6 does not list, instead of being carried or rewritten. Propose: the
   contract says which spellings are allowed.
3. *(No longer a proposal: see "Step A limitations" below.)*
4. **What "project" holds in a manifest** (6.1, line 799). Taken as the project argument (the directory under
   `Projects/`), not the study `id`. Propose naming it.
5. **`evidence.reader` when `format` is not `plugin`.** Refused (`reader-unexpected`).
6. **A `covers` path that exists but is not a regular file.** Refused (`covers-not-file`): a manifest hashes files.
7. **A flags attribute's table bucketer with no `match`.** 4.8 (line 690) makes `first` the default and lines
   207-208 forbid `first` on a flags attribute; refused (`match-missing-flags`) rather than read as either.
8. **"A gate that covers no file, … unless status is draft"** (line 227). Read as: an empty `covers` is an error in
   every status (`covers-empty`); only a missing path is excused in a draft.
9. **A missing ledger folder in a draft.** An error in every status: section 3's draft clause speaks of input files.
10. **A ledger folder inside `.git/` or at (or under) a generated team location.** Refused (`ledger-location`).
11. **A key store holding anything but `<key_id>.pub.pem` regular files; an empty key store; an empty approver list.**
    Refused (`ledger-keys`, `ledger-keys-empty`, `ledger-approvers-empty`); agentteams falls back to default
    authors on an empty list. The log's "signature columns" (line 852) are taken as `action_reviewed, verdict,
    signature, sig_scheme, key_id, derives_from`.
12. **A backslash, a NUL or a drive letter in a path.** Refused (`path-backslash`, `path-nul`, `path-absolute`).
13. **A key given twice in one JSON object.** Refused (`json-duplicate-key`); a JSON parser otherwise keeps the
    last silently.
14. **Which team directories the keys-and-approvers comparison uses** (lines 869-873, "the repository's own team
    directory"). Taken as every team dir at a generated location under the study's repository root, and a sound
    `parent_team`.
15. **Size caps** (the toolkit's own): 16 MiB for the specification, a manifest file and the ledger's JSON files
    (`MAX_JSON_BYTES`), 64 MiB for the ledger's log (`MAX_LOG_BYTES`), 64 KiB for a key file. A larger file is
    refused unread (`too-large`, `ledger-log`, `ledger-privilege`, `manifest-malformed`).
16. **Extra output lines.** `survey-status` prints a `study …` line, an `environment: python …, unicodedata …`
    line, a `ledger:` line, `ledger note:` lines, a `reason:` line per gate and a closing note; `survey-validate`
    prints an `OK`/`FAIL` line and notes; `survey-manifest` prints the scope, action, mode and the `agentteams
    --check-clearance` command. Section 7 fixes only what each prints at least.
17. **Specification location other than `Projects/<project>/study.json`** (line 79, "unless the project says
    otherwise"). How a project says so is not defined; the commands accept only the default.
18. **Not fixed, and not checked:** duplicate enumeration ids; `counted_statuses` a subset of `statuses`; a
    categorical attribute without `levels` or a flags attribute without `flags`; `values` required for the
    `unit-ids` and `id-contains` rules; `window.from` ≤ `window.to`; duplicate tiers or bases. None is an error in
    section 3, so step A accepts them.
19. **What a combining mark is** (rule 1.10). Taken as Unicode general category M (Mn, Mc, Me); a hyphen is
    U+002D only.

20. **Exit status for the causes 6.2 lists** (lines 910-913 against 926 and 941-943). The text says a linked team
    directory and the listed `parent_team` causes leave the gate `UNAVAILABLE`; it does not say whether they also make
    the ledger malformed. Step A reads them as not malformed: `survey-status` exits 0 and `survey-validate` passes,
    with the reason printed. A `parent_team` value that is no path at all is a malformed ledger (`ledger-privilege`).
    Propose: the contract says which.
21. **"or" against "has neither"** (6.2, line 870 against lines 872-873). Line 870 makes the comparison apply where
    the team's list names an approver "or" the team has a verify key; lines 872-873 say a team with only the
    comment-only list, "or with no key file, has neither". Read together, a team that lacks either kind has neither,
    and step A compares only a team that has both (and then both). Propose: the contract says so in one sentence.
22. **A `..` segment in `parent_team`.** Reported as "has a '..' segment, which is not followed" and the gates read
    `UNAVAILABLE`, whether or not the path would stay inside the repository (step B follow-up).

## Step A limitations (not proposals)

- **What a sign-off request is.** The contract is not silent: rule 1.5 (lines 38-39) calls "the date in a sign-off
  request" a field of `agentteams`, so a request is an `agentteams` record. Step A does not read `agentteams`
  records; as its stand-in for detecting change since a request (6.1, line 817) it compares the current manifest with
  the manifest file `survey-manifest` last wrote, and the status reason says so. Step F must revisit this, and the
  order in `gate_status` (see the 6.1 rows).

Settled, no longer a proposal: how an evidence row cites a fetch receipt is decided by 5.4 (lines 770-772); the
check is step B's.
