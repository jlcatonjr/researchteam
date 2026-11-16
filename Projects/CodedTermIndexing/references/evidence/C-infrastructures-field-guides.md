# Evidence slice C — Infrastructures and field guides (primary documentation)

> **Superseded in part (2026-11-16).** Round 2 settled several points this note left open or had wrong:
> the glossaries undefined-entry behaviour, Vale's triggers, the Claude Code file-watching event, the
> page that holds the Definely every-occurrence quotation, and three prose-matching plugins. See
> `R2-adversarial-tools.md` (T04, T07, T08, T13, T25, T34, T48, T51) and `D-audit-reverification.md`.
> Where this note and those disagree, they govern.

- Project: CodedTermIndexing
- Collected: 2026-11-16 (all "accessed" dates below are 2026-11-16)
- Method: Each page was retrieved this session with WebFetch, or with curl followed by local text
  extraction (NISO PDF, LSP spec). Quotes are short excerpts of the retrieved text. WebFetch returns
  text through an extraction model, so treat every quote as **verbatim-as-retrieved**: re-check it
  against the URL before it goes into a compiled deliverable (citation-audit layer 2).
- Search-engine summaries were used **only to find URLs**. No claim below rests on a search snippet.
  Where only a snippet was available, the item is marked UNVERIFIED-CONTENT.
- Legend for the capability matrix: **register** = machine-readable register of terms/definitions;
  **linking** = occurrences resolved/marked/linked to the definition; **occ-index** = generated index
  of occurrences or back-references; **enforce** = checks or flags undefined, forbidden or
  inconsistent terms; **trigger** = what regenerates or re-checks.

---

### 1. Sphinx (glossary, :term:, index, genindex, nitpicky, incremental build)
- Record for citation: Sphinx developers, "Directives", "Cross-referencing syntax", "Configuration",
  "sphinx-build" (pages built with Sphinx 9.3.0, /en/master/).
  URLs: https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html ;
  https://www.sphinx-doc.org/en/master/usage/referencing.html ;
  https://www.sphinx-doc.org/en/master/usage/configuration.html ;
  https://www.sphinx-doc.org/en/master/man/sphinx-build.html — accessed 2026-11-16
- Access level: full
- Evidence:
  > "This directive must contain a reStructuredText definition-list-like markup with terms and definitions." (glossary directive; directives.html)
  > "The definitions will then be referenceable with the term role." (directives.html)
  > "Reference to a term in a glossary." (`:term:` role; referencing.html)
  > "If you use a term that's not explained in a glossary, you'll get a warning during build." (referencing.html)
  > "This directive contains one or more index entries." (index directive; directives.html)
  > "In nitpicky mode, Sphinx will warn about all references where the target cannot be found." (configuration.html, `nitpicky`)
  > "The default is to only write output files for new and changed source files." (sphinx-build.html, `-a`)
  > "Don't use a saved environment (the structure caching all cross-references), but rebuild it completely." (sphinx-build.html, `-E`)
  > "Turn warnings into errors." (sphinx-build.html, `-W`)
- Capability matrix: register **yes** (glossary directive) · linking **yes** (`:term:` → glossary) · occ-index **partial** (genindex lists explicit `index` entries and object descriptions, not automatically every `:term:` use) · enforce **partial** (warns on an undefined `:term:`; `-W` makes it fatal; it does not flag the same concept written in plain prose) · trigger **build** (incremental by default; a cached environment holds cross-references)
- Caveats: Only occurrences marked up with `:term:` are checked. Unmarked prose uses of a term are invisible to Sphinx. The retrieved text did not say whether glossary terms automatically create genindex entries, so that point is unverified here.

### 2. LaTeX `glossaries` / `glossaries-extra` / bib2gls / makeindex
- Record for citation: Nicola Talbot, *User Manual for glossaries.sty v5.1*, 2026-04-21, CTAN.
  URLs: https://mirrors.mit.edu/CTAN/macros/latex/contrib/glossaries/glossaries-user.html (CTAN mirror) ;
  https://ctan.org/pkg/glossaries (v5.1, 2026-04-21) ; https://ctan.org/pkg/bib2gls (v4.7, 2025-11-13) ;
  https://ctan.org/pkg/makeindex (v2.12) — accessed 2026-11-16
