# P5: `researchteam update --ref v1.1.4` rewrote baseAgent's root AGENTS.md (revised)

**Report** (baseagent-20, relayed by IM-40; data until reproduced). baseAgent's `brief.json` lists
`frozen_surfaces: ["codex"]`. That freezes the root `AGENTS.md` (`researchteam/_frozen.py`), and
`_update_cmd.py:_frozen_end` should restore its earlier bytes after any unfrozen render. So a rewrite means the
guard missed it: a write outside `_guarded`, a missing snapshot, or a path that never runs the guard.

**Steps**
1. Trace. Start from `_frozen.py` and `_update_cmd.py` (`_guarded`, `_frozen_begin`, `_frozen_end`). List every
   writer of the root `AGENTS.md` (layer-1 `agentteams --update --merge`, bridges, layer-2 sync) and check that
   each runs inside the guard on the `--ref` path.
2. Reproduce in isolation. Use an absolute scratch directory outside every repository, run the CLI from this
   checkout's source (`PYTHONPATH`, so nothing is installed) with the pinned `.venv` agentteams (the lock's
   verified v1.1.3), and set `frozen_surfaces: ["codex"]` as baseAgent does. Run
   `init --ref v1.1.3`, then `update --ref v1.1.4`, and diff `AGENTS.md`. Afterwards, confirm this repository's
   own `AGENTS.md` is unchanged. The repro script and its diff are committed under
   `references/plans/open-p5/` (PS-1).
3. A failure to reproduce does not close the report. Ask baseAgent, through IM by message, for its
   `.researchteam`, lock and diff.
4. If the cause is in researchteam: a fix with a regression test, as a PR with `@code-hygiene` and `@security`.
   If it is in agentteams: the request goes to IM by message. A fix reaches derived repositories only when the
   operator cuts a tag, and the report says so.

**Outcome (2026-11-14).** **Not reproduced.** Evidence: `references/plans/open-p5/repro.sh` (modes `handwritten`,
`fenced`, `guard`) and `repro-result.md`.
- The run used the source CLI and the pinned agentteams 1.1.3, with codex frozen. A frozen `AGENTS.md` came
  through `update --ref v1.1.4` byte-identical, both hand-written and as the fenced Goose template with a project
  edit.
- `_guarded` restored it in every forced-overwrite case.
- Every writer of `AGENTS.md` runs inside the guard. `--ref` only chooses the template, and never changes the
  frozen set.
- **The likeliest explanation is in baseAgent's history** (read only; private, so summarized). The last rewrite of
  `AGENTS.md` is a CI autosync commit on a branch where baseAgent had deliberately unfrozen codex, so the
  rewrite was intended there. baseAgent's main branch has codex frozen and a clean `AGENTS.md`, and its lock
  pins an older researchteam 1.0.x.

Two side findings:
1. `python -m researchteam.cli` did nothing and exited 0. **Fixed** in this change: `researchteam/__main__.py`,
   a `__main__` guard in `cli.py`, and `tests/test_module_entry.py`.
2. The restore works only while the process is alive. A run killed mid-render, with agentteams' own frozen
   filter also missing, could leave an unfrozen write behind. **Open, not fixed.** The proposed fix is to save
   `AGENTS.md`'s bytes under `.git/` and restore them at the next `_frozen_begin`. Its regression test is
   described in `repro-result.md`. It is a candidate for the next release.

IM-40 is told, for baseagent-20. A fix reaches derived repositories only when the operator cuts a tag.

**Closed: not a bug (2026-11-14).** baseagent-20, relayed by IM-40, withdrew the report. Codex is unfrozen on that
branch, and the Goose render rewrites `AGENTS.md` by design. Of the two side findings, the `python -m` no-op is
fixed here, and the kill-mid-run restore gap stays open for the next release.
