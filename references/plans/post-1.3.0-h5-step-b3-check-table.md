# H5 step B part 2b: check table (survey toolkit against `docs/survey-toolkit.md`, version 1)

Plan: `post-1.3.0-h5-survey-tools-a-d.plan.md`, step B. This pull request is **part 2b**: the batch merge
(`survey-rows`) and the first exceptions draft. Line numbers are those of `docs/survey-toolkit.md` at `f22ac9d`. Tests
are in `tests/test_survey_merge.py` unless another file is named; `[...]` is one parametrized case. Ids marked
"toolkit" are the toolkit's own.

**Gates.** `survey-rows` is not a gated stage. 6.1 (lines 786-791) names enumeration (S0), coding packets (S5),
analysis (S6) and the report (S8); 4.4 (lines 515-523) makes the merge depend on the registry being built, not on a
gate; 4.5 (post-steps) does not concern it. So no `require_gate` call.

## The batch (4.1, lines 322-326)

| Line | What is checked | Id | Test |
|---|---|---|---|
| 322 | "Rows are written as a batch file with the same columns": exactly the eighteen evidence columns, in order | `columns` | `test_a_malformed_or_empty_batch_refuses[other-columns]`, `[no-header]` |
| (proposal 1) | Where a batch is: a path argument, relative to the study's folder or `repo:`-rooted (rule 1.6), that lies inside the study's folder and is a regular file other than the evidence file, read through the capped reader (no final link, no FIFO) | `batch-place` (toolkit), the path ids | `test_where_a_batch_may_not_come_from[...]` (seven cases), `test_a_batch_linked_outside_the_repository_refuses`, `test_a_batch_that_is_a_fifo_is_not_opened` |
| (proposal 2) | An empty batch merges nothing and is refused | `batch-empty` (toolkit) | `test_a_malformed_or_empty_batch_refuses[empty]` |
| section 4 (part 1) | A NUL in a batch cell | `cell-nul` | `test_a_malformed_or_empty_batch_refuses[nul]` |
| 322-323 | "merged by the row tool … nothing is appended unless every row passes": the batch's rows are appended after the file's, in batch order; the file's own bytes are kept as they are ("appended"; existing rows never rewritten) | — | `test_a_batch_is_appended_and_the_registrys_record_renewed` |
| (proposal 3) | The appended rows use the file's own line ending (CRLF where the file uses it, else LF); a file whose last line has no line ending gets one first | — | `test_a_batch_keeps_the_files_crlf_line_endings`, `test_a_file_without_a_final_line_feed_gets_one` |
| (proposal 4) | In a draft without an evidence file yet, the first batch creates it (header, then the rows) | — | `test_a_first_batch_creates_the_evidence_file_in_a_draft` |
| 323 | "A batch is checked in full, together with the file it joins": every check of 4.1, 4.3 and 4.8 runs over the merged file, so a breach already in the file refuses too | the rule ids of 4.1 | `test_a_batch_row_that_fails_a_check_refuses[...]` (five cases), `test_a_breach_already_in_the_file_refuses` |
| 323; 308 | A duplicate id between the batch and the file, or within the batch: decided by `id-duplicate` over the merged file | `id-duplicate` | `test_a_batch_row_that_fails_a_check_refuses[...]` (two cases) |
| 308 | A batch row whose person the registry does not hold | `person-unknown` | `test_a_batch_with_a_new_person_refuses` |
| 324 | "A legacy exception never covers a batch row" | the rule's id | `test_a_legacy_exception_never_covers_a_batch_row` |
| (proposal 5) | A batch row gets no legacy leniency on receipts: 5.4 (lines 774-775) excuses rows "that predate receipts", which a row added now does not | `receipt-missing` | `test_a_batch_row_gets_no_legacy_leniency_on_receipts` |
| 325 | "Merging into a `plugin` format is the project's own write path and is refused" | — | `test_a_merge_into_a_plugin_format_refuses` |
| 1.2 | A malformed specification refuses | — | `test_a_malformed_specification_refuses` |

## The registry's record (4.4, lines 515-523; 4.6)

