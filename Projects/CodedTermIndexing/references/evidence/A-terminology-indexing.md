# Evidence slice A: terminology science, knowledge organization, indexing and concordance history, concept formation, codebooks

> **Superseded in part (2026-11-16).** Round 2 re-read Marić 2024 and Winkels and Hoekstra 2012 in full
> text and changed what they support, and corrected the reading of the Kuhn case. See
> `D-audit-reverification.md` and `R2-adversarial-scholarly.md` (F2, F3, F4, F6, F7a, F7b). Where this
> note and those disagree, they govern.

Retrieved 2026-11-16. Every quote below was retrieved in this session from the URL given. Endpoints used:
CrossRef REST (`https://api.crossref.org/works/<doi>`), Semantic Scholar Graph API, OpenAlex
(`https://api.openalex.org/works/doi:<doi>`; abstracts rebuilt from its inverted index), Europe PMC full-text
XML, publisher landing pages and open PDFs. Page locators are given only where a page number was seen.
"Abstract only" and "publisher description only" mean exactly that: nothing beyond that text was read.

Research question: what role does a machine-readable ("coded") register of term definitions, plus an
automatically maintained index of every occurrence of each term across a document set, play in the academic
literature for enforcing consistent terminology use?

---

## 1. Indexing and concordance history

