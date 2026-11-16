# Adversarial and Conflict Audit: CodedTermIndexing

Date: November 16, 2026  
Protocol: `docs/citation-claim-audit-protocol.md` (2-fold audit, two rounds)  
Audits applied: @reference-manager, @technical-validator, @adversarial, @conflict-auditor  
Scope: every factual claim and every citation in

- 00-research-plan.md
- 01-literature-review.md
- 02-analysis.md
- 03-conclusion.md
- interpretation/interpretive-map.md
- references/bibliography.bib

## The ceiling

This audit establishes that the project is well formed and that every finding below was resolved or is
listed as unresolved. It does not prove that no claim is mistaken. Both rounds were run by the same model
family over the same repository, so their errors are correlated. Round 2 went to the live sources and did
not read round 1's notes, which is why it found things round 1 could not. Items a person should still
check are in the Residual section.

## Audit Result

- Citation-integrity status: PASS after remediation. No fabricated or unresolvable source was found. All
  36 DOIs in the bibliography resolve in CrossRef with matching metadata: 33 were checked in round 2, and
  the three added during reconciliation (Dalpiaz et al. 2019; Semenov and Bojar 2022; Tan et al. 2024)
  were checked by the orchestrating session.
- Quotation status: PASS. Round 2 found all 70 scholarly quotations verbatim in a retrievable copy and all
  31 tool quotations on the tools' own sites. Five quotations were on a page other than the one cited.
- Factual-claim status: PASS WITH REMEDIATIONS. Round 1 found 55 claims that were unverified, overreaching
  or contradicted. Round 2 raised 16 scholarly findings (F1 to F16) and 25 tool rows with a verdict other
  than clean or a requested fix. A closure check then found 11 round 2 findings and 8 ledger entries only
  partly closed, and 16 new problems. All were remediated. Six findings changed what the project claims,
  and two of those contradicted it.
- Cross-file conflict status: PASS after remediation.
- Mechanical gates: `citation-audit` passes with no DEFECT. `history-check` passes (16 rows: 15 sourced,
  1 inference). `methodology-check` reports a missing domain guide, which is recorded as a deliberate gap
  (RR-06).
- Release gate: OPEN, subject to the residual items.

## Method

**Round 1.** @reference-manager checked every citation against the bibliography and the evidence notes
(Dimension A, 34 findings). @technical-validator built a claim ledger against the evidence notes
(Dimension B, about 250 claims verified and 55 not).

