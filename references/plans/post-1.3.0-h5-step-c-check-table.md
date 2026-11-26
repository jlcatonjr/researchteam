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
| 4.1, 319; 4.2, 381-382; 4.1, 339 (close to decided) | The unit is an attribution unit (in an author study, a registry person) and `person_id` its attributed author (the unit itself in an author study): a coded unit is a unit of the attribution file (4.1, line 319), whose evidence "belongs to the unit's attributed author" (4.2, lines 381-382), as 4.1's `unit-person` rule judges an evidence row (line 339) | `codes-unit`, `codes-unit-person` | `[codes-unit]`, `[codes-unit-person]`, `test_the_unit_checks_in_an_author_study[...]`, `test_an_author_study_adjudication_unit_must_be_a_person` |
| 4.1, 289; 4.2, 379 (implied) | `basis` is `own` or `reported`: 4.1 gives the two bases (line 289), and 4.2 speaks of `reported` with the same meaning (line 379) | `codes-basis` | `[codes-basis]`, `test_a_basis_other_than_own_or_reported_is_refused` |
| 3, 133; 4.2, 392 (tightening 3) | A row naming a coded outcome that has a codes file of its own, in another outcome's file: each outcome names its own `codes_file` (section 3, line 133), as its adjudications are "the one the outcome's `source.adjudications` names" (4.2, line 391-392) | `codes-outcome` | `test_a_codes_file_shared_by_two_outcomes_keeps_each_rows_outcome` |
| (tightening 4) | Identifier cells (`unit_id`, `person_id`, `outcome`, `code`, `pass`, `coder`, `basis`, `evidence_ids`) hold none of the shared unsafe characters (`survey_core.UNSAFE_CATEGORIES`) | `codes-value` | `[codes-value]` |
| 3, 217-219 | The codes file must exist outside a draft; the adjudications file may be absent | step A's `file-missing` | `test_without_adjudications_the_file_may_be_absent` |
| (proposal 6) | At most `MAX_FINDINGS_PER_FILE` (1000) findings are printed per file, then one saying how many more were not shown; the run fails all the same (every row file: evidence, attribution, codes, adjudications, overrides, tables) | `findings-suppressed` (toolkit) | `test_findings_are_capped_per_file` |

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
| 400-401; operator D1 | Raw agreement, Cohen's κ and Gwet's AC1 per outcome "with the number of units each rests on", by the operator's standard definitions (below): over the n units with both passes; every code its own category | `<outcome>: n=<n> raw=<d.ddd> kappa=<d.ddd\|undefined> AC1=<d.ddd\|undefined>; m unit(s) with one pass only` | `test_agreement_on_the_invented_study`, `test_agreement_by_hand` |
| operator D1 | κ and AC1 on hand-worked examples: κ and AC1 differ visibly; NA codes and the missing value as categories; q from the codebook against "codes that occur"; every undefined case; rounding at a half | — | `test_kappa_and_ac1_differ_visibly`, `test_na_codes_and_the_missing_value_are_categories`, `test_ac1_uses_the_codes_the_codebook_allows_not_those_that_occur`, `test_the_undefined_cases`, `test_rounding_at_half_is_to_even` |
| 1.5 | The output is byte-identical across runs (exact fractions; the rounding does not depend on the platform) | — | `test_agreement_output_is_byte_identical_across_runs` |
| 4.7, 603 (the convention) | Outcomes are reported in the order the study declares them, those without rows last in declared order | — | `test_agreement_lists_outcomes_in_declared_order` |
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
- Raw agreement, κ and AC1 per outcome with the number of units each rests on (lines 400-401); how they are computed
  is the operator's decision D1.
- `survey-agreement` is not a gated stage (6.1, lines 786-791).

## Not implemented

| Section, line | What | Why |
|---|---|---|
| 4.2, 397-400 | Finalising (`survey-finalize`) | Part 2 of step C |
| 4.2, 403-422 | The rollup (`survey-rollup`) | Part 2 of step C |
| 8, 956 | That passes are blind | A property of packets (step G) and grants (step H) |

