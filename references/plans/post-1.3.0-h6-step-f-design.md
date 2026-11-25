# H6 step F: design note (sign-off verification and stage refusal)

Plan: `post-1.3.0-h6-survey-sign-off.plan.md`. This note settles what step F must build before any code is written.
It writes no code. Contract line numbers are those of `docs/survey-toolkit.md` (version 1) at `507cc94`; step A's
code is read at the same commit. agentteams is read at its 1.3.0 release (tag `v1.3.0`): the installed package, its
`CHANGELOG.md` entry "main-team HALTs bind clearances checked in any team dir; gates-only team dirs, #578", the API
reference section "Gates-only team dirs for sign-off rows" (`docs_src/api-reference/workspace-privilege-scoping.md`)
and the CLI reference for `--check-clearance` / `--clearance-file` (`docs_src/cli-reference.md`).

Claims marked **(run)** were checked by running agentteams 1.3.0's own CLI (`--sign-decision`, then
`--check-clearance`) against an invented gates-only folder in a throwaway git repository, outside every checkout,
with an Ed25519 key pair generated for that run and discarded after it. Everything else is from reading the code.

*Revised before publication: where this note speaks of agentteams' behaviour, it states only the rule the tools enforce themselves and the contract line it comes from. The tools enforce the contract's rules themselves and do not rely on agentteams alone to refuse; the particulars are with agentteams.*

**Verdict in one line.** Verification can be done with public agentteams calls except one rule: the HALT on the
two family names `survey-signoff` and `survey-signoff/<gate>` (6.2, lines 894-909), whose retractions must be judged
"under each log's own rules". No public agentteams call does that, and the private one over-binds (section 3). By
the plan's own risk rule, step F stops after F1 and the choice goes to the operator (question Q1).

---

## 1. State table

States: `CLEARED`, `UNCLEARED`, `UNAVAILABLE` (6.1, lines 815-818), and `NOT DECLARED` (4.6, line 570).
Exit behaviour of the commands does not change with the state (section 7, lines 925-926 and 941-943):

- `survey-status` exits 0 in every state. It exits 1 only when the specification, a manifest file or the ledger is
  malformed, and 2 on a usage error.
- `survey-validate` does not judge gate state. It exits 1 on a malformed specification, row file, ledger or manifest
  file, and 0 otherwise.
- A **gated stage** (4.5, 6.1) applies `stage_decision`. With `blocking`, it runs only when the gate is `CLEARED`;
  otherwise it exits non-zero and writes nothing (rule 1.2, lines 28-29). With `build-only`, it runs in every state
  and its provenance record (4.6, lines 555-556) carries `state`, `mode`, `enforce` and `manifest_sha256`.

In the table, "status 0/1" and "validate 0/1" are the exit codes; "blocking refuses" means a `blocking` stage
refuses, and a `build-only` stage runs and records the state.

**The order question (6.1, lines 815 and 817-818), settled.** A *request* is the manifest file that `survey-manifest`
writes beside the log (`<ledger>/references/<study id>.<gate>.manifest.json`). It holds the bytes the operator is
asked to sign. It is also the file `agentteams --check-clearance … --clearance-file` hashes to form the action it
looks up (`clearance_binding.clearance_action`). The agentteams side of the request is the signed row whose
`action_reviewed` names that file's hash, and whose `date` the operator gives (rule 1.5, lines 38-39). So:

1. When a stored request exists and differs from the manifest built now, or the manifest cannot be built now, the
   gate is `UNCLEARED`. This is decided with the standard library before agentteams is consulted, "whether or not
   signatures can be verified" (line 817).
2. Otherwise the signature is looked up for the request's bytes, which are then exactly the current manifest. So
   "a valid signature exists for the current manifest hash" (line 815) is what is checked.

The two lines fit because verification goes through the request: a signature over the current hash is found only
when the request is current. One corner gives way to line 817. If the covered files are put back to an earlier state
that was signed, while the stored request is newer, the gate reads `UNCLEARED` until `survey-manifest` rewrites the
file. The rewritten file has the old, signed bytes, so no new signature is needed. Q8 asks the operator to confirm
this reading.

