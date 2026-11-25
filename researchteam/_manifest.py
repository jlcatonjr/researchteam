UPSTREAM_REPO = "jlcatonjr/researchteam"
UPSTREAM_BRANCH = "main"

# Placeholder sentinel written into a freshly-scaffolded brief.json's project_name. `update` and
# `materialize` refuse the layer-1 agentteams pass while this string is still present, so a user
# cannot bake the placeholder identity into ~30 generated agent files by running generation before
# editing the brief. Keep in sync with the value in scaffold/brief.template.json.
BRIEF_PLACEHOLDER = "<YOUR PROJECT NAME>"

# ---------------------------------------------------------------------------
# Layer-2 managed files (owned and synced by researchteam, not agentteams).
# Paths are relative to repo root. brief.json, Projects/ and references/ are user-owned and never
# touched by `update`.
#
# The set is split so a derived repo can be EITHER a scholarly research instance (the framework's
# original specialization) OR a generic-domain instance. `brief.json` carries a `layer2_profile`
# field ("scholarly" | "generic"); when it is absent the profile defaults to "scholarly" so every
# pre-existing instance keeps exactly the files it has today (backward-compatible).
# ---------------------------------------------------------------------------

# Framework-neutral files that EVERY derived repo receives regardless of domain.
FRAMEWORK_MANAGED_FILES = [
    "CLAUDE.md",                                   # fenced-preserve (see MERGE_STRATEGIES)
    ".gitignore",                                  # fenced-preserve
    "docs/claude-interface-bridge.md",
    "docs/agentteams-update-policy.md",
    "docs/agent-infrastructure-authority.md",
    "docs/researchteam-framework.md",              # framework + CLI reference (see C4 sequencing)
    "docs/retrieval-surfaces.md",
    "docs/on-the-fly-retrieval-profile.md",
    ".claude/README.md",
    ".claude/checklists/research-task-preflight.md",
    ".claude/prompts/research-report.prompt.md",
    "scripts/claude_researchteam_bridge.sh",
    "scripts/validate_agentteams_update.sh",
    "scripts/agentteams_autosync_gate.sh",
    "scripts/sign_security_decision.py",           # operator-only signed clearance (H-1)
    # Toolchain pinning (OrthodoxLLM Item 3): toolchain.lock itself is repo-owned (written by the
    # autosync gate after a green sync), so it is NOT managed; these read and maintain it.
    "scripts/check_toolchain.py",
    "scripts/bootstrap_toolchain.sh",
    ".claude/settings.toolchain.example.json",    # SessionStart hook to merge by hand
]

