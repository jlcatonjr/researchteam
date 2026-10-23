# `_manifest` — ResearchTeam

Static data that defines what researchteam owns in a derived repository: the upstream repository and branch, the layer-2 managed-file sets that `researchteam update` syncs, how each managed file is merged, the fence markers that delimit upstream-owned regions, and what `init` skips, replaces and renders. The module has one function, `managed_files_for`, which selects the managed-file set for a brief's `layer2_profile`.

`brief.json`, `Projects/` and `references/` are user-owned and are never in a managed set.

> *Source: `researchteam/_manifest.py`*

> **Stability.** This module is underscore-prefixed. The supported interface is the `researchteam` CLI ([CLI reference](../cli-reference.md)); the functions below are documented for contributors and may change between releases.

---

## Constants

### Upstream and placeholder

| Name | Value | Purpose |
|------|-------|---------|
| `UPSTREAM_REPO` | `"jlcatonjr/researchteam"` | Repository that `init` downloads and `update` fetches from. |
| `UPSTREAM_BRANCH` | `"main"` | Default `--ref` for `init`, and the fallback ref when `.researchteam` records none. |
| `BRIEF_PLACEHOLDER` | `"<YOUR PROJECT NAME>"` | The `project_name` written into a freshly scaffolded `brief.json`. `update` and `materialize` refuse the layer-1 agentteams pass while this string is still in `brief.json`. Must match `scaffold/brief.template.json`. |

### Layer-2 managed files

`FRAMEWORK_MANAGED_FILES` — synced to every derived repo, whatever its profile (18 files):

| Path | Merge strategy |
|------|----------------|
| `CLAUDE.md` | `fenced-preserve` |
| `.gitignore` | `fenced-preserve` |
| `docs/claude-interface-bridge.md` | overwrite |
| `docs/agentteams-update-policy.md` | overwrite |
| `docs/agent-infrastructure-authority.md` | overwrite |
| `docs/researchteam-framework.md` | overwrite |
| `docs/retrieval-surfaces.md` | overwrite |
| `docs/on-the-fly-retrieval-profile.md` | overwrite |
| `.claude/README.md` | overwrite |
| `.claude/checklists/research-task-preflight.md` | overwrite |
| `.claude/prompts/research-report.prompt.md` | overwrite |
| `scripts/claude_researchteam_bridge.sh` | overwrite |
| `scripts/validate_agentteams_update.sh` | overwrite |
| `scripts/agentteams_autosync_gate.sh` | overwrite |
| `scripts/sign_security_decision.py` | overwrite |
| `scripts/check_toolchain.py` | overwrite |
| `scripts/bootstrap_toolchain.sh` | overwrite |
| `.claude/settings.toolchain.example.json` | overwrite |

`toolchain.lock` itself is not managed: it is repo-owned and written by the autosync gate after a green sync. `.claude/settings.toolchain.example.json` is a SessionStart hook example that the operator merges into `.claude/settings.json` by hand.

`SCHOLARLY_MANAGED_FILES` — synced only when the profile is scholarly (12 files):

| Path | Merge strategy |
|------|----------------|
| `docs/citation-claim-audit-protocol.md` | overwrite |
| `docs/literature-library-protocol.md` | overwrite |
| `docs/news-perspective-protocol.md` | overwrite |
| `docs/historical-context-protocol.md` | overwrite |
| `scripts/check_methodology_coverage.sh` | overwrite |
| `scripts/check_historical_context.sh` | overwrite |
| `scripts/check_citation_integrity.sh` | overwrite |
| `scripts/build_literature_library.py` | overwrite |
| `scripts/query_literature_library.py` | overwrite |
| `scripts/check_literature_library_integrity.sh` | overwrite |
| `.github/agents/interpretation-advisor.agent.md` | `above-notes` |
| `.github/agents/references/methodology/_TEMPLATE.methodology.guide.md` | overwrite |

Before researchteam 1.0.0 these two were seeded only at `init`; `update` now syncs them.

| Name | Value | Purpose |
|------|-------|---------|
| `SEEDED_FILES` | `[]` (`list[str]`) | Files `init` seeds but `update` never syncs. `doctor --drift` compares their upstream-owned part (everything before `## Project-Specific Notes`) with upstream at the pinned researchteam commit. Currently empty: both former entries became managed. |
| `MANAGED_FILES` | `FRAMEWORK_MANAGED_FILES + SCHOLARLY_MANAGED_FILES` | Backwards-compatible flat list equal to the full scholarly set. |

### Merge strategies

`MERGE_STRATEGIES` (`dict[str, str]`) maps a managed path to how `update` reconciles it. Any managed path not listed uses `"overwrite"`.

