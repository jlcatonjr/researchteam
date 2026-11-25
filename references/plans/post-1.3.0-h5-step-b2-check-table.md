# H5 step B part 2a: check table (survey toolkit against `docs/survey-toolkit.md`, version 1)

Plan: `post-1.3.0-h5-survey-tools-a-d.plan.md`, step B. This pull request is **part 2a**: the provenance record of 4.6
(brought forward from step C, written once in shared code), the overrides file, the identity registry with its
candidates, and the `survey-registry` command. **Part 2b** is the batch merge (`survey-rows`) and writing a first
exceptions file (see "Not in part 2a"). Line numbers are those of `docs/survey-toolkit.md` at `7db59bb`. Tests are in
`tests/test_survey_registry.py` unless another file is named; `[...]` is one parametrized case. Ids marked "toolkit"
are the toolkit's own; the contract gives none in 4.4.

**Gates.** `survey-registry` is not a gated stage. 6.1 (lines 786-791) names enumeration (S0), coding packets (S5),
analysis (S6) and the report (S8); section 7 (line 928) and 4.4 give the registry tool no gate. Its record's `gates` is
therefore `{}` (4.6, line 569: "each gate the stage depends on"). No step-B code calls `stage_decision`.

**The identity source** (5.2, lines 733-735). "With `vantage.module` null or absent, identities are the persons the
project's own rows name, as the registry records them, the candidate search of 4.4 compares those persons with one
another." A vantage module's `identities()` is project code; this version does not load it, and refuses such a study
(`identity-vantage`, "Not implemented").

## The provenance record (4.6, lines 546-574)

