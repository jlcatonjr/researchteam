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
| 4, 276 (proposal 1) | A row whose width differs from the header's, a blank line included | the file's columns id | `test_a_row_of_the_wrong_width_and_a_blank_line_are_errors` |
| 4, 276 | "An empty cell means "not given"; a tool never treats it as a value" | — (an empty value never fires a bucket row) | `test_match_first_takes_the_first_row_that_fires` |
| (proposal 2) | A row file is read only when it is a regular file reached without a final link, of at most `MAX_CSV_BYTES` (256 MiB) | the file's columns id | `test_a_row_file_reached_through_a_final_link_is_not_read` |

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
| 4.1, 300; 345 (proposal 3) | A `reported` row without a `reporter`, in any tier | `reported-reporter` | `[reported-reporter]`, `test_reported_and_own_rules_hold_outside_counted_tiers_too` |
| 4.1, 300; 346 (proposal 3) | An `own` row that names a `reporter`, in any tier | `own-reporter` | `[own-reporter]` |
| 4.1, 301; 347 | A not-established row with a `quote` | `ne-quote` | `[ne-quote]` |
| 4.1, 302; 348 | A not-established row without a `note` | `ne-note` | `[ne-note]` |
| 4.1, 310-311; 349; 5.3, 752-756 | Forbidden vocabulary, matched without regard to case on folded text, in every column but `exempt_columns` (default `["quote"]`; an empty list checks quotations) | `vocabulary` | `[vocabulary]`, `test_the_vocabulary_spares_quotes_unless_told_otherwise`, `test_vocabulary_is_matched_on_folded_text` |
| 4.1, 330 | Every rule id has a case | — | `test_every_rule_id_but_columns_has_a_case` |
| 4.1, 313-314 | The checks apply to the whole file whenever it is checked | — | every case above checks the whole file |
| 4.1, 315 | "a missing registry is itself an error" | `registry-missing` (toolkit) | `test_a_missing_registry_is_itself_an_error` |
| 4.1, 315 (proposal 4) | A registry with other columns, or an empty or repeated `person_id` | `registry-columns`, `registry-person` (toolkit) | `test_registry_shape` |
| 4.1, 314-315 (proposal 5) | Declared attribute kinds: `evidence.attribute_kinds`, the outcomes' and attributes' source attributes, and the period's `basis` | — | `test_the_invented_study_passes_every_row_check` (its `work_date` and `life_dates` rows) |
| 4.1, 317-320 | A person-level row carries the person's own id as `unit_id` | — | `test_a_person_level_row_carries_its_own_person_id` |
| 5.3, 756 | "Without it no vocabulary check runs" (no declaration) | — | `test_the_invented_study_passes_every_row_check` uses one; the shape tests' minimal study has none |
| 5.3, 752 (proposal 6) | A forbidden pattern that does not compile; an unreadable vocabulary file | `vocabulary-file` (toolkit) | `test_a_forbidden_pattern_that_does_not_compile` |
| 4.1, 121; 5.1 (proposal 7) | Evidence in a `plugin` format: the reader plug-in is not loaded in this version, so the rows are not checked, and that is an error | `evidence-plugin` (toolkit) | `test_plugin_format_evidence_is_not_checked_and_says_so` |
| draft | A draft with no evidence file needs no registry | — | `test_a_draft_without_evidence_needs_no_registry` |

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
| 5.4, 770-772 | A `locator` of the form `<work slug>#p<N>` is a locus; "a row with any other locator is checked against the fetch receipt for its `url` and quote". Checked for counted rows, whose quotations 5.4 requires to be re-found | — | `test_a_locus_locator_cites_no_receipt` |
| 3, 223 | "evidence that cites a fetch receipt when `evidence.receipts` is not declared" | `receipts-undeclared` (toolkit) | `test_receipt_citation_errors[undeclared-...]` |
| 4.4, 483-484 | The receipt id: first 24 hex of SHA-256 of the URL, a line feed and the quote folded without spaces | — | `test_the_receipt_id_follows_4_4` |
| 5.4, 773 (proposal 9) | A receipt-citing row with no `url`; no receipt file; a receipt that is not a receipt object of 4.4's keys, or not this row's url and quote | `receipt-url`, `receipt-missing`, `receipt-malformed` (toolkit) | `test_receipt_citation_errors[...]` (five cases), `test_a_cited_receipt_that_is_present_passes` |
| 5.4, 773-775 | In a legacy study an unfindable quotation "is reported and counted, and is not an error" | printed `REPORTED [...]` | `test_a_legacy_study_reports_an_unfindable_quotation` |
| 5.4, 768-776 | Re-finding the quotation at a locus or inside a receipt | **not implemented** (step G); seam `survey_evidence.refind_quotation`, which returns "not checked"; the count is printed | `test_the_refind_seam_never_counts_a_quotation_as_found` |

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
| 681 | `pattern` is searched in the folded value, spaces kept (proposal 13 on case) | — | `test_patterns_search_the_folded_value` |
| 682 | `unless`: the row does not fire on a value this also matches | — | `test_unless_stops_a_row_firing` |
| 690-692 | `match: "first"`: the first row that fires on any value decides; else `fallback`, else the missing value | — | `test_match_first_takes_the_first_row_that_fires` |
| 693-695 | `match: "all"`: every row that fires adds its bucket; no fallback | — | `test_match_all_collects_every_bucket` |
| 690, 207-208 | The per-kind default: `first` for a categorical attribute; a flags table bucketer with no `match` is refused by step A (`match-missing-flags`, its proposal 7) | step A's id | step A's `test_each_check_beyond_shape_is_triggered[match-missing-flags]` |
| 699-700 | One value: `work_date` the first run of three or four digits not part of a longer number; `life_dates` the largest | — | `test_a_year_from_one_value[...]` |
| 700-701 (proposal 14) | No such run: a stated century (`4th c.`) gives its middle year | — | `[4th c.-…]`, `[1st c.-…]` |
| 701 (proposal 14) | Two-digit and negative years are not read (a `-` after a non-digit is a sign; after a digit, a range) | — | `[in 42-…]`, `[-350-…]`, `[1701-1768-…]` |
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

