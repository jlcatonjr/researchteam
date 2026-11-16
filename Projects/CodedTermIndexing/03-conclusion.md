# Conclusion and Executive Summary: Coded Term Definitions and Synced Term-Occurrence Indexing

Prepared by: @conclusion-expert  
Date: November 16, 2026  
Citation style: Chicago Author-Date

## Executive Summary

From the sources, this project infers three conditions for making a project's terminology checkable: the terms are defined
in a register a program can read, every occurrence of each registered form is indexed, and the index is
regenerated automatically and can be tested for staleness. The literature treats the first two at length,
largely in separate traditions. For the third it offers precedents and analogies from software
engineering and legal informatics.

Four conclusions follow, each with limits. The direct evidence on an unchecked register is one
second-hand case of a controlled language discontinued, among other reasons, because its guidelines were
not enforceable (Kuhn 2014). The nearest scholarly precedents for the design are an identifier
dictionary for source code and a specification for legal concept records (Deissenboeck and Pizka 2006;
Winkels and Hoekstra 2012). Among the documentation tools examined, none joins definitions, a stored
index of every plain-prose occurrence across a set of documents, and a freshness check. And no single
trigger is both immediate and unavoidable, so this project infers that the index should be rebuilt by
hooks and verified by a later check that compares content hashes.

Several sources were read only as abstracts or publisher descriptions, the tool survey rests on
documentation and was not exhaustive, and no study was found that tests whether checking a register
improves consistency.

## Main Conclusions

1. **The two halves have largely separate histories.** This project reads the occurrence index as a
   descendant of the concordance, which gathered "all the uses of a given word" in one place (Rouse and
   Rouse 1974, 5). Luhn (1960) later proposed machine-generated indexes that could be "kept up-to-date";
   the link between the two is this project's inference. It reads the register as a descendant of
   vocabulary control, where each concept is "represented by a single preferred term" (NISO 2010, sec.
   5.3.2), and which addresses occurrences in running text only at the margin (Hodge 2000, 12).

2. **A register should not be expected to keep usage consistent unless usage is checked against it.**
   This is a judgement, not a finding. It rests on one controlled language that was discontinued, among
   other reasons, because its guidelines were not enforceable (Kuhn 2014, reporting an earlier source),
   and on analogies from documentation drift in software. The measurement studies show that consistency
   can be scored term by term (Gašpar et al. 2022; Marić 2024). They do not show what a check changes.

3. **Research practice has a close analogue: the codebook.** Its record of label, definition, exclusions
   and examples, and its use to keep several analysts consistent, resemble a project's term register
   (Roberts et al. 2019). The analogy is this project's. The codebook governs how analysts label data,
   not how authors use terms.

4. **The closest precedents come from software engineering and legal informatics.** An identifier
   dictionary is designed to list the occurrences of each name, warn of inconsistency and update
   incrementally with the build, in a design its authors do not evaluate empirically (Deissenboeck and
   Pizka 2006, 278-79). A specification for legal concept records asks for each definition with
   "references to all occurrences," and the system built around it detects change with a hash per article
   (Winkels and Hoekstra 2012, sec. 2, sec. 3.1). Knuth (1984) is the precedent for generating an index from the text's own
   source while leaving the marking of definition points to the author.

5. **The documentation tools examined leave a gap.** The glossary systems of the toolchains examined
   index or check only the uses an author marks. The prose linters and the prose-matching plugins
   examined detect unmarked forms, and none describes a stored index of them. This describes the tools
   examined and may not hold for others.

6. **Freshness needs a test that is independent of the trigger.** Git hooks can be bypassed and are
   local (Git 2026; Chacon and Straub 2014, sec. 8.3), and agent-session hooks run only while a session
   runs (Anthropic 2026). By analogy with build-system traces and with the hash test used for
   legislation, a recorded content hash for the register and for each document lets any later check
   establish whether the index is current (Mokhov et al. 2018, 79:14; Winkels and Hoekstra 2012, sec.
   3.1).

7. **A matching index has a ceiling.** It records where a form appears, not whether it is used in the
   defined sense. Variation is sometimes deliberate (Resi 2025, PDF p. 2), and a well-formed register
   does not make a concept good (Gerring 1999).

## Recommendation

Researchteam should give every project a term register of coded definitions, generate an occurrence index
from the project's documents by matching, record content hashes in the index, rebuild it from hooks, and
verify its freshness in the repository's validation and, where the repository has it, in continuous
integration. A discouraged form used in prose outside a quotation should fail the check unless the
register records an exception with a reason. That last point is a design choice the evidence does not
settle. The design implications are set out in section 7 of the analysis.

