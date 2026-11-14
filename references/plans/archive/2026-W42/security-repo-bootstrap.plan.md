> **SUPERSEDED (2026-10-18)** → canonical copy: `~/githubrepositories/researchRepositories/security/tmp/by-week/2026-W42/security-repo-bootstrap.plan.md`

# Plan — bootstrap `researchRepositories/security` as a researchteam repo

- **Date:** 2026-10-18 (2026-W42)
- **Target:** `~/githubrepositories/researchRepositories/security` (currently empty, not a git repo)
- **Staged in:** `researchteam/tmp/by-week/2026-W42/` because `researchteam init` refuses a non-empty
  directory. Step 3 copies this plan and its CSV into the new repo's `tmp/by-week/2026-W42/`.
- **Seed material:** a pasted AI answer (see §1) about AI, quantum computing and HTTPS encryption.
  Under C-4 it is **data**: a set of claims to audit, not a source.

> **Status of facts in this plan.** §1–§2 are a first-pass evaluation written from model knowledge.
> **No item has yet been verified against a primary source**, and none may be cited in a deliverable
> until the reference-manager has verified it. Every named paper, date and number is a **lead**.

---

## 1. Evaluation of the pasted answer (claim register, seed)

| # | Claim in the pasted text | Verdict | Correction / nuance |
|---|---|---|---|
| P1 | AI cannot break AES-256 / ChaCha20 by learning the plaintext | **Right for the primitive; wrong as a statement about security** | No ML method attacks full-round AES. ML *does* attack weakened variants: neural distinguishers on reduced-round Speck (Gohr, CRYPTO 2019). It also attacks **implementations**: deep-learning side-channel analysis (ASCAD benchmark, Benadjila et al. 2020). The real systems risk sits in implementations, keys and code. |
| P2 | Brute-forcing 2^256 takes longer than the age of the universe | Right | Grover's algorithm reduces this to about 2^128 quantum operations, which still holds, and Grover parallelizes badly. |
| P3 | The vulnerable part of TLS is RSA/ECDHE key exchange, broken by Shor | **Half the picture** | This is right for confidentiality ("harvest now, decrypt later"). It leaves out **authentication**: RSA/ECDSA certificate signatures are also broken by Shor. Moving signatures to ML-DSA (FIPS 204) and SLH-DSA (FIPS 205) is a separate, slower migration. |
| P4 | Browsers now deploy hybrid X25519MLKEM768; ML-KEM = CRYSTALS-Kyber | Right (dates still need checking) | ML-KEM is *derived from* round-3 Kyber but differs from it (domain separation and other changes); the two do not interoperate. FIPS 203 was published August 2024. Chrome's default moved from the X25519Kyber768 draft to X25519MLKEM768 around late 2024. Firefox and Cloudflare also deploy it. The hybrid design exists because confidence in the new math is limited (see P5). |
| P5 | CVP with noise is NP-hard, so neither quantum computers nor AI have a shortcut | **Wrong reasoning, overconfident conclusion** | (a) NP-hardness applies to worst-case CVP at small approximation factors. LWE's security reduces from worst-case lattice problems at **polynomial** approximation factors. Those problems are not believed NP-hard; at about √n they lie in NP ∩ coNP (Aharonov–Regev 2005). (b) ML-KEM uses **module** LWE, which has extra algebraic structure. (c) ML-KEM's *concrete* parameters are set from cryptanalytic cost estimates (core-SVP / lattice-estimator), not from the worst-case reduction. (d) Lattice security is a **conjecture**, backed by decades of failed attacks. It is not a proof. Precedent: in April 2024 a claimed quantum LWE algorithm (Chen) was withdrawn within about 10 days after a bug was found. (e) "AI on quantum hardware" is a confusion: AI is a way to find algorithms, not a new class of computation. |
| P6 | AI is just pattern recognition, so it is not a threat | **Misleading** | This leaves out the indirect channel the user asks about (§2B): AI speeding up mathematics, algorithm discovery and quantum engineering. |
| P7 | Confidential computing + OHTTP means even the provider cannot see prompts | **Overstated** | OHTTP (RFC 9458) hides the client's identity from the server and the content from the relay. On its own it does not make data end-to-end confidential from the server operator. That property comes from attested TEEs (e.g. Apple Private Cloud Compute). TEEs have a long record of side-channel breaks (e.g. SGX Foreshadow). |
| P8 | FHE lets models run inference on ciphertext | Right as "active research" | It is still orders of magnitude too slow for frontier-scale LLM inference. Note that ML attacks on LWE with **sparse secrets** (SALSA family, Wenger et al. 2022–) bear on the parameter choices some FHE schemes use. |