**Round 2.** Two independent reviewers, framed adversarially ("assume a citation or claim is fabricated;
find it"), worked from the deliverables alone and re-verified against the live web without reading the
evidence notes. One covered the scholarly sources and one the tool documentation. Their notes are
`references/evidence/R2-adversarial-scholarly.md` and `R2-adversarial-tools.md`.

**Reconciliation.** The orchestrating session re-read the passages behind three findings that changed the
argument (Marić, Winkels and Hoekstra, Mokhov et al.), remediated every finding, and compared the rounds.
After the closure check it also re-read six tool pages behind claims added in revision. The re-readings
are in `references/evidence/D-audit-reverification.md`.

**Closure check.** @conflict-auditor compared the revised deliverables with both rounds and with this
ledger, and its findings were remediated in turn (see "Closure check" below).

## Where the rounds diverged

Round 2 found what round 1 could not, because round 1 checked the deliverables against notes that
shared the same blind spots.

| Divergence | Round 1 | Round 2 | Resolution |
|---|---|---|---|
| Marić 2024 | Flagged the reading as going beyond the abstract (B-07) | Read the open full text: the author calls consistency "fairly high" (F2) | Confirmed by re-reading section 6.1.3. Marić is no longer used as evidence that a register failed |
| Winkels and Hoekstra 2012, sync trigger | Accepted "not stated" | Section 3.1 states regular checking and a hash per article (F7a) | Confirmed. Now cited as a precedent for the hash test |
| Claude Code hooks | Flagged the "agent edits only" claim as an inference (B-13) | The documentation describes a file-watching event that sees outside changes (T48) | Text corrected in all three files |
| Mokhov et al. page | Accepted 79:4 from the evidence note | The passages are on 79:3 (F1) | Confirmed against the published PDF and corrected |
| Definely quotation | Verified against the note | The words are in a companion article, not the one cited (T34) | Re-attributed |
| "No study was found" | Flagged as stated too broadly (B-08) | Named a nearby study, Dalpiaz et al. 2019 (F9) | Claim narrowed; the study is cited as the nearest work, unread |
| Prose-matching plugins | Not available to round 1 | Two plugins hold definitions and match plain prose (T51) | Added to the review; the gap claim narrowed |

Both rounds independently found the missing reference-list entries, the dropped "among other reasons" in
the Kuhn case, the SKOS S13 basis that did not support implication 2, and the Hilton respondent quotation
presented as a finding.

## Findings Ledger

Findings are grouped. Identifiers are those of the round that raised them: A (round 1, citations), B
(round 1, claims), F (round 2, scholarly), T (round 2, tools).

### Changed what the project claims (AUD-01 and AUD-04 contradicted it)

1. AUD-01 (CRITICAL, Resolved) — B-07, F2
- Location: 01 section 4 and section 10; 02 section 4; 03 summary and conclusion 2.
- Issue: Marić 2024 was presented as a case in which a register did not produce consistent use.
- Challenge: The abstract says only that the terms were sampled from the register. The full text reports
  51 of 100 terms fully consistent and calls overall consistency "fairly high."
- Remediation: Marić is now cited as a measurement study only. Section 4 of the analysis says the direct
  evidence that an unchecked register fails is one second-hand case, and conclusion 2 is stated as a
  judgement.

2. AUD-02 (MAJOR, Resolved) — B-31, B-43, F3, F4
- Location: 01 section 4; 02 section 4; 03 conclusion 2.
- Issue: The Kuhn case lost its qualifier "among other reasons" in 02 and 03, a rule from one controlled
  language was placed beside another, and a heading stated a general law.
- Remediation: The qualifier is restored everywhere. The rule is attributed to ASD Simplified Technical
  English. The heading now reads as a judgement. The 1998 source Kuhn cites is described in prose and not
  given as a citation (A-09).

3. AUD-03 (MAJOR, Resolved) — B-35, B-36, B-37, F5, F11
- Location: 02 section 7, implications 2, 3 and 4.
- Issue: Implication 2 rested on SKOS S13, which constrains the labels of one concept and says nothing
  about uniqueness across concepts. Implication 3 rested on Knuth, whose system marks prose entries by
  hand. Implication 4 used Knuth for currency, which he does not discuss.
- Remediation: Implication 2 rests on Deissenboeck and Pizka and on synonym control. Implication 3 rests
  on the gap and on the tools that match prose. Implication 4 rests on Luhn, with Knuth as a precedent for
  generation only.

4. AUD-04 (MAJOR, Resolved) — F7a, F7b, B-15, B-24, B-29
- Location: 01 section 6 and section 10; 02 table, section 3 and section 5; 03 conclusion 4.
- Issue: The legal concept record was called a design that joins a register to an automatically
  maintained index, its sync trigger was given as "not stated," and "the full design exists" overstated
  both precedents.
- Remediation: The record is described as a specification and a goal, with the 42 percent recall for
  definitions. Its regular checking and hash test are reported and cited for implication 5. Headings now
  say "nearest precedents."

5. AUD-05 (MAJOR, Resolved) — B-13, B-17, T48, T49, T50
- Location: 01 section 9 and section 10; 02 section 5; 03 conclusion 6.
- Issue: Agent-session hooks were said to see only agent edits.
- Remediation: The text distinguishes the after-edit hook from the file-watching event and says that both
  run only while a session runs.

6. AUD-06 (MAJOR, Resolved) — B-28, B-30, T51, T52
- Location: 02 section 3; 03 conclusion 5; 01 section 7.
- Issue: The claim that tools detecting unmarked uses hold no definitions was overstated, and Markdown was
  said to have none of the markup the toolchains rely on.
- Remediation: Two prose-matching plugins are added to the review and the table. The gap is restated as
  the absence of a stored occurrence index with a freshness check. Matching is presented as this
  project's choice.

### Overreach and unverified claims, reworded

7. AUD-07 (MODERATE, Resolved) — B-01, B-46, B-54, B-55: Mulvany was read as a publisher's description.
   The review no longer generalises to "the professional indexing literature," the map gives Mulvany its
   own row, and the analysis now carries the point it promised.
8. AUD-08 (MODERATE, Resolved) — B-02, B-03, B-04, B-05: Warburton's "first monograph" keeps its limit;
   "will miss most real usage" is now an inference without "most"; the NISO and SKOS statement is limited
   to the parts read; "closing sentence" is dropped.
9. AUD-09 (MODERATE, Resolved) — B-06: "Three sources" on enforcement is now one, with the measurement
   studies introduced separately.
10. AUD-10 (MODERATE, Resolved) — B-08, F9: the absence claim is narrowed and identical in all three
    files.
11. AUD-11 (MODERATE, Resolved) — B-09, F12, F13, F16: best practice is reported as cited by Gemkow et
    al.; the code record is reported as taken from earlier guidelines; "unintended variations" is given as
    the authors' experience.
12. AUD-12 (MODERATE, Resolved) — B-10: the occurrence list in the identifier dictionary is quoted as a
    requirement ("should be able to"), and the conclusion notes the design was not evaluated.
13. AUD-13 (MODERATE, Resolved) — B-11, A-30, A-31: text versions are stated where used (thesis
    reproduction, manuscript pages, PDF page).
14. AUD-14 (MODERATE, Resolved) — B-12, B-34, F15: the "watchdog" line is given as one respondent's;
    Pro Git is cited for server-side enforcement and Tan et al. for a proposal.
15. AUD-15 (MODERATE, Resolved) — B-14: the separation of the two traditions is stated as "largely," with
    Hodge on linking names in text.
16. AUD-16 (MODERATE, Resolved) — B-16, T54: "a build refreshes it" is limited to documentation
    toolchains.
17. AUD-17 (MODERATE, Resolved) — B-19, T42: the drafting guidance is quoted with its limit, and its index
    of defined terms is described as an index of definitions, not of uses.
18. AUD-18 (MODERATE, Resolved) — B-20 to B-27, T04, T07, T08, T13, T25, F7a, F11: cells of the comparison
    table were corrected or filled in. They are: the concordance's occurrence handling and sync trigger;
    the codebook's occurrence index; WEB's register, occurrence handling and enforcement; the legal
    record's occurrence handling, index and sync trigger; Sphinx's index; the LaTeX enforcement cell; the
    DITA and DocBook enforcement cells, now in separate rows; and Vale's index and sync trigger. A row was
    added for the prose-matching plugins. The caption no longer claims that every cell is a source's own
    statement.
19. AUD-19 (MODERATE, Resolved) — B-32, B-33, F14: Lee et al. is limited to API documentation; the
    language server "is notified and resolves on request"; Zhong and Su is paraphrased from the abstract
    only.
20. AUD-20 (MODERATE, Resolved) — B-39 to B-45: the conclusion's summary no longer states sufficiency,
    marks the layering as an inference, marks the hash test as an analogy, and calls the codebook an
    analogy.
21. AUD-21 (MODERATE, Resolved) — F6: Hodge's qualification that ambiguity "can be overcome" is added,
    and the ceiling no longer rests on Hodge.
22. AUD-22 (MODERATE, Resolved) — F10: the 2020 statement on definition detection is dated, and the case
    for declared definitions rests on governance.
23. AUD-23 (MINOR, Resolved) — B-38: "five long documents" corrected to four.

### Citations and bibliography

24. CIT-01 (MAJOR, Resolved) — A-01 to A-08, F8, T58: eight in-text citations were missing from their
    file's reference list. Cause: the list generator did not match a label split across a line break.
    Fixed, and the lists were regenerated.
25. CIT-02 (MODERATE, Resolved) — A-10 to A-13: in-text labels and reference entries now agree for memoQ,
    VERBI and the TEI Consortium, and a missing period was added.
26. CIT-03 (MODERATE, Resolved) — A-14 to A-18: the compiler and editor roles for two Benjamins volumes
    are noted in the records. Author names for Feitelson et al., Head et al. and Kang et al. were
    confirmed against CrossRef in a second pass.
27. CIT-04 (MODERATE, Resolved) — A-19, T02, T10, T32, T34, T35, T36, T37, T40: five quotations sat on a
    page other than the record's URL. The reference-list entries for Sphinx, DITA, Google, Write the Docs
    and Vale now carry each page's URL, and the Definely companion article has its own record (Definely
    2026b).
