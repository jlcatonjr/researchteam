# Remediation Plan — `researchteam` ↔ `agentteams` CLI Integration

**Date:** 2026-07-05
**Author:** infrastructure remediation (Claude)
**Trigger:** `researchteam update` crashed with `ModuleNotFoundError: No module named 'build_team'`
while regenerating agent-team roster fences for a consumer repository
(`researchRepositories/SocialScienceHumanities`).
**Status of the immediate outage:** RESOLVED (editable install repaired).
**Status of structural hardening:** IMPLEMENTED — see §8. This document was **audited
(adversarial + conflict) and revised** before implementation; §5 recommendations replace an
earlier draft whose P1/P2 fixes were unsafe (see §5.0).

---

## 1. Incident summary

`researchteam update` performs two phases:
1. **Layer-2 sync** — pulls managed files from `jlcatonjr/researchteam@main` (worked fine, 0 changes).
2. **Layer-1 delegation** — shells out to `agentteams … --update --merge` to regenerate the
   agent team (`researchteam/_update_cmd.py::_run_agentteams`).

Phase 2 aborted immediately: the `agentteams` console script
(`/opt/anaconda3/bin/agentteams`, entry point `build_team:main`) could not import `build_team`.

## 2. Root cause (confirmed)

`agentteams` is installed as an **editable** package (`__editable__.agentteams-1.0.0rc6.pth` +
`__editable___agentteams_1_0_0rc6_finder.py`) in the anaconda environment. The finder's `MAPPING`
pointed at an **ephemeral path that no longer exists** — a temporary git worktree
(`…/scratchpad/scan-fix-worktree/`) from a prior automated session. `pip install -e .` had been run
*from inside that worktree*, so setuptools baked the worktree path into the editable finder. When the
worktree was cleaned up, `build_team` became unimportable and every `agentteams` invocation —
including the one `researchteam update` depends on — began failing with a raw traceback.

The real source (`/Users/jamescaton/githubrepositories/agentteams/build_team.py`) was intact the whole
time; only the install pointer was stale.

## 3. Immediate fix applied (verified)

Reinstalled the editable package from the **stable** repository path under the interpreter that owns
the console script:

```bash
/opt/anaconda3/bin/python -m pip install -e /Users/jamescaton/githubrepositories/agentteams --no-build-isolation
```

Verified this session: `agentteams --version` → `1.0.0rc6`; the finder now maps
`build_team`/`agentteams` to `/Users/jamescaton/githubrepositories/agentteams`; `researchteam update
--dry-run` completes. §1–§3 are accurate as written.

## 4. Structural fragilities in the `researchteam` module (the real remediation)

The outage was a symptom. Three design gaps in `researchteam` turned a stale install into a cryptic
failure and left the integration brittle.

### 4.1 Cross-environment coupling, undeclared
- `pyproject.toml` declares `dependencies = []`. `agentteams` is a **required** runtime dependency for
  `researchteam update` (Layer-1) yet is expressed nowhere.
- `researchteam` runs under its **py3.14 venv**, which has **no** `agentteams`/`build_team`. It relies
  on a **bare `agentteams` found on `PATH`**, which resolves to a *different* interpreter's install
  (`/opt/anaconda3/bin/agentteams`, py3.12). This cross-interpreter coupling is invisible — **and, per
  the audit, it is also what makes the tool work.** `agentteams` is **not on PyPI**, so it *cannot* be
  installed into the venv by name; the PATH resolution to the anaconda interpreter that *has*
  `build_team` is load-bearing, not incidental.

### 4.2 No preflight / health check before shelling out
- `_run_agentteams` called `subprocess.run(["agentteams", …])` and inspected only the return code. A
  broken/missing/incompatible `agentteams` surfaced as a raw `ModuleNotFoundError` with no guidance.
  There was no `researchteam doctor`; `status` reported only marker + version.

