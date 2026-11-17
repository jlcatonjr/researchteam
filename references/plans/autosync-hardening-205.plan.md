# Autosync and workflow-sync hardening (#205)

**Date:** 2026-11-17. **Release:** the next 1.1.x. The fleet's pin coordinator relayed an operator ruling
(R27, 2026-11-17): build and review now, cut the tag only after the fleet's v1.1.8 move is complete. This
session has not seen that ruling recorded; the build is reversible and the cut stays with the operator.

Seven items, from this repository's `@security` reviews of #182 and from derived repositories on v1.1.8:

| # | Item | Decision |
|---|---|---|
| 1 | `open_pr` accepts a 7 to 40 hex `new_sha` | require exactly 40; the gate always emits a full id |
| 2 | A name ending in line breaks is trimmed before the count | count from the listing with `tr` and `wc -l` |
| 3 | The branch may move between the two jobs | documented, not refused: a later move cannot be ruled out by a check in `open_pr`, and the PR's own diff is against the real base |
| 4 | `inputs.force` is written into the gate step's script | passed through `env:` with the event name |
| 5 | The gate job can write Actions caches | no code fix exists (a job cannot drop the runtime token); the update policy now states the rule: a workflow with a write token or a secret restores no cache |
| 6 | `workflow-sync` with no input applies nothing without saying why | says so on stderr and names `--yes`; exit 1 as before |
| 7 | `--check-only` under the system Python fails with an unclear error | the error names the interpreter and says to use the project environment |

Reviews: `@security` naming both workflow paths, `@code-hygiene`, `@conflict-auditor`. After the merge, one
`workflow_dispatch` run with `force=true` in this repository, as for #182.
