# Handoff — Make `researchteam update` **preserve derived `.gitignore` additions**

**From:** SocialScienceHumanities (a derived research repo) — orchestrator session, 2026-08-26.
**To:** researchteam maintainer(s).
**Scope:** Change the **layer-2 update mechanism** so a sync no longer silently deletes ignore
patterns that exist only in a derived repo's `.gitignore`.
**Type:** Durable **code** fix request (the hazard is already documented as *policy* — see
`docs/agentteams-update-policy.md` §"Managed-File Overwrite Hazard"; this asks to close it in the tool).
**Status:** ✅ **IMPLEMENTED 2026-08-31 (2026-W36).** Option A (fenced-preserve) shipped:
`MERGE_STRATEGIES` + fence sentinels in `researchteam/_manifest.py`; `_split_fence` /
`_fence_body` / `_reconcile_fenced` + per-strategy branch in `researchteam/_update_cmd.py`; this
repo's `.gitignore` wrapped in the fence; `tests/test_update_gitignore_preserve.py` covers the §7
matrix (13 tests green); policy doc updated (§"Managed-File Overwrite Hazard" + reviewer gate).
Original request text below is preserved as the design record.

**Original status:** No code changed by this handoff. Non-destructive. Grounded in the current
`main` source (line refs verified 2026-08-26).

---

## 1. TL;DR

`.gitignore` is a `MANAGED_FILES` entry, and layer-2 sync writes every managed file **wholesale**
from upstream (`local_path.write_text(remote_content)`). There is no merge, fence, or three-way
comparison. So **any ignore pattern that exists only in a derived repo is deleted on the next
`researchteam update`** — and the derived weekly CI runs the *blind* `--yes` path, so it happens
with no prompt and no announcement. The failure mode is not a lost edit but **lost protection**:
files that were correctly ignored become stageable, one `git add -A` from entering history.

**Ask:** give the manifest a per-file **merge strategy** and mark `.gitignore` as *fenced-preserve*
— upstream owns a comment-fenced managed block; everything outside the fence is preserved across
syncs. Recommendation, alternatives, and an acceptance-test matrix are below.

---

## 2. Exact mechanism (verified on `main`, 2026-08-26)

| Fact | Location |
|------|----------|
| `.gitignore` is a managed, upstream-owned file | `researchteam/_manifest.py:9` (`MANAGED_FILES`) |
| Managed files are replaced wholesale — no merge | `researchteam/_update_cmd.py:50-98` — on diff, `local_path.write_text(remote_content, …)` |
| Interactive mode shows a diff and can skip a file | `_update_cmd.py:69-79` (`input("Apply? [y/N] ")`) |
| `--yes` applies every diff with **no prompt** | `_update_cmd.py:69` guard skipped when `yes=True` |
| Derived weekly CI runs the blind path | `scripts/agentteams_autosync_gate.sh:96` — `researchteam update --yes` |
| `.gitignore` has **no** fence markers today | current `.gitignore` (repo root) |
| Hazard already documented (policy only) | `docs/agentteams-update-policy.md:149-174` |

The update loop is uniform: it iterates `MANAGED_FILES` and, for any file whose local content differs
from upstream, overwrites it. `.gitignore` is treated exactly like a doc or a shell script. Nothing in
the loop distinguishes "upstream changed this line" from "the derived repo added a line upstream never
had" — the second case simply disappears.

## 3. Why the existing mitigations don't close it

`docs/agentteams-update-policy.md` §"Managed-File Overwrite Hazard" already prescribes: keep generic
patterns upstream; put project-specific ones in `.git/info/exclude`; re-check `git status` after every
sync. Those are correct and should stay — but they are **human-discipline controls layered on a tool
that still deletes silently**:

1. **CI is blind.** The derived autosync (`--yes`) never surfaces the diff to a human, so "re-check
   after sync" has no natural checkpoint on the automated path — the one that fires weekly.
2. **The legitimate case is the one at risk.** A derived repo *should* be able to add a genuinely
   local ignore (a hidden local-only project, a machine-local output dir). Today doing the obvious
   thing — adding it to `.gitignore` — is precisely what the next sync wipes.
3. **`.git/info/exclude` is invisible and per-clone.** It survives syncs, but it is not
   version-controlled, not reviewable in a PR, and easy to forget on a fresh clone. It is a good
   *belt*; it is a poor *only* control.

## 4. Triggering case (concrete, this repo's sibling)

On **2026-08-26**, SocialScienceHumanities imported a manuscript as a hidden, local-only project and
added two derived-only lines to its `.gitignore`:

