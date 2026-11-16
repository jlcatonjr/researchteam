# R2: adversarial citation and claim audit of the scholarly sources (Part I)

Date: 2026-11-16. Round 2 of the 2-fold audit, done independently. Inputs were `01-literature-review.md`
(sections 1–6 and 10), `02-analysis.md` and `03-conclusion.md`, with their reference lists. Nothing
under `references/evidence/` was read. No deliverable was edited.

**Premise adopted:** at least one citation or claim is fabricated, misquoted or misattributed.

**Method.**
- Every DOI was resolved through `api.crossref.org/works/<doi>`, with a generic User-Agent.
- Abstracts came from the CrossRef `abstract` field and from the OpenAlex `abstract_inverted_index`.
- Full texts came from the open copies listed below. Each was converted with `pdftotext` and every
  quotation was searched for with a normalising grep that ignores whitespace, hyphenation and curly
  quotes.
- Page locators were checked against the running heads of each PDF.

**Full texts reached:**

| Source | Copy used |
|---|---|
| Deissenboeck and Pizka | itestra.com journal PDF, *Software Qual J* 14:261–282 |
| Kuhn | arXiv 1507.01701 |
| Marić | hrcak.srce.hr/file/468046 |
| Mokhov et al. | Microsoft Research PDF, which carries the PACMPL Article 79 footer |
| Rouse and Rouse | heyjoe.fbk.eu PDF |
| Knuth | literateprogramming.com/knuthweb.pdf |
| NISO Z39.19 | the URL supplied |
| SKOS | w3.org/TR/skos-reference |
| Hodge | CLIR pub91.pdf |
| Ashburner et al. | PMC3037419 (HTML) |
| Roberts et al. | Europe PMC PMC6437927 |
| Arora et al. | orbilu manuscript |
| Gemkow et al. | depositonce (TU Berlin) |
| Winkels and Hoekstra | UvA pure, accepted manuscript |
| Aghajani et al. 2019 and 2020 | emadpres.github.io |
| Hilton et al. | uwaterloo course copy |
| Resi | CEUR |
| Evans | domainlanguage PDF |
| Tan et al. 2024 | arXiv 2212.01479 |
| Semenov and Bojar | ACL Anthology 2022.wmt-1.41 |

## Summary of verdicts

**Existence and metadata.**
- All 33 DOIs in the Part I reference list resolve. Authors, year, title, venue and pages match CrossRef.
- No reference is fabricated.
- Three works cited in the text of 01 have no entry in 01's reference list (F8).

**Direct quotations.** 70 checked.

| Verdict | Count |
|---|---|
| FOUND VERBATIM | 70 |
| Found in one version only (verbatim in the ACL landing-page abstract; the PDF abstract words it slightly differently) | 1 of the 70 |
| NOT FOUND | 0 |
| CONTRADICTED | 0 |

No quotation was fabricated or altered.

**Locators.** Page and section locators were checked for:
- Rouse and Rouse 5–6
- Hodge 5 and 12
- Resi 2
- Evans 2
- Deissenboeck and Pizka 261, 263, 268, 278 and 279
- Arora et al. 1, 2 and 13
- NISO 5.1 and 5.3.2
- SKOS S13 and S14
- Knuth §27
- Mokhov et al. 79:4 and 79:14

All are correct except one: **Mokhov 79:4 should be 79:3**, in two places (F1).

**Paraphrased claims and numbers.**

| Verdict | Count | Findings |
|---|---|---|
| SUPPORTED | about 45 | |
| OVERSTATED | 8 | F2, F3, F6, F7b, F10, F11, F14, F15 |
| CONTRADICTED | 2 | F2 (Marić full text), F7a (Winkels sync trigger) |
| UNSUPPORTED | 1 | F5 (SKOS S13 used as the basis for cross-concept uniqueness) |
| Attribution-direction notes | 4 | F4, F12, F13, F17 |
| Absence claim weakened | 1 | F9 |
| Missing reference entries | 3 | F8 |

## Findings table