- Access level: partial (the manual is about 419k characters; only the first 100k were read)
- Evidence:
  > "The package uses an indexing program to provide the actual glossary; either makeindex or xindy may serve this purpose" (ctan.org/pkg/glossaries)
  > "The number 1 after each description is the number list (or location list)." (user manual)
  > "This is the list of locations (page numbers, in this case) where the entry was indexed." (user manual)
  > "any entries indexed in the document (through commands like \gls or \glsadd)" (user manual)
  > "you can now run LaTeX on your document again" (user manual, after running makeglossaries; the manual's arara example runs `pdflatex`, `makeglossaries`, `pdflatex`)
  > "Command line application to convert .bib files to glossaries-extra.sty resource files" (ctan.org/pkg/bib2gls)
  > "A general purpose hierarchical index generator; it accepts one or more input files" ... "sorts the entries, and produces an output file which can be formatted." (ctan.org/pkg/makeindex)
- Capability matrix: register **yes** (entry definitions; with bib2gls, a `.bib` term database) · linking **yes** (`\gls` indexes the entry) · occ-index **yes** (the automatically collected "number list" of locations where each entry was indexed) · enforce **partial** (not verified this session: the retrieved text did not cover the behaviour for an undefined entry) · trigger **build** (multi-pass: LaTeX → makeglossaries/makeindex/xindy/bib2gls → LaTeX)
- Caveats: Strongest verified example of an automatic per-term occurrence index (the number list). It is regenerated only by re-running the multi-pass build, so it is stale between builds. The behaviour of `\gls` on an undefined label was not verified this session.

### 3. Vale (vale.sh)
- Record for citation: Vale documentation (errata-ai), "Vocabularies", "substitution", "consistency", "existence"; no page date shown.
  URLs: https://docs.vale.sh/keys/vocabularies ; https://docs.vale.sh/checks/substitution ;
  https://docs.vale.sh/checks/consistency ; https://docs.vale.sh/checks/existence ;
  https://github.com/errata-ai/vale-action ; https://github.com/errata-ai/vale-vscode — accessed 2026-11-16
- Access level: full (docs.vale.sh); partial (the integrations page https://docs.vale.sh/guides/integrations returned "Page Not Found")
- Evidence:
  > "allow you to maintain custom lists of terminology independent of your styles." (vocabularies)
  > "two plain-text files—`accept.txt` and `reject.txt`—that contain one regular expression per line." (vocabularies)
  > "Entries in `accept.txt` are automatically added to a substitution rule (`Vale.Terms`)." (vocabularies)
  > "Entries in `reject.txt` are automatically added to an existence rule (`Vale.Avoid`)." (vocabularies)
  > "`substitution` associates a string with a preferred form." (substitution)
  > "`consistency` will ensure that a key and its value (e.g., "advisor" and "adviser") don't both occur in its scope." (consistency)
  > "it looks for the "existence" of particular tokens." (existence)
  > "The official GitHub Action for Vale -- install, manage, and run Vale with ease." (vale-action README); `fail_on_error`: the action "fails when Vale reports an alert at the `error` level"
  > "The Vale extension for VS Code provides customizable spelling, style, and grammar checking." (vale-vscode README; the README says the extension is deprecated in favour of a fork)
- Capability matrix: register **yes** (vocab files, YAML rules) · linking **no** · occ-index **no** (it reports alerts per occurrence, but builds no persistent index) · enforce **yes** (preferred and forbidden terms; consistency of variant pairs) · trigger **CI** (GitHub Action), **editor** (VS Code extension), **manual** CLI
- Caveats: The register holds terms, not definitions. Vale checks surface forms (regex) and does not link uses to a definition.

### 4. textlint-rule-terminology
- Record for citation: Artem Sapegin, `textlint-rule-terminology` README (GitHub); no version shown.
  URL: https://github.com/sapegin/textlint-rule-terminology — accessed 2026-11-16
- Access level: partial (README only; the textlint.org rule docs redirected and were not followed)
- Evidence:
  > "Textlint rule to check and fix terms, brands and technologies spelling in your tech writing in English."
  > "Whether to load the default replacements (terms)." (`defaultTerms` option) ; "Additional replacements." (`terms` option)
  > Autofix command shown: `textlint --fix --rule terminology Readme.md`
- Capability matrix: register **yes** (term replacement list) · linking **no** · occ-index **no** · enforce **yes** (flags and auto-fixes variants) · trigger **manual / CI** (CLI)
- Caveats: alex, proselint and write-good were not checked.

### 5. DITA 1.3 (OASIS) and DITA Open Toolkit
- Record for citation: OASIS, *DITA Version 1.3 Part 3: All-Inclusive Edition*, OASIS Standard, 17 December 2015; DITA-OT project docs (4.4 dev; 3.4 release notes).
  URLs: https://docs.oasis-open.org/dita/dita/v1.3/os/part3-all-inclusive/langRef/technicalContent/glossentry.html ;
  .../langRef/base/term.html ; .../langRef/technicalContent/abbreviated-form.html ; .../langRef/base/indexterm.html ;
  https://www.dita-ot.org/dev/parameters/parameters-html5 ; https://www.dita-ot.org/3.4/release-notes/ — accessed 2026-11-16
- Access level: full (spec pages); partial (DITA-OT). Two DITA-OT topic URLs returned 404.
- Evidence:
  > "The `<glossentry>` element defines a single sense of a glossary term." (glossentry)
  > "The glossterm element specifies the preferred term that is associated with a definition of a sense." (glossentry page, next-topic summary)
  > "The `<term>` element identifies words that might have or require extended definitions or explanations." (term)
  > "The `@keyref` attribute can be used to associate a term with a resource, typically a definition of the term." (term)
  > "is intended to reference a `<glossentry>` topic that contains both a term and an abbreviated form of that term" (abbreviated-form)
  > "The content of an `<indexterm>` element is used to produce an index entry in a generated index." (indexterm)
  > "All `<indexterm>` elements with the same content are "merged" to form a single index entry in the resulting index" (indexterm)
  > "DITA-OT 3.4 extracts the PDF indexing code to a separate org.dita.index plug-in" (3.4 release notes)
  > `args.indexshow`: "Specifies whether the content of <indexterm> elements are rendered in the output." (allowed yes/no; default no) (DITA-OT 4.4 HTML5 parameters)
- Capability matrix: register **yes** (glossentry topics; keys) · linking **yes** (`term`/`abbreviated-form` with `@keyref`) · occ-index **partial** (index generated from explicit `indexterm` markup, not from `term` uses) · enforce **partial** (the spec allows an implementation to report errors, e.g. "an implementation MAY give an error message" on indexterm ranges; a dedicated undefined-key check was not verified) · trigger **build** (DITA-OT publish)
- Caveats: The retrieved pages did not say whether DITA-OT's HTML5 output builds an index page. Only PDF indexing (org.dita.index) is verified.

### 6. DocBook (TDG 5.2) and DocBook XSL
- Record for citation: Norman Walsh, *DocBook 5.2: The Definitive Guide* (5.2.19), glossterm page rev. 29 Oct 2019; DocBook XSL parameter reference.
  URLs: https://tdg.docbook.org/tdg/5.2/glossterm.html ; https://tdg.docbook.org/tdg/5.2/indexterm.singular.html ;
  https://docbook.sourceforge.net/release/xsl/current/doc/html/glossary.collection.html — accessed 2026-11-16
- Access level: full (glossterm, indexterm.singular); partial (glossary.collection: WebFetch returned a paraphrase plus one quote)
- Evidence:
  > "As an inline, it identifies a term defined in a glossary, and may point to it." (glossterm)
  > "In an online environment, they may also form a link (explicitly or implicitly) to the corresponding definition in a glossary." (glossterm)
  > "@linkend on glossterm must point to a glossentry." (glossterm, constraint)
  > "An indexterm identifies text that is to be placed in the index." (indexterm.singular)
  > "All of the indexterms with a particular type will be collected together in the index with the same type." (indexterm.singular)
  > "simply use firstterm and glossterm to identify the terms you wish to have included in the glossary." (glossary.collection; the glossary is marked `role="auto"` and drawn from a shared glossary database)
- Capability matrix: register **yes** (glossary / shared glossary collection) · linking **yes** (glossterm/firstterm, `@linkend`) · occ-index **partial** (index from explicit `indexterm`) · enforce **partial** (a schema constraint: `@linkend` must point to a glossentry) · trigger **build** (XSL transform)
- Caveats: The glossary.collection page explicitly motivates a single shared database ("separate glossaries ... drift out of sync" — **paraphrase only, not quotable**).

### 7. TEI P5 Guidelines
- Record for citation: TEI Consortium, *TEI P5: Guidelines for Electronic Text Encoding and Interchange*, Version 4.12.0, last updated 28 July 2026, revision 113e933e2.
  URLs: https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-term.html ; .../ref-gloss.html ; .../ref-index.html — accessed 2026-11-16
- Access level: full
- Evidence:
  > "contains a single-word, multi-word, or symbolic designation which is regarded as a technical term." (term)
  > "It may be associated with a gloss element by means of its ref attribute;" "alternatively a gloss element may point to a term element by means of its target attribute." (term, Note)
  > "Because the mutually exclusive target and cRef attributes overlap with the function of the ref attribute," "they are deprecated and may be removed at a subsequent release." (term, Note: deprecation applies to `target`/`cRef` on `<term>`)
  > "identifies a phrase or word used to provide a gloss or definition for some other word or phrase." (gloss)
  > "marks a location to be indexed for whatever purpose." (index) ; `indexName`: "This attribute makes it possible to create multiple indexes for a text."
- Capability matrix: register **partial** (markup vocabulary; no prescribed register file) · linking **yes** (`term/@ref` ↔ `gloss`) · occ-index **partial** (`<index>` marks locations; generating the index is left to processing) · enforce **no** (none stated) · trigger **build** (processor-dependent)
- Caveats: TEI is an encoding standard. It names no maintenance tooling.

### 8. W3C SKOS Reference
- Record for citation: W3C, *SKOS Simple Knowledge Organization System Reference*, W3C Recommendation 18 August 2009.
  URL: https://www.w3.org/TR/skos-reference/ — accessed 2026-11-16
- Access level: partial (first 100k of about 145k characters read)
- Evidence:
  > "The class skos:Concept is the class of SKOS concepts."
  > "The preferred and alternative labels are useful when generating or creating human-readable representations."
  > "The hidden labels are useful when a user is interacting with a knowledge organization system."
  > "skos:prefLabel, skos:altLabel and skos:hiddenLabel are pairwise disjoint properties." (S13)
  > "A resource has no more than one value of skos:prefLabel per language tag." (S14)
  > Section 7.1: notes "could be a definition, information about the scope of a concept, editorial information." (`skos:definition` is a sub-property of `skos:note`)
- Capability matrix: register **yes** (machine-readable RDF) · linking **no** (no document-occurrence model) · occ-index **no** · enforce **yes, within the vocabulary** (integrity conditions S13/S14 on labels) · trigger **n/a** (data model)
- Caveats: SKOS constrains the register's internal consistency, not the usage in documents.

### 9. ISO TC 37 / TC 46 standards and ANSI/NISO Z39.19
- ISO 30042:2019 (TBX), ISO 704:2022, ISO 1087:2019, ISO 25964-1:2011, ISO 999:1996.
  URLs tried: https://www.iso.org/standard/62510.html ; /79077.html ; /62330.html ; /53657.html ; /5418.html — every one returned **HTTP 403** (both WebFetch and curl).
- Access level (ISO): **none — UNVERIFIED-CONTENT.** No claims recorded. The titles appear only as search-result
  titles ("ISO 30042:2019 - Management of terminology resources — TermBase eXchange (TBX)";
  "ISO 704:2022 - Terminology work — Principles and methods"). Retrieve them by hand before citing.

#### ANSI/NISO Z39.19-2005 (R2010)
- Record for citation: NISO, *ANSI/NISO Z39.19-2005 (R2010) Guidelines for the Construction, Format, and Management of Monolingual Controlled Vocabularies* (reaffirmed May 13, 2010).
  URLs: https://www.niso.org/publications/ansiniso-z3919-2005-r2010 ;
  PDF: https://groups.niso.org/higherlogic/ws/public/download/12591/z39-19-2005r2010.pdf — accessed 2026-11-16
- Access level: full (PDF text extracted locally)
- Evidence (PDF):
  > "Controlled vocabularies serve five purposes:" ... "2. Consistency: Promote uniformity in term format and in the assignment of terms." (§5.1 Purpose, p. 10–11)
  > "A controlled vocabulary must compensate for the problems caused by synonymy by ensuring that each concept is represented by a single preferred term." (§5.3.2 Synonymy)
  > "The vocabulary should list the other synonyms and variants as non-preferred terms with USE references to the preferred term." (§5.3.2)
  > "preferred term: One of two or more synonyms or lexical variants selected as a term for inclusion in a controlled vocabulary." (Definitions)
  > "U or USE, which leads from a non-preferred (entry) term to the preferred term" ; "UF or USED FOR, the reciprocal relationship" (equivalence relationship section)
- Capability matrix: register **yes** (normative model: preferred/non-preferred, USE/UF) · linking **n/a** · occ-index **n/a** (concerns indexing of content objects, not term occurrences in prose) · enforce **guidance** (synonym control) · trigger **n/a**

### 10. AsciiDoc / Asciidoctor / Antora
- Record for citation: AsciiDoc Language docs (Eclipse Foundation / Asciidoctor project), "Index catalog" and "Glossary" pages ("AsciiDoc pre-spec"); Antora docs.
  URLs: https://docs.asciidoctor.org/asciidoc/latest/sections/user-index/ ;
  https://docs.asciidoctor.org/asciidoc/latest/sections/glossary/ ; https://docs.antora.org/antora/latest/ — accessed 2026-11-16
- Access level: full (Asciidoctor pages); partial (Antora landing page only)
- Evidence:
  > Flow terms `((<primary>))`: "An index term that appears in the flow of text (i.e., a visible term) and in the index."
  > "only Asciidoctor PDF and the DocBook toolchain support creating an index catalog automatically."
  > "The built-in HTML5 converter in Asciidoctor does not generate an index."
  > "You can include a glossary in an article, book, and book part by setting the `glossary` style on a section."
- Capability matrix: register **partial** (a glossary is a styled description list) · linking **no** (not stated) · occ-index **partial** (index from explicit index terms; PDF/DocBook only) · enforce **no** · trigger **build**
- Caveats: The Antora landing page mentions neither glossary nor index generation. Nothing about Antora is verified.

### 11. MkDocs ecosystem
- Record for citation: (a) `mkdocs-ezglossary` README, realtimeprojects (GitHub), no release shown; (b) Material for MkDocs, "Tooltips" reference (squidfunk).
  URLs: https://github.com/realtimeprojects/mkdocs-ezglossary ; https://squidfunk.github.io/mkdocs-material/reference/tooltips/ — accessed 2026-11-16
  (https://ezglossary.ldeiters.de/ did not resolve.)
- Access level: partial
- Evidence:
  > "A powerful glossary plugin for MkDocs." ; "Reference terms in your documentation:" ; "Generate a summary of all terms:" ; feature: "Reference tracking and linking" (ezglossary README)
  > Snippets "can be used to implement a simple glossary by moving all abbreviations in a dedicated file." (Material tooltips page; the page recommends auto-appending that file to every page and adding its folder to `watch` so `mkdocs serve` reloads)
- Capability matrix: register **yes** · linking **yes** (ezglossary `<section:term>` links; Material abbreviations as tooltips) · occ-index **partial / unverified** (ezglossary advertises "reference tracking" and an `inline_refs` option, but the README text retrieved did not state that it lists every place a term is used) · enforce **unverified** · trigger **build** (`mkdocs build`/`serve`; watch reload)
- Caveats: Undefined-term warnings in ezglossary are not verified.

### 12. Docusaurus — `docusaurus-terminology`
- Record for citation: GRNET, `docusaurus-terminology` README (GitHub, archived and deprecated in favour of rspress-plugin-terminology).
  URL: https://github.com/grnet/docusaurus-terminology — accessed 2026-11-16 (the npm page returned 403)
- Access level: partial
- Evidence:
  > "The plugin needs the directory `docs/terms`, which contains all the terms you need for your website."
  > "The plugin creates a glossary that aggregates all of the terms from the `docs/terms` directory onto a single page"
  > "The plugin parses all `*.md` and `*.mdx` files and replaces each markdown hyperlink pattern with a `<a>` HTML tag supporting a tooltip functionality."
- Capability matrix: register **yes** (one file per term) · linking **yes** · occ-index **no** (not stated) · enforce **no** (not stated) · trigger **build**
- Caveats: Archived and unmaintained.

### 13. Google developer documentation style guide; Google Technical Writing; Microsoft Writing Style Guide
- Record for citation: Google for Developers, "Word list", "Write for a global audience" (style guide) and "Words" (Technical Writing One); Microsoft, "Word choice — Microsoft Style Guide" (ms.date 2024-09-23; updated_at 2026-10-15).
  URLs: https://developers.google.com/style/word-list ; https://developers.google.com/style/translation ;
  https://developers.google.com/tech-writing/one/words ; https://learn.microsoft.com/en-us/style-guide/word-choice/ — accessed 2026-11-16
- Access level: full (Google pages; no last-updated date captured); partial (Microsoft: the A–Z list landing URL tried returned 404; the word-choice page was retrieved)
- Evidence:
  > "This word list covers style and usage guidelines that are specific to developer documentation." (Google word list)
  > "Use the same term throughout the document unless there's a difference in the UI elements for different procedures." (Google word list, *enable* entry)
  > "If you use a particular term for a concept in one place, then use that exact same term elsewhere," (Google, Write for a global audience → Use consistent terminology)
  > "The moral: apply the same unambiguous word or term consistently throughout your document." (Google Technical Writing One, Words)
  > "To improve readability and comprehension, choose your words wisely and use them consistently. If you mean the same thing, use the same word." (Microsoft, Word choice)
  > "For information about specific words and phrases, refer to the A–Z word list" (Microsoft, Word choice)
- Capability matrix: register **partial** (human-readable word lists, not machine-readable) · linking **no** · occ-index **no** · enforce **guidance only** · trigger **manual** (writer/reviewer)

### 14. Write the Docs
- Record for citation: Write the Docs, "Docs as Code" and "Style Guides" guide pages; no date shown.
  URLs: https://www.writethedocs.org/guide/docs-as-code/ ; https://www.writethedocs.org/guide/writing/style-guides/ — accessed 2026-11-16
- Access level: full
- Evidence:
  > "Documentation as Code (Docs as Code) refers to a philosophy" ... "with the same tools as code" ; tools listed include "Version Control (Git)", "Code Reviews", "Automated Tests"
  > "It helps maintain a consistent style, voice, and tone across your documentation" (style guides)
  > "a list of decisions you've made about how to refer to different items you frequently write about" (style guides)
- Capability matrix: register **guidance** · linking **no** · occ-index **no** · enforce **guidance** (automated tests named in general terms; the pages do not mention linting) · trigger **CI implied**

### 15. Git hooks and the pre-commit framework
- Record for citation: Git project, *githooks(5)* (last updated in 2.54.0); Chacon & Straub, *Pro Git* 2nd ed., §8.3 "Git Hooks"; pre-commit.com (pre-commit 4.7.0 shown).
  URLs: https://git-scm.com/docs/githooks ; https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks ; https://pre-commit.com/ — accessed 2026-11-16
- Access level: full
- Evidence:
  > "This hook is invoked by git-commit[1], and can be bypassed with the `--no-verify` option." ... "Exiting with a non-zero status from this script causes the `git` `commit` command to abort before creating a commit." (githooks, pre-commit)
  > "By default the hooks directory is `$GIT_DIR/hooks`, but that can be changed via the `core.hooksPath` configuration variable" (githooks)
  > "It's important to note that client-side hooks are **not** copied when you clone a repository." (Pro Git §8.3)
  > "A framework for managing and maintaining multi-language pre-commit hooks." (pre-commit.com)
  > "Run `pre-commit install` to install pre-commit into your git hooks." ; "If you want to manually run all pre-commit hooks on a repository, run `pre-commit run --all-files`." ; "pre-commit can also be used as a tool for continuous integration." (pre-commit.com)
- Capability matrix: register **n/a** (mechanism) · linking **n/a** · occ-index **n/a** · enforce **yes, as a gate** (a non-zero exit aborts the commit) · trigger **hook** (local; bypassable; not cloned) + **CI** (`--all-files`)
- Caveats: Hooks are local and bypassable, so they need a CI backstop. That conclusion is inferred from the quotes above, not stated as a recommendation by these sources.

### 16. Claude Code hooks
- Record for citation: Anthropic, Claude Code docs, "Hooks reference" and "Settings files and precedence" (no version shown on the page).
  URLs: https://code.claude.com/docs/en/hooks ; https://code.claude.com/docs/en/settings — accessed 2026-11-16
- Access level: full (settings); partial (hooks: first 100k of about 293k characters)
- Evidence:
  > "Hooks are user-defined shell commands, HTTP endpoints, MCP tool calls, LLM prompts, or subagents that execute automatically at specific points in Claude Code's lifecycle."
  > "Hooks are defined in JSON settings files."
  > PostToolUse: "After a tool call succeeds." ; SessionStart: "When a session begins or resumes." ; Stop: "When Claude finishes responding."
  > "This example runs a linting script only when Claude writes or edits a file:" (example uses `"matcher": "Edit|Write"` under `PostToolUse`)
  > "Exit 0 means success, and is the intended exit code when you print JSON for structured control." ; "Exit with code 2 to block the action." ; "The message that comes with the block is your hook's stderr."
  > PostToolUse with exit 2: "Shows stderr to Claude; the tool already ran."
  > "Commit `.claude/settings.json` so everyone who clones the repository gets the same permissions, hooks, and plugin settings." (settings)
  > "Claude Code watches your settings files and reloads them when they change, so it applies most edits to the running session without a restart, including edits to `permissions`, `hooks`, ..." (settings)
- Capability matrix: register **n/a** · linking **n/a** · occ-index **n/a** · enforce **yes, as a gate or feedback** (exit 2 blocks on blocking events; on PostToolUse it feeds stderr back to the agent) · trigger **hook** (per edit: PostToolUse `Edit|Write`; session: SessionStart/Stop)
- Caveats: Unlike git hooks, project hooks live in a committable `.claude/settings.json`. They apply only to Claude Code sessions, not to human edits.

### 17. Terminology-checking products (Acrolinx; memoQ)
- **Acrolinx:** https://www.acrolinx.com/terminology-management/ returned 404. support.acrolinx.com redirects to support.markup.ai, which returned **403** (WebFetch and curl).
  Access level: **none — UNVERIFIED-CONTENT.** No claims recorded.
- **memoQ:** Record for citation: memoQ Translation Technologies, *memoQ documentation 12.6*, "Edit QA settings".
  URL: https://docs.memoq.com/current/en/Workspace/edit-qa-settings.html — accessed 2026-11-16
  Access level: partial
  Evidence:
  > "Warn if forbidden term is used: Select this checkbox to display a warning if a term marked as forbidden is used."
  > "Source to target: Select this radio button to check if all source terms have their translations on the target side, or if identical terms have different translations on the target side." (under "Check for consistent use of terminology")
  Capability matrix: register **yes** (term base) · linking **partial** (term hits) · occ-index **no** (not verified) · enforce **yes** (forbidden terms; consistent translation) · trigger **manual / editor QA run**

### 18. CAQDAS codebooks (MAXQDA)
- Record for citation: VERBI, *MAXQDA Online Manual* ("Overview of Coded Segments"; MAXQDA 2022 manual "Link Memos to Code(s) or Coded Segments").
  URLs: https://www.maxqda.com/help/segment-retrieval/overview-of-coded-segments ;
  https://www.maxqda.com/help-mx22/memos/linking-codes-to-memos — accessed 2026-11-16
  (https://help.maxqda.com/en/coding/code-system returned 404.)
- Access level: partial
- Evidence:
  > Heading "All coded segments of a code", opened by double-clicking a code or choosing "Overview of Coded Segments" (overview page)
  > "Codes can be assigned to a memo similar as to a text segment." ; "right-click the code of interest and select the option Linked Memos" (memos page)
- Capability matrix: register **partial** (code system; code definitions in a codebook not verified this session) · linking **yes** (coded segments) · occ-index **yes** (all coded segments per code, generated on demand) · enforce **no** · trigger **manual** (the analyst codes; the retrieval is live)
- Caveats: NVivo and ATLAS.ti were not checked. MAXQDA code-memo-as-definition is not verified.

### 19. Back-reference indexes in knowledge bases (MediaWiki; Obsidian)
- Record for citation: MediaWiki, "Help:What links here"; Obsidian Help, "Backlinks".
  URLs: https://www.mediawiki.org/wiki/Help:What_links_here ; https://obsidian.md/help/plugins/backlinks — accessed 2026-11-16
- Access level: full
- Evidence:
  > "The **What links here** facility lists the pages on the same site which link to a given page" (MediaWiki)
  > "Linked mentions are backlinks to the notes that contain an internal link to the active note." (Obsidian)
  > "Unlinked mentions are backlinks to any unlinked occurrence of the name of the active note." (Obsidian)
- Capability matrix: register **partial** (page = term) · linking **yes** · occ-index **yes** (automatic backlinks; Obsidian also surfaces *unlinked* occurrences of the name) · enforce **no** · trigger **editor / live** (maintained by the application on save; the mechanism was not stated in the retrieved text)

### 20. Legal and legislative defined terms (Definely; UK OPC)
- Record for citation: Definely Help Center, "Reviewing undefined terms in the Definition Report" (dated July 3, 2026) and "Reviewing defined terms in the Definition Report"; UK Office of the Parliamentary Counsel, *Drafting guidance* (19 March 2024, updated 4 April 2024), GOV.UK.
  URLs: https://help.definely.com/en/articles/545668-reviewing-undefined-terms-in-the-definition-report ;
  https://help.definely.com/en/articles/545644-reviewing-defined-terms-in-the-definition-report ;
  https://www.gov.uk/government/publications/drafting-bills-for-parliament/2024-03-19-drafting-guidance — accessed 2026-11-16
- Access level: full (Definely articles); partial (OPC: first 100k of about 184k characters)
- Evidence:
  > "Definely Draft automatically flags any term that is capitalised throughout your document but lacks a formal definition."
  > Clicking a term's heading shows "every occurrence of that term throughout your agreement." ; the report covers "all defined, undefined and unused terms"
  > OPC 4.1.22: "Definitions that are used in more than one provision and defined in the first of them should generally be signposted" (by a general definitions section or an index of defined terms)
  > OPC 4.1.4: "Avoid labels that are misleading." ; 4.1.7: "Using the same label to denote different things in the same Bill may be confusing."
- Capability matrix (Definely): register **yes** (extracted from the document's own definitions) · linking **yes** · occ-index **yes** (every occurrence per term) · enforce **yes** (undefined, unused) · trigger **editor** (Word add-in; exact trigger not stated)
  (OPC): guidance only; it endorses an **index of defined terms** as a signposting device.
- Caveats: Litera Contract Companion and the US House Legislative Counsel manual were not checked.

### 21. Glossarist
- Record for citation: Glossarist project home page. URL: https://www.glossarist.org/ — accessed 2026-11-16
- Access level: partial
- Evidence:
  > "Glossarist is open-source software for maintaining concept systems across many languages."
  > "Built on ISO 704, ISO 10241-1, and ISO 12620."
- Capability matrix: register **yes** · linking/occ-index/enforce **unverified** · trigger **unverified**

### 22. Language Server Protocol 3.17
- Record for citation: Microsoft, *Language Server Protocol Specification 3.17* (the page labels 3.17 "previous"; 3.18 is current).
  URL: https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/ — accessed 2026-11-16 (full HTML downloaded and text extracted)
- Access level: full
- Evidence:
  > "The references request is sent from the client to the server to resolve project-wide references for the symbol denoted by the given text document position."
  > "The workspace symbol request is sent from the client to the server to list project-wide symbols matching the query string."
  > "The document change notification is sent from the client to the server to signal changes to a text document."
- Capability matrix (as an analogue): register **yes** (symbol definitions) · linking **yes** · occ-index **yes** (project-wide references, on request) · enforce **partial** (diagnostics, not quoted here) · trigger **editor** (didChange notifications)

---

## Not verified / not found

- **ISO 30042:2019, ISO 704:2022, ISO 1087:2019, ISO 25964-1:2011, ISO 999:1996**: iso.org returned 403 to WebFetch and curl. UNVERIFIED-CONTENT. Titles are known only from search-result titles.
- **Acrolinx** terminology docs: 404 / 403. UNVERIFIED-CONTENT.
- **Vale integrations page** (docs.vale.sh/guides/integrations): "Page Not Found". The CI and editor claims rest on the vale-action and vale-vscode READMEs.
- **DITA-OT topic pages** on index terms (two URLs): 404.
- **Microsoft A–Z word list** landing URL: 404 (the word-choice page was used instead).
- **mkdocs-ezglossary docs site** (ezglossary.ldeiters.de): DNS failure. The README was used instead.
- **docusaurus-terminology on npm**: 403. The GitHub README was used instead.
- **MAXQDA code-system page**: 404. **NVivo, ATLAS.ti**: not attempted.
- **Trados MultiTerm**, **Litera Contract Companion**, **US House Legislative Counsel Manual**, **alex/proselint/write-good**: not attempted (one item per category was judged enough).
- **Antora**: the landing page states no glossary or index feature. Nothing verified.
- **Partially read long pages**: glossaries user manual (first 100k of 419k chars), SKOS (100k/145k), Claude Code hooks (100k/293k), OPC guidance (100k/184k).
- Behaviours **not** verified: `\gls` on an undefined label; whether Sphinx glossary terms auto-populate genindex; whether ezglossary lists per-term usage locations; DITA-OT HTML5 index output; how Obsidian maintains its backlinks.

## Summary capability matrix (verified items)

| # | Item | Coded register | Occurrence linking | Generated occurrence index / back-refs | Consistency enforcement | Sync trigger |
|---|------|---|---|---|---|---|
| 1 | Sphinx | yes | yes (`:term:`) | partial (explicit `index` only) | partial (undefined-term warning; `-n`, `-W`) | build (incremental) |
| 2 | LaTeX glossaries / bib2gls | yes | yes (`\gls`) | **yes** (number list) | unverified | build (multi-pass) |
| 3 | Vale | yes (vocab) | no | no | **yes** (substitution/existence/consistency) | CI, editor, CLI |
| 4 | textlint-rule-terminology | yes | no | no | yes (+ autofix) | CLI/CI |
| 5 | DITA 1.3 + DITA-OT | yes (glossentry, keys) | yes (`keyref`) | partial (`indexterm`) | partial | build |
| 6 | DocBook | yes (glossary collection) | yes (`linkend`) | partial (`indexterm`) | partial (schema constraint) | build |
| 7 | TEI P5 | partial | yes (`@ref`) | partial (`<index>`) | no | processor |
| 8 | SKOS | yes | no | no | yes (in-register S13/S14) | n/a |
| 9 | NISO Z39.19 | yes (model) | n/a | n/a | guidance (synonym control) | n/a |
| 10 | Asciidoctor | partial | not stated | partial (PDF/DocBook only; HTML none) | no | build |
| 11 | MkDocs ezglossary / Material | yes | yes | partial/unverified | unverified | build / serve-watch |
| 12 | docusaurus-terminology | yes | yes | no | no | build |
| 13 | Google / Microsoft style guides | partial (human lists) | no | no | guidance | manual |
| 14 | Write the Docs | guidance | no | no | guidance | CI (implied) |
| 15 | git hooks / pre-commit | n/a | n/a | n/a | gate | hook (local, bypassable) + CI |
| 16 | Claude Code hooks | n/a | n/a | n/a | gate/feedback | hook (PostToolUse Edit\|Write, SessionStart, Stop) |
| 17 | memoQ QA | yes (termbase) | partial | no | yes | QA run |
| 18 | MAXQDA | partial | yes | yes (segments per code) | no | manual/live |
| 19 | MediaWiki / Obsidian | partial | yes | **yes** (backlinks; Obsidian unlinked mentions) | no | live/editor |
| 20 | Definely | yes (extracted) | yes | **yes** (every occurrence) | **yes** (undefined/unused) | editor |
| 21 | Glossarist | yes | unverified | unverified | unverified | unverified |
| 22 | LSP 3.17 | yes (symbols) | yes | yes (references) | partial | editor (didChange) |