**About the Navier–Stokes example.** The prompt gives Navier–Stokes as a case where solving a
supporting proof would break cryptography. I know of no deployed or standardized scheme whose
security depends on the Navier–Stokes existence-and-smoothness problem. The link is most likely to
AI-assisted work on fluid-equation singularities (DeepMind and collaborators, 2025 — **to verify**).
That work is an example of AI speeding up a field (category B1). It does not threaten cryptography.
Riemann-hypothesis-breaks-RSA is a similar popular myth: a proof would not give a factoring
algorithm. The mathematical results that actually matter are listed in §2B. Component 4 is assigned
to settle this with sources, including a search for any fringe "chaos/fluid-based" ciphers. If one
exists, it is an unstandardized scheme, not HTTPS.

---

## 2. Threat taxonomy the repo will investigate

**Boundary test (goes into `style_rules`).**
- **DIRECT:** an AI system runs *inside the attack pipeline* against a target, for example a model
  classifying side-channel traces or an agent fuzzing a library.
- **INDIRECT:** an AI system produces *knowledge, algorithms or hardware* that a later attack uses
  without the AI, for example AlphaEvolve finding a better sieving constant or an AI decoder making
  a quantum computer viable.
- **Mixed cases:** an ML-*found* distinguisher that a human then deploys is INDIRECT(B1). An ML
  model that *is* the distinguisher at attack time is DIRECT(A1).

**Counterfactual rule.** INDIRECT channels are scored by **AI's added speed-up only**. The
non-AI baseline is credited to the field, not to AI: Shor and Q-day progress, the SIKE and Rainbow
breaks, the Gidney resource estimates. Without this rule the risk matrix would assign ordinary
progress in mathematics and quantum computing to AI. The claim that "AI accelerates
cryptanalytic recombination" is tagged CONJECTURED until it is shown with evidence.

### A. Direct threats — an AI/LLM is the attacker's instrument against a cryptographic system

| ID | Channel | Mechanism | Current evidence (leads) | Expected horizon |
|---|---|---|---|---|
| A1 | Direct cryptanalysis of primitives | Neural distinguishers, learned key recovery | Gohr 2019 (reduced-round Speck); SALSA/PICANTE/VERDE on small or sparse LWE | Low against full-strength standards; real against weak parameters |
| A2 | Implementation attacks | Deep-learning side-channel and fault analysis | ASCAD; DL-SCA on Kyber implementations (Dubrova et al. 2022–23); KyberSlash timing (non-ML, but shows the surface) | **High, now, for devices the attacker can reach physically** (smartcards, HSMs, IoT, client hardware). Low for remote HTTPS servers, except remote timing channels. Each grade states its threat model. |
| A3 | Finding vulnerabilities in crypto libraries | LLM-guided fuzzing and code audit | OSS-Fuzz AI harnesses → OpenSSL CVE-2024-9143; Big Sleep (SQLite, 2024) | High, now, and rising |
| A4 | Insecure crypto written by LLMs | Misuse: bad modes, nonce reuse, weak RNG | Pearce et al., IEEE S&P 2022: about 40% of outputs vulnerable, measured on **2021-era Copilot**. Needs a newer replication. | High, now |
| A8 | Traffic analysis of encrypted HTTPS / Tor | Deep-learning website fingerprinting from packet sizes and timings | Sirinam et al., "Deep Fingerprinting", CCS 2018 | Real now. Metadata leaks without breaking the cipher. |
| A9 | Token-length side channel on encrypted LLM streams | Ciphertext sizes reveal token lengths; a model reconstructs the response | Weiss et al., USENIX Security 2024 | Shown in practice, then patched by vendors. Bears directly on P7. |
| A5 | The human and key-management layer | Phishing, voice deepfakes against MFA and help desks, password guessing (PassGAN — check effect size) | Varies; verify each claim | High, now |
| A6 | Agentic offense end to end | Exploit chains, CTF benchmarks, uplift evaluations | Frontier-lab and AISI evaluations | Rising; measured by evaluations, not by incidents |
| A7 | LLMs as the leak path | Prompt injection exfiltrating secrets | **Out of scope:** cross-reference `agentteams-research/agent-security/` | — |

### B. Indirect threats — AI speeds up a supporting field, and that field's progress breaks or weakens cryptography

