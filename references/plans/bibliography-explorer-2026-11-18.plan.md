# Plan: bibliography explorer (2026-11-18)

Operator request (2026-11-18, relayed by the OrthodoxLLM session): a bibliography explorer whose reusable
part is developed and stored in researchteam and integrated by OrthodoxLLM into its figures application.
Navigation: period → author → brief bio with attributes, the sources used for the bio and the author's
sources → source detail (complete citation, summary, other attributes).

Division of work, agreed between the two sessions:

- **researchteam:** the data contract, the exporter (BibTeX plus generic CSV/JSON inputs → one explorer
  file, Chicago citations rendered and the contract validated in Python), the display component, an
  example with invented data, and tests.
- **OrthodoxLLM:** mapping its files into the input tables, the bios and summaries, integration as a tab,
  and verification. It receives the component by vendor-copy at a pinned commit.

Constraints: no project data in this repository; stdlib-only Python; no npm and no third-party JavaScript;
all displayed text inserted as text; provenance and verification state always shown.

1. **Contract.** Draft `templates/bibliography-explorer/CONTRACT.md`; the OrthodoxLLM session checks it
   against its files; revise until agreed.
2. **Exporter.** `scripts/build_bibliography_explorer.py`: BibTeX parser, Chicago renderer, input readers,
   validation, deterministic output, report. Tests under `tests/`.
3. **Component.** `templates/bibliography-explorer/`: ES module, stylesheet, example page and invented
   example inputs with their exported file.
4. **Vendoring record.** A file list with SHA-256 hashes and a README on how to vendor and pin.
5. **Review and merge.** `@code-hygiene` on the code, `@conflict-auditor` to close; PR to `main`, both test
   checks green, merged under PS-2. The PR touches no workflow, agent file or pin.
6. **Handoff.** Send the merge commit to the OrthodoxLLM session; record the session in `workSummaries/`.

Steps: `bibliography-explorer-2026-11-18.steps.csv`.
