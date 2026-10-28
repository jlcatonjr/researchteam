# AgentTeams Update Policy

Date: 2026-05-20
Status: Active

## Purpose

Define review and rollback policy for automated AgentTeams synchronization runs using `--update --merge`.

## Integrated AgentTeams Baseline

**Integrated ref:** `7fd4de4` (agentteams `main`, 2026-10-04), recorded in
`.github/agentteams-autosync-ref`. The previously recorded ref was `f3a8b8c`; the narrative below
had stayed at `61849fb`. What changed, for a consumer of this framework:

1. **The branch lifecycle** (agentteams #101/#102). There is a new emitted
   `references/branch-lifecycle.reference.md`. `@git-operations` gains Invariant rule 8, a
   post-merge branch step, and the Output Contract fields `Branch disposition` and
   `Branch inventory`. `@cleanup` gains a weekly branch/stash/worktree sweep. The CLI gains
   `agentteams --branch-inventory | --branch-cleanup | --branch-post-merge`.
2. **The stale `references/git-procedures.md` citation is gone.** `--shrink-policy preserve` had
   pinned 20 sections here, because the guard treated references the template itself retired
   as enrichment. agentteams #103 adds reviewed, content-bound per-section overrides
   (`AGENTTEAMS_SHRINK_ALLOW`, with an `AGENTTEAMS_SHRINK_REPORT` review). This integration
   released 13 sections. In 11, every removed line was template-owned. In the other two (`cleanup` and `agent-updater`), the only non-template loss was the hand-enriched wording of one reference-database row ("project-local `references/bibliography.bib` files"), released by operator decision; the brief's value applies
   and kept 7 that hold researchteam enrichment:
   - `reference-manager`
   - `references/ref-bibtex-reference.md`
   - `references/code-hygiene-rules.reference.md`
   - `framework-watch` data
   - `team-builder`
   - `SETUP-REQUIRED.md`
   - `content-enricher`

   Each released section's old body is in a `.lost` sidecar under `.agentteams-backups/`.
3. **Codex.** Natively rendered Codex agent bodies are now fenced, so merges refresh them. Since
   agentteams #210, Codex is no longer projected from `.github`. It is rendered natively under
   `write_policy: orchestrator-only`, or refused (see *Codex is orchestrator-only* in
   `researchteam-framework.md`).

**Previously recorded:** `61849fb` (2026-08-15); before that, `c6a9cf6` (2026-08-07). This section's own narrative had lagged that
ref since the day it landed — itself a symptom of what this update fixes: the weekly autosync
CI had been producing correct integrations and silently discarding every one of them for 5
straight weeks (2026-07-13 → 2026-08-10), because GitHub Actions was blocked from opening pull
requests by a repo setting (`can_approve_pull_request_reviews`, default off) — `chore/
agentteams-autosync` was regenerated and force-pushed correctly every Monday with no PR ever
appearing to review. Fixed 2026-08-15 by flipping that one setting; landed via
[`#7`](https://github.com/jlcatonjr/researchteam/pull/7). Full incident record:
`tmp/by-week/2026-W33/researchteam-agentteams-integration-gap.plan.md` in the agentteams repo.

What changed that a consumer of this framework should know:

1. **CSV-write guidance sharpened.** The orchestrator's plan-steps guidance now names
   `agentteams.atomicio.atomic_rewrite_csv_rows()` specifically, not just "a real CSV parser" —
   closing the same class of ledger-truncation failure mode agentteams' own repo hit on itself.
2. **Two new work-summarizer verification rules.** (a) Never assert a plan is complete without
   reading its own steps CSV and confirming every row is `done`, and confirming any cited
   deliverable actually exists on disk. (b) `Commits Count` must be sourced from a `git log` run
   in-session, with the latest short hash quoted alongside it — not restated from a prompt or an
   earlier block (closing a documented incident where a stale count went unchecked).
3. **Fence-safe strip contract unified upstream** (`interop.py` no longer carries its own naive
   strip regex) — protective for the same failure class that cost `security.md` most of its
   content in the incident referenced elsewhere in this doc. No visible diff here — it's a
   mechanism fix, not new content.
4. **CAI v2 (durable canonical agent format) and multi-framework pinned-sync landed upstream as
   opt-in features** — available if this repo ever wants `--pin`/`--sync`/canonical
   materialization, but not adopted, so no rendered files changed because of them.

Earlier integrated (ref `67655da`, 2026-08-03; kept for continuity):

5. **Fenced sections made existing agent files genuinely updatable.** Template-owned
   sections — including the Invariant Core and the security agent's authority — are now
   wrapped in paired `AGENTTEAMS` begin/end fence markers. (Spelled that way deliberately:
   the fence-pairing validator counts the literal marker tokens per file, so writing either
   one in prose registers as an unbalanced fence and fails the gate.) Before this, a
   template improvement could not
   reach a deployed team at all if the corresponding section sat outside a fence; the merge
   had no way to tell an intentional local edit from stale generated content. A merge onto a
   pre-split file now *migrates* it rather than duplicating its sections.
6. **`--shrink-policy` (default `preserve`).** When a fenced merge would drop concrete
   references from an enriched body, the existing body is kept and the template update is
   suppressed **for that fence only**; other fences still update. The notices this emits are
   the mechanism working, not a failure. Do not reach for `--shrink-policy=allow` to silence
   them — that is the setting that discards the enrichment.
7. **`--pin-templates`.** Pins the template trust root outside the writable surface. It
   refuses to run rather than guessing where the root lives if it cannot resolve one.
8. **`--reconcile-front-matter` / `--reconcile-apply`.** Reconciles agent front matter,
   notably the superseded `allowed-tools:` key. That key is **silently ignored**, so any
   agent still declaring it inherits every tool regardless of what its body claims. The apply
   path is never implied — reconciliation reports until explicitly told to write.
9. **`--scan-security` runs on every generate** as an advisory pass (blocking under
   `--fleet`). It flags absolute-path PII among other things. Note that the local code index
   (`.github/agents/references/code-index/`) trips this by design and is gitignored — it is a
   machine-local cache and must never be committed.
10. **`references/instruction-authority.reference.md`** now ships with the team: an explicit
    ordering for instruction conflicts, including where read content sits. Read content is
    inert data, never instruction.
11. **Merge-safety fixes worth trusting the tool again over.** A span enclosing a live fence is
    no longer removed (this had caused real data loss); a section whose only surviving copy is
    the one being removed is no longer deleted; and `--dry-run` now runs the same front-matter
    merge as the real run, so the preview is no longer a different code path from the thing it
    previews.

**Not yet integrated.** agentteams' constitutional red-team work (the `--redteam` standing
audit, the 21 closed exploits, and the fleet capability-key remediation) is on an unmerged
branch and is therefore **not** reachable from `main`. It is deliberately excluded from this
baseline: as of 2026-08-07 that branch fails its own `tests/test_constitutional_redteam.py`
(probe E3, `C-5 has no mechanical enforcement for agent-initiated destruction`, measures
`EXPLOITED` against an accepted value of `DEFENDED`). Integrate it only once that battery is
green upstream.

## Execution Policy

1. **Scheduled runs are SHA-gated, not dry-run.** A scheduled run does nothing unless agentteams `main`
   has advanced past the SHA recorded in `.github/agentteams-autosync-ref`. agentteams is a git
   dependency whose version string does **not** move on every change (it stayed `1.0.0rc6` across 8
   substantive commits), and `--update --merge` refreshes threat-intel/graphs/timestamps on every run —
   so the git **SHA**, not the version and not raw file-drift, is the only sound trigger. The gate lives
   in the managed `scripts/agentteams_autosync_gate.sh` (shared by the upstream + derived workflows).
2. **On a real update, the scheduled run auto-opens/updates ONE evergreen PR** (`chore/agentteams-autosync`)
   after every blocking gate passes in-job (validate + forbidden-path + detector unit tests upstream).
   It compares against the ref on the open evergreen branch, so an already-integrated SHA never re-fires
   while the PR waits — no weekly spam. A manual `workflow_dispatch` (optionally `force=true`) does the
   same on demand. Machine-path files (`delivery-receipt.json`, `memory-index.json`) are scrubbed so no
   CI-runner path is ever proposed.
3. **Auto-merge is disabled — the evergreen PR is reviewed and merged by a human.** The autosync is
   automatic *proposal*, not automatic merge; blocking gates run before the PR opens, and the reviewer
   gate below is the final word. (To opt into auto-merge-on-green later, enable `gh pr merge --auto` on
   the evergreen PR — deliberately not enabled by default.)
4. Workflow defense-in-depth guard must fail CI if `.github/agents/.github/` exists before or after update execution.

## Release-Locked Repositories

A repository is **release-locked** when its `toolchain.lock` records a release tag beside a pin:

```
agentteams=jlcatonjr/agentteams@<peeled sha of the agentteams tag>
agentteams.tag=vX.Y.Z
researchteam=jlcatonjr/researchteam@<peeled sha of the researchteam tag>
researchteam.tag=vX.Y.Z
```

(The values are placeholders; a tag is `vX.Y.Z` or `vX.Y.Z-rc.N`. A derived repo pins the tags of the release
it adopts. researchteam's own
`toolchain.lock` shows a live example of the agentteams lines.)

A pin is the **peeled commit of a verified signed tag**: an annotated tag that `git tag -v` verifies
against the operator's `~/.config/agentteams/allowed_signers` under neutralised repository config,
signed by a release-key fingerprint listed in `researchteam/_release.py` (agentteams SECURITY.md
"Release signers"), whose tag object matches the one the remote advertises. The `name=` lines keep their
old format, so older readers still parse the lock.

Under a release lock, the Execution Policy above changes as follows:

1. **The gate follows the release line, never `main`.** The SHA-gate target is the newest verified tag on
   the locked tag's `vX.Y` line that is newer than it (`check_toolchain.py --release-candidate`, then
   `--verify-tag`). With no newer tag, the run is a no-op. A tag that fails verification fails the gate,
   and no PR opens. `force=true` re-integrates the locked tag, which is how an operator-dispatched soak
   run works.
