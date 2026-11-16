# Evidence slice B — software engineering, requirements engineering, documentation, literate programming, build systems / CI

> **Superseded in part (2026-11-16).** The Mokhov et al. locator 79:4 for Definition 2.1 and footnote 5
> is wrong; the page is 79:3. See `D-audit-reverification.md` and `R2-adversarial-scholarly.md` (F1,
> F11, F12, F15, F16). Where this note and those disagree, they govern.

Gathered 2026-11-16. Every quote below was retrieved during this session from the URL given next to it.
Metadata was checked against the CrossRef API (`https://api.crossref.org/works/<doi>`) unless noted otherwise.
Some abstracts came from the OpenAlex API (`https://api.openalex.org/works/https://doi.org/<doi>`). OpenAlex
stores abstracts as an inverted word index, so the text was rebuilt by word position. The words are the
publisher's, but small punctuation differences from the printed abstract are possible.

Page locators: "p. N" is a printed journal or proceedings page seen on the page itself. "PDF p. N" is the
position in the hosted file, used when printed numbers were not visible or differ from the published version.

---

### Knuth 1984 — Literate Programming
- Bibliographic record: Donald E. Knuth. 1984. "Literate Programming." *The Computer Journal* 27 (2): 97–111. DOI 10.1093/comjnl/27.2.97. Text read from http://www.literateprogramming.com/knuthweb.pdf
- Metadata check: CrossRef (title, journal, 27(2), pp. 97–111, issued 1984-02).
- Access level: full text, of a hosted typeset copy. Its running footer reads "submitted to THE COMPUTER JOURNAL", so it is a pre-publication typesetting. Its page numbers do not match the journal's, so locators are given by section and WEB-section number (§).
- Evidence:
  > "One line of processing is called weaving the web; it produces a document that describes the program clearly and that facilitates program maintenance. The other line of processing is called tangling the web; it produces a machine-executable program. The program and its documentation are both generated from the same source, so they are consistent with each other." — knuthweb.pdf, Sec. B
  > "The numbered paragraphs that follow are the actual output of a WEB file that has been “woven” into a document; a computer has also generated the indexes that appear at the program’s end." — Sec. C
  > "27. Index. Every identifier used in this program is shown here together with a list of the section numbers where that identifier appears. The section number is underlined if the identifier was defined in that section." — example program, §27
  > "[[An index like this is prepared automatically by the WEB software, and it is appended to the final section of the program. However, underlining of section numbers is not automatic; the user is supposed to mark identifiers at their point of definition in the WEB source file.]]" — §27
  > "Several other topics that appear in the documentation (e.g., ‘Bertrand’s postulate’) have also been indexed. [[Special instructions within a WEB source file can be used to insert essentially anything into the index.]]" — §27
  > "‘@^’ marks the beginning of an index entry to be set in roman type; … ‘@.’ marks the beginning of an index entry to be set in typewriter type" — Sec. D
  > "The ‘@!’ operation in the program text of Figure 2b governs the underlining of index entries." — Sec. D
- What this supports: This is the earliest primary source in this slice for an automatically generated index of every occurrence of every identifier, with section numbers, produced from the same source as the program. It also shows the split between machine-generated entries and entries the author marks by hand (definition points, and topical entries such as "Bertrand's postulate"). Knuth's consistency claim covers program and documentation generated from one source; it does not cover terminology.
- Caveats: The index covers program identifiers, not natural-language terms in prose. One-letter identifiers are indexed only at their definitions. The paper does not discuss keeping an index in sync between builds; the index is simply regenerated on each WEAVE run. Cite the journal pagination only after checking it against the published version.

### Deissenboeck & Pizka 2006 — Concise and consistent naming
- Bibliographic record: Florian Deissenboeck and Markus Pizka. 2006. "Concise and consistent naming." *Software Quality Journal* 14 (3): 261–282. DOI 10.1007/s11219-006-9219-1. Text read from https://itestra.com/media/publications/concise-consistent-naming-journal.pdf (the journal version; its header reads "Software Qual J (2006) 14:261–282").
- Metadata check: CrossRef (14(3), pp. 261–282, 2006-09).
- Access level: full text (journal version, with journal page numbers visible).
- Evidence:
  > "The enforcement of these rules is supported by a tool that incrementally builds and maintains a complete identifier dictionary while the system is being developed. The identifier dictionary explains the language used in the software system, aids in consistent naming, and supports programmers by proposing suitable names depending on the current context." — Abstract, p. 261
  > "It is indeed practically impossible to preserve globally consistent naming during long-term development efforts, maintenance, or evolution without additional tools." — p. 263
  > "Literature on software project management recommends the usage of a project glossary or dictionary that contains a description of all terms used in a project. This glossary serves as reference for project participants over the entire project life cycle." — p. 265
  > "Definition (Consistency). A naming system C, N, and R is consistent iff R ⊆ N × C is a bijective mapping." — p. 268
  > "Naturally, the manual creation and maintenance of an IDD for a large system must be considered unrealistic. Elaborated tool support is necessary." — p. 278
  > "developers should be able to look up a particular name in the source code, ask the tool for a list of all identifiers with this name, and navigate to selected occurrences." — p. 278
  > "This collector is coupled with Eclipse’s build process and collects all identifiers while the program is being compiled. … Analysis is done in an incremental fashion so only previously changed source code will be analyzed. Name descriptions are either kept in an XML file or a database for team-wide usage." — p. 279
  > "During the collection process identifier names may become annotated with warnings icons (fig. 8) indicating potential consistency problems." — p. 279
