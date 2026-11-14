# PLAN (v1, pre-audit) — Integrate the agentteams update + make integration AUTOMATIC (3 repos)

**Trigger:** agentteams updated `efe8f12 → e6627fb` (8 commits). User: "make sure that researchteam,
OrthodoxLLM, and SocialScienceHumanities automatically integrate these updates."
**Discipline:** plan → adversarial+conflict audit → revise (R#) → implement → gates green.
**Date:** 2026-07-09. researchteam clean on main @ `b2bec7a`.

## What the update contains (verified)
- **PR #51** `fix(code-index): surface code-index retrieval to the primary agent team, not only the Claude
  skill` — adds code-index guidance to generated agent bodies. On researchteam's **already-enriched**
  agents the shrink-guard **suppresses** most of it (dry-run: 11 "template update suppressed" notices).
- **PR #52** low-level/systems vuln screening for @security; **PR #53** curated OS hardening references
  (Linux/macOS/Windows) — the update generates **3 NEW files**
  `.github/agents/references/security-{linux,macos,windows}-hardening.reference.md`; **PR #54** audit revisions.
- `bridge.py` / `git_hooks.py` **unchanged** → **no bridge re-run needed**; hook mechanism unchanged.
- Merge plan (dry-run): `MERGE 1, MERGE-OVERWRITE-FENCED 4 (graphs), UNCHANGED 39` + benign state churn
  (security threat-intel fence, build-log/delivery-receipt/memory-index, graphs) — same class as before.

## Current auto-integration machinery (recon)
- **Local pre-commit hooks:** PRESENT in all 3 repos (`RESEARCHTEAM:agentteams-integrate` runs
  `researchteam update --layer1-only` + `AGENTTEAMS:pipeline-graph-refresh`). **But they only fire when
  AGENT FILES are staged — NOT when agentteams itself updates.** So they do NOT catch this scenario.
- **On-demand:** `researchteam update` / `--layer1-only`. Manual.
- **CI:** `agentteams-sync.yml` (upstream) + `agentteams-sync-derived.yml` (scaffold, + each derived repo's
  own copy). **Scheduled runs are dry-run-only** (`open_pr=false`) → detect drift into an artifact nobody
  reads; never integrate. The `open-pr` job is also gated to `workflow_dispatch` only, AND runs in a
  separate fresh-checkout job (latent bug: it can't see the update job's changes).
- **Noise reality:** agentteams refreshes threat-intel + graphs + timestamps on EVERY run (even
  `--dry-run` leaks these writes) → `has_diff` is ALWAYS true → naive "auto-PR on any drift" = weekly spam.

**Gap to close:** nothing automatically integrates an *agentteams version change*. The durable fix must be
version-GATED (fire only on a real agentteams update), auto-PR (not auto-merge — revert-safety), and
evergreen (one PR, not weekly spam).

## Part A — Integrate the current update NOW (all 3 repos)
- **A1 researchteam (upstream):** `researchteam update --layer1-only --yes` (agent-team regen; no layer-2
  self-sync on upstream). Brings the 3 security-hardening refs + @security updates + graph regen (+ benign
  state churn). Review diff; verify fences balanced, `validate`, `--bridge-check` PASS, lit-lib + citation
  tests green, doctor green. Commit + push main. **Revert any file whose regen corrupts it.**
- **A2 OrthodoxLLM / A3 SSH:** `researchteam update --yes` (layer-1 agentteams merge; layer-2 already
  synced last session → ~no layer-2 change). Verify R7 gate sha `7531c3b57bbd` unchanged (OrthodoxLLM),
  fences balanced, no corruption. Commit + push each private repo. Baseline HEADs captured first.

## Part B — Make integration AUTOMATIC & durable (version-gated CI auto-PR)
- **B1 Upstream `agentteams-sync.yml`:** rework the scheduled path into a **version-gated evergreen
  auto-PR**:
  - Record the last-integrated agentteams ref in a repo file (e.g. `.github/agents/references/
    .agentteams-ref` or reuse build-log's agentteams_version). On schedule, `git ls-remote` agentteams
    main HEAD; if unchanged → exit (no-op, no PR); if changed → run `--update --merge`, run ALL blocking
    gates, and open/update ONE evergreen PR `chore/agentteams-autosync` (peter-evans, same branch =
    updates in place, no spam), writing the new ref. **update+PR in the SAME job** (fixes the latent bug).
  - Auto-PR, NOT auto-merge (human reviews/merges — matches the revert-safety posture + policy §Auto-merge
    disabled). Keep the forbidden-path guards + validate + detector tests as BLOCKING.
- **B2 Scaffold `agentteams-sync-derived.yml`:** same version-gated evergreen auto-PR (for NEW derived
  repos). Layer-2 (researchteam) + layer-1 (agentteams) — gate on EITHER upstream changing.
- **B3 Existing derived repos:** their `.github/workflows/*.yml` are NOT managed (INIT_SKIP_PREFIXES) →
  edit each repo's copy directly to match B2. (Note the non-propagation in open-items.)
- **B4 Policy:** update `docs/agentteams-update-policy.md` — scheduled runs now auto-open an evergreen PR
  on a *real* upstream change (was "dry-run only"). Keep auto-merge disabled + reviewer gate.
- **B5 Local hooks:** already present in all 3; no action (verify + note).

## Invariants
- Auto-PR, never auto-merge (revert-safety; human merges). Version-gate to avoid threat-intel/timestamp
  spam. All validation gates stay BLOCKING (a bad regen never becomes a PR). Evergreen branch (one PR).
- Revert any file whose regen corrupts it or breaks infra (baseline commits + private repos + backups).
- Benign state churn (threat-intel, build-log, graphs) is expected + self-healing — not corruption.
- Don't hand-edit AGENTTEAMS fences; PSN/managed docs are the durable edit homes.

## Open audit questions
1. Is Part A's regen safe on researchteam's enriched agents (shrink-guard preserves content)? Any way the
   security-wave regen or PR51 could CORRUPT an enriched fence vs. cleanly suppress?
2. Part B: is version-gated evergreen auto-PR the right mechanism, or over-engineered? Simpler robust
   alternative? Is `git ls-remote` gating sound? Where to store the last-integrated ref safely?
3. Auto-PR vs auto-commit vs auto-merge — is reviewable auto-PR the right safety level given the user said
   "automatically integrate"? (Default: auto-PR; note auto-merge as a toggle.)
4. Editing the derived repos' unmanaged workflows (B3) — right call, or leave to the scaffold + a note?
5. Permissions/token: does the scheduled auto-PR need more than `GITHUB_TOKEN` (branch protection,
   fork PRs)? Any secret/loop risk (a PR merge re-triggering the workflow)?
6. Does integrating PR51 (code-index to primary team) DUPLICATE/conflict with my PSN pointers +
   retrieval-surfaces.md + code-query from last session?
7. Scope: am I over-reaching? Is "integrate now + evergreen auto-PR + policy" the right size, or should
   Part B be narrower (e.g., just fix the scheduled run to auto-PR with a noise filter)?