| Strategy | Paths | Behaviour |
|----------|-------|-----------|
| `overwrite` (default) | every managed file not listed below | The local file is replaced wholesale with the upstream file. |
| `fenced-preserve` | `.gitignore`, `CLAUDE.md` | Only the block between the `researchteam:managed` begin and end markers is replaced; every line outside it (for example `CLAUDE.md`'s personalized project header) is kept. |
| `above-notes` | `.github/agents/interpretation-advisor.agent.md` | Upstream owns the file from line 1 (front matter included) down to its `## Project-Specific Notes` heading; that heading and everything after it belong to the repo. Upstream-authored Notes reach the repo through the `researchteam:notes` block (see [`notes`](notes.md)). |

`README.md` is deliberately not managed: it is generated per project from `scaffold/README.template.md` and never re-synced.

### Fence markers

A line is a begin or end marker when its stripped form contains the corresponding core string, so both the shell-comment form (`.gitignore`) and the HTML-comment form (Markdown) are recognized, including any trailing prose.

| Name | Value |
|------|-------|
| `FENCE_BEGIN` | `"# >>> researchteam:managed"` |
| `FENCE_END` | `"# <<< researchteam:managed"` |
| `FENCE_CORE_BEGIN` | `">>> researchteam:managed"` |
| `FENCE_CORE_END` | `"<<< researchteam:managed"` |
| `FENCE_BEGIN_MD` | `"<!-- >>> researchteam:managed — synced from upstream; do not edit inside this block -->"` |
| `FENCE_END_MD` | `"<!-- <<< researchteam:managed -->"` |

The Markdown forms are used in `CLAUDE.md` because they are invisible when rendered; a bare `#` line would render as a heading. Matching in `update` and [`personalize`](personalize.md) uses `FENCE_CORE_BEGIN` / `FENCE_CORE_END`.

### `init` scaffolding

`INIT_SKIP_PREFIXES` (`list[str]`) — paths excluded when extracting the template. An entry matches the exact path (trailing `/` removed) or anything below it.

| Entry | Reason |
|-------|--------|
| `Projects/` | User content. |
| `.projects/` | Tracked upstream example project. |
| `.git/` | |
| `tmp/` | |
| `.github/agents/.agentteams-backups/` | |
| `.github/workflows/` | Replaced by the bundled derived-repo workflow. |
| `references/plans/` | |
| `researchteam/` | The Python package itself. |
| `pyproject.toml` | Packaging metadata. |
| `.researchteam` | Generated fresh by `init`. |
| `workSummaries/` | |
| `brief.json` | Generated from `scaffold/brief.template.json`. |
| `README.md` | Generated from `scaffold/README.template.md`. |
| `CLAUDE.md` | Generated from `scaffold/CLAUDE.template.md`. |
| `mkdocs.yml` | The framework's own documentation site. |
| `docs_src/` | Framework documentation site sources. |
| `.github/ci/requirements-docs.txt` | Framework documentation site build requirements. |

| Name | Value | Purpose |
|------|-------|---------|
| `INIT_SCAFFOLD_REPLACEMENTS` | `{".github/workflows/agentteams-sync.yml": "agentteams-sync-derived.yml"}` | Destination path → bundled file in `researchteam/scaffold/` copied in at `init`. |
| `INIT_RENDER_TEMPLATES` | `{"README.md": "README.template.md", "CLAUDE.md": "CLAUDE.template.md"}` | Destination path → template in `researchteam/scaffold/` rendered with `brief.json` token substitution by [`personalize`](personalize.md). |

---

## Functions

### `managed_files_for(profile: str | None) -> list[str]`

> *Source: `researchteam/_manifest.py`*

Return the layer-2 managed-file set for a brief's `layer2_profile`. `update` reads the profile from `brief.json` (a missing brief, invalid JSON, an absent field or a non-string value give `None`; a brief that is not a JSON object raises) and syncs the returned list, except paths under a frozen surface and `above-notes` files kept local.

**Args:**

- `profile` (`str | None`) — The `layer2_profile` value. It is stripped and lower-cased; `None` or an empty string is treated as `"scholarly"`.

**Returns:** `list[str]` — A new list. For `"generic"`, a copy of `FRAMEWORK_MANAGED_FILES`. For any other value, including `None`, `"scholarly"` and unrecognized strings, `FRAMEWORK_MANAGED_FILES` followed by `SCHOLARLY_MANAGED_FILES`. This keeps every repo that predates the profile field on the full scholarly set.

**Example:**

```python
from researchteam._manifest import managed_files_for

generic = managed_files_for("generic")      # framework files only
scholarly = managed_files_for(None)         # framework + scholarly files
```

---

## See Also

- [`index.md`](index.md) — API reference overview.
- [`update.md`](update.md) — layer-2 sync that consumes these sets and strategies.
- [`init.md`](init.md) — uses the `INIT_*` constants.
- [`personalize.md`](personalize.md) — uses `INIT_RENDER_TEMPLATES` and the fence cores.
- [`notes.md`](notes.md) — the `researchteam:notes` block for `above-notes` files.
- [`frozen.md`](frozen.md) — managed paths under a frozen surface are not synced.
- [`doctor.md`](doctor.md) — `SEEDED_FILES` check under `--drift`.
- [`fetch.md`](fetch.md) — how managed files are downloaded.
- [`../cli-reference.md`](../cli-reference.md) — command-line reference.