## Open Questions

- Does a checked register measurably improve terminological consistency in research writing? No study
  was found that applies a consistency index to monolingual technical documentation, and research writing
  was not separately searched.
- How often is a discouraged variant in a research report legitimate, as a quotation or a reported
  usage, as against a slip? The rate decides whether a blocking check with recorded exceptions is
  workable.
- How should a register handle a term whose meaning differs by period or school? The historical-context
  protocol requires such differences to be kept visible, and a single preferred definition may hide them.

## References

Anthropic. 2026. "Hooks Reference." Claude Code documentation. Accessed November 16, 2026. https://code.claude.com/docs/en/hooks

Chacon, Scott, and Ben Straub. 2014. Pro Git. 2nd ed. Apress. https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks

Deissenboeck, Florian, and Markus Pizka. 2006. "Concise and Consistent Naming." Software Quality Journal 14 (3): 261-82. https://doi.org/10.1007/s11219-006-9219-1

Gašpar, Angelina, Sanja Seljan, and Vlasta Kučiš. 2022. "Measuring Terminology Consistency in Translated Corpora: Implementation of the Herfindahl-Hirshman Index." Information 13 (2): 43. https://doi.org/10.3390/info13020043

Gerring, John. 1999. "What Makes a Concept Good? A Criterial Framework for Understanding Concept Formation in the Social Sciences." Polity 31 (3): 357-93. https://doi.org/10.2307/3235246

Git. 2026. "githooks: Hooks Used by Git." Git reference documentation. Accessed November 16, 2026. https://git-scm.com/docs/githooks

Hodge, Gail. 2000. Systems of Knowledge Organization for Digital Libraries: Beyond Traditional Authority Files. Washington, DC: Digital Library Federation and Council on Library and Information Resources. https://www.clir.org/pubs/reports/pub91/

Knuth, Donald E. 1984. "Literate Programming." The Computer Journal 27 (2): 97-111. https://doi.org/10.1093/comjnl/27.2.97

Kuhn, Tobias. 2014. "A Survey and Classification of Controlled Natural Languages." Computational Linguistics 40 (1): 121-70. https://doi.org/10.1162/COLI_a_00168

Luhn, H. P. 1960. "Key Word-in-Context Index for Technical Literature (KWIC Index)." American Documentation 11 (4): 288-95. https://doi.org/10.1002/asi.5090110403

Marić, Laura. 2024. "Terminological Consistency in Croatian Translations of EU Legislation: A Corpus-Based Study." Hieronymus 11: 58-87. https://doi.org/10.17234/Hieronymus.11.3

Mokhov, Andrey, Neil Mitchell, and Simon Peyton Jones. 2018. "Build Systems à la Carte." Proceedings of the ACM on Programming Languages 2 (ICFP): 79:1-79:29. https://doi.org/10.1145/3236774

NISO (National Information Standards Organization). 2010. Guidelines for the Construction, Format, and Management of Monolingual Controlled Vocabularies. ANSI/NISO Z39.19-2005 (R2010). https://www.niso.org/publications/ansiniso-z3919-2005-r2010

Resi, Rossella. 2025. "Representing Terminological Chains for Well-Formed Neologisms." In Proceedings of the 1st International Workshop on Terminological Neologism Management (NeoTerm 2025). CEUR Workshop Proceedings 3972. https://ceur-ws.org/Vol-3972/paper3.pdf

Roberts, Kate, Anthony Dowell, and Jing-Bao Nie. 2019. "Attempting Rigour and Replicability in Thematic Analysis of Qualitative Research Data; A Case Study of Codebook Development." BMC Medical Research Methodology 19: 66. https://doi.org/10.1186/s12874-019-0707-y

Rouse, Richard H., and Mary A. Rouse. 1974. "The Verbal Concordance to the Scriptures." Archivum Fratrum Praedicatorum 44: 5-30. https://heyjoe.fbk.eu/index.php/afp/article/view/12081

Winkels, Radboud, and Rinke Hoekstra. 2012. "Automatic Extraction of Legal Concepts and Definitions." In Legal Knowledge and Information Systems: JURIX 2012, Frontiers in Artificial Intelligence and Applications 250, 157ff. Amsterdam: IOS Press. https://doi.org/10.3233/978-1-61499-167-0-157
