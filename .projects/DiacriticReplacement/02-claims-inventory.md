# Claims Inventory

**Source:** `UsingReinforcementLearningWithEnsembleVotingForRomanianDiacriticReplacement.html` (Ingrid M. Caton)
**Compiled:** 2026-05-29
**Purpose:** Enumerate every assertion in the manuscript so each can be run through the adversarial (presupposition) and conflict (consistency/evidence) audits, and the manuscript revised accordingly.

Claim types: **EMP** = empirical/quantitative result · **MOT** = motivating/background assertion · **METH** = method description/design choice · **INT** = interpretive/causal conclusion.

---

## §1 Introduction / motivation

| ID | Type | Claim (as stated) |
|----|------|-------------------|
| C1 | MOT | LLMs have "surprised both the public and researchers with their efficacy." |
| C2 | MOT | LLM performance "in the context of one-shot prompts is often inconsistent." |
| C3 | MOT | "One-shot prompting has failed to systematically resolve the problem with regard to diacritic restoration." |
| C4 | MOT | There exists a set of words "for which one-shot queries struggle to break the 80% mark." |
| C5 | MOT | "High quality LLMs are especially costly to … instantiate and execute." |
| C6 | MOT | LLMs "are not trained for the specific task of diacritic placement"; even fine-tuned LLMs "will suffer from persistent blind spots." |
| C7 | MOT | Tools employing advanced methods can augment agents, but "have not yet solved the problem"; tools alone do not solve restoration. |
| C8 | MOT | RL "can … improve the accuracy of diacritic placement, but blind spots will still persist." |
| C9 | INT | A composite approach "improves the performance of individual [agents] and also improves performance by combining methods." |
| C10 | METH | Tool-using agents "can decide between using the prediction provided by their tool or … their own judgment." |
| C11 | METH | Selecting agents that perform best on new data is biased (their training data resembles test features); instead select top performers from each training group. |
| C12 | METH | They compare accuracy over "every possible combination of ensemble agents selected from different rounds" and pick the highest-accuracy group as the final tool. |

## §2 Method

| ID | Type | Claim (as stated) |
|----|------|-------------------|
| C13 | METH | All agents are parameterized by LLaMA 3.2 query params: temperature, max_tokens, top_p, frequency_penalty, presence_penalty. |
| C14 | METH | Agents also carry strategy params: use_tools, analysis_weight_{synset,phonetic,frequency}, analysis_confidence_threshold, strategy_aggression, prefer_common_patterns, conservative_threshold, aggressive_threshold. |
| C15 | METH | "The strategy selection mechanism is governed by **ten** distinct parameters that are evolved through reinforcement learning." |
| C16 | METH | Strategy vector **s** = ⟨u_t, w_s, w_p, w_f, w_c, θ_c, α, φ_p, φ_c, τ_con, τ_agg⟩ (**11 components**). |
| C17 | METH | Two strategy classes: A = direct LLM inference (u_t=0); B = tool-augmented (u_t=1). |
| C18 | METH | In Class B, "tool recommendations inform but do not override the LLM's final judgment." |
| C19 | METH | B.1 synset score uses WordNet synsets; base scores "typically 0.8 for unique synset holders, 0.6 for contested variants." |
| C20 | METH | B.2 phonetic rules: 'si'→'și','ca'→'că','in'→'în' weights 0.9–0.95; î/â positional weight 0.6; morphological endings 0.6; conservative defaults 0.1–0.4. |
| C21 | METH | B.3 frequency uses the wordfreq library; thresholds freq>1e-4→0.85, >1e-5→0.70, >1e-6→0.55, rare→0.30; ratio>5.0 boosts 20%, ratio<2.0 reduces 15%; φ_p=0 → 85% of base confidence. |
| C22 | METH | B.4 contextual n-gram uses subs2vec / Romanian OpenSubtitles; loads "over 1 million n-grams"; λ "typically 0.7." |
| C23 | METH | Combined score is a weighted sum of the four strategy scores; v* = argmax combined_score. |
| C24 | METH | Three-tier confidence decision; τ_agg = (1−α)×0.5+0.1, so α→1 ⇒ τ_agg→0.1, α→0 ⇒ τ_agg→0.6. |
| C25 | METH | Mutation: per-parameter rate μ=0.10; σ=0.1 (weights), 0.05 (thresholds), 0.2 (behavioral); τ_con<τ_agg maintained by sequential clipping. |
| C26 | METH | Strategy space is "2⁴ × ℝ⁷", reduced to "≈ 2⁴ × 10⁷" discrete combinations at 3-decimal discretization. |
| C27 | METH | Economic RL: each agent incurs a fixed marginal cost per period; must earn reward > cost to survive; fixed aggregate reward divided by relative performance. |
| C28 | METH | Reward allocated by **squared** accuracy share (to give increasing returns to accuracy). |
| C29 | METH | Time-efficiency reward ∝ squared (T_max − T_i); zero accuracy ⇒ zero efficiency reward. |
| C30 | METH | Total reward split into four equal parts (accuracy, target-accuracy, efficiency, target-efficiency). |
| C31 | METH | Population control: R₀=N₀; R_t = R₀/(t+1) while R_t>R*. |
| C32 | METH | Agents trained over **three generations**; ranked by avg accuracy (tie-break: target-word accuracy); fixed number of top performers selected per generation. |
| C33 | INT | Selecting top performers from *each* generation "integrate[s] diverse perspectives" and avoids over-selecting from the easy generation. |
| C34 | METH | Three independent partitions D_train, D_test, D_ensemble "ensuring complete data independence across evaluation phases." |
| C35 | METH | Brute-force ensemble optimization: evaluate all C(M,K) combinations; E* = argmax ensemble_accuracy(E, **D_test**); generation-balanced constraint. |
| C36 | METH | Position-wise word-level majority voting; handles variable-length predictions via dynamic padding. |
| C37 | METH | Final validation of E* on isolated D_ensemble gives "unbiased assessment of ensemble generalization." |

