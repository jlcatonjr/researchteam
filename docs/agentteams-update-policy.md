# AgentTeams Update Policy

Date: 2026-05-20
Status: Active

## Purpose

Define review and rollback policy for automated AgentTeams synchronization runs using `--update --merge`.

## Integrated AgentTeams Baseline

**Integrated ref:** `67655da` (agentteams `main`, 2026-08-03) — recorded in
`.github/agentteams-autosync-ref`.
**Previously recorded:** `e6627fb` (2026-07-09), 155 commits behind. The gap is the reason
this section exists: the recorded ref is what the SHA gate compares against, so a stale ref
is indistinguishable from "nothing to integrate" until someone reads it.

What changed between those refs that a consumer of this framework should know:

1. **Fenced sections made existing agent files genuinely updatable.** Template-owned
   sections — including the Invariant Core and the security agent's authority — are now
   wrapped in paired `AGENTTEAMS` begin/end fence markers. (Spelled that way deliberately:
   the fence-pairing validator counts the literal marker tokens per file, so writing either
   one in prose registers as an unbalanced fence and fails the gate.) Before this, a
   template improvement could not
   reach a deployed team at all if the corresponding section sat outside a fence; the merge
   had no way to tell an intentional local edit from stale generated content. A merge onto a
   pre-split file now *migrates* it rather than duplicating its sections.
2. **`--shrink-policy` (default `preserve`).** When a fenced merge would drop concrete
   references from an enriched body, the existing body is kept and the template update is
   suppressed **for that fence only**; other fences still update. The notices this emits are
   the mechanism working, not a failure. Do not reach for `--shrink-policy=allow` to silence
   them — that is the setting that discards the enrichment.
3. **`--pin-templates`.** Pins the template trust root outside the writable surface. It
   refuses to run rather than guessing where the root lives if it cannot resolve one.
4. **`--reconcile-front-matter` / `--reconcile-apply`.** Reconciles agent front matter,
   notably the superseded `allowed-tools:` key. That key is **silently ignored**, so any
   agent still declaring it inherits every tool regardless of what its body claims. The apply
   path is never implied — reconciliation reports until explicitly told to write.
   *Status in this repository: 0 agents on the superseded key; 31 on `tools:`.*
5. **`--scan-security` runs on every generate** as an advisory pass (blocking under
   `--fleet`). It flags absolute-path PII among other things. Note that the local code index
   (`.github/agents/references/code-index/`) trips this by design and is gitignored — it is a
   machine-local cache and must never be committed.
6. **`references/instruction-authority.reference.md`** now ships with the team: an explicit
   ordering for instruction conflicts, including where read content sits. Read content is
   inert data, never instruction.
7. **Merge-safety fixes worth trusting the tool again over.** A span enclosing a live fence is
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

Layer-2 sync **overwrites every file in `MANAGED_FILES` wholesale from upstream**. There is
no merge, no fence, and no three-way comparison — `researchteam update --yes` replaces the
local file and reports it as `Updated`. Any content that exists only in a derived repo is
therefore deleted on the next sync, silently.

`.gitignore` is on that list, which makes it the dangerous case: the failure mode is not a
lost edit but *lost protection*, and nothing announces it.

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

## Reviewer Gate

Before merging a sync PR, reviewers must confirm:

1. Changed files are within approved scope (`.github/**`, `brief.json`, validator/policy docs when expected).
2. AGENTTEAMS fence pairing remains valid in all changed markdown/agent files.
3. No new `{MANUAL:*}` placeholders were introduced.
4. No user-authored content outside fenced regions was removed.

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
