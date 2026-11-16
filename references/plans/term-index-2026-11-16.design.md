# Design — Coded Term Definitions and a Synced Term-Occurrence Index

**Date:** 2026-11-16
**Trigger (operator request):** every researchteam project should define its terms in a coded register so
that consistent usage can be enforced; every appearance of a listed term across project documentation
should be indexed; and the index should be kept in sync by a hook or a similarly reliable trigger.
**Research basis:** `Projects/CodedTermIndexing/` (literature review, analysis section 7, conclusion).
**Status:** REVISED after audit and IMPLEMENTED. Section 0 records what the plan audit changed, and
section 0a what the review of the implementation changed. Sections 1 to 6 describe what was built.
`docs/term-index-protocol.md` is the authority for behaviour; where this record and the protocol differ,
the protocol governs.
**Audit findings in full:** `term-index-2026-11-16.audits.md`.
**Tracking:** `term-index-2026-11-16.plan.md` and `.steps.csv` in this folder.

---

## 0. What the audit changed

The draft was audited by `@adversarial`, `@conflict-auditor`, `@security` and `@code-hygiene`. The
adversarial verdict was RETHINK. The resolutions below are binding.

- **R1. The draft did not enforce usage (adversarial F-1, F-17).** Every blocking check in the draft
  concerned the register or the index. The one check on usage, a discouraged form in prose, was
  advisory. The research infers, as a judgement and not an established finding, that a register nothing
  checks usage against should not be expected to produce consistent usage.
  → A discouraged form outside a quotation, with no recorded exception, is a blocking `DEFECT[DISC]`.
  A deliberate use is recorded in the register's `allow` list with a reason. The exception is the audit
  trail.
- **R2. "Every project" was not delivered (F-2, F-16).** Nothing made a register exist, and deleting
  one turned the gate green.
  → A repository sets `term_index_require = true` in `.researchteam`. Every research project without a
  register is then a blocking `DEFECT[NOREG]`. Upstream sets it. Without the switch, a missing register
  blocks only when the project is named, which is the pre-compile check of Working Rule 8.
  → This is a decision: the research recommends a register for every project, and a derived repository
  is left to switch the requirement on for itself, so that an update cannot turn its validation red.
  → A project that has generated index files and no register is always a `DEFECT[ORPHAN]`.
  → A run that checked no register says so and does not print a pass line.
- **R3. The "unavoidable" gate exists only upstream (F-18, conflict C01, hygiene 5).** Derived
  repositories receive no test workflow, and the autosync gate does not call the bridge `validate`.
  → The trigger table says so. Where a repository's CI runs `validate`, the check cannot be skipped.
  Elsewhere the gate is local, and the protocol tells the operator how to add the step to a workflow.
  Shipping a workflow to derived repositories is deferred. It needs its own `@security` review.
- **R4. Staleness was defined two ways (F-15, C02).** A byte comparison against a fresh build would
  turn every derived repository red after any upstream change to the builder, and `researchteam update`
  cannot rebuild files under `Projects/`.
  → `[STALE]` means an input hash differs, or the hashes match and the generator version is the same
  but the files differ (a hand edit). When the hashes match and only the generator version differs, the
  result is an advisory `[REBUILD]`.
- **R5. One index file would conflict on every edit (F-12, F-13).**
  → The index is one file per document under `terminology/index/`, plus a small manifest. An edit to
  one document changes that document's file and one line of the manifest.
  → `glossary.md` is generated from the register alone and lists no occurrences, so it changes only
  when the register does. `terminology/` is never indexed, whatever `scope` says.
- **R6. The matcher was underspecified (F-6 to F-11, C19, C21, C24).** See section 2.3: one line break
  at most, never across a blank line or out of a heading; emphasis markers and hyphens handled;
  mixed-case labels match case-sensitively; quotation needs balanced marks; the reference-list headings
  are the citation detector's; scope globs have their own matcher so Python 3.10 and 3.13 agree.
