# Archive of earlier sessions' plans and operator scripts (published 2026-11-14)

These files were kept in this repository's ignored `tmp/by-week/` from 2026-W21 to 2026-W46. They are
published here under rule PS-1 (`.claude/CLAUDE.md`, all session work is public) on the operator's
decision of 2026-11-14. See `references/plans/hidden-material-2026-11-14.plan.md` and
`docs/hidden-work-remediation-2026-11-14.md`.

**These are historical records. Do not run or reuse the scripts.** Every operator script under
`<week>/operator/` has already been run. The published copies were scrubbed, so they no longer run as written:

| Original | Replaced with |
|---|---|
| the home-directory path | `~` (inside quotes, so it does not expand) |
| the signer install path | `<signer>` |
| the release-key and decision-key file paths | `<release-key-file>`, `<decision-key-file>` |
| session scratchpad paths, `user@host` prompts, email addresses | `<scratchpad>`, `user@host`, `<email>` |
| the operator's name (possessive included), and the GitHub noreply address | `the operator`, `the operator's`, `<noreply>` |
| one pronoun next to the scrubbed name (2026-W42 `v1.0.0-phase-t.plan.md`) | `their` |
| `2026-W42/operator/state.env` (a frozen snapshot; `common.sh` still names `state.env`, so a re-run writes an ignored file) | `state.vars.txt` |

What these scripts did is recorded in the signed tags, the operator-signed rows in
`.github/agents/references/security-decisions.log.csv`, and the PRs they name. Notes about other repositories
were not published here; they belong in infrastructureManagement.

The seed answer (2026-W42, AI-generated text the operator pasted, C-4 data) is not published here either. Its
canonical copy is in the private security repository, under `Projects/ai-cryptography-threats/sources/`.

`2026-W42/operator/state.vars.txt` is the original `state.env`, which holds only PR numbers and tag SHAs. The
`*.env` ignore rule (`@security` S-1) kept it out of PR #162, so that PR published 109 records, not 110. It was added
later under this name.
