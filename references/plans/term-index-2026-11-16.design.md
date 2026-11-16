# Design — Coded Term Definitions and a Synced Term-Occurrence Index

**Date:** 2026-11-16
**Trigger (operator request):** every researchteam project should define its terms in a coded register so
that consistent usage can be enforced; every appearance of a listed term across project documentation
should be indexed; and the index should be kept in sync by a hook or a similarly reliable trigger.
**Research basis:** `Projects/CodedTermIndexing/` (literature review, analysis section 7, conclusion).
**Status:** REVISED after audit. Section 0 records what the audit changed. Sections 1 to 6 are the plan
that is implemented.
**Tracking:** `term-index-2026-11-16.plan.md` and `.steps.csv` in this folder.

---

## 0. What the audit changed

The draft was audited by `@adversarial`, `@conflict-auditor`, `@security` and `@code-hygiene`. The
adversarial verdict was RETHINK. The resolutions below are binding.

- **R1. The draft did not enforce usage (adversarial F-1, F-17).** Every blocking check in the draft
  concerned the register or the index. The one check on usage, a discouraged form in prose, was
  advisory. The research itself reports that a register nothing checks usage against should not be
  expected to produce consistent usage.
  → A discouraged form outside a quotation, with no recorded exception, is a blocking `DEFECT[DISC]`.
  A deliberate use is recorded in the register's `allow` list with a reason. The exception is the audit
  trail.
- **R2. "Every project" was not delivered (F-2, F-16).** Nothing made a register exist, and deleting
  one turned the gate green.
  → A repository sets `term_index_require = true` in `.researchteam`. Every research project without a
  register is then a blocking `DEFECT[NOREG]`. Upstream sets it. Without the switch, a missing register
  blocks only when the project is named, which is the pre-compile check of Working Rule 8.
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
  writes) and `query_term_index.py`. Each stays under 550 lines.
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
- Limits, enforced as `[SCHEMA]`: 5,000 terms, 50 forms per term, 200 characters per form, a 1 MB
  register, 5 MB per document.
- An empty `terms` list is valid. `term-init` writes one.

### 2.3 Matching

- A form matches whole words. A letter, a digit or a hyphen on either side prevents a match.
- A form written in lower case matches without regard to case. A form containing a capital letter
  matches exactly.
- Between the words of a form: spaces, or one line break (with a blockquote or list prefix on the next
  line), or a hyphen. Emphasis markers around a word are ignored. A match never crosses a blank line or
  leaves a heading.
- With `plural` on, the last word also matches with `s` or `es`. Generated plurals count when forms are
  compared for `[AMBIG]`.
- Where forms overlap, the longest match wins.
- Not searched: fenced code blocks, inline code, link targets, bare URLs, HTML comments, YAML front
  matter, and any section headed References, Bibliography, Works Cited or Sources (the citation
  detector's headings).
- An occurrence is `quoted` when it is in a blockquote, or between balanced double quotation marks,
  straight or curly, in the same paragraph. A paragraph with an odd number of straight marks exempts
  nothing.

### 2.4 The checks

`python3 scripts/check_term_index.py [project]`. Exit 0 clean, 1 defect, 2 usage or environment error.

| Class | Code | Meaning |
|---|---|---|
| `DEFECT` | `[SCHEMA]` | The register cannot be parsed, breaks a limit, has a wrong type or an unknown key, or repeats an `id` |
| `DEFECT` | `[AMBIG]` | One form is claimed by two terms, or is both accepted and discouraged |
| `DEFECT` | `[SRC]` | A `source` key is not in the project's `.bib` |
| `DEFECT` | `[SCOPE]` | The scope matches no document, or a pattern is absolute or contains `..` |
| `DEFECT` | `[STALE]` | An index file is missing, an input hash differs, or the files were edited by hand |
| `DEFECT` | `[DISC]` | A discouraged form is used outside a quotation with no `allow` entry |
| `DEFECT` | `[ORPHAN]` | Generated index files exist and the register does not |
| `DEFECT` | `[NOREG]` | No register: when the project is named, or everywhere when `term_index_require = true` |
| `NEEDS-REVIEW` | `[REBUILD]` | The inputs are unchanged and the generator version differs |
| `NEEDS-REVIEW` | `[UNUSED]` | A registered term never occurs |
| `NEEDS-REVIEW` | `[NOSRC]` | A definition has no `source` |
| `NEEDS-REVIEW` | `[QUOTED]` | A count of discouraged forms inside quotations, so that quoting is visible |
| `NEEDS-REGISTER` | — | In a scan without the switch, a research project has no register |

`TERM_INDEX_ADVISORY=1` downgrades defects to exit 0 and prints an advisory-mode line. The check never
writes a file. The codes map onto the conflict-auditor taxonomy: `[AMBIG]` and `[DISC]` to
`TERM_MISMATCH`, `[STALE]` to source drift.

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

New, managed (scholarly profile): `docs/term-index-protocol.md`, `scripts/build_term_index.py`,
`scripts/check_term_index.py`, `scripts/query_term_index.py`, `.claude/settings.terms.example.json`.

Changed:

- `scripts/claude_researchteam_bridge.sh` — four commands; the guarded `validate` step.
- `researchteam/_manifest.py` — five files join `SCHOLARLY_MANAGED_FILES`.
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

Project-owned: `terminology/` in `Projects/CodedTermIndexing`,
`Projects/Matching/LaborMatchingMacroeconomics` and `Projects/ZeldaTimeline`.

Tests: `tests/test_term_index.py`, and cases added to `tests/test_bridge_validate_hooks.py` and
`tests/test_init_personalization.py`.

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
   broken limit. `[SRC]` fires for a key missing from the `.bib`. `[SCOPE]` fires for an empty scope.
10. `[NOREG]` blocks a named project, and blocks in a scan when the switch is set. Without the switch a
    scan reports `NEEDS-REGISTER` and exits 0. `[ORPHAN]` fires when the register is deleted.
11. A run with no register says that nothing was checked and prints no pass line.
12. The check writes nothing. A snapshot of the tree is unchanged after it runs.
13. The hook rebuilds the right project for a file in a nested project, rebuilds stale projects for a
    payload with no file path, does nothing for a path outside the repository or through a symlink,
    survives malformed input, and exits 2 only for a broken register that was itself just edited. Its
    message carries no register text.
14. Two builds run at once leave valid files.
15. A definition holding markup or instruction-shaped text is escaped in the glossary.
16. `validate` passes when the check script is absent, passes when no project has a register and the
    switch is off, and fails on a stale index.
17. The five files are in `SCHOLARLY_MANAGED_FILES` and exist, and the `CLAUDE.md` managed block matches
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
