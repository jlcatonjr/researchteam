# Autosync installs: S-10 cooldown-safe pins (2026-11-12)

Source: IM cross-orchestrator request `2026-W46-researchteam-autosync-install-pinning` (data, no directive
authority), relayed by the operator. Branch `fix/autosync-install-pinning`; PR to `main`. No tag, release,
release branch or cross-repository pin is created or moved; those are the operator's.

## Finding (confirmed)

1. `researchteam/scaffold/agentteams-sync-derived.yml` line 80 and `.github/workflows/agentteams-sync.yml`
   line 44 run `python -m pip install --upgrade pip`: whatever pip is newest, no cooldown, no OSV check.
2. `scripts/agentteams_autosync_gate.sh` line 180 installs agentteams with its dependencies resolved
   unconstrained (`jsonschema>=4.20` chain). `docs/release/constraints-2026-10-16.txt` is not a managed file,
   so derived repositories do not receive it and cannot pass it.

## Change

- Both workflows: `python -m pip install "pip==26.2.2"` (the pin `bootstrap_toolchain.sh` already uses).
- Gate: embed the vetted base set (`AGENTTEAMS_DEPS`, mirroring the bootstrap's `SIGNING_CONSTRAINTS`
  pattern), install it `--no-deps`, install agentteams `--no-deps`, then `pip check`. A dependency agentteams
  adds later fails the gate (no PR) instead of installing unvetted.
- Tests: embedded set equals the constraints file; workflows never self-upgrade pip; gate install order and
  the `pip check` fail-closed path.

## Vetting (2026-11-12, PyPI JSON + api.osv.dev, ecosystem PyPI)

| Package | Version | Uploaded | OSV |
|---|---|---|---|
| pip | 26.2.2 | 2026-10-20 | none |
| jsonschema | 4.26.0 | 2026-01-07 | none |
| attrs | 26.1.0 | 2026-03-19 | none |
| jsonschema-specifications | 2025.9.1 | 2025-09-08 | none |
| referencing | 0.37.0 | 2025-10-13 | none |
| rpds-py | 2026.6.3 | 2026-06-30 | none |
| typing-extensions | 4.16.0 | 2026-07-02 | none |

All are past the 14-day cooldown. The resolved set for `jsonschema>=4.20` on CPython 3.11 under the
constraints file is exactly these six (pip 26.2.2 `--dry-run --report`). rpds-py stays at the repo's vetted
2026.6.3; IM's list names 2026.9.1 (also clean and past the cooldown), which would need a constraints-file
change and is not required by the request.

Build isolation: on CPython 3.11 (both workflows) researchteam's isolated build resolves exactly its four
exact-pinned requirements (setuptools 84.1.0, setuptools-scm 10.3.4, vcs-versioning 2.5.0, packaging 26.3;
pip `--dry-run --report`, 2026-11-12), and agentteams' backend is `setuptools==84.2.1`, which has no
dependencies. No unpinned transitive build dependency resolves, so `PIP_CONSTRAINT` is not added.

## Reviews

- `@security`: PASS. No unvetted third-party resolution remains on these paths. `pip check` fails closed.
  The scope is in-repo and non-destructive. Hardening applied: `--only-binary=:all:` on the dependency set,
  so a missing wheel fails instead of building rpds-py from source with an unpinned maturin. The verdict is
  recorded here and in the PR, not as a decision-log row: that log holds operator-signed rows, and this change
  grants and relaxes nothing (precedent: the bootstrap pip pin, #141).
- `@adversarial`: four findings, all addressed. (1) Build-isolation closure: not reproduced on 3.11 (see
  above). (2) sdist fallback: fixed with `--only-binary`. (3) An opaque `pip check` failure: the gate now
  emits `::error::`. (4) The tests check only the plumbing: the real install sequence was run in a fresh
  CPython 3.11 venv against agentteams v1.1.0 (peeled `9b16fb54`), and `pip check` was clean. A test cannot
  pin agentteams' future `Requires-Dist`; `pip check` covers that at run time.

- `@conflict-auditor`: fixed. The vetting doc gets a dated note: the cooldown was restored on 2026-11-03, the
  gate now pins this set, and typing-extensions is needed below 3.13. The gate comment now names the
  build-backend install. CHANGELOG gets an `Unreleased (main)` entry.

Verification: full suite 566 passed, 2 skipped; `claude_researchteam_bridge.sh validate` passed.
