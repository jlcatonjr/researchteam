# Toolchain group: adopt researchteam's own signed file, sequence 5 (2026-11-23)

Part of the decision-key rotation from `op-2026` to `opr-2026-11`. `.agentteams/toolchain-group.json` was the last
signed document on `main` that only `op-2026` could verify. The operator ruled that researchteam gets its own file,
listing this workspace alone, and signed it on 2026-11-23.

## What changes

| | Sequence 1 (replaced) | Sequence 5 (adopted) |
|---|---|---|
| Key | `op-2026` | `opr-2026-11` |
| Group | four repositories | the same four |
| `derives_from` | `s10-first-party-releases-2026-11` | the same |
| Workspaces | 15 | this repository only |

- `.agentteams/toolchain-group.json`: the signed bytes, unchanged (sha256
  `7cc58607acdca592cb06ddc5ec0cda1561a2cb4aeb1ddf41cdc39dc92e2ec55d`).
- `.github/agents/references/exception-registry.json`: `toolchain_group_sequence` 1 to 5, written by agentteams'
  `load_group(consume=True)`, not by hand. After the merge, the sequence 1 file is refused as a rollback.

## Steps

1. Check the signed file's hash and compare its fields with the sequence 1 file.
2. Copy it in; verify against the `.github` and `.codex` stores ("Toolchain group verified (sequence 5)").
3. Record the high-water mark through agentteams.
4. `@security` review naming both paths (a trust root and a governance path).
5. Operator's merge answer naming the pull request and head; merge; verify on `main`.
6. Tell the release coordinator session.

## Not changed

- No decision row targets the file (it is a trust root). No verify key is added or removed; `op-2026` stays in the
  stores until its retirement plan.
- The earlier file stays in history with its workspaces list. Operator ruling, 2026-11-23 (picker): "Accept history".
  The list holds repository names only, and removing it would need a rewrite and force-push of `main`, which PS-2
  and the rulesets forbid.
- What the group lifts is unchanged: the S-10 cooldown and the per-release decision row for group members only.
