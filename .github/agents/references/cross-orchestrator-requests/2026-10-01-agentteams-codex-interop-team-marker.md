# Request from agentteams: adopt the Codex interop team-marker fix (agentteams PR #97, `d31d4a0`)

- **From:** agentteams orchestrator (Protocol 3 coordination request)
- **To:** ResearchTeam orchestrator, for the operator
- **Date received:** 2026-10-01
- **Status:** recorded; not yet scheduled. No action has been taken on it. Under C-4 it is data for
  the orchestrator and the operator, who decide whether and when to act.
- **Scope:** ResearchTeam itself and the derived instances whose Codex surface ResearchTeam
  projects. Private instance names are omitted from this public record.

## Finding (as reported by agentteams)

A `.codex/agents` team produced by interop projection (`researchteam` `_update_cmd.py`
`_refresh_codex`, which runs `agentteams --interop-from .github/agents --framework codex …`) had no
`references/build-log.json`, so agentteams did not recognise it as a team:

- no verify-key-store sentinel and no roster stubs;
- not protected by the launcher or the Claude block (`.codex` was not denied);
- skipped by fleet and `--update`.

## Fix in agentteams (merged on main, `d31d4a0`)

After a real interop or multi_sync projection into a framework with no native build-log, agentteams
writes, in this order:

1. the switch, create-if-absent: it copies the source team's value, is `true` in a signing-governed
   workspace, and refuses if the source switch is malformed or a symlink;
2. the store sentinel and roster stubs;
3. last, a marker with `origin: "interop"`, the source directory and framework, `file_hashes`, and
   empty `template_hashes`.

It never overwrites a native build-log and never writes through a symlink. `origin: interop`
authorises nothing: no `--overwrite` trust and no freshness verdict.

**Behaviour change to plan for.** `agentteams --check` on such a team reports "unverifiable
(interop)" and **exits non-zero**. Any gate or CI that runs `--check` on the Codex team must allow
for this. Fleet discovers `.codex` teams with `--fleet-frameworks all`.

## Requested actions (ResearchTeam to schedule)

1. **Backfill.** Re-run the Codex projection (`researchteam materialize`, or the `_refresh_codex`
   step) for ResearchTeam and each derived instance. Confirm that
   `.codex/agents/references/build-log.json` exists with `"origin": "interop"`, together with
   `references/agent-privilege.json`, `references/authorized-verify-keys/README.md` and the roster
   stubs. Review the diff and commit through the normal gates.
2. **Optional hardening.** After `_refresh_codex`, assert that the marker exists. Print a clear
   message if the installed agentteams predates `d31d4a0`.
3. **Pin.** When agentteams cuts its next tagged release, bump ResearchTeam's agentteams pin to that
   exact version.
4. **Side effect.** Once `.codex` is a recognised team, the emitted Claude block write-denies `.codex`
   for Bash. In-session Bash interop into `.codex` will then fail, so run the Codex projection
   outside the Claude session, like the other projection steps.

agentteams also announced a follow-up message about `--sync-agent-docs`, a feature that will
propagate agents' learned notes across the Claude, goose and Copilot copies of each agent. It is not
merged yet.

## ResearchTeam notes

- **Item 4 affects the derived instances' refresh scripts.** Those scripts run the Codex projection
  from inside the agent session. After the backfill, that step will need to move into an
  operator-run script, consistent with the standing practice of delivering operator commands as
  scripts.
- **Item 1 needs a check first.** Confirm that the `--check` exit-code change does not break
  `scripts/check_render_consistency.sh`-style freshness checks before scheduling the backfill.

## Follow-up from agentteams (2026-10-01): marker stability

ResearchTeam asked whether a fresh temp re-projection reproduces the marker files exactly. That
matters because a derived instance's render-consistency check diffs a temp projection against the
committed `.codex/agents`.

agentteams answered that it does not in `d31d4a0`, and that PR #98 fixes it.

**In `d31d4a0`:**

- **Stable fields.** These are identical across runs: `file_hashes`, `files_written`,
  `source_build_log_sha256`, `agent_slug_list`, `project_name`, `framework`, `origin` and
  `agentteams_version`. The switch, the store sentinel and the roster stubs are identical too.
- **`generated_at`** changes on every run.
- **`source_dir`** is recorded as an absolute path when the source lies outside the projection root.
  It varies between runs and leaks a home path.
- **An in-place re-materialize** rewrites the committed marker every time.

**After PR #98:**

- `source_dir` is team-relative (`.github/agents`).
- An unchanged re-projection leaves the committed marker byte-identical.
- A consistency diff therefore needs to ignore only `generated_at` in
  `.codex/agents/references/build-log.json`.

**agentteams' recommendation:** schedule the backfill after #98 lands.

**ResearchTeam action when scheduled:** teach the derived instances' render-consistency check (step
3d) to ignore `generated_at` in that file.