## §3 Experimental results

| ID | Type | Claim (as stated) |
|----|------|-------------------|
| C38 | EMP | Two configs: Tool-Enhanced (pool of 6 tool + 3 non-tool agents) and Direct Inference (9 Class-A agents). |
| C39 | METH | Each *ensemble* = 3 agents via generation-balanced optimization; final members named (Tool: 398/433/78; Direct: 181/333/428). |
| C40 | EMP | Tool-enhanced **pool** (9): avg train acc 82.2% (70.5–88.3), word rest 35.4% (16.7–45.5); best Agent_435 88.3%/36.4%. |
| C41 | EMP | Direct **pool** (9): avg train acc 83.6% (77.7–89.6), word rest 44.1% (27.3–54.5); best Agent_436 89.6%/54.5%. |
| C42 | EMP | Training: direct higher avg accuracy (83.6 vs 82.2) and "significantly superior" word restoration (44.1 vs 35.4). |
| C43 | EMP | Individual test (selected, tool-enhanced): avg 84.6%; best individual Agent_405 (not selected) 98.4%/90.9%; selected 433=95.8/90.9, 398=93.6/86.4, 78=58.2/13.6. |
| C44 | EMP | Individual test (selected, direct): avg 97.6%; best Agent_74 (not selected) 98.9%/100%; selected 428=98.1/95.5, 181=97.9/100, 333=97.4/90.9. |
| C45 | INT | Direct inference shows "superior generalization to unseen test data" (97.6 vs 84.6 selected-avg accuracy). |
| C46 | EMP | Final tool-enhanced ensemble: 83.5% acc / 95.5% word rest; "matched best individual agent (Agent_398: 83.5%)" in accuracy, +45.5 pp word restoration. |
| C47 | EMP | Final direct ensemble: 79.7% acc / 81.8% word rest; "underperformed best individual (Agent_181: 82.5%)" by 2.8 pp acc, +59.1 pp word restoration. |
| C48 | INT | "Critical Performance Reversal": tool-enhanced ensemble beat direct ensemble on both acc (83.5 vs 79.7) and word rest (95.5 vs 81.8) despite weaker individuals ⇒ tool augmentation gives complementary decision-making. |
| C49 | INT | Ensemble voting "particularly benefits word restoration"; both ensembles improved word restoration over constituents. |
| C50 | INT | "Selection vs. Performance Paradox": ensemble effectiveness "depends on agent complementarity rather than individual excellence." |
| C51 | EMP | "The experiments were conducted on **22 test sentences** for each phase, providing **sufficient statistical power for reliable conclusions**." |
| C52 | EMP | Summary table (§3.8) values across Training / Individual Testing / Ensemble Voting phases. |
| C53 | INT | §3.9 implications: (a) individual excellence ≠ collective intelligence; (b) tool augmentation benefits; (c) word-restoration efficacy of voting; (d) complementarity over competition. |
| C54 | INT | For practical Romanian diacritic restoration, "tool-enhanced ensemble voting provides superior performance." |

---

**Total: 54 enumerated claims** (12 motivation, 25 method, 11 empirical, 6 interpretive). The audits below assess each for unsupported assertion, internal inconsistency, evidence mismatch, and overstated presupposition.
