# `_term_core_upstream` — ResearchTeam

Compares the pinned copy of the agentteams term-index core (`scripts/term-index-core/`) with the signed agentteams tag its manifest names. The offline check, `scripts/check_term_core.py`, proves only that the copied files match `PINNED.json`. Anyone who can merge can change a copy and its manifest together, so this network comparison is the proof that the manifest matches upstream. It needs the signed tag: comparing with an installed agentteams proves nothing, because a copy taken from that install matches it by construction.

> *Source: `researchteam/_term_core_upstream.py`*

> **Stability.** This module is underscore-prefixed. The supported interface is the `researchteam` CLI ([CLI reference](../cli-reference.md)); the functions below are documented for contributors and may change between releases.

---

## Usage

```text
python -m researchteam._term_core_upstream [--root PATH] [--allow-lock-difference]
```

Each step fails closed:

1. the offline check passes;
2. the manifest's tag verifies as a signed release tag (`_release.verify_tag`) and peels to the manifest's commit;
3. the tag, fetched again with its tree into a temporary bare repository, is the same tag object and peels to the same commit;
4. every listed file, read from that commit with `git cat-file blob`, has the manifest's sha256;
5. the manifest's commit is the agentteams commit `toolchain.lock` pins. At every researchteam release the two must be equal. `--allow-lock-difference` reports a difference without failing.

| Exit | Meaning |
|------|---------|
| 0 | Every step passed. |
| 1 | A hash, commit or lock mismatch (or the offline check found a mismatched, missing or unlisted file). |
| 2 | Cannot verify: no `allowed_signers`, a network or git failure, or a malformed manifest. |

It needs the operator's `allowed_signers` file (see [`release.md`](release.md)). A workflow job is to run it on every pull request that touches `scripts/term-index-core/`; that job is a separate change under `.github/workflows/`. The test `tests/test_term_core_pin.py` runs it when `RT_NETWORK_TESTS=1`.

---

## Functions

### `compare(root: Path, *, allow_lock_difference: bool = False) -> tuple[int, list[str]]`

Runs the steps above for the repository at `root`. Returns the exit code and the report lines (the offline check's lines, then `[term-core-upstream] ...` lines).

### `blob_mismatches(manifest: dict, read_blob) -> list[str]`

One report line for every listed file (modules and data files) whose upstream blob is absent (`read_blob` returned `None`) or hashes differently from the manifest. `read_blob(upstream_path)` returns the file's bytes at the pinned commit.

### `main(argv: list[str] | None = None) -> int`

The command line above. Prints the report lines and returns the exit code.

### Private helpers

| Function | Behaviour |
|----------|-----------|
| `_load_offline_check(root)` | Loads the repository's own `scripts/check_term_core.py` by path. |
| `_git_bytes(args, cwd, timeout=300)` | `git` with the neutral configuration `_release` uses, returning raw bytes. |
| `_fetch_tree_reader(repo, tag, tag_object, commit, tmp)` | Fetches the tag with its tree (depth 1), confirms the tag object and peeled commit, and returns a blob reader. |

---

## See Also

- [`scripts.md`](scripts.md) — `check_term_core.py`, the offline check.
- [`release.md`](release.md) — `verify_tag` and `toolchain.lock`.
- [`doctor.md`](doctor.md) — check 5b', which relays the offline check.
