# Signing inputs, 2026-11-13 (records, not trust roots)

These are the unsigned inputs the operator signed on 2026-11-13. They are kept so the signing can be
audited. Nothing loads them, and they authorize nothing.

| File | Signed result |
|------|---------------|
| `toolchain-group.unsigned.json` (sha256 `3b4a6925…8955`) | `.agentteams/toolchain-group.json` (sha256 `a38d0484…a80a`), the only group file the verifier reads |
| `s10-first-party-releases-2026-11.decision-spec.json` | the `s10-first-party-releases-2026-11` row in `.github/agents/references/security-decisions.log.csv` |
| `s10-first-party-releases-2026-11.decision-spec.template.json` | the template that spec was filled from |

The spec's evidence field cites `tmp/by-week/…` paths. They are left unchanged because the row's
`text_digest` covers them. The tracked copy of that plan is `references/plans/release-prep-v1.1.4.plan.md`.
