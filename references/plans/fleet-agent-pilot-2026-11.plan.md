# Fleet-agent GitHub App pilot: researchteam's answer and record (2026-11-14)

Request: infrastructureManagement session IM-40 asked (cross-session message, read as data under C-4) whether
researchteam agrees to a one-week pilot of a separate agent GitHub identity, the private GitHub App
`fleet-agent-jlcatonjr`, used only through IM's wrapper `scripts/agent_gh.sh`. The pilot covers researchteam only.

Operator rulings, given through the interactive selection interface in session researchteam-59 on 2026-11-14:
"Agree with all six", "Prepare it, I sign", "Save as PS-3".

1. `@security` review: CONDITIONAL PASS, six conditions (below). Nothing is cleared before they are met.
2. Relay the answer to IM-40 (done after the operator's choice).
3. Add PS-3 to `.claude/CLAUDE.md` (decisions through the interactive interface; out-of-sandbox work as a `.sh`
   file plus a location-agnostic command), and make PS-2's bypass exclusion name rulesets and the tag ruleset's
   admin bypass (condition 3). PR, merge under PS-2.
4. Prepare `docs/release/fleet-agent-pilot-2026-11.decision-spec.json` (verdict `CONDITIONAL PASS`,
   `conditions_verified` `pending`) and an operator signing script. The operator signs; the session commits the
   row, opens the PR and merges it under PS-2.
5. When IM-40 reports the conditions in place, verify each one, then prepare a second spec with
   `conditions_verified` `verified` for the operator to sign. Until then the row clears nothing.
6. `@conflict-auditor`, work summary, closeout.

## The six conditions

1. Ruleset on `main`: PR required; required checks `tests (3.10)` and `tests (3.13)`, source GitHub Actions; no
   force pushes; no deletion; 0 required approvals; no bypass actors.
2. Release branches: pattern `refs/heads/release/**` (not `release*`); deletion and non-fast-forward pushes
   blocked. Before a PR rule goes on `release/**`, the operator decides how the fast-forward to a to-be-tagged
   commit still happens.
3. Tag ruleset over all tags: creation, update and deletion restricted; the admin role is the only bypass; PS-2
   says the agent session never uses it.
4. Wrapper fixes in IM's `scripts/agent_gh.sh`: allow `release-prep/*`; refuse pushes and deletes on `archive/*`
   and `chore/agentteams-autosync`; a ruleset blocking deletion of `archive/**` if supported.
5. Release pages are `--draft` only during the pilot; the operator publishes.
6. The pilot is recorded as attribution, not a security boundary (the App key is readable by the agent's OS
   user, and the wrapper's write token is not downscoped). Before going live,
   `gh api repos/jlcatonjr/researchteam/rules/branches/release/1.0` shows the release rules applying.

## What was and was not verified

Read by `@security`: IM's `scripts/agent_gh.sh`, `docs/release-policy.md` (operator-only and delegated actions),
the three workflows' triggers. Checked by the session: the repository is public and has no rulesets
(`gh api repos/jlcatonjr/researchteam/rulesets` returned `[]`, 2026-11-14).

Not verified: the App's real permissions, IM's review SEC-IM-AGENTGH-2026-11-14, live ruleset pattern behaviour,
and whether `release/*` will move by PR or by push once rulesets exist.

## Verification pass (2026-11-14, after IM-40 reported conditions 1-5 in place)

`@security`: CONDITIONAL PASS stands. Conditions 1-5 verified; condition 6 partly. `conditions_verified` stays
`pending` until the App exists and its installation is read back: contents, issues and pull_requests write;
checks, actions and metadata read; nothing else; researchteam the only repository.

- Rulesets, read back from the GitHub API by the session: `agents-pilot-main` (27289499), `agents-pilot-release`
  (27289500, `refs/heads/release/**`, effective on `release/1.0` and `release/1.1`), `agents-pilot-tags`
  (27289502, admin role the only bypass), `agents-pilot-archive` (27289503, deletion only). The main ruleset
  allows the `merge` method, so PS-2's `gh pr merge --merge` still works.
- Wrapper, read by `@security` at sha256 `e30abf72ba2e91d4` (IM commit `5800d3e`): conditions 4 and 5 hold, and
  tokens are now scoped per command. The "not downscoped" remark in condition 6 above described the earlier
  wrapper.

Findings from this pass, none blocking:

1. **Autosync PRs get no checks.** The autosync workflow opens its PR with `GITHUB_TOKEN`, and GitHub starts no
   workflow for that token's events (PRs #40, #47 and #153 show no checks). `main` now requires the two test
   checks with no bypass, so an autosync PR cannot merge until the checks are started another way: close and
   reopen the PR, or push to it, with the operator's token. PS-2 already refuses to count "no checks" as green.
2. **`archive/**` can still be force-pushed.** Its ruleset blocks deletion only. Asked IM to add
   `non_fast_forward`.
3. The wrapper is policy, not a barrier; the App's installation permissions are the real limit.