1. **A row of another width, or a blank line** in a row file: an error under the file's columns id.
2. **A size cap and regular files only** for row files (`MAX_CSV_BYTES`, 256 MiB; no final link, FIFO or device).
3. **`reported-reporter` and `own-reporter` in every tier.** 4.1 lists them after a counted-tier clause
   (line 299-300) but the rule table (345-346) gives no tier; read as applying to every row.
4. **The registry's own shape when evidence is checked**: other columns, an empty or repeated `person_id`, are
   errors; only the `person_id` column holds a person (an id in `merged_from` is not held).
5. **Which attribute kinds are declared**: `evidence.attribute_kinds`, those the outcomes and attributes use, and
   the period's `basis` (4.7 reads `work_date` and `life_dates` rows). Propose naming the period's basis.
6. **A forbidden pattern that does not compile**, and an unreadable vocabulary file: an error.
7. **Plugin-format evidence** is not checked in this version, and that is an error (fail closed), not a skip.
8. **The exceptions file's own errors**: an unknown rule, an empty id, a pair listed twice.
9. **The receipt citation's form**: a receipt-citing counted row needs a `url`; the receipt must exist, be a 4.4
   receipt object, and be for this row's url and (folded) quote. A non-counted row is not checked.
10. **The attribution check without a registry**: the registry's sources stand in.
11. **An empty `person_id` in the attribution file**: refused.
12. **A table `bucket` or a bucketer `fallback` outside the attribute's declared levels or flags**: refused (when
    the attribute declares them).
13. **Case in bucket patterns**: searched in the folded (lower-cased) value without a case flag, so an upper-case
    pattern never fires; 5.3 says vocabulary is matched "without regard to case", 4.8 says nothing.
14. **The year reader's edges**: a century is read only in the form `<n>(st|nd|rd|th) c.`; a `-` directly before a
    run and after a non-digit makes it negative; a run next to a `.` or a letter still counts.
15. **The split of step B** at the registry, because the merge needs the 4.6 record (see the top of this file).
