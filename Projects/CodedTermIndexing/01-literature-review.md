# Literature Review: Coded Term Definitions and Synced Term-Occurrence Indexing

Prepared by: @literature-review-expert  
Date: November 16, 2026  
Citation style: Chicago Author-Date

## How to read this review

The review has two parts. Part I (sections 1 to 6) covers the scholarly literature. Part II (sections 7 to
9) covers existing infrastructures and field guides, read from their own documentation. A tool's
documentation is primary evidence of what the tool says it does. It is not a scholarly finding, and it is
not evidence that the tool works well.

Each source was read at a stated access level: full text, abstract only, or publisher description only. The
level is recorded in `references/bibliography.bib` and the quotations are in `references/evidence/`. Where
a source was read only as an abstract or a description, the text below says so, and the claim is limited to
what that text states.

Four terms are used in one sense throughout. Their canonical definitions are in
`terminology/terms.json`. A **coded definition** is a term definition held as structured data that a
program can read. A **term register** is the set of coded definitions a project maintains. An
**occurrence index** is a derived record of every place a given form appears in a body of documents; in
this project's design the forms are a registered term and its listed variants. An index is **synced** when automatic triggers regenerate it as the
documents or the register change, and any remaining staleness can be detected by a check.

# Part I. The scholarly literature

## 1. The occurrence index before the computer, and its mechanisation

An index of every use of a word is an old instrument. Rouse and Rouse (1974, 5) describe the
thirteenth-century verbal concordance to the scriptures as "a consciously created solution to the needs of
Latin theologians for a device which would enable them to have in one place all the uses of a given word or
phrase in the scriptures." They put its scale at "some 100,000 appearances in the scriptures of roughly
10,000 words," and they call "the inventors of the digital computer, the tool through which most modern
concordances are compiled," the "direct descendants" of its compilers (Rouse and Rouse 1974, 5-6). The
concordance indexes word forms. It holds no definitions and it does not judge whether a word is used
consistently.

Occurrence indexing was later mechanised. The abstract of Luhn (1960) proposes keyword-in-context indexes
that "can be entirely machine-generated and hence kept up-to-date with the current literature," and it sets
out the trade explicitly: the user's "willingness ... to trade perfection for currency." Luhn's index is a
bibliographic index of titles, not an index of term use inside one body of documents, and the abstract says
nothing about definitions or about the concordance. Its relevance here is the argument that machine
generation is a means to currency.

One standard guide to book indexing was consulted through its publisher's description, which calls the
book "both a practical guide and a manifesto about the vital role of the human-crafted index." Its contents
list "Automatic Indexing" and "Computer-aided Indexing" as separate topics (Mulvany 2005). Only that
description and the table of contents were read, so nothing is claimed about the book's argument.

## 2. Terminology science: the concept-oriented record

Terminology science supplies the idea of the register. The discipline's standard textbook and handbook
were read only through their publishers' descriptions and tables of contents, which is enough to
establish what the field treats as central and no more. Cabré (1999) devotes chapters to computerized
terminology, including terminological data banks, and to terminological standardization. The handbook
compiled by Wright and Budin (1997) covers "creation and use of terminological tools (terminology
databases, on-line dictionaries, etc.)" and includes a section headed "Prescriptive Terminology."
Warburton (2021) is described by its publisher as the first monograph on managing terminology "in content
production environments that are both demanding and multilingual," and its contents are organised around
creating, launching, expanding and maintaining the quality of a termbase.

Two points from this literature bear directly on design. First, variation is a recognised object of
study. Daille (2017), in the publisher's description, presents "the first complete inventory of term
variants" and asks how "variants [can] be automatically detected in texts." This project infers that a
register listing only one form of each term will miss variant usage. Second, consistency is a stated norm,
and a contested one. Resi (2025, PDF p. 2) defines it: "Term consistency means using a single designation
for a concept across all occurrences within a document or a domain." The same passage records the
counter-position that "term variants may reflect different perspectives on the same concept" and can "add
functional depth to the text." Resi's is a workshop paper on translation, and its statement that
consistency is a key principle of technical writing rests on sources that were not checked here.

## 3. Controlled vocabulary and knowledge organization

Knowledge organization states the purpose of vocabulary control and the structure that achieves it. The
American standard for monolingual controlled vocabularies lists consistency among the five purposes such
vocabularies serve: to "promote uniformity in term format and in the assignment of terms" (NISO 2010,
sec. 5.1). Its mechanism is synonym control. A controlled vocabulary "must compensate for the problems
caused by synonymy by ensuring that each concept is represented by a single preferred term," and it
"should list the other synonyms and variants as non-preferred terms with USE references to the preferred
term" (NISO 2010, sec. 5.3.2). The SKOS data model expresses a related structure for machines: within one
concept, preferred, alternative and hidden labels are pairwise disjoint, and a resource "has no more than
one value of skos:prefLabel per language tag" (W3C 2009, S13-S14). Both documents govern the register's
internal consistency. In the parts read, neither addresses checking prose against a register. About two
thirds of the SKOS text was read.