2. **The lock moves only to a verified tag.** `check_toolchain.py --write-lock` refuses to move a locked
   pin to an untagged commit. It moves the pin only with `--tag name=vX.Y.Z`, on the same line and not
   older, whose peeled commit is the installed one. A gate run whose lock write fails, fails closed.
3. **Layer 2 syncs from the verified researchteam tag.** When the lock has `researchteam.tag`,
   `researchteam update` fetches managed files from that tag's peeled commit instead of `main`, and in
   derived mode the gate installs that researchteam first. A tag that does not verify, or a commit that
   is not its peeled commit, stops the update; it never falls back to `main`. `--ref` overrides the lock
   deliberately. Before installing anything, the derived workflow verifies `researchteam.tag` **with the
   runner's own `git`**, under neutralised config. The tag must exist in researchteam's own refs (not
   merely as a commit reachable through a fork), be annotated, verify against `allowed_signers`, and
   peel to the lock's `researchteam=` commit. Only then does the workflow install researchteam at that
   commit. So the code that verifies agentteams tags in the gate is the pinned release, not researchteam
   `main`. The gate's own later re-check runs that installed code, so it is not independent; the runner
   check is. A malformed pin or tag, a tag that doesn't verify, a commit mismatch, or a missing
   `allowed_signers` stops the workflow. The derived workflow is seeded at `init` and isn't a synced
   file, so an existing repository adopts this step in its first release-lock PR.