```gitignore
Projects/.MonetaryShocksAndRelativePricesOfAgriculturalAndIndustrialCommodities/
workSummaries/
```

Both are legitimate, both are derived-specific, and both are **exactly the content
`docs/agentteams-update-policy.md:149-174` warns the next `--yes` sync will delete**. That header also
records the precedent: the 2026-08-07 SocialScienceHumanities sync dropped the source-corpus + LaTeX
ignore patterns and exposed **1041 corpus files (198 MB)**. This handoff exists so the tool stops
depending on someone remembering the policy every time.

## 5. Recommended fix — per-file merge strategy, `.gitignore` = *fenced-preserve*

This mirrors idioms the framework already trusts: the `AGENTTEAMS` begin/end fences that made agent
files updatable, and the "USER-EDITABLE … preserved verbatim across `--update --merge`" region in
`CLAUDE.md`. Apply the same shape to `.gitignore`.

### 5.1 Manifest: declare the strategy

`researchteam/_manifest.py` — keep `MANAGED_FILES` as the set, add a strategy map (default =
current behavior, so nothing else changes):

```python
# How each managed file is reconciled on update. Default: wholesale overwrite (current behavior).
MERGE_STRATEGIES = {
    ".gitignore": "fenced-preserve",
}
```

### 5.2 Upstream `.gitignore`: wrap the managed block in a fence

The upstream file carries sentinel comments so the tool knows which region it owns:

```gitignore
# >>> researchteam:managed — do not edit inside this block; `researchteam update` replaces it.
tmp/
.venv/
**/references/corpus/text/
# … all upstream-owned patterns …
# <<< researchteam:managed
#
# Anything BELOW this line is derived-repo-owned and preserved across updates.
Projects/.MonetaryShocksAndRelativePricesOfAgriculturalAndIndustrialCommodities/
workSummaries/
```

### 5.3 Update loop: splice, don't overwrite

`researchteam/_update_cmd.py` — branch on strategy inside the per-file loop:

- **`overwrite` (default):** unchanged — `write_text(remote_content)`.
- **`fenced-preserve`:**
  1. Parse the local file into `(local_pre, local_managed, local_post)` around the fence markers.
  2. Parse upstream into its managed block.
  3. Write `local_pre_of_fence + upstream_managed_block + local_post_of_fence`. Only the fenced
     region is replaced; derived lines outside it are untouched.
  4. **Migration (local has no fence yet):** treat the whole local file as the managed region for a
     first-time wrap **only if** it is byte-equal to the last-known upstream; otherwise do **not**
     silently discard — emit the diff and (interactive) prompt, (`--yes`) keep local + warn, so a
     pre-fence derived file is never wiped by the very update meant to protect it.
  5. **Diff preview + `--yes`:** compute the shown diff against the **fenced region only**, so
     local-only lines never render as spurious deletions in `_update_cmd.py:55-74`.

Because the strategy is per-file and defaults to `overwrite`, every other managed file (docs, scripts,
`CLAUDE.md` — which agentteams already fences separately) is unaffected. The `.sh` exec-bit handling
(`_update_cmd.py:83,95`) is orthogonal and stays.

## 6. Alternatives considered (trade-offs)

| Option | How | Pro | Con |
|--------|-----|-----|-----|
| **A. Fenced-preserve** *(recommended)* | Upstream owns a fenced block; preserve outside | Matches existing fence idiom; reviewable in-repo; upstream add/remove still propagate inside the fence | Requires adding fence markers to upstream `.gitignore` once; a pre-fence file needs a migration path (§5.3.4) |
| **B. Three-way merge** | Store last-synced upstream baseline; apply upstream delta, keep local additions | No fence discipline; most general; could extend to any managed file | Must persist a baseline (e.g. `.researchteam` state or a `.git`-side cache); more moving parts |
| **C. Union / append-only** for `.gitignore` | Never delete local lines; add upstream lines not already present | Trivial; safe against loss | Upstream **removals** never propagate; ordering/duplication drift; only sensible for additive files |

A is the smallest change that removes the silent-deletion class **and** keeps upstream changes flowing.
B is the better long-term generalization if more managed files ever need preserve semantics. C is a
safe stopgap but leaks upstream deletions.

## 7. Acceptance criteria / test matrix

A fix is done when, for `.gitignore` under `fenced-preserve`:

1. **Derived lines survive `--yes`.** `researchteam update --yes` on a repo with lines below the fence
   leaves those lines byte-identical. *(This is the core regression the incident needs.)*