Hodge (2000, 5) places the glossary within this family: "A glossary is a list of terms, usually with
definitions. The terms may be from a specific subject field or from a particular work. The terms are
defined within a specific environment and rarely include variant meanings." Hodge also describes linking
running text to an authority record, where a registered name "can be identified manually or automatically
in the text." On the automatic route the report says both that "because of the ambiguity in organism
names, many examples of this type are now created manually" and that, depending on the files involved,
the ambiguity "can be overcome" (Hodge 2000, 12). The report dates from 2000 and concerns access to
digital libraries, not authoring. It shows that this tradition does address occurrences in running text,
at its margin.

The strongest scholarly example of a coded register is the Gene Ontology. Ashburner et al. (2000)
describe "a structured, precisely defined, common, controlled vocabulary," a system of "specific,
agreed-on terms with definitions and supporting documentation," stored in "a flat file format." The
vocabulary is applied by annotating database records. The paper describes no index of term use in prose,
although it hopes the concepts will be taken up "in our writing as well as our thinking."

A critical strand warns against treating a register as neutral. The publisher's description of Bowker
and Star (1999) states that "each standard and category valorizes some point of view and silences
another." Only that description was read.

## 4. Enforcement, and the measurement of consistency

One source addresses what happened when a register existed and usage could not be checked against it.
Kuhn (2014) surveys controlled natural languages, which pair an approved dictionary with usage rules.
For one of them, ASD Simplified Technical English, Kuhn quotes the rule "Keep to the approved meaning of
a word in the Dictionary. Do not use the word with any other meaning." For another, Caterpillar
Fundamental English, Kuhn reports, citing an earlier source for the figure, a vocabulary restricted to
"around 800 to 1,000 words ... with only one meaning defined for each of them." It was discontinued in
1982 because, "among other reasons," "the basic guidelines of CFE were not enforceable in the English
documents produced." Its successor "was developed following a different approach: The restrictions on the
language should be enforceable." The quoted reason is Kuhn citing a 1998 report that was not read. The
quotations were confirmed in the preprint, so no page numbers are given. This is one case, reported at
second hand, with unenforceability named as one reason among several.

Consistency can be measured, which is what checking requires. Gašpar et al. (2022), read as an abstract,
score terminology consistency in translated corpora with a concentration index. Marić (2024) applies the
same index to 100 trade terms, sampled from the European Union's term register, in English-Croatian
translations of Union legislation. The abstract states that "the results confirm the presence of
terminological inconsistency." The full text adds that 51 of the terms scored the maximum and that "the
overall consistency was fairly high" (Marić 2024, sec. 6.1.3). The study does not say how the translators
used the register, so it is evidence that consistency can be measured term by term and not evidence that
a register failed. Semenov and Bojar (2022), read as an abstract, argue that for professional domains "it
is crucial to measure the consistency of the translation of the terms throughout the whole text," and
report a document-level metric that correlates with human assessment. The quotation is from the abstract
on the proceedings page.

All three measurement studies concern translation. No study was found that applies a consistency index
of this kind to monolingual technical documentation, and research writing was not separately searched.
The nearest work the audit found is an experiment on detecting terminological ambiguity in requirements
(Dalpiaz et al. 2019), which was identified from its record and not read.

## 5. The register in research practice: codebooks and concepts

Research itself has a long-standing practice that resembles a term register: the qualitative codebook.
MacQueen et al. (1998), of which only the opening text was read, describe "how a structured codebook
provides a stable frame for the dynamic analysis of textual data" and "how specific codebook features can
improve intercoder agreement among multiple researchers." DeCuir-Gunby et al. (2011), read as an
abstract, give steps for creating a codebook and for training others to code with it, "including how to
establish reliability."

Roberts et al. (2019) give a record structure, which they take from earlier guidelines. Their codes "were
classified with the following: label, definition, description, qualifications or exclusions and examples
from the raw data." They tie the codebook to consistency of judgement "across various viewers" and over
time, and to "a clear trail of evidence." They also froze it: "minimal changes to the codebook were made
at this stage unless it was deemed absolutely necessary." The codebook governs how analysts label data.
It is an analogy for how authors use terms, and the analogy is this project's. The paper describes
manual coding and no automatic index.

The social-science literature on concept formation supplies a limit. Gerring (1999), read as an abstract,
argues that the goodness of a concept "cannot be reduced to 'clarity,' to empirical or theoretical
relevance, to a set of rules," and treats concept formation as "a highly variable process involving
trade-offs" among eight criteria. A register can fix how a term is used. It cannot show that the concept
is a good one.

## 6. Software and requirements engineering

This literature comes closest to the full design, because its documents are already processed by
programs.

**Glossaries.** In requirements engineering the glossary is a consistency instrument. Arora et al. (2017)
state that glossaries "promote better communication between the stakeholders by establishing a common and
consistent language," and they identify "the use of variant phrases for referring to the same concept" as
a consistency issue. They add, from their own experience of industry, that "industrial requirements are
prone to containing unintended variations" (manuscript pages 1, 2 and 13). Gemkow et al. (2018) put the
task plainly: a glossary should "define the canonical terms used to refer to a given concept, and ...
regulate both the use of synonyms (by clarifying the preferred terms) and homonyms." They report, as best
practice in the field, that a glossary "should be developed continuously," and add that "in many
real-world projects, this effort is not expended initially." Both papers concern building a glossary, not
enforcing one.