28. CIT-05 (MINOR, Resolved) — A-20 to A-28: workshop venue moved out of the address field; companion DOI,
    page update date, corporate author and missing publisher noted.
29. CIT-06 (MAJOR, Resolved) — F1: Mokhov et al. page 79:4 corrected to 79:3.

### Interpretive map

30. MAP-01 (MODERATE, Resolved) — B-47: the "direct descendants" are the inventors of the computer, not
    the compilers. The genealogy arrow is reworded.
31. MAP-02 (MODERATE, Resolved) — B-48: the arrow from project glossary to identifier dictionary is now
    marked as an editors' inference.
32. MAP-03 (MODERATE, Resolved) — B-49 to B-53, A-33, A-34: places and audiences the evidence does not
    carry were removed from the Historical setting register and left blank.
33. MAP-04 (MINOR, Resolved) — A-29: the map states that it carries no reference list and that every
    label resolves in the bibliography.

### Cross-file consistency

34. CON-01 (MAJOR, Resolved) — B-18, A-32: the literature review pointed to this file before it existed.
35. CON-02 (MODERATE, Resolved): the definition of "synced" said "whenever," which the design does not
    deliver for edits made outside a session. The definition now reads "regenerated by automatic triggers
    ... with any remaining staleness detectable by a check," in the plan and the review.
