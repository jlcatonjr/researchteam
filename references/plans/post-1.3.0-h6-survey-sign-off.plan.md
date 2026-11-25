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
