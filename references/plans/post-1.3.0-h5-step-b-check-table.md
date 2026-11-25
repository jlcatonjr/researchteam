# H5 step B (part 1): check table (survey toolkit against `docs/survey-toolkit.md`, version 1)

Plan: `post-1.3.0-h5-survey-tools-a-d.plan.md`, step B. This pull request is **part 1** of step B: the row files.
It checks evidence (4.1) with the contract's rule ids and legacy exceptions, attribution (4.3), bucket tables and
years (4.8), the forbidden vocabulary (5.3), the form and presence of a fetch-receipt citation (5.4, section 3 line
223), and `survey-validate`'s "every row file present" (section 7). **Part 2** is the identity registry (candidates,
overrides, build), the batch merge (`survey-rows`) and `survey-registry`. The reason for the split: the merge renews
the registry's *provenance record* (4.4, lines 515-523), and that record is 4.6, which the plan gives to step C. Part 2
either brings 4.6 forward or waits for it; that choice is the operator's.

Line numbers are those of `docs/survey-toolkit.md` at `507cc94`. Tests are in `tests/test_survey_rows.py` (rows) unless
another file is named; `[...]` is one parametrized case. Where the contract gives an id, the id is the contract's
(4.1's rule ids); every other id is the toolkit's own and is marked so.

**Gates.** Neither part of step B is a gated stage: 6.1 (lines 786-791) names enumeration (S0), coding packets (S5),
analysis (S6) and the report (S8). `survey-validate` is not a stage, and 4.4 makes the merge depend on the registry
being built, not on a gate. No step-B code calls `stage_decision`.

## Row files (section 4)

| Section, line | What is checked | Error id | Test |
|---|---|---|---|
| 4, 275 | CSV, UTF-8 | the file's own id (`columns`, `attribution-columns`, …) | `test_an_unreadable_or_headless_row_file[...]` |
| 4, 275-276 | "exactly the columns listed, in this order. A missing or extra column is an error" | `columns` (evidence) and each file's own id | `test_columns_rule`, `test_attribution_columns_follow_the_passage_attributes`, `test_bucket_table_errors[...table-columns]`, `test_the_exceptions_file_has_exactly_two_columns`, `test_registry_shape` |
| 4, 276 | A row whose width differs from the header's: decided by "A missing or extra column is an error" | the file's columns id | `test_a_row_of_the_wrong_width_and_a_blank_line_are_errors` |
| (proposal 1) | A blank line | the file's columns id | `test_a_row_of_the_wrong_width_and_a_blank_line_are_errors` |
| 4, 276 | "An empty cell means "not given"; a tool never treats it as a value" | — (an empty value never fires a bucket row; an empty locator cites nothing) | `test_match_first_takes_the_first_row_that_fires`, `test_a_locus_locator_cites_no_receipt` |
| 1.6, 40-43 | A row file is opened at its resolved place, as step A opens a covered file: a link that resolves inside the repository is followed; one that leaves it is `path-outside` | step A's `path-outside` | `test_a_row_file_reached_through_a_link_inside_the_repository_is_read`, `test_a_row_file_linked_outside_the_repository_is_refused` |
| (proposal 2) | Only a regular file is read (a FIFO or device is not opened); at most `MAX_CSV_BYTES` (64 MiB), streamed, never held whole | the file's columns id | `test_a_row_file_that_is_a_fifo_is_not_opened`, `test_a_row_file_over_the_cap_is_not_read`, `test_the_row_file_cap_is_64_mib` |
| (proposal 16) | A cell holding a NUL character | `cell-nul` (toolkit) | `test_a_nul_in_a_cell_is_a_finding` |
| 4.1 (line numbers) | A finding names the line a row starts on, so a quoted cell over several lines does not shift later lines | — | `test_line_numbers_follow_quoted_multi_line_cells` |
| 1.2 (output) | No value from a file (a header cell, a row value, a pattern, a declared path, a file name) can add an output line or move the cursor: every output line escapes control characters, and file values are quoted with `repr` | — | `test_a_forged_header_cannot_add_an_output_line`, `test_control_characters_from_any_file_value_are_escaped`, `test_a_control_character_in_a_declared_path_is_escaped` |

## Evidence (4.1)

| Section, line | What is checked | Rule id (contract) | Test |
|---|---|---|---|
| 4.1, 280-281, 296; 332 | The eighteen columns, in order | `columns` | `test_columns_rule` |
| 4.1, 308; 333 | An empty `id` | `id-empty` | `test_each_rule_id_is_triggered[id-empty]` |
| 4.1, 308; 334 | A repeated `id` | `id-duplicate` | `[id-duplicate]` |
| 4.1, 303; 335 | An `attribute_kind` the specification does not declare; "checked against the outcomes and attributes that use it" (314) | `attribute-kind` | `[attribute-kind]` |
| 4.1, 308; 336 | A `person_id` the registry does not hold | `person-unknown` | `[person-unknown]` |
| 4.1, 304; 337 | A `unit_id` in an author study, or none in a passage or work study | `unit-id` | `[unit-id]`, `test_a_unit_id_in_an_author_study_is_an_error` |
| 4.1, 305-306; 338 | A `unit_id` that is neither an attribution unit nor the row's `person_id` | `unit-unknown` | `[unit-unknown]` |
| 4.1, 306-307; 339 | A row on an attribution unit whose `person_id` is not the unit's attributed author | `unit-person` | `[unit-person]` |
| 4.1, 308-309; 340 | A `\|` in a `person_id` or a `unit_id` | `id-separator` | `[id-separator]` |
| 4.1, 303; 341 | A `tier` not in `evidence.tiers` | `tier-unknown` | `[tier-unknown]` |
| 4.1, 298; 342 | A counted row without a `quote` | `counted-quote` | `[counted-quote]` |
| 4.1, 298; 343 | A counted row with neither `citation` nor `source_id` | `counted-citation` | `[counted-citation]` |
| 4.1, 299; 344 | A counted row whose `basis` is not `own` or `reported` | `counted-basis` | `[counted-basis]` |
| 4.1, 345-346 (against 342-344) | A `reported` row without a `reporter`, in any tier: decided by the rule table, which says "a counted row" for 342-344 and "a `reported` row" / "an `own` row" for 345-346 | `reported-reporter` | `[reported-reporter]`, `test_reported_and_own_rules_hold_outside_counted_tiers_too` |
| 4.1, 346 | An `own` row that names a `reporter`, in any tier (as above) | `own-reporter` | `[own-reporter]` |
| 4.1, 340 | A `\|` in a `person_id` | `id-separator` | `test_a_pipe_in_a_person_id_is_an_error` |
| 4.1, 301; 347 | A not-established row with a `quote` | `ne-quote` | `[ne-quote]` |
| 4.1, 302; 348 | A not-established row without a `note` | `ne-note` | `[ne-note]` |
| 4.1, 310-311; 349; 5.3, 752-756 | Forbidden vocabulary, matched without regard to case on folded text, in every column but `exempt_columns` (default `["quote"]`; an empty list checks quotations) | `vocabulary` | `[vocabulary]`, `test_the_vocabulary_spares_quotes_unless_told_otherwise`, `test_vocabulary_is_matched_on_folded_text` |
| 4.1, 330 | Every rule id has a case | — | `test_every_rule_id_but_columns_has_a_case` |
| 4.1, 313-314 | The checks apply to the whole file whenever it is checked | — | every case above checks the whole file |
| 4.1, 315 | "a missing registry is itself an error" | `registry-missing` (toolkit) | `test_a_missing_registry_is_itself_an_error` |
| 4.1, 315 (proposal 4) | A registry with other columns, or an empty or repeated `person_id` | `registry-columns`, `registry-person` (toolkit) | `test_registry_shape` |
| 4.1, 314; 4.7, 626, 630; 3, 269-270 | Declared attribute kinds: `evidence.attribute_kinds`, those the outcomes and attributes use, and, as a reading of the text, the period's `basis`: the period attribute reads `work_date` and `life_dates` rows (626, 630), so it "uses" them (314) | — | `test_the_invented_study_passes_every_row_check` (its `work_date` and `life_dates` rows) |
| 4.1, 317-320 | A person-level row carries the person's own id as `unit_id` | — | `test_a_person_level_row_carries_its_own_person_id` |
| 5.3, 756 | "Without it no vocabulary check runs" (no declaration) | — | `test_the_invented_study_passes_every_row_check` uses one; the shape tests' minimal study has none |
| 5.3, 752 (proposal 6) | A forbidden pattern that does not compile, for any reason the engine gives (an error, a repeat count too large, nesting too deep); an unreadable vocabulary file | `vocabulary-file` (toolkit) | `test_a_forbidden_pattern_that_does_not_compile`, `test_a_pattern_that_cannot_be_compiled_is_a_finding_whatever_it_raises[...]`, `test_every_compile_failure_is_caught[...]` |
| (proposal 17) | Limits on project patterns: `MAX_PATTERN_CHARS` (1000) per pattern, `MAX_PATTERNS` (10000) per file, `MAX_MATCH_CHARS` (65536) of folded text per search; a longer cell is reported as not checked, under `vocabulary` | `vocabulary-file`, `table-pattern`, `vocabulary` | `test_a_pattern_that_cannot_be_compiled_is_a_finding_whatever_it_raises[over-long]`, `test_too_many_patterns_and_too_long_text` |
| 4.1, 121, 313-314; 5.1, 725 | Evidence in a `plugin` format: **not implemented** — see "Not implemented" | `evidence-plugin` (toolkit; fails closed) | `test_plugin_format_evidence_is_not_checked_and_says_so` |
| 3, 217 | A draft may lack its input files: no evidence file needs no registry; a missing attribution or vocabulary file is not read | — | `test_a_draft_without_evidence_needs_no_registry`, `test_a_draft_may_lack_the_attribution_and_vocabulary_files` |

## Legacy exceptions (4.1, lines 351-366)

| Line | What is checked | Error id | Test |
|---|---|---|---|
| 352-353 | Columns `id, rule` | `exceptions-columns` (toolkit) | `test_the_exceptions_file_has_exactly_two_columns` |
| 355-356 | A listed breach is reported, with counts by rule, and does not fail | — (printed: `breaches excused by rule`) | `test_a_listed_breach_is_excused_and_counted` |
| 357-358 | `columns`, `id-empty`, `id-duplicate` cannot be listed | `exceptions-unlistable` (toolkit) | `test_exception_file_errors[...columns...]`, `[...id-duplicate...]` |
| 357-358 | A row with an empty or repeated id cannot be named, so no listing excuses it | — | `test_a_duplicated_id_cannot_be_excused` |
| 359-360 | A listed row that comes to break a further rule fails on that rule | the rule's id | `test_a_listed_row_that_breaks_a_further_rule_fails_on_it` |
| 361-362 | A listed exception that no longer applies (row removed, or now passes) is an error | `exceptions-stale` (toolkit) | `test_exception_file_errors[...]` (two cases) |
| 363 | Allowed only in a legacy study | `legacy-exceptions-status` (step A) | `test_exceptions_are_allowed_only_in_a_legacy_study` |
| (proposal 8) | A rule that is not a 4.1 rule id; an empty id; a pair listed twice | `exceptions-rule`, `exceptions-id`, `exceptions-duplicate` (toolkit) | `test_exception_file_errors[...]` |
| 366 | Every output records how many exceptions it was read with | printed by `survey-validate` (`read with N legacy exception(s)`); the record itself is 4.6, step C | `test_a_listed_breach_is_excused_and_counted` |
| 364-365 | "The tool can write a first version from the current breaches" | **not implemented** (part 2, with `survey-rows`) | — |
| 323 | "A legacy exception never covers a batch row" | **not implemented** (part 2: the batch merge) | — |

## Fetch-receipt citations (5.4; section 3, line 223; 4.4, lines 478-487)

| Line | What is checked | Error id | Test |
|---|---|---|---|
| 5.4, 770-772 | A `locator` of the form `<work slug>#p<N>` is a locus; "a row with any other locator is checked against the fetch receipt for its `url` and quote" — every row, whatever its tier; an empty locator is not given and cites nothing | — | `test_a_locus_locator_cites_no_receipt` |
| 3, 223; 5.4, 771 | "evidence that cites a fetch receipt when `evidence.receipts` is not declared", for a row in any tier | `receipts-undeclared` (toolkit) | `test_receipt_citation_errors[undeclared-...]`, `test_an_uncounted_row_that_cites_a_receipt_needs_the_receipts_declared` |
| 4.4, 480-486 | A receipt has the thirteen keys; only `sha256`, `context` and `wayback` may be absent; the ten others are required | `receipt-malformed` | `test_a_receipt_missing_a_required_key_is_malformed[...]` (ten cases), `test_ten_receipt_keys_are_required` |
| 4.4, 483-484 | The receipt id: first 24 hex of SHA-256 of the URL, a line feed and the quote folded without spaces | — | `test_the_receipt_id_follows_4_4` |
| 5.4, 773 (proposal 9) | A counted receipt-citing row with no `url`, or with no receipt file: its quotation cannot be re-found. A receipt that is there but is not a 4.4 receipt of this row's url and quote, or resolves outside the repository, is an error in any tier | `receipt-url`, `receipt-missing`, `receipt-malformed` (toolkit) | `test_receipt_citation_errors[...]` (five cases), `test_a_cited_receipt_that_is_present_passes`, `test_an_uncounted_row_with_a_broken_receipt_fails_but_one_without_needs_none` |
| 5.4, 773-774 | A counted row with an empty `locator`: its quotation can be re-found neither at a locus nor through a receipt, and lines 773-774 decide the outcome (an error in a draft or active study, reported and counted in a legacy one); only the id is the toolkit's | `locator-missing` (toolkit id) | `test_a_counted_row_without_a_locator_is_refused` |
| 5.4, 773-775 | In a legacy study a counted row that predates receipts (no receipt, no url, no locator) "is reported and counted, and is not an error" | printed `REPORTED [...]` | `test_a_legacy_study_reports_an_unfindable_quotation` |
| (proposal 20) | A receipt that is there and broken (`receipt-malformed`) fails a legacy study too. This tightens lines 773-775, which say a counted row whose quotation cannot be re-found "at a locus or in a receipt" is not an error in a legacy study | `receipt-malformed` | `test_a_broken_receipt_is_an_error_in_a_legacy_study_too` |
| 4.1, 356; 5.4, 774 | Excused breaches by rule, and counted quotations not re-found (and how many were reported), printed on every run, failing runs included | — | `test_excused_counts_and_unfindable_totals_print_on_a_failing_run` |
| 5.4, 768-776 | Re-finding the quotation at a locus or inside a receipt, and what a receipt's own `found: false` means | **not implemented** (step G); seam `survey_evidence.refind_quotation`, which returns "not checked" and does not read `found` | `test_the_refind_seam_never_counts_a_quotation_as_found` |

## Attribution (4.3, lines 424-441)

The contract gives these no ids; they are the toolkit's own. None can be listed as a legacy exception (432-433).

| Line | What is checked | Error id | Test |
|---|---|---|---|
| 426-427, 431 | Columns: the six, one per passage attribute, then `basis, note`; "header included" | `attribution-columns` | `test_attribution_columns_follow_the_passage_attributes` |
| 429 | `status` is one of `unit.attribution.statuses` | `attribution-status` | `test_each_attribution_check_is_triggered[attribution-status]` |
| 430 | `author_kind` is `person` or one of `unit.collective.kinds` | `attribution-author-kind` | `[attribution-author-kind]` |
| 434 | A `unit_id` that is empty | `attribution-unit-empty` | `[attribution-unit-empty]` |
| 434 | … repeated | `attribution-unit-duplicate` | `[attribution-unit-duplicate]` |
| 434-435 | … or equal to a `person_id` the registry holds | `attribution-unit-is-person` | `[attribution-unit-is-person]` |
| 434-435 (proposal 10) | Without a registry, the persons of the registry's own sources (the attribution and evidence files, 4.4 lines 509-511) stand in; this can only refuse more | `attribution-unit-is-person` | `test_without_a_registry_the_registrys_sources_stand_in` |
| 436 | A passage-attribute cell that is empty or not one of its level codes | `attribution-passage-attribute` | `[attribution-passage-attribute]` |
| 437 | One `person_id` with more than one `author_kind` | `attribution-author-kinds` | `[attribution-author-kinds]` |
| 438 | A `\|` in a `unit_id` or a `person_id` | `attribution-separator` | `[attribution-separator]` |
| (proposal 11) | An empty `person_id` | `attribution-person-empty` | `[attribution-person-empty]` |

## Bucket tables and years (4.8, lines 673-706)

| Line | What is checked | Error id | Test |
|---|---|---|---|
| 675-676 | Columns `field, pattern, unless, bucket, note` | `table-columns` (toolkit) | `test_bucket_table_errors[...table-columns]` |
| 686 | An empty table | `table-empty` (toolkit) | `[...table-empty]` |
| 686 | A row without `pattern`, `bucket` or `note` | `table-row` (toolkit) | three cases |
| 686-687 | An expression that does not compile (`pattern` or `unless`) | `table-pattern` (toolkit) | two cases |
| (proposal 12) | A `bucket` that is not one of the attribute's declared levels or flags | `table-bucket` (toolkit) | `[...table-bucket]` |
| (proposal 12) | A bucketer `fallback` that is not one of the attribute's declared levels | `table-fallback` (toolkit) | `test_a_fallback_outside_the_levels_is_refused` |
| 680 | `field` is the `attribute_kind` the row looks at, or `*` | — | `test_match_first_takes_the_first_row_that_fires` |
| 681 | `pattern` is searched in the folded value, spaces kept | — | `test_patterns_search_the_folded_value` |
| 681 (proposal 13) | A pattern or `unless` with an upper-case letter outside an escape: it is searched in folded, lower-cased text and could never match, so it is refused | `table-pattern` | `test_an_upper_case_table_pattern_is_refused` |
| 682 | `unless`: the row does not fire on a value this also matches | — | `test_unless_stops_a_row_firing` |
| 690-692 | `match: "first"`: the first row that fires on any value decides; else `fallback`, else the missing value | — | `test_match_first_takes_the_first_row_that_fires` |
| 693-695 | `match: "all"`: every row that fires adds its bucket; no fallback | — | `test_match_all_collects_every_bucket` |
| 690, 207-208 | The per-kind default: `first` for a categorical attribute; a flags table bucketer with no `match` is refused by step A (`match-missing-flags`, its proposal 7) | step A's id | step A's `test_each_check_beyond_shape_is_triggered[match-missing-flags]` |
| 699-700 | One value: `work_date` the first run of three or four digits not part of a longer number; `life_dates` the largest | — | `test_a_year_from_one_value[...]` |
| 699-701 | A run of three or four digits is read whatever words stand around it (`AD 1200`, `1200 CE`, `c. 1750`, `Epistulae ad Familiares, 1742`, `ce livre, 1750`, `5th centre, 1750`) | — | `test_values_read_by_the_run_rule[...]` |
| 700-701 | Only where a value has no such run, a stated century gives its middle year. `4th c.` is the text's example; accepted spellings: an ordinal of one or two digits (`1st`, `2nd`, `3rd`, `4th`, …) followed, as a whole token and in any case, by `c`, `c.`, `cent`, `cent.`, `century` or `centuries` (`4th c`, `4th C.`, `4th century`, `12th cent.`, `4th-5th centuries`). An ordinary word after an ordinal is not a century (`5th centre`, `4th cell`). Several centuries: the first for `work_date`, the largest for `life_dates` (proposal 14) | — | `test_a_stated_century_gives_its_middle_year[...]`, `test_an_ordinary_word_after_an_ordinal_is_not_a_century[...]`, `test_a_run_of_digits_comes_before_a_stated_century` |
| 701 (proposal 14) | Two-digit and negative years are not read (a `-` after a non-digit is a sign; after a digit, a range) | — | `[in 42-…]`, `[-350-…]`, `[1701-1768-…]` |
| 701 (proposal 14) | A number marked BC or BCE (`350 BC`, `350 B.C.E.`, `4th c. BC`; a whole token after the number, any case, dotted or not) is negative, so it is not read; another run in the same value still is | — | `test_a_year_marked_bc_is_negative_and_not_read[...]`, `test_a_bc_run_does_not_hide_another_run` |
| 703-704 | Several values: `life_dates` the largest year | — | `test_life_dates_take_the_largest_year_among_values` |
| 705-706 | A year equal to a cut begins the later period | — | `test_a_year_equal_to_a_cut_begins_the_later_period` |
| 703 | `work_date` years combine by the cell (4.7) | **not implemented** (step D, the frame) | — |
| 639 | A plug-in bucketer | **not implemented** (refused in a frame by 4.7; step D) | — |

## `survey-validate` (section 7, line 925)

| Line | What is checked | Output | Test |
|---|---|---|---|
| 925 | "checks the specification, every row file present and the ledger's folder; writes nothing" | step A's checks, then every row file this table lists | `test_the_invented_study_passes_every_row_check`, `test_validate_writes_nothing_and_is_deterministic` |
| 1.5 | Deterministic: the same run twice gives the same output | — | `test_validate_writes_nothing_and_is_deterministic` |
| 925 | Row files of later steps (codes, adjudications, the logs, overrides) | **not implemented** (steps B part 2, C, D, G) | — |

## Not implemented

| Section, line | What | Why |
|---|---|---|
| 4.1, 121, 313-314; 5.1, 717, 725 | Evidence in a `plugin` format | Plug-in evidence readers are not loaded in this part, so a study whose evidence format is `plugin` **fails `survey-validate`** (`evidence-plugin`). The text decides that plug-in rows are checked (121, 313-314, 725); loading a reader executes project code, and 5.1 (717: "it is cleared the same way the specification is") raises whether that needs gate S0 cleared first. That needs a plan before it is built |
| 5.4, 768-776 | Re-finding quotations; a receipt's `found` | Step G (seam `refind_quotation`) |
| 4.7 | Combining a cell's `work_date` years; plug-in bucketers in a frame | Step D |

## Not in part 1 (step B part 2)

| Section, line | What | Why not here |
|---|---|---|
| 4.1, 322-326 | The batch merge: checked in full with the file it joins; nothing appended unless every row passes; never covered by a legacy exception; refused into a `plugin` format | It renews the registry's provenance record (4.4), which is 4.6 (step C) |
| 4.4, 489-506 | The overrides file: columns, decisions, every rule of 491-506 | Part 2, with the registry |
| 4.4, 507-523 | The registry: persons, names, build, the record a merge renews | Part 2; needs 4.6 |
| 4.4, 524-530 | Candidates (`same-id`, `exact`, `similar`), proposed override rows, stop words | Part 2 |
| 7, 928-929 | `survey-registry`, `survey-rows` and their bridge commands | Part 2 |
| 4.1, 364-365 | Writing a first version of the exceptions file | Part 2 |

## Proposed contract changes

1. **A blank line in a row file** is an error under the file's columns id (a row of another width is decided by
   line 276).
