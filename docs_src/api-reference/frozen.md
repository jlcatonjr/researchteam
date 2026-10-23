# `_frozen` — ResearchTeam

Declared frozen surfaces: the contract shared by agentteams and researchteam (introduced in researchteam 1.0.1). `brief.json` may carry `frozen_surfaces`, a JSON array of unique framework ids. For every listed surface, researchteam never renders, merges, projects, converts, bridges, Notes-syncs, managed-syncs, overwrites or deletes that surface's files, including the root paths it owns. The one write it makes is restoring a frozen `AGENTS.md`'s own earlier bytes after an unfrozen render touched it. agentteams 1.0.x honours the same key with the same meaning; agentteams' freeze manifest and `--freeze-surface` are agentteams-only. An absent key or `[]` freezes nothing. An unknown id, a duplicate or a non-array value refuses the run. Removing a surface researchteam previously recorded as frozen is an *unfreeze*, which is constraint-relaxing and needs an operator-signed decision row verified by the pinned agentteams' own security gate.

> *Source: `researchteam/_frozen.py`*

> **Stability.** researchteam's modules are underscore-prefixed. The supported interface is the `researchteam` CLI ([CLI reference](../cli-reference.md)). The functions on this page are documented for contributors and may change between releases.

---

## Constants

| Name | Value | Meaning |
|------|-------|---------|
| `SURFACE_IDS` | `("copilot-vscode", "copilot-cli", "claude", "goose", "agents-md", "codex", "grok")` | The allowed ids in `frozen_surfaces`. |
| `OWNED` | `dict[str, tuple[str, ...]]` (below) | Repository-relative paths each surface owns; a trailing `/` means the whole directory. |
| `AGENTS_MD` | `"AGENTS.md"` | The root file several surfaces can own. |
| `AGENTS_MD_OWNERS` | `frozenset({"codex", "goose", "agents-md"})` | Listing any of these freezes the root `AGENTS.md`. |
| `MARKER_KEY` | `"frozen_surfaces"` | Key name in both `brief.json` and `.researchteam`. |

`OWNED`:

| Surface | Owned paths |
|---------|-------------|
| `copilot-vscode` | `.github/agents/` |
| `copilot-cli` | `.github/agents/` |
| `claude` | `.claude/agents/` |
| `goose` | `.goose/`, `.goosehints`, `scripts/goose-run-resilient.py`, `scripts/goose-openrouter-route-proxy.py`, `scripts/goose-coordination-mcp.py` |
| `agents-md` | (none besides `AGENTS.md`) |
| `codex` | `.codex/`, `.agents/skills/` |
| `grok` | `.grok/` |

The Goose entries outside `.goose/` are files agentteams' Goose emitter writes on every render; the coordination MCP script is owned whether or not coordination is on.

---

## File formats

### `brief.json`

```json
{
  "frozen_surfaces": ["claude", "codex"]
}
```

### `.researchteam` marker

The frozen set researchteam last honoured, written by `record` (ids sorted, comma-separated). `recorded` accepts commas or spaces as separators:

```ini
frozen_surfaces = claude, codex
```

---

## Classes

### `FrozenSurfacesError`

Subclass of `ValueError`. A `frozen_surfaces` value researchteam cannot honour exactly; the run refuses.

---

## Functions

### `load(root)`

The validated frozen set from `brief.json`.

**Args:**

- `root` (`Path`) — Repository root.

**Returns:** `frozenset[str]` — The listed surface ids; empty when `brief.json` is missing, is not a JSON object, or has no `frozen_surfaces` key.

**Raises:**

- `FrozenSurfacesError` — If `brief.json` exists but cannot be read or parsed; if the value is not a JSON array; if it contains a non-string or an id not in `SURFACE_IDS`; or if it contains duplicates.

---

### `owned_paths(frozen)`

Every path a frozen set owns, sorted, with `AGENTS.md` appended when any of `AGENTS_MD_OWNERS` is listed.

**Args:**

- `frozen` (`frozenset[str]`) — Surface ids (each must be a key of `OWNED`).

**Returns:** `tuple[str, ...]`

**Raises:**

- `KeyError` — If `frozen` contains an id not in `OWNED`. `load` guarantees it does not.

---

### `is_frozen_path(rel, frozen)`

Whether a repository-relative path belongs to a frozen surface. A leading `./` is stripped. A directory entry matches the directory itself and anything under it; a file entry matches only exactly.

**Args:**

- `rel` (`str`) — Repository-relative path.
- `frozen` (`frozenset[str]`) — Surface ids.

**Returns:** `bool`

**Example:**

```python
from researchteam._frozen import is_frozen_path

is_frozen_path(".claude/agents/navigator.md", frozenset({"claude"}))  # True
is_frozen_path("AGENTS.md", frozenset({"codex"}))                    # True
is_frozen_path("AGENTS.md", frozenset({"claude"}))                   # False
```