**Identifier dictionaries.** Deissenboeck and Pizka (2006) describe the nearest scholarly precedent for
a term register joined to an incrementally maintained occurrence index. They define consistency formally, as a one-to-one
mapping between names and concepts (Deissenboeck and Pizka 2006, 268), and they hold that "it is indeed
practically impossible to preserve globally consistent naming during long-term development efforts,
maintenance, or evolution without additional tools" (263). Their tool "incrementally builds and maintains
a complete identifier dictionary while the system is being developed" (261). They require that
"developers should be able to look up a particular name in the source code, ask the tool for a list of
all identifiers with this name, and navigate to selected occurrences" (278). The collector "is coupled
with Eclipse's build process," analysis "is done in an incremental fashion so only previously changed
source code will be analyzed," and names "may become annotated with warnings icons ... indicating
potential consistency problems" (279). The setting is Java identifiers, collected by compiling the code,
and the paper presents the design without an empirical evaluation of it. The abstract of Lawrie et al.
(2006) notes the cost this design carries, "an expert provided mapping from identifiers to concepts," and
proposes a syntactic approximation that needs none. An experiment summarised in the abstract of Feitelson
et al. (2022) suggests why a shared register is needed at all: "the probability that two developers would
select the same name is low," with a median of 6.9 percent.

**Literate programming.** Knuth (1984), read here in a pre-publication typeset copy, is the classic
source for an index generated from the same source as the text. In the WEB system an index of every program identifier, with the sections where it appears,
"is prepared automatically by the WEB software." The underlining that shows where an identifier is
defined "is not automatic; the user is supposed to mark identifiers at their point of definition," and
the author inserts entries for topics in the prose by hand (Knuth 1984, sec. 27 of the example program).
The division is instructive: the machine finds the occurrences of identifiers, and the author declares
where they are defined. WEB holds no register of definitions, and its prose entries are marked, not
detected.

**Documentation drift.** A group of empirical studies shows that text which must agree with something
else tends to fall out of step with it. Aghajani et al. (2019) built a taxonomy of documentation issues
in which up-to-dateness is a large category, defined as a document that "is not in sync with other parts
of a system," and in which "Inconsistent terminology" is a named issue type. In a follow-up survey, read
here as reproduced in the first author's doctoral thesis, 59 percent of practitioners rated inconsistency
between code and documentation as important, and "lack of/poor automatization" was the tool issue they
met most often (Aghajani et al. 2020). The survey drew most of its respondents from one company. The
abstract of Wen et al. (2019) describes code-comment inconsistencies as "comments that are not kept in
sync with the code they document." Tan et al. (2007) link such drift to defects: their tool found 60
comment-code inconsistencies in four systems, "33 new bugs and 27 bad comments." Lee et al. (2021)
attribute outdated API documentation to manual upkeep, "nearly all of the associated updates are
performed manually," and the abstract of Zhong and Su (2013) reports more than 1,000 documentation errors
detected by combining natural-language and code analysis. Tan et al. (2024), read as a preprint, found
that most of over 3,000 projects contained an outdated code reference at some point, and proposed, as
future work, a workflow that scans "whenever there is a new commit or pull request." These studies
concern code names and comments, not glossary terms.

**Keeping a derived artifact current.** Mokhov et al. (2018) supply the vocabulary for deciding whether a
derived artifact is stale. A build system is minimal "if it executes tasks at most once per build and
only if they transitively depend on inputs that changed since the previous build" (79:3). File
modification times, the method Make uses, can be fooled, for example with `touch` or by backup software
(79:3, 79:14). The alternative is "to record the values/hashes of dependencies used last time, and if
something has changed, the key is dirty and must be rebuilt" (79:14). The paper is about build systems in
general. Applying it to an occurrence index is this project's inference.

**Continuous integration.** Hilton et al. (2016) studied the use of continuous integration in
open-source projects, which their abstract describes as systems that "automate the compilation, building,
and testing of software." One survey respondent they quote said it "acts like a watchdog. You may not run
tests, or be careful with merges, but the CI will." Evans (2015, 2), a practitioner reference and not a
peer-reviewed source, ties the practice to vocabulary directly: "Apply Continuous Integration to keep
model concepts and terms strictly consistent within these bounds." Evans means frequent merging and
shared practice, and does not describe an automated terminology check.

**Definitions and occurrences in documents.** Three further sources concern prose. Winkels and Hoekstra
(2012) set out, for Dutch tax law, the information they want recorded for each legally defined concept:
the text where it is defined, its definition, "references to all occurrences of the concept in the
sources," its relations and its synonyms. That is a specification for a coded register with an occurrence
index, built for tracing the effect of legal change. The record is the experiment's goal. Its automatic
extraction of definitions recalled 42 percent of them (sec. 4.1). The paper also describes how it keeps
its records in step with a changing source: it works "by regularly checking for new versions," and "a
SHA1 hash code is generated and attached to" each article, so that "if the hash code differs, something
definitely changed and the direct links with the earlier version and the concepts are broken" (sec. 3.1).
Head et al. (2021), read as an abstract, built a reading interface that surfaces definitions at each
occurrence, shows "how the term or symbol is used across the paper," and generates a glossary; a
usability study found that it helped readers. Kang et al. (2020), read as an abstract, reported in 2020
that earlier approaches to detecting definitions in scholarly papers were "far from being accurate enough
to use in realworld applications," and then presented a system that improved on them. Mihalcea and Csomai
(2007), read as an abstract, show that linking concept mentions to an external resource can approach the
quality of manual annotation.