- **R7. Period senses (F-3, C08, C09).** The historical-context protocol requires a source's own terms.
  → Its rule 2 overrides `[DISC]`: the message says to quote the source or record an exception, never to
  replace the source's term. A term with period senses is registered once per sense, each with a
  qualified label. The register holds the project's own usage. The interpretive map holds what terms
  meant in each period.
- **R8. Citations in definitions escaped the citation audit (F-14).**
  → `source` is the string `project definition` or a list of keys in the project's `.bib`. A key that is
  not in the `.bib` is a blocking `DEFECT[SRC]`.
- **R9. Code structure (hygiene 1, 2; C26).** One engine, no copied logic, no shell wrapper:
  `build_term_index.py` (engine and the commands that write), `check_term_index.py` (the gate, never
  writes) and `query_term_index.py`. Each stays under 550 lines. (Changed in section 0a, I4.)
- **R10. `validate` would break generic-profile repositories (C03, hygiene 5).** The bridge goes to
  every repository and the scripts only to scholarly ones.
  → The `validate` step is skipped when the check script is absent.
- **R11. Hook safety (`@security` conditions 1 to 18; F-19, F-22; C04).** The hook runs outside the
  sandbox. The builder confines every path to the repository, refuses symlinks, writes atomically
  under a lock, and reports only codes, term identifiers and positions. The wiring ships as an example
  the operator merges. `@security` ruled on this before implementation and reviews the diff.
  → The hook also runs on `Bash` and at `SessionStart`, where it rebuilds whatever is stale. That
  covers edits made by shell commands, by git, and between sessions.
- **R12. Naming (C25, F-23).** The protocol is `docs/term-index-protocol.md`, matching the scripts. A
  register carries `"schema": "researchteam-term-register"`. A `terms.json` without it is not treated
  as a register, so an instance's own file of that name cannot turn `validate` red.
- **R13. Where this plan lives (hygiene 6, C30).** Under `references/plans/`, which `init` does not copy.
- **R14. The project's reference generator (hygiene 7).** `references/build_references.py` and
  `sources.json` are removed after their last run. The `.bib` is the bibliography of record.
- **R15. Demonstrate on other projects before propagating (F-24).** Registers are added for
  `Projects/Matching/LaborMatchingMacroeconomics` and `Projects/ZeldaTimeline`, so the tool runs on a
  nested project and on two other subject areas.

## 0a. What the review of the implementation changed

The first implementation (commit 761c938) was reviewed by `@security`, `@code-hygiene` and
`@conflict-auditor`, and an independent reviewer hunted for defects by experiment. The findings are in
`term-index-2026-11-16.audits.md`. The resolutions:

- **I1. A crafted register or document could stall the builder (security N1 to N3a).** A form made only
  of markup characters, a scope pattern compiled to a backtracking expression, and three masking
  patterns could each take hours.
  → Every word of a form must hold a letter or a digit. Scope patterns are matched by a bounded matcher
  and never compiled. The masking patterns cannot rescan. Tests run hostile inputs under a time limit.
- **I2. The matcher was too slow for a hook (defect D1).** One run took minutes on a 200-document
  project against a 30-second hook timeout.
  → Forms are grouped by their first word and each document is scanned once. The hook skips a project
  whose hashes match its manifest, and after an edit rescans only the changed documents. `term-build`
  and the gate always rescan everything, so the gate still catches a hand-edited index file.
- **I3. Fail-open paths (hygiene H-01 to H-03; defects D3 to D5, D13).** A misspelt or commented
  `term_index_require`, a project the citation detector sees and this tool did not, a register placed in
  a folder of projects, a nested project, a project name with a space, and a changed generator version
  could each leave something unchecked.
  → The switch follows the marker reader's grammar and an invalid value stops the check. Project
  discovery uses the citation detector's markers and finds nested projects. Only a discovered project
  can be named. A different generator version no longer hides a missing or stray generated file.