4. **CI needs the trust root.** A runner has no `~/.config/agentteams/allowed_signers`. The operator
   provisions one, for example by writing a repository secret to a file and exporting
   `AGENTTEAMS_ALLOWED_SIGNERS`, in the derived workflow before the gate step. Without it, release-locked
   runs fail closed.
   **The secret holds exactly one line: the release key's.** Its format is
   `<principal> namespaces="git" <type> <key>`, copied from agentteams SECURITY.md "Release signers". The
   trust-root step pins the release key's fingerprint (`RELEASE_FP`). A secret holding another key, a second
   line or a malformed line stops the workflow before anything is installed. A key rotation is a reviewed edit
   to `RELEASE_FP` in the workflow, never a secret change. Existing derived repositories must hand-copy this
   step from `researchteam/scaffold/agentteams-sync-derived.yml`, as they did for item 3, because that file
   isn't synced.
   **So does every collaborator.** On a developer machine, `researchteam update` in a release-locked repo
   verifies the researchteam tag before syncing Layer 2, and refuses without
   `~/.config/agentteams/allowed_signers`. That's the intended fail-closed behaviour. Install the release
   signers' line from agentteams SECURITY.md "Release signers" there, or pass `--ref` to choose a ref
   deliberately.
5. **Schedules stay paused during a joint cut.** In a coordinated release (the shared v1.0.0 policy), the
   weekly schedule is disabled with `gh workflow disable`, with no file edit, until every repository has
   tagged. Soak runs are operator-dispatched.

