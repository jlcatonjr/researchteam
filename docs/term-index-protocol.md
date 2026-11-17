# Term Register and Synced Term Index — Protocol

This is the single authoritative procedure for defining a project's terms and indexing their use.
`CLAUDE.md`, the preflight checklist, the research-report prompt and the bridge reference point here. The
finding codes are defined in this document and nowhere else.

## What it is

Each research project keeps three things under `<project>/terminology/`:

- a **term register** (`terms.json`): one coded definition per concept, with one preferred label, the
  accepted variants and the discouraged forms;
- a **term index** (`term-index.json` and `index/`): a generated record of every place a registered form
  appears in the project's documents;
- a **glossary** (`glossary.md`): a generated reading view of the register.

The register is written by people and agents. The index and the glossary are generated, committed, and
never edited by hand. Hooks rebuild the index as files change, and a check verifies it from recorded
content hashes.

The design follows the research project `Projects/CodedTermIndexing/` in the upstream repository.

## The honest ceiling (read this first — it is binding)

**`WELL-FORMED AND CURRENT ≠ CONSISTENT IN MEANING`.** A clean check establishes that:

- the register is well formed and no form is claimed by two terms;
- the index matches the documents and the register it was built from;
- no discouraged form appears outside a quotation without a recorded exception.

It does not establish that a term is used in its defined sense, that a definition is a good one, or that
every term the project relies on has been registered. Matching finds forms, not meanings. The index
covers the files in scope, which by default are the project's markdown files. An occurrence is a place
where a form appears. It is not evidence, and the index is not a retrieval surface for sources
(`docs/retrieval-surfaces.md`).