- What this supports: This is the closest analogue in this slice to a coded term register plus a synced occurrence index. The design has a dictionary of names with descriptions, an occurrence list per name, consistency warnings, and collection tied to the build, run incrementally. The paper also defines consistency formally (a bijection between names and concepts, so no synonyms and no homonyms) and argues that consistency cannot be kept by hand.
- Caveats: The setting is source-code identifiers in Java/Eclipse (2006), not prose documents. The paper makes the incremental, build-coupled collection a design and implementation claim; it does not evaluate it empirically. In the IDD, descriptions are entered by hand and only the identifiers are collected automatically.

### Lawrie, Feild & Binkley 2006 — Syntactic Identifier Conciseness and Consistency
- Bibliographic record: Dawn Lawrie, Henry Feild, and David Binkley. 2006. "Syntactic Identifier Conciseness and Consistency." In *Sixth IEEE International Workshop on Source Code Analysis and Manipulation (SCAM 2006)*, 139–148. IEEE. DOI 10.1109/SCAM.2006.31.
- Metadata check: CrossRef (pp. 139–148, 2006-09).
- Access level: abstract only (OpenAlex; Semantic Scholar reported the abstract "elided by the publisher").
- Evidence (https://api.openalex.org/works/https://doi.org/10.1109/SCAM.2006.31):
  > "Deissenbock and Pizka recently introduced rules for concise and consistent variable naming. One requirement of their approach is an expert provided mapping from identifiers to concepts. An approach for the concise and consistent naming of variables that does not require any additional information (e.g., a mapping) is presented."
  > "Using a pool of 48 million lines of code, experiments with the resulting syntactic rules for concise and consistent naming illustrate that violations of the syntactic pattern exist. Two case studies show that three quarters of the violations uncovered are "real"."
- What this supports: Consistency checking against a register needs someone to maintain the register (Deissenboeck & Pizka's expert-provided mapping). Lawrie et al. offer a syntactic approximation that needs no mapping; in their two case studies about three-quarters of the flagged violations were real.
- Caveats: Abstract only. Identifiers in code, not documentation terms.

### Arora, Sabetzadeh, Briand & Zimmer 2017 — Automated Extraction and Clustering of Requirements Glossary Terms
- Bibliographic record: Chetan Arora, Mehrdad Sabetzadeh, Lionel Briand, and Frank Zimmer. 2017. "Automated Extraction and Clustering of Requirements Glossary Terms." *IEEE Transactions on Software Engineering* 43 (10): 918–945. DOI 10.1109/TSE.2016.2635134. Text read from the author postprint: https://orbilu.uni.lu/bitstream/10993/28943/1/ASBZ_TSE_Manuscript_revised.pdf
- Metadata check: CrossRef (43(10), pp. 918–945, 2017-10). Semantic Scholar gave the abstract and the open-access link.
- Access level: full text (accepted manuscript; locators are manuscript PDF pages, not journal pages).
- Evidence:
  > "A glossary is an important part of any software requirements document. By making explicit the technical terms in a domain and providing definitions for them, a glossary helps mitigate imprecision and ambiguity." — Abstract, PDF p. 1
  > "In particular, glossaries … (1) improve the accuracy and understandability of requirements, (2) mitigate vagueness and ambiguity, (3) promote better communication between the stakeholders by establishing a common and consistent language" — PDF p. 1
  > "identifying potential consistency issues such as the use of variant phrases for referring to the same concept. An example of variant phrases in Fig. 1 is “GSI component status” and “status of GSI component”." — PDF p. 2
  > "the user may elect to eliminate from the requirements document either “GSI component status” or “status of GSI component” in order to make the terminology consistent." — PDF p. 10
  > "industrial requirements are prone to containing unintended variations, both due to the flexibility of natural language and also due to differences in terminology and style across different individuals and organizations." — PDF p. 13
  > "the experts either agreed or strongly agreed in 61.2% (41/67) of the cases that the clusters where helpful for identifying variant terms." — PDF p. 25
- What this supports: A glossary's function includes "a common and consistent language". Variant phrasings of one concept are a real consistency problem in industrial requirements, and clustering related terms helps surface them (61.2% expert agreement).
- Caveats: Three industrial case studies from two sectors. The paper is about building a glossary, not about enforcing it or indexing term occurrences once it exists.

### Dwarakanath, Ramnani & Sengupta 2013 — Automatic extraction of glossary terms from natural language requirements
- Bibliographic record: Anurag Dwarakanath, Roshni R. Ramnani, and Shubhashis Sengupta. 2013. "Automatic extraction of glossary terms from natural language requirements." In *2013 21st IEEE International Requirements Engineering Conference (RE)*, 314–319. IEEE. DOI 10.1109/RE.2013.6636736.
- Metadata check: CrossRef (pp. 314–319, 2013-07). Author given names are from CrossRef only.
- Access level: abstract only (OpenAlex).
- Evidence (https://api.openalex.org/works/https://doi.org/10.1109/RE.2013.6636736):
  > "We present a method for the automatic extraction of glossary terms from unconstrained natural language requirements."
  > "This requires solving co-ordination ambiguity and adjectival modifier ambiguity."
- What this supports: Glossary term extraction from requirements had been automated as a research problem by 2013.
- Caveats: Abstract only. Says nothing about consistency enforcement or maintenance.

### Gemkow, Conzelmann, Hartig & Vogelsang 2018 — Automatic Glossary Term Extraction from Large-Scale Requirements Specifications
- Bibliographic record: Tim Gemkow, Miro Conzelmann, Kerstin Hartig, and Andreas Vogelsang. 2018. "Automatic Glossary Term Extraction from Large-Scale Requirements Specifications." In *2018 IEEE 26th International Requirements Engineering Conference (RE)*, 412–417. IEEE. DOI 10.1109/RE.2018.00052. Text read from the TU Berlin postprint: https://depositonce.tu-berlin.de/bitstreams/2eb48b4f-45df-41d2-9f12-71dc18dc15c2/download (repository DOI 10.14279/depositonce-7113). No arXiv copy was found.
- Metadata check: CrossRef (pp. 412–417, 2018-08).
- Access level: full text (postprint; PDF p. 1 is a repository cover sheet, the paper starts at PDF p. 2).
- Evidence:
  > "Glossaries serve to ensure that all stakeholders have a common understanding of key terms. To this end, it is necessary to have a set of unambiguous terms that clearly define the key concepts used in the requirements to minimize the risk of misinterpretation" — Sec. I, PDF p. 2
  > "Best practice in RE holds that a glossary should be developed continuously during the process of requirements elicitation [2]. However, in many real-world projects, this effort is not expended initially" — Sec. I, PDF p. 2
  > "Conceptually, an important task of any glossary is to define the canonical terms used to refer to a given concept, and to regulate both the use of synonyms (by clarifying the preferred terms) and homonyms (by clearly disambiguating different meanings and, typically, recommending alternative terms that are clearly distinct)." — PDF p. 7
  > "However, our approach can only reduce morphological variance through lemmatization. Any form of semantic synonyms are ignored" — PDF p. 7
- What this supports: The authors say a glossary should fix canonical terms and regulate synonyms and homonyms. They also say best practice is to maintain a glossary continuously, which real projects often do not do.
- Caveats: "Best practice" is attributed to their reference [2], which was not checked here. Their extraction method does not detect semantic synonyms.

### Aghajani et al. 2019 — Software Documentation Issues Unveiled
- Bibliographic record: Emad Aghajani, Csaba Nagy, Olga Lucero Vega-Márquez, Mario Linares-Vásquez, Laura Moreno, Gabriele Bavota, and Michele Lanza. 2019. "Software Documentation Issues Unveiled." In *2019 IEEE/ACM 41st International Conference on Software Engineering (ICSE)*, 1199–1210. IEEE. DOI 10.1109/ICSE.2019.00122. Text read from the author copy: https://emadpres.github.io/pdfs/icse2019.pdf
- Metadata check: CrossRef (pp. 1199–1210, 2019-05).
- Access level: full text (author copy; locators are PDF pages).
- Evidence:
  > "we built a comprehensive taxonomy consisting of 162 types of documentation issues linked to (i) the information it contains, (ii) how the information is presented, (iii) the documentation process and (iv) documentation tool support." — PDF p. 1
  > "Up-to-dateness (190). A document is outdated when it is not in sync with other parts of a system. Up-to-dateness differs from “Correctness” and “Completeness” in that the information was correct and complete before a change was introduced." — PDF p. 6
  > "One way of doing so is to use a contingency matrix, where rows represent code components and columns represent existing documentation artifacts. … This matrix can then be queried to check for inconsistencies." — PDF p. 6
  > "We also observed intra-documentation consistency issues (e.g., “inconsistent title between sidebar and article” [92])" — PDF p. 7
  > Figure 1 (taxonomy, PDF p. 5) contains a leaf labelled "Inconsistent terminology" (read from the figure's text layer; it sits beside "Inconsistent styling").
- What this supports: Outdatedness ("not in sync") is a major category of real documentation issues, with 190 instances. The authors suggest a queryable matrix linking code components to the documents that cover them, an analogue of an occurrence index used for consistency checks. "Inconsistent terminology" is a named issue type in the taxonomy.
- Caveats: Based on 878 artifacts from mailing lists, Stack Overflow, issues and PRs, so it describes how often issues are discussed, not how often they occur. The figure label was read from extracted text; the number of instances for "Inconsistent terminology" was not seen.

### Aghajani et al. 2020 — Software Documentation: The Practitioners' Perspective
- Bibliographic record: Emad Aghajani, Csaba Nagy, Mario Linares-Vásquez, Laura Moreno, Gabriele Bavota, Michele Lanza, and David C. Shepherd. 2020. "Software Documentation: The Practitioners' Perspective." In *Proceedings of the ACM/IEEE 42nd International Conference on Software Engineering (ICSE '20)*, 590–601. ACM. DOI 10.1145/3377811.3380405.
- Metadata check: CrossRef (pp. 590–601, issued 2020-06-27; CrossRef title field is just "Software documentation").
- Access level: full text of the paper as **reproduced as Chapter 6 of Aghajani's PhD thesis**, *Software Documentation: Automation and Challenges* (Università della Svizzera italiana, accepted 18 June 2020), https://folia.unifr.ch/documents/319169/files/2020INFO014.pdf. The thesis lists the chapter as the ICSE 2020 paper. The publisher PDF and the USI copy (inf.usi.ch) returned HTTP 403. Wording may differ slightly from the published proceedings. Locators are thesis printed pages.
- Evidence:
  > "We present two surveys performed with 146 practitioners to investigate (i) the documentation issues they perceive as more relevant together with solutions they apply when these issues arise; and (ii) the types of documentation considered as important in different tasks." — thesis p. 93
  > "Inconsistency between code and documentation was also perceived as an important issue by practitioners (59% of them) and is one of the top recurring issues they face." — thesis p. 103
  > "The most common up-to-dateness documentation issues involve code comments, which might not reflect changes implemented in the code [WNBL19]." — thesis p. 103
  > "Regarding Documentation tools issues, the lack of/poor automatization was the only issue frequently faced by practitioners. Smarter tools, better IDE integration, and automated generation of documentation were the common requests in this context." — thesis p. 106
- What this supports: 59% of practitioners rated code–documentation inconsistency as important, and it is among the issues they meet most often. They ask for more automation.
- Caveats: 125 of the 146 respondents were from one company (ABB), so the results may not generalise. Cite the ICSE DOI, but say the text was read in the thesis reproduction. "Inconsistency" here means code versus documentation, not terminology.

### Wen, Nagy, Bavota & Lanza 2019 — A Large-Scale Empirical Study on Code-Comment Inconsistencies
- Bibliographic record: Fengcai Wen, Csaba Nagy, Gabriele Bavota, and Michele Lanza. 2019. "A Large-Scale Empirical Study on Code-Comment Inconsistencies." In *2019 IEEE/ACM 27th International Conference on Program Comprehension (ICPC)*, 53–64. IEEE. DOI 10.1109/ICPC.2019.00019.
- Metadata check: CrossRef (pp. 53–64, 2019-05).
- Access level: abstract only (Semantic Scholar API). The author PDF at inf.usi.ch returned a Cloudflare challenge or HTTP 403.
- Evidence (https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/ICPC.2019.00019):
  > "Keeping comments up-to-date during code change activities requires substantial time and attention. For this reason, researchers have proposed methods to detect code-comment inconsistencies (i.e., comments that are not kept in sync with the code they document)"
  > "The study has been performed by mining 1.3 Billion AST-level changes from the complete history of 1,500 systems."
  > "Our analysis discloses the extent to which different types of code changes (e.g., change of selection statements) trigger updates to the related comments, identifying cases in which code-comment inconsistencies are more likely to be introduced."
- What this supports: Keeping derived or coupled text in sync with its source costs effort and often fails. Code–comment drift was studied at scale (1,500 systems).
- Caveats: Abstract only; no specific rates are recorded here. The subject is comments, not glossaries.

### Tan, Yuan, Krishna & Zhou 2007 — /*iComment: Bugs or Bad Comments?*/
- Bibliographic record: Lin Tan, Ding Yuan, Gopal Krishna, and Yuanyuan Zhou. 2007. "/*iComment: Bugs or Bad Comments?*/." In *Proceedings of the 21st ACM SIGOPS Symposium on Operating Systems Principles (SOSP '07)*, 145–158. ACM. DOI 10.1145/1294261.1294276. Text read from https://www.cs.purdue.edu/homes/lintan/publications/icomment_sosp07.pdf
- Metadata check: CrossRef (pp. 145–158, 2007-10-14; CrossRef title "/*icomment").
- Access level: full text (14-page author copy; quotes from the abstract, PDF p. 1).
- Evidence:
  > "As software evolves, they can easily grow out-of-sync, indicating two problems: (1) bugs - the source code does not follow the assumptions and requirements specified by correct program comments; (2) bad comments - comments that are inconsistent with correct code, which can confuse and mislead programmers to introduce bugs in subsequent versions." — PDF p. 1
  > "iComment automatically extracts 1832 rules from comments with 90.8-100% accuracy and detects 60 comment-code inconsistencies, 33 new bugs and 27 bad comments, in the latest versions of the four programs." — PDF p. 1
- What this supports: Natural-language text that has drifted out of sync with code is linked to real defects: 33 new bugs across Linux, Mozilla, Wine and Apache.
- Caveats: Concerns comments against code, not term registers. Evidence for 2007 C/C++ systems.

### Arnaoudova, Di Penta & Antoniol 2016 — Linguistic antipatterns: what they are and how developers perceive them
- Bibliographic record: Venera Arnaoudova, Massimiliano Di Penta, and Giuliano Antoniol. 2016. "Linguistic antipatterns: what they are and how developers perceive them." *Empirical Software Engineering* 21 (1): 104–158. DOI 10.1007/s10664-014-9350-8. CrossRef "issued" is 2015-01-29 (online first); the volume is 2016.
- Metadata check: CrossRef.
- Access level: **none (UNVERIFIED-CONTENT)**. CrossRef, Semantic Scholar and OpenAlex have no abstract. The Springer page redirects to a login page, the Polytechnique Montréal course copy needs a Moodle login, and the institutional repository holds no file.
- Evidence: none recorded.
- What this supports: nothing, until the text is read.
- Caveats: A search-engine summary described the content, but it was not read first-hand, so nothing is recorded.

### Hilton, Tunnell, Huang, Marinov & Dig 2016 — Usage, costs, and benefits of continuous integration in open-source projects
- Bibliographic record: Michael Hilton, Timothy Tunnell, Kai Huang, Darko Marinov, and Danny Dig. 2016. "Usage, Costs, and Benefits of Continuous Integration in Open-Source Projects." In *Proceedings of the 31st IEEE/ACM International Conference on Automated Software Engineering (ASE 2016)*, 426–437. ACM. DOI 10.1145/2970276.2970358. Text read from a course-hosted copy: https://cs.uwaterloo.ca/~m2nagapp/courses/CS846/1171/papers/hilton_ase16.pdf
- Metadata check: CrossRef (pp. 426–437, 2016-08-25).
- Access level: full text (locators are PDF pages).
- Evidence:
  > "Continuous integration (CI) systems automate the compilation, building, and testing of software." — Abstract, PDF p. 1
  > "We found that 40% of all the projects in our breadth corpus use CI." — PDF p. 3
  > Table 6: "CI makes us less worried about breaking our builds 87.71 / CI helps us catch bugs earlier 79.61" (percent of survey respondents) — PDF p. 8
  > Respondent quote: "Acts like a watchdog. You may not run tests, or be careful with merges, but the CI will. :)" — PDF p. 7
  > "projects that use CI: (i) release twice as often, (ii) accept pull requests faster, and (iii) have developers who are less worried about breaking the build. Therefore, it should come as no surprise that 70% of the most popular projects on GitHub heavily use CI." — PDF p. 10
- What this supports: CI was widely adopted and is valued as an automatic check that runs whether or not individual developers remember to run it (the "watchdog" quote). That is the role CI plays when it checks that a derived index is in sync.
- Caveats: Open-source GitHub projects (data about 2015–16; 34,544 projects, 1,529,291 builds, 442 survey respondents). The study is about compiling and testing, not documentation or terminology checks. The release-rate findings are correlational.

### Mokhov, Mitchell & Peyton Jones 2018 — Build systems à la carte
- Bibliographic record: Andrey Mokhov, Neil Mitchell, and Simon Peyton Jones. 2018. "Build Systems à la Carte." *Proceedings of the ACM on Programming Languages* 2 (ICFP): Article 79, 29 pages. DOI 10.1145/3236774. Text read from https://www.microsoft.com/en-us/research/uploads/prod/2018/03/build-systems.pdf (the published version, carrying "Proc. ACM Program. Lang., Vol. 2, No. ICFP, Article 79").
- Metadata check: CrossRef (vol. 2, issue ICFP, pp. 1–29, 2018-07-30; abstract present and matching).
- Access level: full text (article page numbers 79:N visible).
- Evidence:
  > "Definition 2.1 (Minimality). A build system is minimal if it executes tasks at most once per build and only if they transitively depend on inputs that changed since the previous build." — p. 79:4
  > "To achieve minimality Make relies on two main ideas: (i) it uses file modification times to detect which files changed, and (ii) it constructs a task dependency graph" — p. 79:4
  > "Technically, you can fool Make by altering the modification time of a file without changing its content, e.g. by using the command touch. Make is therefore minimal only under the assumption that you do not do that." — footnote 5, p. 79:4
  > "Shake also supports the early cutoff optimisation. When it executes a task and the result is unchanged from the previous build, it is unnecessary to execute the dependent tasks … Make and Excel do not, whereas Shake and Bazel (introduced below) do." — p. 79:5
  > "The idea of a dirty bit is to have one piece of persistent information per key, saying whether the key is dirty or clean." — Sec. 4.2.1, p. 79:14
  > "Note that Make requires that file timestamps only go forward in time, which can be violated by backup software." — p. 79:14
  > "An alternative way to determine if a key is dirty is to record the values/hashes of dependencies used last time, and if something has changed, the key is dirty and must be rebuilt — in essence a trace which we can use to verify existing values." — Sec. 4.2.2, p. 79:14
- What this supports: This gives the vocabulary for deciding when a derived artifact such as an occurrence index is stale. Timestamps and dirty bits can be fooled; verifying traces of content hashes record what was used last time. Minimality means rebuilding only what depends on changed inputs, and early cutoff stops propagation when a rebuilt output is unchanged.
- Caveats: A formal and design study of build systems in general. It does not discuss documentation indexes or CI. Any application to term indexes is an analogy for the deliverable to argue.

### Butler, Wermelinger, Yu & Sharp 2010 — Exploring the Influence of Identifier Names on Code Quality: An Empirical Study
- Bibliographic record: Simon Butler, Michel Wermelinger, Yijun Yu, and Helen Sharp. 2010. "Exploring the Influence of Identifier Names on Code Quality: An Empirical Study." In *2010 14th European Conference on Software Maintenance and Reengineering (CSMR)*, 156–165. IEEE. DOI 10.1109/CSMR.2010.27.
- Metadata check: CrossRef (pp. 156–165, 2010-03).
- Access level: abstract only (OpenAlex). The CORE copies returned HTML or HTTP 403.
- Evidence (https://api.openalex.org/works/https://doi.org/10.1109/CSMR.2010.27):
  > "We found that flawed identifiers in Java classes were associated with source code found to be of low quality by static analysis. This paper extends that work in three directions. First, we show that the association also holds at the finer granularity level of Java methods."
- What this supports: Empirical evidence of an association between naming flaws and lower code quality, as judged by static analysis.
- Caveats: Abstract only. The association is correlational. "Flawed identifiers" covers many naming-style flaws, not only synonym or homonym inconsistency, and the abstract does not say which flaws.

### Feitelson et al. 2022 — How Developers Choose Names (added; relevant to why a register is needed)
- Bibliographic record: Dror G. Feitelson, Ayelet Mizrahi, Nofar Noy, Aviad Ben Shabat, Or Eliyahu, and Roy Sheffer. 2022. "How Developers Choose Names." *IEEE Transactions on Software Engineering* 48 (1): 37–52. DOI 10.1109/TSE.2020.2976920. Author given names are not confirmed (CrossRef gave family names only).
- Metadata check: CrossRef (48(1), pp. 37–52, issued 2022-01). An open copy was listed by OpenAlex (arXiv 2103.07487) but not read.
- Access level: abstract only (OpenAlex).
- Evidence (https://api.openalex.org/works?search=… , record for doi 10.1109/tse.2020.2976920):
  > "The first experiment shows that the probability that two developers would select the same name is low: in the 47 instances in our experiments the median probability was only 6.9 percent. At the same time, given that a specific name is chosen, it is usually understood by the majority of developers."
- What this supports: Left to themselves, developers rarely choose the same name for the same thing (median 6.9%), an empirical reason why an explicit shared register of preferred terms is needed.
- Caveats: Abstract only; experimental scenarios with 334 subjects. Name choice, not consistency over time.

### Evans 2015 — Domain-Driven Design Reference (ubiquitous language)
- Bibliographic record: Eric Evans. 2015. *Domain-Driven Design Reference: Definitions and Pattern Summaries.* Domain Language, Inc. Licensed CC BY 4.0. https://domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf. Its contents page marks some entries as "New term introduced since the 2004 book", i.e. Evans, *Domain-Driven Design: Tackling Complexity in the Heart of Software* (Addison-Wesley). **The book itself was not read**; cite the Reference.
- Metadata check: none available (no DOI). Title, author, publisher and year were read from the PDF title page.
- Access level: full text (printed page numbers visible).
- Evidence:
  > "ubiquitous language — A language structured around the domain model and used by all team members within a bounded context to connect all the activities of the team with the software." — Definitions, PDF p. 6
  > "Explicitly define the context within which a model applies. … Apply Continuous Integration to keep model concepts and terms strictly consistent within these bounds" — Bounded Context, p. 2
  > "The terminology of day-to-day discussions is disconnected from the terminology embedded in the code" — Ubiquitous Language, p. 3
  > "developers should watch for ambiguity or inconsistency that will trip up design." — p. 3
  > "Commit the team to exercising that language relentlessly in all communication within the team and in the code. … Recognize that a change in the language is a change to the model." — p. 4
  > "Institute a process of merging all code and other implementation artifacts frequently, with automated tests to flag fragmentation quickly. Relentlessly exercise the ubiquitous language" — Continuous Integration, p. 5
- What this supports: A practitioner source that explicitly ties continuous integration to keeping "model concepts and terms strictly consistent", and treats one shared vocabulary across talk, documents and code as a design principle.
- Caveats: A practitioner pattern summary, not peer-reviewed. In Evans, "Continuous Integration" includes frequent merging and human practice ("exercise the language"); he does not describe automated terminology checks. Do not date the quotes to 2003/2004 without reading the book.

### Zhong & Su 2013 — Detecting API documentation errors
- Bibliographic record: Hao Zhong and Zhendong Su. 2013. "Detecting API documentation errors." In *Proceedings of the 2013 ACM SIGPLAN International Conference on Object Oriented Programming Systems Languages & Applications (OOPSLA '13)*, 803–816. ACM. DOI 10.1145/2509136.2509523. Also *ACM SIGPLAN Notices* 48 (10): 803–816, DOI 10.1145/2544173.2509523.
- Metadata check: CrossRef (both DOIs; the abstract came from the SIGPLAN Notices record).
- Access level: abstract only (CrossRef).
- Evidence (https://api.crossref.org/works/10.1145/2544173.2509523):
  > "These API documents contain valuable information, but may also mislead programmers as they may contain errors (e.g., broken code names and obsolete code samples). Although most API documents are actively maintained and updated, studies show that many new and latent errors do exist."
  > "We formulate a class of inconsistencies to indicate potential documentation errors, and combine NL and code analysis techniques to detect and report such inconsistencies."
  > "DOCREF has detected more than 1,000 new documentation errors, which we have reported to the authors."
- What this supports: Mechanically cross-checking names that appear in prose against the names that actually exist finds documentation errors at scale (over 1,000 in five libraries).
- Caveats: Abstract only. API names, not glossary terms.

### Lee, Wu, Cheung & Kang 2021 — Automatic Detection and Update Suggestion for Outdated API Names in Documentation
- Bibliographic record: Seonah Lee, Rongxin Wu, Shing-Chi Cheung, and Sungwon Kang. 2021. "Automatic Detection and Update Suggestion for Outdated API Names in Documentation." *IEEE Transactions on Software Engineering* 47 (4): 653–675. DOI 10.1109/TSE.2019.2901459 (published online 2019). Text read from https://s-cube-xmu.github.io/uploads/Automatic%20Detection%20and%20Update%20Suggestion%20for%20Outdated%20API%20Names%20in%20Documentation.pdf
- Metadata check: CrossRef (47(4), pp. 653–675, issued 2021-04).
- Access level: full text (23-page copy; quotes from PDF p. 1).
- Evidence:
  > "However, API documentation is commonly outdated because nearly all of the associated updates are performed manually." — Abstract, PDF p. 1
  > "Our insight is that API updates in documentation can be derived from API implementation changes between code revisions." — Abstract
  > "when we checked the updates suggested by FreshDoc against the developers’ manual updates in the revised documentation, FreshDoc detected 82 percent of the outdated names. When we reported 40 outdated API names found by FreshDoc via issue tracking systems, developers accepted 75 percent of the suggestions." — Abstract
- What this supports: The authors attribute outdatedness to manual updating, and show that change-driven automatic detection of stale names works in practice.
- Caveats: Java API documentation in four open-source projects.

### Tan, Wagner & Treude 2024 — Detecting outdated code element references in software repository documentation
- Bibliographic record: Wen Siang Tan, Markus Wagner, and Christoph Treude. 2024. "Detecting outdated code element references in software repository documentation." *Empirical Software Engineering* 29 (1): article 5. DOI 10.1007/s10664-023-10397-6 (CrossRef issued 2023-11-21). Text read from the arXiv preprint: https://arxiv.org/pdf/2212.01479 (v1, 2 Dec 2022).
- Metadata check: CrossRef bibliographic query matched the title, authors and journal.
- Access level: full text of the **preprint** (wording may differ from the published version).
- Evidence:
  > "We posit that one possible reason why documentation becomes out of sync so easily is that developers are unaware of when their source code modifications render the documentation obsolete." — Abstract, PDF p. 1
  > "we analysed over 3,000 GitHub projects and found that most projects contain at least one outdated code element reference at some point in their history." — Abstract
  > "A possible direction for future work is to create a workflow that automatically clones the repository, runs the analysis, and outputs the potentially outdated references. Using a tool such as GitHub Action to automate the workflow simplifies the process considerably as it allows developers to configure their repository to automatically scan for outdated references whenever there is a new commit or pull request." — PDF p. 23
- What this supports: References that live in documents (an occurrence relation) commonly go stale. The authors name per-commit and per-PR CI automation as the way to keep them in sync.
- Caveats: Preprint text. The CI workflow is proposed future work, not something they evaluated.

### Antoniol, Canfora, Casazza, De Lucia & Merlo 2002 — Recovering traceability links between code and documentation
- Bibliographic record: Giuliano Antoniol, Gerardo Canfora, Gerardo Casazza, Andrea De Lucia, and Ettore Merlo. 2002. "Recovering traceability links between code and documentation." *IEEE Transactions on Software Engineering* 28 (10): 970–983. DOI 10.1109/TSE.2002.1041053.
- Metadata check: CrossRef (28(10), pp. 970–983, 2002-10).
- Access level: abstract only (OpenAlex).
- Evidence (https://api.openalex.org/works/https://doi.org/10.1109/TSE.2002.1041053):
  > "We propose a method based on information retrieval to recover traceability links between source code and free text documents. A premise of our work is that programmers use meaningful names for program items"
  > "the analysis of these mnemonics can help to associate high-level concepts with program concepts and vice-versa."
- What this supports: Links between documents and code can be recovered from shared vocabulary, which presupposes consistent naming across them.
- Caveats: Abstract only. An information-retrieval (probabilistic and vector-space) method, not an exact term index.

### Git project documentation — hooks (client-side bypass vs. server-side enforcement)
- Bibliographic records:
  - Git project. "githooks — Hooks used by Git." Git reference documentation. https://git-scm.com/docs/githooks (retrieved 2026-11-16; current online version).
  - Scott Chacon and Ben Straub. 2014. *Pro Git.* 2nd ed. Apress. Section 8.3, "Customizing Git — Git Hooks." https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks. Authors, publisher and edition were read from https://git-scm.com/book/en/v2.
- Metadata check: none (no DOI). Quotes checked against the raw HTML with curl, not only through WebFetch.
- Access level: full text.
- Evidence:
  > "By default the hooks directory is $GIT_DIR/hooks, but that can be changed via the core.hooksPath configuration variable" — githooks, DESCRIPTION
  > [pre-commit] "This hook is invoked by git-commit[1], and can be bypassed with the --no-verify option." — githooks, pre-commit
  > [pre-receive] "If the hook exits with non-zero status, none of the refs will be updated." — githooks, pre-receive
  > "It’s important to note that client-side hooks are not copied when you clone a repository. If your intent with these scripts is to enforce a policy, you’ll probably want to do that on the server side" — Pro Git §8.3
  > "you can use a couple of important server-side hooks as a system administrator to enforce nearly any kind of policy for your project." — Pro Git §8.3
- What this supports: Authoritative statements that client-side hooks are optional (they can be skipped with `--no-verify`), are not cloned with the repository, and sit in a per-clone directory by default. Enforcing a policy belongs on the server side. A synced index maintained only by a pre-commit hook is therefore not guaranteed; a server-side or CI check is the enforcement point.
- Caveats: Tool documentation and a practitioner book, not empirical research. The githooks page is unversioned live documentation. `core.hooksPath` lets a project point hooks at a tracked directory, but each clone must still set it. No peer-reviewed study of hook reliability or bypass rates was found (see below).

---

## Not verified / not found

- **Arnaoudova, Di Penta & Antoniol 2016**, linguistic antipatterns (10.1007/s10664-014-9350-8): metadata verified, content UNVERIFIED (no abstract in any API; publisher and course copies need a login).
- **Wen et al. 2019** and **Lawrie et al. 2006**, **Dwarakanath et al. 2013**, **Butler et al. 2010**, **Zhong & Su 2013**, **Antoniol et al. 2002**, **Feitelson et al. 2022**: abstract only. Full-text claims (rates, tables, page numbers) are not recorded.
- **Aghajani et al. 2020**: the publisher and USI PDFs were blocked (HTTP 403). Read in the thesis reproduction only.
- **Evans 2003/2004 book**: not read. The 2015 DDD Reference was used instead.
- **Peer-reviewed study of git pre-commit hook reliability, bypass rates or adoption vs. server-side CI**: none found in two searches; results were blogs and vendor articles only. Only Git's own documentation and *Pro Git* are recorded.
- **Empirical studies directly measuring harm from synonym/homonym terminology in requirements** (e.g. Berry or Kamsties on ambiguity): not searched to completion and none verified. The nearest verified evidence is Deissenboeck & Pizka's cited claim on homonyms slowing readers (p. 265, attributed to Anderson 1995, not checked), Butler et al. 2010 (abstract), and Arora et al. 2017 on unintended variations in industrial requirements.
- **Semantic Scholar batch API** returned HTTP 429 (rate limit) at first; abstracts were then taken one at a time or from OpenAlex.
