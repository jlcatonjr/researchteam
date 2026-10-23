# `_release` — ResearchTeam

Release-line pins: verify a signed release tag and find the newest one on a release line. A repository is *release-locked* when its `toolchain.lock` records a tag beside a pin. The `name=owner/repo@sha` lines keep their old format, so older readers still parse the lock. A release-locked pin moves only to a newer tag on the same `vX.Y` line, and only after that tag verifies: it is an annotated tag; `git tag -v` passes against the operator's `allowed_signers` under neutralised git configuration; the signing key's fingerprint is one of the release keys named in this module, not just any good signature; and the verified tag object equals the one the remote advertises. The pin is then the tag's peeled commit. The module is stdlib-only; `scripts/check_toolchain.py` imports it, and `researchteam update` uses `locked_layer2_ref` to decide which researchteam commit to sync from.

> *Source: `researchteam/_release.py`*

> **Stability.** researchteam's modules are underscore-prefixed. The supported interface is the `researchteam` CLI ([CLI reference](../cli-reference.md)). The functions on this page are documented for contributors and may change between releases.

---

## File format: `toolchain.lock`

```text
researchteam=jlcatonjr/researchteam@<peeled 40-hex sha>
agentteams=jlcatonjr/agentteams@<peeled 40-hex sha>
agentteams.tag=v1.0.0-rc.10
```

A `<name>.tag=` line makes that pin release-locked. Lines that start with neither `<name>=` (and contain `@`) nor `<name>.tag=` are ignored, so comment lines are allowed.

---

## Constants

| Name | Value | Meaning |
|------|-------|---------|
| `RELEASE_KEY_FINGERPRINTS` | `frozenset({"SHA256:IPdnLwlFdHNhr7QGKVWU40BOKyYzv2u8qxP/qxnzTNM"})` | Operator release keys (agentteams `SECURITY.md`, "Release signers"), from `v1.0.0-rc.9` onward. |
| `DEFAULT_ALLOWED_SIGNERS` | `~/.config/agentteams/allowed_signers` | Default `allowed_signers` path. It lies outside every write root: agents may read it, never write it. |
| `TAG_RE` | `^v(\d+)\.(\d+)\.(\d+)(?:-rc\.(\d+))?$` | A release tag: `vX.Y.Z` or `vX.Y.Z-rc.N`. |

The environment variable `AGENTTEAMS_ALLOWED_SIGNERS`, when set and non-empty, overrides `DEFAULT_ALLOWED_SIGNERS` (an operator-run CI job may point it at a copy provisioned from a repository secret).

---

## Classes

### `ReleaseError`

Subclass of `RuntimeError`. A tag that is not a verified release, or a release line that cannot be read.

---

## Functions

### `tag_key(tag)`

Sort key for release tags: patch order, with a final release sorting after every RC of the same version.

**Args:**

- `tag` (`str`) — A release tag name.

**Returns:** `tuple[int, int, int, int, int]` — `(major, minor, patch, 1, 0)` for a final release; `(major, minor, patch, 0, N)` for `-rc.N`.

**Raises:**

- `ReleaseError` — If `tag` does not match `TAG_RE`.

**Example:**

```python
from researchteam._release import tag_key

tag_key("v1.0.0-rc.10")  # (1, 0, 0, 0, 10)
tag_key("v1.0.0")        # (1, 0, 0, 1, 0)
```

---

### `release_line(tag)`

The `vX.Y` release line of a tag.

**Args:**

- `tag` (`str`) — A release tag name.

**Returns:** `str` — For example `"v1.0"` for `v1.0.3` or `v1.0.0-rc.10`.

**Raises:**

- `ReleaseError` — If `tag` is not a release tag.

---

### `allowed_signers_path()`

The `allowed_signers` file to verify against: `AGENTTEAMS_ALLOWED_SIGNERS` if set and non-empty, else `DEFAULT_ALLOWED_SIGNERS`, with `~` expanded.

**Returns:** `str`

---

### `release_signers(path, dest)`

Copy into `dest` only the `allowed_signers` lines whose key is a release key, so the file the environment names is never trusted beyond the pinned fingerprints. Blank and `#` comment lines are skipped. For each line, the first `ssh-*`, `ecdsa-*` or `sk-*` key is fingerprinted with `ssh-keygen -lf -`; the line is kept when the fingerprint is in `RELEASE_KEY_FINGERPRINTS`. `dest` is always written, empty if nothing matched.

**Args:**

- `path` (`str`) — Source `allowed_signers` file.
- `dest` (`str`) — File to write the kept lines to.

**Returns:** `int` — Number of lines kept.

**Raises:**

- `OSError` — If `path` cannot be read or `dest` cannot be written.

---

### `remote_tags(repo)`

