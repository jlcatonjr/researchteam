# H6 step F: check table (sign-off verification and stage refusal)

Plan: `post-1.3.0-h6-survey-sign-off.plan.md`. Contract: `docs/survey-toolkit.md`, version 1, sections 6.1 and 6.2;
line numbers are that file's. This table is the record of step F. Each row states the tools' own rule and the
contract line it comes from. The tools enforce the contract's rules themselves, in addition to agentteams' check.

The open questions were settled on 2026-11-25:

- some by the operator, the rest by stricter defaults the session adopted on `@security`'s advice (see
  "Proposals");
- `@security` added cases 39 to 46;
- the reviews of 2026-11-25 added S1 to S10 and T1 to T6.

Tests are in `tests/test_survey_verify.py` (step F) and `tests/test_survey_gates.py` (step A, adapted).

- **Signing** tests are named `test_signed_*`. They run only where agentteams 1.3.0 and `cryptography` are
  importable (`tests/survey_signing.py`), and are skipped with the reason elsewhere.
- **Fake** tests use a stand-in verifier. They prove the wiring, not that a signature verifies.

## Definitions (6.2)

- **Scope.** `survey-signoff/<gate>/<study id>` (line 834): the name a clearance is checked under. It is not the
  row's `scope` column (lines 887-888).
- **Action.** `<scope>:sha256-<manifest hash>` (line 834). The manifest hash is the SHA-256 of the manifest file's
  bytes (lines 810-811), and the action is the row's `action_reviewed`. The tools compare the deciding row's action
  with the action they computed exactly, case included.
- **Request.** The manifest file `survey-manifest` writes, `<ledger>/references/<study id>.<gate>.manifest.json`:
  the bytes the operator is asked to sign, and the file agentteams' `--check-clearance … --clearance-file` check is
  given. Its date is the operator's, in the signed row (rule 1.5).
- **Signing.** `survey-manifest` prints the spec and the command:

  ```
  AGENTTEAMS_DECISION_ED25519_KEYFILE=<operator key file> agentteams --sign-decision <spec.json> --output <ledger>
  ```

  Without a terminal, the operator runs it again with `--confirm-review-sha256 <digest>`. It never passes
  `--allow-checkout-signing` and never exports `AGENTTEAMS_DECISION_SIGNING_KEY` (lines 881-886).

## The order (`survey_gates.gate_status`)