| ID | File:line or section | Item checked | Verdict | What was found (with URL) | Suggested correction |
|---|---|---|---|---|---|
| F1 | 01:209–211; 02:131–132 | Mokhov et al. 2018, minimality definition "(79:4)" and file times fooled by `touch` "(79:4, 79:14)" | QUOTE FOUND VERBATIM; LOCATOR WRONG | Definition 2.1 (Minimality) and footnote 5 ("you can fool Make by altering the modification time of a file without changing its content, e.g. by using the command touch") both fall under running head **79:3**, before the 79:4 head. Backup software (79:14) and "values/hashes of dependencies used last time" (79:14) are correct. https://www.microsoft.com/en-us/research/uploads/prod/2018/03/build-systems-a-la-carte.pdf | Change 79:4 to 79:3 in 01:209, 01:211 and 02:132. Confirm against the ACM DL PDF. |
| F2 | 01:118–121; 01:338–340 (§10.2); 02:92–95; 03:14–15; 03:35–37 | Marić 2024. The quotations "taken from IATE" and "the results confirm the presence of terminological inconsistency" | QUOTES FOUND VERBATIM (abstract). INFERENCE OVERSTATED, and CONTRADICTED by the open full text | The full text, §6.1.3: "51 terms having optimal scores of 100. This means that the overall consistency was fairly high, with the median score being 100.00 (IQR = 63.31-100.00)." IATE is also the researcher's *sampling source* for the 100 terms. Marić notes that many English terms in IATE lack a Croatian equivalent and that 29 of the 100 terms lack a definition or are unreliable in IATE. The deliverable says that "a register ... did not, in that corpus, produce consistent use" and treats it as a case where "a register by itself was not enough". The source itself characterises consistency as fairly high. https://hrcak.srce.hr/file/468046 | Read the full text, which is open access. Restate as: "inconsistency was present in about half the terms, but the author judges overall consistency fairly high (median HHI 100)". Drop Marić as evidence that an unchecked register fails, or heavily qualify it. Also note that it is unknown whether translators were bound to the IATE entries. |
| F3 | 01:338–339 (§10.2); 02:89–91; 03:34–35 | Kuhn 2014: CFE "discontinued ... because" it was unenforceable | OVERSTATED | Kuhn: "CFE was discontinued by Caterpillar in 1982, because (among other reasons) 'the basic guidelines of CFE were not enforceable ...' (Kamprath et al. 1998)". 01:112–113 keeps "among other reasons". §10, 02 and 03 drop it ("abandoned as unenforceable", "discontinued as unenforceable"). CTE development started in 1991, "almost a decade after". https://arxiv.org/pdf/1507.01701 | Restore "among other reasons" in 01 §10, 02 §4 and 03 conclusion 2. |
| F4 | 01:109–113 | Kuhn: the "Keep to the approved meaning ..." rule and "around 800 to 1,000 words ... with only one meaning" | FOUND VERBATIM; ATTRIBUTION (e) | (a) The rule is quoted by Kuhn from **ASD-STE (Simplified Technical English)**, not from CFE, although the sentence that follows in 01 is about CFE. (b) The ellipsis removes "(Crabbe 2009)". The vocabulary figure is Kuhn citing Crabbe. | Name ASD-STE as the source of the rule, and write "Kuhn, citing Crabbe (2009)". |
| F5 | 02:168–169 (implication 2) | "Require each preferred label and variant to belong to one concept only. Basis: ... the label disjointness of SKOS (W3C 2009, S13)" | UNSUPPORTED (misapplied) | S13: "skos:prefLabel, skos:altLabel and skos:hiddenLabel are pairwise disjoint properties". This constrains the labels **of one resource**. The SKOS Reference sets no integrity condition against two concepts sharing a label. Only notations get a by-convention uniqueness rule (§6.5.3). 01:81–83 states S13/S14 correctly. https://www.w3.org/TR/skos-reference/ | Cite S13/S14 only for the within-concept rule. Base cross-concept uniqueness on Deissenboeck and Pizka (bijection) and NISO 5.3.2, or on the SKOS Primer's recommendation, and label it a project choice. |
| F6 | 01:89–91; 02:138–139; 02:184; 03:59–60 | Hodge 2000, 12: "Because of the ambiguity in organism names, many examples of this type are now created manually" | QUOTE FOUND VERBATIM (p. 12); SELECTIVE, so OVERSTATED | The next sentence in Hodge: "However, depending on the extent of the files involved, the ambiguity of the Latin and common names for organisms can be overcome." 01 presents the quotation as "the limit of the automatic route", and 02/03 use it as the basis for the ceiling. https://www.clir.org/wp-content/uploads/sites/6/pub91.pdf | Add Hodge's qualification. The ceiling claim (matching finds forms, not senses) stands on its own logic and does not need Hodge as proof. |
| F7a | 02:53 (table row, "Sync trigger: not stated") | Winkels and Hoekstra 2012 | CONTRADICTED | §3.1, Version Management: the system builds a version history "by regularly checking for new versions", and "a SHA1 hash code is generated and attached to" each article. "If the hash code differs, something definitely changed and the direct links with the earlier version and the concepts are broken." This is a stated sync trigger (polling) and a content-hash staleness test. It is the closest precedent for implication 5, yet 02 §5 and 03 credit hashing only to Mokhov et al. https://pure.uva.nl/ws/files/88234356/125492_Winkels_Hoekstra_Jurix_2012_2.pdf | Table: "periodic polling; SHA-1 per article". Cite Winkels and Hoekstra §3.1 alongside Mokhov et al. in 02 §5 and implication 5. |
| F7b | 01:223–227; 03:45–47 | Winkels: "references to all occurrences of the concept in the sources" | QUOTE FOUND VERBATIM; OVERSTATED | The five-item record is listed under "Goals of the Experiment" ("for every concept we need to add information"). The results report definition extraction as "somewhat disappointing ... recall is only 42%" (§4.1). 03 says the record "holds each definition". | Say that the record is the experiment's goal, and report the 42% recall for definitions. This also supports the "definitions should be declared" point. |
| F8 | 01:125 (Semenov and Bojar 2022); 01:203 (Tan et al. 2024); 01:101 (Bowker and Star 1999) | Reference-list completeness | MISSING ENTRIES | The works exist and the claims check out. (1) Semenov, Kirill, and Ondřej Bojar. 2022. "Automated Evaluation Metric for Terminology Consistency in MT." *WMT 2022*, 450–457. https://aclanthology.org/2022.wmt-1.41. The quotation matches the landing-page abstract verbatim; the PDF abstract reads "consistency of translation of terms". (2) Tan, Wen Siang, Markus Wagner, and Christoph Treude. 2024. "Detecting Outdated Code Element References in Software Repository Documentation." *Empirical Software Engineering* 29 (1): 5. https://doi.org/10.1007/s10664-023-10397-6, preprint arXiv 2212.01479. "over 3,000 GitHub projects", "most projects contain at least one outdated code element reference at some point" and the future-work quotation are all verbatim. (3) Bowker and Star is in 02's list but not 01's. Kamprath et al. 1998 is used at second hand without an entry, which is acceptable if styled "quoted in Kuhn 2014". | Add the three entries to the 01 references. Format Kamprath as "quoted in". |
| F9 | 01:127–128; 02:192–193; 03:73–74 | Absence claim: "No peer-reviewed study measuring terminology consistency in monolingual technical or research documentation was found" | WEAKENED (borderline counter-examples) | (a) Dalpiaz, van der Schalk, Brinkkemper, Aydemir and Lucassen. 2019. "Detecting Terminological Ambiguity in User Stories: Tool and Experimentation." *Information and Software Technology* 110: 3–16. https://doi.org/10.1016/j.infsof.2018.12.007. It is a peer-reviewed controlled experiment on detecting near-synonyms (terminological inconsistency) in monolingual requirements. (b) The deliverable's own Aghajani et al. 2019 codes "Inconsistent terminology" as an issue type in mined documentation artifacts. (c) Deissenboeck and Pizka §5 and Lawrie et al. 2006 measure synonym and naming violations in monolingual code. None of these computes a corpus consistency index as Marić and Gašpar do, so the claim survives only in a narrow reading. | Narrow the wording to "no study applying a consistency index (for example HHI) to monolingual documentation". Cite Dalpiaz et al. 2019 as the nearest work. |
| F10 | 01:229–231; 02:155–156 | Kang et al. 2020: definition detection is "far from being accurate enough to use in realworld applications" | QUOTE FOUND VERBATIM (abstract); OVERSTATED and temporal | In the abstract the sentence describes the state of the art *before* the authors' own HEDDEx system, which then improves F1 by 12.7 and 14.4 points. 02 turns this into the 2026 premise "was reported as too inaccurate for use". That reads a 2020 state of the art forward without dating it. https://aclanthology.org/2020.sdp-1.22 | Write "in 2020, prior systems were reported as ...". Rest "definitions should be declared" on the governance argument (Knuth's division and auditability), not on a dated accuracy figure. |
| F11 | 02:52 (table); 02:155–158; 03:48 | Knuth 1984 §27 as precedent for "definitions declared by the author" | QUOTES FOUND VERBATIM; EQUIVOCATION | In WEB, "definition" means the *program point where an identifier is defined* ("underlining of section numbers is not automatic; the user is supposed to mark identifiers at their point of definition"). It is not a prose definition of a term. 02 and 03 carry it across to term definitions without saying so. Minor: one-letter identifiers are indexed only at their definition, so the index is not of "every identifier" occurrence. http://www.literateprogramming.com/knuthweb.pdf | Say "by analogy". In WEB the author marks where identifiers are defined. |
| F12 | 01:164–165 | Gemkow et al. 2018: "should be developed continuously" | FOUND (two-column text); ATTRIBUTION (e) | Gemkow: "Best practice in RE holds that a glossary should be developed continuously during the process of requirements elicitation [2]." This is Gemkow reporting cited best practice. | Write "They report the best-practice view that ...". |
| F13 | 01:139–141 | Roberts et al. 2019 code record structure | FOUND VERBATIM; ATTRIBUTION (e) | "Codes were written following the guidelines of Boyatzis [9] and were classified with the following: label, definition, ..." | Add "following Boyatzis". |
| F14 | 01:201–202 | Zhong and Su 2013, abstract: errors found "by cross-checking names in prose against names in code" | OVERSTATED relative to the stated access level (d) | The abstract says only that DOCREF "combine[s] NL and code analysis techniques" to detect inconsistencies, and mentions "broken code names" and "obsolete code samples". The specific mechanism is not in the abstract. ">1,000" is correct. | Paraphrase the abstract only, or read the paper. |
| F15 | 01:215–218; 02:120–121 | Hilton et al. 2016: CI "valued as a check that does not depend on individual diligence"; "runs whether or not anyone remembers to" | QUOTE FOUND VERBATIM (one respondent, P371); OVERSTATED | The watchdog line is a single respondent's comment. The most popular survey reasons were "less worried about breaking our builds" and "catch bugs earlier". 02 presents the respondent's remark as a finding. https://cs.uwaterloo.ca/~m2nagapp/courses/CS846/1171/papers/hilton_ase16.pdf | Write "one respondent described CI as ...". |
| F16 | 01:162; 02:70 | Arora et al. 2017, 13: "industrial requirements are prone to containing unintended variations" | FOUND VERBATIM (manuscript p. 13); minor | The sentence is prefixed "from our experience, we observe that". It is experiential, not a measured result, yet 02 calls it "what the requirements literature reports in practice". | Write "the authors observe from experience". |
| F17 | 01:66–69; 02:142; 03:60 | Resi 2025, 2: counter-position on variants | FOUND VERBATIM (p. 2) | Resi attributes the view to "text-linguistic approaches to terminology [10-11]". 01's "records the counter-position" is accurate. 01 already flags the unchecked support for the "key principle" claim ([8,9]). | None needed. Optionally name the attributed school. |