2. **Upstream additions land.** A new pattern added to the upstream managed block appears after sync.
3. **Upstream removals apply.** A pattern removed upstream *inside the fence* is removed locally.
4. **No spurious deletions in preview.** `--dry-run` / interactive diff never lists a derived-only
   line as a `-` deletion.
5. **Pre-fence migration is non-destructive.** A derived `.gitignore` with no fence markers is never
   silently overwritten; it is wrapped (if upstream-equal) or surfaced (if it diverged), per §5.3.4.
6. **Other managed files unchanged.** Docs/scripts still overwrite wholesale; `.sh` exec bit preserved.
7. **Idempotent.** Running update twice with no upstream change is a no-op (no re-fencing churn).

Suggested home: a `tests/test_update_gitignore_preserve.py` alongside the existing update tests, plus
one row in the `docs/agentteams-update-policy.md` reviewer gate ("derived-owned `.gitignore` region
preserved").

## 8. Interim mitigation (until the fix ships)

Unchanged from `docs/agentteams-update-policy.md:165-174`, restated for the handoff reader:

1. **Generic patterns belong upstream** in this repo's `.gitignore` — the only place a sync
   propagates rather than deletes.
2. **Genuinely project-specific exclusions go in the derived clone's `.git/info/exclude`** — never
   synced, never committed, unreachable by any managed-file overwrite. Mirror into `.gitignore` for
   visibility, but treat that copy as expendable.
3. **After any layer-2 sync, re-check exclusions before staging.** A jump in
   `git status --porcelain --untracked-files=all | wc -l` is the tell.

For the 2026-08-26 SSH case specifically: the two derived lines were also mirrored into that clone's
`.git/info/exclude` as the durable belt while this fix is pending.

## 9. Rollout notes

- **Backwards compatible.** `MERGE_STRATEGIES` defaults to `overwrite`; repos and files not opted in
  behave exactly as today.
- **One upstream edit required:** add the fence markers to the upstream `.gitignore` (§5.2). Until
  that lands, `fenced-preserve` degrades safely (no fence in upstream → treat as overwrite, or better,
  as "preserve everything and warn" so nothing is lost meanwhile).
- **No agentteams (layer-1) change.** This is entirely within the researchteam layer-2 updater.
- **Doc touch-up:** once shipped, update `docs/agentteams-update-policy.md` §"Managed-File Overwrite
  Hazard" to note that `.gitignore` is now merge-preserved, not wholesale-overwritten.

## 10. Appendix — file/line index (verified 2026-08-26)

- `researchteam/_manifest.py:6-29` — `MANAGED_FILES` (`.gitignore` at line 9).
- `researchteam/_update_cmd.py:42-98` — per-file sync loop; wholesale writes at lines 82 and 94.
- `researchteam/_update_cmd.py:69-79` — interactive `Apply? [y/N]` (skipped under `--yes`).
- `researchteam/cli.py:53,103-104` — `--yes` / `--dry-run` wiring.
- `scripts/agentteams_autosync_gate.sh:95-98` — derived runs `researchteam update --yes`; upstream
  runs `--layer1-only --yes`.
- `docs/agentteams-update-policy.md:149-174` — existing hazard policy this handoff asks to enforce
  in code.

---

### Revision history
- **v1 (2026-08-26):** initial draft.
- **v1.1 (2026-08-26):** post-audit revision — see "Audit trail" below.

### Audit trail (adversarial + technical-accuracy pass, 2026-08-26)
Findings applied before finalizing:
- **Overreach check:** original draft implied CI "silently commits" the exposure. Corrected — the
  autosync opens a **reviewed PR** (auto-merge disabled; `agentteams-update-policy.md:99-102`); the
  risk is *lost protection surfacing in that PR's tree*, not an auto-commit. Language in §1/§3 tightened.
- **Migration gap:** the first draft's `fenced-preserve` would itself wipe a *pre-fence* derived
  `.gitignore` (no markers → whole file treated as managed). Added the non-destructive migration rule
  (§5.3.4) and test #5.
- **Preview correctness:** added the requirement that the shown diff be computed against the fenced
  region only (§5.3.5), else legitimate local lines render as deletions and train reviewers to ignore
  the warning.
- **Line-ref accuracy:** every `file:line` in §2/§10 re-checked against `main` source on 2026-08-26.
- **Scope honesty:** confirmed this is layer-2-only (no agentteams change) and defaults preserve
  current behavior for all other files (§5.1, §9).