# Part II. Existing infrastructures and field guides

The statements in this part report what each tool's or guide's own documentation says, as retrieved on
November 16, 2026. Sections 7 and 8 do not evaluate the tools.

## 7. Documentation toolchains and markup standards

**Sphinx.** Sphinx has a glossary directive whose definitions "will then be referenceable with the term
role," and it reports a marked term that has no entry: "If you use a term that's not explained in a
glossary, you'll get a warning during build." A build option turns warnings into errors (Sphinx 2026).
Glossary terms receive entries in the general index that point to the definition, not to each use. The
documentation read describes no check of unmarked prose.

**LaTeX glossaries.** The `glossaries` package records, for each entry, a "number list (or location
list)," which is "the list of locations (page numbers, in this case) where the entry was indexed," for
"any entries indexed in the document (through commands like \gls or \glsadd)" (Talbot 2026). This is an
automatically collected occurrence index of marked uses. It is refreshed only by rerunning the build:
several LaTeX runs, usually with an indexing program between them. By default a reference to an undefined
entry is an error. About a quarter of the manual was read in the first round, and these two points were
confirmed in the second.

**DITA.** DITA defines a glossary entry element that "defines a single sense of a glossary term," a
`term` element whose key reference "can be used to associate a term with a resource, typically a
definition of the term," and index entries that are merged into "a generated index" (OASIS 2015). The
index is built from explicit index markup, not from uses of `term`.

**DocBook.** In DocBook, a glossary term used inline "identifies a term defined in a glossary, and may
point to it," and the schema requires that such a pointer "must point to a glossentry" (Walsh 2019).
Index entries are again explicit markup.

**TEI.** The TEI Guidelines provide `term`, which "may be associated with a gloss element by means of
its ref attribute," and `index`, which "marks a location to be indexed for whatever purpose" (TEI
Consortium 2026). TEI is an encoding standard. Generating the index is left to whoever processes the
text.

**AsciiDoc.** The AsciiDoc documentation supports marked index terms and a glossary section style, and
states that "only Asciidoctor PDF and the DocBook toolchain support creating an index catalog
automatically," while "the built-in HTML5 converter in Asciidoctor does not generate an index"
(Asciidoctor 2026).

**Terminology plugins for Markdown sites.** One plugin keeps one file per term, aggregates the terms into
a glossary page, and replaces links to term files with tooltips (GRNET 2026). Its repository is archived,
and it works on uses the author has written as links. Two others, found in the second audit round, hold
definitions and match plain prose. One keeps terms and definitions in a data file and "automatically
detects glossary terms in your markdown" (McClowes 2026). The other keeps a definition page per term and
replaces each use in the project "with a link" to that page "when building" (AngryMane 2026). A third
site generator "uses a combination of Markdown extensions to enable site-wide glossaries" of abbreviations
shown as tooltips (Squidfunk 2026). All three act on the built output. None of the pages read describes a
stored index of occurrences or a check that one is current.

**Language servers.** As an analogue from programming tools, the Language Server Protocol defines a
request "to resolve project-wide references for the symbol denoted by the given text document position,"
and a notification that signals each change to a document (Microsoft 2026). References are resolved on
request, and the server is told of each change.

## 8. Prose linters, terminology tools and occurrence views

**Vale.** Vale's vocabularies are "two plain-text files—`accept.txt` and `reject.txt`—that contain one
regular expression per line." Accepted entries feed a substitution rule and rejected entries an existence
rule. A separate rule type "will ensure that a key and its value (e.g., "advisor" and "adviser") don't
both occur in its scope" (Vale 2026). Vale holds terms, not definitions. It reports each violation, and
its documentation describes no persistent index of occurrences. Its documentation lists editor and
language-server integrations, a pre-commit hook and continuous-integration actions, and describes an
edit-time hook for a coding assistant that "lints each prose file as the assistant writes it." Each of
the trigger layers this project considers is therefore already supported for prose linting.

**textlint.** A textlint rule exists "to check and fix terms, brands and technologies spelling in your
tech writing," with a configurable list of replacements (Sapegin 2026). Only its README was read.

**Translation tools.** One translation environment offers a check that warns "if a term marked as
forbidden is used," and a check for "consistent use of terminology" against a term base (memoQ 2026).

**Qualitative analysis software.** One qualitative analysis package offers an overview of "all coded
segments of a code" (VERBI 2026). In the pages read, the analyst assigns the codes and the retrieval is
automatic. Whether the package can also assign codes from a text search was not checked.

**Knowledge bases.** MediaWiki's "What links here" facility "lists the pages on the same site which link
to a given page" (MediaWiki 2026). Obsidian distinguishes linked mentions from "unlinked mentions,"
which are "backlinks to any unlinked occurrence of the name of the active note" (Obsidian 2026). The
second is the nearest thing in a general writing tool to an index of unmarked occurrences. The pages read
describe no definitions register and no consistency check, and do not say how the list is kept current.