| Line | What is checked or written | Id | Test |
|---|---|---|---|
| 553-558 | The record has exactly `output, tool, study, schema_version, inputs, gates, plugins, legacy_exceptions`, with their types; `gates` entries `{state, mode, enforce, manifest_sha256?}`; `inputs` entries `{path, sha256}`; `plugins` entries `{file, attr, version, sha256}` | `provenance-malformed` (toolkit) | `test_the_record_is_4_6s_shape`, `test_a_malformed_record_is_refused[...]` (six cases) |
| 561-562 | A non-JSON output's record is beside it, named as the output with `.provenance.json` added, written in the same run | — | `test_the_record_name_is_the_output_plus_provenance_json`, `test_the_registry_is_built_from_the_rows` |
| 563-564 | `inputs` lists the files the tool actually read, the specification among them, each as it was read: the SHA-256 of the very bytes parsed (`read_rows_hashed` reads once) | — | `test_the_record_is_4_6s_shape` |
| (proposal 9, a change against 563) | A declared input that was absent at build is listed too, with `"sha256": ""`; its appearing later makes the output not built | — | `test_a_declared_input_absent_at_build_is_recorded_and_its_appearing_makes_the_output_stale` |
| 565 | The record holds no hash of its output | — | `test_the_record_is_4_6s_shape` |
| 566-567 (proposal 17) | An output whose record is missing, or whose `inputs` or `plugins` no longer match the files, is not built; with `expect_tool` / `expect_schema_version`, so is one whose record names another tool or schema version | `check_current` | `test_check_current_compares_the_tool_and_schema_version`; | `test_an_input_that_changes_leaves_the_registry_not_built`, `test_a_malformed_record_file_is_not_built`, `test_a_recorded_plugin_that_changes_is_not_built` |
| 569-571 | `gates`: each gate the stage depends on, with its state, mode and enforce as `gate_status` gives them; a gate not declared is `NOT DECLARED`; `plugins` each plug-in loaded | `gate_entries` | `test_gate_entries_record_each_state_as_gate_status_gives_it`, `test_the_gate_mode_is_carried_into_the_record`, `test_the_record_is_4_6s_shape` |
| 4.1, 366; 4.6, 571 | `legacy_exceptions`: the registry rests on the evidence file, so it records how many exceptions that file is read with (the exceptions file's lines), and lists the exceptions file among its inputs; a malformed exceptions file refuses the build | — | `test_the_record_counts_the_exceptions_the_evidence_is_read_with` |
| 572 | Canonical JSON, no date | — | `test_the_record_is_4_6s_shape`, `test_the_build_is_deterministic` |
| 573 | Nothing is added to a CSV's own columns | — | `test_the_registry_is_built_from_the_rows` (the registry has its four columns) |

## The overrides file (4.4, lines 491-506)

| Line | What is checked | Id (toolkit) | Test |
|---|---|---|---|
| 491 | Columns `alias_id, target_id, decision, decided_by, reason` | `overrides-columns` | `test_overrides_columns` |
| 491-492 | "Every column is required in every row" (a named author and a reason in each) | `overrides-empty` | `test_each_overrides_check_refuses_and_writes_nothing[overrides-empty]` |
| 492-498 | `decision` is `link`, `merge` or `distinct` | `overrides-decision` | `[overrides-decision]` |
| 496-498 | Targets: `link`, an id in the identity source (here, a project person, 5.2), which may equal the alias; `merge`, another id of the project; `distinct`, the other id | `overrides-target` | `[overrides-target]`, `test_a_link_may_name_the_alias_itself` |
| 500-501 | A `distinct` row settles that one pair and no other; an alias may have several | — | `test_several_distinct_rows_for_one_alias`, `test_a_candidate_named_by_an_override_is_decided` |
| 501-502 | At most one `link` or `merge` per alias; a second is an error | `overrides-second` | `[overrides-second]`, `test_more_overrides_breaches[...]` (two links) |
| 502-503 | A `distinct` row for a pair that is also linked or merged | `overrides-conflict` | `[overrides-conflict]`, `test_more_overrides_breaches[...]` (distinct and linked) |
| 503 | A `merge` or `distinct` row whose `target_id` equals its `alias_id` | `overrides-self` | `[overrides-self]`, `test_more_overrides_breaches[...]` (distinct with itself) |
| 503-504 | The same pair and decision given twice; a pair is the same whichever id is written first | `overrides-repeat` | `[overrides-repeat]` |
| 504-505 | The decision is always written, never read off which side `target_id` belongs to | — (the `decision` cell decides; nothing else is read) | every case above |
| 505-506 | "The registry links and merges only from this file"; a candidate is decided only when a row names that pair | — | `test_a_merge_folds_the_alias_into_the_target`, `test_a_link_records_the_identity`, `test_a_candidate_named_by_an_override_is_decided` |
| 496 | A `link` row's alias is "the project's person": an alias that is not a project person is refused | `overrides-alias` | `[overrides-alias]` |
| (proposal 1) | A `distinct` row's alias must be a project person (the text is silent for `distinct`) | `overrides-alias` | `test_a_distinct_row_names_project_persons_on_both_sides` |
| 497 (proposal 4) | A `merge` row's alias may be absent from the rows only when the registry on disk already lists it in that target's `merged_from` (its rows were rewritten to the target); an alias that appears nowhere is a mistyped alias | `overrides-alias` | `test_a_merge_stays_valid_after_the_aliass_rows_are_rewritten`, `test_a_merge_alias_that_appears_nowhere_is_refused` |
| (proposal 2) | A merge whose target is itself merged; a link to a merged person; a link to a person who is linked to another (5.2, line 733: identities "as the registry records them") | `overrides-chain` | `[overrides-chain]`, `test_more_overrides_breaches[...]` (link to a merged person), `test_a_link_to_a_person_linked_elsewhere_is_a_chain` |
| (proposal 3) | Two persons linked to one identity | `overrides-shared-identity` | `[overrides-shared-identity]` |
| 7, 925 | `survey-validate` checks the overrides file, a row file of 4.4 | the ids above | `test_each_overrides_check_refuses_and_writes_nothing[...]` (second half) |
| 527-528 | The tool never writes the overrides file | — | `test_candidates_are_listed_and_never_applied` (the tree is unchanged) |

## The registry (4.4, lines 507-523)

| Line | What is built | Id | Test |
|---|---|---|---|
| 507 | Columns `person_id, display_name, identity_id, merged_from`; written by the registry tool | — | `test_the_registry_is_built_from_the_rows` |
| 509-511 | Persons from the evidence file and, in a passage or work study, the attribution file; a study can build before its first evidence row | — | `test_persons_come_from_the_attribution_file_before_any_evidence` |
| 511-512 | The attribution file is one of the registry's recorded inputs | — | `test_the_record_is_4_6s_shape` |
| 513-514 | `display_name`: the linked identity's name; a name the evidence reader supplies (a plugin format; not loaded); the `person_id` itself. Without a vantage module the identity is a project person whose only name is its id: a person linked to another shows the other's id (proposal 13) | — | `test_the_registry_is_built_from_the_rows`, `test_a_link_to_another_person_shows_that_persons_name` |
| 507-508 | `identity_id` is the id in the identity source: the `link` row's target | — | `test_a_link_records_the_identity` |
| 497; 4.1, 308 | A `merge` makes two ids one person: the alias's row is folded into the target's and listed in `merged_from`; the registry holds both ids, so an evidence row may still carry the alias and pass `person-unknown` | — | `test_a_merge_folds_the_alias_into_the_target`, `test_evidence_may_carry_a_merged_alias`, `test_a_distinct_row_changes_no_registry_row` |
| 521-523; 566-567 | The registry first, its record last. Interrupted between them: if no input changed, the new registry is the old one byte for byte and the old record is still true; if an input changed, appeared or went, the old record no longer matches and the registry reads as not built. Both targets are checked again after the temporary files are written and before either replace, so a refused write changes nothing | — | `test_an_interruption_before_the_record_leaves_the_registry_not_built`, `test_an_interrupted_registry_write_leaves_the_old_file`, `test_a_write_refused_at_either_last_check_changes_nothing[...]`, `test_an_os_error_while_writing_is_a_refusal` |
| 1.2 | Fail closed: any finding refuses and nothing is written | — | `test_each_overrides_check_refuses_and_writes_nothing[...]`, `test_a_malformed_source_file_refuses` |
| 1.5 | Deterministic: rows in code-point order of `person_id`, LF, the same bytes in two repositories; a second build changes nothing | — | `test_the_build_is_deterministic` |
| 1.6; plan | Written as survey-manifest writes: no link on the way (checked again just before writing), a regular file or nothing there, a temporary file in the same folder, mode 0644, `os.replace` | — | `test_a_link_on_the_way_to_the_registry_refuses`, `test_a_registry_path_that_is_a_directory_refuses`, `test_outputs_are_mode_0644` |
| 1.2, 1.3 (proposal 14) | **Allowlist**: an output and its record lie inside the study's own folder, checked three ways that must agree (NFC, case-folded path; real path of the nearest existing parent; a walk up to the study folder's device and inode before the repository root); a study at the repository root writes no output; a `repo:` output outside the study folder is refused | — | `test_an_output_outside_the_study_folder_is_refused[...]` (`CLAUDE.md`, `.claude/settings.json`, the bridge script, `toolchain.lock`, `.agentteams/toolchain-group.json`), `test_a_repo_rooted_output_inside_the_study_folder_is_accepted`, `test_a_study_relative_registry_elsewhere_in_the_study_is_accepted`, `test_a_study_at_the_repository_root_writes_no_output` |
| 1.2, 1.3 (proposal 14) | **Within the study folder**: never the specification, another declared path or a covered file; never inside a declared folder or a folder that holds a covered file (other than the study folder); never in the ledger folder; NFC and case-folded names, and device and inode. **Second layer**: never at or under `.git`, `.github` or a generated team location | — | `test_the_registry_may_not_be_written_over_a_protected_file[...]` (eleven cases), `test_a_declared_path_equal_to_the_records_name_is_refused`, `test_an_nfd_spelling_of_a_declared_file_is_refused`, `test_an_output_inside_a_declared_folder_is_refused` |
| (proposal 16) | A registry value (an id, a name, `merged_from`) holding a control character, a line or paragraph separator, or a NUL refuses the build; the registry never holds a cell with a line break | `registry-value` (toolkit) | `test_a_registry_value_with_a_control_character_or_line_break_is_refused[...]` |