1. Not declared: `NOT DECLARED`.
2. The request (stored manifest file) malformed: `UNAVAILABLE`, and a finding.
3. A request whose manifest differs from the one built now, or cannot be built: `UNCLEARED` (line 817, "whether or
   not signatures can be verified").
4. The ledger folder malformed: `UNAVAILABLE`.
5. A reason the HALT scan cannot be made (lines 910-913; case 39): `UNAVAILABLE`.
6. A HALT on a family name in any scanned log (the interim rule): `UNAVAILABLE`.
7. No request: `UNCLEARED`, also when the manifest cannot be built (Q7, T5).
8. agentteams not usable here (absent, as always on Python 3.10; older than 1.3.0; without `cryptography`):
   `UNAVAILABLE` (rule 1.7, line 45; lines 915-917; T1).
9. One snapshot of the folder; then the tools' rules on the deciding row (`UNCLEARED`); then agentteams' check in
   the child, about exactly the computed action; then a second snapshot (any change gives `UNAVAILABLE`).

**Caveat for every row below that reads `UNCLEARED` at step 9** (rows 2b, 3, 5, 6, 8, 9, 9b, 9c, 9d, 10, 12 and case
44): without a usable agentteams the gate reads `UNAVAILABLE` instead, because step 8 comes first (row 14).

## States

| # | Situation | State | The tools' rule (contract line) | Test |
|---|---|---|---|---|
| 1 | A valid Ed25519 row for the current hash, key in the folder, author on the list, request current | `CLEARED` | All of steps 1-9 pass, and the child's answer is well-formed and `cleared` for the exact action (815; 861-865) | `test_signed_a_valid_ed25519_row_clears_through_agentteams`; fake: `test_a_well_formed_row_reaches_the_verifier_and_its_answer_decides` |
| 2 | Only a row for an older hash, request still old | `UNCLEARED` | Stale request (817) | `test_signed_a_covered_file_edited_after_signing_unclears` |
| 2b | The same, request rewritten to the current bytes | `UNCLEARED` (caveat) | No row names the action (815) | same test |
| 3 | No row for the current hash | `UNCLEARED` (caveat) | No row names the action (815) | same; `test_without_agentteams_a_row_the_tools_would_refuse_still_reads_unavailable[…]` |
| 3a | No request, also with a manifest that cannot be built | `UNCLEARED`, with or without agentteams | Q7, T5: nothing to verify; not one of line 816's causes | `test_no_request_is_uncleared_and_never_asks_agentteams`, `test_no_request_and_a_manifest_that_cannot_be_built_is_uncleared`, `test_before_any_request_a_declared_gate_is_uncleared` |
| 4 | A row of any scheme but `ed25519` anywhere in the folder log | malformed (`ledger-scheme`): `UNAVAILABLE`, status 1, validate 1 | Every row must be `ed25519` (861-865; Q5). The shared-secret scheme exists; the tools do not count it (864-865) | `test_every_row_of_the_folder_log_must_be_ed25519` |
| 5 | `key_id` names no key file in the folder | `UNCLEARED` (caveat) | 862; keys from the snapshot (S7) | `test_the_tools_refuse_a_row_that_breaks_their_rules[…op-other…]`, `test_signed_a_row_by_a_key_not_in_the_folder_never_reaches_agentteams` |
| 6 | Author (first of `requesting_agent`, `author`) not on the folder's list | `UNCLEARED` (caveat) | 841-842, 863; list from the snapshot (S7) | `…[…someone-else…]` (two cases) |
| 7 | A waiver file in the folder, also one appearing during the check | malformed (step A): `UNAVAILABLE` | A waiver file is an error (866-868), checked again after the call | step A tests; `test_an_error_file_appearing_during_the_check_is_unavailable` |
| 8 | The latest row for the action is a HALT (folder log) | `UNCLEARED` (caveat) | 894-897 | `test_a_retraction_row_is_skipped_and_the_halt_behind_it_decides` |
| 8a | A HALT on a family name, in any scanned log, either column schema, signed or not, retracted or not | `UNAVAILABLE`: whether it still stands cannot be verified here (816; T3) | The interim rule (Q1). A study's exact scope, optionally with exactly `:sha256-<64 hex>`, is exempt, judged on the raw cell (no strip, no normalisation; B1); a padded one is not. Every other id is squashed (NFKD, non-spacing marks and format characters dropped, lower-cased, only `a-z0-9` kept; S1, A3). It names gate `g` when it contains `surveysignoff<g>`, else every gate when it contains `surveysignoff` | `test_a_family_halt_in_any_scanned_log_blocks_the_gates_it_names` (27 cases), `test_a_family_halt_in_the_other_column_schema_or_the_parent_team_binds`, `test_a_family_halt_in_the_folder_log_binds` |
| 9 | A HALT on this study's exact scope or action in the folder log, any of the five generated team locations, or `parent_team`'s log | `UNCLEARED` (caveat) | 898-905: exempt from the family scan and judged by agentteams' check in the child, which reads all of these logs (A1) | `test_signed_a_halt_in_a_team_log_binds_through_agentteams[ACTION]`, `[SCOPE]`, `test_signed_an_exempt_halt_binds_through_agentteams_in_every_scanned_log` (12 cases) |
| 9b | A row with a non-empty `derives_from` | `UNCLEARED` (caveat) | Q6: `derives_from`, `scope` and `effect_*` must be empty | `…[…derives_from…]`, `[…scope…]`, `[…effect_grants…]` |
| 9c | A HALT on a study id that extends this one (`demo-2` against `demo`) | `UNCLEARED` (caveat); the reason says so | Ids are matched across separators (Q2) | `test_signed_a_halt_in_a_team_log_binds_through_agentteams[EXTENDED]` |
| 9d | A valid PASS for a study id that extends this one (`tidebell-survey-2`), same gate | `UNCLEARED` (caveat) | The deciding row must name exactly the computed action; the child is asked only about it | `test_a_row_for_a_study_id_that_extends_this_one_never_decides`, `test_signed_a_valid_pass_for_a_study_that_extends_this_one_never_clears_it` |
| 10 | A HALT **on the action**, retracted, with no new PASS after it | `UNCLEARED` (caveat) until a new PASS; then `CLEARED` | After a retraction no earlier permission survives: the HALT behind the retraction decides, never an older PASS. For a HALT on the **scope** (not the action): a retracted HALT on the scope in the folder log is not a row for the action, so the older PASS reaches the child, which decides (S6) | `test_a_retraction_never_restores_an_older_sign_off`, `test_signed_a_retracted_halt_on_the_action_needs_a_new_pass` |
| 10a | A retraction signed with a shared secret | It never counts: the child's `HOME` is empty, so no shared-secret key is found (Q11) | — | `test_the_childs_environment_is_an_allowlist`, `test_the_child_runs_isolated_with_an_empty_home` |
| 11 | A `consumed` column in the folder log | malformed (`ledger-log`) | The header's set of columns has no `consumed` column, so such a log is refused; a check spends nothing (852, 889) | `test_a_log_with_an_extra_column_is_malformed` |
| 12 | `CONDITIONAL PASS` with conditions pending | `UNCLEARED` (caveat) | 889-891 | `…[…pending…]` |
| 12a | `CONDITIONAL PASS` verified | `CLEARED` if agentteams' check clears it | 890 | `test_a_verified_conditional_pass_reaches_the_verifier` |
| 13 | Folder log malformed | malformed ledger: `UNAVAILABLE` | Step A, plus the header's set of columns (852) and `ledger-scheme` | step A tests |
| 13c | A header with agentteams' columns in another order; one missing `prev_digest`; one with an extra or repeated column | Any order: well-formed, and every rule reads rows by column name, so a reordered log decides as the written order does. Otherwise: malformed (`ledger-log`), naming what is missing, extra or repeated | 852; operator decision, 2026-11-25 | `test_a_header_only_log_in_any_column_order_is_valid`, `test_a_header_with_another_set_of_columns_is_malformed_and_says_which`, `test_a_row_in_a_log_with_its_columns_reordered_is_read_by_name`, `test_signed_a_signed_row_in_a_reordered_log_still_clears` |
| 13a | agentteams' check does not clear an action whose row passed the tools' rules | `UNCLEARED` | The tools read only the child's `cleared` answer, never its message (Q3) | `test_signed_a_swapped_key_is_not_cleared_by_agentteams` |
| 13b | A team log that cannot be read (link, size, encoding, open quote, width, no action or verdict column, permission) | `UNAVAILABLE`, status 0, reason without a path | 910-913; S4 | `test_a_team_log_that_cannot_be_read_leaves_every_gate_unavailable` (four cases), `test_a_log_that_cannot_be_read_is_reported_without_its_path` |
| 14 | agentteams or `cryptography` absent, or agentteams older than 1.3.0 or not `X.Y.Z` | `UNAVAILABLE` for every gate with a current request. No request and a stale request stay `UNCLEARED`. A blocking stage refuses | Rule 1.7 (45); 915-917; T1 | `test_python_without_agentteams_reads_unavailable_and_blocking_stages_refuse`, `test_without_agentteams_…` (four cases), `test_an_old_or_unreadable_agentteams_version_is_unavailable` |
| 16 | Files changed since the request | `UNCLEARED`, decided first | 817 | `test_a_stale_request_is_uncleared_before_anything_else` |
| 16a | Files put back to a signed state while the request is newer | `UNCLEARED` until `survey-manifest` rewrites the request; then `CLEARED`, with no new signature | Q8 (see proposal 12) | `test_files_put_back_to_a_signed_state_read_uncleared_until_the_request_is_rewritten` |
| 17 | `mode: retroactive` | As prospective; recorded | 828-829; 4.6 | `test_require_gate_records_the_4_6_entry` |
| 18 | `enforce: build-only` | The stage runs and records the state, except when the folder is malformed: then it refuses | 823-826; Q9 | `test_a_malformed_sign_off_folder_refuses_every_gated_stage`, `test_require_gate_records_the_4_6_entry` |
| 19, 20 | Undeclared gate; legacy study | `NOT DECLARED`: refuses, or runs in a legacy study | 820-821 | step A `test_stage_decision_follows_the_6_1_table` |
| 21 | Something changed while agentteams checked | `UNAVAILABLE` | Snapshot before and after | `test_a_change_while_agentteams_checks_is_unavailable` |
| 22 | The child's answer: anything but exit 0 and one JSON object; `cleared` not exactly `true`; another action; version under 1.3.0; module not exactly `<purelib>/agentteams/__init__.py`; another prefix; more than 64 KiB; a grandchild holding stdout | `UNAVAILABLE` (a well-formed `cleared: false` is `UNCLEARED`) | S3, S4, S5 of the first review; S3 of the second | `test_only_one_well_formed_answer_for_the_exact_action_clears` (17 cases), `test_the_childs_stdout_is_read_through_a_bounded_read`, `test_a_grandchild_holding_stdout_open_is_stopped_with_its_group` |

## `@security` cases 39 to 46

| Case | Handling | Test |
|---|---|---|
| 39: more than one git root encloses the ledger folder | `UNAVAILABLE`: the tools read the team logs of the study's repository only | `test_more_than_one_git_root_above_the_folder_is_unavailable` |
| 40: the verifier's own install is patched inside the ignored `.venv`, so no diff shows it | Covered by N1: `survey-status` says whether the verifying package and its interpreter are inside the work tree | `test_the_verifier_location_never_shows_a_home_path` |
| 41: a forged `HALT-RETRACTED` in an unsigned team log lifts a HALT recorded after the sign-off | **Residual; held by review.** It concerns HALTs on a scope or an action in a team log, which agentteams' check in the child judges. A family HALT blocks whether retracted or not | — |
| 42: a specification edit sets `legacy` and removes a gate's declaration; no manifest goes stale, and the stage runs as `NOT DECLARED` | **Residual; flag it in review** | — |
| 43: a plug-in or post-step swapped between the gate check and its run | For the stages that run project code (steps D and G): run only bytes whose hash matches the cleared manifest entry (`require_gate` docstring) | — |
| 44: `key_id` with `/` or `..` | `UNCLEARED` (caveat) | `…[…../op-test…]`, `…[…keys/op-test…]` |
| 45: control or separator characters in a log value | `survey_core.safe` escapes every printed line | `test_status_escapes_every_value_from_a_log`, `test_safe_escapes_controls_and_separators` |
| 46: two study ids that differ only by case | A study id is a lower-case slug, so this cannot occur. Actions are compared exactly, case included | `test_the_newest_row_for_the_action_must_name_it_exactly` |

## Cases that must not clear (a reviewer can extend this list)

| # | Case | The tools' rule |
|---|---|---|
| 1 | A row copied from another study's folder (another study id) | The deciding row must name exactly the computed action |
| 2 | A row for another gate | Same |
| 3 | A row for a study id that extends this one | Same (row 9d) |
| 4 | A manifest of another project, gate or mode | Step A `manifest-malformed`, or a stale request |
| 5 | A row for an older manifest hash | Stale request, or no row names the action |
| 6 | Key file swapped or removed after signing | The child's check fails, or no key file for `key_id` |
| 7 | Approver removed from the list after signing | The author must be on the list the tools read |
| 8 | An empty or comment-only approver list | An error (`ledger-approvers-empty`) |
| 9 | A row of the shared-secret scheme, or with no scheme | Every row must be `ed25519` |
| 10 | A waiver file in the folder | A waiver file is an error; checked again after the call |
| 11 | A HALT on the action or the scope, in any scanned log | Row 8; row 9 |
| 12 | A HALT on a family name, however spelt | Row 8a |
| 13 | A `consumed` column | The header's set of columns refuses it |
| 14 | A `CONDITIONAL PASS` with conditions pending; any verdict but `PASS` or verified `CONDITIONAL PASS` | Row 12 |
| 15 | A row with `derives_from`, `scope` or an `effect_*` value | Row 9b |
| 16 | A row signed from a checkout | The checkout-signing mark is refused (840; Q4) |
| 17 | A `key_id` with a path in it | Case 44 |
| 18 | A later row whose action only starts with the action | The latest row for the action must name it exactly |
| 19 | The request, log, keys or approver list changing during the check | Row 21 |
| 20 | A verifier answer that is not exactly one well-formed object for the exact action | Row 22 |
| 21 | An agentteams on `PATH` from another environment | The child is always the tools' own interpreter, and its prefix must equal the parent's |
| 22 | `AGENTTEAMS_DECISION_SIGNING_KEY` in the caller's environment | The child's environment is an allowlist |

## The child

The child runs `sys.executable -B -I -c survey_verify.CHILD <folder> <scope> <manifest>`.

- **What it runs.** The snippet imports only agentteams' public `clearance_binding.check_file_clearance` and
  `clearance_action`. It prints one JSON line: `version`, `file`, `purelib`, `prefix`, `cleared`, `action`.
- **Its environment** is exactly `PATH=/usr/bin:/bin`, `LC_ALL=C`, and `HOME` = `TMPDIR` = a fresh, empty folder,
  removed afterwards.
- **How it is run.**
  - It runs in a session of its own.
  - `stdin` is closed and `stderr` is discarded.
  - The timeout is 120 s; on it, or on an over-long answer, the whole process group is stopped.
  - `stdout` is read through a bounded read.
- **The empty `HOME`.** agentteams' shared-secret key file lives under `~/.config/agentteams/keys/`, so it is never
  found. Ed25519 verify keys are read from the team directory only.
- **Where the verifier is.** `survey-status` prints whether the verifying package and its interpreter are inside the
  work tree, never a home path (N1).

## Proposals (contract changes; version 2 unless the operator says otherwise)

### Operator decisions (2026-11-25)

1. **Family HALTs: the interim rule** (Q1). Any HALT row on a family name blocks, retracted or not; it reads
   `UNAVAILABLE`, because the tools cannot tell an open HALT from a retracted one. Line 816 read alone would give
   `UNCLEARED` for a HALT that stands (T3).
   - agentteams 1.3.1 will bind a family HALT to longer ids only across a colon, while the contract's family names
     are joined with `/`. So the tools keep their own family scan after 1.3.1.
   - A public listing of a log's open HALTs (asked of agentteams) will then replace the any-HALT-row rule.
   - Whether the family names should use colons is a proposal for a later contract version.
2. **The log's header and schemes** (Q5; header revised by the operator on 2026-11-25): the header holds exactly
   the set of columns of agentteams 1.3.0's new-log header (line 852), each once, in any order, the chain column
   `prev_digest` required; and every row is Ed25519. The set has no `consumed` column, so such a log is refused; a
   check spends nothing (889). Every row is read by column name, so the order changes no rule.
3. **A `build-only` stage refuses when the sign-off folder is malformed** (Q9). The 6.1 table alone says it runs.
4. **Identical manifests are accepted for version 1** (Q10); a repository identity in the manifest is proposed for
   version 2.
5. **A CI job** runs the signing tests (its own pull request; see "What the CI job needs").
6. **The verifier's location is reported** (N1).

### Stricter defaults the session adopted on `@security`'s advice (proposals, not operator rulings)

7. **A HALT on a study id that extends another binds both** (Q2). This differs from lines 906-907.
8. **A retraction signed with a shared secret never counts** (Q11), even where valid in its own log. This departs
   from lines 909-910.
9. **Rows signed from a checkout are refused** (Q4; line 840).
10. **`derives_from`, `scope` and `effect_*` are empty in a sign-off row** (Q6).
11. **A declared gate with no request reads `UNCLEARED`** (Q7), also when the manifest cannot be built (T5). Where
    agentteams is absent this departs from line 917 ("report every gate as `UNAVAILABLE`") (T2).
12. **A request is the manifest file** (Q8). When the covered files are put back to an earlier signed state while
    the request is newer, the gate reads `UNCLEARED` until `survey-manifest` rewrites the request. Line 815 read
    alone ("a valid signature exists for the current manifest hash") would give `CLEARED`.
13. **The family-name match is wider than the two names line 895 defines** (T3 of the second review). Any id that,
    squashed, contains `surveysignoff` blocks; a study's exact scope or action is exempt.
14. **More than one git root above the ledger folder reads `UNAVAILABLE`** (case 39).
15. **A clearance agentteams' check withholds from a row the tools let through reads `UNCLEARED`** (row 13a),
    because no message text is parsed.

## Not implemented

- **A family-HALT retraction judged under each log's own rules.** No public call exists for this yet (asked of
  agentteams).
