# Literature Review

**For:** *Using Reinforcement Learning With Ensemble Voting for Romanian Diacritic Restoration* — Ingrid M. Caton
**Compiled:** 2026-05-29 · **Revised:** 2026-05-29 (post adversarial + conflict review)
**Citation style:** Chicago author–date. Full entries in [`references/bibliography.bib`](references/bibliography.bib).

> **Nature of this document — prescriptive, not descriptive.** The article in its current form contains **no in-text citations and no References section**. This review therefore proposes the scholarly apparatus the article *should* engage; phrases like "must-cite," "load-bearing," and "depends on" describe a target state. **Action zero for the author: wire the manuscript to this bibliography** — none of the per-source recommendations take effect until the article actually cites them.
>
> **Provenance.** Every source carries a resolvable DOI (resolved against the Crossref REST API, or the deterministic `10.48550/arXiv.<id>` scheme for arXiv-native works). The works with no DOI (pre-2017 ACL/LREC papers, NIPS 1994, the JMLR article, three classic books, Condorcet 1785, and open-draft/software items) carry a **reliable canonical link** (official author page, ACL Anthology, NeurIPS proceedings, publisher catalogue, BnF Gallica, or Zenodo). No DOIs, URLs, or locators were invented.
>
> **Review status — reviewed; open issues remain.** All sources passed an **adversarial (presupposition) review** and a **conflict audit** on 2026-05-29. The audit found one *blocking* factual error in the original draft (a mischaracterization of the article's central result), now corrected; remaining open issues for the author are consolidated in §9. This is not a clean bill of health — it is a reviewed draft with explicit caveats.

---

## 1. How this article sits in the literature

The article is the intersection of **four** research programs:

1. **Diacritic restoration** — the application task (restore Romanian ă, â, î, ș, ț from unmarked text).
2. **Ensemble learning and voting** — the mechanism behind the headline result.
3. **Reinforcement / evolutionary learning with an *economic* selection rule** — agents bear a fixed marginal cost each period and are allocated a share of a fixed aggregate reward by relative performance; the tuning engine.
4. **LLM agents with optional tool use** — LLaMA 3.2 agents that may trust an external linguistic tool or fall back on their own judgment.

**What the article actually shows (corrected).** On its 22-sentence test set, the **tool-enhanced ensemble *matched* its single best individual agent on sentence accuracy** (both 83.5%) while lifting exact word-restoration to 95.5% (+45.5 pp over its constituents). The genuinely novel comparison is **cross-ensemble**: the tool-enhanced ensemble beat the *direct-inference* ensemble on both accuracy (83.5% vs 79.7%) and word restoration (95.5% vs 81.8%) **even though the direct-inference pool contained higher-scoring individual agents**. So the defensible reading of "individual excellence ≠ collective intelligence" is *between ensembles*, not "the ensemble beat its own strongest member on accuracy" (it did not — it tied). The ensemble's clear *within-pool* win is on word restoration, not accuracy.

Two observations condition the whole review: (a) that headline rests on a **single comparison at n=22 with ensemble selection performed on the test set** — so the diversity literature is load-bearing but cannot, by itself, rescue an underpowered result; and (b) the "economic model" has a real precedent in Baum's *Hayek Machine*, but the mapping is an **analogy, not a structural identity** (see §5).

---

## 2. Diacritic restoration — the task literature (must-cite)

- **Mihalcea and Nastase (2002)** — *Letter Level Learning for Language Independent Diacritics Restoration*. The foundational raw-text, language-independent formulation; >98% letter accuracy on four languages **including Romanian**. Historical baseline and the "letter vs. word" framing the article's word-level metric inherits.
- **Mihalcea (2002)** — *Diacritics Restoration: Learning from Letters versus Learning from Words*. Motivates the sentence-accuracy vs. exact-word-restoration distinction.
- **Tufiș and Ceaușu (2007)** — *Diacritics Restoration in Romanian Texts* (RACAI/RANLP). Canonical **Romanian-specific** statistical approach; the pre-neural comparison point.
- **De Pauw, Wagacha, and de Schryver (2007)** — *Automatic Diacritic Restoration for Resource-Scarce Languages*. Low-resource framing relevant to Romanian.
- **Náplava, Straka, Straková, and Hajič (2018)** — *Diacritics Restoration Using Neural Networks* (LREC). The strong multilingual **character-level RNN** baseline.
- **Náplava, Straka, and Straková (2021)** — *Diacritics Restoration using BERT* (PBML 116). **[Added per review.]** The **Transformer/BERT-era** restorer that supersedes the same group's 2018 RNN work; the obvious "why not just fine-tune a Romanian BERT for diacritics?" baseline. A 2024/2026 thesis must engage this, not stop at the RNN era.
- **Ruseti, Cotet, and Dascalu (2020)** — *Romanian Diacritics Restoration Using Recurrent Neural Networks* (arXiv:2009.02743). The most directly comparable **Romanian-optimized** neural restorer; the single most important external benchmark.
- **Nuțu, Lőrincz, and Stan (2019)** — *Deep Learning for Automatic Diacritics Restoration in Romanian* (ICCP). Romanian-specific architecture comparison.
- **Asahiah, Odẹ́jọbí, and Adágúnodò (2018)** — *A Survey of Diacritic Restoration in Abjad and Alphabet Writing Systems* (*Natural Language Engineering* 24(1)). Cross-writing-system survey; situates the task. *(Use as a survey, not a primary method.)*

> **Gap flagged:** the article reports results on **22 test sentences** with no comparison to any neural Romanian baseline. To be defensible it must (i) benchmark against Ruseti et al. (2020) and/or Náplava et al. (2018, 2021) and (ii) address the test-set size (see §9, and Dror et al. 2018 in §8).

---

## 3. Romanian NLP — closely related work and resources (must-cite)

**Resources the article uses operationally:**
- **Tufiș, Ion, Bărbu Mititelu, and Ștefănescu (2013)** — *The Romanian Wordnet in a Nutshell* (*LRE* 47(4)) — and the **RoWordNet Python API** (Dumitrescu et al., GitHub). Together these are the lexical resource behind **Strategy B.1**. *Caveat (per conflict audit C-4): the article body says generically "WordNet synsets"; the Romanian (RoWordNet) attribution is inferred from the project's `diac_rowordnet` module. The author should confirm RoWordNet vs. English WordNet and name it explicitly.*
- **van Paridon and Thompson (2021)** — *subs2vec* (*Behavior Research Methods* 53). The Romanian OpenSubtitles n-gram source for **Strategy B.4**.
- **Speer (2022)** — *wordfreq* (software). Frequency database for **Strategy B.3**. *Currency caveat (per review P5): wordfreq was frozen by its maintainer in 2021 over generative-AI text contamination; cite as a 2021-era frozen snapshot, not a current frequency authority.*
- **Lison and Tiedemann (2016)** — *OpenSubtitles2016* (LREC). The corpus upstream of subs2vec. *Background/transitive dependency — the article uses subs2vec's n-grams, not OpenSubtitles directly.*

**Adjacent Romanian models (comparison baselines — not drop-in backbones):**
- **Dumitrescu, Avram, and Pyysalo (2020)** — *The Birth of Romanian BERT* — and **Masala, Ruseti, and Dascalu (2020)** — *RoBERT*. These are **encoder** models; they are valid **task baselines** (fine-tune-and-label diacritics) but **not** generative backbones you can swap in where LLaMA 3.2 generates restored text. *(Re-scoped per review P3 — the original draft mis-cast them as alternative "backbones.")*
- **Masala et al. (2024)** — *"Vorbești Românește?"* (Findings of EMNLP 2024; arXiv:2406.18266). Open Romanian-tuned **generative** LLMs (RoLLMs) — the genuine alternative *backbone* to LLaMA 3.2 and the centerpiece of the backbone-choice question below.

> **Gap flagged:** the article runs (English-centric) LLaMA 3.2 on a Romanian task without (i) naming the exact LLaMA 3.2 checkpoint (1B/3B, base/instruct) or (ii) justifying the choice against Romanian-tuned generative LLMs (RoLLMs). Both should be addressed.

---

## 4. Ensemble learning and voting — methodological core (must-cite)

- **Hansen and Salamon (1990)** — *Neural Network Ensembles*. The original "voting over models reduces error"; direct ancestor of agent voting.
- **Krogh and Vedelsby (1995)** — *Neural Network Ensembles, Cross Validation, and Active Learning*. **[Added per review.]** The **ambiguity / bias–variance–covariance decomposition** — the actual formal statement of *why diversity reduces ensemble error*. This, not bagging/boosting, is the load-bearing theory for "individual excellence ≠ collective intelligence."
- **Kuncheva and Whitaker (2003)** — *Measures of Diversity in Classifier Ensembles*. **[Added per review.]** Shows the **diversity–accuracy relationship is weak and measure-dependent**. Cited deliberately to keep the article's diversity claim *honest*: diversity does **not** guarantee that a more-diverse-but-individually-weaker ensemble beats a less-diverse-but-stronger one.
- **Breiman (1996)** — *Bagging*; **Breiman (2001)** — *Random Forests*; **Freund and Schapire (1997)** — *AdaBoost*; **Wolpert (1992)** — *Stacked Generalization*. The classical aggregation/combination tradition (variance reduction, randomized diversity, boosting, learned combiners) — context for the brute-force ensemble-selection step.
- **Kuncheva (2014)** — *Combining Pattern Classifiers* (book). Reference text on **majority/plurality/weighted voting** — the article's exact mechanism.
- **Zhou (2012)** — *Ensemble Methods* (book). The "**many could be better than all**" *selective-pruning* result — related to, but narrower than, the article's claim; cite precisely.
- **Condorcet (1785)** — *Jury Theorem*. Why majority voting among better-than-chance voters improves accuracy.

> **Recommendation:** ground the "complementarity over individual excellence" claim in **Krogh and Vedelsby (1995)** for the mechanism and **Kuncheva and Whitaker (2003)** for the honest caveat that diversity does not monotonically predict gain. Do **not** present diversity theory as *predicting* the article's reversal — it does not; the reversal remains an n=22 hypothesis (see §9).

---

## 5. Reinforcement learning, evolution, and agent economies (must-cite)

- **Sutton and Barto (2018)** — *Reinforcement Learning: An Introduction*. Reward shaping, credit assignment, exploration/exploitation.
- **Holland (1992)** — *Adaptation in Natural and Artificial Systems*. Genetic algorithms **and classifier systems with bucket-brigade credit assignment** — the closest classical home for the article's "agents earn to survive."
- **Goldberg (1989)** — *Genetic Algorithms in Search, Optimization, and Machine Learning*. **Fitness-proportional selection** — which is, mathematically, what the article's "share of squared accuracy" reward allocation *is*.
- **Eiben and Smith (2015)** — *Introduction to Evolutionary Computing*. Mutation operators with **parameter-specific perturbation scales** (the article's σ = 0.1 / 0.05 / 0.2).
- **Baum (2000)** — *Toward a Model of Intelligence as an Economy of Agents* (the **Hayek Machine**). The nearest precedent for an *agent-economy* framing — a population that survives on earned reward. **Caveat (per review P1): the mapping is an analogy, not a structural identity.** In Baum's model agents *transact with one another* via endogenous prices and conserved internal currency; the article instead distributes a **fixed exogenous aggregate reward** top-down by proportional share, with no inter-agent market. Cite Baum as agent-economy *inspiration*; ground the actual mechanism in fitness-proportional selection (Goldberg 1989; Holland 1992) and RL credit assignment (Sutton & Barto 2018). Claim a "Hayek economy" only if the model adds genuine inter-agent transactions.
- **Tesfatsion (2006)** — *Agent-Based Computational Economics* (Handbook, Vol. 2). Situates survival-of-profitable-agents in economics.
- **Stanley and Miikkulainen (2002)** — *NEAT*. Neuroevolution; precedent for *evolving* agent configurations rather than gradient-training them.
- **Bergstra and Bengio (2012)** — *Random Search for Hyper-Parameter Optimization*. *Background:* a baseline an evolutionary search could be compared against — but the article does **not** currently run that comparison, so cite as motivation only, not as a benchmark the article beats.

---

## 6. LLMs, prompting, tool use, and LLM ensembles (must-cite)

- **Touvron et al. (2023)** — *LLaMA* — and **Llama Team (2024)** — *The Llama 3 Herd of Models* (covers the **3.x line incl. 3.2**). Model provenance; the manuscript must still name the exact checkpoint.
- **Brown et al. (2020)** — *Language Models Are Few-Shot Learners* (GPT-3). The one-shot/in-context paradigm whose **unreliability the article opens by criticizing**.
- **Wang et al. (2023)** — *Self-Consistency*. **Majority vote over sampled outputs of one model** — the single-model analogue of the article's cross-agent voting; an important contrast (the article votes across *differently-tuned* agents, not samples of one).
- **Jiang, Ren, and Lin (2023)** — *LLM-Blender*. Ensembling **heterogeneous** LLMs via ranking + fusion; the closest "ensemble of LLMs" baseline (voting vs. learned fusion).
- **Li et al. (2024)** — *More Agents Is All You Need*. Sampling-and-voting ("Agent Forest") shows accuracy **scales with agent count** — the strongest contemporaneous parallel; **must be cited and differentiated** (the article adds tool-augmentation diversity and evolutionary selection on top of voting).
- **Schick et al. (2023)** — *Toolformer*. Deciding **when to call a tool vs. self-rely** — exactly the article's `use_tools` / confidence-threshold gate.
- **Yao et al. (2023)** — *ReAct*. The reasoning-plus-acting agent paradigm.

---

## 7. Lexical and n-gram foundations (supporting)

- **Miller (1995)** — *WordNet* — and **Fellbaum (1998)** (ed.) — *WordNet*. Origin of the synset abstraction (Strategy B.1); RoWordNet is the Romanian instantiation.
- **Jurafsky and Martin (2024)** — *Speech and Language Processing* (3rd ed. draft). n-gram language models and smoothing behind Strategy B.4.

---

## 8. Evaluation methodology (added per review)

- **Dror, Baumer, Shlomov, and Reichart (2018)** — *The Hitchhiker's Guide to Testing Statistical Significance in NLP* (ACL). **[Added per review.]** Provides the significance-testing protocol the article needs: its §3.8 asserts "22 test sentences … sufficient statistical power for reliable conclusions," a claim no cited source supports and that this reference directly contradicts. The author should run an appropriate test (or bootstrap) and **retract the "sufficient statistical power" sentence**.

---

## 9. Review findings and resolutions (adversarial + conflict audit, 2026-05-29)

Both reviews were run over the 48-source set, the review prose, and the article.

**Resolved in this revision:**

| ID | Finding | Severity | Resolution applied |
|----|---------|----------|--------------------|
| C-1 | Original draft said the ensemble "beat individually stronger agents" / led with "95.5%" — the article shows accuracy only **tied** the best individual (83.5%); the real win is **cross-ensemble**. | **Blocking** | §1 rewritten to state the matched-accuracy / cross-ensemble result precisely. |
| P1 | Baum "Hayek Machine" sold as a **structural** identity and "primary" cite. | Major | §5 softened to analogy; mechanism re-grounded in fitness-proportional selection (Goldberg/Holland). |
| P2 | "Diversity theory grounds the reversal" — it does not. | Major | §4 adds Krogh & Vedelsby (1995) and Kuncheva & Whitaker (2003); claim re-scoped as honest, reversal demoted to hypothesis. |
| P3 | RoBERT / Romanian BERT mis-cast as alternative **backbones**. | Major | §3 re-labels them as encoder **baselines**; RoLLMs kept as the generative backbone. |
| P4 | Coverage gaps: diversity theory, BERT-era restoration, significance testing. | Major | Added Krogh & Vedelsby 1995, Kuncheva & Whitaker 2003, Náplava et al. 2021, Dror et al. 2018. |
| P5 | wordfreq freeze; Lison/Bergstra over-promoted. | Minor | Currency caveat added to wordfreq; Lison 2016 and Bergstra 2012 demoted to background. |
| P7 / B-1 | Review read as descriptive though the article cites nothing; `[verified]` tag conflated "metadata-checked" with "used by the article." | Major | Header re-framed as **prescriptive**; provenance note clarified (DOIs verified ≠ article-grounded). |
| C-4 | B.1 source: article says generic "WordNet"; RoWordNet inferred from code. | Minor | §3 caveat added; author to confirm. |

**Open issues the author must still resolve (not fixable in the bibliography):**

1. **Wire citations into the manuscript** — it currently has none (P7).
2. **Statistical power** — retract "22 sentences provide sufficient statistical power"; add a significance test (Dror et al. 2018) (C-2).
3. **Test-set selection** — the headline 83.5/79.7 figures appear to come from ensemble selection performed on `D_test`; clarify the held-out protocol or temper the claims.
4. **Name the LLaMA 3.2 checkpoint** and justify it against RoLLMs (P3).
5. **Confirm RoWordNet vs. English WordNet** for Strategy B.1 (C-4).

**Minor/cosmetic (no action required):** arXiv DOIs on `@inproceedings` NeurIPS/ICLR entries resolve to the preprint, not the venue — documented in each `note` (A-1); `grattafiori2024llama3` citekey vs. corporate `{Llama Team}` author is a non-rendered key choice (A-3).

---

## References

See [`references/bibliography.bib`](references/bibliography.bib) for complete BibTeX entries (**48 sources**, every entry with a DOI or reliable canonical link). Inline citations above use Chicago author–date keyed to that file.
