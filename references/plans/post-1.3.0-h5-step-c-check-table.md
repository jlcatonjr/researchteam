# H5 step C (part 1): check table (survey toolkit against `docs/survey-toolkit.md`, version 1)

Plan: `post-1.3.0-h5-survey-tools-a-d.plan.md`, step C. This pull request is **part 1** of step C: the checks on the
codes and adjudications files (4.2, lines 368-395), and `survey-agreement` (lines 400-401; section 7, line 932).
**Part 2** is finalising (`survey-finalize`, lines 397-400) and the rollup (`survey-rollup`, lines 403-422), with
their outputs' provenance records (4.6). Line numbers are those of `docs/survey-toolkit.md` at `251b1f0`. Tests are in
`tests/test_survey_codes.py` unless another file is named. Ids are the toolkit's own (4.2 gives none).

**Gates.** `survey-agreement` is not a gated stage: 6.1 (lines 786-791) names enumeration (S0), "building coding
packets" (S5, line 789), analysis (S6) and the report (S8); agreement reads finished passes and writes nothing, so it
has no output to record a gate in (4.6 concerns outputs). The gate reading for finalising and the rollup is part 2's.

**Blind passes.** "Blind" (section 8, line 956: a coder works "from a blind packet" and never "sees the other pass")
is a property of the packets (step G) and of the agents' grants (step H), not of these files; nothing here checks it.

## Codes rows (4.2, lines 370-386)