The gate state is decided in this order (step A's order, with steps 7 to 9 new):

1. Not declared.
2. Stored manifest file malformed.
3. Stale request.
4. Ledger malformed.
5. The HALT scan cannot be made (`ledger.unavailable`).
6. The manifest cannot be built.
7. The verifier is unavailable.
8. No request.
9. Verify.

| # | Situation | State | status / validate / stage | Contract | How step F decides it |
|---|---|---|---|---|---|
| 1 | An Ed25519 row for the current manifest hash, `key_id` naming a key file in the folder, author on the folder's approver list, latest matching row, no binding HALT, stored request equal to the current manifest | `CLEARED` | status 0, validate 0; the stage runs | 815; 861-865; 841-842 | agentteams `check_file_clearance` returns cleared **and** the tools' own check of the latest matching row (`sig_scheme` is `ed25519`) passes **and** nothing read changed during the check |
| 2 | Only a row for an **older** manifest hash | `UNCLEARED` | 0 / 0 / blocking refuses | 817-818; 889-890 | If the stored request is older: step 3 (stale request), without agentteams. If the request was rewritten to the current bytes: agentteams finds no PASS for the new action **(run)** |
| 3 | **No row** for the current hash (request current) | `UNCLEARED` | 0 / 0 / blocking refuses | 815 | agentteams: "no matching PASS decision" **(run)** |
| 3a | No request yet (no manifest file), agentteams usable | `UNCLEARED`, reason "no sign-off request: run survey-manifest" | 0 / 0 / blocking refuses | 815 (Q7) | Step 8. Step A reported `UNAVAILABLE` here only because it could verify nothing |
| 4 | A row with a **non-Ed25519 scheme** (the shared-secret HMAC scheme), anywhere in the folder log | malformed ledger (operator decision Q5) | status 1, validate 1; blocking refuses | 861-865 | **The tools' own rule:** every row must be `ed25519`. 6.2 (line 864) notes that agentteams also accepts a shared-secret row; the tools do not count one |
| 5 | `key_id` names a key **not in the folder**: missing, or present only in a team dir | `UNCLEARED` | 0 / 0 / blocking refuses | 862 | agentteams loads the key from the folder's store only ("no Ed25519 verify key …") **(run)**. A key file that exists but cannot be read leaves the gate `UNAVAILABLE` (step A already reads every key file) |
| 6 | Author **not on the approver list** | `UNCLEARED` | 0 / 0 / blocking refuses | 841-842, 863 | agentteams author check against the folder's `security-approvers.txt` **(run)**. An empty or comment-only approver list is an error (`ledger-approvers-empty`). |
| 7 | A **waiver file** in the folder | `UNAVAILABLE` | **status 1, validate 1**; blocking refuses (build-only: Q9) | 866-868 | **The tools' own rule:** a waiver file is an error (step A's `ledger-waiver`), checked again after the agentteams call |
| 8 | Unretracted **HALT in the folder's own log** on the action or the scope | `UNCLEARED` | 0 / 0 / blocking refuses | 894-897 | agentteams **(run)** |
| 8a | The same, on `survey-signoff` or `survey-signoff/<gate>` | `UNCLEARED` | 0 / 0 / blocking refuses | 895, 907-909 | **The tools' own check** (agentteams does not bind a shorter name **(run)**). Needs Q1 |
| 9 | Unretracted HALT in a **repository team log** (the five generated locations under every enclosing `.git` root, and `parent_team`) **on the action or the scope** | `UNCLEARED` | 0 / 0 / blocking refuses | 898-905 | agentteams `halt_scan_dirs` and `check_file_clearance` **(run)** |
| 9a | … **on a family name** | `UNCLEARED` | 0 / 0 / blocking refuses | 907-909 | The tools' own check. Needs Q1 |
| 9b | … **on an ancestor** named in the sign-off row's `derives_from` | Not reachable: a sign-off row with a non-empty `derives_from` is refused (Q6). | — | not in the contract | — |
| 9c | HALT on **another study** whose id extends this one with `-` or `_` (a HALT on `…/S0/demo-2` against study `demo`) | `UNCLEARED` (over-binding) | 0 / 0 / blocking refuses | 906-907 say a HALT on another action does not bind | agentteams' `action_matches` prefix rule **(run)**. Fails safe, but differs from the text (Q2) |
| 10 | The HALT is **retracted** by a `HALT-RETRACTED` row that is valid in its own log | As if there were no HALT, except that a HALT on the **exact action** stays the latest decision for it, so the gate is `UNCLEARED` until a **new** Ed25519 PASS follows the retraction | 0 / 0 / per state | 910 | agentteams for the action and the scope; Q1 for the family names. A retraction that is unsigned in a signing-active log, has no evidence, or comes from an unapproved author retracts nothing |
| 11 | A `consumed` mark in the folder log | malformed ledger | status 1, validate 1; blocking refuses | 852, 889 | **The tools' own rule:** the exact header has no `consumed` column, so such a log is refused; a check spends nothing (line 889) |
| 12 | **CONDITIONAL PASS**, conditions `pending` | `UNCLEARED` | 0 / 0 / blocking refuses | 890-891 | agentteams **(run)** |
| 12a | **CONDITIONAL PASS**, `conditions_verified = verified`, Ed25519 and otherwise valid | `CLEARED` | 0 / 0 / runs | 890 | agentteams, plus the tools' scheme check |
| 13 | **Malformed folder log**: fails step A's structure | `UNAVAILABLE` | **status 1, validate 1** | 816-817, 910-913 | step A `ledger-log` (step F extends the structure: section 6) |
| 13a | Folder log passes the tools' structure but agentteams refuses it | `UNCLEARED` (the tools read only the child's `cleared` answer, never its message) | status 0, validate 0 | 816-817 | A gate state, not a finding, so that exit codes never depend on whether agentteams is installed. The tools' stricter structure makes this rare |
| 13b | A **team log** (generated location or `parent_team`) unreadable or malformed | `UNAVAILABLE` | status 0, validate 0 | 910-913 | The tools pre-check every scanned log with the standard library (and with `check_log` when agentteams is present). Step A proposal 20 keeps exit 0 |
| 14 | **agentteams absent** from the tools' interpreter, or `cryptography` absent | `UNAVAILABLE` (or `UNCLEARED` when there is no request or the request is stale). *Revised after review (T1): this is decided before rows 3, 5, 6 and 12, which read `UNCLEARED` only where agentteams is usable* | 0 / 0 / blocking refuses | 1.7 (44-46); 816 | `importlib.metadata.version("agentteams")` and `importlib.util.find_spec("cryptography")`, standard library, with no import of agentteams |
| 15 | **agentteams older than 1.3.0**, or a version that cannot be parsed | `UNAVAILABLE`, with the version in the reason | 0 / 0 / blocking refuses | 915-917 | Same lookup. `1.3.0` or later, by leading integers; anything else fails closed |
| 16 | **Files changed since the request** (or a covered file now missing) | `UNCLEARED` | 0 / 0 / blocking refuses | 817-818 | Step 3 of the order, standard library only, before the ledger and before agentteams (step A's test `test_uncleared_holds_even_when_the_ledger_is_malformed` stays true) |
| 17 | `mode: retroactive` | As for prospective | status prints the mode; outputs record it | 828-829; 4.6 | `mode` is a field of the manifest, so a change of mode is a stale request (row 16) |
| 18 | `enforce: build-only` | Any | 0 / 0 / **the stage runs** and records `state`, `mode`, `enforce`, `manifest_sha256` | 823-826; 4.6 | `stage_decision` (unchanged) |
| 19 | **Undeclared gate** | `NOT DECLARED` | status prints it, 0 / 0 / the stage refuses | 820-821 | unchanged |
| 20 | Undeclared gate in a **legacy study** | `NOT DECLARED` | 0 / 0 / the stage runs and records `NOT DECLARED` | 820-821; 4.6 line 570 | unchanged. A declared gate in a legacy study follows rows 1-18 like any other |
| 21 | A reason the HALT scan cannot be made (team dir through a link, the `parent_team` causes) | `UNAVAILABLE` | status 0, validate 0 (step A proposal 20) | 910-913 | Step A's `ledger.unavailable`. With agentteams present, `halt_scan_dirs` raising is a second source of the same state |
| 22 | Something read during the check (the request, the folder log, the key store, the approver list, the folder's files) **changed between the tools' read and agentteams' read** | `UNAVAILABLE`, reason "changed during the check; run again" | 0 / 0 / blocking refuses | 1.2 | Hash before and after the agentteams call |

---

## 2. What "a request" and "the action id" are (6.2)

- **Scope.** `survey-signoff/<gate>/<study id>` (line 834): the name a clearance is *checked* under
  (`--check-clearance SCOPE`). It is never the row's `scope` column (lines 887-888).
- **Action id.** `<scope>:sha256-<manifest hash>` (line 834), where the manifest hash is the SHA-256 of the manifest
  file's bytes, line feed included (lines 810-811). It is the row's `action_reviewed`.
- **How the hash is bound.** Only through `action_reviewed`, which is the second field of the signed payload.
  `--check-clearance` recomputes the hash from the bytes of `--clearance-file` and looks for a row whose
  `action_reviewed` matches by `action_matches`: equal, or equal plus a suffix that starts with one of `-`, `_`, `.`
  or `:`. The suffix decorates; it never names another hash.

  Nothing else carries the hash. There is no digest column for it. The `scope` column may be empty; if it is not
  empty, it must list the action exactly (`decision_log._scope_permits`). The `text_digest` column binds the free
  text (`conditions`, `evidence`), not the manifest.
- **The request.** The manifest file `survey-manifest` writes: `<ledger>/references/<study id>.<gate>.manifest.json`
  (step A, proposal 1). Its `date` lives in the operator's signing spec and the signed row, never in a tool's output
  (rule 1.5).
- **The fields of a sign-off row** as `--sign-decision` writes it **(run)**:

  | Field | Value |
  |---|---|
  | `date` | given by the operator |
  | `action_reviewed` | the action id |
  | `verdict` | `PASS` by default, or `CONDITIONAL PASS` with `conditions_verified` = `verified` |
  | `author` | a name on the folder's approver list |
  | `key_id` | the stem of `<key_id>.pub.pem` in the folder's `authorized-verify-keys/` |
  | `sig_scheme` | `ed25519` (set by agentteams) |
  | `prev_digest` | the chain tip (set by agentteams) |
  | `text_digest` | set by agentteams |
  | `signature` | the hex Ed25519 signature |
  | `derives_from`, `scope`, `effect_*` | empty |

  Every row of the folder log must be `ed25519` (Q5).
- **The operator's signing command.** Line 881 of the contract gives it; `survey-manifest` today prints only the
  scope, the action, the mode and the verify command. Step F makes `survey-manifest` also print the spec (to stdout,
  writing no file) and this command:

  ```
  AGENTTEAMS_DECISION_ED25519_KEYFILE=<operator key file> \
    agentteams --sign-decision <spec.json> --output <ledger folder>
  ```

  where `<spec.json>` is

  ```
  {"action_reviewed": "survey-signoff/<gate>/<study id>:sha256-<manifest hash>",
   "author": "<approver>", "date": "<YYYY-MM-DD>", "key_id": "<key_id>", "evidence": "<what was reviewed>"}
  ```

  - **Without a terminal.** The first run prints the payload and a review digest and refuses before it reads the key.
    The operator then runs it again with `--confirm-review-sha256 <digest>` **(run)**.
  - **What the handoff script never uses.** It never passes `--allow-checkout-signing`, which is recorded in the
    signed `conditions_verified` as `signed-from-checkout (--allow-checkout-signing)` **(run)**. It never exports
    `AGENTTEAMS_DECISION_SIGNING_KEY` (lines 884-886).
- **The verify command** (step A prints it; run from the repository root):

  ```
  agentteams --check-clearance <scope> --clearance-file <ledger>/references/<study id>.<gate>.manifest.json \
    --output <ledger>
  ```

  It exits 0 when cleared, 1 when not cleared and 2 on a usage error. The reason is printed as text only.

---

## 3. The agentteams calls verification needs

What counts as public is agentteams' own rule (`agentteams/_api_surface.py`, the surface `api_impact` tracks for
breaking changes): a module-level name without a leading underscore, `__all__`, and every CLI option. The
`clearance_binding` and `security_gate` modules have no `__all__`, so their names without an underscore are public
by that rule. A name with an underscore is private, whatever re-exports it.

| Call | Public? Evidence | What it checks | Public equivalent |
|---|---|---|---|
| `importlib.metadata.version("agentteams")` (standard library) | n/a (no agentteams import) | installed version (rows 14-15) | — |
| CLI `--check-clearance SCOPE --clearance-file PATH --output DIR` | **public**: CLI flag, CLI reference, API reference "Gates-only team dirs", changelog #578 | everything `check_file_clearance` checks; exit 0/1/2 | — |
| `agentteams.cli.clearance_binding.check_file_clearance(team_dir, scope, path)` | **public**: no underscore, named in the API reference and changelog | the hash of PATH gives the action. HALT on the scope in every scanned dir. HALT on the action in every scanned dir (in the folder through `check_clearance`). Then the folder's latest matching row: scope column, non-eligibility, approved author, Ed25519 verify against the folder's key store, text binding, lineage. Also the chain and `check_log` of every log it reads | the CLI flag above |
| `clearance_binding.halt_scan_dirs(team_dir)` | **public**: no underscore, docstring; named in the module docs, not in the API reference | the list of dirs whose HALTs bind, with the fail-closed refusals (links, `parent_team`) | none (the tools reimplement it in step A; a local parity test compares the two) |
| `clearance_binding.canonical_team_dirs()`, `is_team_dir()`, `clearance_action()` | **public** (no underscore) | the five locations, the team-dir test, the action id | the tools have their own (`TEAM_LOCATIONS`, `is_team_dir`, `action`); parity test only |
| `agentteams.cli.security_gate.check_clearance(output_dir, *, action)` | **public** (no underscore; its docstring presents it as the read-only check) | one dir only: HALT on the action, latest row, authenticity | called inside `check_file_clearance`; not needed directly |
| `agentteams.cli.action_ids.action_matches`, `halt_names_action` | **public** (`__all__`) | the id-match rules | — (needed for the tools' latest-row selection and family match) |
| `agentteams.governance_logs.check_log(path)` | **public** (`__all__`) | a malformed CSV log (width, open quote, swallowed rows) | — (used to classify `UNAVAILABLE` before the clearance call) |
| `agentteams.cli.decision_chain.verify_chain`, `is_chained` | **public** (`__all__`) | the hash chain | not needed by the tools |
| `agentteams.cli.decision_log.SIGNED_DECISION_COLUMNS` | **public** (no underscore) | the signed-log columns | test fixtures and a parity test only |
| `decision_log._assert_no_unretracted_halt(dir, action=…)` | **private** | HALT on an action, retractions authenticated under the log's own rules (author roster, HMAC key or Ed25519 store, the `enforce_decision_signing` switch, evidence), lineage ancestors | **none** |
| `decision_log._open_halt_for`, `_read_decision_rows`, `_decision_signing_active`, `_assert_authorizing_row_is_authentic` | **private** | the parts of the above | none |
| `security_gate._latest_security_decision(dir, *, action)` | **private** | which row is "the latest decision that matches the action" (6.2, line 864) | none; the tools can rebuild the selection with the public `action_matches` (about 15 lines, narrowing only), with a parity test |
| `decision_log._decision_signature_values`, `_DECISION_SIGNATURE_FIELDS`, `_OPTIONAL_SIGNED_AXES` | **private** | the signed payload | none; not needed for verification, only for hand-built test rows (section 4) |
| `signed_ledger.ed25519_verify`, `ed25519_sign`, `canonical_payload` | **public** (`__all__`) | Ed25519 over `\|`-joined fields | — (useless without the private payload builder) |

**What the tools check themselves** (they enforce the contract's rules and do not rely on agentteams alone to refuse):

- Every row of the folder log is `ed25519` (row 4; 6.2, lines 861-865).
- A waiver file is an error, checked again after the call (row 7; 6.2, lines 866-868).
- No unretracted HALT stands on the family names (rows 8a and 9a).
- The folder log has exactly agentteams' new-log header (6.2, line 852).
- Nothing changed during the check (row 22).

All of these can be done with the standard library and public names, **except the retraction rule for family
HALTs.**

**(b) This private name is unavoidable for a faithful implementation:**
`decision_log._assert_no_unretracted_halt` (or its parts `_open_halt_for`, `_read_decision_rows`,
`_decision_signing_active` and `_assert_authorizing_row_is_authentic`).

- **What it would do.** It would check the family names `survey-signoff` and `survey-signoff/<gate>` in every dir
  that `halt_scan_dirs` returns. The contract requires that "a retraction counts only where it is valid in its own
  log" (line 910). Judging that needs each log's roster, its signing state, its HMAC key or Ed25519 store, and the
  evidence rule.
- **Even this call is not faithful.** Its HALT side uses `halt_names_action`, which also matches by token run. So a
  check of `survey-signoff` is bound by a HALT on *any* study's sign-off action, for example
  `survey-signoff/S5/other:sha256-…`. That contradicts "a HALT on some other action does not bind a sign-off"
  (lines 906-907) and makes one study's HALT stop every gate of every study.
- **The smallest alternatives** (operator's choice, Q1):
  1. Ask agentteams for a public read-only call that returns the *unretracted HALT ids* of one team dir under that
     log's own rules, for example `unretracted_halts(team_dir) -> list[(row, action_id)]`. The tools then match the
     family names exactly. This is the clean route, and probably one of the two helpers the session already asked
     for (plan, "Which agentteams calls").
  2. Pin the private call, run through the CLI's interpreter, with a test that fails when its signature or
     behaviour changes, and accept the token over-binding (it fails safe).
  3. Standard library only, matching family HALTs exactly, but counting **no** retraction. A family HALT would then
     be irrevocable short of rewriting history, which C-2 and PS-2 forbid. Not acceptable.
  4. Standard library only, counting a retraction when a later `HALT-RETRACTED` row with the exact id merely
     exists. That can be forged in any unsigned team log. Not acceptable.
- **The CLI does not avoid the private name.** No flag reports HALT state alone. `--check-clearance survey-signoff
  …` always exits 1 (there is no PASS for that action), and only its message text tells a HALT from an absence. It
  also over-binds in the same way.

**Subprocess or optional import (rule 1.7, lines 44-46).** Rule 1.7 says the tools "import nothing outside the
Python standard library" and that verifying a signature "needs agentteams, which is optional". Two readings:

- **A subprocess call to the agentteams CLI** keeps the tools' process standard-library-only, in the letter of the
  rule. It is the interface the contract prints itself (line 883, "or the function behind it"). Run it as
  `[sys.executable, "-I", "-m", "build_team", "--check-clearance", …]` (`build_team` is agentteams' console entry
  module), so that the agentteams found is the one installed for the tools' own interpreter and never a stray one
  on `PATH`.

  Run it with `cwd` set to the repository root and with `AGENTTEAMS_DECISION_SIGNING_KEY` removed from the child's
  environment. That variable makes every log the process touches signing-active (lines 884-886). In the
  verifier, that would stop a team log's valid unsigned retraction from counting under that log's own rules.

  - **Determinism.** The result depends on the same files plus the child's environment, which the tools control.
  - **Cost.** About 0.2 s per call, measured **(run)**: under a second for four gates.
  - **What it can and cannot do.** It reports exit code and message text only. It cannot call `halt_scan_dirs`, so
    the tools keep their own reimplementation and the UNCLEARED/UNAVAILABLE split comes from the tools' pre-checks.
    It cannot do the family-HALT rule either, but neither can an import with public names.
  - **Testability.** Tests use real agentteams through the same path. Absence is simulated with an interpreter
    without agentteams, or a stub of the metadata lookup.
- **An optional import** (`importlib.import_module` inside one function of one module) gives the tools direct
  calls, typed results, `halt_scan_dirs`, and easy tests. But it breaks the first sentence of 1.7 as written, so
  step A's `test_the_code_is_python_3_10_syntax_and_standard_library_only` would need an exception. It also inherits
  the parent's environment variables and warnings.

**Recommendation: the subprocess**, because it is the cleaner reading of 1.7 and isolates the environment. If Q1 is
answered with option 2, the pinned private call runs as a fixed `python -I -c` snippet in the same child
interpreter, so it stays out of the tools' process. On Python 3.10 agentteams cannot be installed (it requires
3.11 or later), so every gate there is `UNAVAILABLE` or `UNCLEARED`, as the plan says.

---

## 4. How tests can create a signed row without any real key

- **A throwaway key pair at run time: yes.** `cryptography` (agentteams' signing dependency) generates an Ed25519
  key in `tmp_path`. The test writes the public PEM to `<folder>/references/authorized-verify-keys/<id>.pub.pem` and
  keeps the private PEM in `tmp_path`. Nothing is committed, and nothing touches the operator's keys or
  researchteam's own team folders.
- **Produce the row with agentteams' own minter.** Use the CLI `--sign-decision <spec> --output <folder>` with
  `AGENTTEAMS_DECISION_ED25519_KEYFILE=<tmp key>`, in two passes. The first pass, with no terminal, prints the
  review digest and refuses before reading the key; the second passes `--confirm-review-sha256 <digest>`. The
  public `operator_signing.sign_decision(...)` and `review_digest(...)` (`__all__`) do the same in-process. A row
  made this way clears through `--check-clearance` **(run)**.
- **The signer-location gate.** agentteams does not refuse a signer *because it is under the home directory*. It
  refuses (criterion a of `signer_location.verify_install_location`) when the package, `sys.prefix` or
  `sys.executable` is inside the current directory, inside a git work tree, or inside an agent-writable root that
  `.claude/settings.json` grants. A virtual environment inside the repository's checkout counts as inside a work
  tree even when git ignores it **(run)**.

  The override is `--allow-checkout-signing` (or `allow_checkout=True`). It is recorded in the signed
  `conditions_verified` as `signed-from-checkout (--allow-checkout-signing)` **(run)**. Tests would therefore pass the
  override. If the operator decides that the tools must refuse rows
  carrying that mark (Q4), the tests can no longer use the minter from the repository's environment, and only the
  next option remains.
- **Building the row directly** with agentteams' own payload builder is what the tests do (`tests/survey_signing.py`
  explains why and how); the payload format is not public, so it is not described here.
- **What runs in CI.** The two test checks install only `.github/ci/requirements-test.txt`, which has neither
  agentteams nor `cryptography`, on Python 3.10 and 3.13.

  **CI can run, with the standard library:**

  - every state that needs no signature: rows 3a, 7, 13, 13b, 14, 15, 16, 19-21;
  - the order of `gate_status`, through the verifier seam, with a fake verifier used only for ordering and never
    to claim that a real row clears;
  - the tools' own checks over invented CSV text: latest-row selection, the Ed25519-scheme rule, exact matching of
    family HALTs, the new structural rules of section 6;
  - the version gate, through a stubbed metadata lookup;
  - `stage_decision`, and a stage's re-hash of what it runs.

  **Skipped in CI, with a stated reason:**

  - `CLEARED` end to end;
  - every case that needs a real signature or agentteams' HALT scan (most of section 5);
  - the parity tests: the tools' latest-row selection against agentteams', `TEAM_LOCATIONS` against
    `canonical_team_dirs()`, and the tools' header rule against `SIGNED_DECISION_COLUMNS`.

  These run locally in the locked environment, and the pull request records the run. `@security` is told that
  they are not covered by CI (plan, "What CI runs"). A CI job with agentteams is the operator's decision (metaplan
  P10).
- **Determinism.** A random key gives different signature bytes on each run. Tests assert states and reasons, never
  signature bytes. Rule 1.5 binds tool outputs, not fixtures.

---

## 5. Cases that must NOT clear

"Who stops it": **at** = agentteams 1.3.0 (**(run)** where it was run); **tools** = a new step F check; **A** =
step A's structural checks; **residual** = not detectable by any tool and held only by review and branch protection
(6.2, lines 874-880; open point 7). A security reviewer can add rows at the end.

| # | Case | Who stops it |
|---|---|---|
| 1 | A row from another study's folder (another study id) copied into this folder | at: the action names the study id |
| 2 | A row from another repository's folder with the **same** project name, study id and covered bytes | **Clears.** The sign-off binds bytes, not a repository (Q10) |
| 3 | A row for another gate (an S5 row against S0) | at: the action names the gate |
| 4 | A manifest whose `project`, `gate` or `mode` differs | stored file of another gate or project: A (`manifest-malformed`). A different `mode`: the hash differs, so the request is stale (row 16) |
| 5 | A row for an older manifest hash | stale request (tools), or no PASS for the action (at) |
| 6 | Key file swapped after signing | at: Ed25519 verification fails **(run)** |
| 7 | Key file removed from the folder, or present only in a team dir | at **(run)** |
| 8 | A key and an approver planted in the folder, with a row signed by that key | **residual** (6.2, lines 874-880; open point 7). Parity with the team's store when the team has keys and approvers (A) |
| 9 | Approver list edited after signing to drop the signer | at **(run)**. Edited to add a new author: residual, as 8 |
| 10 | Approver list empty or comments only | A: an empty or comment-only approver list is an error (`ledger-approvers-empty`) |
| 11 | A row signed with the shared-secret HMAC scheme | **tools**: every row must be `ed25519` (6.2, 861-865) |
| 12 | An HMAC row relabelled `sig_scheme=ed25519` | at: `sig_scheme` is signed, so verification fails |
| 13 | A waiver file in the folder | A and **tools**: a waiver file is an error (6.2, 866-868), checked again after the call |
| 14 | A HALT added after the PASS, on the action or the scope, in the folder log or any team log | at **(run)** |
| 15 | A HALT on `survey-signoff` or `survey-signoff/<gate>` in any scanned log | **tools** (agentteams ignores it **(run)**; Q1) |
| 16 | A HALT in the declared `parent_team`'s log | at (`halt_scan_dirs`) |
| 17 | A team dir, its `references/` or its log reached through a symbolic link; a scanned log unreadable | A and at → `UNAVAILABLE` |
| 18 | A HALT on the exact action, retracted, with no new PASS after it | at **(run)** |
| 19 | A retraction that is unsigned in a signing-active log, carries no evidence, or comes from an unapproved author | at |
| 20 | A `CONDITIONAL PASS` with conditions pending | at **(run)** |
| 21 | Another verdict (`USED`, unknown) as the latest matching row | at |
| 22 | A `consumed` mark in the folder log | **tools**: the exact header has no `consumed` column, so such a log is refused; a check spends nothing (6.2, lines 852 and 889) |
| 23 | (merged into 22) | — |
| 24 | Rows out of date order | Dates are never compared, and file order decides (no clock, rule 1.5) |
| 25 | Edits to a log's history | **residual**: no tool can detect every edit to a log's history; review of the ledger folder's history is the control (6.2, lines 874-880) |
| 26 | Duplicate ids: an earlier PASS and a later row for the same action that is not a valid PASS; a header naming a column twice | at: the latest decides; a duplicated column makes the log malformed |
| 27 | A non-empty `scope` column that does not list the action | at (`_scope_permits`) |
| 28 | `derives_from` naming an id the folder log does not record, or a cycle | at: fails closed. **tools** (Q6): any non-empty `derives_from` |
| 29 | The folder log uses the "current" schema (`decision`, `status` columns), so the latest-row selection becomes ambiguous | **tools** (section 6) |
| 30 | A folder log whose header is not exactly agentteams' new-log header | **tools**: header rule (section 6; 6.2, line 852) |
| 31 | The request file changes between the tools' comparison and agentteams' read | **tools**: re-hash after the call (row 22) |
| 32 | A covered plug-in or post-step changed after the check and before it runs | **tools** (in each stage): a stage runs only bytes whose hash matches the cleared manifest entry |
| 33 | A sign-off row written in a team log instead of the folder | at: the PASS is read from the folder only |
| 34 | A study id long enough that the scope exceeds agentteams' 128-character limit | at: fails closed. **tools**: proposed validator error (section 6) |
| 35 | An `agentteams` on `PATH` from another environment, or one older than 1.3.0 | **tools**: the child is always the tools' own interpreter, and its version is checked |
| 36 | A row with a `\|` in a signed field | at: refused (payload delimiter) |
| 37 | A row signed with `--allow-checkout-signing` | **tools**: a row carrying agentteams' checkout-signing mark is refused (Q4; 6.2, line 840) |
| 38 | `AGENTTEAMS_DECISION_SIGNING_KEY` exported in the verifying shell | **tools**: removed from the child's environment |

---

## 6. Proposed module and function layout

**New `scripts/survey/survey_verify.py`.** The only module that reaches agentteams, through a subprocess
(recommended) or a guarded import (Q3).

- `AGENTTEAMS_MIN = (1, 3, 0)`.
- `probe() -> Verifier | Unavailable`, standard library only:
  - `importlib.metadata.version("agentteams")`, parsed by leading integers and fail-closed;
  - `find_spec("cryptography")`;
  - a child command fixed to `sys.executable -I -m build_team`.
- `Verifier.check_file(folder, scope, request_path) -> (ok, reason)`:
  - runs the child with `cwd` at the repository root, `AGENTTEAMS_DECISION_SIGNING_KEY` removed, and a timeout;
  - exit 0 means `ok`, 1 means not cleared, anything else means unavailable.
- `Verifier.family_halts(dirs, names)`: the Q1 answer. Until Q1 is answered it returns "unavailable: the family-HALT
  rule is not implemented". **Step F cannot report `CLEARED` until Q1 is settled**, which keeps it fail-closed.

**`survey_ledger.py`.** Standard library; the new structural rules make a malformed ledger, so status and validate
exit 1.

- **Header.** The folder log's header must be exactly the one agentteams writes for a new log: `timestamp`,
  `requesting_agent` and then `SIGNED_DECISION_COLUMNS`. At least, it must contain the six legacy required columns
  and `author`, `sig_scheme`, `key_id`, `signature`, `prev_digest` and `text_digest`.
- **No other schema.** No `decision`, `status`, `owner` or `plan_slug` column, and no column named twice.
- **Schemes.** Every row is `ed25519` (operator decision Q5).
- **`derives_from`** is empty on every row whose `action_reviewed` starts with `survey-signoff/` (Q6).

The module also gains helpers:

- `read_log_rows(path)`: a strict `csv` read, capped, regular file only;
- `latest_matching_row(rows, action)`: agentteams' selection, rebuilt with the `action_matches` rule: newest first,
  skip `HALT-RETRACTED`; the tools then require the exact action;
- `family_halt_candidates(rows, gate)`: exact match on `survey-signoff` and `survey-signoff/<gate>`, plus the `-_.:`
  suffix rule;
- the scanned-log pre-check for row 13b.

`LOG_COLUMNS` grows accordingly. The structural rules for team logs stay `UNAVAILABLE` reasons, not findings
(proposal 20).

**`survey_gates.py`.**

- **`verify_signoff` is replaced** by `verify_signoff(study, gate, request_path, current_sha256, ledger, verifier)
  -> (state, reason, evidence)`. `evidence` holds the row number, `key_id` and `author` for `survey-status`. Inside
  it:
  1. Hash the request file, the folder log, the key store and the approver list.
  2. Run the tools' family-HALT check.
  3. Run `check_file`.
  4. Read the folder log's latest matching row and require `sig_scheme == "ed25519"`, a verdict of `PASS` (or
     `CONDITIONAL PASS` with `verified`), and a `key_id` that is among the keys step A read.
  5. Check that the folder still has no waiver file (a waiver file is an error).
  6. Hash again: any difference gives `UNAVAILABLE`.
- **`gate_status`**: the order of section 1 (the "STEP F MUST REVISIT THIS ORDER" comment is resolved there). After
  step 3, "stale request", come: ledger malformed; HALT scan impossible; manifest cannot be built; verifier
  unavailable; no request (`UNCLEARED`); verify.
- `NO_VERIFICATION` goes.
- **New** `require_gate(study, gate, *, legacy) -> (RUNS|REFUSES, record, grant)` for stages. `record` is the 4.6
  `gates` entry. `grant` holds the cleared manifest's entries, so a stage re-hashes each covered file it reads or
  executes and refuses, writing nothing, on any difference (section 5, item 32).
- `stage_decision` keeps its table.

**`survey_status.py`.**

- **Per gate, unchanged:** state, `manifest_sha256`, `enforce`, `mode` and the reason.
- **Per gate, for `CLEARED`:** "signed by `<author>` with key `<key_id>` (ledger log row `<n>`)".
- **One `verification:` line:** "agentteams `<version>` (this interpreter)" or "not available: `<reason>`".
- **The closing note "this version verifies no signature" is replaced by the 6.2 limit, in one line:**

  `note: a CLEARED gate proves that its manifest was signed by a key that was in the ledger folder when the gate was
  checked, by an author on the folder's approver list as it then stood; it does not prove who put the key there
  (6.2; open point 7).`

**`survey_manifest.py`.** It also prints the spec and the `--sign-decision` command of section 2, still writing
nothing but the manifest file (rule 1.4).

**`survey_validate.py`.** Notes only. It still does not judge gate state.

**`survey_spec.py`.** A proposed new error: a study id longer than 128 minus `len("survey-signoff/S0/")` characters
(section 5, item 34).

**Step A files that must change:**

- `scripts/survey/survey_gates.py`;
- `scripts/survey/survey_ledger.py`;
- `scripts/survey/survey_status.py`;
- `scripts/survey/survey_manifest.py`;
- `scripts/survey/survey_validate.py` (notes);
- `scripts/survey/survey_spec.py` (the id-length rule, if accepted);
- `tests/test_survey_gates.py`: `test_before_any_request_a_declared_gate_is_unavailable` and
  `test_the_verification_seam_says_why_it_cannot_clear` change; `test_no_gate_ever_reads_cleared_in_this_version`
  goes;
- `tests/survey_support.py`: `LOG_HEADER` lacks `timestamp,requesting_agent`, so agentteams rejects it as malformed
  **(run)**; add a signing helper that skips without agentteams or `cryptography`;
- `tests/test_survey_core.py` (only if Q3 chooses the import);
- the check table `references/plans/post-1.3.0-h5-step-a-check-table.md` (its "not implemented: step F" rows), or a
  step F table beside it.

The changelog and the scripts reference change as the repository's practice requires. Plus a new
`tests/test_survey_verify.py`.

**Found while reading, and must be fixed in step F whatever Q1 says.** Step A requires the log to exist before
`survey-manifest` will write a request (a missing log is `ledger-log`). Its fixture header, which is what an operator
would copy, is refused by agentteams as malformed. agentteams' `--sign-decision` then also refuses to extend that
log **(run)**. An operator following the fixture could never sign.

---

## 7. Open questions for the operator

- **Q1. The family-HALT rule (6.2, lines 894-910) needs a private agentteams name.** Options:
  - (a) wait for an agentteams release with a public read-only "unretracted HALT ids of a team dir" call, and ship
    step F without `CLEARED` until then; *recommended*;
  - (b) pin `decision_log._assert_no_unretracted_halt` in the child interpreter, with a test that fails when it
    changes, and accept that one study's HALT stops every study's gates (token over-binding);
  - (c) change the contract (version 2) to drop the two family names.
- **Q2. agentteams over-binds across study ids** (a HALT on `…/demo-2` binds `demo`; table row 9c), against lines
  906-907. Options:
  - (a) accept and document it (fails safe); *recommended*;
  - (b) add a validator rule that no study id in the repository extends another with `-` or `_`;
  - (c) ask agentteams for an exact-scope mode.
- **Q3. How the tools reach agentteams.** Options:
  - (a) a subprocess of the tools' own interpreter's agentteams CLI, with a cleaned environment; *recommended*;
  - (b) a guarded optional import in `survey_verify.py`, with an exception to the standard-library test.
- **Q4. Rows signed with `--allow-checkout-signing`.** Options:
  - (a) count them, as agentteams does;
  - (b) refuse them, since 6.2 (line 840) says the operator signs from a trusted install. Tests then need a signer
    installed outside every work tree, or the private payload format.
- **Q5. A stricter folder-log structure** (section 6: agentteams' new-log header, every row `ed25519`). It changes
  a malformed/well-formed verdict, so the first project's log must be checked against it before the merge. Options:
  - (a) adopt it; *recommended*;
  - (b) adopt only the header rule;
  - (c) neither.
- **Q6. `derives_from` on a sign-off row.** Options:
  - (a) refuse any non-empty value; *recommended*;
  - (b) follow agentteams, so ancestors bind only within the folder's own log.
- **Q7. A declared gate with no request while agentteams is usable.** Options:
  - (a) `UNCLEARED`; *recommended*;
  - (b) `UNAVAILABLE`, as step A reports it.
- **Q8. Files reverted to an earlier signed state while the stored request is newer.** Options:
  - (a) `UNCLEARED` until `survey-manifest` rewrites the file, with no re-signing; *recommended*, and the reading of
    section 1;
  - (b) `CLEARED`, which needs a private call path, because the public check hashes a file.
- **Q9. A `build-only` stage when the ledger is malformed.** Options:
  - (a) run and record `UNAVAILABLE` (the 6.1 table);
  - (b) refuse (rule 1.2, "a tool that finds a violation … writes nothing").
- **Q10. Identical manifests in two repositories** (section 5, item 2). Options:
  - (a) accept: a sign-off binds bytes (6.2 as written);
  - (b) add a repository identity to the manifest (contract version 2).
- **Q11. Environment dependence of retractions.** A team log's HMAC-signed retraction verifies only where that
  team's HMAC key is available. A gate can therefore read `UNCLEARED` in CI and `CLEARED` in the operator's shell.
  Options:
  - (a) accept (fails safe) and say so in the status reason;
  - (b) require that HALT retractions in team logs be Ed25519.
- **Q12. A CI job that installs agentteams and `cryptography`** to run the `CLEARED` path (metaplan P10; its own
  pull request to a PS-2 path). Options:
  - (a) add it with step F;
  - (b) local runs recorded in the pull request, as planned.