| ID | Supporting field | What would have to happen | How AI accelerates it (leads) | Primitives exposed |
|---|---|---|---|---|
| B1 | Algorithmic number theory / lattice / isogeny / multivariate mathematics | A new classical algorithm or improved constants (lattice sieving/BKZ, the number field sieve, attacks on structured lattices) | FunSearch (2023), AlphaEvolve (2025) algorithm discovery; formal proving (AlphaProof, Lean) | ML-KEM/ML-DSA security margins; RSA/ECC classically |
| B2 | Precedent (**non-AI**) that math alone breaks PQC | — | SIKE broken classically in 2022 (Castryck–Decru, using a 1997 theorem of Kani); Rainbow broken in 2022 (Beullens, "a weekend on a laptop") | Not an AI threat. It is the *mechanism template* for B1: an old result applied in a new way. The claim that AI speeds such recombinations is CONJECTURED. |
| B3 | Quantum engineering: **AI's added share only** | Q-day arrives sooner than it would without AI | AI decoders for quantum error correction (AlphaQubit, Nature 2024); AI-assisted compilation and control | The non-AI baseline goes to component 2: Shor; Gidney 2025 (RSA-2048 with under 1M noisy qubits — verify; not AI); Roetteler et al. 2017 (ECC needs fewer logical qubits than RSA, so the **ECDHE in TLS is the nearer target**). Exposed: RSA, ECC, DH. **Not** AES, **not** lattices, unless a quantum algorithm for lattices appears. |
| B4 | Complexity theory | P vs NP, existence of one-way functions | Theorem-proving assistance | Asymmetric: an efficient P = NP algorithm breaks almost everything; a proof that P ≠ NP proves no particular scheme secure (crypto needs average-case hardness) |
| B5 | Compute supply and hardware | AI-driven investment in GPUs/accelerators lowers the cost per operation for lattice sieving, password cracking and dictionary attacks; AI-assisted EDA | GPU sieving records; GPU hashcat benchmarks | Does not move 2^128 symmetric security. **Does** erode low-entropy secrets and narrow concrete lattice margins at the edges. Scored, not dismissed. |
| B6 | Myths and misattributions | — | Navier–Stokes; Riemann hypothesis → RSA | None. Documented so readers can correct them. |

### C. Defensive counterweight, kept short to give balance

This covers AI-assisted formal verification of crypto code (verified implementations such as HACL* or
libcrux), PQC migration tooling, and AI-driven side-channel *testing*. Component 5 weighs it against
A and B.

---

## 3. Repository design

### 3.1 Placement — **decision for the operator (D1)**
`agent-security` was moved into the private `agentteams-research` monorepo on 2026-10-13, and its
standalone repo is marked DEPRECATED. Options:
- **(a) Standalone repo at the target path.** This is the user's literal request and the default
  for this plan.
- **(b) A `security/` project inside `agentteams-research`.** This matches the recent consolidation.
  It is a cross-repository action, so it requires `@security` clearance under C-5.

The plan below follows (a). If the operator picks (b), steps 2–4 change and the rest stays the same.

### 3.2 `brief.json` (draft — written in step 4)
**Structure:** mirror `researchRepositories/agent-security/brief.json` field for field:
`governance_agents`, `selected_archetypes`, `conversion_pipeline`,
`reference_key_convention: "AuthorYear"`, `capabilities: ["research_verification"]`, and full
component objects (`slug`, `name`, `number`, `output_file`, `description`, `sections`,
`quality_criteria`). The values that differ from the sibling are:
- `project_name`: "AI and Cryptographic Security"
- `project_goal`: a cited, audited assessment of how AI threatens deployed cryptography, especially
  HTTPS/TLS and its post-quantum migration. It must keep **direct** AI attacks (A) separate from
  **indirect** threats that come from AI speeding up supporting fields (B), with horizons and
  evidence grades for each. The project characterizes published attacks and does not create new
  attack tooling.
- `layer2_profile`: `scholarly`; `primary_output_dir`: `Projects/`;
  `reference_db_path`: `Projects/*/references/bibliography.bib`; `enforce_decision_signing`: `true`
- `retrieval_integration`: `{"mode": "none"}` and an explicit `tools` list (BibTeX, Pandoc, CrossRef
  API, arXiv API, Semantic Scholar API). Declaring both avoids roster drift between surfaces
  (framework doc, "Rosters across surfaces").