**Contract drafting.** One contract-drafting product reports defined, undefined and unused terms. It
"automatically flags any term that is capitalised throughout your document but lacks a formal
definition" (Definely 2026a), and a companion help article says the user can "see every occurrence of that
term throughout your agreement" (Definely 2026b). Of the tools reviewed, this is the only one whose documentation
describes a register, an index of every occurrence and a consistency report together. It works inside one
document and takes its register from that document's own definitions. No peer-reviewed study of such
tools was found.

## 9. Field guides, and the trigger

**Style guides.** The published style guides state the norm without a mechanism. Google's guide, in its
advice on writing for translation, says: "If you use a particular term for a concept in one place, then
use that exact same term elsewhere" (Google 2026). Microsoft's says: "If you mean the same thing, use the
same word," and refers writers to an A-Z word list (Microsoft 2024). The Write the Docs guide describes a
style guide as including "a list of decisions you've made about how to refer to different items you
frequently write about," and describes "docs as code" as writing documentation "with the same tools as
code," among them version control, code review and automated tests (Write the Docs 2026). The United
Kingdom's legislative drafting guidance warns that "using the same label to denote different things in
the same Bill may be confusing." It says that definitions "used in more than one provision and defined in
the first of them should generally be signposted," for example in "an index of defined terms," which
lists where each definition is, not where each term is used (OPC 2024, 4.1.7, 4.1.22).

**Hooks.** The documentation of the two hook systems most relevant to this framework states their
limits. A Git pre-commit hook "can be bypassed with the `--no-verify` option" (Git 2026). Client-side
hooks "are not copied when you clone a repository," and "if your intent with these scripts is to enforce
a policy, you'll probably want to do that on the server side" (Chacon and Straub 2014, sec. 8.3). The
pre-commit framework notes that it "can also be used as a tool for continuous integration" (Pre-commit
2026). Claude Code hooks "execute automatically at specific points in Claude Code's lifecycle" and are
"defined in JSON settings files"; a hook can run after a file is written or edited, and when such a hook
exits with code 2 its message is shown to the agent although "the tool already ran" (Anthropic 2026). The
same documentation describes a file-watching event that fires "no matter what changed the file,"
including "a process outside Claude Code entirely," for the paths it is told to watch. All of these run
only while a session is running. No peer-reviewed study of hook reliability was found.

## 10. What the review establishes

1. The occurrence index and the controlled register are both old and well theorised, largely in separate
   traditions. Concordances and keyword-in-context indexes record occurrences without definitions.
   Terminology science and vocabulary control define terms and address their occurrences in running text
   only at the margin (Hodge 2000, 12).
2. The review found one report that a register without enforcement failed: a controlled language
   discontinued, among other reasons, because its guidelines were not enforceable (Kuhn 2014, reporting
   an earlier source). It found studies showing that consistency can be measured term by term (Gašpar et
   al. 2022; Marić 2024). It found no study of whether checking a register improves consistency.
3. The nearest precedents for a register joined to an automatically maintained occurrence index come
   from software engineering (Deissenboeck and Pizka 2006), with Knuth (1984) as the precedent for an
   index generated from the text's own source. Legal informatics supplies a specification for the record
   and a content-hash test for change (Winkels and Hoekstra 2012).
4. Among the tools reviewed, registers with marked-occurrence linking are common, plugins that match
   plain prose exist, enforcement of surface forms is available, and a stored index of every occurrence
   is rare. Where a documentation toolchain keeps an index, a build refreshes it, so it is stale between
   builds. Knowledge bases show backlinks as the user works, and language servers resolve references on
   request.
5. Git's documentation says client hooks can be bypassed and are not cloned, and the sources that
   discuss enforcement point to the server side. Agent-session hooks run only while a session runs.

Items the review could not verify, and so does not rely on, are listed in
`04-adversarial-conflict-audit.md`.

## References

Aghajani, Emad, Csaba Nagy, Mario Linares-Vásquez, Laura Moreno, Gabriele Bavota, Michele Lanza, and David C. Shepherd. 2020. "Software Documentation: The Practitioners' Perspective." In Proceedings of the ACM/IEEE 42nd International Conference on Software Engineering, 590-601. ACM. https://doi.org/10.1145/3377811.3380405

Aghajani, Emad, Csaba Nagy, Olga Lucero Vega-Márquez, Mario Linares-Vásquez, Laura Moreno, Gabriele Bavota, and Michele Lanza. 2019. "Software Documentation Issues Unveiled." In 2019 IEEE/ACM 41st International Conference on Software Engineering (ICSE), 1199-1210. IEEE. https://doi.org/10.1109/ICSE.2019.00122

AngryMane. 2026. "mkdocs-glossary-plugin." Software repository README. Accessed November 16, 2026. https://github.com/AngryMane/mkdocs-glossary-plugin

Anthropic. 2026. "Hooks Reference." Claude Code documentation. Accessed November 16, 2026. https://code.claude.com/docs/en/hooks