### 4.3 Wrong descriptor passed to `agentteams` — a two-sided data-loss trap
- `_run_agentteams` hardcoded `--description brief.json`. Two descriptor files carry **complementary,
  non-overlapping halves** of the project definition, and **each is a subset, not a superset, of the
  other** (audit correction — the earlier draft wrongly called `brief.json` "minimal"):
  - `brief.json` (14 keys) — **content of record**: `authority_sources` (7 sources), `style_rules`
    (11 Chicago rules), `conversion_pipeline`, `reference_key_convention`, rich `components`, and the
    output-path fields. **Lacks the archetype roster.**
  - `.github/agents/_build-description.json` (12 keys) — **roster of record**: `selected_archetypes`
    (9) + `governance_agents` (10). **Lacks every content field above.**
- These content fields are **consumed on every render** by `agentteams/analyze.py` (not only at initial
  build): `authority_sources` → the FENCED `authority_sources_list` in `conflict-auditor.agent.md` /
  `technical-validator.agent.md`; `style_rules` → `style_rules_summary`; etc.
- Consequences, both empirically confirmed by dry-run on this repo:
  - `--description brief.json` alone → `output-compiler`, `visual-designer` reported as **orphans**
    ("not part of the current team"); under `--prune` they would be **deleted**.
  - `--description _build-description.json` alone → archetypes recognized, but the descriptor-derived
    fences (`authority_sources_list`: 7 sources → the single placeholder `- Project source files
    (read-only)`; `style_rules_summary`: 11 rules → `No project-specific style rules defined.`) would
    **shrink to defaults** — saved *only* by `agentteams`' external shrink-guard `preserve` policy,
    which `researchteam` does not control.
