# Concept map: intake of a handed-over branch (2026-11-23)

A derived project's session wrote a concept-map feature for researchteam (template, exporter, protocol, skill,
tests) and handed it over as a git bundle, routed through the managing repository's coordinator. This session, as
researchteam's lead, checks it, publishes it and takes it to a merge decision.

## Steps

1. Check the bundle's hash and head; import it into a separate worktree.
2. Run the concept-map tests, the full suite and the repository validation.
3. Reviews before publication: `@security` (publication, exporter, component, synced doc) and `@code-hygiene`.
4. Operator ruling on the private project details in the branch (PS-1).
5. Reword the two commits as ruled; fix the reviews' blocking findings in a third commit.
6. Push `feat/concept-map` and open the pull request.
7. `@security` re-check of the fixes, and `@conflict-auditor`, on the pull request's head.
8. Operator's merge decision for that head (PS-2); merge commit; check `main`.
9. Tell the handing-over session the pull request number and the merged commit, so it can re-pin.

## Rulings and results

- Operator, 2026-11-23 (picker): "Rewrite before push". The files and the first commit message were generalised
  before anything was pushed, so the handed-over head is not in this repository's history.
- `@security`: CONDITIONAL PASS. Condition 1 (operator review or generalise) met by the rewrite. Condition 2
  (exporter must not delete or overwrite inputs or files it did not write) fixed in the third commit.
- `@code-hygiene`: three blocking findings (a "clean build" claim the code did not enforce; a single band lost its
  label; the skill's ownership), all fixed. The advisory findings not fixed are listed in pull request #247.
- Tests on the pushed head: 1047 passed, 2 skipped, with Graphviz and Node present.

## Follow-up: CI runs the concept-map tests (pull request #250)

Operator decision, 2026-11-23, relayed by the handing-over session and confirmed by the operator's merge answer in
this session: CI should install Graphviz and have Node, so the layout tests and the component test stop skipping.

- `tests.yml` installs Graphviz from the runner's Ubuntu archive and checks for Node 20 or later; the step fails
  when either is missing. No action was added: Node is the runner image's own.
- S-10: the installed version was read from the first green run, and the vulnerability search is recorded beside
  the step. One open advisory, of low priority, was found and accepted by `@security` for this use.
- `@security` PASS naming `.github/workflows/tests.yml` at the merged head. Merged as `fdf0fb6`; `main` is green.
- One comparison still skips by design: the example's layout, byte for byte, when the runner's Graphviz differs
  from the version that made the example.