Arora, Chetan, Mehrdad Sabetzadeh, Lionel Briand, and Frank Zimmer. 2017. "Automated Extraction and Clustering of Requirements Glossary Terms." IEEE Transactions on Software Engineering 43 (10): 918-45. https://doi.org/10.1109/TSE.2016.2635134

Asciidoctor. 2026. "Index Catalog" and "Glossary." AsciiDoc Language documentation. Accessed November 16, 2026. https://docs.asciidoctor.org/asciidoc/latest/sections/user-index/

Ashburner, Michael, Catherine A. Ball, Judith A. Blake, David Botstein, Heather Butler, J. Michael Cherry, Allan P. Davis, et al. 2000. "Gene Ontology: Tool for the Unification of Biology." Nature Genetics 25 (1): 25-29. https://doi.org/10.1038/75556

Bowker, Geoffrey C., and Susan Leigh Star. 1999. Sorting Things Out: Classification and Its Consequences. Cambridge, MA: MIT Press. https://doi.org/10.7551/mitpress/6352.001.0001

Cabré, M. Teresa. 1999. Terminology: Theory, Methods and Applications. Edited by Juan C. Sager. Translated by Janet Ann DeCesaris. Amsterdam: John Benjamins. https://doi.org/10.1075/tlrp.1

Chacon, Scott, and Ben Straub. 2014. Pro Git. 2nd ed. Apress. https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks

Daille, Béatrice. 2017. Term Variation in Specialised Corpora: Characterisation, Automatic Discovery and Applications. Amsterdam: John Benjamins. https://doi.org/10.1075/tlrp.19

Dalpiaz, Fabiano, Ivor van der Schalk, Sjaak Brinkkemper, Fatma Başak Aydemir, and Garm Lucassen. 2019. "Detecting Terminological Ambiguity in User Stories: Tool and Experimentation." Information and Software Technology 110: 3-16. https://doi.org/10.1016/j.infsof.2018.12.007

DeCuir-Gunby, Jessica T., Patricia L. Marshall, and Allison W. McCulloch. 2011. "Developing and Using a Codebook for the Analysis of Interview Data: An Example from a Professional Development Research Project." Field Methods 23 (2): 136-55. https://doi.org/10.1177/1525822X10388468

Definely. 2026a. "Reviewing Undefined Terms in the Definition Report." Definely Help Center, July 3, 2026. https://help.definely.com/en/articles/545668-reviewing-undefined-terms-in-the-definition-report

Definely. 2026b. "Reviewing Defined Terms in the Definition Report." Definely Help Center, July 6, 2026. https://help.definely.com/en/articles/545644-reviewing-defined-terms-in-the-definition-report

Deissenboeck, Florian, and Markus Pizka. 2006. "Concise and Consistent Naming." Software Quality Journal 14 (3): 261-82. https://doi.org/10.1007/s11219-006-9219-1

Evans, Eric. 2015. Domain-Driven Design Reference: Definitions and Pattern Summaries. Domain Language, Inc. https://domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf

Feitelson, Dror G., Ayelet Mizrahi, Nofar Noy, Aviad Ben Shabat, Or Eliyahu, and Roy Sheffer. 2022. "How Developers Choose Names." IEEE Transactions on Software Engineering 48 (1): 37-52. https://doi.org/10.1109/TSE.2020.2976920

Gašpar, Angelina, Sanja Seljan, and Vlasta Kučiš. 2022. "Measuring Terminology Consistency in Translated Corpora: Implementation of the Herfindahl-Hirshman Index." Information 13 (2): 43. https://doi.org/10.3390/info13020043

Gemkow, Tim, Miro Conzelmann, Kerstin Hartig, and Andreas Vogelsang. 2018. "Automatic Glossary Term Extraction from Large-Scale Requirements Specifications." In 2018 IEEE 26th International Requirements Engineering Conference (RE), 412-17. IEEE. https://doi.org/10.1109/RE.2018.00052

Gerring, John. 1999. "What Makes a Concept Good? A Criterial Framework for Understanding Concept Formation in the Social Sciences." Polity 31 (3): 357-93. https://doi.org/10.2307/3235246

Git. 2026. "githooks: Hooks Used by Git." Git reference documentation. Accessed November 16, 2026. https://git-scm.com/docs/githooks

Google. 2026. "Word List" and "Write for a Global Audience." Google Developer Documentation Style Guide. Accessed November 16, 2026. https://developers.google.com/style/word-list https://developers.google.com/style/translation

GRNET. 2026. "docusaurus-terminology." Software repository README (archived). Accessed November 16, 2026. https://github.com/grnet/docusaurus-terminology

Head, Andrew, Kyle Lo, Dongyeop Kang, Raymond Fok, Sam Skjonsberg, Daniel S. Weld, and Marti A. Hearst. 2021. "Augmenting Scientific Papers with Just-in-Time, Position-Sensitive Definitions of Terms and Symbols." In Proceedings of the 2021 CHI Conference on Human Factors in Computing Systems, 1-18. ACM. https://doi.org/10.1145/3411764.3445648

