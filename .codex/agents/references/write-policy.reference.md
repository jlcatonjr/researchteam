<!-- AGENTTEAMS:BEGIN content v=1 -->
# Write Policy Reference — `orchestrator-only`

Only the orchestrator writes. Every other agent returns one of three JSON artifacts. The orchestrator
applies or runs it with `agentteams`, which checks it against the team's policy (`agent_policies`,
`protected_paths`, `proposal_gates` in the project brief) and records it in a signed ledger.

## `change-proposal`: create or replace a file

```json
{"kind": "change-proposal", "dispatch": "<nonce from the orchestrator>",
 "path": "src/module.py", "base_sha256": "<sha256 of the file you read>",
 "content": "<the full new file text>", "rationale": "one or two sentences"}
```

- **`base_sha256`:** use `"absent"` for a new file. A stale base is refused, so re-read and re-propose.
- **`content`:** the whole file, not a diff.

## `delete-proposal`: delete a file

```json
{"kind": "delete-proposal", "dispatch": "<nonce>", "path": "src/old.py",
 "base_sha256": "<sha256 of the file you read>", "rationale": "why it goes"}
```

## `command-request`: run a command

```json
{"kind": "command-request", "dispatch": "<nonce>", "argv": ["python3", "scripts/check.py", "slug"],
 "purpose": "why", "expected_writes": ["reports/slug.json"]}
```

- **`argv`:** a list, never a shell string. It must match one of your registered command prefixes and
  argument patterns.
- **`expected_writes`:** any other file the command writes fails the run.
- **`cwd`** (optional): the project-relative working directory. It must equal the matching command entry's
  pinned `cwd` (default `.`).
- **`stdin_from_content`** (optional): `{"path": "<project-relative path>", "content": "<text>"}`, piped to the
  command on standard input, e.g. a draft to `lake env lean --stdin`. Only a command entry that registers
  `stdin_gates` accepts it; those gates run on the content first (`path` is context for them), and any finding
  refuses the request. The content is never written to the project.

## The runner

The orchestrator's `agentteams` commands queue requests for an out-of-session runner. The operator starts it
outside every agent session:

```
agentteams --serve-requests --project <root> --description <brief>
```

- **The ledger key** is read from `~/.config/agentteams/keys/proposal-ledger.key` (mode 0600), or from the
  file named by `AGENTTEAMS_PROPOSAL_LEDGER_KEY_FILE`. Agent sessions can't read that directory, and can't
  write `.agentteams/`.
- **The brief is pinned** at start. If it changes, the runner stops and must be restarted.
- **Confinement.** The runner runs every command and gate in an OS sandbox, configured per agent by
  `confined_programs`: `{"agent": {"exec": [...], "write": [...]}}`.
  - It comes from the operator's file, `~/.config/agentteams/confined/<project>-<hash>.json`
    (`agentteams --confined-path`; install it with `agentteams --install-confined FILE`, which prints the JSON
    and its sha256 and installs only with a matching `--confirm-review-sha256`), so machine paths
    stay out of the committed brief. With no such file, the brief's block applies. Both at once are refused.
    Its reserved `gate_exec` key can also hold gates' `exec` paths (P5c), instead of the brief. Each is bound to
    its gate's argv (`gate_argv_sha256`, written by `--install-confined`): change a gate's argv and the file must
    be reinstalled.
    The file is pinned at start like the brief, and must be yours and not group- or world-writable.
  - Writes go only to the declared roots and a private `TMPDIR`. The ledger, the queue, `.git` and the
    control plane stay protected, and the key directory is unreadable.
  - On macOS only the declared `exec` paths can run. Give the toolchain *root* (e.g. `~/.elan`): Homebrew
    Python, for one, re-executes a binary inside its framework.
  - Changes inside the write roots count as declared.
  - With no usable sandbox the runner refuses, unless the brief sets `allow_unconfined_runs` (each such run
    is logged).
- **Crash recovery:** a stale heartbeat makes every request refuse. Restart the runner and re-queue.

## Exit codes (`agentteams --apply-proposal` / `--run-request`)

| Code | Meaning |
|---|---|
| 0 | Applied, or the command ran (`--run-request` passes the command's own exit code through) |
| 1 | Refused: schema, nonce, scope, protected path, stale base, gate or allowlist. Stderr carries a `refused:` line; without one, a `--run-request` exit 1 is the command's own |
| 3 | The command wrote outside `expected_writes`, or timed out |
<!-- AGENTTEAMS:END content -->
