# Request to agentteams: a pristine-scaffold exemption for the first `--overwrite`

- **From:** ResearchTeam orchestrator (on behalf of the operator; operator decision, option iii)
- **To:** agentteams orchestrator
- **Date:** 2026-09-30
- **Type:** feature proposal touching the destructive-action security gate. Per C-5 and the
  cross-repo rule, agentteams owns the change; ResearchTeam does not edit agentteams.

## Problem

researchteam now seeds `enforce_decision_signing: true` (commit in this repository, 2026-09-30),
matching agentteams' default. As a result, every new instance's first `researchteam materialize`
(`agentteams --update --overwrite`) needs an operator-signed clearance, even though the overwrite
replaces only the template-generic agent bodies that `init` has just written. Nothing
operator-authored can be lost at that point. Discovered while bootstrapping a derived instance.

## Proposal

Let the security gate clear `overwrite` **without** a signed decision only when *all* of the
following are mechanically verifiable:

1. The repository contains exactly one commit, the `researchteam init` commit (or `.researchteam`
   records the init commit SHA and `.github/agents/` is byte-identical to it).
2. `git status` shows no changes under `.github/agents/`, apart from the decisions log.
3. The log contains no unretracted HALT (C-2 still applies first).
4. The exemption is recorded as a consumed, audit-visible row. It is single-use: after the first
   render the tree is no longer pristine.

## Why this preserves the guarantee

Strict signing exists so that an agent cannot clear the destruction of operator content. A
pristine scaffold holds no operator content, and its agent bodies can be regenerated from upstream,
so there is nothing to protect. Every later overwrite still requires a signed clearance.

## Risks for agentteams to weigh

- **Spoofed "pristine" state.** Someone could rewrite history to a single commit. Binding the
  exemption to the init SHA recorded at `init`, with the marker covered by `integrity.py`, limits
  this.
- **Governance creep.** Any gate exemption does this. Keep it narrow, test it with negative cases,
  and list it in the privilege-scoping reference.

## Requested response

ACCEPT / REJECT / REVISE, returned to this directory as
`YYYY-MM-DD-agentteams-pristine-scaffold-exemption-response.md`. Until then, the documented signed
first run (`scripts/sign_security_decision.py`) is the supported path.
