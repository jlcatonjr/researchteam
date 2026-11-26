# H6: survey tools, step F: sign-off verification and stage refusal (2026-11-25)

Metaplan: `post-1.3.0-high-items.metaplan.md`. This plan carries out step F of `survey-tools-2026-11-23.plan.md`.
The specification is `docs/survey-toolkit.md`, version 1, section 6 (6.1 gates, 6.2 sign-offs, settled on
2026-11-24 against agentteams 1.3.0's gates-only team directory).

## What is built

- **Verification.** H5 step A already builds the manifest, makes the structural ledger checks and reports
  `UNCLEARED` or `UNAVAILABLE`. This step adds the part that needs agentteams: checking the signature over the
  current manifest hash, and the HALT scan of the repository's team logs. Only an Ed25519 row by a key in the
  folder clears a gate (a waiver file there is already an error in step A); an unretracted HALT in the repository's team logs binds
  a study's sign-off. A gate whose files changed since its request stays `UNCLEARED` whatever verifies (6.1).
- **`agentteams` is optional (rule 1.7).** The tools import nothing outside the standard library. Verification
  calls agentteams only when it is importable and is 1.3.0 or later; otherwise a gate keeps the state step A
  gives it (`UNCLEARED` where its files changed, else `UNAVAILABLE`), and a blocking gate in either state
  refuses. On a Python where agentteams cannot be installed (3.10), every blocking stage therefore refuses. An older agentteams is `UNAVAILABLE` with that
  reason, never a silent pass.
- **Which agentteams calls.** Public ones only. The session asked agentteams (through the release coordinator,
  2026-11-24) for public equivalents of two private gate helpers. Step F1 reads agentteams 1.3.0 and lists the
  public calls that are enough. If verification cannot be done without a private name, the step stops there and
  the choice (wait for the agentteams release that adds them, or pin a named private call with a test that fails
  when it changes) goes to the operator with `@security`'s view.
- **Stage refusal.** The function is step A's. This step makes `CLEARED` reachable, so `survey-status` reports
  real states. Its callers are the gated stages of 6.1 and 4.5: H5 step D's post-steps (S6), and later the
  enumeration and packet commands of step G (S0, S5). No command of H5 steps A to C is gated.
- **No tool writes a sign-off or a ledger row** (rule 1.4). `survey-manifest` still writes only the manifest
  file and prints what the operator signs.

## Tests

- An invented ledger folder built by the test in a temporary git repository, with a throwaway key pair
  generated at run time: never a committed private key, never the operator's keys, never researchteam's own team
  folders.
- **What CI runs.** Neither test check installs agentteams, so in CI the tests that need it are skipped with a
  stated reason, and CI covers only the paths without it (`UNAVAILABLE`, `UNCLEARED`, the refusals, the
  structural errors). The `CLEARED` path, which is the one that decides, runs only locally, in the environment
  the lock pins; that run's command and result are recorded in the pull request, and `@security` is told it is
  not covered by CI. Adding a CI job that installs agentteams is the operator's decision (metaplan P10), by its
  own pull request to a PS-2 path.
- Each state of 6.2, each refusal, the HALT rule, an edited covered file un-clearing a
  gate, a key missing from the folder, a non-Ed25519 row, an agentteams older than 1.3.0.

## Reviews

`@security` reviews the whole step: it decides what counts as cleared. Its PASS is required before the pull
request is put to the operator, whatever paths it touches. `@technical-validator` compares each state and
refusal with section 6's text. `@code-hygiene`; `@conflict-auditor`.

## What a clear gate proves, stated in the output

Section 6.2 says what a sign-off proves while its keys live in the repository, and open point 7 of the contract
(a trust root outside the repository) is not solved here. `survey-status` prints that limit in one line, as the
contract words it.

## Depends on

H5 step A merged (the loader, the gate list, the manifest builder, the states, the refusal function, the
structural ledger checks). It does not wait for B to D. It shares the survey core, the fixtures, the manifest and
the bridge script with them, so whichever of B and F merges second merges `main` first and resolves there.

## Risks

- **Private agentteams names** (above): stop and ask, do not copy agentteams' code into the tools.
- **A verification that passes too easily.** The fixture set includes rows that must not clear; `@security` is
  asked for cases the session did not think of before the code is final.
- **The first project's signed gates.** Its session confirmed on 2026-11-24 that its gates stay valid under 6.2.
  After the merge it is asked to run `survey-status` on its study; a gate that reads differently there than its
  own tool reports is a finding for both sides, and data to this session.

Steps: `post-1.3.0-h6-survey-sign-off.steps.csv`.

## Step F1: the design note, `@security`'s read, and the operator's decisions (2026-11-25)

Design note: `references/plans/post-1.3.0-h6-step-f-design.md` on the branch `feat/survey-tools-f` (commit
`e8519c7`). Its claims marked as run were checked against agentteams 1.3.0's own command line with an invented
folder and a throwaway key. `@security` read it: CONDITIONAL PASS; code may start once the operator has answered
six questions; the code gets its own `@security` review.

**Findings that shape the step.**
- The contract's HALT rule for the two family names has no public route in agentteams 1.3.0, and the private one
  binds too widely (one study's HALT would stop every study's gates).
- A sign-off is bound to its manifest only through the signed action id, which carries the manifest's hash.
- agentteams' clearance check is looser than the contract in several respects, so the tools enforce the
  contract's rules themselves and never rely on agentteams alone to refuse. The particulars are with agentteams
  and are not recorded here.
- The folder-log header in step A's test fixture lacks two columns agentteams requires; agentteams rejects such a
  log and will not sign into it. Step A never reports `CLEARED`, so nothing wrong was accepted; it is fixed in a
  small pull request before step F (branch `fix/survey-ledger-log-header`).
- Two gaps no tool can close: rows cut off the end of the log, and a deleted `consumed` mark. Review and branch
  protection hold them; the status output says so.

**Operator's decisions (picker, 2026-11-25).**
- **Family HALT: "Strict interim scan".** The tools read every team log the HALT scan covers and treat any HALT
  row on the two family names as blocking every gate, signed or not, retracted or not; a log that cannot be read
  leaves the gates `UNAVAILABLE`. A retracted family HALT therefore keeps blocking until agentteams offers a
  public call; the session confirms none exists today, says so in the reason text, and asks agentteams for the
  call.
- **Log structure: "Adopt both rules".** A study's sign-off log has the header agentteams writes for a new log,
  and every row is Ed25519. The first project's session is asked to check its log against the rule before the
  merge; if its log would fail, the question returns to the operator.
- **A malformed sign-off folder and a `build-only` stage: "Refuse".** Recorded as a contract proposal, since the
  gate table read alone says the stage runs.
- **Identical manifests in two repositories: "Accept for now".** A known limit of contract version 1; a
  repository identity in the manifest is proposed for version 2.
- **CI: "Add the CI job".** A job that installs agentteams at the pinned commit with its signing backend, so the
  `CLEARED` path runs in CI. Its own pull request to the workflow, with `@security`'s PASS naming the path and
  hash-pinned installs vetted under Rule S-10.
- **Where the verifying agentteams lives: "Report it, do not refuse".** `survey-status` prints the verifier's
  location and whether it is inside the work tree; a gate may read `CLEARED` from such an install, with that note.

**Adopted without asking, as `@security` marked them fail-safe:** a HALT on a study id that extends another
blocks both (accepted, documented); agentteams is reached as a child process of the tools' own interpreter, never
imported; rows marked as signed from a checkout are refused; a sign-off row must have empty `derives_from`,
`scope` and effect columns; a declared gate with no request reads `UNCLEARED`; files put back to an earlier
signed state read `UNCLEARED` until the manifest is rewritten; the child runs with an allowlisted environment and
an empty home folder, so a retraction signed with a shared secret never counts.

**How `CLEARED` is decided.** The child runs one fixed snippet under `-I` that calls agentteams' public
file-clearance check and prints one JSON line. A gate is `CLEARED` only if the child exits 0, prints exactly one
JSON object, says cleared, names the action the tools computed, reports agentteams 1.3.0 or later imported from
the interpreter's own site-packages, and shares the parent's prefix. Anything else is `UNCLEARED` or
`UNAVAILABLE`. No failure text is parsed.

**Cases that must not clear:** the note's section 5, with `@security`'s additions 39 to 46 (a planted `.git`
between the folder and the repository root; a patched verifier; a forged retraction in an unsigned team log; a
specification edited to `legacy` with a gate's declaration removed; a plug-in reading outside what was hashed; a
`key_id` with path characters; control characters in `author` or `key_id`; study ids that differ only by case).

## agentteams 1.3.1 and the family names (relayed 2026-11-25; data)

The managing repository's session relayed the operator's ruling on the scope of agentteams 1.3.1 (no date yet). It
includes the read-only listing of open HALTs this plan asked for. Two of its design rulings bear on step F:

- **After a HALT is retracted, no earlier permission for that action survives;** it must be issued again. For a
  study this means a gate signed before a HALT on its action stays uncleared after the retraction until the
  operator signs again. The tools must not treat a retraction as restoring an older sign-off.
- **A family HALT binds longer ids only across a colon** (a HALT on `x` binds `x:y`, not `x-y`). The contract's
  two family names are joined to the gate and the study id with `/` (`survey-signoff/<gate>/<study id>`), and to
  the manifest hash with `:`. So agentteams 1.3.1's own matcher will bind a HALT on the full scope to its
  hash-bearing action, but it will NOT bind a HALT on `survey-signoff` or `survey-signoff/<gate>` to a study's
  action. **The tools therefore keep their own scan of the two family names when 1.3.1 arrives;** what 1.3.1
  changes is that the scan can use the public listing to tell a retracted HALT from an open one, in place of the
  interim rule that any HALT row blocks. Whether the family names should instead be written with colons is a
  question for a later contract version, recorded as a proposal.

## The first project's check of its signed log (2026-11-25; data)

The first integrating project's session checked its study's sign-off log, read-only, against the rules the tools
on `main` apply. Four gates are signed there with the current decision key.

- **Holds:** every row is Ed25519; each deciding row names the exact action with the manifest hash, has empty
  `derives_from`, `scope` and effect columns, a key in the folder's store and an author on its approver list; no
  waivers file; no HALT row on either family name in any tracked team log. (Whether a row carries the
  checkout-signing mark was not verified there.)
- **Fails rule 1, the exact header.** Its log has the header an earlier agentteams wrote: the same columns as
  the 1.3.0 new-log header except that `prev_digest` is absent, and in a different order. agentteams 1.3.0's own
  public log check accepts that header (checked here on an invented log). Under the operator's decision of
  2026-11-25 ("header as agentteams writes it") the tools read that log as malformed, so none of its four gates
  could read `CLEARED` and `survey-status` would exit non-zero. The decision was conditional on this check, so
  it returns to the operator.
- **Differs on where manifests live.** Its manifests are in a folder of the study, not in the sign-off folder's
  `references/` as the tools write and read them (the tools' location is step A's proposal 1; the contract's text
  does not fix it). With no manifest where the tools look, a gate reads "no request", `UNCLEARED`. The manifests'
  bytes, and so the signed hashes, do not depend on where the files sit.

**Operator's decisions on that check (picker, 2026-11-25).**
- **Header: "Same columns, any order".** The tools require exactly agentteams 1.3.0's set of columns for a study's
  sign-off log, the hash-chain column included, and no longer their order. This replaces the "exact header" half
  of the earlier decision; "every row Ed25519" stands. The first project's log lacks the chain column, so it
  must gain it before its gates can clear; that is done on the project's side, through the managing repository's
  operator scripts, and whether its existing signatures stay valid is confirmed there.
- **Manifests: "Project moves its manifests".** The tools keep one place, the sign-off folder's `references/`.
  The first project copies its manifest files there when it adopts the tools; nothing is signed again, since the
  hashes do not depend on where the files sit. The place stays a contract proposal.

**Follow-up from the first project (2026-11-25; data).** Its study's evidence is in the built-in CSV format, not a
reader plug-in; it does declare a vantage module. So what stops the tools on that study today is the vantage
module (`identity-vantage`), not the evidence reader. An earlier note in this session's reports, that the first
project uses a reader plug-in, was wrong: it came from a reviewer's reading of an example in the contract, not
from the project. The managing repository's session will rehearse agentteams' log migration on a copy of that
project's log when the project decides to adopt the tools, and report whether the existing signatures survive.

**Recorded from `@security`'s read of the header change (pull request #271):** the tools check only that the
hash-chain column is present in the header. The chain's values are verified by agentteams' own check, which the
tools run in the child process; the tools themselves check nothing about them.