## Clean results (SUPPORTED or FOUND VERBATIM), for the record

| Source | Result |
|---|---|
| Rouse and Rouse 1974 | All three quotations are verbatim. Pages 5 and 5–6 are correct, with p. 6 beginning mid-sentence at "some 100,000". The "100,000 ... 10,000" figure is theirs. |
| Luhn 1960 | Both abstract quotations are verbatim (CrossRef abstract). |
| Mulvany 2005 | The description quotation and the TOC entries "Automatic Indexing" and "Computer-aided Indexing" are verbatim (chicagoreference.com). |
| Cabré 1999 | Ch. V "Computerized terminology" and Ch. VI "Terminology and Standardization" confirmed through CrossRef chapter DOIs. "Data banks" was not seen (see below). |
| Wright and Budin 1997 | The description quotation is verbatim (CrossRef). Section "2.2 Prescriptive Terminology" exists (10.1075/z.htm1.23pre). |
| Warburton 2021 | "first monograph" is reported in the publisher description (search snippet only). |
| Daille 2017 | Both quotations are verbatim (CrossRef abstract). |
| NISO 2010 | All three quotations are verbatim. Sections 5.1 ("five purposes") and 5.3.2 Synonymy are correct. |
| SKOS (01) | S13 and S14 are correct, and the date is 18 August 2009. |
| Hodge 2000 | The glossary definition on p. 5 is verbatim. |
| Ashburner et al. 2000 | All four quotations are verbatim. "in our writing as well as our thinking" is in the closing sentence before the acknowledgements. |
| Bowker and Star 1999 | The description quotation is verbatim. |
| Kuhn 2014 | The enforceability quotations and "1982" are verbatim and correct. |
| Gašpar et al. 2022 | Uses HHI, a concentration index. Correct. |
| MacQueen et al. 1998 | Both quotations are verbatim in the opening text. The venue, *CAM Journal* 10 (2), matches CrossRef. |
| DeCuir-Gunby et al. 2011 | The quotation is verbatim. Online first 2010, print 2011. |
| Roberts et al. 2019 | All four quotations are verbatim. |
| Gerring 1999 | Both quotations are verbatim, and "eight" is correct. |
| Arora et al. 2017 | pp. 1, 2 and 13 are correct (manuscript). |
| Gemkow et al. 2018 | The canonical-terms quotation is verbatim. |
| Deissenboeck and Pizka 2006 | All six quotations are verbatim. Pages 261, 263, 268 (Definition (Consistency), a bijective mapping), 278 and 279 are correct. "Without an empirical evaluation" is supported: "So far, there are no direct experiences with the IDD" (p. 281). |
| Lawrie et al. 2006 | Verbatim. |
| Feitelson et al. 2022 | "median probability was only 6.9 percent" is correct. |
| Knuth 1984 | Both §27 quotations are verbatim. Hand-inserted index entries are confirmed. |
| Aghajani et al. 2019 | "is not in sync with other parts of a system" (Up-to-dateness, n=190) and "Inconsistent terminology" are verbatim. |
| Aghajani et al. 2020 | 59% is correct. "lack of/poor automatization was the only issue frequently faced". 125 of 146 respondents were from ABB, so "one company" is correct. |
| Wen et al. 2019 | Verbatim. |
| Tan et al. 2007 | 60 / 33 / 27 and four systems are correct (abstract). |
| Lee et al. 2021 | Verbatim. |
| Evans 2015 | The quotation is verbatim on printed p. 2 (Bounded Context). |
| Head et al. 2021 | Verbatim; the usability study is correct. |
| Mihalcea and Csomai 2007 | "hardly distinguishable from manual annotations" supports "approach". |

