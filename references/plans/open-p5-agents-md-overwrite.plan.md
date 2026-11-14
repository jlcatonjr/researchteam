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