| Line | What is checked | Id | Test |
|---|---|---|---|
| 370 | Columns `unit_id, person_id, outcome, code, pass, coder, basis, reporter, evidence_ids, level, note`; strict CSV | `codes-columns` | `test_codes_columns` |
| 372 | `pass` is `A`, `B` or `final` | `codes-pass` | `test_each_codes_check[codes-pass]` |
| 377 | An outcome the specification does not declare with source `codes` | `codes-outcome` | `[codes-outcome]` |
| 377; 372-373 | A code outside the allowed set: the outcome's level codes, NA codes and `missing` value | `codes-code` | `[codes-code]` |
| 378 | A code other than `missing` without `evidence_ids` or without a `basis`; the missing value needs neither | `codes-evidence`, `codes-basis` | `[codes-evidence]`, `[codes-basis]`, `test_the_missing_value_needs_no_evidence_or_basis` |
| 378-379 | `reported` without a `reporter` | `codes-reporter` | `[codes-reporter]` |
| 380 | An evidence id that does not exist | `codes-evidence-unknown` | `[codes-evidence-unknown]` |
| 380-382 | An evidence id that belongs to another person; in a passage or work study "a unit's evidence belongs to the unit's attributed author", and a person-level row to its person | `codes-evidence-person` | `[codes-evidence-person]`, `test_a_person_level_evidence_row_belongs_to_its_person` |
| 383 | Two rows for the same unit, outcome and pass | `codes-duplicate` | `[codes-duplicate]` |
| 384-386 | A `final` row for a unit that lacks an `A` or a `B` row, unless it comes from an adjudication whose note begins `missing pass: A, ` or `missing pass: B, ` (naming the pass that is missing) followed by the reason; "comes from" read as: the final row carries the adjudication's code, coder, basis, reporter, evidence and note (lines 397-399) | `codes-final-unpaired` | `test_a_final_row_needs_both_passes`, `test_a_final_row_from_a_missing_pass_adjudication_is_accepted`, `test_a_final_row_that_does_not_come_from_the_adjudication_is_refused[...]` |
| 1.3, 31-32 | Every code row has a coder: "a link, a basis and a code are always written by a named agent or person" | `codes-coder` | `[codes-coder]` |
| (tightening 1) | The unit is an attribution unit (in an author study, a registry person) and `person_id` its attributed author (the unit itself in an author study) | `codes-unit`, `codes-unit-person` | `[codes-unit]`, `[codes-unit-person]` |
| (tightening 2) | `basis` is `own` or `reported` (4.1's two bases; 4.2 says only "without a `basis`") | `codes-basis` | `[codes-basis]` |
| (tightening 3) | A row naming a coded outcome that has a codes file of its own, in another outcome's file | `codes-outcome` | `test_a_codes_file_shared_by_two_outcomes_keeps_each_rows_outcome` |
| (tightening 4) | Identifier cells (`unit_id`, `person_id`, `outcome`, `code`, `pass`, `coder`, `basis`, `evidence_ids`) hold none of the shared unsafe characters (`survey_core.UNSAFE_CATEGORIES`) | `codes-value` | `[codes-value]` |
| 3, 217-219 | The codes file must exist outside a draft; the adjudications file may be absent | step A's `file-missing` | `test_without_adjudications_the_file_may_be_absent` |

## Adjudications (4.2, lines 388-395)

| Line | What is checked | Id | Test |
|---|---|---|---|
| 390 | Columns `unit_id, outcome, code, coder, basis, reporter, evidence_ids, note`; strict CSV | `adjudication-columns` | `test_each_adjudication_check[adjudication-columns]` |
| 391 | The file is the one the outcome's `source.adjudications` names: its rows name that outcome | `adjudication-outcome` | `[adjudication-outcome]` |
| 392 | Checked like codes rows (code, evidence, basis, reporter, evidence belonging, unit) | `adjudication-code`, `adjudication-evidence-person`, `adjudication-unit`, … | `[adjudication-code]`, `[adjudication-evidence-person]`, `[adjudication-unit]` |
| 392 | `coder` and `note` are required | `adjudication-coder`, `adjudication-note` | `[adjudication-coder]`, `[adjudication-note]` |
| 383, 392 | "Checked like codes rows": one adjudication per unit and outcome | `adjudication-duplicate` | `[adjudication-duplicate]` |
| 393-394 | An adjudication for a unit and outcome on which A and B agree: "an agreed code is not changed" | `adjudication-agreed` | `[adjudication-agreed]` |
| 394-395 | Where a pass is missing, the note begins `missing pass: A, ` or `missing pass: B, ` (the missing one), followed by the reason | `adjudication-missing-pass` | `[adjudication-missing-pass]`, `test_a_missing_pass_note_must_name_the_pass_and_a_reason[...]` |
| (tightening 5) | A note that says a pass is missing on a unit that has both | `adjudication-missing-pass` | `test_a_missing_pass_note_on_a_unit_with_both_passes_is_refused` |
| (proposal 2) | An adjudication for a unit with neither pass | `adjudication-no-pass` | `[adjudication-no-pass]` |
| 7, 925 | `survey-validate` checks both files | the ids above | `test_each_codes_check[...]` |

## Agreement (4.2, lines 400-401; section 7, line 932)

| Line | What is reported | Output | Test |
|---|---|---|---|
| 400-401 | Raw agreement per outcome "with the number of units [it] rests on": of the units with both an A and a B row, those with the same code in both, as "k of n"; every code counts as itself (proposal 3); the units with one pass only are named apart | `<outcome>: raw agreement k of n unit(s) with both passes; m unit(s) with one pass only` | `test_agreement_on_the_invented_study`, `test_agreement_by_hand` |
| 400 | Cohen's κ and Gwet's AC1 | **not computed** (proposal 1): printed as such | `test_agreement_on_the_invented_study` |
| 1.2 | Refused when the study, a row file or a code file has an error; refused without a coded outcome | `REFUSED` | `test_agreement_refuses_on_a_code_error_and_writes_nothing`, `test_agreement_refuses_without_a_coded_outcome` |
| 1.5 | The same output twice; nothing written | — | `test_agreement_is_deterministic`, `test_agreement_on_the_invented_study` |
| 7, 932 | The bridge command, refusing `--root` | exit 2 | `test_the_bridge_runs_survey_agreement_and_refuses_root` |

## Step B follow-ups (in this pull request)

| Item | What changed | Test (in `tests/test_survey_merge.py`) |
|---|---|---|
| (a) | Part 2b proposal 8: "TAB and line breaks included; a plain space is accepted"; NEL (U+0085) refused even in a text column | `test_nel_is_refused_even_in_a_text_column`, `test_a_plain_space_is_accepted_everywhere_but_where_a_check_refuses_it` |
| (b) | The batch's refusal message uses the finding's wording | `test_nel_is_refused_even_in_a_text_column` |
| (c) | A CR LF inside a text cell, merged into a CR LF file | `test_a_crlf_text_cell_merges_into_a_crlf_file` |
| (d) | No exceptions draft for an id `safe()` would print escaped (private use included; the stricter choice) | `test_no_exceptions_draft_for_an_id_with_a_private_use_character` |

## Decided by the text

- The columns of codes rows (line 370) and adjudications (line 390); `pass` is `A`, `B` or `final` (line 372).
- The allowed codes: level codes, NA codes, the `missing` value (lines 372-373).
- Every error of lines 377-386, and that adjudications are "checked like codes rows" with `coder` and `note` required
  and none for an agreed unit (lines 392-394), and the missing-pass note (lines 394-395).
- A coder on every code row (rule 1.3, lines 31-32).
- Raw agreement per outcome with the number of units it rests on (lines 400-401).
- `survey-agreement` is not a gated stage (6.1, lines 786-791).

## Not implemented

| Section, line | What | Why |
|---|---|---|
| 4.2, 400 | Cohen's κ and Gwet's AC1 | The text names them without a formula; proposal 1 |
| 4.2, 397-400 | Finalising (`survey-finalize`) | Part 2 of step C |
| 4.2, 403-422 | The rollup (`survey-rollup`) | Part 2 of step C |
| 8, 956 | That passes are blind | A property of packets (step G) and grants (step H) |

## Proposed contract changes

1. **Cohen's κ and Gwet's AC1**: the contract names them without a formula, so they are not computed. Proposed
   formulas, for two coders over the n units with both passes, with q categories (the outcome's allowed codes),
   p_o the raw agreement k/n, and p_A(c), p_B(c) the share of units each pass gives code c:
   κ = (p_o − p_e) / (1 − p_e), with p_e = Σ_c p_A(c)·p_B(c) (Cohen, 1960);
   AC1 = (p_o − p_e) / (1 − p_e), with p_e = (1 / (q − 1)) · Σ_c π_c(1 − π_c) and π_c = (p_A(c) + p_B(c)) / 2
   (Gwet, 2008). Also to settle: whether NA codes and the missing value count as categories, q (all allowed codes or
   those used), the value when 1 − p_e = 0, and rounding.
2. **An adjudication for a unit with neither pass** is refused (`adjudication-no-pass`): lines 397-398 speak of a
   unit where "one pass is missing".
3. **Every code counts as itself in raw agreement**, NA codes and the missing value included: the text does not say
   whether they count.
4. **The `level` column of a codes row** is carried and not checked: the text names it (line 370) and says nothing of
   it.
5. **The same coder for both passes** is not checked: section 8 (line 956) has passes A and B by `@position-coder` A
   and B, but no row rule says the coders differ.

## Tightenings (stricter than the text)

1. The unit is an attribution unit (a registry person in an author study), and a codes row's `person_id` is its
   author.
2. `basis` is `own` or `reported`.
3. A row in another coded outcome's codes file is refused.
4. Identifier cells hold none of the shared unsafe characters.
5. A missing-pass note on a unit that has both passes is refused.
