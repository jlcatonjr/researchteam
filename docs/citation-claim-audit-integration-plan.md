# Integration Plan — 2-Fold Citation & Claim Audit

**Date:** 2026-07-07
**Author:** infrastructure integration (Claude)
**Trigger (user request):** "Each time a project is initiated or developed, the workflow should
trigger a 2-fold audit of the bibliography and URL links to the bibliography, as well as all the
facts and interpretations asserted by the article (especially in light of references listed to
justify each claim). This list of audits should occur twice so that we can be highly certain that
no citation or claim has been fabricated."
**Status:** IMPLEMENTED & VERIFIED 2026-07-07 (all acceptance criteria met — §4). Revised after
adversarial + conflict audit (§0).
**Supersedes:** `source-integrity-audit-integration-plan.md` (renamed — see R12).

---

## 0. What the audit changed (binding resolutions — do not revert to the draft)

The DRAFT was audited by independent adversarial and conflict passes. Both independently flagged the
same three load-bearing defects. These resolutions are binding; §§1–5 below already reflect them.

- **R1 (CRITICAL — derived CI break).** The draft added a **blocking** detector-unit-test step to
  the *derived* CI scaffold, but the test file is **not** a `MANAGED_FILE` and the derived workflow
  is init-frozen — so it would reference a nonexistent file and turn **every derived repo's CI red
  forever.** → Derived scaffold gets a **guarded advisory scan only**
  (`[ -x scripts/check_citation_integrity.sh ] && SOURCE…ADVISORY=1 …`); the **blocking unit test
  stays upstream-only** (where `scripts/tests/` is guaranteed present), exactly as the methodology
  detector already does.
- **R2 (CRITICAL — block only on the unambiguous).** The draft made **fuzzy** `.bib`↔`## References`
  drift and locator-syntax checks *blocking* `DEFECT`s. Against the real corpus this false-positive
  **blocks valid work**: Chicago prose (`Lucas, Robert E., Jr., and Edward C. Prescott. 1974.`,
  mixed author inversion, Oxford commas, four 2005 entries) cannot be matched to BibTeX in bash at a
  block-worthy confidence, and **valid DOIs contain parentheses**
  (`10.1016/0022-0531(71)90013-5`). → Blocking `DEFECT` is reserved for the **two mechanically
  certain checks only**: duplicate citation key `[DUP]` and a `.bib` entry missing a **universal**
  field (`author`/`title`/`year`) `[META]`. **Everything heuristic → `NEEDS-REVIEW` (advisory,
  exit 0):** drift `[RM]`/`[PE]`, in-text miss `[CU]`, URL/DOI syntax `[URL]`/`[DOI]`, structure
  `[STRUCT]`. Unit tests must assert the parenthesized DOIs above do **not** trip anything.
- **R3 (cut the double-derive theater).** The draft's "detector derives its ledger twice and
  diffs" is guaranteed-identical for a deterministic script — it tests for detector nondeterminism,
  not fabrication, and mislabels itself as the user's "occur twice." → Detector runs **once** in
  production. A **determinism guard** (run twice on a fixture, assert byte-identical) moves into the
  test harness. The user's "occur twice" is satisfied **solely** by the Round-1/Round-2 agent
  protocol (§3.3).
- **R4 (honest trigger; anchor at pre-compile closeout).** "Initiated/developed" are **not
  machine-detectable events** in this repo, and the semantic agent audit **cannot be fired
  automatically** by prose. → The **primary enforcement anchor is the pre-compile closeout gate**
  (orchestrator Rule 3 / Workflow 11 + the Rule-12 fail-closed gate), which catches everything
  before publication regardless of whether an initiate/develop prompt fired. Automatic surface = the
  **advisory CI scan**; on-demand = the **bridge command** the Claude workflow rule invokes;
  optional = a **documented per-commit opt-in one-liner** (no default git hook — `.git/hooks` is not
  version-controlled and would not propagate). "Initiate/develop" prompts are **best-effort**, not
  claimed as reliable automation.