# Scholarly-domain tooling — synced only when the brief's layer2_profile is "scholarly".
SCHOLARLY_MANAGED_FILES = [
    "docs/citation-claim-audit-protocol.md",
    "docs/literature-library-protocol.md",
    "docs/news-perspective-protocol.md",
    "docs/historical-context-protocol.md",
    "docs/concept-map-protocol.md",                # procedure; the exporter and component are vendored (templates/concept-map)
    "scripts/check_methodology_coverage.sh",
    "scripts/check_historical_context.sh",
    "scripts/check_citation_integrity.sh",
    "scripts/build_literature_library.py",
    "scripts/query_literature_library.py",
    "scripts/check_literature_library_integrity.sh",
    # Term register + synced occurrence index (docs/term-index-protocol.md). One engine
    # (term_index_engine.py) that the builder, the gate and the query import; the hook example is
    # merged by hand.
    "docs/term-index-protocol.md",
    "scripts/term_index_engine.py",
    "scripts/build_term_index.py",
    "scripts/check_term_index.py",
    "scripts/query_term_index.py",
    ".claude/settings.terms.example.json",
    # The pinned agentteams term-index core the engine's adapters load (researchteam 1.3.0): the loader and
    # offline check, then the directory's own .gitattributes, its manifest, the copied files and their licence.
    # Every file in the directory is listed here: the offline check refuses an unlisted code file but would not
    # notice a missing non-code file such as .gitattributes. The directory is synced as exact bytes
    # (BYTE_EXACT_PREFIXES).
    "scripts/check_term_core.py",
    "scripts/term-index-core/.gitattributes",
    "scripts/term-index-core/PINNED.json",
    "scripts/term-index-core/_term_text.py",
    "scripts/term-index-core/term_index.py",
    "scripts/term-index-core/LICENSE",
    # Survey toolkit, step A (docs/survey-toolkit.md, version 1): the shared core, the specification validator and
    # its generated JSON Schema, the ledger checks, the gates, and the three commands the bridge runs. Every file
    # of scripts/survey/ is listed: the commands import one another by file name.
    "docs/survey-toolkit.md",                      # the contract the tools implement and their messages cite
    "scripts/survey/survey_core.py",
    "scripts/survey/survey_spec.py",
    "scripts/survey/survey_ledger.py",
    "scripts/survey/survey_gates.py",
    "scripts/survey/survey_schema.py",
    "scripts/survey/study.schema.json",
    "scripts/survey/survey_validate.py",
    "scripts/survey/survey_status.py",
    "scripts/survey/survey_manifest.py",
    # Step B: the row files (4.1 evidence, 4.3 attribution, 4.8 bucket tables and years).
    "scripts/survey/survey_tables.py",
    "scripts/survey/survey_attribution.py",
    "scripts/survey/survey_evidence.py",
    # Step B part 2: the provenance record (4.6), the identity files and survey-registry (4.4).
    "scripts/survey/survey_provenance.py",
    "scripts/survey/survey_identity.py",
    "scripts/survey/survey_registry.py",
    # Step B part 2b: the batch merge (4.1, 4.4).
    "scripts/survey/survey_rows.py",
    # Step C: codes and adjudications (4.2) and survey-agreement.
    "scripts/survey/survey_codes.py",
    "scripts/survey/survey_agreement.py",
    # Step F: sign-off verification (6.2), reaching agentteams only as a child process.
    "scripts/survey/survey_verify.py",
    # OrthodoxLLM Item 1: formerly seeded at init only; now synced.
    ".github/agents/interpretation-advisor.agent.md",       # above-notes (see MERGE_STRATEGIES)
    ".github/agents/references/methodology/_TEMPLATE.methodology.guide.md",
]

# Managed files under these prefixes are fetched and written as bytes, never decoded, and synced as one set:
# scripts/check_term_core.py checks the copied files' sha256 against PINNED.json. The directory's own
# .gitattributes (one of these files) marks them -text -ident -filter, so git does not convert them in any
# repository that receives the directory. Before 1.3.0 nothing of this directory was synced.
BYTE_EXACT_PREFIXES = ("scripts/term-index-core/",)

# Files `init` seeds that `update` never syncs (not managed, not agentteams-rendered, not project
# content). `doctor --drift` compares their upstream-owned part (everything before
# `## Project-Specific Notes`) with upstream at the pinned researchteam commit. A file leaves this list
# when it becomes managed; the interpretation-advisor and the methodology template did in Item 1.
SEEDED_FILES: list[str] = []  # both former entries are managed since OrthodoxLLM Item 1

# Backwards-compatible flat list (scholarly default). Existing callers/tests that import
# MANAGED_FILES keep seeing the full scholarly set.
MANAGED_FILES = FRAMEWORK_MANAGED_FILES + SCHOLARLY_MANAGED_FILES


def managed_files_for(profile: str | None) -> list[str]:
    """Return the managed-file set for a brief's ``layer2_profile``.

    ``"generic"`` yields only the framework-neutral files; anything else (including ``None`` /
    absent) yields the full scholarly set, preserving the historical behaviour for every instance
    that predates the profile field.
    """
    if (profile or "scholarly").strip().lower() == "generic":
        return list(FRAMEWORK_MANAGED_FILES)
    return list(FRAMEWORK_MANAGED_FILES) + list(SCHOLARLY_MANAGED_FILES)


