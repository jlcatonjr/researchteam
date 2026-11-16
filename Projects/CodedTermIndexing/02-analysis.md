# Analysis: What a Synced Term Index Does, and What It Takes to Keep One

Prepared by: @main-analysis-expert  
Date: November 16, 2026  
Citation style: Chicago Author-Date

## Introduction

The literature review found the two halves of the design largely in separate traditions. One tradition
defines terms and controls their variants. The other indexes occurrences. This analysis compares the
sources along the five axes set in the research plan (register, occurrence handling, index, enforcement
and sync trigger), identifies the gap, and draws design implications for researchteam. The terms **coded
definition**, **term register**, **occurrence index** and **synced** are used as defined in
`terminology/terms.json`.

Statements about tools report what their documentation says. Design implications in section 7 are this
project's inferences, and each names the evidence it rests on.

## 1. Three roles the literature gives to the pairing

Read together, the sources give a register joined to an occurrence index three distinct roles.

**A finding aid.** The oldest role is to let a reader see every use of a word in one place. That is the
stated purpose of the medieval concordance (Rouse and Rouse 1974, 5), and it is the role of the reading
interface in Head et al. (2021), which shows how a term is used across a paper.

**A consistency instrument.** The second role is to hold usage to one designation per concept. Vocabulary
control states the goal: each concept "represented by a single preferred term" (NISO 2010, sec. 5.3.2).
Requirements engineering gives the glossary the same job, to fix canonical terms and to regulate synonyms
and homonyms (Gemkow et al. 2018). Deissenboeck and Pizka (2006, 268) formalise it as a one-to-one mapping
between names and concepts. An occurrence index serves this role by making departures findable: it shows
where each form was used. The consistency studies score how concentrated the renderings of each term are
(Gašpar et al. 2022, abstract), which presupposes a record of those renderings.

**An audit trail.** The third role is to make a definitional decision traceable. Roberts et al. (2019)
value the codebook because "it allowed a clear trail of evidence." Winkels and Hoekstra (2012) want
"references to all occurrences of the concept in the sources" so that the effect of a change in the law
can be traced.

A research project needs all three. A reader of a research report needs to find where a term is defined
and used. An author, or a team of agents writing separate components, needs to use each term in one
sense. A reviewer who changes a definition needs to know every passage the change touches.

## 2. Comparison across the five axes

| System | Register | Occurrence handling | Occurrence index | Enforcement | Sync trigger |
|---|---|---|---|---|---|
| Verbal concordance (Rouse and Rouse 1974) | none | every word form | yes | none | not stated |
| Controlled vocabulary (NISO 2010; W3C 2009) | preferred and non-preferred terms | not addressed in the parts read | not addressed in the parts read | inside the register only | not addressed |
| Qualitative codebook (Roberts et al. 2019) | label, definition, exclusions, examples | assigned by analysts | not described | reliability testing | manual |
| Identifier dictionary (Deissenboeck and Pizka 2006) | names with descriptions | collected by compiling | yes | consistency warnings | build, incremental |
| WEB (Knuth 1984) | none; definition points marked by the author | identifiers collected automatically; prose entries marked | yes | none stated | each weave |
| Legal concept record (Winkels and Hoekstra 2012) | definition, synonyms, relations | not stated | specified as a goal | none stated | regular checking; a hash per article |
| Sphinx (Sphinx 2026) | glossary | marked by the author | explicit index entries and glossary definitions, not uses | warning on an undefined marked term | build |
| LaTeX glossaries (Talbot 2026) | entry definitions | marked by the author | yes, of marked uses | error on an undefined marked entry | multi-pass build |
| DITA (OASIS 2015) | glossary entries | marked by the author | marked index entries only | none stated | build |
| DocBook (Walsh 2019) | glossary entries | marked by the author | marked index entries only | schema constraint on pointers | build |
| Vale (Vale 2026) | accepted and rejected forms, no definitions | pattern matching | none described | preferred, forbidden and inconsistent forms | command line, editor, pre-commit, continuous integration, agent edit hook |
| Prose-matching glossary plugins (McClowes 2026; AngryMane 2026) | definitions | pattern matching | none described | none described | build |
| Contract drafting tool (Definely 2026a; Definely 2026b) | taken from the document | detected automatically | yes | undefined and unused terms | not stated |