36. CON-03 (MODERATE, Resolved): the analysis recommended that a discouraged form be advisory, while the
    plan audit showed that an advisory check would not be enforcement. Implication 7 now recommends a
    failing check with recorded exceptions and says the evidence does not settle the choice.

### Closure check

37. CLO-01 (MAJOR, Resolved): the conclusion's summary had dropped "among other reasons" from the Kuhn
    case and turned "discontinued" into "fails," although this ledger said the qualifier was restored
    everywhere. Restored. The heading of section 4 of the analysis no longer states a law.
38. CLO-02 (MAJOR, Resolved): the analysis said in bold that the tools detecting unmarked uses keep no
    index, which its own table contradicted for the contract tool. The claim is limited to documentation
    tools and to a stored index.
39. CLO-03 (MODERATE, Resolved): "the sources suggest three conditions" and "descends from" presented the
    project's own synthesis as sourced. Both are now marked as the project's reading. Luhn is cited for
    machine generation as a means to currency, not as its condition.
40. CLO-04 (MODERATE, Resolved): Deissenboeck and Pizka were called a precedent for a "synced" index,
    which under the project's definition implies a staleness check the paper does not have. Now
    "incrementally maintained."
41. CLO-05 (MODERATE, Resolved): Arora et al.'s observation is marked as experience in the analysis as
    well; "on each change" was dropped from the Hilton et al. citation; "already practised" became
    "already supported"; the Obsidian claim is cited; a heading resting on a publisher's description was
    softened; a third prose-matching tool was added (T51); Knuth's text version is stated in the review;
    audiences the evidence does not carry were removed from five more register rows (MAP-03).