| Line | What is checked or written | Id | Test |
|---|---|---|---|
| 516 | "It refuses unless the registry is built": the registry's record is there, by `survey-registry`, for this `schema_version`, and its inputs match (4.6, lines 566-567) | — | `test_the_registry_must_be_built`, `test_a_stale_registry_refuses` |
| 516-521 | "Before writing anything it works out the merged evidence file and the registry that a build over it would give. If that registry's rows differ from the present ones … it stops, writes nothing, and says that the registry must be built first": the build of part 2a (`plan_registry`), run over the merged file in memory, compared row by row with the registry on disk | — | `test_a_batch_with_a_new_person_refuses`, `test_a_hand_edited_registry_is_found` |
| 4.6, 565 (residual of part 2a) | A registry edited by hand, which its record cannot see (it holds no hash of the registry), is found by that comparison | — | `test_a_hand_edited_registry_is_found` |
| 521-523 | "Otherwise it writes the evidence file and then the registry's new provenance record, last": the renewed record is the record a fresh build over the merged file writes, so `survey-registry` afterwards changes nothing | — | `test_a_batch_is_appended_and_the_registrys_record_renewed` |
| 522-523 | "so that an interrupted run leaves the registry not built and never wrongly current": interrupted after the evidence file, the old record names the old evidence hash and reads as not built; a build makes it current again | — | `test_an_interruption_between_the_writes_leaves_the_registry_not_built` |
| 1.2 | Both targets are checked again after the temporary files are written and before either replace (`write_all`), so a refusal at either late check changes nothing; an OSError is a refusal | — | `test_a_write_refused_at_either_last_check_changes_nothing[...]`, `test_an_os_error_while_writing_is_a_refusal` |
| 1.5 | The merged file and the record are the same bytes in two repositories | — | `test_the_merged_file_is_byte_deterministic` |
| (part 2a proposal 14) | The evidence file is written only through `check_output_target` with its own pointer: inside the study's folder, and no other declared path (a gate's covers included) may name it | — | `test_an_evidence_file_outside_the_study_folder_is_not_written`, `test_an_evidence_file_a_gate_covers_is_not_a_target` |
| (proposal 6) | 4.6 (line 568) lets a stage run in a `draft` study when a record does not match; 4.4 (line 516) says the merge "refuses unless the registry is built". The merge follows 4.4, the narrower and more specific rule, in a draft too | — | `test_the_registry_must_be_built` |

## A first exceptions file (4.1, lines 364-365)

| Line | What is checked | Id | Test |
|---|---|---|---|
| 364-365 | "The tool can write a first version from the current breaches for a person to review": `survey-rows <project> --draft-exceptions` prints `id,rule` for each current breach, in file and rule order, and writes nothing (proposal 7) | — | `test_a_first_exceptions_file_is_printed_and_nothing_is_written` |
| 365 | "it never adds to an existing one": refused when the study already declares `evidence.legacy_exceptions` (a declared file must exist outside a draft, section 3 line 217, and only a legacy study declares one, line 224) | — | `test_a_first_exceptions_file_never_adds_to_an_existing_one` |
| 363 | Only in a legacy study | — | `test_a_first_exceptions_file_is_for_a_legacy_study` |
| 357-358 | A breach of `columns`, `id-empty` or `id-duplicate` cannot be listed, so no draft is written while one stands | the rule's id | `test_no_first_exceptions_file_while_an_unlistable_breach_stands` |

## Command and bridge (section 7, line 929)

| Line | What is checked | Output | Test |
|---|---|---|---|
| 929 | `survey-rows` "checks a batch of evidence rows and merges it into the evidence file, renewing the registry's record or refusing where it could not" | `survey-rows <project> <batch>` | `test_the_bridge_runs_survey_rows_and_refuses_root` |
| step A pattern | The bridge refuses a user-supplied `--root` | exit 2 | `test_the_bridge_runs_survey_rows_and_refuses_root` |
| — | Usage errors exit 2 | — | `test_usage_errors` |

## Follow-ups from the last reviews

| Item | What changed | Test |
|---|---|---|
| (a) | Step F's messages that quote ledger-log cells (`survey_gates.py`: the action, verdict, conditions, key id, author, and the signer line; `survey_ledger.py`: the family-HALT action) go through `q()`, cut at its length | `tests/test_survey_verify.py::test_status_escapes_every_value_from_a_log` (expects the `repr` form) |
| (b) | `survey_provenance.gate_entries`'s docstring says `CLEARED` is reachable since step F | — |
| (c) | The `gate_entries` test asserts `UNCLEARED` (no request for S0) | `tests/test_survey_registry.py::test_gate_entries_record_each_state_as_gate_status_gives_it` |
| (d) | Carriage-return and tab cases for the padded-id exemption of the family-HALT scan | `tests/test_survey_verify.py` (three cases) |
| (e) | The part 2a table's "Residual" says part 2b's merge now detects a registry that differs from a fresh build | — |

## Not implemented

| Section, line | What | Why |
|---|---|---|
| 4.1, 325 | A merge into a `plugin` format | The text refuses it: "the project's own write path" |
| 5.4, 768-776 | Re-finding a batch row's quotation | Step G (the seam `refind_quotation`) |

## Proposed contract changes

1. **Where a batch comes from**: a path argument under rule 1.6 that lies inside the study's folder and is a regular
   file other than the evidence file (the text says "a batch file" and nothing of its place).
2. **An empty batch** is refused: it merges nothing.
3. **Line endings of appended rows**: the file's own (CRLF where it uses CRLF, else LF); a missing final line ending
   is added before the first appended row.
4. **A first batch in a draft** creates the evidence file (header, then the rows).
5. **No legacy receipt leniency for a batch row**: 5.4's leniency is for rows "that predate receipts".
6. **A record mismatch in a draft**: the merge refuses (4.4, line 516), although 4.6 (line 568) lets a stage run.
7. **The first exceptions draft is printed, not written**: the text names no place for it, and the exceptions file is
   covered by a gate, so the person saves it, declares it as `evidence.legacy_exceptions` and covers it.