"Not stated", "not described" and "not addressed" mean the text read did not say. The concordance and
codebook rows include this project's reading of sources that do not use these categories.

## 3. The gap

Three observations follow from the table.

First, **the glossary systems of the documentation toolchains examined depend on the author marking each
use.** Sphinx, LaTeX glossaries, DITA and DocBook link or index a term only where the author wrapped it in
markup. A use written as plain prose is outside the system, and so is a variant the author did not think
to mark. This matters because unintended variation is what Arora et al. (2017, manuscript page 13)
observe, from their experience, in industrial requirements, and unintended uses are by definition
unmarked.

Second, **the documentation tools examined that detect unmarked uses keep no stored index of them.** Vale
matches patterns in
plain prose and reports violations, but its register is a list of forms without definitions and its
documentation describes no persistent index (Vale 2026). The prose-matching glossary plugins hold
definitions and find plain-prose uses, but they act on the built output and describe no stored index
(McClowes 2026; AngryMane 2026). Outside documentation toolchains, Obsidian shows unlinked mentions of a
note's name (Obsidian 2026), and the contract tool lists every occurrence within one document (Definely
2026b).

Third, **the nearest precedents sit outside prose authoring.** The identifier dictionary works on source
code. The legal concept record is a specification for legislation. Within the sources reviewed, no
documentation toolchain joins a register of definitions, a stored index of every occurrence in plain
prose across a set of documents, and a check that the index is current. This is a statement about the
sources reviewed. It is not a claim that no such tool exists.

Plain Markdown, the format researchteam deliverables are written in, has no native glossary markup.
Marking is possible through link syntax, as the plugins show, but marking every use would still miss
unintended variants. This project therefore chooses to detect occurrences by matching, as Vale does,
while holding definitions, as the glossary systems do.

## 4. Whether a register alone is enough: what the evidence does and does not show

The direct evidence is thin. Kuhn (2014) reports one controlled language discontinued because, among
other reasons, its guidelines "were not enforceable in the English documents produced," and reports that
its successor was designed so that "the restrictions on the language should be enforceable." That is one
case, reported at second hand, from industrial technical writing. The measurement studies show that
consistency varies term by term in corpora where it is institutionally valued (Marić 2024), without
showing what a check would change. No study was found that tests whether checking usage against a
register improves consistency.

The software literature supplies a reason by analogy. API documentation goes out of date because nearly
all updates to it are made by hand (Lee et al. 2021), and practitioners name the lack of automation as
the tool problem they meet most (Aghajani et al. 2020). Deissenboeck and Pizka (2006, 263) state the
point for names: consistency over a long effort is "practically impossible ... without additional tools."

These support a modest conclusion: a register that nothing checks usage against should not be expected
to keep usage consistent. The conclusion is a judgement from one case and from analogies. It is not an
established finding.

## 5. Why the trigger matters, and which trigger

An occurrence index is a derived artifact. It is correct only for the documents and the register it was
built from. The documentation toolchains reviewed refresh their indexes when the document is built, so
between builds the index describes an earlier text. For a research project the consequence is specific:
a stale index reports a term as absent from a passage that now uses it, or reports consistent usage that
an edit has since broken.

The sources describe four kinds of trigger.

1. **Build coupling.** The identifier dictionary collects during compilation and analyses only changed
   code (Deissenboeck and Pizka 2006, 279). Markdown deliverables have no compile step that every edit
   passes through, so this trigger has no direct equivalent.