Hilton, Michael, Timothy Tunnell, Kai Huang, Darko Marinov, and Danny Dig. 2016. "Usage, Costs, and Benefits of Continuous Integration in Open-Source Projects." In Proceedings of the 31st IEEE/ACM International Conference on Automated Software Engineering, 426-37. ACM. https://doi.org/10.1145/2970276.2970358

Hodge, Gail. 2000. Systems of Knowledge Organization for Digital Libraries: Beyond Traditional Authority Files. Washington, DC: Digital Library Federation and Council on Library and Information Resources. https://www.clir.org/pubs/reports/pub91/

Kang, Dongyeop, Andrew Head, Risham Sidhu, Kyle Lo, Daniel Weld, and Marti A. Hearst. 2020. "Document-Level Definition Detection in Scholarly Documents: Existing Models, Error Analyses, and Future Directions." In Proceedings of the First Workshop on Scholarly Document Processing, 196-206. Association for Computational Linguistics. https://doi.org/10.18653/v1/2020.sdp-1.22

Knuth, Donald E. 1984. "Literate Programming." The Computer Journal 27 (2): 97-111. https://doi.org/10.1093/comjnl/27.2.97

Kuhn, Tobias. 2014. "A Survey and Classification of Controlled Natural Languages." Computational Linguistics 40 (1): 121-70. https://doi.org/10.1162/COLI_a_00168

Lawrie, Dawn, Henry Feild, and David Binkley. 2006. "Syntactic Identifier Conciseness and Consistency." In Sixth IEEE International Workshop on Source Code Analysis and Manipulation (SCAM 2006), 139-48. IEEE. https://doi.org/10.1109/SCAM.2006.31

Lee, Seonah, Rongxin Wu, Shing-Chi Cheung, and Sungwon Kang. 2021. "Automatic Detection and Update Suggestion for Outdated API Names in Documentation." IEEE Transactions on Software Engineering 47 (4): 653-75. https://doi.org/10.1109/TSE.2019.2901459

Luhn, H. P. 1960. "Key Word-in-Context Index for Technical Literature (KWIC Index)." American Documentation 11 (4): 288-95. https://doi.org/10.1002/asi.5090110403

MacQueen, Kathleen M., Eleanor McLellan, Kelly Kay, and Bobby Milstein. 1998. "Codebook Development for Team-Based Qualitative Analysis." CAM Journal 10 (2): 31-36. https://doi.org/10.1177/1525822X980100020301

Marić, Laura. 2024. "Terminological Consistency in Croatian Translations of EU Legislation: A Corpus-Based Study." Hieronymus 11: 58-87. https://doi.org/10.17234/Hieronymus.11.3

McClowes. 2026. "docusaurus-plugin-glossary." Software repository README. Accessed November 16, 2026. https://github.com/mcclowes/docusaurus-plugin-glossary

MediaWiki. 2026. "Help: What Links Here." Project documentation. Accessed November 16, 2026. https://www.mediawiki.org/wiki/Help:What_links_here

memoQ. 2026. "Edit QA Settings." memoQ documentation 12.6. Accessed November 16, 2026. https://docs.memoq.com/current/en/Workspace/edit-qa-settings.html

Microsoft. 2024. "Word Choice." Microsoft Writing Style Guide. https://learn.microsoft.com/en-us/style-guide/word-choice/

Microsoft. 2026. Language Server Protocol Specification 3.17. Accessed November 16, 2026. https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/

Mihalcea, Rada, and Andras Csomai. 2007. "Wikify! Linking Documents to Encyclopedic Knowledge." In Proceedings of the Sixteenth ACM Conference on Information and Knowledge Management, 233-42. ACM. https://doi.org/10.1145/1321440.1321475

Mokhov, Andrey, Neil Mitchell, and Simon Peyton Jones. 2018. "Build Systems à la Carte." Proceedings of the ACM on Programming Languages 2 (ICFP): 79:1-79:29. https://doi.org/10.1145/3236774

Mulvany, Nancy C. 2005. Indexing Books. 2nd ed. Chicago: University of Chicago Press. https://doi.org/10.7208/chicago/9780226550176.001.0001

NISO (National Information Standards Organization). 2010. Guidelines for the Construction, Format, and Management of Monolingual Controlled Vocabularies. ANSI/NISO Z39.19-2005 (R2010). https://www.niso.org/publications/ansiniso-z3919-2005-r2010

OASIS. 2015. Darwin Information Typing Architecture (DITA) Version 1.3 Part 3: All-Inclusive Edition. OASIS Standard, 17 December 2015. https://docs.oasis-open.org/dita/dita/v1.3/os/part3-all-inclusive/langRef/technicalContent/glossentry.html https://docs.oasis-open.org/dita/dita/v1.3/os/part3-all-inclusive/langRef/base/term.html https://docs.oasis-open.org/dita/dita/v1.3/os/part3-all-inclusive/langRef/base/indexterm.html

Obsidian. 2026. "Backlinks." Obsidian Help. Accessed November 16, 2026. https://obsidian.md/help/plugins/backlinks

OPC (Office of the Parliamentary Counsel, United Kingdom). 2024. Drafting Guidance. March 19, 2024. https://www.gov.uk/government/publications/drafting-bills-for-parliament/2024-03-19-drafting-guidance

