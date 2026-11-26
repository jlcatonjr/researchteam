# H5 step D part 1: check table (survey toolkit against `docs/survey-toolkit.md`, version 1)

Plan: `survey-tools-2026-11-23.plan.md`, step D. This is **part 1** of step D: the `survey-frame` command (section 7,
line 935). It covers the frame of a passage or work study, its passage list and records (4.7, lines 575-671; 4.6),
and the frame-change log's check (4.4, lines 461-476). It checks post-steps (4.5, lines 532-544) without running
any. Line numbers are those of `docs/survey-toolkit.md` at `599dc90`, which is version 1, frozen. Tests are in
`tests/test_survey_frame.py`. Ids are the toolkit's own.

The frame reads the final codes the way the rollup does. `load_final` in `survey_finalize.py` is shared, not copied:

- the file must be exactly what finalising gives, in every status (operator decision O3);
- its record must be current, except that a draft study reports a stale record and goes on;
- every file read is hashed before the final codes are worked out again, and guarded until the write.

`write_outputs` writes the frame, the passage list, the dropped list (where the rule is declared) and their records in
one `write_all`: the outputs first, the records last.

## Operator rulings (picker, 2026-11-25)

Each is decided for the toolkit, and each is a proposal for a later contract version.

- **A, "Replace .csv".** The dropped list is the frame's path with `.csv` replaced by `.dropped.csv`, and a frame
  path that does not end in `.csv` is refused. `--out <frame>` takes the frame's full path, and the list's name is
  derived from it. With the rule declared and nothing dropped, a header-only list is written. Without the rule, a
  list from an earlier build at that path is refused. The dropped list has its own 4.6 record, like the other
  outputs.
- **B, "The tool, from arguments".** Given `--change-id`, `--date`, `--reason` and `--results-seen yes|no`,
  `survey-frame` appends the frame-change entry in the same write as the frame. The author gives every stated fact
  (rule 1.5: the date never comes from the clock), and an id already in the log is refused. Without the arguments,
  the command refuses and prints the entry needed, as before. The tool computes `frame_sha256`, `n_units`, `added`,
  `removed` and `units` from the frame; computing the last three as well was accepted with ruling B2.
- **B2, "No record for the log"** (picker, 2026-11-25). `survey-frame` appends the entry and writes the frame in one
  run, through one guarded write. The log gets no 4.6 record of its own. The records of the frame, the passage list
  and the dropped list list the log as it stands **after** the append, so they are current. This is an exception to
  line 549 ("Every file a tool writes for a later stage or a reader has a provenance record") and is proposed for a
  later contract version.
- **B3, "Replace when the log names it"** (picker, 2026-11-25). `survey-frame` may replace its own frame, passage
  list and dropped list, and their records, at the same paths. It does so only when the log's last entry, after
  this run's append if any, holds the new frame's hash, and only where the record beside each output is this tool's
  record for it. D2 and D5 stand for the other commands: the shared writer's default stays "refuse", and replacing
  is an explicit switch only `survey-frame` passes.
- **D, "Read through the registry".** A merged id counts as the person it was merged into, through the recorded
  `merge` override; the rows stay as written. One function, `survey_final.merged_persons`, reads the overrides file's
  merges for both the rollup and the frame, so the two read ids the same way. **The rollup changes with this.** A
  passage attributed to a merged id now counts for its person there too. The overrides file was already among both
  records' `inputs`, read through `hash_inputs`.
- **E, "Cells with a counted passage".** As built.
- **C and F.** As built, by the coordinator's choice, told to the operator. F was not open: a record lists "each gate
  the stage depends on" (line 569), and the passage list is "a second output of the same tool" (line 656), so its
  record lists the stage's gates, S5 and S6.

## The frame-change log (4.4, lines 461-476)

