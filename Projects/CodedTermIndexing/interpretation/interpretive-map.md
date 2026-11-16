# Interpretive Map: Coded Term Definitions and Synced Term-Occurrence Indexing

Commissioned by: @interpretation-advisor · Written by: @primary-producer  
Date: November 16, 2026  
Status: scaffold. This file is not compiled into the report.

## Vantage

The project reads its sources from the standpoint of a framework designer who wants to know what to
build. That standpoint favours sources that describe mechanisms and gives less room to sources that
question whether terminology should be standardised at all. Section "Passages that resist the analogy"
records where that bias matters.

No domain methodology guide is referenced, so the methodology-coverage check reports a missing guide for
this project. The gap is recorded on purpose. The project draws on five traditions, and this repository
has a guide for none of them. A guide would live under `.github/agents/references/methodology/` in the
upstream framework repository, where `researchteam init` would copy it into every derived repository.
The traditions table and the genealogy below carry what a guide would hold for this project.

## Traditions the sources come from

| Tradition | What it contributes | Its standard of evidence | Sources used |
|---|---|---|---|
| History of the book | The occurrence index as an instrument | Manuscript and archival evidence | Rouse and Rouse 1974 |
| Professional indexing practice | The human-made index as a standard | Practice guidance (read as a publisher's description) | Mulvany 2005 |
| Documentation and information science | Machine-generated indexes; vocabulary control | Design argument; standards consensus | Luhn 1960; NISO 2010; Hodge 2000; W3C 2009 |
| Terminology science | The concept-oriented term record; variation | Descriptive linguistics; practice | Cabré 1999; Wright and Budin 1997; Warburton 2021; Daille 2017; Resi 2025 |
| Qualitative research methods | The codebook as a register for analysts | Reliability testing; case study | MacQueen et al. 1998; DeCuir-Gunby et al. 2011; Roberts et al. 2019 |
| Software and requirements engineering | Glossaries, identifier dictionaries, drift, build freshness, continuous integration | Tool design; repository mining; surveys | Knuth 1984; Deissenboeck and Pizka 2006; Arora et al. 2017; Aghajani et al. 2019; Mokhov et al. 2018; Hilton et al. 2016 |

## Genealogy

Every arrow is sourced or marked as an inference.

- Thirteenth-century verbal concordance → computer-compiled concordances (per Rouse and Rouse 1974, 5-6,
  who call the inventors of the digital computer the "direct descendants" of the concordance's compilers
  and the computer the tool of most modern concordances).
- Concordance → keyword-in-context index [editors' inference — unsourced]. Luhn's abstract does not cite
  the concordance tradition.
- Vocabulary control in documentation → SKOS preferred and alternative labels [editors' inference —
  unsourced]. The two share a structure; the SKOS text read does not state the descent.
- Deissenboeck and Pizka's naming rules → Lawrie, Feild and Binkley's syntactic rules (per Lawrie et al.
  2006, abstract, which names the earlier work as its starting point).
- Project glossary in software management → identifier dictionary [editors' inference — unsourced].
  Deissenboeck and Pizka (2006, 265) report the recommendation of a project glossary; the evidence read
  does not state that the dictionary descends from it.
- Hash test for changed legislation → hash test for a stale term index [editors' inference — unsourced].
  This is the project's own analogy from Winkels and Hoekstra (2012, sec. 3.1).
- Literate programming index → documentation generators with glossaries and indexes [editors' inference
  — unsourced].
- Qualitative codebook → a research project's term register [editors' inference — unsourced]. This is
  the project's own analogy.

## Historical setting

| Source | Date | Place | Occasion / audience | Text version | Basis |
|---|---|---|---|---|---|
| Verbal concordance to the scriptures | 13th century | St. Jacques, as an earlier account reported and examined by the source has it | Latin theologians; teaching and preaching | Three successive medieval versions are discussed by the source | (per Rouse and Rouse 1974, 5-6) |
| Rouse and Rouse, "The Verbal Concordance to the Scriptures" | 1974 | — | — | Journal article, digitised scan | (per Rouse and Rouse 1974, 5) |
| Luhn, keyword-in-context index | 1960 | — | — | Abstract only | (per Luhn 1960, abstract) |
| Knuth, "Literate Programming" | 1984 | — | — | Pre-publication typeset copy, cited by section | (per Knuth 1984, sec. 27) |
| Caterpillar Fundamental English, discontinued | 1982 | — | Writers of the company's English documents | Reported at second hand from a 1998 source that was not read | (per Kuhn 2014, entry on Caterpillar Fundamental English) |
| Hodge, knowledge organization systems | 2000 | Washington, DC | Digital library builders | Full report | (per Hodge 2000, 5) |
| Gene Ontology paper | 2000 | — | A "wide biological community," in the paper's words | Author manuscript | (per Ashburner et al. 2000, abstract) |
| ANSI/NISO Z39.19 | 2005, reaffirmed 2010 | — | — | Reaffirmed text of 2010 | (per NISO 2010, sec. 5.1) |
| Deissenboeck and Pizka, identifier dictionary | 2006 | — | Software maintainers; Java and Eclipse | Journal version | (per Deissenboeck and Pizka 2006, 279) |
| SKOS Reference | 2009 | — | — | W3C Recommendation, about two thirds read | (per W3C 2009, S13-S14) |
| Winkels and Hoekstra, legal concepts | 2012 | Netherlands | Dutch tax administration; legal informatics | Author manuscript | (per Winkels and Hoekstra 2012, sec. 2) |
| Mulvany, Indexing Books, 2nd ed. | 2005 | — | — | Publisher's description and contents only | (per Mulvany 2005, publisher's description) |
| Mokhov, Mitchell and Peyton Jones, build systems | 2018 | — | — | Published version | (per Mokhov et al. 2018, 79:14) |
| Roberts, Dowell and Nie, codebook case study | 2019 | New Zealand | Health-services researchers | Full text | (per Roberts et al. 2019, methods) |
| Marić, terminological consistency | 2024 | European Union translation corpus of 2020 | — | Abstract, and section 6.1.3 of the full text | (per Marić 2024, abstract) |
| Tool documentation (Sphinx, Vale, Git, Claude Code and others) | accessed 2026-11-16 | — | Users of each tool | Live pages; several undated | [editors' inference — unsourced] |

Place and audience are left blank (—) wherever the evidence read does not state them. The last row is an inference in one respect only: the date is the day the pages were read, and an undated
page gives no date of writing. What a tool did before that day is not established.

## Anachronism guards

- **Backward.** The medieval concordance is not called an "index of term occurrences against a register."
  It had no register. The deliverables say it indexed word forms.
- **Backward.** Knuth's index is described in his terms, as an index of identifiers by section. It is
  not called a terminology check.
- **Forward.** Luhn's "kept up-to-date" is not read as a statement about hooks or continuous
  integration. It concerns regenerating a bibliographic index by machine.
- **Flattening.** "Terminology science" is not treated as one view. The deliverables record both the norm
  of one designation per concept and the position that variation can be functional (Resi 2025).
- **Text version.** Kuhn 2014 was read in its arXiv version, Knuth 1984 in a pre-publication copy,
  Aghajani et al. 2020 in a thesis reproduction, Arora et al. 2017 as an accepted manuscript, and Tan et
  al. 2024 as a preprint. The literature review says so where it uses these, and give section or
  version-specific locators, or none.
- **Dated findings.** Kang et al. 2020 describe the state of definition detection in 2020. The
  deliverables date the statement and do not present it as the present state.
- **Tool documentation.** A tool's behaviour is dated to the day its documentation was read. The
  deliverables do not say a tool "has always" or "never" done something.

## Passages that resist the analogy

- Gerring (1999) holds that concept formation is not reducible to rules. A register is a set of rules.
- The description of Bowker and Star (1999) holds that standards silence some points of view.
- Mulvany (2005) is described by its publisher as "a manifesto about the vital role of the human-crafted
  index." The book's argument was not read.
- Resi (2025) records that variants can add meaning.
- Hodge (2000, 12) reports that ambiguity pushed much linking of names in text back to manual work, and
  adds that it can be overcome in some files.

Each of these is carried into section 6 of the analysis.

This map cites its sources by the labels used in the deliverables. Every label resolves to a record in
`references/bibliography.bib`. The map is a scaffold and carries no reference list of its own.

## Interpretive directives

1. Report tool behaviour as "the documentation says," with the access date.
2. Keep the codebook as an analogy. Do not write that qualitative researchers "index term occurrences."
3. Present the enforcement evidence as cases, with their settings, and do not generalise it into a law.
4. State the access level wherever a source was read as an abstract or a description.