Pre-commit. 2026. "pre-commit: A Framework for Managing and Maintaining Multi-Language Pre-Commit Hooks." Project documentation. Accessed November 16, 2026. https://pre-commit.com/

Resi, Rossella. 2025. "Representing Terminological Chains for Well-Formed Neologisms." In Proceedings of the 1st International Workshop on Terminological Neologism Management (NeoTerm 2025). CEUR Workshop Proceedings 3972. https://ceur-ws.org/Vol-3972/paper3.pdf

Roberts, Kate, Anthony Dowell, and Jing-Bao Nie. 2019. "Attempting Rigour and Replicability in Thematic Analysis of Qualitative Research Data; A Case Study of Codebook Development." BMC Medical Research Methodology 19: 66. https://doi.org/10.1186/s12874-019-0707-y

Rouse, Richard H., and Mary A. Rouse. 1974. "The Verbal Concordance to the Scriptures." Archivum Fratrum Praedicatorum 44: 5-30. https://heyjoe.fbk.eu/index.php/afp/article/view/12081

Sapegin, Artem. 2026. "textlint-rule-terminology." Software repository README. Accessed November 16, 2026. https://github.com/sapegin/textlint-rule-terminology

Semenov, Kirill, and Ondřej Bojar. 2022. "Automated Evaluation Metric for Terminology Consistency in MT." In Proceedings of the Seventh Conference on Machine Translation (WMT), 450-57. Abu Dhabi: Association for Computational Linguistics. https://doi.org/10.18653/v1/2022.wmt-1.41

Sphinx. 2026. "Directives," "Cross-Referencing Syntax," "Configuration," and "sphinx-build." Sphinx documentation (built with Sphinx 9.3.0). Accessed November 16, 2026. https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html https://www.sphinx-doc.org/en/master/usage/referencing.html

Squidfunk. 2026. "Tooltips." Material for MkDocs reference documentation. Accessed November 16, 2026. https://squidfunk.github.io/mkdocs-material/reference/tooltips/

Talbot, Nicola. 2026. User Manual for glossaries.sty v5.1. CTAN, April 21, 2026. https://ctan.org/pkg/glossaries

Tan, Lin, Ding Yuan, Gopal Krishna, and Yuanyuan Zhou. 2007. "/*iComment: Bugs or Bad Comments?*/." In Proceedings of the 21st ACM SIGOPS Symposium on Operating Systems Principles, 145-58. ACM. https://doi.org/10.1145/1294261.1294276

Tan, Wen Siang, Markus Wagner, and Christoph Treude. 2024. "Detecting Outdated Code Element References in Software Repository Documentation." Empirical Software Engineering 29 (1): 5. https://doi.org/10.1007/s10664-023-10397-6

TEI Consortium. 2026. TEI P5: Guidelines for Electronic Text Encoding and Interchange. Version 4.12.0. https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-term.html

Vale. 2026. "Vocabularies," "substitution," "consistency," and "existence." Vale documentation. Accessed November 16, 2026. https://docs.vale.sh/keys/vocabularies https://docs.vale.sh/checks/consistency https://docs.vale.sh/guides/agents.md

VERBI. 2026. "Overview of Coded Segments." MAXQDA online manual. Accessed November 16, 2026. https://www.maxqda.com/help/segment-retrieval/overview-of-coded-segments

W3C (World Wide Web Consortium). 2009. SKOS Simple Knowledge Organization System Reference. W3C Recommendation, 18 August 2009. https://www.w3.org/TR/skos-reference/

Walsh, Norman. 2019. DocBook 5.2: The Definitive Guide. Online edition. https://tdg.docbook.org/tdg/5.2/glossterm.html

Warburton, Kara. 2021. The Corporate Terminologist. Amsterdam: John Benjamins. https://doi.org/10.1075/tlrp.21

Wen, Fengcai, Csaba Nagy, Gabriele Bavota, and Michele Lanza. 2019. "A Large-Scale Empirical Study on Code-Comment Inconsistencies." In 2019 IEEE/ACM 27th International Conference on Program Comprehension (ICPC), 53-64. IEEE. https://doi.org/10.1109/ICPC.2019.00019

Winkels, Radboud, and Rinke Hoekstra. 2012. "Automatic Extraction of Legal Concepts and Definitions." In Legal Knowledge and Information Systems: JURIX 2012, Frontiers in Artificial Intelligence and Applications 250, 157ff. Amsterdam: IOS Press. https://doi.org/10.3233/978-1-61499-167-0-157

Wright, Sue Ellen, and Gerhard Budin, comps. 1997. Handbook of Terminology Management. Vol. 1, Basic Aspects of Terminology Management. Amsterdam: John Benjamins. https://doi.org/10.1075/z.htm1

Write the Docs. 2026. "Docs as Code" and "Style Guides." Community guide. Accessed November 16, 2026. https://www.writethedocs.org/guide/docs-as-code/ https://www.writethedocs.org/guide/writing/style-guides/

Zhong, Hao, and Zhendong Su. 2013. "Detecting API Documentation Errors." In Proceedings of the 2013 ACM SIGPLAN International Conference on Object Oriented Programming Systems Languages and Applications, 803-16. ACM. https://doi.org/10.1145/2509136.2509523