Moving a pin is a security event: record each move in an `@security` row naming the tag object and the
peeled SHA.

## Automatic Integration (keep the tree always integrated)

Goal: the committed repository state should always equal what `agentteams --update --merge` would
generate, so the "latest agentteams update" is integrated without a manual step. Three layers:

1. **Pre-commit hook (local, immediate).** When agent infrastructure is staged (`*.agent.md`,
   `brief.json`, `_build-description.json`), the hook regenerates and re-stages the derived
   artifacts before the commit is created:
   - the AgentTeams-managed block refreshes the topology/architecture graphs;
   - the `RESEARCHTEAM:agentteams-integrate` block runs the full union-descriptor merge via
     `researchteam update --layer1-only` and re-stages the result.
   Both are **non-blocking** (skip cleanly if the tools are absent) so a commit never fails on them.
2. **On-demand / manual.** `researchteam update --layer1-only` runs the same union-descriptor merge
   with **no** layer-2 file sync — safe on the upstream repo (a full `researchteam update` there would
   overwrite local managed-file edits with the older upstream versions).
3. **CI autosync (remote, SHA-gated) — the durable, always-propagating layer.** The `agentteams-sync`
   workflow (upstream) and the scaffold-emitted `agentteams-sync` (derived) run weekly + on
   `workflow_dispatch`. Both are thin shells over the managed `scripts/agentteams_autosync_gate.sh`,
   which SHA-gates on agentteams `main`, and on a real change installs that pinned SHA, runs the regen
   (upstream `--layer1-only`; derived full), scrubs machine-path churn, runs the blocking gates, records
   the SHA in `.github/agentteams-autosync-ref`, and lets the workflow open/update the evergreen PR (see
   Execution Policy). Because the gate is a **managed** file, fixes to the logic propagate to every
   derived repo via `researchteam update` — the four workflow copies (upstream, scaffold, each derived)
   stay thin and rarely change.

**Division of labor (hook vs CI — they do not fight).** The local pre-commit hook fires on *staged agent
files* and re-integrates at whatever agentteams version is *installed locally*; the CI autosync fires on
an *agentteams `main` SHA change* and integrates the *pinned upstream* SHA. Disjoint triggers; any overlap
is self-healing (the `preserve` shrink policy protects enriched fences; `researchteam doctor` flags a stale
local install). The blocking gates run **in-job before** the PR is created — a `GITHUB_TOKEN`-authored PR
does not fire `pull_request` checks, so in-job gating (not PR-status checks) is what guarantees a bad regen
never becomes a mergeable PR.

**Follow-up ([RT]).** The SHA-gate keys on the agentteams commit only; a researchteam-managed-only change
(no agentteams change) is not yet an independent auto-trigger in derived repos — dispatch with `force=true`
to pull one on demand. A future enhancement co-gates on the researchteam ref.

**Propagation caveat.** Git hooks are **per-clone** and are not version-controlled, so the hook does
not travel with `git push`/`clone`. Its durable install is `agentteams --install-git-hooks`; the
`RESEARCHTEAM:agentteams-integrate` block should live in that installer (agentteams repo) for
cross-repo propagation. Until then, add the block per clone (it is present in the upstream repo and
in each derived repo updated by a maintainer). The CI backstop (layer 3) is the version-controlled,
always-propagating guarantee.