42. CLO-06 (MODERATE, Resolved): a quotation of Vale's documentation joined words from two sentences. It
    now quotes one sentence, re-read at the source.
43. CLO-07 (MINOR, Resolved): the round 0 evidence notes now carry a notice pointing to the later notes
    that supersede them in part.

## Residual Risks

- RR-01 (MODERATE): The ISO standards on terminology work, vocabularies, termbase exchange and indexes
  (ISO 704, 1087, 25964-1, 30042, 999) could not be retrieved. They are not cited, and the review's
  account of terminology standards rests on NISO and SKOS.
- RR-02 (MODERATE): Sources read only as an abstract, an opening passage or a publisher's description:
  Luhn 1960; Mulvany 2005; Cabré 1999; Wright and Budin 1997; Warburton 2021; Daille 2017; Bowker and
  Star 1999; Gerring 1999; MacQueen et al. 1998; DeCuir-Gunby et al. 2011; Gašpar et al. 2022; Semenov
  and Bojar 2022; Kang et al. 2020; Head et al. 2021; Mihalcea and Csomai 2007; Lawrie et al. 2006; Wen
  et al. 2019; Feitelson et al. 2022; Zhong and Su 2013. Each use is marked in the literature review, and
  not again in the analysis or the conclusion. The Semenov and Bojar quotation matches the abstract on the
  proceedings page; the abstract in the PDF is worded slightly differently.
- RR-03 (MODERATE): The reason given for discontinuing Caterpillar Fundamental English comes from a 1998
  report that Kuhn quotes. That report was not read.
- RR-04 (MINOR): Dalpiaz et al. 2019 is cited from its record only.
- RR-05 (MINOR): The end page of Winkels and Hoekstra 2012 is not confirmed. The year of Pro Git's second
  edition (2014) is not on the page read.
- RR-06 (MINOR): No domain methodology guide exists for this project, so `methodology-check` reports a
  missing guide. The interpretive map explains why. Run with `METHODOLOGY_COVERAGE_ADVISORY=1`.
- RR-07 (MINOR): The mechanical citation detector prints `NEEDS-REVIEW[RM]` for Gašpar and Marić because
  it does not match surnames with diacritics, and `[PE]` for sources cited only with multi-author labels.
  Both are detector limits. The records exist and are cited.
- RR-08 (MODERATE): The tool survey was not exhaustive. Commercial terminology tools, and plugins for
  site generators other than those named, were not examined. The three prose-matching tools added in
  revision are described from their README or reference page only.
- RR-09 (MODERATE): Two tool claims added in revision rest on the round 2 reading alone: that the LaTeX
  glossaries package raises an error on an undefined entry by default, and the list of triggers in Vale's
  documentation.
- RR-10 (MINOR): The Mokhov et al. page numbers were confirmed against the copy hosted by the authors'
  employer, which carries the publisher's pagination. The publisher's own PDF could not be retrieved.
- RR-11 (MINOR): The statement that Deissenboeck and Pizka do not evaluate their design empirically is
  this project's characterisation. Round 2 located the relevant passage on page 281, which this session
  did not re-read.
- RR-12 (MINOR): Whether the qualitative analysis package reviewed can assign codes automatically from a
  text search was not checked.

Items for human resolution: RR-01, RR-03, RR-05, RR-09 and RR-11.

## Final Disposition

Both rounds of the 2-fold audit were run, followed by a closure check. Every finding was remediated, and
the two findings that contradicted the argument (AUD-01, AUD-04) changed it: the project now claims less about enforcement and
credits the hash test to a source it had under-read. Citation integrity is consistent, and no unresolved
citation or claim finding remains. The residual items above are stated for a human reader to resolve.