- **I4. Size and readability (hygiene H-08).** The engine had been compressed to fit 550 lines at the
  cost of readability, and the hardening above needed more room.
  → The engine is its own module, `scripts/term_index_engine.py`, which only reads. The builder keeps
  the commands that write. Limits: engine 650 lines, builder 300, gate 250, query 100. Six files are
  managed, not five. The result of a pass over a project is a small dataclass.
- **I5. Markdown handling (defects D6 to D9, D14, D15).** Fence length and info strings, code spans with
  several backticks, reference-link definitions, a heading's last line, and front matter were handled
  wrongly. All fixed, each with a test.
- **I6. Robustness (defects D2, D10 to D12; hygiene H-04 to H-07; security N3b to N7).** A form of only
  hyphens; leftover temporary files; a traceback on deeply nested input; `init` on a file; an unreadable
  file reported as a defect and not as an error; the discouraged-form rule written twice; paths with
  unusual characters in hook messages; `validate` honouring a caller's `RT_ROOT`. All fixed.
- **I7. Overlapping forms.** The rule is now: at one starting position the longest form wins, and
  otherwise the form that starts first. The protocol says so.
- **I8. Upgrades (consistency K07).** The generator version must change whenever the generated bytes
  change. A test pins the output of a fixture to the version.
- **I9. Sense in the registers (consistency K11, K15 to K19).** The demonstration register's definition of
  "occurrence index" was narrower than the project's own use of the term for concordances. It was
  widened. Two definitions in the Matching register and three source attributions in the Zelda register
  were corrected to match those projects' texts.
- **I10. Records (consistency K22).** The full findings of the plan audit and of this review are in a
  tracked file.

- **I11. Second review of the fixes (commit 500d3cc).** `@security` and `@code-hygiene` reviewed the fix
  commit and found more. The matcher's work still grew with the number of forms sharing a first word,
  and the code-span pattern and the glob matcher were still super-linear: forms are now capped at 16
  words and 32 per first word, scope lists at 64 patterns, code spans are paired in one pass, and the
  glob matcher makes one pass per token. A committed index file reused by the hook is checked record by
  record against the register before it is trusted. `term-init` refuses a path through a symbolic link
  and a folder inside a project. Two different tests of "the same form" became one. Project discovery
  now matches the citation detector's, hidden directories included, and a test runs both on one tree.
  An empty `term_index_require` is an error. The timing tests no longer depend on the clock: they
  compare the time for an input with the time for twice that input.