2. **Editor and session events.** A language server is notified of each change and resolves references
   on request (Microsoft 2026). In an agent session, a Claude Code hook can run after each file edit, and
   a file-watching event can fire for changes made by other processes to watched paths (Anthropic 2026).
   Both run only while a session is running. Vale's documentation describes an edit-time hook of this
   kind for prose linting (Vale 2026).
3. **Commit hooks.** A pre-commit hook can refuse a commit, but it "can be bypassed with the
   `--no-verify` option" (Git 2026) and is not copied on clone (Chacon and Straub 2014, sec. 8.3).
4. **Server-side checks.** Pro Git places policy enforcement on the server side (Chacon and Straub 2014,
   sec. 8.3). Continuous integration automates building and testing (Hilton et al. 2016), and Tan et al. (2024) propose, as future work, scanning documentation on every commit or pull request.

No one trigger is both immediate and unavoidable. The first three are immediate and can be missed. The
fourth, where a repository has it, cannot be missed and is late. This project therefore infers that the
triggers should be layered, with the late one as the gate wherever it exists. No source reviewed
evaluates the combination.

What makes the layers agree is a staleness test that does not depend on which trigger last ran. Two
sources describe it. Winkels and Hoekstra (2012, sec. 3.1) attach a hash to each article of law and treat
a changed hash as proof that "something definitely changed" and that the links to the concepts are
broken. Mokhov et al. (2018, 79:14) describe the general form for build systems: record the hashes of the
inputs used last time, and treat the artifact as dirty if they have changed. File times are not a safe
substitute, since they can be altered without a change of content (Mokhov et al. 2018, 79:3). By analogy,
an index that records the content hash of the register and of each indexed document can be verified by
anyone, at any time, by recomputing the hashes.

## 6. Limits the literature places on the design

**Matching finds forms, not meanings.** An occurrence index built by matching records where a registered
form appears. It cannot tell whether the word is used in the registered sense. This follows from what
matching is. Hodge (2000, 12) reports ambiguity as an obstacle to automatic linking of names in text,
while adding that it can be overcome in some files.

**Variation is not always error.** Resi (2025, PDF p. 2) records the position that variants "may reflect
different perspectives on the same concept." Quotations, titles and the reporting of another author's
vocabulary are legitimate places for a discouraged form. A check that left no room for them would push
authors to distort their sources. Researchteam's own historical-context protocol requires the opposite:
to use a source's own terms and to name later categories as later.

**A register fixes usage, not quality.** Gerring (1999) argues that the goodness of a concept cannot be
reduced to a set of rules. A register that passes every check may still define its terms badly.

**A register is not neutral.** The publisher's description of Bowker and Star (1999) notes that each
category "valorizes some point of view and silences another." The choice of a preferred term is an
interpretive act and should be recorded as one.

**A human-made index is still advocated.** The publisher of one standard indexing guide describes
it as "a manifesto about the vital role of the human-crafted index" (Mulvany 2005). An occurrence index
generated by matching is a concordance of registered forms. It is not a substitute for an analytical
index.

**Definitions should be declared.** Winkels and Hoekstra (2012, sec. 4.1) report that automatic
extraction of legal definitions recalled 42 percent of them, and Kang et al. (2020) reported in 2020 that
earlier definition detectors were not accurate enough for use. Those are dated results. The stronger
reason is governance: a declared definition has an author and a history, and Knuth's system likewise
leaves the marking of definition points to the author while automating the index of identifiers (Knuth
1984, sec. 27).

## 7. Design implications for researchteam

Each implication names its basis. They are recommendations, not findings.

1. **Keep a concept-oriented register per project.** One record per concept, with an identifier, one
   preferred label, a definition, accepted variants and discouraged variants. Basis: the preferred and
   non-preferred structure of vocabulary control (NISO 2010, sec. 5.3.2) and the code record in Roberts
   et al. (2019).
2. **Require each form to belong to one concept only.** Basis: the one-to-one mapping of Deissenboeck and
   Pizka (2006, 268) and synonym control (NISO 2010, sec. 5.3.2).