2. **Row files are regular files of at most 64 MiB** (`MAX_CSV_BYTES`), streamed; a FIFO or device is not opened.
   Links follow rule 1.6, as for covered files.
3. *(Settled: `reported-reporter` and `own-reporter` apply in every tier, by lines 342-346.)*
4. **The registry's own shape when evidence is checked**: other columns, an empty or repeated `person_id`, are
   errors; only the `person_id` column holds a person (an id in `merged_from` is not held).
5. *(A reading, not a proposal: the period's `basis` counts as used, by lines 314, 626, 630, 269-270.)*
6. **A forbidden pattern that does not compile**, for any reason the engine gives, and an unreadable vocabulary
   file: an error.
7. *(Not a proposal: `evidence-plugin` is "not implemented"; see that section.)*
8. **The exceptions file's own errors**: an unknown rule, an empty id, a pair listed twice.
9. **The receipt citation's form**: a counted receipt-citing row needs a `url` and its receipt; a receipt that is
   there must be a 4.4 receipt of this row's url and folded quote, inside the repository, in any tier; an uncounted
   row's quotation need not be re-found, so it needs no url or receipt (line 773 speaks of counted rows only).
10. **The attribution check without a registry**: the registry's sources stand in.
11. **An empty `person_id` in the attribution file**: refused.
12. **A table `bucket` or a bucketer `fallback` outside the attribute's declared levels or flags**: refused (when
    the attribute declares them).
