# Concept-map protocol

How a project draws, audits and publishes a **concept map**: a figure of how views of a question developed,
divided and converged, with each writer tied to the claims and findings they affirm or deny. The data shapes are
in `templates/concept-map/CONTRACT.md`; the exporter is `scripts/build_concept_map.py`; the component is
`templates/concept-map/concept-map.js`. This protocol is the procedure around them: who drafts, who audits, what
is checked, and what is written down.

It generalises the process first used for a reception map in a derived project. There, an independent audit of the
first draft returned findings that changed the map. The checklist in section 5 is drawn from those findings.

## 1. When to use it

Use a concept map when a deliverable argues about **reception or debate**: who held which view, who answered whom,
and where the project's own findings stand. Do not use it for a chronology (use a timeline), for counts (use a
chart) or for a citation network.

A map is a summary of the project's research files, not a new source. Every node and line must trace to those
files (rule 1 of `CLAUDE.md`). A line with no documented influence is drawn as inferred (section 3, step 1).

## 2. Roles

| Step | Agent (default team) | Does |
|---|---|---|
| Scope, sources, vocabulary | `@orchestrator` with the project's workstream expert | fixes the question, the files the map may draw on, the bands and the vocabularies |
| Draft and revise the spec | `@visual-designer` (or `@primary-producer`) | writes `figures/<map>.json`; builds; reads the report |
| Tie persons | `@reference-manager` | gives each actor node its person ids from the register; marks the unregistered; settles group edges |
| Round 1 audit | `@technical-validator`, read-only, **independent** | audits the draft against the research files, with no list of suspected faults |
| Round 2 check | `@conflict-resolution` | checks each finding against the lines it cites before anything changes; decides ACCEPT / REJECT / REVISE |
| Second pass | `@quality-auditor` | re-checks the revised map label by label against the same files |
| Presuppositions (optional) | `@adversarial` | asks what the map assumes: periods, parties, the direction of "influence" |
| Integration | `@visual-designer` | vendors the component and the exporter; wires the host page |

The drafter never audits their own map. The round-1 auditor sees the map and the files, not the drafter's notes,
so their findings are not anchored on the draft's reasoning.

## 3. Steps

1. **Scope.** Write down:
   - the question the map answers;
   - the research files it may draw on, and nothing else;
   - the bands, usually periods;
   - the three vocabularies (`node_kinds`, `fills`, `relations`), each term with a one-line definition.

   Always include a relation for links that are **inferred or parallel only** (`inferred: true`, drawn dotted).
   State what fill means (for example "confession *at the time of writing*") and put it in `legend_note`.
2. **Draft v1** from the project's own brief or report alone. Save it as `figures/<map>.json` and build it
   (section 4). Keep the v1 spec and SVG under `<map>.v1.*` as the audit record.
3. **Tie persons.** Every actor node lists its persons by register id, normally the bibliography explorer's file,
   passed with `--registry`. A writer with no entry is listed as `unregistered`, with the reason. Never guess an
   id from a name. A group node lists everyone its label names.
4. **Settle group edges.** The build report lists under REVIEW every line from a group node that does not say whom it
   speaks for. For each one, read the line's label and its sources:
   - if it speaks for some members only (a quotation from one of them, say), give `only`;
   - if it holds for every member, give `all_members: true`;
   - if it rests on someone *outside* the box, it stays under REVIEW and goes to the residuals.

   A clean build has no REVIEW line that has not been judged.
5. **Round 1: independent audit.** Give the validator the SVG, the spec and the research files. Ask for findings,
   each with a severity (major or minor), the evidence (file and line) and a proposed change. Give no list of
   suspected faults.
6. **Round 2: check before acting.** For each major finding, read the cited lines. Record a disposition: Accepted,
   Accepted in part (say which part) or Rejected (say why, with evidence). A finding is not acted on until it has
   been checked.
7. **Revise to v2.** Edit the spec, rebuild, and keep v1.
8. **Second pass.** Re-check every node label, line label, date, person tie and group edge of v2 against the same
   files. Use the checklist in section 5.
9. **Write the audit log**, `figures/<map>.audit.md`, with these sections:
   1. how the audit was run;
   2. the findings and their dispositions, in a table;
   3. the second pass;
   4. residual items not resolved;
   5. later updates, dated.

   The map's `notice` and `status` stay UNVERIFIED until a person has reviewed it.
10. **Integrate and gate.** Vendor the component and exporter (`templates/concept-map/README.md`) and wire the host
    page so a click lists the people in the host's own drill-down. Run the project's gates for the deliverable the
    map serves: the citation audit, and, where the project has them, its rules for characterising people and its history checks.

## 4. Commands

```bash
python3 scripts/build_concept_map.py figures/<map>.json \
    --registry <explorer-data.json> \
    --out <host>/concept-map-data.json --dot figures/<map>.dot --svg figures/<map>.svg \
    --report <dir>/build-report.txt
```

A project wraps this in one script that runs from any directory, kept beside the spec (for example
`Projects/<project>/analysis/concept-map/run_map.sh`). Graphviz (`dot`) must be installed. The DOT and SVG are
outputs: do not edit them.

## 5. Audit checklist

Each item below generalises one or more findings of the first audit.

- **Direction in time.** Does every "answers", "rebuts" or "develops" line run from the earlier writer to the later?
- **Documented or inferred?** Is each solid line's influence documented in a file? If it rests on a title, on
  general knowledge or on a resemblance, draw it as inferred.
- **One claim per node.** Is any node merging separable claims (date, dependence, pseudonymity, forgery)? Split it.
- **Coverage.** Are the early reception, the first doubts, each camp's defenders and critics, and the project's
  own conclusion all on the map? A missing side reads as consensus.
- **Reported or own words.** Is a position drawn from a writer's own text or from a later report of it? Say
  "reported" in the label, or draw the report as its own node.
- **Identity at the time.** Does the fill or label give confession, school or office at the time of writing, not
  at death?
- **Dates.** Does each node sit in the band its date puts it in? Mark undated nodes "n.d."
- **Groups.** Does each group line speak for all its members (step 4)? Is anyone named on a line missing from the
  box, or anyone in the box contradicted by their own node elsewhere on the map?
- **Quotations.** Is every quoted phrase verbatim in a file, with its locator?
- **Vocabulary rules.** Does any label break the project's rules for characterising people (for example
  a rule on how an author's standing may be described)?
- **Coding agreement.** Where the project codes positions (a cluster or survey frame), does the map agree with
  the coding? Record any disagreement as a residual. Do not silently re-code.

## 6. What a clean build and a clean audit mean

A clean build means the spec is well-formed and internally consistent. The build does not stop for an unregistered
person or an unjudged group line: it lists them in the report as warnings (the group lines as REVIEW). The map is
ready for audit only when the report has no REVIEW line and every unregistered person is accounted for. A clean audit means the two rounds and the second pass found nothing left to
change. Neither means the map is true. It stays an agent-drafted summary of the project's files, UNVERIFIED until
a person reviews it.