## Candidates (4.4, lines 524-530; 5.2, lines 733-734)

| Line | What is listed | Id | Test |
|---|---|---|---|
| 524-526 | Possible matches, each with its kind: `same-id`, `exact` (folded names equal), `similar` (names share tokens) | — | `test_kinds_of_candidates`, `test_candidates_are_listed_and_never_applied` |
| 5.2, 733-734 | Without a vantage module the search "compares those persons with one another": each pair once, so `same-id` cannot arise between two persons | — | `test_candidates_are_listed_and_never_applied` |
| 526-527 | A candidate is never a link, whatever its kind; nothing is written | — | `test_candidates_are_listed_and_never_applied` |
| 529-530 | Stop words: one per line; words left out when names are compared; without the file, no word is left out | `stop-words-file` (toolkit, unreadable file) | `test_stop_words_leave_words_out`, `test_candidates_are_listed_and_never_applied` (empty file) |
| 506; 7, 928 | A candidate is decided when an override row names the pair; a decided pair is not listed and takes no place in the cap, so deciding the shown ones reveals the next (proposal 15) | — | `test_a_candidate_named_by_an_override_is_decided`, `test_deciding_the_shown_candidates_reveals_the_next` |
| (proposal 5) | A word is a run of letters and digits of the folded name (`_`, `-` and white space separate words); the names are the `person_id`s | — | `test_candidates_are_listed_and_never_applied`, `test_underscores_separate_words` |
| (proposal 15) | Persons are indexed by folded name and by word, so only persons sharing one are compared; at most `MAX_CANDIDATES` (1000) undecided candidates are shown, in the fixed order, and the rest counted up to `MAX_COUNTED` (100000) | — | `test_candidates_scale_and_are_capped` |

