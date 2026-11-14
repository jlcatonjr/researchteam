# Plan — `.gitignore` fenced-preserve for `researchteam update`

**Week:** 2026-W36 · **Date:** 2026-08-31 · **Owner:** orchestrator session
**Source spec:** `docs/gitignore-preservation-handoff.md` (v1.1, adversarially audited 2026-08-26)

## Problem

`.gitignore` is a `MANAGED_FILES` entry; layer-2 sync (`_update_cmd.py`) overwrites every managed
file wholesale from upstream. Any ignore pattern that exists only in a derived repo is silently
deleted on the next `researchteam update --yes` (the blind weekly CI path), turning correctly
ignored files into stageable ones. Root-cause fix requested by the SocialScienceHumanities session.

## Fix (Option A — fenced-preserve)

Per-file merge strategy. `.gitignore` opts into `fenced-preserve`: upstream owns a comment-fenced
managed block; everything outside the fence is preserved verbatim across syncs. Default strategy
stays `overwrite`, so no other managed file changes behavior. Layer-2 only; no agentteams change.

## Acceptance criteria (from spec §7)

1. Derived lines survive `--yes` (fenced local).
2. Upstream additions inside the fence land.
3. Upstream removals inside the fence apply.
4. No spurious deletions in preview (diff computed against fenced region only).
5. Pre-fence migration is non-destructive (diverged unfenced local never silently wiped under `--yes`).
6. Other managed files unchanged (overwrite default; `.sh` exec bit preserved).
7. Idempotent (identical managed block → no write).

## Risk / safety

- Backwards compatible: `MERGE_STRATEGIES` defaults to `overwrite`.
- Degrade-safe: if upstream copy is unfenced, `fenced-preserve` refuses to wholesale-overwrite
  (keeps local + warns) rather than reintroducing the loss.
- One upstream edit: wrap this repo's `.gitignore` body in the fence markers.
- PR #9 merge is independent (separate commit already reviewed).

## Blocking-issue note

GitHub Actions is account-billing-blocked (failed payment / spending limit). Sibling autosync and
this repo's CI cannot run until the operator clears billing in GitHub → Settings → Billing & plans.
Not fixable from the repo or CLI. Does not block the PR #9 merge (git op, no required checks).