- **I12. Third review (commit 2f5c99f).** `@security` found that the cap on forms per first word was
  counted per offset and so could be multiplied, and that `term-init` passed when `Projects/` was itself
  a symbolic link. `@code-hygiene` found the same cap problem, that plural keys were still built two
  ways (so a form ending in a separator could take another term's matches), and that the protocol
  called the project search "the detector's" while it differed in three ways. All fixed: the cap counts
  across offsets; one function builds every key a form answers to, and a form may not begin or end with
  a separator; the differences are stated. The engine's limit was raised to 700 lines so the section
  dividers could be restored. The timing test now compares an input with one four times as long.
- **I13. Final review (commit 95cc967).** `@security` passed the head. `@code-hygiene` asked for two more
  validation rules, because a form that passed validation could still never match: a form may not begin
  or end with any white space (a no-break space included), and a hyphen in a form may not touch a space
  or another hyphen. Both added, with the fourth difference from the citation detector stated.

Corrections to this record, found by the same review: acceptance criterion 13 said the hook exits 2 only
for a broken register; it also exits 2 for a discouraged form in the file just edited. An oversized
document is a `[SCOPE]` defect, not `[SCHEMA]`. A wrapped form continues after a blockquote prefix or
indentation; a list marker on the next line is not skipped. No cases were added to
`tests/test_init_personalization.py`; the managed-block test is in `tests/test_term_index.py`.
`[NOSRC]` is advisory although the research recommends recording a source for every definition: a
project may register a term before it has settled where the definition comes from.

Not adopted, with reasons:

- **A hook entry point under `.claude/hooks/` (F-19).** That directory is generated by agentteams.
  `@security` ruled that an example invoking the script under `scripts/` is acceptable, the same
  arrangement as the existing toolchain hook. The example's comment states the exposure.
- **A bash scenario suite (F-27, C12).** The new scripts are Python, and `@code-hygiene` ruled pytest
  correct for them. The autosync gate's detector loop is unchanged.
- **`brief.json` criteria (C16).** Editing a brief regenerates agent files. Deferred.
- **A `doctor` check and an `update` nudge for the hook (F-20, C31).** Deferred. The protocol tells the
  operator to merge the example.
- **Senses as a schema feature (F-3).** Deferred. R7 gives the interim rule.

## 1. Requirements from the research

| # | Requirement | Research basis |
|---|---|---|
| Q1 | One concept-oriented record per term: identifier, one preferred label, definition, accepted variants, discouraged variants | Vocabulary control; the qualitative codebook record |
| Q2 | A form belongs to one concept only | One-to-one naming |
| Q3 | Occurrences are found by matching plain prose. Authors do not mark terms | The gap in marked-term toolchains |
| Q4 | The index is generated and never edited by hand | Machine generation as the condition of currency |
| Q5 | The index records content hashes of its inputs, and staleness is decided from them | Verifying traces in build systems, by analogy |
| Q6 | Triggers are layered. A check that cannot be skipped is the gate wherever one exists | Hooks can be bypassed; this project's inference |
| Q7 | Usage is checked against the register, and a deliberate departure is recorded | A register that is not checked; variation is sometimes deliberate |
| Q8 | The ceiling is stated | Matching finds forms, not meanings |
| Q9 | Each definition records its source, or is marked as the project's own | Audit trail |

## 2. Design

### 2.1 Files, per project

Under `<project>/terminology/`, where `<project>` is a research project directory under `Projects/`,
at any depth:

- `terms.json` — the term register. Authored.
- `term-index.json` — the manifest: register hash, generator version, and each indexed document's hash.
  Generated.
- `index/<document path>.json` — that document's occurrences. Generated.
- `glossary.md` — a reading view of the register. Generated.

All generated files are committed. They hold no timestamps and no absolute paths. Paths are POSIX and
relative to the project.

### 2.2 The register

```json
{
  "schema": "researchteam-term-register",
  "schema_version": "1.0",
  "scope": {"include": ["**/*.md"], "exclude": []},
  "terms": [
    {
      "id": "occurrence-index",
      "label": "occurrence index",
      "definition": "A derived record of every place a registered term or one of its listed variants appears in the project's documents.",
      "variants": ["occurrence indexing"],
      "discouraged": ["term concordance"],
      "source": "project definition",
      "notes": "Optional."
    }
  ],
  "allow": [
    {"term": "occurrence-index", "file": "01-literature-review.md", "reason": "Reports the source's own word."}
  ]
}
```

- Required per term: `id` (a lower-case slug), `label`, `definition`. Optional: `variants`,
  `discouraged`, `source`, `notes`, `plural` (default `true`).
- An unknown key is a `[SCHEMA]` defect, so a misspelt key is not silently ignored.
- `allow` records a deliberate use of a term's discouraged forms in one file, with a reason.
- Limits bound the size of a register and the work of matching. They are listed in
  `docs/term-index-protocol.md` ("The register") and are not repeated here.
- An empty `terms` list is valid. `term-init` writes one.

### 2.3 Matching

- A form matches whole words. A letter, a digit or a hyphen on either side prevents a match.
- A form written in lower case matches without regard to case. A form containing a capital letter
  matches exactly.
- Between the words of a form: spaces, or one line break (with a blockquote prefix or indentation on the
  next line), or a hyphen. Emphasis markers around a word are ignored. A match never crosses a blank line or
  leaves a heading.
- With `plural` on, the last word also matches with `s` or `es`. Generated plurals count when forms are
  compared for `[AMBIG]`.
- Where two forms could start at one place, the longest wins; otherwise the one that starts first.
- Not searched: fenced code blocks, inline code, link targets, bare URLs, HTML comments, YAML front
  matter, and any section headed References, Bibliography, Works Cited or Sources (the citation
  detector's headings).
- An occurrence is `quoted` when it is in a blockquote, or between balanced double quotation marks,
  straight or curly, in the same paragraph. A paragraph with an odd number of straight marks exempts
  nothing.

### 2.4 The checks

`python3 scripts/check_term_index.py [project]`. Exit 0 clean, 1 defect, 2 usage or environment error.
The finding codes, with which block and which are advisory, are defined in `docs/term-index-protocol.md`
("The gate") and are not repeated here. In outline: a malformed or ambiguous register, a `source` key
missing from the `.bib`, an empty or unsafe scope, a stale or hand-edited index, a discouraged form used
without a recorded exception, an orphaned index and a missing register all block. A changed generator
version, an unused term, a definition without a source and a count of quoted discouraged forms are
advisory. The check never writes a file. The codes map onto the conflict-auditor taxonomy: `[AMBIG]` and
`[DISC]` to `TERM_MISMATCH`, `[STALE]` to source drift.

### 2.5 The triggers

| Layer | Trigger | What it does | What it misses |
|---|---|---|---|
| 1 | Claude Code hook: `PostToolUse` on `Write`, `Edit`, `MultiEdit`, `NotebookEdit` and `Bash`; and `SessionStart` | Rebuilds the edited file's project, or every project whose inputs changed | Sessions where the operator has not merged the example; other harnesses; edits while no session runs, until the next one starts |
| 2 | `term-build` | Rebuilds on request | Being forgotten |
| 3 | Optional Git `pre-commit` snippet, check only | Refuses a commit while a check fails | `--no-verify`; clones that have not installed it |
| 4 | `claude_researchteam_bridge.sh validate` | Runs the check over every project | Repositories whose CI does not run `validate` |

Upstream, `tests.yml` runs `validate`, so layer 4 cannot be skipped there. A derived repository has no
such workflow unless its owner adds one. There the gate is the local `validate` and the pre-compile
check of Working Rule 8, both of which depend on being run.

The check goes inside `validate`, and not under `scripts/validate.d/`, because `validate.d` is
repository-owned and is not synced. No other content check runs in `validate`. This one does because a
stale index is a mechanical fact about committed files, like a broken fence.

### 2.6 Commands

```bash
bash scripts/claude_researchteam_bridge.sh term-init <project>
bash scripts/claude_researchteam_bridge.sh term-build [project]
bash scripts/claude_researchteam_bridge.sh term-check [project]
bash scripts/claude_researchteam_bridge.sh term-query <project> "<label or id>"
```

## 3. Files changed

New, managed (scholarly profile): `docs/term-index-protocol.md`, `scripts/term_index_engine.py`,
`scripts/build_term_index.py`, `scripts/check_term_index.py`, `scripts/query_term_index.py`,
`.claude/settings.terms.example.json`.

Changed:

- `scripts/claude_researchteam_bridge.sh` — four commands; the guarded `validate` step.
- `researchteam/_manifest.py` — six files join `SCHOLARLY_MANAGED_FILES` (with `scripts/term_index_engine.py`).
- `CLAUDE.md` and `researchteam/scaffold/CLAUDE.template.md` — Working Rule 8, identical in both, worded
  for a project that keeps a register.
- `.researchteam` — `term_index_require = true`.
- `.claude/README.md`, `.claude/checklists/research-task-preflight.md`,
  `.claude/prompts/research-report.prompt.md`.
- `docs/claude-interface-bridge.md`, `docs/researchteam-framework.md`, `docs/retrieval-surfaces.md`,
  `docs/citation-claim-audit-protocol.md`, `docs/historical-context-protocol.md`.
- `docs_src/bridge-reference.md`, `docs_src/guides.md`, `docs_src/api-reference/manifest.md`,
  `docs_src/api-reference/scripts.md`.
- `CHANGELOG.md`.

Project-owned: the research project `Projects/CodedTermIndexing/` itself, and `terminology/` in `Projects/CodedTermIndexing`,
`Projects/Matching/LaborMatchingMacroeconomics` and `Projects/ZeldaTimeline`.

Tests: `tests/test_term_index.py`, and cases added to `tests/test_bridge_validate_hooks.py`.

Not changed: generated agent files, `.claude/settings.json`, `toolchain.lock`, workflows, `brief.json`,
the scaffold brief, the autosync gate.

## 4. Acceptance criteria

1. Two builds of a non-empty fixture give byte-identical files, whatever order the files were created in.
2. `[STALE]` fires when a document changes, when the register changes, when a document enters or
   leaves the scope, and when a generated file is edited by hand. A rebuild clears it.
3. Unchanged inputs with a different generator version give `[REBUILD]` and exit 0.
4. A form wrapped across one line break is indexed once, at the line where it starts. A form split by
   a blank line, or running out of a heading, is not indexed.
5. A form inside a fenced block (both fence styles), inline code, a URL, an HTML comment or a
   reference list is not indexed. A form in emphasis, or hyphenated, is.
6. A lower-case form matches a capitalised use. A form with a capital letter does not match the
   lower-case word.
7. A discouraged form in prose exits 1 with `[DISC]`. The same form in a blockquote, between straight
   or curly quotation marks, or covered by an `allow` entry does not. An unbalanced quotation mark
   exempts nothing.
8. `[AMBIG]` fires for a form shared by two terms, for a collision created by the plural rule, and for a
   form both accepted and discouraged.
9. `[SCHEMA]` fires for bad JSON, a missing field, a repeated id, a wrong type, an unknown key and a
   broken limit (the limit on scope patterns is reported as `[SCOPE]`). `[SRC]` fires for a key missing from the `.bib`. `[SCOPE]` fires for an empty scope.
10. `[NOREG]` blocks a named project, and blocks in a scan when the switch is set. Without the switch a
    scan reports `NEEDS-REGISTER` and exits 0. `[ORPHAN]` fires when the register is deleted.
11. A run with no register says that nothing was checked and prints no pass line.
12. The check writes nothing. A snapshot of the tree is unchanged after it runs.
13. The hook rebuilds the right project for a file in a nested project, rebuilds stale projects for a
    payload with no file path, does nothing for a path outside every project, ignores malformed input,
    and exits 2 only for a discouraged form in the file just edited or a broken register that was itself
    just edited. Its message carries no register or document text.
14. Two builds run at once leave valid files.
15. A definition holding markup or instruction-shaped text is escaped in the glossary.
16. `validate` passes when the check script is absent, passes when no project has a register and the
    switch is off, and fails on a stale index.
17. The six files are in `SCHOLARLY_MANAGED_FILES` and exist, and the `CLAUDE.md` managed block matches
    the scaffold's.
18. All three projects pass `term-check`, and a discouraged form seeded into a deliverable makes it
    fail.
19. The suite and `validate` pass on Python 3.10 and 3.13.

## 5. The honest ceiling

`WELL-FORMED AND CURRENT ≠ CONSISTENT IN MEANING`. A clean check establishes that the register is well
formed, that no form is claimed twice, that the index matches the documents, and that no discouraged
form appears unquoted without a recorded exception. It does not establish that a term is used in its
defined sense, that a definition is a good one, or that every term the project relies on is registered.
The index covers the files in scope, which by default are the project's markdown files. Matching finds
forms.

## 6. Out of scope

- Automatic extraction of candidate terms.
- A register shared between projects.
- Stemming beyond the simple plural.
- Rewriting prose to replace a discouraged form.
- A workflow for derived repositories.