The release tags on `https://github.com/<repo>`, from `git ls-remote --tags ... refs/tags/v*`. Peeled `^{}` entries and names that do not match `TAG_RE` are skipped.

**Args:**

- `repo` (`str`) — `owner/repo` on GitHub.

**Returns:** `dict[str, str]` — `{tag name: advertised tag object}`.

**Raises:**

- `ReleaseError` — If `ls-remote` fails, cannot run, or times out.

---

### `newest_on_line(repo, current)`

The newest release tag on `current`'s `vX.Y` line that sorts after `current`. The candidate is not verified here; call `verify_tag` before moving a pin to it.

**Args:**

- `repo` (`str`) — `owner/repo` on GitHub.
- `current` (`str`) — The currently pinned tag.

**Returns:** `str | None` — The tag name, or `None` if there is no newer tag on the line.

**Raises:**

- `ReleaseError` — If `current` is not a release tag or the remote tags cannot be listed.

---

### `verify_tag(repo, tag)`

Verify a signed release tag and return its tag object and peeled commit. The tag is fetched into a temporary bare repository, then checked in this order:

1. `tag` matches `TAG_RE`.
2. The `allowed_signers` file exists.
3. The remote advertises the tag.
4. The fetched ref resolves to a 40-hex object of type `tag` (a lightweight tag is refused).
5. The fetched tag object equals the advertised one.
6. The `allowed_signers` file holds at least one release key (`release_signers`).
7. `git tag -v`, using only the release keys as `gpg.ssh.allowedSignersFile`, exits 0 and its stderr carries a `Good "git" signature ... key SHA256:...` line; every such fingerprint must be a release key. Only stderr is read, since stdout carries the tag message, which the tagger controls.
8. The tag peels to a 40-hex commit.

**Args:**

- `repo` (`str`) — `owner/repo` on GitHub.
- `tag` (`str`) — Release tag name.

**Returns:** `tuple[str, str]` — `(tag object sha, peeled commit sha)`.

**Raises:**

- `ReleaseError` — If any check fails, or a git command cannot run or times out.

---

### `read_lock_pin(root, name)`

Read one tool's pin from `<root>/toolchain.lock`. When a line appears more than once, the last one wins.

**Args:**

- `root` (`os.PathLike[str] | str`) — Repository root.
- `name` (`str`) — Tool name, e.g. `"researchteam"` or `"agentteams"`.

**Returns:** `tuple[str, str, str | None] | None` — `(owner/repo, sha, tag or None)`; `None` if the lock is unreadable or has no `<name>=...@...` line. A `<name>.tag=` line without a pin line also yields `None`.

**Example:**

```python
from researchteam._release import read_lock_pin

read_lock_pin(".", "agentteams")
# ("jlcatonjr/agentteams", "<sha>", "v1.0.0") for the lock shown above with agentteams.tag=v1.0.0
```

---

### `locked_layer2_ref(root, upstream_repo)`

The researchteam commit to sync Layer 2 from when `toolchain.lock` release-locks researchteam. The caller fails closed on `ReleaseError`.

**Args:**

- `root` — Repository root (anything `read_lock_pin` accepts).
- `upstream_repo` (`str`) — Expected `owner/repo` for researchteam.

**Returns:** `tuple[str, str] | None` — `(peeled sha, tag)`; `None` when the lock has no researchteam pin or the pin carries no tag.

**Raises:**

- `ReleaseError` — If the lock names another repository, the tag does not verify (`verify_tag`), or the pinned commit is not the tag's peeled commit.

---

### Private helpers

| Name | Purpose |
|------|---------|
| `_git(args, cwd=None, timeout=60)` | Run git with neutralised configuration: `core.hooksPath=/dev/null`, `core.fsmonitor=false`, `gpg.format=ssh`, `gpg.ssh.program=ssh-keygen`; all `GIT_*` environment variables removed; `GIT_TERMINAL_PROMPT=0`, `GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_NOSYSTEM=1`. Raises `ReleaseError` on `OSError` or timeout. |
| `_SHA` | `^[0-9a-f]{40}$`. |
| `_GOOD_SIG` | Whole-line match of `git tag -v`'s good-signature message, capturing the `SHA256:` fingerprint. |
| `_NEUTRAL` | The `-c` options `_git` prepends. |

---

## See Also

- [`index`](index.md) — API reference overview.
- [`update`](update.md) — syncs from the verified tag when the lock is release-locked.
- [`doctor`](doctor.md) — reports the toolchain pin.
- [`drift`](drift.md) — `pinned_ref` reads the researchteam pin.
- [`agentteams-provenance`](agentteams-provenance.md) — checks which agentteams code a render runs.
- [`fetch`](fetch.md) — fetches files from GitHub at a ref (this module uses git directly).
- [CLI reference](../cli-reference.md)