# How each managed file is reconciled on update.
# Default (any file NOT listed here) = "overwrite": wholesale replacement from upstream — the
# historical behavior for every doc and script. "fenced-preserve": only the upstream-owned block
# delimited by the researchteam:managed fence is replaced; every line OUTSIDE that fence is a
# derived-repo addition (e.g. CLAUDE.md's personalized project-identity header) and survives the
# sync. README.md is intentionally NOT managed — it is generated per-project at init from
# scaffold/README.template.md and never re-synced. See docs/agentteams-update-policy.md.
MERGE_STRATEGIES = {
    ".gitignore": "fenced-preserve",
    "CLAUDE.md": "fenced-preserve",
    # "above-notes": upstream owns the file from line 1 (front matter included) down to its
    # `## Project-Specific Notes` heading; that heading and everything after it stay the repo's.
    # Upstream-authored Notes reach the repo through the researchteam:notes block (_notes.py).
    ".github/agents/interpretation-advisor.agent.md": "above-notes",
}

# Sentinel comment lines delimiting the upstream-owned region of a fenced-preserve file. Matched
# by their sentinel CORE (below) on the stripped line, so BOTH the shell-comment idiom used by
# .gitignore (``# >>> researchteam:managed``) and the HTML-comment idiom used by markdown files
# (``<!-- >>> researchteam:managed -->``) are recognized, along with any self-documenting trailing
# prose. Mirrors the AGENTTEAMS begin/end fence idiom the framework already uses for agent files.
FENCE_BEGIN = "# >>> researchteam:managed"
FENCE_END = "# <<< researchteam:managed"

# Comment-syntax-independent cores. A line is a BEGIN/END marker when its stripped form CONTAINS
# the corresponding core (">>>" vs "<<<" keep the two unambiguous).
FENCE_CORE_BEGIN = ">>> researchteam:managed"
FENCE_CORE_END = "<<< researchteam:managed"

# Markdown (HTML-comment) fence markers, used by CLAUDE.md's managed block. Invisible when the
# document renders, unlike a bare ``#`` line which markdown would show as an H1 heading.
FENCE_BEGIN_MD = "<!-- >>> researchteam:managed — synced from upstream; do not edit inside this block -->"
FENCE_END_MD = "<!-- <<< researchteam:managed -->"

# Path prefixes (and exact paths) excluded when scaffolding a new derived repo.
# The workflow file is handled separately via bundled scaffold template. brief.json, README.md and
# CLAUDE.md are excluded here because init GENERATES project-specific versions from the scaffold
# templates (see _init_cmd.run_init / _personalize) rather than copying the framework's own.
INIT_SKIP_PREFIXES = [
    "Projects/",
    ".projects/",                  # tracked upstream EXAMPLE project — must not leak into a derived repo
    ".git/",
    "tmp/",
    ".github/agents/.agentteams-backups/",
    ".github/workflows/",          # replaced by bundled derived-repo template
    "references/plans/",
    "researchteam/",               # the Python package itself
    "pyproject.toml",              # packaging metadata, not for derived repos
    ".researchteam",               # generated fresh by init
    "workSummaries/",
    "brief.json",                  # generated fresh from scaffold/brief.template.json
    "README.md",                   # generated per-project from scaffold/README.template.md
    "CLAUDE.md",                   # generated per-project from scaffold/CLAUDE.template.md
    "mkdocs.yml",                  # the framework's own docs site (GitHub Pages), not for derived repos
    "docs_src/",
    ".github/ci/requirements-docs.txt",
]

# Scaffold files bundled in the package that replace upstream files during init.
# Keys are destination paths in the derived repo; values are filenames in researchteam/scaffold/.
INIT_SCAFFOLD_REPLACEMENTS = {
    ".github/workflows/agentteams-sync.yml": "agentteams-sync-derived.yml",
}

# Scaffold templates rendered (with brief.json token substitution) at init by _personalize.
# Keys are destination paths in the derived repo; values are template filenames in
# researchteam/scaffold/.
INIT_RENDER_TEMPLATES = {
    "README.md": "README.template.md",
    "CLAUDE.md": "CLAUDE.template.md",
}