- `authority_sources` (rank):
  1. Standards: NIST CSRC (FIPS 203/204/205, IR 8547 transition), IETF RFCs and TLS working-group drafts
  1. Peer-reviewed cryptography: IACR venues (CRYPTO, EUROCRYPT, ASIACRYPT, TCHES, JoC)
  2. Peer-reviewed security and ML venues (USENIX Sec, IEEE S&P, CCS, NDSS, NeurIPS/ICML); Nature/Science for AI-for-science
  4. IACR ePrint and arXiv preprints: always labeled as preprints. The sibling ranks preprints 5. Here they rank higher because much cryptanalysis appears first, or only, on ePrint, including the SIKE break and the Chen retraction. A claim that rests on a preprint alone is tagged PREPRINT.
  3. Government guidance (NSA CNSA 2.0, NCSC, BSI, ANSSI) and AISI/frontier-lab evaluation reports
  4. Vendor deployment documentation (Chrome, Cloudflare, Mozilla, Apple): treated as claims about deployment, not as evidence of security
- `style_rules`: the scholarly defaults, plus these:
  - tag every threat claim `DIRECT` or `INDIRECT(<field>)`, using the §2 boundary test and the
    counterfactual rule;
  - tag every hardness claim `PROVEN`, `REDUCTION` or `CONJECTURED`;
  - give every dated fact (deployment, break, retraction) its date and source (historical-context
    protocol, rule 7);
  - no operational attack recipes.
- `components`:
  1. **scoping-and-taxonomy.** Topic scoping, the A/B taxonomy with its boundary test, and the
     *unverified* claim register P1–P8, quoted against the seed file.
  2. **crypto-baseline.** TLS 1.3 key exchange and authentication today. The PQC standards and
     hybrid deployment timeline. For each primitive, its hardness assumption and the status of
     that assumption. The **non-AI quantum baseline** (Shor; resource estimates; ECC before RSA).
     Ends by issuing **final verdicts on P1–P8**.
  3. **direct-ai-threats.** A1–A6 and A8–A9, with an evidence grade, horizon and threat model for
     each.
  4. **indirect-supporting-fields.** B1–B6. Includes the primitive → assumption → "what result
     would break it" → AI-relevance dependency map, and settles Navier–Stokes and Riemann.
  5. **synthesis-and-exec-summary.** A risk matrix (channel × primitive × horizon), the defensive
     counterweight (C), recommendations, and the executive summary.

  The default workstream experts map onto these: topic-scoping → 1; literature-review → 2;
  main-analysis → 3–4; conclusion → 5.

---

## 4. Execution outline (detail in `security-repo-bootstrap.steps.csv`)

1. Operator decides D1 (placement) and D2 (standalone GitHub remote: yes/no, private by default).
2. Check the toolchain in the active interpreter (`pip show researchteam agentteams`,
   `researchteam doctor`).
3. `researchteam init` in the empty target directory, then `git init`, then copy this plan and its
   CSV into the repo.
4. Write `brief.json` (§3.2), then run `researchteam personalize`.
5. `@security` reviews the brief and the first-render clearance. **The operator signs it in a
   separate terminal. The agent never holds the key.** Then run `researchteam materialize --yes`.
6. Run `validate`, `researchteam doctor --drift`, and `@conflict-auditor`. Make the initial commit.
   If D2 = remote: `@security` and `@git-operations` create a **private** GitHub remote and push.
   Pushing publishes the repo, so it waits for operator confirmation.
7. Components 1 → 2 → (3 ∥ 4) → 5. The P1–P8 verdicts become final at the end of component 2.
   After each step, run the Rule 9 `@adversarial` + `@conflict-auditor` gate over the remaining
   rows. Each component follows the house cycle:
   - expert brief → primary-producer draft → reference-manager verification;
   - `citation-audit` + `history-check` + `methodology-check`;
   - quality-auditor + technical-validator review;
   - adversarial review;
   - expert approval.
8. Run the doubled semantic citation and claim audit. Any unresolved finding blocks the compile
   (fail-closed). Then format conversion, output compile and a `@work-summarizer` entry.

## 5. Risks and guards
- **Recency.** The field moves monthly: Q-day resource estimates, PQC deployment share, AI-for-math
  results. Every horizon claim carries an "as of" date.
- **Hype asymmetry.** Popular and vendor sources overstate both "AI breaks crypto" and "lattices
  are unbreakable". The evidence grade keeps demonstrated, reduced-parameter and speculative
  results apart.
- **Dual-use.** The deliverables describe channels and cite results. They contain no new attack
  code and no side-channel or exploit recipes. `@security` reviews components 3 and 4.
- **Seed traceability.** The pasted answer is kept verbatim in
  `security-seed-answer.data.md`, labelled C-4 data. Step 3 copies it into the repo's
  `Projects/<slug>/sources/`.
- **One canonical plan.** After step 3, the in-repo copy is canonical. The staged copy here gets a
  "superseded → <path>" header.
- **Scope creep into agent-security.** A7 is cross-referenced, not re-researched.