---

### `snapshot(root, frozen)`

SHA-256 of every file under the frozen paths. Directories are walked recursively; symlinks are skipped. A file path that does not exist is recorded with the value `"absent"`.

**Args:**

- `root` (`Path`) — Repository root.
- `frozen` (`frozenset[str]`) — Surface ids.

**Returns:** `dict[str, str]` — `{relative path: sha256 hex digest or "absent"}`.

---

### `changed_since(root, frozen, before)`

Frozen files added, removed or modified since `snapshot` returned `before`.

**Args:**

- `root` (`Path`) — Repository root.
- `frozen` (`frozenset[str]`) — Surface ids.
- `before` (`dict[str, str]`) — An earlier `snapshot` result.

**Returns:** `list[str]` — Sorted relative paths whose digest differs.

**Example:**

```python
from pathlib import Path
from researchteam import _frozen

root = Path(".")
frozen = _frozen.load(root)
before = _frozen.snapshot(root, frozen)
# ... render ...
touched = _frozen.changed_since(root, frozen, before)
```

---

### `recorded(root)`

The frozen set researchteam last honoured, from the `frozen_surfaces` line of `.researchteam`. Ids not in `SURFACE_IDS` are dropped silently (unlike `load`, which refuses them).

**Args:**

- `root` (`Path`) — Repository root.

**Returns:** `frozenset[str]` — Empty when the marker is unreadable or has no such line.

---

### `at_head(root)`

The union of the frozen sets that `brief.json` and `.researchteam` declare at git `HEAD`, read with `git show HEAD:<file>` (hooks disabled, 20-second timeout). Used so that removing a surface from both files in the working tree still counts as an unfreeze. Unknown ids and unreadable or non-list values are ignored.

**Args:**

- `root` (`Path`) — Repository root.

**Returns:** `frozenset[str]` — Empty outside git, when the files are absent at `HEAD`, or when git fails or times out.

---

### `record(root, frozen)`

Write the honoured frozen set to `.researchteam`, only when it differs from `recorded(root)`. An existing `frozen_surfaces` line is replaced (with an empty line when `frozen` is empty, and each `\n\n\n` then replaced by `\n\n`); otherwise the line is appended. The marker is never created: if `.researchteam` does not exist, nothing is written.

**Args:**

- `root` (`Path`) — Repository root.
- `frozen` (`frozenset[str]`) — The set to record.

**Returns:** `bool` — Whether the file was written.

---

### `verify_unfreeze(root, surface, launcher)`

Ask the pinned agentteams, under its own interpreter, whether `unfreeze-<surface>` is authorised. The check runs `<interpreter> -I -c <script> <root>/.github/agents unfreeze-<surface>` with `cwd="/"` and a 60-second timeout, and reads a JSON line `{"ok": ..., "why": ...}` from the last line of stdout. The script refuses unless all of these hold:

1. The agentteams install provides `check_clearance`, `_latest_security_decision`, `derive_effect_class`, `requires_operator_signature` and `RELAXING` (older installs refuse).
2. A bare `unfreeze-<surface>` probe row with no `effect_*` declarations derives as `RELAXING` (agentteams 1.0.0 and earlier do not, and are refused).
3. `check_clearance` clears the action.
4. No security waiver exists for the action (a waiver is accepted by the gate before any row signature is checked, so it is refused here), and the install can check for one.
5. The latest decision row for the action exists and `requires_operator_signature` is true for it.
6. The row's `sig_scheme` is `ed25519` and its `signature` is non-empty.

**Args:**

- `root` (`Path`) — Repository root.
- `surface` (`str`) — Surface id being unfrozen.
- `launcher` (`str | None`) — Path to the `agentteams` launcher; its interpreter is found with [`launcher_interpreter`](agentteams-provenance.md).

**Returns:** `tuple[bool, str]` — `(authorised, reason)`. Returns `(False, ...)` when `launcher` is falsy, its interpreter cannot be found or is not executable, or the check cannot run or returns unparseable output.

---

### Private helpers

| Name | Purpose |
|------|---------|
| `_MARKER_RE` | Multiline regex `^frozen_surfaces\s*=\s*(.*)$` for the `.researchteam` line. |
| `_VERIFY` | The Python script `verify_unfreeze` runs under agentteams' interpreter. |
| `_run` | `subprocess.run`, bound at import so test fakes of `subprocess.run` do not reach these calls. |

---

## See Also

- [`index`](index.md) — API reference overview.
- [`update`](update.md) — enforces frozen surfaces during a sync and records the honoured set.
- [`doctor`](doctor.md) — reports the frozen set and any pending unfreeze.
- [`agentteams-provenance`](agentteams-provenance.md) — `launcher_interpreter`.
- [`notes`](notes.md) — the Notes sync that frozen surfaces exclude.
- [CLI reference](../cli-reference.md)
