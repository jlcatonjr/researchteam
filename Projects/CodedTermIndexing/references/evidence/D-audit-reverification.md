# Evidence slice D: passages re-read during the audit

Retrieved 2026-11-16 by the orchestrating session, after the round 2 audit, to settle findings that changed
the argument. Each PDF was downloaded with curl and converted with `pdftotext -layout`; the quotations
below were found in that text with grep. They are verbatim apart from line breaks.

### Marić 2024 (full text, open access)
- URL: https://hrcak.srce.hr/file/468046
- Section 6.1.3, "Herfindahl Hirschman Index score":
  > "The distribution of the HHI scores was left-skewed (see Figure 3.), with 51 terms having optimal
  > scores of 100. This means that the overall consistency was fairly high, with the median score being
  > 100.00 (IQR = 63.31-100.00)."
- Consequence: the study measures consistency of 100 trade terms sampled from IATE. It reports
  inconsistency for about half of them and judges overall consistency fairly high. It does not show that a
  register failed, and it does not say how translators used IATE.

### Winkels and Hoekstra 2012 (author manuscript)
- URL: https://pure.uva.nl/ws/files/88234356/125492_Winkels_Hoekstra_Jurix_2012_2.pdf
- Section 3.1, "Version Management":
  > "We therefore need some way of constructing a version history by regularly checking for new versions,
  > and comparing them to those we looked at before. To uniquely identify the text of an article, a SHA1
  > hash code is generated and attached to it. If the system receives a new version of the article with
  > the same hash code, it assumes nothing has changed (see Figure 2). If the hash code differs, something
  > definitely changed and the direct links with the earlier version and the concepts are broken"
- Section 4.1, "Results":
  > "We tested the definition extraction on the same 6 laws and results are somewhat disappointing. MA
  > finds definitions with few false positives (5%), but recall is only 42%."
- Consequence: the paper states a sync trigger (regular checking) and a content-hash test for change. Its
  five-item concept record is a goal of the experiment, and automatic extraction of definitions recalled
  42 percent.

### Mokhov, Mitchell and Peyton Jones 2018 (published version, Microsoft Research copy)
- URL: https://www.microsoft.com/en-us/research/uploads/prod/2018/03/build-systems-a-la-carte.pdf
- Definition 2.1 (Minimality) and footnote 5 (fooling Make with `touch`) are on the page headed 79:3,
  not 79:4. The passages on backup software and on recording hashes of dependencies are on 79:14.

### Dalpiaz et al. 2019 (metadata only)
- CrossRef record for doi 10.1016/j.infsof.2018.12.007: Fabiano Dalpiaz, Ivor van der Schalk, Sjaak
  Brinkkemper, Fatma Başak Aydemir and Garm Lucassen. 2019. "Detecting terminological ambiguity in user
  stories: Tool and experimentation." Information and Software Technology 110: 3-16.
- Content was not read by this session. The round 2 note (R2-adversarial-scholarly.md, F9) describes it as
  a controlled experiment on detecting near-synonyms in monolingual requirements. The deliverables cite it
  only as the nearest work the audit found, with that description attributed to the title.

### Tool pages re-read by the orchestrating session after the closure check
Fetched with curl and searched as text, so that the claims added in revision rest on two readings:
- Claude Code hooks reference (https://code.claude.com/docs/en/hooks.md): "Claude Code detects changes
  with a filesystem watcher, not by inspecting tool calls, so it runs the hook no matter what changed the
  file" — found.
- Definely article 545644: "Expand a term by clicking the grey heading box to see every occurrence of
  that term throughout your agreement." — found.
- docusaurus-plugin-glossary README: "The remark plugin automatically detects glossary terms in your
  markdown" — found.
- mkdocs-glossary-plugin README: "in your project will be replaced with a link to x_word.md when
  building" — found.
- Vale, guides/agents: "The hook lints each prose file as the assistant writes it and hands back the
  alerts" — found. The round 2 note had joined this to the phrase "edit-time hook" from another
  sentence; the deliverable now quotes only the words above.
- Material for MkDocs, Tooltips: "Material for MkDocs uses a combination of Markdown extensions to
  enable site-wide glossaries." — found.
Not re-read: the glossaries manual on undefined entries, and Vale's list of integrations. Those rest on
the round 2 reading alone.

### Tool documentation re-read in round 2
`R2-adversarial-tools.md` records, with the page each was found on (all fetched with curl):
- Definely article 545644 (July 6, 2026): "Expand a term by clicking the grey heading box to see every
  occurrence of that term throughout your agreement." (row T34)
- glossaries manual: "undefaction = error: Generates an error if a referenced entry is undefined
  (default, and the only available setting with just the base glossaries package)" and Table 1.1, where
  two of the indexing options need no external application. (rows T07, T08)
- Vale documentation lists editor and language-server integrations, pre-commit, GitHub Actions and
  CircleCI, and a Claude Code plugin with "an edit-time hook [that] lints each prose file as the
  assistant writes it". (row T25)
- Claude Code hooks reference, FileChanged event: "Claude Code detects changes with a filesystem watcher,
  not by inspecting tool calls, so it runs the hook no matter what changed the file: an Edit or Write
  tool call, a script Claude runs with Bash, or a process outside Claude Code entirely." (row T48)
- Sphinx: glossary terms receive general-index entries that point to the definition, not to each use.
  (row T04)
- Three plugins that hold definitions and match plain prose, none keeping an occurrence index:
  docusaurus-plugin-glossary, mkdocs-glossary-plugin, and Material for MkDocs tooltips. (row T51)
- OPC 4.1.22 in full, including: "An index of defined terms is a provision that simply lists terms
  defined elsewhere, and indicates where the definitions can be found." (row T42)