- **R5 (fill the in-text blind spot).** The draft compared `## References` ↔ `.bib` but **never
  inspected in-text citations** — so an in-text-only fabricated cite is invisible. This is not
  hypothetical: `LaborMatchingMacroeconomics/01-literature-review.md` cites **`(Shi 1995)`** in
  prose with **no `Shi1995` entry** anywhere. → Add an **advisory** in-text scan: extract
  `(Surname Year)` / `Surname (Year)`, check surname+year against the `.bib`, emit
  `NEEDS-REVIEW [CU]` on a miss. (Advisory only — it shares the same fuzzy fragility; its value is
  *surfacing candidates*, which would have caught `Shi 1995`.)
- **R6 (propagate ceiling honesty up).** The detector layer was honest (`WELL-FORMED ≠ RESOLVED`)
  but §1/§3.3 echoed the user's "highly certain no fabrication." Two same-model passes are
  **correlated, not independent**; a syntactically valid but fabricated DOI can pass the detector
  *and* both agent rounds. → §1/§3.3 reworded: the double pass **raises detection of
  non-systematic slips**, gives **no proof of non-fabrication** and **little** assurance against
  shared/systematic blind spots; residuals are driven to explicit `UNVERIFIED` for **human,
  out-of-band** resolution. No surface claims "proven genuine."