| Line | Sentence or rule | Id | Test |
|---|---|---|---|
| 461-467 | One JSON Lines entry per change, with the nine fields and their types | `change-log` | `test_a_malformed_log_is_refused_and_no_entry_proposed[...]` |
| 469 | "The log is the file `frame_rules.change_log` names" | — | `test_the_records` (the log is the record's last input) |
| 469-471 | A passage or work frame's units are its `unit_id` values, the cells' ids: "the log records cells, not passages" | — | `test_no_entry_refuses_and_prints_the_entry_needed` (the entry lists cell ids) |
| 470 | "its `person_id` values in an author study": no frame is built in an author study (4.7, line 580), so no log entry lists persons | — | `test_an_author_study_is_refused` |
| 472-473 | `frame_sha256` is the hash of the frame file "as it stands after the last post-step", computed as a manifest computes a text file's (6.1: each CRLF made LF) | — | `test_the_frame_hash_is_a_text_files`, `test_the_invented_studys_frame_and_passage_list` |
| 473 | "The first entry lists every unit as added" | `change-log` | `test_a_malformed_log_is_refused_and_no_entry_proposed[...]` |
| 474-475 | `id` is what a report cites; `results_seen` records whether a result had been seen, "shown wherever the change is reported" | `change-log` (an empty or repeated `id`) | `test_a_malformed_log_is_refused_and_no_entry_proposed[...]`. No tool reports changes yet, so "shown wherever reported" has no reader in part 1 |
| 475-476 | "The check fails when the current frame's hash differs from the last entry's: a frame cannot change without an entry" | `change-log-entry` | `test_no_entry_refuses_and_prints_the_entry_needed`, `test_a_changed_frame_needs_a_new_entry` |
| 1.2, 1.5 | The check fails before anything is written (rule 1.2). Without the change arguments, the entry the log needs is printed with `id`, `date`, `reason` and `results_seen` left for the author, because no tool fills in a date or a reason (rule 1.5) | — | the same two tests |
| B | The change arguments go together: all four or none, `--results-seen` `yes` or `no` | usage error | `test_the_change_arguments_go_together[...]` |
| 461; B | With the arguments and an unchanged frame, no entry is written. The log has "one entry per change to the frame" (line 461), and giving the arguments breaks no rule, so they are not used and the command says so. It does not refuse | — | `test_the_change_arguments_and_an_unchanged_frame_write_no_entry` |
| 474; B | An `--change-id` already in the log, or an empty one, is refused; so is an empty `--date` or `--reason` | `change-log-id`, `change-log-fact` | `test_an_id_already_in_the_log_is_refused` |
| B, B2 | With the arguments and a changed frame, the author's four facts and the tool's `frame_sha256`, `n_units`, `added`, `removed` and `units` make the entry. It is appended in the same guarded write as the frame, its lists and their records (`write_all`): either all are written or none. The log has no record; every record lists the log as it stands after the append | — | `test_the_first_build_with_the_change_arguments_creates_the_log`, `test_a_changed_frame_with_the_change_arguments_is_replaced_in_one_run` |
| B2 | The log grows by exactly one entry at its end. The new bytes are the bytes as read plus one line and a line feed, written whole through the guarded writer. The guard holds the bytes as read, so a log changed on disk since then refuses everything | — | `test_a_changed_frame_with_the_change_arguments_is_replaced_in_one_run`, `test_a_log_changed_on_disk_before_the_write_refuses_everything` |
| B2 (tightening 7) | A log whose last line does not end in a line feed is refused. The contract's text does not say how a line is joined to one, so nothing in the log as read is ever changed | `change-log-end` | `test_a_log_not_ending_in_a_line_feed_is_refused` |
| B2; 218 | The log's path passes the same output checks: inside the study's folder (`check_output_target`, its own declared pointer allowed) and no link. A log that does not exist yet is created: section 3 lets `change_log` be absent "because a stage writes them or they start empty" (line 218), in any status | — | `test_the_first_build_with_the_change_arguments_creates_the_log` |
| B3 | The command replaces its own earlier frame, passage list and dropped list at the same paths only when the log's last entry, after this run's append if any, holds the new frame's hash. Otherwise the log check refuses first | — | `test_a_changed_frame_with_the_change_arguments_is_replaced_in_one_run`, `test_replacement_is_refused_when_the_last_entry_does_not_name_the_new_frame` |
| B3 | Only this command's own outputs are replaced: the record at each record path must be this tool's record for that output. An output with no record, or a foreign record, is refused | — | `test_an_existing_different_output_is_refused`, `test_a_foreign_record_at_a_record_path_refuses_the_replacement` |
| B3 | A dropped list that would no longer be written (the rule removed) is still refused: the tool deletes nothing | — | `test_a_dropped_list_without_the_rule_is_refused` |
| D2, D5, B3 | Every other command keeps refusing to overwrite; `write_outputs` replaces only with `replace=True`, which only `survey-frame` passes | — | `test_every_other_command_keeps_refusing_to_overwrite` |
| (tightening 1) | No blank line. `frame_sha256` is 64 lower-case hex digits. `n_units` is the number of `units`, and `units` has no repeats. A later entry's `added` and `removed` are exactly what its `units` gained and lost since the entry before. The last entry's `units` are the frame's, in its order | `change-log`, `change-log-entry` | `test_a_malformed_log_is_refused_and_no_entry_proposed[...]`, `test_a_later_entry_lists_what_changed` |

## Post-steps (4.5, lines 532-544): checked, not run

| Line | Sentence | Id | Test |
|---|---|---|---|
| 534-535 | `frame_rules.post_steps` lists the project's scripts, "run in the order given after the frame is written"; a step adds columns and does nothing else | — | **not run** in part 1 (see "Running post-steps") |
| 537-538 | The frame build runs each step; later checks treat the frame as it stands after the last step | `post-steps-unavailable` | `test_post_steps_allowed_by_their_gate_are_not_yet_run` |
| 539-540 | A step that changes the units, their order or an existing column is refused | — | design below |
| 541 | A step is deterministic and follows 5.1 on network and clock | — | design below |
| 542-544 | Each step file is covered by a gate; "while that gate is blocking and not cleared, the frame build refuses to run the step" | `post-step-gate`, `post-step-uncovered` | `test_a_post_step_under_a_blocking_gate_not_cleared_is_refused` (S5, blocking, UNCLEARED), `test_post_steps_allowed_by_their_gate_are_not_yet_run` (S6, build-only) |
| 1.6 (tightening 2) | Each step's path: rule 1.6, inside the study's folder, no link on its way (`locate_in_study`), a regular file | `post-step-place`, `post-step-file` | `test_a_post_step_outside_the_study_folder_is_refused`, `test_a_linked_post_step_is_refused`, `test_a_post_step_that_is_a_folder_is_refused` |
| (order) | Two passes, in this order: every step's path first, then the gates of the steps whose path passed. A step refused by its path is not passed to a gate, because a gate clears a file at a place, and a refused place has nothing to clear. The study is refused either way | — | `test_post_steps_are_checked_paths_first_then_gates` |
| — | No step is executed: no child process is started and nothing is imported | — | `test_no_post_step_is_executed` |

## The frame (4.7, lines 575-671)

| Line | Sentence or rule | Id | Test |
|---|---|---|---|
| 577-578 | The frame is written from the final codes, the attribution file, the evidence and the specification | — | `test_the_invented_studys_frame_and_passage_list` |
| 579-580 | "the frame tool refuses to run in" an author study | — | `test_an_author_study_is_refused` |
| 582-585 | A cell is one author and one value of each `rollup_by` attribute; `unit_id` is `<person_id>\|<value>\|...` in `rollup_by` order, the `person_id` alone without `rollup_by` | — | `test_cells_split_by_rollup_by_and_ordered_by_code_point`, `test_the_period_rule` (no `rollup_by`) |
| 587-589 | The units behind a cell are the rollup's: of that author and those values, with no `exclude_from_rollup` value and a counted status | — | `test_a_cell_without_a_counted_passage_is_not_in_the_frame` |
| (ruling E) | The frame's cells are those with at least one counted passage | — | `test_a_cell_without_a_counted_passage_is_not_in_the_frame` |
| (ruling D) | A cell's author, and "the author's rows", are read through the recorded merges: a passage or row of a merged id is its person's; the rows stay as written. Merged ids with two `author_kind` values are an error | `author-kinds` | `test_a_merged_id_counts_as_its_person_in_the_frame`, `test_the_rollup_reads_merged_ids_the_same_way`, `test_merged_ids_with_two_author_kinds_are_an_error` |
| 591-594 | The columns, in this order | — | `test_the_frame_columns`, `test_the_invented_studys_frame_and_passage_list` |
| 598 | `author` is the cell's `person_id` | — | the same |
| 599 | `unit_kind` is the author's `author_kind` (one per person, 4.3) | — | the same |
| 600 | The period's label and its number from 1; both the missing value when no year places the cell | — | `test_the_period_rule` |
| 601 | A categorical attribute: one column, a declared level or the missing value | `frame-value` | `test_attribute_evidence`, `test_every_cell_is_checked` |
| 602 | A flags attribute: `<key>_<flag>` 1 or 0 in `flags` order, then `<key>_<missing>`, 1 when no value maps to a flag | — | `test_attribute_evidence` |
| 603 | One column per outcome whose source is `codes` and whose rollup is not `none`, in declared order | — | `test_the_frame_columns` |
| 605-607 | Attribute columns in `attributes` order; the period attribute not repeated; missing value the attribute's `missing` (default `NE`); `NE` without a period attribute | — | `test_the_frame_columns`, `test_the_period_rule` |
| 609-616 | Outcome cells: none or NA codes only give empty; at least one `missing` and no level code give `missing`; at least one level code gives the 4.2 rollup over them (`mixed` for `mixed-if-conflict`) | `frame-rollup` (a 4.2 rule error, such as a `single-code` conflict or a tie, part 2's T2) | `test_the_outcome_cell_table`, `test_mixed_if_conflict_in_a_frame_cell` |
| 618-620 | An NA code never appears in a frame | `frame-value` | `test_every_cell_is_checked` |
| 620-621 | A final code that is not a level code, an NA code or the outcome's `missing` is an error | `frame-code` | `test_the_outcome_cell_table` |
| 621 | "A passage with no final code at all counts as 'none' (open point 4)" | — | `test_the_outcome_cell_table` (no codes give empty). Through the command the case cannot arise: under D4 a current final file has a final row for every unit and coded outcome |
| 623-629 | `work_date`: counted-tier rows of the cell's passages; if their years all fall in one period it is the cell's; if in more than one, or none, the next basis; a person-level `work_date` row is not used | — | `test_the_period_rule` |
| 630-631 | `life_dates`: the person-level rows in counted tiers; if they give a year (4.8: the largest), its period | — | `test_the_period_rule` |
| 633 | No basis places the cell: both period columns the missing value | — | `test_the_period_rule`, `test_the_invented_studys_frame_and_passage_list` |
| 635-638 | Attribute values: the author's counted-tier rows whose `attribute_kind` is a source attribute and whose `unit_id` is the person's own id or one of the cell's passages, in evidence-file order, bucketed by the table (4.8). A categorical attribute with no value gets the missing value | `frame-value-too-long` (a value over the matcher's cap, 4.8) | `test_attribute_evidence`, `test_a_flags_value_over_the_cap_is_a_finding_and_no_stray_column`, `test_bucket_tables_are_parsed_from_the_hashed_bytes` (the tables come from the bytes `load_final` hashed) |
| 638-639 | "A plug-in bucketer is refused in a frame, and nothing is written (open point 6)" | `frame-plugin-bucketer` | `test_a_plug_in_bucketer_is_refused` |
| 641-643; A | `not-on-question`: a cell whose outcome columns are all empty is left out and written to `<frame>.dropped.csv` (`unit_id, rule, reason`), so that it can still be inspected. By ruling A that is the frame's path with `.csv` replaced, written with its header only when nothing is dropped, with a record of its own | — | `test_not_on_question_drops_cells_with_all_outcomes_empty`, `test_a_cell_with_every_outcome_empty_is_dropped`, `test_the_rule_declared_and_nothing_dropped_writes_a_header_only_list` |
| 643-644; A | "Without the rule the cell stays in the frame." A dropped list from an earlier build at that path is refused; a frame path not ending in `.csv` is refused | — | `test_the_invented_studys_frame_and_passage_list` (no rule, no list), `test_a_dropped_list_without_the_rule_is_refused`, `test_where_the_outputs_may_not_go[...]` |
| 644 | "The other exclusion rules are not defined over cells in version 1 (section 3)": the specification check refuses any other rule in a passage or work study (section 3, lines 212-213) | `exclude-rule-cells` (step A) | step A's specification tests |
| 646-649 | CSV, every cell quoted, LF, rows in ascending code-point order of `unit_id`; the passage list in evidence-file order; `frame_sha256` from the frame file | — | `test_every_cell_is_quoted`, `test_cells_split_by_rollup_by_and_ordered_by_code_point`, `test_the_invented_studys_frame_and_passage_list` |
| 651-652 | Every cell checked before anything is written: each value one its column allows, each `unit_id` unique, every column present; on any breach nothing is written and the breaches are listed | `frame-value`, `frame-unit-duplicate`, `frame-column` | `test_every_cell_is_checked` |
| 653 | "The finalised codes must be current (4.6)" | — | `test_a_final_file_that_is_not_current_is_refused`, `test_a_hand_edited_final_file_is_refused` |
| 653 | "The frame's provenance record lists gates S5 and S6" | — | `test_the_records` |
| 654 | "Post-steps (4.5) run after these checks" | — | not run in part 1 |
| 656-660 | The passage list: one row per evidence row whose `unit_id` is an attribution unit, counted or not; its columns | — | `test_the_invented_studys_frame_and_passage_list` |
| 661-663 | `unit_id` is the passage's cell, or the cell it would be in if counted; `passage_id`, `person_id` (the attributed author), `attribution` (its status), `counted` `true` or `false` | — | the same |
| 663-669 | The first reason that applies: `tier-<tier>` (`tier-blank`); `excluded-<attribute>-<value>` (the first key in the specification's order); `attribution-<status>` (`attribution-blank`); `not-on-question` | — | `test_the_passage_list_reasons_in_order`, `test_not_on_question_drops_cells_with_all_outcomes_empty` |
| 671 | "A reason is a label to show, not a field to take apart": the tool writes each reason and never reads one back. A tier, an attribute or a value may itself hold `-`, so `excluded-genre-draft` does not split one way only | — | `test_the_passage_list_reasons_in_order` |
| 671 | "Person-level rows are not listed" | — | `test_the_invented_studys_frame_and_passage_list` (ev-002 and ev-004 are not listed), `test_the_passage_list_reasons_in_order` |
| 4.6 | Each output's record: 4.6's shape, every file read (rule O4: gate reads stand under `gates`), `plugins` empty (no plug-in is loaded), the legacy exceptions; current after the write | — | `test_the_records`, `test_the_records_inputs_are_the_files_read` |
| 1.5 | The same bytes in two repositories; "unchanged" on a second run | — | `test_deterministic_and_unchanged_twice` |
| D2 (as for the final codes) | An existing output is never written over with other bytes; outputs lie inside the study's folder and are not declared files; no output is named as a record, the final file or its record | — | `test_an_existing_different_output_is_refused`, `test_where_the_outputs_may_not_go[...]` |
| 7, 935 | The bridge command, refusing `--root`; usage errors exit 2 | — | `test_the_bridge_runs_the_command_and_refuses_root`, `test_usage_errors` |
| 5.2 | A vantage module's `included()` exclusions are recorded in the frame-change log: a vantage module is not loaded by this version, so such a study is refused (fail closed) | `identity-vantage` | `test_a_vantage_module_is_refused` |

## What the contract leaves open

Points A to F, B2 and B3 were ruled on (above). E's third reading, every author crossed with every declared
`rollup_by` level, was not chosen: such a frame would hold cells no passage stands behind. B2 and B3 are kept
below as they were put to the operator, with the option chosen. Nothing in part 1 is stopped now.

**B2. Writing the frame-change log from the run.** *Ruled: option (a), "No record for the log".* As it was put: the command refuses, writes nothing, and prints the
full entry, the author's facts included, for the author to append. The text does not settle this:

- Line 549-550: "Every file a tool writes for a later stage or a reader has a provenance record". The log, once the
  tool writes it, needs one.
- Line 563: `inputs` lists the files the tool read, "each as it was read". This run reads the log before appending
  to it, so both the frame's record and the log's own record would list the log's old bytes.
- Lines 566-567: an output whose `inputs` no longer match the files "is treated by the next stage as not built". The
  frame's record would be stale from the moment it is written. A log record that lists the log itself would be
  stale for good.

The options for the operator:

- (a) The log has no record of its own: it is the author's log, among 4.4's "logs and working files". The frame's
  record lists the log as it stands after the append, the entry being the frame's own. **Recommended.** It reads
  line 563 for a file this run itself writes, and needs that stated in a later version.
- (b) The log gets a record whose `inputs` leave the log itself out, and the frame's record lists the log after
  the append.
- (c) Two runs: with the arguments the tool appends the entry and writes no frame; the next run reads the new log
  and writes the frame. This still meets line 549's record question for the log, so it needs (a) or (b) as well.

**B3. A changed frame at the same path** (found in the hand run). *Ruled: option (a), "Replace when the log names it".* The writer refuses to
write over an existing output with other bytes, as D2 ruled for the final codes and D5 for the rollup. So a changed
frame cannot replace the old frame at the same path: the author has to move the old frame and its record aside.
That holds even though the log's last entry already names the new frame, so the change is recorded. 4.4 assumes the
frame file changes ("the hash of the frame file as it stands", line 472; "a frame cannot change without an entry",
line 476).

- (a) Let `survey-frame` replace the frame, the passage list and the dropped list when the log's last entry names
  the new frame's hash. The entry is the record of the change. **Recommended.**
- (b) Keep refusing, as now.

**G and H** stand as recorded:

- G: section 11's point 4 cannot arise with a current final file; the frame applies no outcome `merges` (line 616);
  a plug-in bucketer is refused (line 639).
- H: attribute evidence takes the author's rows, now read through the merges (ruling D); `work_date` takes a
  passage's rows whoever they name (line 626).

## Running post-steps: a design for the operator and `@security` (not built)

A post-step is the project's own Python file. Running one executes project code, so the frame build must run
exactly the cleared bytes, isolated as far as the standard library allows, and check what comes back.

**`@security`'s conditions for part 2.** `@security` set these on the part 1 review. They are conditions, not yet
decided by the operator:

1. **Which gate may allow a run.** Only a blocking gate that the operator has signed and that reads `CLEARED`, pinned
   to the step file's sha256 in that gate's manifest, may allow a run. A build-only gate (S6 in the invented study)
   must refuse a run once running exists, although 6.1's table lets a build-only stage run.
2. **How the step reaches the child.** The step's bytes and the frame go over stdin, never in argv. (An earlier draft
   of this section said both that the bytes were handed over and that the frame went on stdin; both go on stdin.)
3. **The child process.**
   - It reuses `survey_verify`'s `run_child`, in a new session, with the process group killed at the time limit.
   - Its output is read through a bounded reader. stderr is discarded.
   - The interpreter is started as `sys.executable -B -I -S`, with no `PATH` in the environment and no shell.
   - The study's folder is never added to `sys.path`.
   - The step never names its runner: the runner is a fixed snippet of the toolkit's, and the step only defines the
     function the runner calls.
4. **The result.** It is strictly re-parsed, every 4.7 cell check runs again, and it is written only through the
   guarded writer.
5. **When a step never runs.** Never in CI, in a hook, in `survey-validate`, or under a standing grant, a management
   directive or a waiver; and never while a HALT stands.
6. **What the user docs say.** They say plainly that this is not a sandbox.

The design, with those conditions folded in:

1. **Gate and bytes.** For each step, the gates that cover it are checked as built, then condition 1 applies. The
   step file's bytes are read once (`read_capped`, no link followed) and hashed. The hash must equal the file's entry
   in the cleared manifest (@security case 43, the note on `require_gate`). Only those bytes are sent to the child,
   so a file swapped after the check is never run.
2. **The child process** (condition 3):
   - `sys.executable -B -I -S -c <a fixed runner snippet>`;
   - an allowlisted environment with no `PATH`: `LC_ALL=C.UTF-8`, `PYTHONHASHSEED=0`, `TZ=UTC`, and `HOME` an
     empty temporary folder;
   - the working folder a new empty temporary folder, removed afterwards;
   - a time limit (a proposal: 60 s per step), after which the process group is killed;
   - stdout read with a size cap, stderr discarded.

   The runner reads one framed message on stdin: the step's bytes, its declared path (for messages only) and the
   frame as quoted CSV. It compiles the bytes and calls one function the step defines, for example
   `add_columns(header, rows) -> (header, rows)`, the way 5.1 calls a plug-in's `attr` and nothing else. It writes
   the new frame as quoted CSV on stdout.
3. **What a step may write, and where: nothing.** 4.5 says a step "does nothing else", and 5.1 says it "writes no
   file". The frame build writes the result, through `write_all`. The step gets no repository path. Anything it
   leaves in its working folder is discarded.
4. **Checking the output** (lines 539-540; condition 4). The result is re-parsed strictly as quoted CSV and checked:
   - the same `unit_id` values in the same order;
   - every existing column in the same place, with the same values cell for cell;
   - only columns added, at the end, with names that are new, not repeated and not named like a frame column
     (section 3, line 203);
   - every 4.7 cell check again.

   A step that breaks any of these is refused, and the frame is not written. The hash of the frame after the last
   step is what the log's entry names (line 472). Each later step reads what the step before it returned.
5. **The record.** A step file is project code that a gate clears, as a plug-in is. The recommendation is to list it
   under `plugins` as `{file, attr, version, sha256}`: 4.6 (line 564) lists "a plug-in file" under `plugins` only,
   and 5.1 (line 722) records a plug-in's version. `post_steps` is `[path]` (section 3, line 161), with no version
   and no `attr`. Options:
   - (a) a later version makes `post_steps` entries `Plugin` objects (recommended);
   - (b) until then, `version` `""`, `attr` the fixed function name, and the step's hash as `sha256`.
6. **What a standard-library tool cannot enforce.**
   - No network (5.1): no sandbox in the standard library blocks a child's sockets.
   - No clock (5.1): a step can read the time. Running each step twice and refusing on any difference (a proposal)
     catches variation from run to run, not variation by date.
   - No writes outside the working folder: nothing stops the child writing where the user may. The guards detect
     changes only to the files the build hashed.
   - Memory and child processes of its own: the `resource` module is not on every platform.

   The binding control is the gate: a person reads the step and the operator signs it. The isolation lowers the
   risk of an accident and is not a sandbox (condition 6), the position 5.1 takes for plug-ins.

## Tightenings

1. The frame-change log's internal consistency (the fourth row of the log table).
2. A post-step's path lies inside the study's folder, with no link, and is a regular file. Rule 1.6 asks only that
   it stays in the repository.
3. A value longer than the bucket matcher's cap (4.8) refuses the frame (`frame-value-too-long`).
4. An output may not be named as a record, nor be the final file or its record, nor be another output of the same
   run (`write_outputs`).
5. As for the rollup (O3), the final file's bytes must be what finalising gives, in every status.
6. Merged ids that carry two `author_kind` values refuse the frame and the rollup (`author-kinds`).
7. A frame-change log whose last line does not end in a line feed is refused before an entry is appended.
8. B3's replacement is narrower than "replace": only `survey-frame`, only its own outputs with its own record
   beside each, only when the log's last entry names the new frame. D2 and D5 stand for every other command.

## Proposals for a later contract version

1. Rulings A to F, B2 and B3, each as ruled. B2 is an exception to line 549: the frame-change log, which a tool now
   writes, has no record of its own, and the records that rest on it list it as it stands after the append. B3: an
   output may be replaced by its own tool when a recorded change names it.
2. A declared field for the frame's path, so that `survey-validate` can run the log's hash check (B, C).
3. `post_steps` entries as `Plugin` objects (the design, point 5).
4. Running each post-step twice to check determinism (the design, point 6).
5. Whether a frame-change entry is required when only the dropped list or the passage list changes. The text makes
   the log follow the frame file alone (line 472).

## What part 1 does not satisfy

- **4.5 (lines 534-544):** post-steps are not run. A study that declares any is refused after its steps' paths and
  gates are checked. This is part 2, after the design and `@security`'s conditions are ruled on.
- **5.2, line 745:** a vantage module's exclusions, recorded in the frame-change log, are not implemented. Such a
  study is refused, as the registry refuses it.
- **4.4, line 475:** `results_seen` "is shown wherever the change is reported". No tool reports changes yet.
