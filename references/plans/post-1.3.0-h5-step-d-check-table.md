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

`write_outputs` writes the frame, the passage list and their records in one `write_all`: the outputs first, the
records last.

## The frame-change log (4.4, lines 461-476)

| Line | Sentence or rule | Id | Test |
|---|---|---|---|
| 461-467 | One JSON Lines entry per change, with the nine fields and their types | `change-log` | `test_a_malformed_log_is_refused_and_no_entry_proposed[...]` |
| 469 | "The log is the file `frame_rules.change_log` names" | — | `test_the_records` (the log is the record's last input) |
| 469-471 | A passage or work frame's units are its `unit_id` values, the cells' ids: "the log records cells, not passages" | — | `test_no_entry_refuses_and_prints_the_entry_needed` (the entry lists cell ids) |
| 472-473 | `frame_sha256` is the hash of the frame file "as it stands after the last post-step", computed as a manifest computes a text file's (6.1: each CRLF made LF) | — | `test_the_frame_hash_is_a_text_files`, `test_the_invented_studys_frame_and_passage_list` |
| 473 | "The first entry lists every unit as added" | `change-log` | `test_a_malformed_log_is_refused_and_no_entry_proposed[...]` |
| 474-475 | `id` is what a report cites; `results_seen` records whether a result had been seen, "shown wherever the change is reported" | `change-log` (an empty or repeated `id`) | `test_a_malformed_log_is_refused_and_no_entry_proposed[...]`. No tool reports changes yet, so "shown wherever reported" has no reader in part 1 |
| 475-476 | "The check fails when the current frame's hash differs from the last entry's: a frame cannot change without an entry" | `change-log-entry` | `test_no_entry_refuses_and_prints_the_entry_needed`, `test_a_changed_frame_needs_a_new_entry` |
| 1.2, 1.5 | The check fails before anything is written (rule 1.2). The entry the log needs is printed with `id`, `date`, `reason` and `results_seen` left for the author, because no tool fills in a date or a reason (rule 1.5). Who writes the entry is open point B | — | the same two tests |
| (tightening 1) | No blank line. `frame_sha256` is 64 lower-case hex digits. `n_units` is the number of `units`, and `units` has no repeats. A later entry's `added` and `removed` are exactly what its `units` gained and lost since the entry before. The last entry's `units` are the frame's, in its order | `change-log`, `change-log-entry` | `test_a_malformed_log_is_refused_and_no_entry_proposed[...]`, `test_a_later_entry_lists_what_changed` |

## Post-steps (4.5, lines 532-544): checked, not run

| Line | Sentence | Id | Test |
|---|---|---|---|
| 534-535 | `frame_rules.post_steps` lists the project's scripts, "run in the order given after the frame is written"; a step adds columns and does nothing else | — | **not run** in part 1 (see "Running post-steps") |
| 537-538 | The frame build runs each step; later checks treat the frame as it stands after the last step | `post-steps-unavailable` | `test_post_steps_allowed_by_their_gate_are_not_yet_run` |
| 539-540 | A step that changes the units, their order or an existing column is refused | — | design below |
| 541 | A step is deterministic and follows 5.1 on network and clock | — | design below |
| 542-544 | Each step file is covered by a gate; "while that gate is blocking and not cleared, the frame build refuses to run the step" | `post-step-gate`, `post-step-uncovered` | `test_a_post_step_under_a_blocking_gate_not_cleared_is_refused` (S5, blocking, UNCLEARED), `test_post_steps_allowed_by_their_gate_are_not_yet_run` (S6, build-only) |
| 1.6 (tightening 2) | Each step's path: rule 1.6, inside the study's folder, no link on its way, a regular file | `post-step-place`, `post-step-file` | `test_a_post_step_outside_the_study_folder_is_refused`, `test_a_linked_post_step_is_refused` |
| — | No step is executed: no child process is started and nothing is imported | — | `test_no_post_step_is_executed` |

## The frame (4.7, lines 575-671)

| Line | Sentence or rule | Id | Test |
|---|---|---|---|
| 577-578 | The frame is written from the final codes, the attribution file, the evidence and the specification | — | `test_the_invented_studys_frame_and_passage_list` |
| 579-580 | "the frame tool refuses to run in" an author study | — | `test_an_author_study_is_refused` |
| 582-585 | A cell is one author and one value of each `rollup_by` attribute; `unit_id` is `<person_id>\|<value>\|...` in `rollup_by` order, the `person_id` alone without `rollup_by` | — | `test_cells_split_by_rollup_by_and_ordered_by_code_point`, `test_the_period_rule` (no `rollup_by`) |
| 587-589 | The units behind a cell are the rollup's: of that author and those values, with no `exclude_from_rollup` value and a counted status | — | `test_a_cell_without_a_counted_passage_is_not_in_the_frame` |
| (reading 1) | The frame's cells are those with at least one counted passage (open point E) | — | `test_a_cell_without_a_counted_passage_is_not_in_the_frame` |
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
| 635-638 | Attribute values: the author's counted-tier rows whose `attribute_kind` is a source attribute and whose `unit_id` is the person's own id or one of the cell's passages, in evidence-file order, bucketed by the table (4.8). A categorical attribute with no value gets the missing value | `frame-value-too-long` (a value over the matcher's cap, 4.8) | `test_attribute_evidence` |
| 638-639 | "A plug-in bucketer is refused in a frame, and nothing is written (open point 6)" | `frame-plugin-bucketer` | `test_a_plug_in_bucketer_is_refused` |
| 641-644 | `not-on-question`: a cell whose outcome columns are all empty is left out and written to `<frame>.dropped.csv` (`unit_id, rule, reason`); without the rule the cell stays | `frame-dropped-name` (**stopped**: open point A) | `test_not_on_question_drops_cells_with_all_outcomes_empty` (built), `test_a_study_declaring_not_on_question_stops_on_the_open_point` |
| 646-649 | CSV, every cell quoted, LF, rows in ascending code-point order of `unit_id`; the passage list in evidence-file order; `frame_sha256` from the frame file | — | `test_every_cell_is_quoted`, `test_cells_split_by_rollup_by_and_ordered_by_code_point`, `test_the_invented_studys_frame_and_passage_list` |
| 651-652 | Every cell checked before anything is written: each value one its column allows, each `unit_id` unique, every column present; on any breach nothing is written and the breaches are listed | `frame-value`, `frame-unit-duplicate`, `frame-column` | `test_every_cell_is_checked` |
| 653 | "The finalised codes must be current (4.6)" | — | `test_a_final_file_that_is_not_current_is_refused`, `test_a_hand_edited_final_file_is_refused` |
| 653 | "The frame's provenance record lists gates S5 and S6" | — | `test_the_records` |
| 654 | "Post-steps (4.5) run after these checks" | — | not run in part 1 |
| 656-660 | The passage list: one row per evidence row whose `unit_id` is an attribution unit, counted or not; its columns | — | `test_the_invented_studys_frame_and_passage_list` |
| 661-663 | `unit_id` is the passage's cell, or the cell it would be in if counted; `passage_id`, `person_id` (the attributed author), `attribution` (its status), `counted` `true` or `false` | — | the same |
| 663-669 | The first reason that applies: `tier-<tier>` (`tier-blank`); `excluded-<attribute>-<value>` (the first key in the specification's order); `attribution-<status>` (`attribution-blank`); `not-on-question` | — | `test_the_passage_list_reasons_in_order`, `test_not_on_question_drops_cells_with_all_outcomes_empty` |
| 671 | "Person-level rows are not listed" | — | `test_the_invented_studys_frame_and_passage_list` (ev-002 and ev-004 are not listed), `test_the_passage_list_reasons_in_order` |
| 4.6 | Each output's record: 4.6's shape, every file read (rule O4: gate reads stand under `gates`), `plugins` empty (no plug-in is loaded), the legacy exceptions; current after the write | — | `test_the_records`, `test_the_records_inputs_are_the_files_read` |
| 1.5 | The same bytes in two repositories; "unchanged" on a second run | — | `test_deterministic_and_unchanged_twice` |
| D2 (as for the final codes) | An existing output is never written over with other bytes; outputs lie inside the study's folder and are not declared files; no output is named as a record, the final file or its record | — | `test_an_existing_different_output_is_refused`, `test_where_the_outputs_may_not_go[...]` |
| 7, 935 | The bridge command, refusing `--root`; usage errors exit 2 | — | `test_the_bridge_runs_the_command_and_refuses_root`, `test_usage_errors` |
| 5.2 | A vantage module's `included()` exclusions are recorded in the frame-change log: a vantage module is not loaded by this version, so such a study is refused (fail closed) | `identity-vantage` | `test_a_vantage_module_is_refused` |

## What the contract leaves open (for the operator to rule on)

Each point gives the options and a recommendation. The first-named option is the recommended one, except where the
recommendation is stated otherwise. **Stopped** means that a study the point touches is refused until the operator
rules. Everything else is built as the recommendation says.

**A. The dropped list's file name** (line 643: "written to `<frame>.dropped.csv`"). **Stopped.** A study that
declares `not-on-question` is refused, because the frame and dropped list cannot be written without the name. Cells
are still worked out and tested.

- (a) The frame's path with its `.csv` suffix replaced: `out/frame.csv` gives `out/frame.dropped.csv`. A frame path
  that does not end in `.csv` is refused. **Recommended.** Where 4.6 means "added", it says so (line 562: "named as
  the output with `.provenance.json` added"), and 4.7 does not say it here.
- (b) The frame's path with `.dropped.csv` added: `out/frame.csv.dropped.csv`.
- (c) A `--dropped <path>` argument.

With it, two sub-points:

- When the rule is declared and no cell is dropped: (a) write the dropped list with its header only, so a stale list
  never stands beside a new frame (recommended); or (b) write none.
- When the rule is not declared and a dropped list from an earlier build is there: (a) refuse, and the project
  removes it (recommended; the survey tools never delete a file); or (b) ignore it.

**B. Who writes a frame-change log entry.** Section 3 (line 218) lets `change_log` be absent "because a stage writes
them or they start empty". Rule 1.5 says "a log row carries the date its author gives it". Built now: the check
refuses, and the command prints the entry the log needs.

- (a) `survey-frame` appends the entry itself. The author gives `--change-id`, `--date`, `--reason` and
  `--results-seen yes|no`, and the entry goes in the same `write_all` as the frame, the log written last.
  **Recommended.** Without those arguments the command behaves as now.
- (b) The author always writes the entry by hand, as built.

Where the check also runs: `survey-validate` cannot check the hash, because no field declares where the frame is
(open point C). The recommendation is that `survey-validate` checks the log's shape when the log is there (a
proposal).

**C. The command's arguments and the passage list's name.** Section 7 names the command only. Built:
`survey-frame <project> <final file> --out <frame> --passages <path>`, as D2 and D5 did for finalising and the
rollup.

- (a) As built. **Recommended.**
- (b) The passage list beside the frame under a fixed name (for example `<frame>.passages.csv`, named like A), with
  no `--passages`.

**D. Ids the registry has merged that the rows still name.** 4.7 reads "the author's rows" and the cell's
`person_id`, and does not say whether an id in a registry row's `merged_from` is that person's. **Stopped.** A study
whose attribution or evidence file names such an id is refused (`frame-merged-id`).

- (a) Read a merged id as its person: the cell's author, and "the author's rows", go through the registry. This is
  not inference (rule 1.3): a merge is a recorded override (4.4, line 505). **Recommended.**
- (b) Refuse, as built, so that the project rewrites its rows to the merged id.
- (c) Take ids as written. Two cells would then be one person.

**E. Which cells the frame has** (reading 1, built).

- (a) The cells with at least one counted passage. **Recommended.** Line 661 has a passage's `unit_id` be "the cell
  the passage belongs to, or would belong to if it were counted", which reads a cell as made by counted passages.
  The rollup also leaves out an author all of whose units were left out (4.2, lines 409-410).
- (b) Every author and value combination any attribution row makes. A cell with no counted passage would then have
  every outcome empty, and would stay in the frame as an empty row wherever `not-on-question` is not declared.

**F. The passage list's record.** Line 653 names the gates only for the frame's record. Built: the passage list's
record lists S5 and S6 too, since it is an output of the same stage.

- (a) As built. **Recommended.**
- (b) `gates` `{}`.

**G. Section 11 points 4 and 6, as they bear on part 1.** Nothing to rule on now; recorded so that no one has to
rediscover them.

- Point 4 (a counted unit with no final code): line 621 says it counts as "none", and that is built. Under D4
  finalising refuses a unit with no pass, so with a current final file the case cannot arise.
- Point 6 (outcome `merges`): the frame writes "a level code" (line 616) and applies no merge, because a merge's
  target "may be a new label" (section 3, line 190), which the column would not allow. Point 6 stays open for the
  tool that applies merges.
- Point 6 (frame rules over cells): section 3 refuses every rule but `not-on-question` in a passage or work study.
- Point 6 (a plug-in bucketer): refused (line 639).

**H. Rows of a passage whose `person_id` is not the attributed author.** A legacy study can list `unit-person` as an
exception. Built: attribute evidence takes the author's rows only (line 636: "the author's rows"). `work_date` takes
the passage's rows whatever their `person_id` (line 626 names no author). Recommended as built.

## Running post-steps: a design for the operator and `@security` (not built)

A post-step is the project's own Python file. Running one executes project code, so the frame build must run
exactly the cleared bytes, isolated as far as the standard library allows, and check what comes back.

1. **Gate and bytes.** For each step, `require_gate` on every gate that covers it, as built. Then the step file's
   bytes are read once, through `read_capped` with no link followed, and hashed. The hash must equal the file's
   entry in the cleared manifest of the covering gate (the note on `require_gate`, @security case 43). The child
   process is then given those bytes, not the path, so a file swapped after the check is never run.
2. **Starting the child process**, as `survey_verify` starts `agentteams`:
   - `sys.executable -B -I -c <a fixed runner snippet>` (`-I`: no user site-packages, no `PYTHON*` variables, no
     script folder on `sys.path`; `-B`: no bytecode written);
   - an allowlisted environment: `PATH` set to the interpreter's own folder, `LC_ALL=C.UTF-8`, `PYTHONHASHSEED=0`,
     `TZ=UTC`, `HOME` an empty temporary folder, nothing else;
   - a fixed working folder: a new empty temporary folder, removed afterwards;
   - stdin closed, a time limit (`subprocess.run(timeout=...)`, a proposal of 60 s per step), and stdout and stderr
     captured with a size cap;
   - no shell.

   The runner snippet compiles the step's bytes under its declared path and calls one function the step must define,
   for example `add_columns(header, rows) -> (header, rows)`, the way 5.1 calls a plug-in's `attr` and nothing else.
   It passes the frame as data on stdin (the quoted CSV) and reads the result back as quoted CSV on stdout.
3. **What a step may write, and where: nothing.** 4.5 says a step "does nothing else", and 5.1 says it "writes no
   file". The step returns the new frame on stdout; the frame build checks it and writes it through `write_all`.
   The step gets no path of the repository to write to. Its working folder is a temporary one, and anything left
   there is discarded.
4. **Checking the output** (lines 539-540). The same `unit_id` values in the same order; every existing column
   present, in the same place and with the same values, cell for cell; only columns added, at the end, with names
   that are new, free of repeats and not named like a frame column (section 3, line 203). A step that breaks any of
   these is refused, and the frame is not written. The new frame's hash is what the log's entry must name (line
   472). Every later step reads the frame the previous step returned.
5. **The record.** A step file is project code that a gate clears, as a plug-in is. The recommendation is to list it
   under `plugins` as `{file, attr, version, sha256}`. 4.6 (line 564) lists "a plug-in file" under `plugins` only,
   and 5.1 (line 722) records a plug-in's version. Here `attr` would be the function the runner calls and `version`
   the step's declared version. `post_steps` is `[path]` (section 3, line 161), so it carries no version and no
   `attr`. Options:
   - (a) a later contract version makes `post_steps` entries `Plugin` objects (recommended);
   - (b) until then, `version` `""`, `attr` the fixed function name, and the step's hash as `sha256`.
6. **What a standard-library tool cannot enforce.**
   - **No network** (5.1). No sandbox in the standard library blocks sockets for a child process. Clearing
     proxy variables and giving an empty `HOME` stop only the casual case. A step can still open a socket.
   - **No clock** (5.1). A step can read the time. `TZ=UTC` and a fixed seed make it reproducible only if the step
     does not read the clock. Determinism (line 541) can be checked only after the fact, by running the step twice
     and comparing its outputs (a proposal: the frame build runs each step twice and refuses on any difference).
     Even that misses a step that varies by date rather than by run.
   - **No file writes outside the working folder.** Nothing in the standard library stops a child process from
     writing where the user may write. The frame build can detect changes only to files it hashed (its inputs, by
     the guards).
   - **Resource use** beyond the time limit and the output cap (memory, child processes of its own): the `resource`
     module works on Linux and macOS only, and not on every platform.

   So the binding control is the gate: a person reads the step and the operator signs it. The isolation above
   lowers the risk of an accident, but it is not a sandbox. This is the same position 5.1 takes for plug-ins.

## Tightenings

1. The frame-change log's internal consistency (the fourth row of the log table).
2. A post-step's path lies inside the study's folder, with no link, and is a regular file. Rule 1.6 asks only that
   it stays in the repository.
3. A value longer than the bucket matcher's cap (4.8) refuses the frame (`frame-value-too-long`).
4. An output may not be named as a record, nor be the final file or its record, nor be another output of the same
   run (`write_outputs`).
5. As for the rollup (O3), the final file's bytes must be what finalising gives, in every status.

## Proposals for a later contract version

1. Points A to F above, each as ruled.
2. A declared field for the frame's path, so that `survey-validate` can run the log's hash check (B, C).
3. `post_steps` entries as `Plugin` objects (the design, point 5).
4. Running each post-step twice to check determinism (the design, point 6).
5. Whether a frame-change entry is required when only the dropped list or the passage list changes. The text makes
   the log follow the frame file alone (line 472).

## What part 1 does not satisfy

- **4.5 (lines 534-544):** post-steps are not run, and a study that declares any is refused after its steps' paths
  and gates are checked. This is part 2, after the design above is ruled on.
- **4.7, lines 641-644:** the dropped list is not written, and a study declaring `not-on-question` is refused
  (point A).
- **4.7, through point D:** a study whose rows name a merged id is refused.
- **5.2, line 745:** a vantage module's exclusions, recorded in the frame-change log, are not implemented. Such a
  study is refused, as the registry refuses it.
- **4.4, line 475:** `results_seen` "is shown wherever the change is reported". No tool reports changes yet.