3. **Detect occurrences by matching plain prose, without asking authors to mark terms.** Basis: the gap
   in section 3, and the practice of Vale and the prose-matching plugins.
4. **Generate the occurrence index, and never edit it by hand.** Basis: Luhn (1960) on machine generation
   as a means to currency, with Knuth (1984) as the precedent for generating an index from the
   text's own source.
5. **Record content hashes of the register and of every indexed document, and decide staleness from
   them.** Basis: Winkels and Hoekstra (2012, sec. 3.1), and Mokhov et al. (2018, 79:14) by analogy.
6. **Layer the triggers, and make a check that cannot be skipped the gate wherever one exists.** Rebuild
   after each edit in an agent session, offer a commit hook, and check freshness in the repository's
   validation and, where the repository has it, in continuous integration. Basis: section 5. This is the
   project's inference.
7. **Check usage against the register, and record every deliberate departure.** A discouraged form in
   prose, outside a quotation, should fail the check unless the register records an exception with a
   reason. Basis: the one reported case of an unenforceable register (Kuhn 2014), the audit trail that
   the codebook literature values (Roberts et al. 2019), and the legitimacy of deliberate variation
   (Resi 2025). The evidence does not show that a blocking check works better than an advisory one. This
   is a design choice, made because a recorded exception costs little and leaves a trail.
8. **State the ceiling.** A clean check means the register is well formed, the index is current, and no
   discouraged form appears without a recorded exception. It does not mean the terms are used in their
   defined sense. Basis: section 6.
9. **Record the source of each definition, or mark it as the project's own.** Basis: the codebook's audit
   trail (Roberts et al. 2019) and the non-neutrality of categories (Bowker and Star 1999).

## 8. Threats to this analysis

- Several load-bearing sources were read only as abstracts or publisher descriptions. Each such use is
  marked in the literature review, and not again here.
- The enforcement evidence in section 4 is one second-hand case from industrial technical writing. No
  study was found that applies a consistency index to monolingual technical documentation, and research
  writing was not separately searched.
- The tool comparison rests on documentation, which may be incomplete or out of date, and four long
  documents were read only in part.
- The search was not exhaustive. Two plugins that bear on section 3 were found only in the second audit
  round and rest on their README files, and other tools that were not examined may close the gap
  described there.
- The ISO standards on terminology work and on indexes could not be retrieved and are not cited.

## References

Aghajani, Emad, Csaba Nagy, Mario Linares-Vásquez, Laura Moreno, Gabriele Bavota, Michele Lanza, and David C. Shepherd. 2020. "Software Documentation: The Practitioners' Perspective." In Proceedings of the ACM/IEEE 42nd International Conference on Software Engineering, 590-601. ACM. https://doi.org/10.1145/3377811.3380405

AngryMane. 2026. "mkdocs-glossary-plugin." Software repository README. Accessed November 16, 2026. https://github.com/AngryMane/mkdocs-glossary-plugin

Anthropic. 2026. "Hooks Reference." Claude Code documentation. Accessed November 16, 2026. https://code.claude.com/docs/en/hooks

Arora, Chetan, Mehrdad Sabetzadeh, Lionel Briand, and Frank Zimmer. 2017. "Automated Extraction and Clustering of Requirements Glossary Terms." IEEE Transactions on Software Engineering 43 (10): 918-45. https://doi.org/10.1109/TSE.2016.2635134

Bowker, Geoffrey C., and Susan Leigh Star. 1999. Sorting Things Out: Classification and Its Consequences. Cambridge, MA: MIT Press. https://doi.org/10.7551/mitpress/6352.001.0001

Chacon, Scott, and Ben Straub. 2014. Pro Git. 2nd ed. Apress. https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks

Definely. 2026a. "Reviewing Undefined Terms in the Definition Report." Definely Help Center, July 3, 2026. https://help.definely.com/en/articles/545668-reviewing-undefined-terms-in-the-definition-report

Definely. 2026b. "Reviewing Defined Terms in the Definition Report." Definely Help Center, July 6, 2026. https://help.definely.com/en/articles/545644-reviewing-defined-terms-in-the-definition-report