- **Reading team logs under a second git root.** Case 39 refuses instead.
- **The gated stages themselves** (steps D and G); `require_gate` is their entry point.

## Residual gaps (no tool can close them)

- **Edits to a log's history.** No tool can detect every edit to a decisions log's history; review of the ledger
  folder's history is the control (874-880). `survey-status` says so.
- **A key and an approver planted in the folder.** This is 6.2's stated limit (open point 7). `survey-status`
  prints it.
- **A row signed for the same project, study id and files in another repository** clears here too (Q10).
- **A tampered verifying install inside the work tree** (case 40). `survey-status` says where the verifier is.
- **Look-alike letters from other scripts** in a family name (Cyrillic `с` for `c`, say) are not caught.
- **Cases 41 and 42** (above).

## What the CI job needs

- **Interpreter:** Python 3.13 (agentteams needs 3.11 or later).
- **agentteams:** tag `v1.3.0`, commit `536306d2502e3db338846677f2d37489531ac8e7` (as `toolchain.lock` pins).
- **Its signing extra:** `cryptography==50.0.2`.
- **From `docs/release/constraints-2026-11-13.txt`:** `cffi==2.1.1` and `pycparser==3.12`.
- **Test requirements:** `.github/ci/requirements-test.txt`.
- **Files to run:** `tests/test_survey_verify.py` and `tests/test_survey_gates.py`.