## Managed-File Overwrite Hazard (read before adding any local ignore pattern)

Layer-2 sync **overwrites most files in `MANAGED_FILES` wholesale from upstream** (the default
`overwrite` strategy in `researchteam/_manifest.py`). For those files there is no merge and no
three-way comparison — `researchteam update --yes` replaces the local file and reports it as
`Updated`. Any content that exists only in a derived repo is therefore deleted on the next sync,
silently.

> **Update (2026-W36): `.gitignore` is `fenced-preserve`, not wholesale-overwritten.** It
> carries a `# >>> researchteam:managed … # <<< researchteam:managed` fence; sync replaces only the
> region *inside* the fence and preserves every derived-repo line *below* it. For an already-fenced
> file the diff preview is computed against the fenced region only, so derived lines never render as
> spurious deletions; and a pre-fence derived `.gitignore` is never silently wiped — under `--yes`
> it is kept-and-warned, and interactively it is surfaced as a full diff (which *does* show the
> would-be losses) requiring explicit approval before any replacement. See `docs/gitignore-preservation-handoff.md` and
> `researchteam/_update_cmd.py` (`_reconcile_fenced`).
>
> **Update (2026-W39): `CLAUDE.md` is also `fenced-preserve`, and `README.md` is no longer a
> managed file.** `CLAUDE.md` carries the same fence, now in HTML-comment form
> (`<!-- >>> researchteam:managed … --> … <!-- <<< researchteam:managed -->`); sync replaces only
> the framework governance block inside it and preserves the project-owned title + *Project
> Purpose* header above it. `README.md` has been removed from `MANAGED_FILES` entirely — it is
> generated per-project from `researchteam/scaffold/README.template.md` (as is `CLAUDE.md`'s header)
> by `researchteam personalize` and is never synced from upstream. The wholesale-overwrite hazard
> below therefore applies only to the remaining `overwrite`-strategy files in `MANAGED_FILES`
> (docs, scripts, prompts); the discipline rules remain the durable belt for those.
>
> **Update (2026-W41): the `above-notes` strategy and `researchteam:notes` blocks (OrthodoxLLM
> Item 1).**
>
> - **The advisor.** `.github/agents/interpretation-advisor.agent.md` is managed for scholarly
>   instances with `above-notes`: upstream owns everything above `## Project-Specific Notes`, front
>   matter included. The repo owns that heading and everything after it. The previous file is
>   saved to the gitignored `tmp/researchteam-backups/<run>/`, and the diff is printed even under
>   `--yes`. Under `--yes`, an upstream change that **widens** the front matter's `tools:`,
>   `agents:` or handoff targets is refused (Constitutional C-3); review it interactively instead.
> - **A customised advisor is kept.** Upstream's part replaces the local one only when the local
>   part still equals upstream's at the repo's pinned researchteam commit (`toolchain.lock`, else
>   the `.researchteam` ref, else `main`; compared like `doctor --drift`). A repo that retargeted it
>   (mathAgents) is kept with a `customised locally … kept local unchanged` line, under `--yes`
>   too; so is one whose pinned copy cannot be fetched. Interactively the prompt defaults to No.
>   `researchteam update --accept-upstream <path>` (repeatable) takes upstream's part anyway; the
>   C-3 widening refusal still applies.
> - **Notes blocks.** Rules that researchteam writes for the advisor and the topic-scoping,
>   literature-review and main-analysis experts live in a `researchteam:notes` block at the top of
>   each agent's Notes. `update` syncs the block on `.github`, `.claude` and `.goose`, backs up each
>   file it changes, and never touches Notes text outside the block. agentteams preserves Notes
>   verbatim, so layer 1 and layer 2 never write the same region. See `researchteam/_notes.py`.

`.gitignore` was historically the dangerous case: the failure mode is not a lost edit but *lost
protection*, and nothing announced it. The fence closes that class in code; the rules below stay in
force for the rest of `MANAGED_FILES` and as defense-in-depth.

**This is not hypothetical.** On 2026-08-07 a sync of SocialScienceHumanities dropped that
repo's source-corpus and LaTeX ignore patterns, exposing **1041 corpus files (198 MB)** that
had been correctly ignored moments earlier — one `git add -A` away from entering history.
Nothing was committed, and the patterns were restored, but the exposure was created by a
routine update with `--yes`.

**Rules that follow from it:**

1. **A generic ignore pattern belongs upstream, in this repo's `.gitignore`.** That is the
   only place a sync propagates rather than deletes. The corpus and LaTeX patterns now live
   here for exactly this reason.
2. **A genuinely project-specific exclusion goes in the derived clone's `.git/info/exclude`.**
   It is never synced, never committed, and no managed-file overwrite can reach it. Mirror it
   into `.gitignore` for visibility if you like, but treat that copy as expendable.
3. **After any layer-2 sync, re-check the exclusions you rely on** before staging anything.
   `git status --porcelain --untracked-files=all | wc -l` jumping is the tell.
4. **Derived-only `.gitignore` patterns go BELOW the `# <<< researchteam:managed` marker.** That
   region is preserved across every sync. Patterns of general use still belong upstream, inside the
   fence, so they propagate to all derived repos.

## Reviewer Gate

Before merging a sync PR, reviewers must confirm:

1. Changed files are within approved scope (`.github/**`, `brief.json`, validator/policy docs when expected).
2. AGENTTEAMS fence pairing remains valid in all changed markdown/agent files.
3. No new `{MANUAL:*}` placeholders were introduced.
4. No user-authored content outside fenced regions was removed.
5. Derived-owned `.gitignore` region (below `# <<< researchteam:managed`) is preserved intact.

## Rollback Protocol

1. If validation fails in CI: do not open PR; inspect artifacts and rerun after fixes.
2. If unsafe PR is opened: close PR and pin prior AgentTeams ref.
3. If a bad sync is merged: revert commit and rerun in dry-run mode with stricter scope checks.

## Legacy Mirror Handling

- `.github/agents/.github/**` is forbidden nested mirror content and not source-of-truth.
- `.github/agents/.agentteams-backups/**` is archival backup content and not source-of-truth.
- Do not include either path family in sync scope or review baselines.

## Escalation

Escalate to maintainer review if:
- out-of-scope path changes are detected,
- fence mismatches are detected,
- duplicate-tree drift reappears in active source-of-truth paths.

## Validator Test Matrix (Local)

Use these commands to verify validator behavior locally:

1. Baseline outside git worktree context (expected fail, exit 1)

```bash
bash scripts/validate_agentteams_update.sh
echo $?
```

Expected:
- Error indicating no git worktree and no override.
- Exit code `1`.

2. Allow-skip outside git worktree context (expected pass, exit 0)

```bash
VALIDATION_ALLOW_NO_GIT=1 bash scripts/validate_agentteams_update.sh
echo $?
```

Expected:
- Warning indicating skip is explicitly allowed.
- Exit code `0`.

3. Allowed changed file simulation (expected pass, exit 0)

```bash
VALIDATION_CHANGED_FILES='docs/agentteams-update-policy.md' bash scripts/validate_agentteams_update.sh
echo $?
```

Expected:
- Validation completes successfully.
- Exit code `0`.

4. Forbidden nested mirror simulation (expected fail, exit 1)

```bash
VALIDATION_CHANGED_FILES='.github/agents/.github/reintroduced.txt' bash scripts/validate_agentteams_update.sh
echo $?
```

Expected:
- Error indicating forbidden nested mirror path.
- Exit code `1`.

5. Agent file with unresolved placeholders (expected fail, exit 1)

```bash
VALIDATION_CHANGED_FILES='.github/agents/conclusion-expert.agent.md' bash scripts/validate_agentteams_update.sh
echo $?
```

Expected:
- Error indicating unresolved `{MANUAL:*}` placeholders in changed active agent file.
- Exit code `1`.