- So **neither single descriptor is safe.** A blind *swap* (the earlier draft's P1) trades archetype
  orphaning for silent authority/style-fence regression and a path-convention flip.

## 5. Recommended remediation (prioritized, audited & revised)

### 5.0 What the audit changed (do not revert to the earlier draft)
- The earlier P1 **swapped** to `_build-description.json`. **Rejected** — it silently shrinks the
  authority/style fences (§4.3). Replaced by a **descriptor union** (P1 below).
- The earlier P2 recommended `subprocess.run([sys.executable, "-m", "build_team", …])`. **Rejected** —
  `sys.executable` is the py3.14 venv, which has no `build_team`; this **reintroduces the outage**.
- The earlier P2 recommended adding `agentteams>=1.0.0rc6` to `[project.dependencies]`. **Rejected** —
  `agentteams` is not on PyPI, so this **breaks `pip install researchteam`**.
- The earlier P1 code promised to "surface the dual-descriptor advisory" but passing the manifest *as*
  the descriptor **suppresses** it (the sibling probe then finds only itself). The union keeps
  `brief.json` semantics so the advisory still fires.

### 5.1 P1 — Reconcile descriptors via a UNION (prevents both data-loss modes)
In `researchteam/_update_cmd.py`, build a runtime union: `brief.json` as the **base** (preserving every
content field and today's output-path convention unchanged) with `selected_archetypes` +
`governance_agents` **injected** from `_build-description.json`; write it to a short-lived temp
descriptor beside `brief.json` and pass that to `agentteams`. If `brief.json` already carries the
roster, or the manifest is absent, fall back to `brief.json` directly (so the advisory still fires).
Net effect vs. today: archetypes are recognized (no orphans); **nothing else changes** (paths,
authority, style identical to the current `brief.json` run).

### 5.2 P1 — Preflight health check with an actionable error
Before shelling out: `shutil.which("agentteams")` (absent → install instructions), then an
`agentteams --version` probe. The probe is a genuine **import assertion** — the entry point is
`build_team:main`, so `--version` imports `build_team` before argparse; a non-zero probe is the exact
stale-editable-install signature of this incident and yields a one-line reinstall instruction instead
of a traceback. Keep the resolved absolute path and invoke *that*.

### 5.3 P2 — Declare the dependency correctly (optional, from git)
- Keep base `dependencies = []` so `pip install researchteam` and the documented
  `pip install git+…/researchteam.git` always resolve.
- Add `[project.optional-dependencies] update = ["agentteams @ git+https://github.com/jlcatonjr/agentteams"]`
  (VCS URL — verified reachable; **no PyPI floor**, which would be unsatisfiable and, being a
  pre-release, excluded by default pip resolution). Document editable-from-local-checkout as the
  primary dev path. The preflight + `doctor` enforce presence at runtime.
- Do **not** invoke via `sys.executable -m build_team`; keep the PATH-resolved console script (§4.1).

### 5.4 P2 — Add `researchteam doctor`
A subcommand validating the toolchain end-to-end: `agentteams` resolves; `--version` runs (import
assertion); the install is **not ephemeral** (resolve the console script's shebang interpreter, ask it
where `build_team` lives, warn loudly if that path is under `/tmp`, `/private/tmp`, `/var/folders`, or a
`*-worktree`/`scratchpad` dir); and the two descriptors are reconcilable (content fields present in
`brief.json`, roster present in `_build-description.json`). Exits non-zero on any failure.

### 5.5 P3 — Cross-repo contract note (defense in depth)
`researchteam`'s P1 correctness depends on `agentteams`' `analyze.py` field-consumption and the
`preserve` shrink-guard — behavior in a **separate, pre-release, editable-installed** repo. Because the
editable version string is frozen while source changes underneath, a version floor gives no protection;
`doctor`'s runtime checks are the real guard. The union descriptor is designed to be correct even if
`preserve` were disabled (it never presents a shrinking descriptor in the first place).

## 6. Out-of-scope note (belongs to `agentteams`, filed for visibility)
`agentteams … --framework goose --recipe-check` looks for recipes at `.github/agents/.goose/recipes`
but the recipes live at the repo-root `.goose/recipes`. This is an `agentteams` path-resolution bug, not
a `researchteam` one; noted here so it is not lost.

## 7. Acceptance criteria (revised — fix-agnostic, and covering the regression the audit found)
- [x] `researchteam update` never emits a raw `ModuleNotFoundError`; a broken/absent `agentteams`
      yields a one-line actionable message (preflight `_preflight_agentteams`). **Verified.**
- [x] `researchteam update` does not orphan registered archetypes **and** does not shrink the
      descriptor-derived fences: a dry-run shows `output-compiler`/`visual-designer` recognized and the
      `authority_sources_list` / `style_rules_summary` fences UNCHANGED (union descriptor). **Verified**
      (3 orphans → the 2 registered archetypes recognized; no shrink warnings).
- [x] `agentteams` is invoked via an interpreter that actually owns `build_team` (the PATH-resolved
      console script, asserted by the `--version` import probe); it is an **optional git extra**, never a
      PyPI dependency, so `pip install researchteam` still resolves. **Verified.**
- [x] `researchteam doctor` reports toolchain health, ephemeral-install smell, and descriptor
      reconcilability, exiting non-zero on failure. **Verified** (all-green on this repo; not-found and
      ephemeral paths produce actionable FAILs).
- [x] Regression check: a repo with a hand-authored archetype shows it retained (UNCHANGED body, roster
      recognized), not orphaned. **Verified** on this repo's `output-compiler`/`visual-designer`.

## 8. Implementation status (this revision)
Implemented in `researchteam`:
- `researchteam/_update_cmd.py` — `_preflight_agentteams()` (which + `--version` import probe →
  actionable errors); `_resolve_descriptor()` (brief.json ⊕ roster union → temp descriptor, cleaned up
  in `finally`); `_run_agentteams()` rewired to use both, invoking the resolved console-script path.
- `researchteam/_doctor_cmd.py` — new `researchteam doctor`.
- `researchteam/cli.py` — `doctor` subcommand registered and dispatched.
- `pyproject.toml` — base `dependencies = []` kept; `[project.optional-dependencies] update` added
  (git VCS URL, no PyPI floor).

Not changed (correctly out of scope): the goose recipe-path bug (§6, `agentteams`-owned); any
`build_team.py` behavior. Note the earlier draft's citation of `build_team.py:632` as the
"roster-reading" logic was a misattribution — that line is in `_write_run_log` (a build-log **writer**);
the roster is honored earlier in `analyze.build_manifest()`. The supporting evidence is instead
`build_team.py`'s own post-migration advisory, which recommends `_build-description.json` for `--merge`
runs — a recommendation the **union** honors without the fence-shrink cost.
