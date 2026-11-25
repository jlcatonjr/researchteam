# H6 step F: check table (sign-off verification and stage refusal)

Plan: `post-1.3.0-h6-survey-sign-off.plan.md`. Design: `post-1.3.0-h6-step-f-design.md` (its section 1 is the state
table this file maps to code). The design note's open questions were settled on 2026-11-25: some by the
operator, others by stricter defaults the session adopted on `@security`'s advice (see "Proposals" for which is
which). `@security` added cases 39 to 46, and the reviews of 2026-11-25 added S1 to S10 and T1 to T6. Contract line numbers are those of `docs/survey-toolkit.md`, version 1.

Tests are in `tests/test_survey_verify.py` (step F) and `tests/test_survey_gates.py` (step A, adapted).

- **Signing** tests are named `test_signed_*`. They run only where agentteams 1.3.0 and `cryptography` are
  importable, and are skipped with the reason elsewhere.
- **Fake** tests use a stand-in verifier. They prove the wiring, not that a signature verifies.

## States (design note, section 1)

| # | Situation | State, as built | Code | Test |
|---|---|---|---|---|
| 1 | A valid Ed25519 row for the current hash, key in the folder, approver on the list, request current | `CLEARED` | `survey_gates.verify_signoff` (the tools' rules, then the child), `survey_verify.interpret` | `test_signed_a_valid_ed25519_row_clears_through_agentteams`; fake: `test_a_well_formed_row_reaches_the_verifier_and_its_answer_decides` |
| 2 | Only a row for an older manifest hash | `UNCLEARED` (stale request; after a rewrite of the request, no row) | `gate_status` step 3; `row_refusal` | `test_signed_a_covered_file_edited_after_signing_unclears` |
| 3 | No row for the current hash | `UNCLEARED`, the tools' reason, agentteams not asked. Where agentteams is not usable here, the gate reads `UNAVAILABLE` instead (rule 1.7; review T1): the probe comes first | `verify_signoff`, `row_refusal` | `test_signed_a_covered_file_edited_after_signing_unclears`; `test_without_agentteams_a_row_the_tools_would_refuse_still_reads_unavailable[…]` |
| 3a | No request (Q7, a default the session adopted), including when the manifest cannot be built now (T5: not a cause of `UNAVAILABLE` line 816 lists) | `UNCLEARED`, with or without agentteams | `gate_status` step 7 | `test_no_request_is_uncleared_and_never_asks_agentteams`, `test_before_any_request_a_declared_gate_is_uncleared`, `test_no_request_and_a_manifest_that_cannot_be_built_is_uncleared` |
| 4 | A row of another scheme (the shared-secret scheme, or none) **anywhere** in the folder log (Q5) | malformed ledger (`ledger-scheme`): `UNAVAILABLE`, status 1, validate 1. *Differs from the note (which had `UNCLEARED`), by the operator's decision* | `survey_ledger._check_log` | `test_every_row_of_the_folder_log_must_be_ed25519` |
| 5 | `key_id` not a key file in the folder | `UNCLEARED`, agentteams not asked. Where agentteams is not usable here, the gate reads `UNAVAILABLE` instead (rule 1.7; review T1): the probe comes first | `row_refusal` (keys from the snapshot, S7) | `test_the_tools_refuse_a_row_whatever_agentteams_would_say[…op-other…]`, `test_signed_a_row_by_a_key_not_in_the_folder_never_reaches_agentteams`, `test_without_agentteams_…[cells1]` |
| 6 | Author not on the list the tools read (6c), read as agentteams reads it (`requesting_agent`, then `author`) | `UNCLEARED`. Where agentteams is not usable here, the gate reads `UNAVAILABLE` instead (rule 1.7; review T1): the probe comes first | `row_author`, `row_refusal` (list from the snapshot, S7) | `…[…someone-else…]` (two cases), `test_without_agentteams_…[cells2]` |
| 7 | A waiver file in the folder (an error, 6.2 lines 866-868), checked again after the agentteams call | malformed (step A); `UNAVAILABLE` | step A `ledger-waiver`; `_snapshot` | step A tests; `test_an_error_file_appearing_during_the_check_is_unavailable` |
| 8 | HALT in the folder log on the action | `UNCLEARED` (the tools: the latest row is a HALT) | `deciding_row`, `row_refusal` | `test_a_retraction_row_is_skipped_and_the_halt_behind_it_decides`, `test_signed_a_retracted_halt_on_the_action_needs_a_new_pass` |
| 8a, 9a | A HALT on a family name in any scanned log, either column schema; signed or not, retracted or not (Q1, interim; operator decision). An id names gate `<g>` when its tokens contain `survey signoff <g>` as a run, else every gate when they contain `survey signoff` (`survey-signoff:freeze`, `survey-signoff/S0-2026`, `freeze-survey-signoff`, case and spacing variants); a study's scope or action (`survey-signoff/<gate>/<study id>…`) is left to agentteams (@security S1) | `UNAVAILABLE`: whether the HALT still stands cannot be verified here (6.1, line 816; T3), and the reason says so | `survey_ledger._scan_family_halts`, `family_gates`, `tokens` | `test_a_family_halt_in_any_scanned_log_blocks_the_gates_it_names` (14 cases), `test_a_family_halt_in_the_other_column_schema_or_the_parent_team_binds`, `test_a_family_halt_in_the_folder_log_binds` |
| 9 | HALT on the action or the scope in a generated team log | `UNCLEARED` (agentteams, in the child) | `survey_verify.CHILD` | `test_signed_a_halt_in_a_team_log_binds_through_agentteams[ACTION]`, `[SCOPE]` |
| 9b | An ancestor (`derives_from`) | Not reachable: a row with a non-empty `derives_from` is refused (Q6) | `row_refusal` (`EMPTY_COLUMNS`) | `…[…derives_from…]` |
| 9d | A valid PASS for a study id that extends this one (`tidebell-survey-2` against `tidebell-survey`), same gate | `UNCLEARED`: the row that decides must name exactly the action the tools computed, and the verifier is only ever asked about that action | `deciding_row`, `row_refusal` | `test_a_row_for_a_study_id_that_extends_this_one_never_decides`, `test_signed_a_valid_pass_for_a_study_that_extends_this_one_never_clears_it` |
| 9c | HALT on a study id that extends this one (`demo-2` against `demo`, Q2) | `UNCLEARED`; the reason says so | `gates.NOT_CLEARED` | `test_signed_a_halt_in_a_team_log_binds_through_agentteams[EXTENDED]` |
| 10 | A retracted HALT on the exact action, with no new PASS after it | `UNCLEARED` until a new PASS; then `CLEARED`. After a retraction no earlier permission survives: the tools never treat an older sign-off as restored | `deciding_row` skips `HALT-RETRACTED`, so the HALT behind it decides | `test_a_retraction_never_restores_an_older_sign_off`, `test_a_retraction_row_is_skipped_and_the_halt_behind_it_decides`, `test_signed_a_retracted_halt_on_the_action_needs_a_new_pass` |
| 10a | A shared-secret retraction in a team log (Q11) | It never counts: the child's `HOME` is empty, so agentteams finds no shared-secret key | `survey_verify.child_env` | `test_the_childs_environment_is_an_allowlist`, `test_the_child_runs_isolated_with_an_empty_home` |
| 11 | A `consumed` column in the folder log | malformed (`ledger-log`): the exact header has no `consumed` column, so such a log is refused; a check spends nothing (6.2, lines 852 and 889) | `LOG_HEADER` | `test_a_log_with_an_extra_column_is_malformed` |
| 12 | `CONDITIONAL PASS`, pending | `UNCLEARED`. Where agentteams is not usable here, the gate reads `UNAVAILABLE` instead (rule 1.7; review T1): the probe comes first | `row_refusal` | `…[…pending…]`, `test_without_agentteams_…[cells3]` |
| 12a | `CONDITIONAL PASS`, verified | `CLEARED` when agentteams agrees | `row_refusal` | `test_a_verified_conditional_pass_reaches_the_verifier` |
| 13 | Folder log malformed | malformed ledger, `UNAVAILABLE` | step A, and `ledger-scheme` | step A tests |
| 13a | Folder log well-formed for the tools but refused by agentteams | **`UNCLEARED`**, not `UNAVAILABLE`: the tools read only the child's `cleared` answer, never its message text (Q3). Both refuse. The exact header and the every-row-Ed25519 rule make this rare | `interpret` | — |
| 13b | A team log that cannot be read (link, size, encoding, open quote, width, no action or verdict column) | `UNAVAILABLE`; status 0 | `_read_any_log` | `test_a_team_log_that_cannot_be_read_leaves_every_gate_unavailable` (four cases) |
| 14 | agentteams or `cryptography` absent (always on Python 3.10) | `UNAVAILABLE` for every gate with a current request, decided before the tools' row rules (rule 1.7, line 45; lines 915-917; review T1). No request and a stale request stay `UNCLEARED` (line 817; Q7). A blocking stage refuses; a build-only one runs | `verify_signoff` step 1, `survey_verify.probe` | `test_python_without_agentteams_reads_unavailable_and_blocking_stages_refuse`, `test_without_agentteams_a_row_the_tools_would_refuse_still_reads_unavailable` (four cases) |
| 15 | agentteams older than 1.3.0, or a version not exactly `X.Y.Z` | `UNAVAILABLE` (before the child, and again on the child's own answer) | `probe`, `parse_version`, `interpret` | `test_an_old_or_unreadable_agentteams_version_is_unavailable`; `test_only_one_well_formed_answer_for_the_exact_action_clears[…]` |
| 16 | Files changed since the request | `UNCLEARED`, decided first | `gate_status` step 3 | `test_a_stale_request_is_uncleared_before_anything_else`; step A tests |
| 16a | Files put back to a signed state while the request is newer (Q8) | `UNCLEARED` until `survey-manifest` rewrites the request; then `CLEARED` with no new signature | `gate_status` step 3 | `test_files_put_back_to_a_signed_state_read_uncleared_until_the_request_is_rewritten` |
| 17 | `mode: retroactive` | As prospective; recorded | `require_gate` | `test_require_gate_records_the_4_6_entry` |
| 18 | `enforce: build-only` | The stage runs and records the state, **except when the folder is malformed (Q9: refuses)** | `stage_decision(folder_malformed=…)`, `require_gate` | `test_a_malformed_sign_off_folder_refuses_every_gated_stage`, `test_require_gate_records_the_4_6_entry` |
| 19, 20 | Undeclared gate; legacy study | `NOT DECLARED`; refuses, or runs in a legacy study | `stage_decision` (unchanged) | step A `test_stage_decision_follows_the_6_1_table`; `test_require_gate_records_the_4_6_entry` |
| 21 | A reason the HALT scan cannot be made | `UNAVAILABLE`; status 0 | step A | step A tests |
| 22 | Something changed while agentteams checked | `UNAVAILABLE` | `_snapshot` | `test_a_change_while_agentteams_checks_is_unavailable` |
| — | The child's answer: anything but exit 0 and one JSON object, with `cleared` exactly `true` (S3), the same action, version ≥ 1.3.0, its module exactly `<purelib>/agentteams/__init__.py` (S4), and the parent's prefix; stdout read through a bounded read (S5) | `UNAVAILABLE` (or `UNCLEARED` for a well-formed `cleared: false`) | `interpret`, `run_child` | `test_only_one_well_formed_answer_for_the_exact_action_clears` (17 cases), `test_the_childs_stdout_is_read_through_a_bounded_read`, `test_the_child_is_started_with_minus_b_and_minus_i` |

## `@security` cases 39 to 46

| Case | Handling | Test |
|---|---|---|
| 39: more than one git root encloses the ledger folder | `UNAVAILABLE`: the tools read the team logs of the study's repository only | `test_more_than_one_git_root_above_the_folder_is_unavailable` |
| 40: the verifier's own install is patched inside the ignored `.venv`, so no diff shows it | Covered by the report line of N1: `survey-status` says whether the verifying package and its interpreter are inside the work tree (S6) | `test_the_verifier_location_never_shows_a_home_path` |
| 41: a forged `HALT-RETRACTED` in an unsigned team log lifts a HALT recorded after the sign-off | **Residual; held by review.** It concerns HALTs on a scope or an action in a team log, which agentteams judges in the child. A family HALT is not affected: under the interim rule it blocks whether retracted or not | — |
| 42: a specification edit sets `legacy` and removes a gate's declaration; no manifest goes stale, and the stage runs as `NOT DECLARED` | **Residual; flag it in review** | — |
| 43: a plug-in or post-step swapped between the gate check and its run | Belongs to the stages that run project code (steps D and G). `survey_gates.require_gate`'s docstring says a stage runs only bytes whose hash matches the cleared manifest's entry. No code in step F | — |
| 44: `key_id` with `/` or `..` | Refused (`UNCLEARED`) | `…[…../op-test…]`, `…[…keys/op-test…]` |
| 45: control characters or newlines in a log value | `survey_core.safe` (step B's helper) escapes every control, format, surrogate, private-use and line or paragraph separator character in every printed line: `print_findings`, the `survey-status` reasons and notes, the `survey-validate` notes and `survey-manifest`'s lines | `test_status_escapes_every_value_from_a_log`, `test_safe_escapes_controls_and_separators` |
| 46: two study ids that differ only by case | A study id is a lower-case slug (`survey_spec.SLUG`), so two ids cannot differ only by case. The tools cannot list a repository's other studies without a scan the contract does not define. As the fallback, they compare the action exactly, case included | `test_the_row_that_decides_is_agentteams_latest_and_must_name_the_action_exactly` |

## The child (Q3)

The child runs `sys.executable -B -I -c survey_verify.CHILD <folder> <scope> <manifest>` (`-B`: no `__pycache__`, T2).

- **What it runs.** The snippet imports only agentteams' public `clearance_binding.check_file_clearance` and
  `clearance_action`. It prints one JSON line: `version`, `file`, `purelib`, `prefix`, `cleared`, `action`.
- **Its environment** is exactly `PATH=/usr/bin:/bin`, `LC_ALL=C`, and `HOME` = `TMPDIR` = a fresh, empty folder,
  removed afterwards.
- **How it is run.** `stdin` is closed, `stderr` is discarded, the timeout is 120 s, and `stdout` is read through a
  bounded read that stops after 64 KiB + 1 byte, which is refused (S5).
- **What it reads from `HOME`.** agentteams 1.3.0 reads a shared-secret key from
  `~/.config/agentteams/keys/decision-hmac.key` (`signed_ledger.HMAC_KEY_DIR`), and the empty `HOME` defeats that.
  It reads Ed25519 verify keys only from the team directory, never from `HOME`.
- **Where the verifier is.** `survey-status` prints the verifying agentteams' location: "inside the work tree" (a
  path relative to the root) or "outside the work tree" (from `site-packages` on), and whether its interpreter's
  prefix is inside the work tree (S6). It never prints a home path (N1).

## Not implemented

- **Judging a retraction of a family HALT** under each log's own rules. No public agentteams call does it; the
  interim rule (Q1) blocks on every such HALT row.
- **Reading team logs under a second git root.** Case 39 refuses instead.
- **Telling `UNCLEARED` from `UNAVAILABLE`** when agentteams refuses a log the tools accept (row 13a).
- **The gated stages themselves** (steps D and G); `require_gate` is their entry point.
- **A CI job** that installs agentteams. It is a separate pull request; the list it needs is in the step F report
  and the changelog.

## Residual gaps (no tool can close them)

- **Edits to a log's history.** No tool can detect every edit to a decisions log's history; review of the ledger
  folder's history is the control (6.2, lines 874-880). `survey-status` says so.
- **A key and an approver planted in the folder.** Proving who put them there is 6.2's stated limit (open point 7);
  only reviewed changes and branch protection hold it. `survey-status` prints the limit.
- **A row signed for the same project, study id and files in another repository** clears here too (Q10, accepted
  for version 1).
- **A tampered verifying install.** An agentteams inside the work tree can be edited by an agent. `survey-status`
  says where the verifier is installed (N1), and a gate may still read `CLEARED` from it.
- **Cases 41 and 42** of `@security`'s list (above).

## Proposals (contract changes; version 2 unless the operator says otherwise)

### Operator decisions (2026-11-25)

1. **Family HALTs: the interim rule** (Q1). Any HALT row on a family name blocks, retracted or not; this replaces
   "a retraction counts only where it is valid in its own log" (line 910) for those names. The gate reads
   `UNAVAILABLE`, not `UNCLEARED`, because the tools cannot tell an open HALT from a retracted one, so whether it
   stands "cannot be verified here" (line 816); line 816 read alone would give `UNCLEARED` for a HALT that stands
   (T3). agentteams 1.3.1 will bind a family HALT to longer ids only across a colon, and the contract's family
   names are joined with `/`; so the tools keep their own family scan after 1.3.1, and agentteams' listing of open
   HALTs will then replace the any-HALT-row rule. Whether the family names should use colons is a proposal for a
   later contract version.
2. **The log's header and schemes** (Q5). The "signature columns" (line 852) become agentteams 1.3.0's exact
   new-log header, and every row of a study's sign-off log is Ed25519. The exact header has no `consumed` column, so
   such a log is refused; a check spends nothing (line 889).
3. **A `build-only` stage refuses when the sign-off folder is malformed** (Q9). The 6.1 table alone says it runs.
4. **Identical manifests are accepted for version 1** (Q10); a repository identity in the manifest is proposed for
   version 2.
5. **A CI job** that installs agentteams and `cryptography` runs the signing tests (its own pull request).
6. **The verifier's location is reported** (N1): inside or outside the work tree, for the package and its
   interpreter.

### Stricter defaults the session adopted on `@security`'s advice (proposals, not operator rulings)

7. **A HALT on a study id that extends another** (`demo-2` against `demo`) binds both (Q2). This differs from lines
   906-907.
8. **A retraction signed with a shared secret never counts** (Q11): the child's `HOME` is empty, so no
   shared-secret key is found, even where the retraction is valid in its own log. This departs from lines 909-910.
9. **Rows signed from a checkout are refused** (Q4; line 840 says the operator signs from a trusted install).
10. **A sign-off row has empty `derives_from`, `scope` and `effect_*` columns** (Q6).
11. **A declared gate with no request is `UNCLEARED`** (Q7), also when the manifest cannot be built (T5).
12. **A request is the manifest file** (Q8). When the covered files are put back to an earlier, signed state while
    the stored request is newer, the gate reads `UNCLEARED` until `survey-manifest` rewrites the request; line 815
    read alone ("a valid signature exists for the current manifest hash") would give `CLEARED`. The rewritten request
    has the signed bytes, so no new signature is needed.
13. **More than one git root above the ledger folder** leaves the gates `UNAVAILABLE` (case 39).
14. **A log agentteams refuses but the tools accept reads `UNCLEARED`** (row 13a), because no message text is
    parsed.