Deissenboeck, Florian, and Markus Pizka. 2006. "Concise and Consistent Naming." Software Quality Journal 14 (3): 261-82. https://doi.org/10.1007/s11219-006-9219-1

Gašpar, Angelina, Sanja Seljan, and Vlasta Kučiš. 2022. "Measuring Terminology Consistency in Translated Corpora: Implementation of the Herfindahl-Hirshman Index." Information 13 (2): 43. https://doi.org/10.3390/info13020043

Gemkow, Tim, Miro Conzelmann, Kerstin Hartig, and Andreas Vogelsang. 2018. "Automatic Glossary Term Extraction from Large-Scale Requirements Specifications." In 2018 IEEE 26th International Requirements Engineering Conference (RE), 412-17. IEEE. https://doi.org/10.1109/RE.2018.00052

Gerring, John. 1999. "What Makes a Concept Good? A Criterial Framework for Understanding Concept Formation in the Social Sciences." Polity 31 (3): 357-93. https://doi.org/10.2307/3235246

Git. 2026. "githooks: Hooks Used by Git." Git reference documentation. Accessed November 16, 2026. https://git-scm.com/docs/githooks

Head, Andrew, Kyle Lo, Dongyeop Kang, Raymond Fok, Sam Skjonsberg, Daniel S. Weld, and Marti A. Hearst. 2021. "Augmenting Scientific Papers with Just-in-Time, Position-Sensitive Definitions of Terms and Symbols." In Proceedings of the 2021 CHI Conference on Human Factors in Computing Systems, 1-18. ACM. https://doi.org/10.1145/3411764.3445648

Hilton, Michael, Timothy Tunnell, Kai Huang, Darko Marinov, and Danny Dig. 2016. "Usage, Costs, and Benefits of Continuous Integration in Open-Source Projects." In Proceedings of the 31st IEEE/ACM International Conference on Automated Software Engineering, 426-37. ACM. https://doi.org/10.1145/2970276.2970358

Hodge, Gail. 2000. Systems of Knowledge Organization for Digital Libraries: Beyond Traditional Authority Files. Washington, DC: Digital Library Federation and Council on Library and Information Resources. https://www.clir.org/pubs/reports/pub91/

Kang, Dongyeop, Andrew Head, Risham Sidhu, Kyle Lo, Daniel Weld, and Marti A. Hearst. 2020. "Document-Level Definition Detection in Scholarly Documents: Existing Models, Error Analyses, and Future Directions." In Proceedings of the First Workshop on Scholarly Document Processing, 196-206. Association for Computational Linguistics. https://doi.org/10.18653/v1/2020.sdp-1.22

Knuth, Donald E. 1984. "Literate Programming." The Computer Journal 27 (2): 97-111. https://doi.org/10.1093/comjnl/27.2.97

Kuhn, Tobias. 2014. "A Survey and Classification of Controlled Natural Languages." Computational Linguistics 40 (1): 121-70. https://doi.org/10.1162/COLI_a_00168

Lee, Seonah, Rongxin Wu, Shing-Chi Cheung, and Sungwon Kang. 2021. "Automatic Detection and Update Suggestion for Outdated API Names in Documentation." IEEE Transactions on Software Engineering 47 (4): 653-75. https://doi.org/10.1109/TSE.2019.2901459

Luhn, H. P. 1960. "Key Word-in-Context Index for Technical Literature (KWIC Index)." American Documentation 11 (4): 288-95. https://doi.org/10.1002/asi.5090110403

Marić, Laura. 2024. "Terminological Consistency in Croatian Translations of EU Legislation: A Corpus-Based Study." Hieronymus 11: 58-87. https://doi.org/10.17234/Hieronymus.11.3

McClowes. 2026. "docusaurus-plugin-glossary." Software repository README. Accessed November 16, 2026. https://github.com/mcclowes/docusaurus-plugin-glossary