## The register

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
      "notes": "Optional scope notes."
    }
  ],
  "allow": [
    {"term": "occurrence-index", "file": "01-literature-review.md", "reason": "Reports the source's own word."}
  ]
}
```

| Field | Required | Meaning |
|---|---|---|
| `schema` | yes | Must be `researchteam-term-register`. A `terms.json` without it is not treated as a register |
| `terms[].id` | yes | A lower-case slug of 1 to 64 letters, digits and hyphens, starting with a letter or digit |
| `terms[].label` | yes | The preferred form |
| `terms[].definition` | yes | The definition, in the project's own words or a source's |
| `terms[].variants` | no | Other accepted forms |
| `terms[].discouraged` | no | Forms not to be used for this concept |
| `terms[].source` | no | `"project definition"`, or a list of keys in the project's `.bib` |
| `terms[].notes` | no | Scope notes, exclusions, period or school |
| `terms[].plural` | no | `false` turns off the automatic plural. Default `true` |
| `scope` | no | Which files are indexed. Default: every `.md` file in the project. `terminology/` is never indexed |
| `allow` | no | A recorded exception: this term's discouraged forms may be used in this file, for this reason |

An unknown key is a defect, so a misspelt key is not silently ignored. `schema_version`, when present,
must be `"1.0"`. Every word of a form must contain a letter or a digit. A form may not begin or end with
white space, a hyphen, an underscore, `>` or `*`, and inside a form a hyphen may not touch a space or
another hyphen. Limits: 5,000 terms, 50 forms per
term, 20,000 forms in all, 200 characters and 16 words per form, 32 forms beginning with the same word
(counted separately for lower-case forms and for forms with a capital, by the first run of letters and
digits in the word), 64 scope patterns in each list and 200 characters per pattern, a 1 MB register,
5 MB per document. The limits bound the work of
matching, so that no register or document can stall the hook or the gate. An empty `terms` list is valid.

Two forms are the same form when they differ only in case, or in what stands between their words: a
space, a line break, a hyphen, an underscore, an emphasis marker or a blockquote prefix. "snake_case"
and "snake case" are one form, so two terms may not claim them. That is a rule about who owns a form.
It does not widen matching: a form written with an underscore matches text written with an
underscore.

Rules for writing a register:

1. **One concept, one record.** Give each concept one preferred label. List the other forms the project
   accepts as variants.
2. **One form, one concept.** A form may not belong to two terms. A word with two senses in the project
   is registered once per sense, each with a qualified label, such as "virtue (Stoic)" and "virtue
   (Christian)". A qualified label matches only that literal text, so list as variants the phrases the
   documents really use for each sense, such as "Stoic virtue". The bare word cannot belong to both
   terms, and its uses are then not indexed. This is a limit of matching by form.
3. **Record where a definition comes from.** Use `"project definition"` for the project's own, or the
   `.bib` keys of the sources it follows. A definition with no `source` is reported for review and does
   not block: a project may register a term before it has settled where the definition comes from.
4. **Do not register common words.** A label that is also an ordinary word will match its ordinary uses.
5. **Record deliberate departures.** Where a document must use a discouraged form outside a quotation,
   add an `allow` entry with the reason.

## How matching works

- A form matches whole words. A letter, a digit or a hyphen on either side prevents a match.
- A form written in lower case matches without regard to case. A form with a capital letter matches
  exactly.
- Between the words of a form the text may have spaces, one line break, or a hyphen. Emphasis markers are
  ignored. A match never crosses a blank line or leaves a heading.
- The last word also matches with `s` or `es`, unless `plural` is `false`. List irregular plurals as
  variants.
- Where two forms could start at the same place, the longest wins. Where they overlap otherwise, the
  one that starts first wins, so an accepted form can hide a discouraged form that begins inside it.
- Not searched: fenced code blocks, inline code, link targets, reference-link definitions, bare URLs,
  HTML comments, YAML front matter at the top of a file, and any section whose heading is References,
  Bibliography, Works Cited or Sources, alone or followed by a space and more words (the citation
  detector's rule). Such a section ends at the next heading.
- Not indexed: `terminology/` itself, hidden directories, symbolic links, and a nested project, which has
  its own register.
- Scope patterns use `**/`, `**`, `*` and `?`. Other characters, brackets and braces included, are
  literal.
- An occurrence counts as quoted when it is in a blockquote, or between balanced double quotation marks,
  straight or curly, in the same paragraph. In a paragraph with an odd number of straight marks, the
  straight marks exempt nothing; curly pairs and blockquotes still do. Single quotation marks do not
  count.

## Relation to the historical-context protocol

`docs/historical-context-protocol.md`, rule 2, requires a source's own terms and those of its period. That
rule overrides this one. A `[DISC]` finding never means "replace the source's word". It means one of:

- use the preferred label, where the passage is in the project's own voice;
- quote the source, where the form is the source's;
- add an `allow` entry with the reason, where the form is a reported usage that cannot be quoted.

The register holds the project's own usage. The interpretive map holds what key terms meant in each
period. A register entry may point to the map in its `notes`.

## Who does what

Component experts are the project's own: `@<component-slug>-expert`, one per `brief.json` component.

| Agent | Role under this protocol |
|---|---|
| Expert of the scoping / research-plan component | Starts the register with the terms the research question depends on. The research plan points to the register. Where a deliverable restates a definition for its reader, the register governs |
| `@interpretation-advisor` | Says which terms have period or school senses, so they are registered once per sense |
| Experts of the literature-review and analysis components | Propose terms and variants as the sources introduce them |
| `@primary-producer` | Uses the preferred labels. Adds an `allow` entry, with a reason, for a deliberate departure |
| `@reference-manager` | Confirms that each `source` key is in the project's `.bib` |
| `@technical-validator` | Puts each sourced definition on the claim ledger |
| `@conflict-auditor` | Treats `[AMBIG]` and `[DISC]` as `TERM_MISMATCH` findings and `[STALE]` as source drift |
| `@adversarial` | Asks whether a preferred label hides a contested sense |

## Commands

```bash
bash scripts/claude_researchteam_bridge.sh term-init <project>                 # write a starter register
bash scripts/claude_researchteam_bridge.sh term-build [project]                # rebuild index and glossary
bash scripts/claude_researchteam_bridge.sh term-check [project]                # the gate
bash scripts/claude_researchteam_bridge.sh term-query <project> "<label, variant or id>"  # where a term occurs; or --list
# direct: python3 scripts/build_term_index.py build|init|hook ; scripts/check_term_index.py ; scripts/query_term_index.py
# all three import scripts/term_index_engine.py, so they read a register and match text the same way
```

`<project>` is a project's path under `Projects/`, or its directory name when that is unique.

## The gate

`scripts/check_term_index.py [project]` builds the index in memory and compares it with the committed
files. It never writes. Exit 0 means no defect, 1 means at least one, and 2 means a usage or environment
error.

| Class | Code | Meaning | Exit effect |
|---|---|---|---|
| `DEFECT` | `[SCHEMA]` | The register cannot be read or parsed, breaks a limit, has a form of a shape the rules above refuse, has a wrong type or an unknown key, or repeats an `id` | blocks |
| `DEFECT` | `[AMBIG]` | One form is claimed by two terms, or is both accepted and discouraged. Automatic plurals count | blocks |
| `DEFECT` | `[SRC]` | A `source` key is in no `.bib` file under the project's folder (those of a nested project included). A repository-level bibliography is not consulted | blocks |
| `DEFECT` | `[SCOPE]` | The scope matches no document, a pattern leaves the project, holds a backslash or is too long, a list has more than 64 patterns, or a document is not a regular file or is too large | blocks |
| `DEFECT` | `[STALE]` | No index was built, a document or the register changed since it was built, or a generated file is missing, was edited by hand, or is not one the builder writes | blocks |
| `DEFECT` | `[DISC]` | A discouraged form is used outside a quotation with no `allow` entry | blocks |
| `DEFECT` | `[ORPHAN]` | Files exist at the generated paths (`terminology/term-index.json` or `terminology/index/`) and there is no register | blocks |
| `DEFECT` | `[NOREG]` | The project has no register (see "Which projects need a register") | blocks |
| `NEEDS-REVIEW` | `[REBUILD]` | The inputs are unchanged, and the index was built by another version of the builder | advisory |
| `NEEDS-REVIEW` | `[UNUSED]` | A registered term never occurs | advisory |
| `NEEDS-REVIEW` | `[NOSRC]` | A definition has no `source` | advisory |
| `NEEDS-REVIEW` | `[QUOTED]` | How many discouraged forms sit inside quotations. Exempt, and counted so that quoting stays visible | advisory |
| `NEEDS-REGISTER` | — | In a scan, a research project has no register and the repository does not require one | advisory |

`TERM_INDEX_ADVISORY=1` downgrades every `DEFECT` to exit 0 and prints an `ADVISORY MODE` line. The bridge
`validate` command ignores that variable.

Staleness is decided from content hashes, not file times. The manifest records the SHA-256 of the
register and of each indexed document. `[REBUILD]` exists so that an upgrade of the builder does not turn
a repository red: when only the builder changed, the check asks for a rebuild and does not block.

### Which projects need a register

- A project named on the command line must have one. `term-check <project>` is the pre-compile check.
- A repository that sets `term_index_require = true` in `.researchteam` requires one for every research
  project, and a scan reports `[NOREG]` for each that lacks it. The value is `true`, `yes`, `on` or `1`,
  or `false`, `no`, `off` or `0`. Any other value, an empty one included, stops the check with an error,
  so a misspelling cannot switch the requirement off unnoticed. A research project is a directory under
  `Projects/` that holds a research plan, a `references/` folder or a numbered deliverable. The search
  follows the citation detector's: hidden directories are searched, and folders named `plans`,
  `JSModules`, `cssfiles`, `node_modules`, `.git` and `.agentteams-backups` are not. It differs in four
  ways: only `Projects/` is searched (the detector also searches `.projects/`), it stops at twelve
  levels, a project's own `terminology/` folder is not searched, and a directory that holds a term
  register is a project even without one of those markers.
- Otherwise a scan reports `NEEDS-REGISTER` and does not block.

A run that found no register to check says `NOTHING CHECKED` and prints no pass line.

## When it runs

| Layer | Trigger | What it does | What it misses |
|---|---|---|---|
| 1 | Claude Code hooks: after `Write`, `Edit`, `MultiEdit`, `NotebookEdit` and `Bash`, and at `SessionStart` | Rebuilds the edited file's project, or every project whose inputs changed. Reports a discouraged form left in the file just edited, or, for a register that was just edited, what stops it loading (`[SCHEMA]`, `[AMBIG]`, `[SCOPE]`). Other findings, `[SRC]` among them, come from the gate | Sessions where the operator has not merged the example. Other harnesses. Edits made while no session runs, until the next one starts |
| 2 | `term-build` | Rebuilds on request | Being forgotten |
| 3 | An optional Git `pre-commit` check | Refuses a commit while the check fails | `--no-verify`. Clones that have not installed it |
| 4 | `claude_researchteam_bridge.sh validate` | Runs the check over every project | Repositories whose CI does not run `validate` |

No layer is both immediate and impossible to skip, so they are layered. Layer 4 cannot be skipped where
continuous integration runs `validate`. The upstream repository's test workflow does. **A derived
repository has no such workflow unless its owner adds one** (see "Adding the gate to a derived
repository's CI"). Without it the gate is the local `validate` and the pre-compile `term-check`, both of
which depend on being run.

- **At initiate / develop.** Start the register with the research plan. Run `term-build` after editing
  when the hooks are not installed.
- **Pre-compile closeout.** Run `term-check <project>` next to the citation audit and the
  historical-context check. Any `DEFECT` blocks compilation.

### Installing the hooks (operator step)

Merge the `hooks` entries of `.claude/settings.terms.example.json` into `.claude/settings.json`.
researchteam never edits `settings.json`. Hooks run outside the sandbox, and the command runs a script
under `scripts/`, which agents can edit. Merging the example gives that script the same trust as the
toolchain check. The builder writes only under `<project>/terminology/`, refuses symbolic links, makes no
network call and starts no process. Its report to the agent carries finding codes, term identifiers,
file paths and positions, never document or register text. A path with unusual characters is withheld.
The hook skips a project whose files have not changed, and after an edit it rescans only the documents
that changed. `term-build` and the gate always rescan everything.

### Optional Git hook (opt-in, per clone)

There is no default Git hook: `.git/hooks` is not version-controlled. To refuse a commit while the check
fails, add this to your own `.git/hooks/pre-commit`. It checks and never rebuilds:

```sh
python3 -B scripts/check_term_index.py || exit 1
```

### Adding the gate to a derived repository's CI

`researchteam workflow-sync --workflow validate` writes `.github/workflows/researchteam-validate.yml`: a
read-only workflow that runs the bridge validator on pull requests and on pushes to `main`. It is opt-in.
`researchteam init` does not install it and `researchteam update` never touches it. Run again later, the
command keeps the workflow's `on:` block as the repository has it. Give a new workflow the repository's
own security review.

A repository that already has a test workflow can add one step to it instead:

```yaml
- name: Bridge validate
  run: bash scripts/claude_researchteam_bridge.sh validate
