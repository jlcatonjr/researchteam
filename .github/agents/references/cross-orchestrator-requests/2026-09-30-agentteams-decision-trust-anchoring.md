# Request to agentteams: anchor clearance trust, add a routine minter, and gate every overwrite path

- **From:** ResearchTeam orchestrator (on behalf of the operator)
- **To:** agentteams orchestrator
- **Date:** 2026-09-30
- **Type:** security findings plus feature requests. agentteams owns every change; ResearchTeam does
  not edit agentteams (cross-repo rule).
- **Related:** `2026-09-30-agentteams-pristine-scaffold-exemption.md`. That request becomes
  unnecessary if F-5 below is accepted.

All findings were reproduced against agentteams 1.0.0rc7 (editable checkout), with file:line
evidence.

## F-1 (critical): HMAC decision signing does not stop agent self-clearance

`sign_decision_row` and the verifier (`cli/decision_log.py:287,348,713`) take the HMAC key from
the verifying process's environment (`AGENTTEAMS_DECISION_SIGNING_KEY`). The HMAC path pins no key:
there is no fingerprint and no `key_id` check. Any process that can run a shell command can
therefore choose a key, sign an authorizing row and pass the gate.

**Reproduction.** Inside an agent session (`CLAUDECODE=1`), in a throwaway team dir with
`enforce_decision_signing: true`:

1. `AGENTTEAMS_DECISION_SIGNING_KEY=<agent-chosen>`
2. `sign_decision_row(row)`
3. `check_clearance(dir, action="overwrite")` returns `(True, '')`.

`enforce_decision_signing` blocks *unsigned* rows only.

**Request.** Anchor routine authorizations where agents cannot write:

- allow Ed25519 for routine (non-relaxing) authorizing rows, verified against
  `references/authorized-verify-keys/<key_id>.pub.pem` (today Ed25519 applies only when
  `requires_operator_signature`, `:686-695`);
- deprecate env-key HMAC for authorization, or pin HMAC keys by a committed fingerprint;
- keep minting and rendering in separate invocations, so no secret is present during a render.

## F-2 (high): no routine decision minter

agentteams mints grants (`--issue-grant`), directives (`--issue-directive`) and relaxing decisions
(`--sign-decision`), but has no minter for the most common operator act: clearing a routine
`overwrite`/`prune`. Derived repos have had to write their own; a third-party minter would break
silently if the signed payload changed.

**Request.** An operator-only `--issue-decision`, **Ed25519-first** (per F-1). It should reuse
`atomicio.atomic_rewrite_csv_rows`, migrate the schema columns, verify after writing, and roll back
if verification fails.

## F-3 (high): `--sync-init` overwrites agent files without passing the gate

`multi_sync.sync_init` projects with `overwrite=True` (`multi_sync.py:461`, after a backup, with
`preserve_existing`). The destructive gate (`_assert_destructive_action_allowed`) is called only
from `generate.py:380,842` and `standalone_modes.py:62`.

**Request.** Route every overwrite-capable path through the same gate, or document why
`sync_init` is exempt.

## F-4 (medium): the gate crashes on short CSV rows

A decisions-log row with fewer fields than the header (the header had gained a `consumed` column
when a clearance was consumed) makes `security_gate.py:640` raise `AttributeError`:
`row.get("consumed", "")` returns `None` for missing trailing fields. The gate then crashes instead
of refusing or proceeding.

**Request.** Use `(row.get(k) or "")` throughout the log readers, or reject short rows with a
clear, fail-closed message.

## F-5 (policy input): whether regenerating tracked generated files is destructive

An operator has ruled, for a derived instance, that re-rendering git-tracked, generated agent files
is **not** destructive under C-5: git history makes it fully reversible. Today, agentteams gates
`--update --overwrite` as a destructive action regardless of whether the targets are tracked and
clean.

**Request.** Evaluate classifying an overwrite whose targets are all git-tracked and unmodified
(recoverable at `HEAD`) as non-destructive, or as a lighter-weight clearance class. Destructive
treatment would remain for untracked, dirty or gitignored targets. If accepted, the
pristine-scaffold exemption request is superseded.

## F-6 (evaluation requested): sandbox configuration merge

agentteams emits sandbox settings that read-deny `~/.config/agentteams/keys` and write-deny the
verify-key stores and `agent-privilege.json`. These settings are **inert until the operator merges
them**, and on the reporting host none is merged. The trust anchoring in F-1 depends on them.

**Request.** Evaluate and recommend:

- whether the merge should be guided or automated (e.g. a `--check-wiring`-driven operator step);
- what the merged profile should be for Claude Code and Goose on Linux, where `denyWrite` paths
  must exist;
- how to verify it end to end. The help text marks the Claude arm on Linux as "unverified
  end-to-end".

## F-7 (low): key hygiene and agent-session warning

- The HMAC key is accepted only from an env var. agentteams' own help warns that such variables
  are inherited by sandboxed agent commands (`parser.py:1079-1080`). Offer a keyfile source under
  `~/.config/agentteams/keys`.
- Reject weak or placeholder keys. In one instance, three clearances were signed with the literal
  placeholder `...`.
- Optionally warn when a minter runs in a detectable agent session (defense in depth only; the
  variables are unsettable).

## Requested response

Per finding: ACCEPT / REJECT / REVISE, returned as
`YYYY-MM-DD-agentteams-decision-trust-anchoring-response.md` in this directory.

## Interim operator posture

Pending F-1 and F-5, the operator has paused key-signed clearances in the affected instance:
`enforce_decision_signing: false`, with `@security` review rows retained for audit. The reason is
F-1: a signature that an agent could produce itself added ceremony, not protection.