13. **An upper-case bucket pattern**: refused, because it is searched in folded, lower-cased text (4.8 says
    nothing on case; 5.3 says vocabulary is matched "without regard to case").
14. **BC and BCE, and several centuries in one value.** 4.8 says negative years are not read (line 701) but not how
    a value marks one. Step B reads a number followed by `BC` or `BCE` (a whole token, any case, dotted or not) as
    negative, so it gives no year, and a `-` directly before a run and after a non-digit as a sign. Where a value
    states several centuries and no run, the first is read for `work_date` and the largest for `life_dates`, as for
    runs; the text speaks of "a stated century" only. (The text decides precedence: a century is read only where
    there is no run.)
15. **The split of step B** at the registry, because the merge needs the 4.6 record (see the top of this file).
16. **A NUL in a cell**: an error (`cell-nul`).
17. **Limits on project patterns**: 1000 characters a pattern, 10000 patterns a file, 65536 characters of folded
    text a search.
18. *(Settled by lines 773-774: a counted row without a `locator` cannot be re-found; only the id `locator-missing` is the toolkit's.)*
19. **Escaped output**: control characters in any output line are escaped, and a quoted value is cut at
    `MAX_QUOTED_CHARS` (200) characters in messages only (the contract fixes no output form).
20. **A broken receipt in a legacy study** is an error (`receipt-malformed`), tightening lines 773-775: a receipt that
    is there but unusable is not a row "that predates receipts".
