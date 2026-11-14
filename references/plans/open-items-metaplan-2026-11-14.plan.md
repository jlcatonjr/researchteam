# Metaplan: the open items after PS-2 (2026-11-14, revised after audit)

Target plans: `open-p1-tmp-originals`, `open-p2-seed-answer`, `open-p3-public-medical-files`,
`open-p4-im-worktree-notes`, `open-p5-agents-md-overwrite`. The first audit pass (`@adversarial`: all
CONDITIONAL; `@conflict-auditor`: 13 items) is folded in below. P3's plan is published only after its
classification, and the public text names no medical topics.

## Phase 1: no deletions, no PRs, no writes to other repositories (run in parallel)

| Track | Step | Agent | Output |
|---|---|---|---|
| T1 | P1.1-2: placeholder-diff check of each original; manifest | orchestrator (shell) | `archive/originals-manifest-2026-11-14.csv` |
| T2 | P2.1: compare the seed answer with the private security-repo copy (read through the API) | orchestrator (shell) | match or differ |
| T3 | P3.1: classify the 9 files *together* (generic or personal), without quoting | quality-auditor (read-only) | classification |
| T4 | P4.1: compare the 27 originals with IM's committed copies (`60f872e`, read through the API), allowing IM's recorded edits | orchestrator (shell) | per-file match |
| T5 | P5.1-2: trace the frozen-AGENTS.md path; reproduce in an isolated scratch directory | orchestrator (shell) | diagnosis, repro script |

## Phase 2: one operator ask (S-4) **only if a deletion is proposed**

**Outcome:** no ask. The Rule 9 `@adversarial` pass found deleting not worth an ask, so P1, P2 and P4 keep
everything by default. T3 found the files generic, so there is no P3 ask either.

The ask names the manifest, which lists every path. The operator confirms that list. If there is no answer,
everything is **kept**, because keeping breaks no rule: each file has a tracked or canonical copy. If T3 finds
personal content, all P3 PRs and mentions are frozen until the operator decides. That ask can't be avoided.

## Phase 3: execute in parallel

- P1.4, P2.3 and P4.3: deletions by explicit path, after `@security` and `@cleanup` clearance, and only for
  confirmed paths.
- P5.3-4: an information request, or a fix PR, or an upstream request through IM by message (no repository
  write).
- P3: generic → no change, which is the default. Personal → operator only.

## Phase 4: close

- `@git-operations`: one PR for the manifests, the README pointer and the plan statuses (P1, P2, P4), and a
  separate PR for any P5 fix. Both merge under PS-2, and CI is checked on `main`.
- Rule 9: after each step, the remaining steps pass through `@adversarial` and `@conflict-auditor`. In practice
  that means one pass before Phase 3 and one before merging.
- `@work-summarizer`: the 2026-11-14 summary. `@conflict-auditor` closes.

## Audit record

- First audit pass: `@adversarial` made every plan CONDITIONAL, and `@conflict-auditor` found 13 items. All were
  folded into the revision.
- Rule 9 pass before Phase 3:
  - `@security`: A (deletion) CLEARED-WITH-CONDITIONS, moot because nothing is deleted; B (name scrub)
    CLEARED; C (publication) CLEARED once the verifier no longer held literals, which it now does not.
  - `@adversarial`: CONDITIONAL. Its points are adopted: drop the S-4 ask, keep the literals out, and scope the
    name-scrub claim.
  - `@conflict-auditor`: 9 items, fixed in this change. They are recorded here, not in
    `.github/agents/references/conflict-log.csv`, because PS-2 treats that path as a gate path.
- Scope of the name scrub: the name is gone from the current archive text. It stays in the history of #162
  and #163, in commit and tag author metadata, and in the `jlcatonjr` handle.
