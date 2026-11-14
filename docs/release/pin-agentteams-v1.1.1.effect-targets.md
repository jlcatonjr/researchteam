# pin-agentteams-v1.1.1: `effect_targets` coverage (record, 2026-11-14)

## Gap

The operator-signed row `pin-agentteams-v1.1.1` (`.github/agents/references/security-decisions.log.csv`, added in
`65f5604`, merged with #158) lists `effect_targets = toolchain.lock; pyproject.toml`.

#158 also added one `model:` line to each of the 33 front-mattered `.claude/agents/*.md` files: `claude-fable-5-2`
for the orchestrator, `opus` for the others. The CHANGELOG calls `model` a privileged key. The signed row does not
name those files. `@conflict-auditor` flagged this on #158 before signing. The row was signed with the original
targets.

## Decision: no new row

Recommended by the orchestrator and accepted by the operator on 2026-11-14.

- `@security` reviewed the model lines on #158 (PASS-WITH-NOTES). Each file gains exactly one `model:` line, and no
  `tools:` line changed, so no capability is widened (C-3).
- The row's classification is unaffected. The signer reported it as non-relaxing (the row's `effect_class` field is empty), with no grants and no
  relaxations. A model choice neither grants nor relaxes anything.
- Widening `effect_targets` would need a second signed row for the same action. That would duplicate a decision in
  the hash-chained log, the outcome the operator discarded on 2026-11-14 (a re-run of the signer, restored before
  any commit).
- The review record for the model lines is the `@security` and `@conflict-auditor` comment on #158:
  https://github.com/jlcatonjr/researchteam/pull/158#issuecomment-6857854864

## For later pin specs

When a pin PR also changes agent front matter, list those paths in the spec's `effect_targets` before signing.
