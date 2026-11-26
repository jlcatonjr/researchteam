# H5 step C part 2: check table (survey toolkit against `docs/survey-toolkit.md`, version 1)

Plan: `post-1.3.0-h5-survey-tools-a-d.plan.md`, step C. This pull request is **part 2** of step C: `survey-finalize`
(4.2, lines 397-400; section 7, line 933) and `survey-rollup` (4.2, lines 403-422; section 7, line 934), built on part
1b (pull request #270). Line numbers are those of `docs/survey-toolkit.md` at `251b1f0` (unchanged since). Tests are in
`tests/test_survey_final.py`. Ids are the toolkit's own.

## Operator decisions (2026-11-25)

The operator ruled on the open points of part 2 (picker, 2026-11-25), starting from the first integrating project's
reference tool. Each is decided for the toolkit, and each is a proposal for a later contract version, since the
contract's text does not contain it.

- **D2** Final codes go to a file of their own, `survey-finalize <project> --out <path>`; the path lies inside the
  study's folder and is not a file the study declares or a gate covers (`check_output_target`, `write_all`, guards on
  every input read). The passes file is only read. Rows have the codes columns with `pass` = `final`. An existing
  output is never appended to: identical bytes are "unchanged", anything else is refused.
- **D3** An agreed unit's final row is pass A's row with `coder` = `agreed`, `level` empty, and `note` = `agreed`, or
  `agreed; evidence differed` when the two passes' `evidence_ids` differ (compared as sets of ids). A disagreement
  takes its adjudication's coder, basis, reporter, evidence and note; a unit with one pass needs a missing-pass
  adjudication (part 1's check).
- **D4** A unit with no pass at all refuses finalising, every such unit listed, coverage judged against the study's
  units (the attribution file's units; in an author study the registry's persons). **Stricter than the reference
  tool.**
- **D5** `survey-rollup <project> <final file> --out <path>`, the same path rules; the input must be a current
  `survey-finalize` output. Columns: `person_id`; each `unit.rollup_by` key; `author_kind`; one per coded outcome whose
  rollup is not `none`; `<outcome>__types` where `unit.rollup_types` is set.
- **D6** Both records list gate S5 only (its state from `gate_entries`), the inputs read with their hashes, and
  `legacy_exceptions` where 4.1 (line 366) requires it. Neither command is a refusing stage.

After the reviews of pull request #272 the operator ruled on three more points (picker, 2026-11-25):

- **O1** `<outcome>__types` holds each distinct value once, joined with `;`, in the order the study declares that
  passage attribute's levels. Code-point order applies only where the attribute declares no levels, or to a value that
  is not among them; such values come after the declared ones, in code-point order. (Once the attribution file passes
  4.3's checks, every value is one of the declared levels, so this fallback cannot be reached.) Which units are
  "behind" a cell the contract decides (4.7, lines 587-589): see the rollup table.
- **O2** A codes file that already holds `final` rows is accepted if they match. The contract allows and checks them
  (4.2, lines 372 and 384). Finalising, and the rollup's re-derivation, derive the final rows from passes A and B and
  the adjudications, then compare each existing `final` row with the derived row for the same outcome and unit, cell
  for cell, in every column the final file carries. If every one is equal and none is extra (a final row for a unit
  and outcome that has no derived row), the separate file is written. Otherwise the run refuses and names the row.
  With D3, a derived agreed row has coder `agreed` and note `agreed` or `agreed; evidence differed`. A study's own
  final row made by hand from pass A's row keeps pass A's coder and note, so it is refused. That is intended.
- **O3** The rollup refuses a final file whose bytes differ from the derived final codes in every status, draft
  included (a tightening). The draft leniency of 4.6 (line 568: "In a `draft` study the mismatch is reported and the
  stage runs") applies where it speaks: to the final file's record. When `check_current` says the record no longer
  matches its inputs (or is missing) but the bytes still equal the derived ones, a draft study prints the reasons and
  goes on; any other status refuses.

## Finalising (4.2, lines 397-400; D2-D4, D6)

| Line | What is checked or written | Id | Test |
|---|---|---|---|
| 397 | "Where passes A and B agree, the final row is theirs": pass A's row, marked as D3 says | — | `test_the_invented_studys_final_codes`, `test_an_agreed_unit_with_the_same_evidence_says_agreed` |
| 397-399 | "Where they disagree, or where one pass is missing, the final row is the adjudication's, with the adjudication's own coder, basis, evidence and note" | — | `test_the_invented_studys_final_codes` |
| 399 | "Without one, no final row is written; the tool lists the units and exits non-zero" | `final-no-adjudication` | `test_a_disagreement_without_an_adjudication_refuses`, `test_a_unit_with_one_pass_and_no_adjudication_refuses` |
| 400 | "A single pass never becomes final on its own" | `final-no-adjudication` | `test_a_unit_with_one_pass_and_no_adjudication_refuses` |
| D4 (a tightening against the reference tool) | A unit with no pass refuses; every such unit listed; in an author study the units are the registry's persons | `final-no-pass` | `test_a_unit_with_no_pass_refuses_and_every_one_is_listed`, `test_finalising_in_an_author_study_uses_the_registrys_persons` |
| 1.2 | Every row and code file passes its checks first | the files' ids | `test_a_code_file_error_refuses` |
| 372, 384; O2 | A `final` row in the codes file is allowed if it is the derived row, cell for cell; one that differs, or has no derived row, refuses, the row named | `final-differs`, `final-extra` | `test_a_final_row_in_the_passes_file_that_matches_is_accepted`, `test_a_final_row_in_the_passes_file_that_differs_is_refused`, `test_a_final_row_in_the_passes_file_with_no_derived_row_is_refused` |
| D3 (proposal 4) | "Evidence differed" compares the two passes' `evidence_ids` as sets | — | `test_evidence_differed_compares_sets_of_ids` |
| D2 | Where the output may go: inside the study's folder, not a declared or covered file, not in the ledger, no link | the target's refusals | `test_where_the_final_codes_may_not_go[...]` (seven cases), `test_a_linked_output_folder_is_refused` |
| 562 (tightening 3) | An output named as a record (ending `.provenance.json`, case folded) is refused; a file at the record's path that is not a 4.6 record whose `output` is this output and whose `tool` is this command is never written over; the record path has no link on its way | — | `test_an_output_named_as_a_record_is_refused[...]`, `test_an_unrelated_file_at_the_record_path_is_refused`, `test_another_outputs_record_at_the_record_path_is_refused`, `test_a_record_another_tool_wrote_at_the_record_path_is_refused` |
| 1.2 | Every file whose hash goes into a record or a guard is read under one cap (`MAX_INPUT_BYTES`), the one the guards re-read with | — | (no behaviour change: both caps were 64 MiB) |
| D2 | An existing output: identical bytes are "unchanged"; different ones refused | — | `test_finalising_is_deterministic_and_unchanged_twice`, `test_an_existing_different_output_is_refused` |
| 1.2 | A refusal at either late check, and an input that changed since it was read (the guards), change nothing | — | `test_a_refusal_at_either_late_check_changes_nothing[...]`, `test_an_input_changed_before_the_write_refuses[...]` |
| 1.5 | The same bytes in two repositories; rows in the outcomes' declared order, then code-point order of `unit_id` | — | `test_finalising_is_deterministic_and_unchanged_twice` |
| 563; D6 | The record: 4.6's shape; every file read ("`inputs` lists the files the tool actually read"), with its hash, or `""` for a declared file that is absent: the specification, each coded outcome's codes and adjudications files, the evidence file and its exceptions file, the attribution file (passage or work), the registry, the overrides file, the forbidden vocabulary and each bucket table. No fetch receipt is read (the next row), so the list is exactly the files the command opens, gate S5's reads aside (see "The gates entry"). Gate S5 only, with its state and mode; the legacy exceptions | — | `test_the_final_codes_record`, `test_the_records_inputs_are_the_files_read[finalize]` |
| 563 | Finalising, and the rollup's re-derivation, read no fetch receipt: the row checks run without the 5.4 citation check (`check_row_files(citations=False)`). Nothing in 4.2 (lines 397-422) makes final codes or the rollup rest on a receipt's contents; the receipt check stays with `survey-validate`, `survey-rows` and the later quotation step. Every other check runs: the 4.2 code and adjudication checks, 4.3, the 4.1 row checks, the registry | — | `test_neither_command_reads_a_receipt[...]` (a receipt missing or broken: `survey-validate` reports it, both commands run and open nothing under the receipts folder) |

## The rollup (4.2, lines 403-422; D5, D6)

| Line | What is checked or written | Id | Test |
|---|---|---|---|
| 403 | "takes passage or work codes to their author": refused in an author study | — | `test_a_rollup_in_an_author_study_is_refused` |
| 405 | Only `final` rows count, and only for units whose attribution status is in `counted_statuses` | — | `test_the_invented_studys_rollup` (p-003 "doubtful") |
| 406 | A unit whose passage-attribute value is listed in `unit.exclude_from_rollup` is left out | — | `test_a_counted_unit_and_an_excluded_one` |
| 407-408 | NA codes and the missing value are skipped; "an author whose remaining codes are all skipped gets `missing`" | — | `test_a_collective_author_keeps_its_kind_and_na_gives_the_missing_value`, `test_nothing_left_gives_the_missing_value` |
| 409-410 | "an author all of whose units were left out by status or exclusion is not in the rollup. The tool reports how many authors that is" | printed: `N author(s) left out` | `test_the_invented_studys_rollup`, `test_a_counted_unit_and_an_excluded_one` |
| 411, 418 | An outcome whose source is an evidence attribute, or whose rollup is `none`, does not appear | — | `test_the_rollup_columns_follow_d5` |
| 412 | `single-code`: the one code all remaining units share; more than one is an error (the rollup is refused, nothing written) | `rollup-conflict` | `test_single_code_and_its_conflict`, `test_a_single_code_conflict_refuses_the_rollup` |
| 413 | `mixed-if-conflict`: the shared code, or the reserved code `mixed` | — | `test_mixed_if_conflict` |
| 414 | `max-order`: the code with the highest `order` | — | `test_max_order_takes_the_highest_order` |
| 415-417 | `any-present`: the `present_code` if any remaining unit has it; otherwise the lowest `order` (ordinal) or the code declared first in `levels` (nominal) | — | `test_any_present` |
| 171, 414, 416 (proposal 6) | Section 3 does not make each level's `order` unique (line 171): two distinct remaining codes at the deciding `order` (`max-order`, or `any-present` on an ordinal outcome) are an error naming the outcome, the cell and the codes, and the rollup is refused | `rollup-conflict` | `test_a_tie_on_the_deciding_order_is_an_error`, `test_a_tie_refuses_the_rollup_and_names_the_cell` |
| 419 | "results are split by each key in `unit.rollup_by`": one row per author and combination of values | — | `test_the_invented_studys_rollup` |
| 420-421; 587-589; O1 | `<outcome>__types` beside each outcome where `unit.rollup_types` names a passage attribute: the values "among the units behind it" (line 421). The units behind a cell are decided by 4.7 (lines 587-589): the attribution rows of that author and those `rollup_by` values that have no value listed in `unit.exclude_from_rollup` and whose status is in `counted_statuses`, here those with a final row for the outcome (every one, under D4). NA- and missing-coded units stay included: line 407 skips their codes for the rule only. Each distinct value once, `;`-joined, in the attribute's declared level order (O1) | — | `test_the_invented_studys_rollup`, `test_types_follow_the_declared_order_of_the_attribute`, `test_types_value_puts_undeclared_values_last`, `test_a_collective_author_keeps_its_kind_and_na_gives_the_missing_value` |
| 422 | A collective author keeps its `author_kind` | — | `test_a_collective_author_keeps_its_kind_and_na_gives_the_missing_value` |
| 566-568; D5, O3 | The input must be a current `survey-finalize` output: its record exists and matches (lines 566-567). In a draft study a record that does not match is reported and the stage runs (line 568) | — | `test_a_rollup_needs_a_current_final_file`, `test_outside_a_draft_a_stale_record_refuses_the_rollup`, `test_a_draft_rollup_with_a_stale_record_but_matching_bytes_runs_and_reports` |
| 565; O3 (tightening 1) | The final file's bytes must be what `survey-finalize` gives from the study's inputs, in every status, draft included: the record holds no hash of its output (line 565), so a hand edit would otherwise pass | — | `test_a_hand_edited_final_file_is_refused_by_the_rollup`, `test_differing_bytes_refuse_the_rollup_in_every_status[...]` |
| 562 (tightening 3) | The output or its record may not be the final file or its record; the final file's record path has no link on its way | — | `test_a_rollup_whose_record_would_be_the_final_file_is_refused`, `test_a_linked_record_of_the_final_file_is_refused` |
| 1.2 | Every file the rollup reads is hashed before the final codes are worked out again and guarded until the write | — | `test_a_rollup_input_changed_before_the_write_refuses[...]` |
| D5 | The final file and the output lie inside the study's folder | — | `test_a_rollup_with_a_final_file_outside_the_study_is_refused` |
| D5 | Columns in D5's order | — | `test_the_rollup_columns_follow_d5` |
| 1.5 | Rows in code-point order of `person_id`, then of the `rollup_by` values in the order `rollup_by` names them; "unchanged" on a second run | — | `test_the_rollup_is_deterministic_and_unchanged_twice` |
| 563; D6 | The record: every file read, with its hash: the specification, the final file and its record, and every file finalising lists (the re-derivation reads them all, and no receipt); gate S5 only; the legacy-exception count the evidence was read with (the rollup rests on the evidence through the final codes, 4.1 line 366) | — | `test_the_invented_studys_rollup`, `test_the_records_inputs_are_the_files_read[rollup]` |

## Commands (section 7, lines 933-934)

| Line | What | Test |
|---|---|---|
| 933-934 | `survey-finalize` and `survey-rollup` bridge commands, refusing `--root` | `test_the_bridge_runs_both_commands_and_refuses_root` |
| — | Usage errors exit 2 | `test_usage_errors` |
| — | Display only: the cap on printed findings (at most 1000 per file) groups by the exact file a finding carries, not by splitting its location | `test_the_cap_groups_findings_by_their_exact_file` |

## Where the contract's rule text and the brief's summary were compared

The rules were taken from 4.2 (lines 403-422) as written: `single-code`, `mixed-if-conflict`, `max-order`,
`any-present` (with the ordinal and nominal fallbacks of lines 416-417) and `none`. The brief's summary agreed with the
text; nothing differed.

## Not implemented

| Section, line | What | Why |
|---|---|---|
| 4.7 | The frame | Step D |
| 4.2, 403 | A rollup in an author study | The text rolls "passage or work codes" to their author; refused |

## Proposed contract changes

1. **`<outcome>__types`: how the values are written** (operator decision O1). The contract decides which units: "the
   values of that attribute among the units behind it" (4.2, lines 420-421), and the units behind a cell are the
   rollup's: counted, not excluded, of that author and those `rollup_by` values (4.7, lines 587-589). NA- and
   missing-coded units are among them; line 407 skips their codes only when the rule is applied. The text does not say
   how the values are written. O1: each distinct value once, joined with `;`, in the order the attribute declares its
   levels. A value that is not among them comes after, in code-point order.
2. **Each operator decision above (D2-D6, O1-O3)** is a proposal for a later contract version.
3. **A later recode that leaves an adjudication behind.** The reference tool's users met this. When a later ruling
   recodes a pass so that the passes agree, the earlier adjudication becomes an error (`adjudication-agreed`, part 1).
   Once it is removed, the final row shows `agreed` with no pointer to the ruling. Proposed for a later version: a way
   to record why a pass was recoded (a ruling id in the pass's `note`, or a column), carried into the final row.
4. **"Evidence differed"** compares the two passes' `evidence_ids` as sets of ids. The same ids in another order, or one
   id repeated, do not differ.
5. **Files the output rests on: no longer needed.** An earlier version of this table stopped on the fetch receipts,
   which the row checks opened and the records left out. Both commands now skip the 5.4 citation check and open no
   receipt, so the records list exactly the files read and line 563 is met as written.
6. **Ties at the deciding `order`.** Section 3 does not require each level's `order` to be unique (line 171). Where two
   distinct remaining codes share the highest (`max-order`) or lowest (`any-present`, ordinal) order, the tool reports
   an error naming the outcome, the cell and the codes, and refuses the rollup. It does not take whichever code comes
   first. Proposed: make `order` unique within an outcome (a specification error), or name a tie-break.

## The gates entry (4.6) and what it stands for: STOPPED

Computing gate S5's entry (`gate_entries`) reads files that are not in `inputs`. It reads the files the manifest
lists: the specification, which is in `inputs`, and the files S5 covers, here the codebook. It also reads the study's
sign-off folder: the stored manifest (the request), the log, the verify keys and the approvers. What 4.6 says:

- Line 563: "`inputs` lists the files the tool actually read, the specification among them, each as it was read. A
  plug-in file is listed under `plugins` only." The one exception it names is the plug-in file.
- Line 556: a `gates` entry holds `state`, `mode`, `enforce` and `manifest_sha256`. Lines 569-570: "`gates` lists
  each gate the stage depends on."
- Lines 803-811: the manifest lists the specification and the gate's `covers` with their hashes, and "the gate's
  identity is the SHA-256 of the manifest file's bytes". So `manifest_sha256` does stand for the content of every
  covered file.
- Lines 815-818: the state (`CLEARED`, `UNCLEARED`, `UNAVAILABLE`) is what the sign-off folder's files give. The
  entry's `state` reports them; it does not hash them.

As written, line 563 lets nothing but a plug-in stand outside `inputs`. It does not say that a `gates` entry stands
for the reads made to compute it, even though `manifest_sha256` does cover the covered files' content in fact.
Listing the codebook and the sign-off files in `inputs` would need no new field, but it would make the final codes
stale whenever a sign-off is recorded or a codebook changes. **This needs a ruling; nothing was changed.** The two
readings are:

- (a) Line 563 covers the files the output's content is computed from. The gate's reads are met by `gates`: the
  covered files through `manifest_sha256`, and the sign-off folder through `state`. This is what all three records do
  now. Propose saying so in a later version.
- (b) Line 563 as written: list every covered file and every sign-off file in `inputs` too.

The three records are consistent under reading (a):

- The registry record (part 2a, `survey-registry`) has `gates` `{}`. Its stage depends on no gate (6.1), it calls no
  gate code, and its `inputs` are exactly the files it reads: the specification, the evidence file, the attribution
  file, the overrides file and the exceptions file.
- The final codes and the rollup records list S5. Their `inputs` are exactly the files they read apart from S5's
  reads: `test_the_records_inputs_are_the_files_read` checks this, leaving out the ledger folder and the covered
  codebook.

## Tightenings

1. The rollup refuses a final file whose bytes are not what `survey-finalize` gives from the study's inputs, in every
   status, draft included (O3; the record cannot see its output).
2. D4 (a unit with no pass refuses) is stricter than the reference tool, by the operator's decision.
3. An output named as a record (ending `.provenance.json`) is refused. So is a file at a record's path that is not
   this output's 4.6 record, an output or record path that is the rollup's own final file or its record, and a link on
   a record's path (@security S1, S3).
4. A tie at the deciding `order` is an error (proposal 6).
5. A study's own `final` row for an agreed unit, made by hand and carrying the coder's name (or pass A's note), is
   refused by finalising (`final-differs`), while `survey-validate` accepts it. 4.2 line 384 allows a `final` row
   wherever both passes exist, and line 397 says only "the final row is theirs". This follows from D3 (a derived
   agreed row has coder `agreed`) and O2 (an existing final row must equal the derived row).