## Command and bridge (section 7, line 928)

| Line | What is checked | Output | Test |
|---|---|---|---|
| 928 | `survey-registry` "builds the identity registry; lists candidates; applies recorded overrides" | `survey-registry <project>`; `--candidates` lists (proposal 6) | `test_the_bridge_runs_survey_registry_and_refuses_root` |
| step A pattern | The bridge refuses a user-supplied `--root`, and refuses when `scripts/survey/` is absent | exit 2; exit 1 | `test_the_bridge_runs_survey_registry_and_refuses_root`; step A's absent-tools test covers the shared function |

## Step B part 1 follow-ups (in this pull request)

| Item | What changed | Test (in `tests/test_survey_rows.py`) |
|---|---|---|
| (a) | `BC` also read in the forms `B.C`, `B.C.E`, `B. C.`, `B C` | `test_more_bc_spellings_are_negative[...]` |
| (b) | A century range (`4th-5th centuries`) reads both centuries: the first for `work_date`, the largest for `life_dates` (proposal 14 of part 1, now in proposal 7 here) | `test_a_century_range_reads_both_centuries` |
| (c) | Only a whole chain grouped by thousands is part of a longer number: one separator throughout, every later group exactly three digits, a lead of one or two digits, or of three with two or more groups after it (`1,750`, `12,750`, `1.234.567`, `123,456,789`). Any other chain is a list: `12.03.750` reads 750, `450,500` reads 450 / 500, `12.03.1750` 1750, `1742,1790` 1742 / 1790, `1750.5` 1750 (proposal 8) | `test_a_run_grouped_with_a_comma_or_dot_is_part_of_a_longer_number[...]`, `test_a_comma_list_of_years_gives_the_first_and_the_largest` |
| (d) | `q()` cuts the text of any value, not only a string | `test_long_lists_in_messages_are_cut_too` |
| (e) | The part 1 table's `locator-missing` row cites line 276 | — |
| (f) | Step A's messages quote file content through `q()` | `test_step_a_messages_cut_a_long_declared_path` |

## Not implemented

| Section, line | What | Why |
|---|---|---|
| 5.2, 740-748 | A vantage module's `identities()` as the identity source, its names and aliases, and `same-id` candidates against it | Loading a vantage module runs project code; like the evidence reader (part 1), it needs a plan (5.1, line 717) before it is built. A study with one is refused (`identity-vantage`) |
| 4.4, 514 | "A name the evidence reader supplies (a `plugin` format may carry one)" | The reader plug-in is not loaded (part 1); plugin evidence is refused |
| 4.4, 527-528 | "The tool may write proposed override rows to a separate file for a person to review" | The contract says "may" and names no file or shape; candidates are listed on the screen only |

## Not in part 2a (part 2b)

| Section, line | What |
|---|---|
| 4.1, 322-326; 4.4, 515-523; 7, 929 | The batch merge `survey-rows`: the batch checked in full with the file it joins, never covered by a legacy exception, refused into a plugin format, refused unless the registry is built, refused when a build over the merged file would change the registry's rows, then the evidence file and the registry's renewed record (last) |
| 4.1, 364-365 | "The tool can write a first version [of the exceptions file] from the current breaches for a person to review; it never adds to an existing one" — the text gives this to "the tool" (the row tool), so it goes with `survey-rows` |

## Proposed contract changes

1. **A `distinct` row's alias** must be a person of the project (`overrides-alias`). For `link` (line 496, "the
   project's person") and `merge` (line 497, "two of the project's ids") the text decides; for `distinct` it is silent.