Microsoft. 2026. Language Server Protocol Specification 3.17. Accessed November 16, 2026. https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/

Mokhov, Andrey, Neil Mitchell, and Simon Peyton Jones. 2018. "Build Systems à la Carte." Proceedings of the ACM on Programming Languages 2 (ICFP): 79:1-79:29. https://doi.org/10.1145/3236774

Mulvany, Nancy C. 2005. Indexing Books. 2nd ed. Chicago: University of Chicago Press. https://doi.org/10.7208/chicago/9780226550176.001.0001

NISO (National Information Standards Organization). 2010. Guidelines for the Construction, Format, and Management of Monolingual Controlled Vocabularies. ANSI/NISO Z39.19-2005 (R2010). https://www.niso.org/publications/ansiniso-z3919-2005-r2010

OASIS. 2015. Darwin Information Typing Architecture (DITA) Version 1.3 Part 3: All-Inclusive Edition. OASIS Standard, 17 December 2015. https://docs.oasis-open.org/dita/dita/v1.3/os/part3-all-inclusive/langRef/technicalContent/glossentry.html https://docs.oasis-open.org/dita/dita/v1.3/os/part3-all-inclusive/langRef/base/term.html https://docs.oasis-open.org/dita/dita/v1.3/os/part3-all-inclusive/langRef/base/indexterm.html

Obsidian. 2026. "Backlinks." Obsidian Help. Accessed November 16, 2026. https://obsidian.md/help/plugins/backlinks

Resi, Rossella. 2025. "Representing Terminological Chains for Well-Formed Neologisms." In Proceedings of the 1st International Workshop on Terminological Neologism Management (NeoTerm 2025). CEUR Workshop Proceedings 3972. https://ceur-ws.org/Vol-3972/paper3.pdf

Roberts, Kate, Anthony Dowell, and Jing-Bao Nie. 2019. "Attempting Rigour and Replicability in Thematic Analysis of Qualitative Research Data; A Case Study of Codebook Development." BMC Medical Research Methodology 19: 66. https://doi.org/10.1186/s12874-019-0707-y

Rouse, Richard H., and Mary A. Rouse. 1974. "The Verbal Concordance to the Scriptures." Archivum Fratrum Praedicatorum 44: 5-30. https://heyjoe.fbk.eu/index.php/afp/article/view/12081

Sphinx. 2026. "Directives," "Cross-Referencing Syntax," "Configuration," and "sphinx-build." Sphinx documentation (built with Sphinx 9.3.0). Accessed November 16, 2026. https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html https://www.sphinx-doc.org/en/master/usage/referencing.html

Talbot, Nicola. 2026. User Manual for glossaries.sty v5.1. CTAN, April 21, 2026. https://ctan.org/pkg/glossaries

Tan, Wen Siang, Markus Wagner, and Christoph Treude. 2024. "Detecting Outdated Code Element References in Software Repository Documentation." Empirical Software Engineering 29 (1): 5. https://doi.org/10.1007/s10664-023-10397-6

Vale. 2026. "Vocabularies," "substitution," "consistency," and "existence." Vale documentation. Accessed November 16, 2026. https://docs.vale.sh/keys/vocabularies https://docs.vale.sh/checks/consistency https://docs.vale.sh/guides/agents.md

W3C (World Wide Web Consortium). 2009. SKOS Simple Knowledge Organization System Reference. W3C Recommendation, 18 August 2009. https://www.w3.org/TR/skos-reference/

Walsh, Norman. 2019. DocBook 5.2: The Definitive Guide. Online edition. https://tdg.docbook.org/tdg/5.2/glossterm.html

Winkels, Radboud, and Rinke Hoekstra. 2012. "Automatic Extraction of Legal Concepts and Definitions." In Legal Knowledge and Information Systems: JURIX 2012, Frontiers in Artificial Intelligence and Applications 250, 157ff. Amsterdam: IOS Press. https://doi.org/10.3233/978-1-61499-167-0-157