- **R7 (don't stake reliability on layer-1 prose).** Survival of a USER-EDITABLE routing pointer
  across `agentteams --update --merge` is asserted by template text, not proven here. → Reliability
  lives in **CI + the managed protocol doc + Rule 12**, which propagate deterministically. The
  orchestrator pointer is placed at the **end of Project-Specific Notes** mirroring the
  **interpretation-advisor block that has already survived** prior regenerations, and is treated as
  **best-effort**. Verified non-destructively with `researchteam update --dry-run`.
- **R8 (cut sprawl).** → **Cut** the `@reference-manager` and `@technical-validator` USER-EDITABLE
  pointers (layer-1 ceremony; don't propagate to derived repos; duplicate the orchestrator routing;
  and technical-validator has a managed fence interleaved in its notes — a needless hazard).
  **Keep** exactly: the detector, upstream tests, the bridge command, upstream CI (blocking test +
  advisory scan), derived CI (advisory scan only), two `MANAGED_FILES` (detector + protocol doc),
  the orchestrator pointer (best-effort), and the single managed protocol doc as the DRY home for
  the procedure. CLAUDE.md + preflight + prompt each carry a **one-line pointer** to that one doc
  (distinct Claude entry points; the procedure itself is not duplicated).
- **R9 (own the discovery divergence).** The detector does **not** mirror the methodology script's
  flat `Projects/*/` glob — it does **marker-based recursive** discovery (marker =
  `00-research-plan.md` ∨ a `references/` dir ∨ a `NN-*.md`) over **both** `Projects/` and hidden
  `.projects/`, using `find … -prune` to exclude `.agentteams-backups/`, `references/plans/`,
  `.git/`, and shared-asset dirs (`JSModules/`, `cssfiles/`). It mirrors the detector **contract**
  (advisory/blocking modes, exit codes, `RT_ROOT`, tests, bridge+CI wiring), not the glob. Tested
  against all 3 real roots + a backup tree that must be excluded.
- **R10 (code-tagged output for mechanical consolidation).** Every finding line carries a bracketed
  candidate code (`DEFECT [DUP|META]`, `NEEDS-REVIEW [CU|RM|PE|URL|DOI|STRUCT]`) so
  `@conflict-auditor` consolidates into its existing `CU/FU/AE/RM/RX/PE` taxonomy mechanically. The
  detector stays a **stateless stdout scanner** — it does **not** write `conflict-log.csv` (that is
  the agent's job, per the methodology-detector precedent).
- **R11 (upstream-main ordering).** `researchteam update` fetches `MANAGED_FILES` from `@main`, so
  the two new managed files must land on upstream `main` in the **same commit** that edits
  `_manifest.py`, or every `update` run (here and in derived repos) emits soft fetch-error lines
  until they do. This repo *is* upstream, so committing here satisfies it; documented as a
  release-sequencing note (no push performed without user request).
- **R12 (rename off the overloaded word "source").** "source" already means two other things in
  this codebase — `SOURCE_DRIFT (SD)` (deliverable-vs-disk) and the authority-URL "Source Layer."
  → `check_citation_integrity.sh`, bridge `citation-audit`, `docs/citation-claim-audit-protocol.md`,
  and this plan renamed to `citation-claim-audit-integration-plan.md`.

---

## 1. What the user is asking for (decomposed, with the honesty the audit requires)

Two audit **dimensions**, run in **two rounds**:

- **Dimension A — Citation & bibliography integrity.** Every in-text citation is backed by a real
  bibliography record; every record carries the metadata + locator it claims; URLs are well-formed;
  the two parallel bibliography surfaces (`.bib` and each deliverable's `## References`) don't drift.
- **Dimension B — Claim & interpretation integrity.** Every fact/interpretation is paired with the
  reference(s) cited to justify it; no claim outruns its evidence; no citation is mis-attributed.

"**2-fold**" = the two dimensions. "**occur twice**" = the {A,B} audit runs in **two rounds**
(Round 2 adversarially framed and re-run from the deliverable, then diffed against Round 1).

**Honest ceiling (R6, and repository design law).** No automated system — script or LLM — can
**prove** a citation or claim is genuine; a syntactically valid but fabricated DOI, or a plausible
but unsupported paraphrase, can pass every automated check. The double pass **raises the probability
of catching non-systematic slips**; it does **not** certify non-fabrication and adds **little**
against shared/systematic model blind spots (two same-model passes are correlated). What this system
guarantees is: **structural defects are caught deterministically**, **fabrication-shaped signals are
surfaced**, and **every unresolved item is driven to an explicit `UNVERIFIED` that blocks compile
until a human resolves it out-of-band.** `WELL-FORMED ≠ RESOLVED`, everywhere.

---

## 2. Findings — what already exists (extend, don't duplicate)

### 2.1 The audit *agents* already exist; they are simply never paired or doubled
- **Dimension A** → `@reference-manager` (Zero-Defect Citation Gate; `KEY_RESOLUTION`,
  `METADATA_COMPLETENESS`, `RESOLVER_CHECK`, `DEDUPLICATION_CHECK`) + `@conflict-auditor`
  (`CITATION_UNVERIFIED CU`, `REFERENCE_MISSING RM`, `REFERENCE_MISMATCH RX`, `PHANTOM_ENTRY PE`).
- **Dimension B** → `@technical-validator` (`CH-08/09/10`, claim ledger, fail-closed) +
  `@conflict-auditor` (`FACT_UNVERIFIED FU`, `ATTRIBUTION_ERROR AE`) + `@quality-auditor` (`Q-LGC`).
- **Enforcing backbone already exists** in `orchestrator.agent.md`: Constitutional **Rule 5**
  (never fabricate references, line 136) and **Rule 12** (fail-closed verification gate — unresolved
  `UNVERIFIED`/`NOT-FOUND`/`CONTRADICTED` blocks publication/compilation/acceptance, line 143);
  reinforced by `@conflict-auditor` Rule 6 (unresolved `FU/CU/AE/CC` blocks release).
- **Manual precedent:** `references/plans/adversarial-conflict-audit-labor-matching.plan.md` ran
  `@adversarial → @technical-validator → @reference-manager → @conflict-auditor` once and produced a
  `04-adversarial-conflict-audit.md` ledger. This plan **promotes that one-off into a standing,
  doubled protocol** anchored at closeout.

### 2.2 The gap
The orchestrator's standing closeout — Rule 3, "Standard Doc-Sync Closeout" (259–270), "Workflow 11:
Final Check" (413–444) — has **no citation-integrity and no claim-verification step**;
`@conflict-auditor` at closeout checks *contradictions* only. `@technical-validator` and
`@reference-manager` run in *separate* workflows (3, 5), never paired, never doubled. No
"double/twice/2-fold" language exists. The primitives exist; **the paired, doubled, closeout-anchored
trigger does not.** That is what this plan adds.

### 2.3 The detector *contract* to mirror (not its glob — R9)
`scripts/check_methodology_coverage.sh`: deterministic stdout scanner; advisory env flag
(`METHODOLOGY_COVERAGE_ADVISORY=1` ⇒ exit 0) + blocking default; `RT_ROOT` override; bash-3.2 unit
tests; wired into the bridge + CI; a `MANAGED_FILE`. We mirror this **contract**. We diverge on
discovery (recursive, `.projects/` included) and own that divergence.

### 2.4 On-disk reality (verified)
3 project roots — `Projects/ZeldaTimeline`, `Projects/Matching/LaborMatchingMacroeconomics` (nested),
`.projects/DiacriticReplacement` (hidden). **Chicago author-date** citations (`(Author Year)` /
`Author (Year)` — no `[@key]`). **Non-uniform `.bib`** (only `author/title/year` universal;
`doi`/`url`/`isbn` vary). **Two parallel bibliographies per project** (`.bib` + hand-maintained
`## References`). HTML readers `fetch()` the `.md` (scan `.md`, skip `.html`).
`.projects/DiacriticReplacement` **deliberately has zero in-text citations** → "no references" is a
**valid state → advisory, never a block.** Live defect already present: an in-text `(Shi 1995)` with
no bib backing (R5).

### 2.5 Governing constraints (design law)
Anti-fabrication ceiling (`WELL-FORMED ≠ RESOLVED`, no self-attestation); advisory-by-design
(judgment calls surface, don't auto-gate); respect fences (durable additions in USER-EDITABLE /
`docs/` / scripts, never in a fence); anti-sprawl.

---

## 3. Design (post-audit)

Reliability principle: **a script runs identically every time; agent prose is guidance a model may
or may not follow.** So the mechanical subset is a deterministic detector (spine); the semantic
subset is the doubled agent protocol (depth), **anchored at pre-compile closeout** (R4); triggers
are layered (automatic CI advisory scan + on-demand bridge + best-effort prompts + optional opt-in
hook).

### 3.1 Component 1 — Detector `scripts/check_citation_integrity.sh`
Mirrors the detector contract (§2.3); recursive marker-based discovery (R9). Result classes:
- **`DEFECT` (blocking; exit 1 unless advisory) — mechanically certain only (R2):** duplicate
  citation key `[DUP]`; `.bib` entry missing a universal field `[META]`.
- **`NEEDS-REVIEW` (always advisory; exit 0) — every heuristic signal (R2, R5):** `.bib`↔`##
  References` drift `[RM]`/`[PE]`; in-text cite with no bib backing `[CU]`; malformed-looking
  URL/DOI `[URL]`/`[DOI]`; missing `## References` / missing `.bib` / zero-citation deliverable
  `[STRUCT]`.
- **`PASS`.**
Every finding line is **code-tagged** (R10). Exit contract mirrors methodology: `0` clear/advisory,
`1` ≥1 `DEFECT` in blocking mode, `2` usage/env error; `CITATION_INTEGRITY_ADVISORY=1` downgrades
`DEFECT` to warn-only. Every run prints the ceiling banner (R6). **Runs once** (R3).

### 3.2 Component 2 — Tests `scripts/tests/test_citation_integrity.sh`
Bash-3.2 throwaway `RT_ROOT` fixtures (mirror `test_methodology_coverage.sh`): PASS; each `DEFECT`
(dup key, missing field); each `NEEDS-REVIEW` (drift, in-text miss, no-refs, citation-free must stay
exit 0); advisory-downgrade; **valid parenthesized-DOI fixture that must NOT trip** (R2);
**recursive discovery** over all 3 root shapes + a backup tree that must be **excluded** (R9); and a
**determinism guard** (detector twice on a fixture ⇒ byte-identical) (R3). **Blocking upstream CI
only** (R1).

### 3.3 Component 3 — Protocol `docs/citation-claim-audit-protocol.md` (single DRY source, MANAGED)
- **Round 1 (baseline).** `@reference-manager` (A) ‖ `@technical-validator` (B) → `@conflict-auditor`
  consolidates into `CU/FU/AE/RM/RX/PE` and logs; unresolved `CU/FU/AE` block compile via **existing
  Rule 12** (no new gate).
- **Round 2 (adversarial re-audit).** `@adversarial` frames "assume a citation/claim is fabricated";
  A + B **re-audit from the deliverable alone**; `@conflict-auditor` **diffs Round 2 vs Round 1** —
  divergence escalates. Convergence-clean is the confidence bar **with the R6 caveat stated in the
  doc** (correlated passes; no proof of non-fabrication).
- **Anchor:** run at project closeout **before `@output-compiler`** (R4). Output: a
  `04-*-audit.md`-style ledger (the format the real projects already use).

### 3.4 Component 4 — Trigger surfaces (honest; R4)
- **Bridge** `citation-audit [project]` in `claude_researchteam_bridge.sh` → runs the detector
  (mirrors `methodology-check`).
- **CI:** upstream `agentteams-sync.yml` gets a **blocking test** step + a **guarded advisory scan**;
  derived `agentteams-sync-derived.yml` gets the **guarded advisory scan only** (R1). Closes the
  pre-existing gap where derived CI runs no detector at all.
- **Orchestrator** Project-Specific Notes (USER-EDITABLE, after the interpretation-advisor block):
  a best-effort routing pointer — on develop and **at closeout before `@output-compiler`**, run
  `citation-audit` then the Round-1/Round-2 protocol; unresolved `CU/FU/AE` block compile per Rule 12.
  **No fence touched.**
- **Claude interface (managed → propagate):** one-line pointers to the protocol doc in `CLAUDE.md`
  (Working Rule), `.claude/checklists/research-task-preflight.md` (step), and
  `.claude/prompts/research-report.prompt.md` (Mandatory Requirements). `researchteam init` prints
  one reminder line. Documented **opt-in** per-commit one-liner in the protocol doc (no default hook).

### 3.5 Component 5 — Propagation
`_manifest.py::MANAGED_FILES` += `scripts/check_citation_integrity.sh`,
`docs/citation-claim-audit-protocol.md` (R11 sequencing note). Plan + steps CSV under
`tmp/by-week/<ISO-week>/` per CLAUDE.md Rule 4.

### 3.6 Deliberately NOT done
No blocking pre-commit hook or new push-triggered workflow (R4 — non-propagating / sprawl); no new
numbered Workflow inside the `available_workflows` fence; no new Constitutional Rule (Rules 5/12
suffice); no `[@key]` resolution engine; no `conflict-log.csv` writes from the detector (R10); no
"proven genuine" verdict anywhere (R6); no agent-doc USER-EDITABLE pointers (R8).

---

## 4. Acceptance criteria
- [x] Detector discovers all 3 roots (nested + hidden), **excludes** `.agentteams-backups/` /
      `references/plans/` / asset dirs, prints code-tagged PASS/DEFECT/NEEDS-REVIEW + ceiling banner.
- [x] Dup key and missing-universal-field ⇒ `DEFECT` + exit 1 (blocking) / exit 0 (advisory env).
- [x] Drift, in-text miss (incl. the live `Shi 1995`), URL/DOI syntax, no-refs, citation-free
      project ⇒ `NEEDS-REVIEW`, **exit 0** — never a hard fail.
- [x] A valid parenthesized DOI (`10.1016/0022-0531(71)90013-5`) trips **nothing**.
- [x] `test_citation_integrity.sh` passes under bash 3.2 and modern bash, incl. the determinism guard.
- [x] `bash …/claude_researchteam_bridge.sh citation-audit [project]` works.
- [x] Upstream CI gains blocking test + advisory scan; **derived scaffold gains advisory scan only**,
      guarded; `validate_agentteams_update.sh` still passes; no `AGENTTEAMS` fence modified.
- [x] `researchteam update --dry-run` recognizes the two new `MANAGED_FILES`; no unrelated changes.
- [x] Orchestrator edit confined to USER-EDITABLE Project-Specific Notes; every fence intact.
- [x] CLAUDE.md / preflight / prompt / init each point to the **one** protocol doc (no duplicated
      procedure); no agent-doc USER-EDITABLE pointers added.
- [x] Every output distinguishes WELL-FORMED from RESOLVED; nothing claims to prove non-fabrication.

## 5. Rollback
Additive and independent; revert order: init reminder → prompt/preflight/CLAUDE.md → orchestrator
note → CI steps → bridge command → `MANAGED_FILES` entries → protocol doc → tests → detector. No
existing file destructively rewritten; all agent edits are outside fences and additive.