### Luhn 1960 — Key word-in-context index for technical literature (KWIC index)
- Bibliographic record: H. P. Luhn. 1960. "Key word-in-context index for technical literature (kwic index)." *American Documentation* 11 (4): 288–295. Wiley. DOI 10.1002/asi.5090110403. https://doi.org/10.1002/asi.5090110403
- Metadata check: CrossRef API and Semantic Scholar API (title, venue, volume/issue/pages, Oct. 1960).
- Access level: abstract only (CrossRef abstract field; identical text from Semantic Scholar).
- Evidence (https://api.crossref.org/works/10.1002/asi.5090110403):
  > "Indexes giving keywords in their context are proposed as suitable for disseminating new information. These can be entirely machine‐generated and hence kept up‐to‐date with the current literature."

  > "A distinction is made between bibliographical indexes for new and past literature based on the willingness of the user to trade perfection for currency."

  > "A compatible coding scheme to identify the indexed documents is also proposed."
- What this supports: An early (1960) proposal that an occurrence-in-context index can be fully machine-generated and so kept current, with an explicit trade-off of "perfection for currency". It is a precedent for the *automatically maintained* half of the research question.
- Caveats: The index is a bibliographic index of titles across literature, not of term use inside a document set. The "coding scheme" codes *document identifiers*, not term definitions. Luhn says nothing here about definitions or terminological consistency.

### Busa 1980 — The annals of humanities computing: The Index Thomisticus
- Bibliographic record: R. Busa. 1980. "The annals of humanities computing: The index Thomisticus." *Computers and the Humanities* 14 (2): 83–90. Springer. DOI 10.1007/BF02403798.
- Metadata check: CrossRef API (title, journal, vol. 14, no. 2, pp. 83–90, Oct. 1980). Semantic Scholar has the title, no abstract.
- Access level: none (UNVERIFIED-CONTENT). No abstract in CrossRef, Semantic Scholar or OpenAlex. Springer's landing page returned a bot-check page / login redirect.
- Evidence: none retrieved.
- What this supports: Nothing can be claimed from this source until its text is read.
- Caveats: Cite for bibliographic existence only.

### Rouse & Rouse 1974 — The verbal concordance to the scriptures
- Bibliographic record: R. H. Rouse and M. A. Rouse. 1974. "The verbal concordance to the scriptures." *Archivum Fratrum Praedicatorum* 44: 5–30. https://heyjoe.fbk.eu/index.php/afp/article/view/12081 (PDF: https://heyjoe.fbk.eu/index.php/afp/article/download/12081/12082). No DOI found.
- Metadata check: HeyJoe (Biblioteca Fondazione Bruno Kessler) landing page and the PDF's cover sheet, both giving vol. 44 (1974), pp. 5–30. Not checked in CrossRef (no DOI).
- Access level: full text (digitized scan, CC BY-NC-ND 4.0).
- Evidence (PDF above):
  > "Of the numerous technical aids to teaching and preaching produced in the thirteenth century, the verbal concordance to the scriptures is not only one of the earliest but probably the most important, because its system of reference, its method of compilation and its successful application of complete alphabetization were used by generations of later tool-makers." (p. 5, opening)

  > "The concordance was a consciously created solution to the needs of Latin theologians for a device which would enable them to have in one place all the uses of a given word or phrase in the scriptures." (p. 5)

  > "In mastering the task of extracting and alphabetizing the some 100,000 appearances in the scriptures of roughly 10,000 words, the compilers of the verbal concordance rank with their direct descendants, the inventors of the digital computer, the tool through which most modern concordances are compiled." (pp. 5–6; footnote omitted)

  > "this consisted of the alphabetical listing of thousands of words, each provided with a record of its appearances in the Bible cited in the briefest possible fashion" (p. 6, describing the St. Jacques concordance as characterized by Quétif and Échard)
- What this supports: The occurrence-level term index ("all the uses of a given word ... in one place") has a 13th-century origin as a deliberately designed tool. The authors themselves draw the line from it to computer-compiled concordances.
- Caveats: Scholarship from 1974; later work may revise the dating and attributions. The p. 6 description of the three medieval concordances is the Rouses *reporting* Quétif and Échard (1719), whose account the article then goes on to examine critically. A verbal concordance indexes *word forms*. It is not a register of definitions and does not enforce consistent usage.

### Duncan 2021 — Index, A History of the
- Bibliographic record: Dennis Duncan. 2021. *Index, A History of the*. London: Allen Lane (Penguin). US edition: *Index, A History of the: A Bookish Adventure from Medieval Manuscripts to the Digital Age*. New York: W. W. Norton, 336 pp., ISBN 978-1-324-00254-3.
- Metadata check: Penguin UK product page (https://www.penguin.co.uk/books/311987/index-a-history-of-the-by-duncan-dennis/9780241548752), which shows "Imprint: Allen Lane", "Published: 02/09/2021", ISBN 9780241548752. That ISBN is the page's *audio download* edition ("Length: 490 minutes"; "(P) Penguin Audio 2021"). The page also lists paperback 2022 and ebook 2021 editions. Publishers Weekly review page (https://www.publishersweekly.com/9781324002543) gives the Norton details above. The hardback ISBN was not confirmed from a page I read.
- Access level: publisher description only (plus a trade review).
- Evidence:
  > "Charting its curious path from the monasteries and universities of thirteenth-century Europe to Silicon Valley in the twenty-first, Dennis Duncan reveals how the index has saved heretics from the stake, kept politicians from high office and made us all into the readers we are today." (Penguin page)

  > "he highlights key innovations in the centuries-long development of this search tool, including the trend towards putting words in alphabetical order; the shift from scrolls to codexes, whose page numbers were crucial to the creation of a usable index; and the rise of medieval universities, where scholars needed “new ways of efficiently finding parcels of text.”" (Publishers Weekly review; the inner quotation is PW quoting Duncan)
- What this supports: A recent trade-scholarly history that places the index's origin in 13th-century Europe and continues it to digital search. It corroborates the Rouses' dating at the level of a publisher blurb only.
- Caveats: Marketing copy and a review, not the book text. It is a popular history from an academic author, not a peer-reviewed study. Nothing here addresses terminology control.

### Mulvany 2005 — Indexing Books, 2nd ed.
- Bibliographic record: Nancy C. Mulvany. 2005. *Indexing Books*. 2nd ed. Chicago: University of Chicago Press. DOI 10.7208/chicago/9780226550176.001.0001. Cloth ISBN 978-0-226-55276-7. Landing page: https://www.bibliovault.org/BV.landing.epl?ISBN=9780226552767 (reached via doi.org).
- Metadata check: CrossRef API (title, author, publisher, 2005) and the BiblioVault landing page.
- Access level: publisher description and table of contents only.
- Evidence (BiblioVault page):
  > "New to this edition are discussions of \"information overload\" and the role of the index, open-system versus closed-system indexing, electronic submission and display of indexes, and trends in software development, among other topics."

  > "Indexing Books is both a practical guide and a manifesto about the vital role of the human-crafted index in the Information Age."

  Table of contents, chapter 10: "Tools for Indexing — Manual Methods; Automatic Indexing; Computer-aided Indexing; The Future".
- What this supports: The standard professional reference on book indexing treats automatic and computer-aided indexing as a topic, while it advocates the "human-crafted index". This marks a tension with fully automatic occurrence indexing.
- Caveats: Mulvany's actual argument on automatic indexing was not read. Do not attribute any specific claim about concordances or automatic indexes to her beyond the TOC headings.

---

## 2. Terminology science and terminology management

### Cabré 1999 — Terminology: Theory, Methods and Applications
- Bibliographic record: M. Teresa Cabré. 1999. *Terminology: Theory, methods and applications*. Ed. Juan C. Sager; trans. Janet Ann DeCesaris. Terminology and Lexicography Research and Practice 1. Amsterdam: John Benjamins. DOI 10.1075/tlrp.1. https://benjamins.com/catalog/tlrp.1
- Metadata check: CrossRef API (author, editor Sager, 1999) and the Benjamins catalogue page.
- Access level: publisher description and table of contents only.
- Evidence (CrossRef abstract field / Benjamins page):
  > "The book covers its subject comprehensively and deals among other things with concepts (the relation between linguistics, cognitive science, communication studies, documentation and computer science); Methodology, especially with regard to specialised language and dictionaries; ... Terminology as a standard in multilingual communication and guardian of cultures."

  Table of contents (Benjamins page) includes: "Chapter V: Computerized terminology | pp. 160–193 ... 3.Terminology and data bank 4.Terminological data banks" and "Chapter VI: Terminology and Standardization | pp. 194–214 ... 2.Terminological standardization".
- What this supports: A foundational textbook treats computerized terminology data banks and terminological standardization as core parts of the discipline.
- Caveats: Only the blurb and TOC were seen. No claim about Cabré's position on consistency enforcement can be made from these.

### Wright & Budin (comps.) 1997 — Handbook of Terminology Management, vol. 1
- Bibliographic record: Sue Ellen Wright and Gerhard Budin, comps. 1997. *Handbook of Terminology Management. Volume 1: Basic Aspects of Terminology Management*. Amsterdam: John Benjamins. DOI 10.1075/z.htm1. https://benjamins.com/catalog/z.htm1
- Metadata check: CrossRef API (editors Wright, Budin; 1997) and the Benjamins page (which labels them "Compiler").
- Access level: publisher description and table of contents only.
- Evidence (CrossRef abstract field):
  > "The Handbook covers a broad range of topics integrated from an international perspective and treats such fundamental issues as: practical methods of terminology management; creation and use of terminological tools (terminology databases, on-line dictionaries, etc.); terminological applications."

  TOC items (Benjamins page): "1.3.1 Terminological Definitions Bruno de Bessé and Juan C. Sager | pp. 63–74"; "2.2 Prescriptive Terminology"; "2.2.1 Terminology Standardization : Management Strategies Sue Ellen Wright | pp. 197–202"; "2.2.4 Do’s and Don’ts of Terminology Management Catherine Bowman, Diane Michaud and Heidi Suonuuti | pp. 215–217".
- What this supports: The handbook places terminology databases, terminological definitions and prescriptive (standardizing) terminology management within one practical field.
- Caveats: Chapter contents not read. Chapter authors should be cited individually if a chapter is used.

### Warburton 2021 — The Corporate Terminologist
- Bibliographic record: Kara Warburton. 2021. *The Corporate Terminologist*. Terminology and Lexicography Research and Practice 21. Amsterdam: John Benjamins. xxiv, 249 pp. DOI 10.1075/tlrp.21. https://benjamins.com/catalog/tlrp.21
- Metadata check: CrossRef API (title, author, 2 Mar 2021) and the Benjamins page. OpenAlex supplied the same blurb.
- Access level: publisher description and table of contents only.
- Evidence (Benjamins page):
  > "The Corporate Terminologist is the first monograph that addresses the principles and methods for managing terminology in content production environments that are both demanding and multilingual, such as those found in global companies and institutions."

  > "The repurposability of terminology resources is a fundamental criterion that motivates the design, selection, and use of terminology management tools, and has a bearing on the definition of termhood itself."

  TOC: "Create the termbase | pp. 181–189", "Launch the termbase | pp. 191–199", "Expand the termbase | pp. 201–214", "Maintain quality | pp. 215–227"; "The terminology management system | pp. 163–177".
- What this supports: Corporate terminology management is organized around a termbase (a structured, machine-readable term register) that is created, launched, expanded and quality-maintained. The publisher describes repurposability of terminology resources as a design criterion for the tools.
- Caveats: Book text not read. Nothing seen here states that the termbase is used to *check* documents automatically.

### Daille 2017 — Term Variation in Specialised Corpora
- Bibliographic record: Béatrice Daille. 2017. *Term Variation in Specialised Corpora: Characterisation, automatic discovery and applications*. Terminology and Lexicography Research and Practice 19. Amsterdam: John Benjamins. DOI 10.1075/tlrp.19. https://benjamins.com/catalog/tlrp.19
- Metadata check: CrossRef API (lists Daille as author) and the Benjamins page (lists her as "Editor"). Note the discrepancy.
- Access level: publisher description and table of contents only.
- Evidence (CrossRef abstract field):
  > "This book presents the first complete inventory of term variants and the linguistic procedures that lead to their formation."

  > "The book provides insights into the following issues: What is a variant? What are the main linguistic mechanisms involved in the transformation of base terms into variants? How can variants be automatically detected in texts? Should variation be taken into account in natural language processing applications?"

  TOC: "Chapter 6. Processing methods for the detection of variants from corpora | pp. 109–124"; "Chapter 8. Synonymic variants | pp. 147–168".
- What this supports: Term variation, meaning several forms for one concept, is an established research object in computational terminology, and its automatic detection in texts is an open methodological question. This is the detection problem that occurrence indexing of a term register must handle.
- Caveats: The book's answers are not read. The publisher frames variation descriptively; it does not cast variation as error to be eliminated.

### Resi 2025 — Representing Terminological Chains for Well-Formed Neologisms (workshop paper)
- Bibliographic record: Rossella Resi. 2025. "Representing Terminological Chains for Well-Formed Neologisms." In *Proceedings of the 1st International Workshop on Terminological Neologism Management (NeoTerm 2025)*, Thessaloniki, 18 June 2025. CEUR Workshop Proceedings vol. 3972. https://ceur-ws.org/Vol-3972/paper3.pdf. No DOI.
- Metadata check: CEUR volume index page (https://ceur-ws.org/Vol-3972/) and the PDF header. No CrossRef record (CEUR issues no DOIs).
- Access level: full text.
- Evidence (PDF, section 2.2 "Term consistency", PDF p. 2):
  > "Term consistency means using a single designation for a concept across all occurrences within a document or a domain."

  > "The former is considered a key principle of technical writing [8,9] while the latter serves as a quality criterion in major evaluation methods for terminological errors in translation." (former = intralingual, latter = interlingual consistency)

  > "Nonetheless text-linguistic approaches to terminology, emphasize that term variants may reflect different perspectives on the same concept. Rather then diminishing clarity, this can add functional depth to the text [10-11]."
- What this supports: It gives a crisp definition of term consistency as "a single designation for a concept across all occurrences". It also records the counter-position that variation can be functional, an important caveat against mechanical enforcement.
- Caveats: Workshop paper, 2025, German–Italian translation focus. It is not a measurement study. The "key principle" claim is attributed to its refs [8,9], which were not checked.

---

## 3. Knowledge organization systems and controlled vocabulary

### Hodge 2000 — Systems of Knowledge Organization for Digital Libraries
- Bibliographic record: Gail Hodge. 2000. *Systems of Knowledge Organization for Digital Libraries: Beyond Traditional Authority Files*. Washington, DC: Digital Library Federation and Council on Library and Information Resources (CLIR report pub91). April 2000, 43 pp. ISBN 1-887334-76-9. https://www.clir.org/pubs/reports/pub91/ ; PDF https://www.clir.org/wp-content/uploads/sites/6/pub91.pdf
- Metadata check: CLIR landing page ("Gail Hodge (4/00, 43pp) ... ISBN 1-887334-76-9") and the PDF title page. No DOI.
- Access level: full text. Printed page numbers are given below; printed page = PDF page − 6.
- Evidence (PDF):
  > "authority files that control variant versions of key information (such as geographic names and personal names)" (p. 3)

  > "Authority files are lists of terms that are used to control the variant names for an entity or the domain value for a particular field. ... Nonpreferred terms may be linked to the preferred versions." (p. 5)

  > "Glossaries. A glossary is a list of terms, usually with definitions. The terms may be from a specific subject field or from a particular work. The terms are defined within a specific environment and rarely include variant meanings." (p. 5)

  > "The same entity can be characterized in different ways, depending on the KOS that is used." (p. 4)

  > "It is used by many U.S. government agencies for consistent naming of plants and animals for regulatory and monitoring purposes. To link textual material in a digital library to the ITIS record, the organism name can be identified manually or automatically in the text and submitted as a query to the ITIS database." (p. 12)

  > "Because of the ambiguity in organism names, many examples of this type are now created manually." (p. 12)
- What this supports: This is the classic KOS typology. A glossary is a term list with definitions scoped to "a particular work", and authority files control variants by linking non-preferred to preferred forms. Hodge also describes identifying registered names in text, manually or automatically, and linking each to its authority record, while noting that ambiguity pushed that linking back to manual work.
- Caveats: Written in 2000 for digital libraries, not for authoring. Linking text to authority records serves access and enrichment; Hodge does not present it as consistency enforcement on authors.

### Zeng 2008 — Knowledge Organization Systems (KOS)
- Bibliographic record: Marcia Lei Zeng. 2008. "Knowledge Organization Systems (KOS)." *Knowledge Organization* 35 (2–3): 160–182. DOI 10.5771/0943-7444-2008-2-3-160.
- Metadata check: CrossRef API (title, journal, 35(2–3): 160–182, 2008).
- Access level: none directly (UNVERIFIED-CONTENT for the primary). CrossRef, Semantic Scholar and OpenAlex carry no abstract; the Nomos eLibrary page returned 403. One passage of Zeng's abstract was retrieved *as quoted* in a secondary source: Fulvio Mazzocchi, "Knowledge organization system (KOS)", *ISKO Encyclopedia of Knowledge Organization*, https://www.isko.org/cyclo/kos
- Evidence (secondary quotation, from the ISKO page, introduced there as "Zeng (2008, from the abstract)"):
  > "These systems model the underlying semantic structure of a domain and provide semantics, navigation, and translation through labels, definitions, typing, relationships, and properties for concepts [...] Embodied as (Web) services, they facilitate resource discovery and retrieval by acting as semantic road maps, thereby making possible a common orientation for indexers and future users, either human or machine [...]."
- What this supports: Only if cited through Mazzocchi: KOSs carry "labels, definitions ... for concepts" and give "a common orientation for indexers and future users, either human or machine".
- Caveats: Secondary quotation with ellipses by Mazzocchi. Verify against the primary before use, or cite "as quoted in Mazzocchi".

### Lancaster — Vocabulary Control for Information Retrieval
- Bibliographic record: F. Wilfrid Lancaster. *Vocabulary Control for Information Retrieval*. Washington, DC: Information Resources Press. 1st ed. 1972 (ISBN 0878150064, 233 pp.); 2nd ed. 1986 (ISBN 0878150536, 270 pp.).
- Metadata check: Open Library work record OL2274919W and its editions list (https://openlibrary.org/works/OL2274919W). The publisher place was not shown there; "Washington, DC" is NOT verified and must be confirmed. WorldCat search returned HTTP 429 (rate-limited), so it is not confirmed there.
- Access level: none (UNVERIFIED-CONTENT).
- Evidence: none.
- What this supports: Bibliographic existence only.
- Caveats: Confirm the place of publication and the edition before citing.

### Bowker & Star 1999 — Sorting Things Out
- Bibliographic record: Geoffrey C. Bowker and Susan Leigh Star. 1999. *Sorting Things Out: Classification and Its Consequences*. Cambridge, MA: MIT Press. DOI 10.7551/mitpress/6352.001.0001.
- Metadata check: CrossRef API (title, authors, MIT Press, 1999-09-29) and Semantic Scholar (subtitle).
- Access level: publisher description only (CrossRef abstract field).
- Evidence (https://api.crossref.org/works/10.7551/mitpress/6352.001.0001):
  > "All are examples of classification—the scaffolding of information infrastructures."

  > "The authors emphasize the role of invisibility in the process by which classification orders human interaction."

  > "Sorting Things Out has a moral agenda, for each standard and category valorizes some point of view and silences another."
- What this supports: A critical counterweight. Standardized categories are not neutral, and they become invisible infrastructure. Any enforced term register "valorizes some point of view".
- Caveats: Publisher copy, not the authors' text. The book concerns classification systems such as ICD and race classification, not document terminology.

### Ashburner et al. 2000 — Gene Ontology: tool for the unification of biology
- Bibliographic record: Michael Ashburner, Catherine A. Ball, Judith A. Blake, David Botstein, Heather Butler, J. Michael Cherry, Allan P. Davis, Kara Dolinski, et al. (The Gene Ontology Consortium). 2000. "Gene Ontology: tool for the unification of biology." *Nature Genetics* 25 (1): 25–29. DOI 10.1038/75556. Author manuscript: https://pmc.ncbi.nlm.nih.gov/articles/PMC3037419/
- Metadata check: CrossRef API (vol. 25, no. 1, pp. 25–29, May 2000) and the PMC record.
- Access level: full text (PMC author manuscript, NIHMS269796).
- Evidence (PMC3037419):
  > "The goal of the Gene Ontology Consortium is to produce a dynamic, controlled vocabulary that can be applied to all eukaryotes even as knowledge of gene and protein roles in cells is accumulating and changing." (Abstract)

  > "The goal of the Consortium is to produce a structured, precisely defined, common, controlled vocabulary for describing the roles of genes and gene products in any organism." (section "A dynamic gene ontology")

  > "In this way the GO Consortium has built up a system that supports a common language with specific, agreed-on terms with definitions and supporting documentation (the GO ontologies) that can be understood and used by a wide biological community."

  > "The GO project is currently using a flat file format to store the ontologies, definitions of terms and gene associations."

  > "It is hoped that the GO concepts ... will find favour among biologists so that we can all facilitate, in our writing as well as our thinking, the grand unification of biology that the genome sequences portend." (ellipsis mine)
- What this supports: This is the strongest exemplar of a coded, machine-readable register of defined terms ("agreed-on terms with definitions", stored as files) built for consistent use across many databases. Its consistency mechanism is annotation of records against the register, and the authors explicitly hope for uptake "in our writing".
- Caveats: 2000-era description. GO annotates *database records*, not prose documents, and the paper describes no occurrence index of terms in texts. The "writing" remark is an aspiration, not an enforcement mechanism.

### Kuhn 2014 — A Survey and Classification of Controlled Natural Languages
- Bibliographic record: Tobias Kuhn. 2014. "A Survey and Classification of Controlled Natural Languages." *Computational Linguistics* 40 (1): 121–170. MIT Press. DOI 10.1162/COLI_a_00168. Preprint: arXiv:1507.01701v1 (7 Jul 2015), https://arxiv.org/pdf/1507.01701
- Metadata check: CrossRef API and Semantic Scholar (vol. 40, no. 1, pp. 121–170, March 2014).
- Access level: full text (arXiv version; the MIT Press PDF returned 403). Page numbers below are **arXiv PDF pages**, not journal pages.
- Evidence (arXiv PDF):
  > "A typical CL uses a well-defined subset of a language’s grammar and lexicon, but adds the terminology needed in a technical domain. (Kittredge 2003)" (p. 2; Kuhn quoting Kittredge)

  > "The vocabulary of the language is restricted to around 800 to 1,000 words (Crabbe 2009), with only one meaning defined for each of them (e.g., right only as the opposite of left)." (p. 15, on Caterpillar Fundamental English)

  > "CFE was discontinued by Caterpillar in 1982, because (among other reasons) “the basic guidelines of CFE were not enforceable in the English documents produced” (Kamprath et al. 1998). As a result, Caterpillar Technical English (see appendix) was developed following a different approach: The restrictions on the language should be enforceable" (p. 15)

  > "These rules restrict the language on the lexical level (e.g., “Use approved words from the Dictionary only as the part of speech given”) ... as well as on the semantic level (e.g., “Keep to the approved meaning of a word in the Dictionary. Do not use the word with any other meaning.”)." (p. 16, on ASD Simplified Technical English)

  > "Written texts can be revised and given to a language checker before publication, whereas spoken language typically lacks this two-stage process." (p. 22)

  > "An open list of about 250 words defines preferred terminology for the given computer and telephony domain, and clarifies usage and meaning of these words." (p. 28, appendix entry for a corporate CNL)
- What this supports: Industrial controlled languages pair an approved dictionary, one meaning per word, with rules such as "Keep to the approved meaning". Kuhn reports a case (Caterpillar Fundamental English) abandoned in part because its guidelines "were not enforceable in the English documents produced", followed by a successor designed to be enforceable. He also notes the existence of pre-publication language checkers. This is direct evidence that a definitional register without enforcement can fail.
- Caveats: The CFE failure is Kuhn quoting Kamprath et al. 1998 (a secondary report). Survey article, English-based CNLs only. The arXiv pagination differs from the journal's.

### Mihalcea & Csomai 2007 — Wikify! Linking documents to encyclopedic knowledge
- Bibliographic record: Rada Mihalcea and Andras Csomai. 2007. "Wikify!: linking documents to encyclopedic knowledge." In *Proceedings of the Sixteenth ACM Conference on Information and Knowledge Management (CIKM '07)*, 233–242. ACM. DOI 10.1145/1321440.1321475.
- Metadata check: CrossRef API (pp. 233–242, 2007-11-06) and Semantic Scholar (full title).
- Access level: abstract only (OpenAlex). The author PDF (https://web.eecs.umich.edu/~mihalcea/papers/mihalcea.cikm07.pdf) was downloaded, but its two-column text extraction was garbled, so no body quotes are used.
- Evidence (https://api.openalex.org/works/doi:10.1145/1321440.1321475):
  > "Given an input document, the system identifies the important concepts in the text and automatically links these concepts to the corresponding Wikipedia pages. Evaluations of the system show that the automatic annotations are reliable and hardly distinguishable from manual annotations."
- What this supports: Automatic identification of concept mentions in a document and linking of each to an external definitional resource is an established NLP task. In this study, automatic links approached manual quality.
- Caveats: The resource is Wikipedia, not a project-specific register. The task includes disambiguation (choosing which entry), not checking consistency of usage.

---

## 4. Social-science concept formation

### Sartori 1970 — Concept Misformation in Comparative Politics
- Bibliographic record: Giovanni Sartori. 1970. "Concept Misformation in Comparative Politics." *American Political Science Review* 64 (4): 1033–1053. DOI 10.2307/1958356.
- Metadata check: CrossRef API (vol. 64, no. 4, pp. 1033–1053, Dec. 1970).
- Access level: opening text only. The CrossRef "abstract" field holds the article's first two paragraphs. Cambridge Core returned 403.
- Evidence (https://api.crossref.org/works/10.2307/1958356):
  > "In a very crucial sense there is no methodology without logos, without thinking about thinking. And if a firm distinction is drawn—as it should be—between methodology and technique, the latter is no substitute for the former."
- What this supports: Only the general framing: Sartori distinguishes conceptual methodology from technique.
- Caveats: The retrieved text does NOT contain Sartori's argument on "conceptual stretching" or the ladder of abstraction. Do not cite those from this evidence; they need the full text.

### Gerring 1999 — What Makes a Concept Good?
- Bibliographic record: John Gerring. 1999. "What Makes a Concept Good? A Criterial Framework for Understanding Concept Formation in the Social Sciences." *Polity* 31 (3): 357–393. University of Chicago Press. DOI 10.2307/3235246.
- Metadata check: CrossRef API (vol. 31, no. 3, pp. 357–393, March 1999).
- Access level: abstract only (OpenAlex). The publisher page returned 403.
- Evidence (https://api.openalex.org/works/doi:10.2307/3235246):
  > "Goodness in concept formation, I argue, cannot be reduced to 'clarity,' to empirical or theoretical relevance, to a set of rules, or to the methodology particular to a given study."

  > "a standard set of criteria, whose demands are felt in the formation and use of all social science concepts: (1) familiarity, (2) resonance, (3) parsimony, (4) coherence, (5) differentiation, (6) depth, (7) theoretical utility, and (8) field utility."

  > "Rather than conceiving of concept formation as a method (with a fixed set of rules and a definite outcome), I view it as a highly variable process involving trade-offs among these eight demands."
- What this supports: A caution for the research question. Gerring holds that concept quality is not reducible to "a set of rules" and involves trade-offs. A coded register can fix a term's definition and use, but that alone does not make the concept good.
- Caveats: Abstract only. Gerring does not discuss registers or indexes.

---

## 5. Qualitative-research codebooks (a coded register of definitions applied across a document set)

### MacQueen et al. 1998 — Codebook Development for Team-Based Qualitative Analysis
- Bibliographic record: Kathleen M. MacQueen, Eleanor McLellan, Kelly Kay, and Bobby Milstein. 1998. "Codebook Development for Team-Based Qualitative Analysis." *CAM Journal* (now *Field Methods*) 10 (2): 31–36. SAGE. DOI 10.1177/1525822X980100020301.
- Metadata check: CrossRef API (container title "CAM Journal", vol. 10, no. 2, pp. 31–36, May 1998).
- Access level: opening text only. The OpenAlex "abstract" field holds the article's opening text, truncated; the SAGE page returned 403.
- Evidence (https://api.openalex.org/works/doi:10.1177/1525822X980100020301):
  > "Codes are the building blocks for theory or model building and the foundation on which the analyst’s arguments rest. Implicitly or explicitly, they embody the assumptions underlying the analysis."

  > "We generally use multiple coders so that we can assess the reliability and validity of the coded data through intercoder agreement measures"

  > "This paper describes (1) how a structured codebook provides a stable frame for the dynamic analysis of textual data; (2) how specific codebook features can improve intercoder agreement among multiple researchers"
- What this supports: In team qualitative research a structured codebook, a register of defined codes, is presented as "a stable frame" whose features "can improve intercoder agreement". That is, a definitions register is used to make many analysts apply labels consistently across a text corpus.
- Caveats: Opening text only; the specific codebook features were not read. Consistency here concerns *coders applying codes to data*, not *authors using terms in prose*. That is an analogy, not identity, with the research question.

### DeCuir-Gunby, Marshall & McCulloch 2011 — Developing and Using a Codebook for the Analysis of Interview Data
- Bibliographic record: Jessica T. DeCuir-Gunby, Patricia L. Marshall, and Allison W. McCulloch. 2011. "Developing and Using a Codebook for the Analysis of Interview Data: An Example from a Professional Development Research Project." *Field Methods* 23 (2): 136–155. DOI 10.1177/1525822X10388468.
- Metadata check: CrossRef API (vol. 23, no. 2, pp. 136–155; online 2010-12-27). Semantic Scholar gives 2011.
- Access level: abstract only (CrossRef).
- Evidence (https://api.crossref.org/works/10.1177/1525822X10388468):
  > "This article gives specific steps on how to create a codebook for coding interview data. The authors examine the development of theory- and data-driven codes through the discussion of a professional development (PD) research project. They also discuss how to train others to code using the codebook, including how to establish reliability."
- What this supports: Codebooks are treated as instruments for training multiple coders and establishing reliability.
- Caveats: Abstract only. Date: online December 2010, issue 2011.

### Roberts, Dowell & Nie 2019 — Attempting rigour and replicability in thematic analysis
- Bibliographic record: Kate Roberts, Anthony Dowell, and Jing-Bao Nie. 2019. "Attempting rigour and replicability in thematic analysis of qualitative research data; a case study of codebook development." *BMC Medical Research Methodology* 19: 66. DOI 10.1186/s12874-019-0707-y. Full text: Europe PMC PMC6437927 (https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6437927/fullTextXML).
- Metadata check: CrossRef API (vol. 19, issue 1, 2019-03-28) and Semantic Scholar. The article number 66 comes from the PMC XML `<elocation-id>66`.
- Access level: full text (CC BY, via Europe PMC XML). There are no page numbers; section headings are given instead.
- Evidence (PMC6437927 full text):
  > "Codes were written following the guidelines of Boyatzis [9] and were classified with the following: label, definition, description, qualifications or exclusions and examples from the raw data." (Results, "Summarising the data and identifying initial themes")

  > "The decision to use and test a codebook was important in the demonstration of rigour in this project, as it allowed a clear trail of evidence for the validity of the study and also allowed ease of inter-rater reliability testing of the data." (Methods, "Developing the codebook and stages of data coding and testing")

  > "Reliability was tested in this project in two ways: Consistency of judgment over absence and presence (test-retest reliability); and Consistency of judgement across various viewers (inter-rater reliability)." (Results, "Testing the reliability of the code")

  > "The development, use and testing of codebooks is not often reported in qualitative research reports, and rarely in enough detail for replication of the process."

  > "minimal changes to the codebook were made at this stage unless it was deemed absolutely necessary as the codebook was now deemed to be in its final version."
- What this supports: This gives a concrete schema for a register entry: label, definition, description, qualifications or exclusions, and examples. The codebook is linked explicitly to consistency of judgement across coders and over time, and to an audit trail. The codebook is also frozen once final, a form of version control on definitions.
- Caveats: A single case study (a New Zealand health-services PhD project). Reliability here was a simple percent-agreement formula, which the authors call "a much cruder" measure than alternatives. The codebook is applied by human coders, with no automated occurrence index.

---

## 6. Studies that measure terminology (in)consistency

### Gašpar, Seljan & Kučiš 2022 — Measuring Terminology Consistency in Translated Corpora
- Bibliographic record: Angelina Gašpar, Sanja Seljan, and Vlasta Kučiš. 2022. "Measuring Terminology Consistency in Translated Corpora: Implementation of the Herfindahl-Hirshman Index." *Information* 13 (2): 43. MDPI. DOI 10.3390/info13020043.
- Metadata check: CrossRef API (vol. 13, no. 2, art. 43, 2022-01-18).
- Access level: abstract only (CrossRef). The MDPI page returned 403.
- Evidence (https://api.crossref.org/works/10.3390/info13020043):
  > "Consistent terminology can positively influence communication, information transfer, and proper understanding. In multilingual written communication processes, challenges are augmented due to translation variants."

  > "Terminology consistency was measured using the HHI—a commonly accepted measurement of market concentration. Results show that the HHI can be used for measuring terminology consistency to improve information transfer and message understanding. In translation settings, the process shows the need for quality management solutions."
- What this supports: Terminology consistency can be operationalized and scored across a corpus by measuring how concentrated the renderings of each term are. This is the occurrence-level counting that a term index makes possible.
- Caveats: The work is interlingual (translation), on legal corpora (Croatian/English/Latin). Abstract only; the extraction and validation details are unread.

### Marić 2024 — Terminological consistency in Croatian translations of EU legislation
- Bibliographic record: Laura Marić. 2024. "Terminological consistency in Croatian translations of EU legislation: a corpus-based study." *Hieronymus: Časopis za istraživanja prevođenja i terminologije* 11: 58–87. DOI 10.17234/Hieronymus.11.3. https://hrcak.srce.hr/en/323753
- Metadata check: CrossRef API (vol. 11, pp. 58–87, 2024-12-16) and the Hrčak landing page.
- Access level: abstract only.
- Evidence (Hrčak page):
  > "The EU produces thousands of translations, with particular emphasis on terminological consistency as it can impact clarity and legal certainty. However, the fast-paced, “multitranslator” environment raises the question of how consistently terminology is used."

  > "Terminological consistency is measured using the HHI, following the example of Itagaki et al. (2007). Trade-related terms are taken from IATE and analysed on a corpus compiling DGT’s English-Croatian translation memories from 2020. The results confirm the presence of terminological inconsistency and show a weak positive correlation between consistency and frequency, and no correlation between consistency and structure."
- What this supports: Measurable inconsistency persists even where a coded term register (IATE) exists and consistency is institutionally emphasized. Terms from a register were checked against a corpus and inconsistency was found. This is direct evidence that a register alone does not guarantee consistent use.
- Caveats: Translation corpus, one language pair, one domain, 2020 data. Abstract only. Itagaki et al. (2007) is cited but was NOT located or verified here.

### Semenov & Bojar 2022 — Automated Evaluation Metric for Terminology Consistency in MT
- Bibliographic record: Kirill Semenov and Ondřej Bojar. 2022. "Automated Evaluation Metric for Terminology Consistency in MT." In *Proceedings of the Seventh Conference on Machine Translation (WMT)*, 450–457. Abu Dhabi: Association for Computational Linguistics. DOI 10.18653/v1/2022.wmt-1.41. https://aclanthology.org/2022.wmt-1.41/
- Metadata check: CrossRef API (pp. 450–457, 2022) and the ACL Anthology page.
- Access level: abstract only.
- Evidence (ACL Anthology page):
  > "The most widely used metrics for machine translation tackle sentence-level evaluation. However, at least for professional domains such as legal texts, it is crucial to measure the consistency of the translation of the terms throughout the whole text."

  > "We also demonstrate that the proposed metric scores significantly differ from the widespread automated metric scores, and correlate with the human assessment."
- What this supports: Whole-document term consistency is a distinct property that sentence-level evaluation misses, and it can be scored automatically in line with human judgement. This argues for document-level, occurrence-wide checking.
- Caveats: Evaluates MT output (Czech→English), not human authoring. Abstract only.

(Only three measurement studies were verified. A fourth, on monolingual technical documentation, was searched for but not found in peer-reviewed form. Itagaki et al. 2007 is a likely candidate but was not verified.)

---

## 7. Automatic definition detection, glossary linking and defined-term checking

### Winkels & Hoekstra 2012 — Automatic Extraction of Legal Concepts and Definitions
- Bibliographic record: Radboud Winkels and Rinke Hoekstra. 2012. "Automatic Extraction of Legal Concepts and Definitions." In *Legal Knowledge and Information Systems (JURIX 2012)*, Frontiers in Artificial Intelligence and Applications 250, starting p. 157 (start page from the DOI; end page not seen). IOS Press. DOI 10.3233/978-1-61499-167-0-157. Author manuscript: https://pure.uva.nl/ws/files/88234356/125492_Winkels_Hoekstra_Jurix_2012_2.pdf
- Metadata check: CrossRef API (title, authors, series, 2012) and the UvA-DARE record (https://dare.uva.nl/id/332bc8f9-24d9-4cc8-ab81-dce66ce89fe0). The page range end is not confirmed.
- Access level: full text (accepted author manuscript).
- Evidence (author manuscript, section 2 "Goals of the Experiment"):
  > "A first step is to list all concepts as defined in legislation and possibly other sources."

  > "Moreover, for every concept we need to add information: ... A reference to the text where the concept is defined if that is the case in the input sources; The definition of the concept if it is given in the sources; References to all occurrences of the concept in the sources; Possible relations with other concepts; Possible synonyms of the concept or strongly related concepts." (list numbering lost in extraction)

  Abstract (UvA-DARE): > "In this paper we present the results of an experiment in automatic concept and definition extraction from written sources of law using relatively simple natural language and standard semantic web technology. The software was tested on six laws from the tax domain."
- What this supports: This is the closest match in the slice to the research question's full design. For a public administration (the Dutch tax authority), each legally defined concept is to be recorded with its defining text, its definition, "references to all occurrences of the concept in the sources", relations and synonyms. The record is a machine-readable register combined with an occurrence index, built with semantic-web (SKOS/Dublin Core) technology.
- Caveats: An experiment on six Dutch tax laws (2012). The purpose is traceability and impact assessment of legal change, not enforcing drafters' consistency.

### Kang et al. 2020 — Document-Level Definition Detection in Scholarly Documents
- Bibliographic record: Dongyeop Kang, Andrew Head, Risham Sidhu, Kyle Lo, Daniel Weld, and Marti A. Hearst. 2020. "Document-Level Definition Detection in Scholarly Documents: Existing Models, Error Analyses, and Future Directions." In *Proceedings of the First Workshop on Scholarly Document Processing*, 196–206. ACL. DOI 10.18653/v1/2020.sdp-1.22. https://aclanthology.org/2020.sdp-1.22/
- Metadata check: CrossRef API (pp. 196–206, 2020; author family names Kang, Head, Sidhu, Lo, Weld, Hearst). Full given names are from standard ACL listing conventions and were NOT confirmed on a page read; confirm before citing.
- Access level: abstract only (ACL Anthology page).
- Evidence:
  > "The task of definition detection is important for scholarly papers, because papers often make use of technical terminology that may be unfamiliar to readers. Despite prior work on definition detection, current approaches are far from being accurate enough to use in realworld applications."

  > "We note that performance on the high-recall document-level task is much lower than in the standard evaluation approach, due to the necessity of incorporation of document structure as features."
- What this supports: Automatically finding where terms are defined in a document is hard, and document-wide recall is much worse than sentence-level benchmarks suggest. This is an argument for an *explicit, author-maintained* coded register rather than inferring definitions from prose.
- Caveats: Workshop paper, 2020; the state of the art has since moved on.

### Head et al. 2021 — Augmenting Scientific Papers with Just-in-Time, Position-Sensitive Definitions of Terms and Symbols (ScholarPhi)
- Bibliographic record: Andrew Head, Kyle Lo, Dongyeop Kang, Raymond Fok, Sam Skjonsberg, Daniel S. Weld, and Marti A. Hearst. 2021. "Augmenting Scientific Papers with Just-in-Time, Position-Sensitive Definitions of Terms and Symbols." In *Proceedings of the 2021 CHI Conference on Human Factors in Computing Systems*, 1–18. ACM. DOI 10.1145/3411764.3445648.
- Metadata check: CrossRef API (pp. 1–18, 2021-05-06; six author family names) and the Semantic Scholar API (seven authors including Hearst; S2 year 2020 reflects the arXiv preprint 2009.14237).
- Access level: abstract only (Semantic Scholar).
- Evidence (https://api.semanticscholar.org/graph/v1/paper/DOI:10.1145/3411764.3445648):
  > "Comprehension is often stymied when the information needed to understand a passage resides somewhere else—in another section, or in another paper."

  > "We introduce ScholarPhi, an augmented reading interface with four novel features: (1) tooltips that surface position-sensitive definitions from elsewhere in a paper, (2) a filter over the paper that “declutters” it to reveal how the term or symbol is used across the paper, (3) automatic equation diagrams that expose multiple definitions in parallel, and (4) an automatically generated glossary of important terms and symbols."

  > "A usability study showed that the tool helps researchers of all experience levels read papers."
- What this supports: This is reader-side evidence. Linking each occurrence of a term to its definition, showing every use of a term across a document, and auto-generating a glossary helped readers in a usability study. It is the same structure as definitions register plus occurrence index, but used for comprehension rather than enforcement.
- Caveats: Author-list discrepancy: CrossRef lists six authors and Semantic Scholar seven (adds Hearst); verify on the ACM page. Usability study only (no effect sizes seen). Single-paper scope, not a document set.

---

## Not verified / not found

- **Busa 1980** (10.1007/BF02403798): metadata only; content UNVERIFIED (no abstract anywhere; Springer blocked).
- **Zeng 2008** (10.5771/0943-7444-2008-2-3-160): primary content not reached (Nomos 403). One abstract passage is available only as quoted in Mazzocchi's ISKO Encyclopedia entry.
- **Lancaster, Vocabulary Control for Information Retrieval**: Open Library record only (1972; 2nd ed. 1986; Information Resources Press). Place of publication not verified. WorldCat rate-limited (HTTP 429). No content.
- **Sartori 1970**: only the opening paragraphs were reached. His "conceptual stretching" / ladder-of-abstraction argument is NOT verified from text.
- **Mulvany 2005**: publisher description and TOC only; her treatment of automatic indexing is unread.
- **Duncan 2021**: publisher/review copy only. The hardback ISBN is unconfirmed (the Penguin page ISBN 9780241548752 is the audio edition).
- **Itagaki et al. 2007** (cited by Marić as the origin of the HHI consistency method): not located or verified.
- **A peer-reviewed monolingual study of terminology inconsistency in technical documentation**: searched, none found. The only hit was a CEUR workshop paper (Resi 2025), included above as a definitional source.
- **Peer-reviewed work on "defined term" checking in contracts specifically**: none found. Search results were vendor products (LegalOn, Robin AI, Zuva, Definely) and a US patent, none of which are scholarly or were read. They are not recorded as sources.
- **Wikify! body text**: the PDF was downloaded but the text extraction was garbled, so only the abstract is used.
- **MacQueen et al. 1998**: the OpenAlex text is the opening of the article and truncated; codebook-structure details were unread.
- The end page for Winkels & Hoekstra 2012, and full given names for Kang et al. 2020 need confirmation on the publisher pages.