2. **Chains**: a merge whose target is itself merged, a link to a merged person, or a link to a person who is
   linked to another, is refused (`overrides-chain`).
3. **Two persons linked to one identity** are refused (`overrides-shared-identity`): they would be one person, which
   is a merge.
4. **Merged ids in the registry**: `merged_from` is `;`-separated and sorted, and every id in it is held by the
   registry, resolving to the row's person, so an evidence row may still carry a merged alias (4.1, line 308). A merge
   row whose alias no longer occurs in the rows stays valid only while the registry on disk already lists the alias in
   that target's `merged_from`: line 497 does not say whether the alias must still occur. Later readers must map a
   merged alias to its target where they read a person: 4.3's `author_kind` per person (line 437), 4.7's `author`
   and person-level rows (and 4.3's unit-id check, line 434); 4.7 does not say so.
5. **Words for `similar`**: runs of letters and digits of the folded name (`_`, `-` and white space separate words),
   stop words removed; the names compared are the `person_id`s, the only names the project's own rows carry.
6. **The command line**: `survey-registry <project>` builds; `--candidates` lists and writes nothing.
7. **A century range** (`4th-5th centuries`) states two centuries: the first for `work_date`, the largest for
   `life_dates` (extends part 1's proposal 14).
8. **A number grouped by thousands** is "part of a longer number" (line 699) only as a whole chain: one separator,
   every later group exactly three digits, a lead of one or two digits, or of three with two or more groups after it.
   Any other chain is a list of numbers, each read on its own (`450,500` -> 450 / 500; `12.03.750` -> 750).
9. **A change against line 563**: a record lists every *declared* input, not only "the files the tool actually read";
   one that was absent at build is listed with `"sha256": ""`, and its appearing later makes the output not built.
   Reason: an input that appears after the build (a new overrides file, a first evidence file) changes what the build
   would give, and without this the output would still read as built. Compatibility: a reader built strictly to line
   563 would treat `""` as the hash of a missing file, so such an output would never read as built while that file is
   absent. That fails safe, but the operator must rule on it before step C reads these records.
10. **A gate that is not declared** has `mode` and `enforce` empty in the record (4.6 names only its state).
11. **The registry's own CSV form**: cells quoted only where CSV needs it, LF, rows in code-point order of
    `person_id` (the contract fixes the form of the frame's files, not the registry's).
12. *(Settled by 4.1, line 366: the registry records how many exceptions the evidence is read with.)*
13. **A link to a different person without a vantage module** is a merge in all but name: the identity is a project
    person, and the linked person shows its id. Propose: without a vantage module, a link names only the alias itself
    (or is not allowed), and two persons who are one are written as a merge.
14. **An output and its record lie inside the study's folder; a `repo:` output outside it is an error.** 4.4 and 4.6
    only ever place an output in the study. Within the folder an output is never the specification, a declared or
    covered file, inside a declared folder or a folder holding a covered file, or in the ledger folder; and never
    under `.git`, `.github` or a generated team location. A study at the repository root writes no output.
15. **The candidate listing**: undecided candidates only, at most 1000 shown in the fixed order and the rest counted
    up to 100000; a pair an override row names is decided and not listed, so deciding the shown ones reveals the next
    (section 7 says the tool "lists candidates"; it names no listing of decided ones).
16. **Registry values**: no `person_id`, name or `merged_from` cell may hold a control character, a line or paragraph
    separator, or a NUL (the contract gives `person_id` no pattern beyond "no `|`").
17. **A toolkit version in the record**: 4.6 names the `tool` and the study's `schema_version`, not the toolkit's
    release, so a record written by an older release of the same tool reads as built; `check_current` can compare the
    tool and the schema version only.

## Residual

- **A hand-edited registry** cannot be told apart from a built one: the record carries no hash of its output (4.6,
  line 565), so `check_current` cannot see a change to the registry itself. Since the registry holds the ids in
  `merged_from` too, a hand-added id there would let evidence rows carrying it pass `person-unknown`. Only a comparison
  with a fresh deterministic build detects it; part 2b's merge makes that comparison ("refused if a build over the
  merged file would change the registry's rows", 4.4, lines 517-521). Adding it to `survey-validate` now (a
  `registry-stale` finding) would change what validate reads and fail every study whose registry predates the build
  rules, so it is left for 2b.
