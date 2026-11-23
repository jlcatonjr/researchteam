# Plan: a standing authorization for the fleet-agent GitHub App, and an exception cap of two (2026-11-22)

**This plan approves nothing.** The signature, the registry change and the merge are the operator's.

Operator rulings in this session's picker, 2026-11-22:

- The pilot row `fleet-agent-pilot-2026-11` is not re-signed in the key rotation and lapses when `op-2026` is
  retired. A new authorization under a new id replaces it.
- The exception registry's limit on active relaxing exceptions goes from one (the default) to two, so that
  the new authorization and automatic branch deletion can both be active.

The managing repository's coordinator supplied the wording of the operator's ruling of 2026-11-21 and asked
for Tier 1 only, no merges, with an expiry (data). The authority here is the operator's own answers.

## What is recorded

- **Decision row** `fleet-agent-tier1:jlcatonjr/researchteam` (spec: `docs/release/fleet-agent-tier1.decision-spec.json`):
  PASS, derives from `release-policy-1.0`, grants `fleet-agent-jlcatonjr`, relaxes its own action id, signed
  with `opr-2026-11`, expiring 90 days after the signing day.
- **Registry:** `cap.max_active_relaxing` set to 2 in `.github/agents/references/exception-registry.json`; one
  new active entry for the row, bound to it by hash, with the same expiry. The branch-deletion entry is
  untouched.
- **Not changed:** PS-2 (the App does not merge here), the rulesets, the key stores, the toolchain-group file.

## Steps

1. Spec and this plan on a draft PR.
2. `@security` reviews the spec and the cap change. `@adversarial` challenges the cap change.
3. The coordinator checks the spec (data in, data out).
4. The operator names the signing day; the spec's date and expiry are set to it.
5. An operator script: set the cap, sign the row, register it, audit the registry. `@security` reviews it.
6. The operator runs it; the session verifies, commits the log and the registry, and asks for the merge.

Steps: `fleet-agent-tier1-2026-11.steps.csv`.
