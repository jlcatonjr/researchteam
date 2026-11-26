# H5 step C part 2: check table (survey toolkit against `docs/survey-toolkit.md`, version 1)

Plan: `post-1.3.0-h5-survey-tools-a-d.plan.md`, step C. This pull request is **part 2** of step C: `survey-finalize`
(4.2, lines 397-400; section 7, line 933) and `survey-rollup` (4.2, lines 403-422; section 7, line 934), built on part
1b (pull request #270). Line numbers are those of `docs/survey-toolkit.md` at `251b1f0`. Tests are in
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

## Finalising (4.2, lines 397-400; D2-D4, D6)

| Line | What is checked or written | Id | Test |
|---|---|---|---|
| 397 | "Where passes A and B agree, the final row is theirs": pass A's row, marked as D3 says | — | `test_the_invented_studys_final_codes`, `test_an_agreed_unit_with_the_same_evidence_says_agreed` |
| 397-399 | "Where they disagree, or where one pass is missing, the final row is the adjudication's, with the adjudication's own coder, basis, evidence and note" | — | `test_the_invented_studys_final_codes` |
| 399 | "Without one, no final row is written; the tool lists the units and exits non-zero" | `final-no-adjudication` | `test_a_disagreement_without_an_adjudication_refuses`, `test_a_unit_with_one_pass_and_no_adjudication_refuses` |
| 400 | "A single pass never becomes final on its own" | `final-no-adjudication` | `test_a_unit_with_one_pass_and_no_adjudication_refuses` |
| D4 (a tightening against the reference tool) | A unit with no pass refuses; every such unit listed; in an author study the units are the registry's persons | `final-no-pass` | `test_a_unit_with_no_pass_refuses_and_every_one_is_listed`, `test_finalising_in_an_author_study_uses_the_registrys_persons` |
| 1.2 | Every row and code file passes its checks first | the files' ids | `test_a_code_file_error_refuses` |
| D2 | A final row in the passes file refuses: final codes go to their own file | `final-in-codes` | `test_a_final_row_in_the_passes_file_refuses` |
| D2 | Where the output may go: inside the study's folder, not a declared or covered file, not in the ledger, no link | the target's refusals | `test_where_the_final_codes_may_not_go[...]` (seven cases), `test_a_linked_output_folder_is_refused` |
| D2 | An existing output: identical bytes are "unchanged"; different ones refused | — | `test_finalising_is_deterministic_and_unchanged_twice`, `test_an_existing_different_output_is_refused` |
| 1.2 | A refusal at either late check, and an input that changed since it was read (the guards), change nothing | — | `test_a_refusal_at_either_late_check_changes_nothing[...]`, `test_an_input_changed_before_the_write_refuses[...]` |
| 1.5 | The same bytes in two repositories; rows in the outcomes' declared order, then code-point order of `unit_id` | — | `test_finalising_is_deterministic_and_unchanged_twice` |
| 4.6; D6 | The record: 4.6's shape, the inputs read (the specification, each coded outcome's codes and adjudications files, the evidence file and its exceptions file, the attribution file or the registry) with their hashes, gate S5 only with its state and mode, the legacy exceptions | — | `test_the_final_codes_record` |

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
| 419 | "results are split by each key in `unit.rollup_by`": one row per author and combination of values | — | `test_the_invented_studys_rollup` |
| 420-421 | `<outcome>__types` beside each outcome where `unit.rollup_types` names a passage attribute (proposal 1 on which units and how joined) | — | `test_the_invented_studys_rollup` |
| 422 | A collective author keeps its `author_kind` | — | `test_a_collective_author_keeps_its_kind_and_na_gives_the_missing_value` |
| D5 | The input must be a current `survey-finalize` output: its record exists and matches (4.6, lines 566-567) | — | `test_a_rollup_needs_a_current_final_file` |
| (tightening 1) | The final file's bytes must be what `survey-finalize` gives from the study's inputs: the record holds no hash of its output (4.6, line 565), so a hand edit would otherwise pass | — | `test_a_rollup_needs_a_current_final_file`, `test_a_hand_edited_final_file_is_refused_by_the_rollup` |
| D5 | The final file and the output lie inside the study's folder | — | `test_a_rollup_with_a_final_file_outside_the_study_is_refused` |
| D5 | Columns in D5's order | — | `test_the_rollup_columns_follow_d5` |
| 1.5 | Rows in code-point order of `person_id`, then of the `rollup_by` values in the order `rollup_by` names them; "unchanged" on a second run | — | `test_the_rollup_is_deterministic_and_unchanged_twice` |
| 4.6; D6 | The record: the specification, the final file and the attribution file with their hashes; gate S5 only; the final codes' legacy-exception count (the rollup rests on the evidence through them, 4.1 line 366) | — | `test_the_invented_studys_rollup` |

## Commands (section 7, lines 933-934)

| Line | What | Test |
|---|---|---|
| 933-934 | `survey-finalize` and `survey-rollup` bridge commands, refusing `--root` | `test_the_bridge_runs_both_commands_and_refuses_root` |
| — | Usage errors exit 2 | `test_usage_errors` |

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

1. **`<outcome>__types`: which units, how joined** (needs the operator's confirmation). The tool reports the sorted
   unique values of the `unit.rollup_types` attribute over the *counted* units behind the cell: the units of that
   author and those `rollup_by` values whose attribution status is counted and which no `exclude_from_rollup` value
   leaves out, that have a final row for the outcome. Units coded with an NA code or the missing value **are**
   included: they are counted units behind the cell (lines 405-406), and only the rule skips their codes (line 407).
   Values are joined with `;`. The contract decides that the column reports "the values of that attribute among the
   units behind it" (lines 420-421). It does not say whether units left out by status or exclusion, or units whose
   codes the rule skips, are "behind it", nor how the values are written; this is the narrowest reading consistent
   with the reference tool as described. Under D4 every counted unit has a final row, so the set is all counted,
   non-excluded units of the cell.
2. **Each operator decision above (D2-D6)** is a proposal for a later contract version.
3. **A later recode that leaves an adjudication behind.** The reference tool's users met this: when a later ruling
   recodes a pass so that the passes agree, the earlier adjudication becomes an error (`adjudication-agreed`, part
   1), and once it is removed the final row shows `agreed` with no pointer to the ruling. Propose for a later version: a
   way to record why a pass was recoded (a ruling id in the pass's `note`, or a column), carried into the final row.
4. **"Evidence differed"** compares the two passes' `evidence_ids` as sets of ids: the same ids in another order do not
   differ.

## Tightenings

1. The rollup refuses a final file whose bytes are not what `survey-finalize` gives from the study's inputs (the
   record cannot see its output).
2. D4 (a unit with no pass refuses) is stricter than the reference tool, by the operator's decision.