## Operator decisions (2026-11-25)

The operator ruled on every open point (picker, 2026-11-25), starting from the first integrating project's reference
tool. These are decided for the toolkit, and each is also a proposal for a later contract version, since the
contract's text does not contain it.

**D1, "standard definitions" (agreement, 4.2 line 400).** Per coded outcome, over the units with both a pass-A and a
pass-B row (a unit with one pass is left out of all three statistics; n is the number of such units):

- every code is its own category, NA codes and the missing value included (two passes coding the missing value
  agree);
- raw agreement p_a = (units with identical codes) / n;
- Cohen's κ, unweighted also for ordered levels: p_e = Σ_k p_A(k)·p_B(k) over the codes, with p_A(k), p_B(k) each
  pass's proportions; κ = (p_a − p_e) / (1 − p_e);
- Gwet's AC1: q = the number of codes the specification allows for the outcome (its level codes, NA codes and missing
  value, as declared; not the number that occur); π_k = (p_A(k) + p_B(k)) / 2; p_e1 = (1/(q − 1))·Σ_k π_k(1 − π_k)
  over all q allowed codes; AC1 = (p_a − p_e1) / (1 − p_e1);
- `undefined`, never 1.0 or NaN: n = 0 (all three); 1 − p_e = 0 (κ); q ≤ 1 or 1 − p_e1 = 0 (AC1);
- computed exactly (`fractions.Fraction`) and printed to three decimals, half to even, so the output is identical on
  every platform and Python version (rule 1.5);
- one line per outcome in declared order, then the units with one pass only.

**Where this differs from the reference tool** (for step D's comparison): AC1's q is the number of codes the
specification allows, not the number that occur; and the undefined cases print `undefined`, where the reference tool
gives a number.

**Part 2 (finalising and the rollup).** D2: final codes go to a separate file named on the command line; D3: an agreed
unit's final row is pass A's with `coder` and `note` `agreed` (`agreed; evidence differed` where the evidence ids
differ); D4: a unit with no pass at all refuses finalising (stricter than the reference tool); D5: the rollup's
columns and inputs; D6: both records list gate S5 only. Recorded in full in part 2's check table.

## Conditions for part 2 (from @security, if final rows go into the codes file)

Not implemented; kept here for part 2.

1. `check_output_target` allows exactly that outcome's declared codes file as its own pointer and refuses everything
   else; a codes file another outcome shares is refused unless every outcome naming it is finalised in the same run.
2. The file is **rebuilt, never appended**: the existing A and B rows are kept byte for byte.
3. The old file is read again and its hash compared just before writing; refused if it changed.
4. The new bytes are read back and the code checks run on them; refused unless there are no findings, every A and B
   row is unchanged, and every new row is `final` and copies an adjudication or agreed A and B rows.
5. Refused when any `final` row already exists, unless the run would produce identical output.
6. Written with the CSV writer's minimal quoting.
7. Tests: a linked codes file, a file swapped between read and write, a shared codes file.

## Proposed contract changes

1. *(Decided by the operator, D1: κ and AC1 by the standard definitions; a proposal for a later contract version.)*
2. **An adjudication for a unit with neither pass** is refused (`adjudication-no-pass`): needs a ruling (see "Waiting
   on the operator").
3. *(Decided by the operator, D1: every code is its own category, NA codes and the missing value included.)*
4. **The `level` column of a codes row** is carried and not checked: the text names it (line 370) and says nothing of
   it.
5. **The same coder for both passes** is not checked: the text requires blind passes (section 8, line 956), not
   different coders.
6. **At most 1000 findings printed per file**, then one line saying how many more (`findings-suppressed`).

## Tightenings (stricter than the text)

1. *(Now close to decided: lines 319, 381-382 and 339; see the codes table.)*
2. *(Implied by lines 289 and 379; see the codes table.)*
3. A row in another coded outcome's codes file is refused (each outcome names its own files, lines 133 and 392).
4. Identifier cells hold none of the shared unsafe characters.
5. A missing-pass note on a unit that has both passes is refused.