```

`researchteam doctor` says whether a workflow runs the validator and whether the hooks are wired, and
`researchteam update` prints a reminder while a project has a register and the hooks are not wired.

## Upgrades and updates

- `researchteam update` syncs the scripts and this document. It never writes `Projects/`, so it cannot
  rebuild an index. After an update that changes the builder, `term-check` reports `[REBUILD]`. Run
  `term-build` and commit the result.
- The builder carries a generator version, and it must change whenever the generated bytes would change
  for the same inputs. That is how the gate tells an upgrade (advisory `[REBUILD]`) from a hand edit
  (blocking `[STALE]`). A test upstream pins the output to the version.
- Commit a project's `terminology/` files before running `researchteam update`. The update validator
  reports changed files outside its own scope.
- A pull request that changes the builder's output should also rebuild the upstream projects' indexes.

## What this protocol does not do

- It does not check meaning (the ceiling above).
- It does not extract candidate terms. A person or an agent decides what to register.
- It does not rewrite prose.
- It does not share a register between projects.
- It does not stem words beyond the simple plural.
- It does not install a CI workflow in a derived repository. The validate workflow is opt-in.

## Origin

Operator ruling, 2026-11-16: every project defines its terms in a coded register, every appearance of a
registered term is indexed, and the index is kept in sync by a reliable trigger. Design and audit record:
`references/plans/term-index-2026-11-16.design.md` in the upstream repository.
