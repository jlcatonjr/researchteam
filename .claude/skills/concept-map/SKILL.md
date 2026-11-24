---
name: concept-map
description: Draw, audit and publish a concept map of a debate (who affirms or denies which claim, and how views developed) with the researchteam concept-map exporter and component. Use when asked for a reception map, a map of positions or perspectives, or to make such a graph interactive in an explorer page.
---

# /concept-map

Follow `docs/concept-map-protocol.md`; the data shapes are in `templates/concept-map/CONTRACT.md`.

1. **Scope.** Write down the question, the research files the map may draw on, the bands and the three
   vocabularies. Always include an `inferred` relation, and say what fill means.
2. **Draft** `figures/<map>.json` from the project's brief alone and build it:
   `python3 scripts/build_concept_map.py figures/<map>.json --registry <explorer-data.json> --out <host>/concept-map-data.json --dot figures/<map>.dot --svg figures/<map>.svg --report <dir>/build-report.txt`.
   Keep v1 as `<map>.v1.*`.
3. **Persons.** Give each actor node its register ids and never guess one from a name. Mark the rest
   `unregistered`, with a reason. Settle every REVIEW line in the report with `only` or `all_members: true`, or
   carry it to the residuals.
4. **Round 1.** Spawn `@technical-validator` (read-only) with the SVG, the spec and the research files, and no list
   of suspected faults. Ask for findings with severity, file:line evidence and a proposed change.
5. **Round 2.** Check each major finding against the cited lines before acting, and record Accepted / Accepted in
   part / Rejected.
6. **Revise** to v2, then do the **second pass** against the protocol's checklist (section 5).
7. **Log** everything in `figures/<map>.audit.md`: how the audit was run, findings and dispositions, second pass,
   residuals, later updates. The status stays UNVERIFIED.
8. **Integrate.** Vendor the component and exporter at a pinned commit (`templates/concept-map/README.md`). Wire the
   host so `onSelect` lists the actor's persons, or a topic's `membersByRelation` groups, in the host's own
   drill-down panel. Run the project's gates.

Never edit the generated DOT, SVG or map file. Edit the spec and rebuild.