## Could not check, and why

- **Cabré 1999: "including terminological data banks".** Only the chapter-level titles were reached through CrossRef. benjamins.com returned 403.
- **Warburton 2021.** The table of contents (creating, launching, expanding and maintaining a termbase) and the "first monograph" wording were confirmed only through a search-engine summary. The publisher page returned 403.
- **Wright and Budin 1997.** Only one TOC heading was confirmed (2.2). The full TOC was not reached.
- **Kamprath et al. 1998.** This is the source Kuhn quotes. It was not retrieved, so the primary wording of the CFE reason is unverified.
- **Kuhn 2014.** Pagination in the published *Computational Linguistics* version was not checked, because only the arXiv preprint was read. The deliverable gives no page numbers.
- **Mokhov et al. 2018.** The ACM DL PDF itself (Cloudflare-blocked) was not checked. The Microsoft Research copy carries the ACM Article 79 footer and pagination, so F1 is high-confidence but should be confirmed.
- **Winkels and Hoekstra 2012.** The published page range is unknown: CrossRef and OpenAlex carry no pages, so "157ff" could not be completed. The manuscript is the accepted version, not the IOS Press typeset.
- **Full texts of Gerring, MacQueen et al., DeCuir-Gunby et al., Lee et al., Zhong and Su, Wen et al., Lawrie et al. and Tan et al. 2007.** These were not reached (paywalled). The deliverable uses them at abstract level, and abstract-level claims were checked.
- **Body text of Bowker and Star.** Not read. The deliverable correctly limits itself to the description.
- **Gašpar et al. 2022 full text.** MDPI returned an HTML challenge. The abstract-level claim was checked.
- **Absence-claim search.** It was not exhaustive (one targeted web search plus known literature), so other counter-examples may exist.
