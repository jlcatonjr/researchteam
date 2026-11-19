# P2: release tags that GitHub shows as "Verified"

Written 2026-11-19 by the researchteam agent session, for the agent that takes this over.

## Goal
The next release tag (1.2.1 or 1.3.0) shows GitHub's "Verified" badge, and the cut script proves it.

## State on 2026-11-19 (checked through the GitHub API, read-only)
- `v1.1.9`, `v1.2.0-rc.1` and `v1.2.0` all report `verified=false`, reason **`unknown_key`**.
- All three verify against the release key with `scripts/check_toolchain.py --verify-tag`. The signatures are
  good; only GitHub's display is affected.
- **Cause found.** The account's public key lists show the release key (fingerprint ending `…qxnzTNM`)
  registered as an **authentication** key only. The one **signing** key on the account is a different key.
  GitHub therefore cannot match the tag signature to the account, whatever the tagger email is.
- The release coordinator reported the cause as the checkout's local `user.email` not being tied to the
  operator's GitHub account, and relayed an operator ruling: fix forward only, the existing tags stay, and the
  operator sets the local email. That ruling was given in another session, and the email is the second
  condition, not the first. Both points go to the operator at Gate 1.

## What GitHub needs for the badge
(a) the signing key registered on the tagger's account as a **signing** key, and (b) a tagger email that is a
verified address of that account. (a) is unmet today. (b) is not yet checked.

## Steps
1. **Check condition (b), read-only.** Read the tagger email of `v1.2.0` from the tag object and say whether
   it can be a verified address of the account. Do not print a personal address into any tracked file.
2. **Operator decisions.** Two were answered in the authoring session's picker on 2026-11-19:
   - **Signing key: "Prepare the script".** The next agent writes and hands over the registration script
     (step 3). The answer covers preparing the script; running it is the operator's act.
   - **Tagger email: "GitHub no-reply address".** The cut script requires the account's GitHub-provided
     no-reply address. Read its exact form from the account (it may carry a numeric id prefix); do not guess.

   One remains for Gate 1: confirm "fix forward only: the existing tags stay". The options as first put:
   - Register the release key as a signing key on the GitHub account? It is an account setting, so the
     operator does it; the agent prepares a script with one command (PS-3), reviewed by `@security`. The
     script reads the public key only and prints its fingerprint.
   - Which tagger email? Recommended: the account's GitHub-provided no-reply address. GitHub always treats
     it as verified, and it is not personal data, so the cut script can carry it in a tracked file. The
     alternative, a personal address, has to stay out of tracked files (PS-1), which leaves the expected
     value only in the operator's untracked `common.sh`.
   - Confirm "fix forward only: the existing tags stay".
3. **Key-registration handoff script (if chosen at Gate 1).** One command, public key only; it prints the
   fingerprint. `@security` reviews it; the operator runs it.
4. **Cut-script change.** In the next cut script, derived from `16-cut-v1.2.0.sh`:
   - **before signing, blocking:** the tagger email equals the expected value (passed explicitly with
     `-c user.email`, not read from whatever the checkout holds); and the release key's fingerprint is in the
     account's public signing-key list;
   - **after the tag push, report only:** read the tag object's `verification` through the API, retrying
     for a short time because GitHub may not have it at once, and print and record the result. It never
     stops the release: the tag is already public, and the tag ruleset forbids deleting or moving it.
5. **Write the requirement down.** One sentence in `docs/release-policy.md`, section "Tags": the cut script
   checks the tagger identity and the registered signing key before signing, and reports GitHub's
   verification after pushing. Docs PR, `@security` review naming that file, the operator's live approval.
6. **Prove it** on the next real tag: record the API's `verification` result in the work summary.

## Not in scope
Re-signing or replacing existing tags (ruled out by the operator). Any change to repository settings, rulesets
or keys by the agent.

## Operator decisions
The three Gate 1 questions in step 2; the merge of the docs PR.

## Done when
A release tag reports `verified=true`, and the cut script's checks before signing would have stopped it if the
tagger email or the signing-key registration were wrong.
