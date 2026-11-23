# Plan: a standing authorization for the fleet-agent GitHub App, and an exception cap of two (2026-11-22)

**This plan approves nothing.** The signature, the registry change and the merge are the operator's.

Operator rulings in this session's picker, 2026-11-22:

- The pilot row `fleet-agent-pilot-2026-11` is not re-signed in the key rotation and lapses when `op-2026` is
  retired. A new authorization under a new id replaces it.
- First: raise the exception cap to two. After the reviews, a second picker with the narrower options the
  first had not offered: **the cap is two only until 2027-02-18**, the row expires that day (the day the
  branch-deletion exception ends), and the cap returns to one in the step that ends them.
- Signing day: 2026-11-23.

The managing repository's coordinator supplied the wording of the operator's ruling of 2026-11-21, asked for
Tier 1 only with no merges and an expiry, and checked the action list against its wrapper (data). The
authority here is the operator's own answers.

## Reviews of the first draft (2026-11-22)

- **`@security`: CONDITIONAL PASS on the draft.** Adopted: the installation's repository condition restored;
  the relaxed rule named correctly (the role split of the "GitHub management" section); a C-4 clause; the
  App's permissions rest on the operator's read-back at the script's prompt; the merge part of the relayed
  ruling marked not adopted; the push and release wording made exact; a wider basis clause; an incident
  clause; the cap's reason recorded in the row. Not adopted: `effect_targets` naming the repository, because
  the signer reads that field as file write targets; it stays empty, as in the pilot row.
- **`@adversarial`: CONDITIONAL.** Adopted: the cap bound to the row's expiry; "no precedent" wording; the
  term aligned with the other exception. Its preferred alternative (a grant-only row with the cap at one) was
  put to the operator with the others; `@security` had found the rule the row relaxes, and the operator chose
  the relaxing row with the bounded cap.

## What is recorded

- **Decision row** `fleet-agent-tier1:jlcatonjr/researchteam` (spec: `docs/release/fleet-agent-tier1.decision-spec.json`):
  PASS, derives from `release-policy-1.0`, grants `fleet-agent-jlcatonjr`, relaxes its own action id, signed
  with `opr-2026-11`, dated 2026-11-23, expiring 2027-02-18.
- **Registry:** `cap.max_active_relaxing` set to 2 (until 2027-02-18) in `.github/agents/references/exception-registry.json`; one
  new active entry for the row, bound to it by hash, with the same expiry. The branch-deletion entry is
  untouched.
- **Not changed:** PS-2 (the App does not merge here), the rulesets, the key stores, the toolchain-group file.

## Steps

1. Spec and this plan on a draft PR.
2. `@security` reviews the spec and the cap change. `@adversarial` challenges the cap change.
3. The coordinator checks the spec (data in, data out).
4. The operator names the signing day; the spec's date and expiry are set to it.
5. An operator script (`references/plans/archive/2026-W47/operator/26-sign-fleet-agent-tier1.sh`): the operator's
   read-back of the App's installation, the signature, then the cap and the registration in one step, and an
   audit. `@security` reviews it. The tracked copy has placeholders for the signer and the key; the copy the
   operator runs is outside the tracked tree.
6. The operator runs it; the session verifies, commits the log and the registry, and asks for the merge.
7. Later, tracked in the steps file: the cap returns to one by an operator script, on 2027-02-18 or as soon as
   either exception ends; and a pointer to this row goes into the Project-Specific Rules before the App's first
   write under it.

Steps: `fleet-agent-tier1-2026-11.steps.csv`.
