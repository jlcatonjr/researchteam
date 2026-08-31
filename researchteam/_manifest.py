UPSTREAM_REPO = "jlcatonjr/researchteam"
UPSTREAM_BRANCH = "main"

# Layer-2 files owned and synced by researchteam (not agentteams).
# Paths are relative to repo root. brief.json and Projects/ are user-owned and never touched.
MANAGED_FILES = [
    "CLAUDE.md",
    "README.md",
    ".gitignore",
    "docs/claude-interface-bridge.md",
    "docs/agentteams-update-policy.md",
    "docs/agent-infrastructure-authority.md",
    "docs/citation-claim-audit-protocol.md",
    "docs/literature-library-protocol.md",
    "docs/retrieval-surfaces.md",
    "docs/on-the-fly-retrieval-profile.md",
    "docs/news-perspective-protocol.md",
    ".claude/README.md",
    ".claude/checklists/research-task-preflight.md",
    ".claude/prompts/research-report.prompt.md",
    "scripts/claude_researchteam_bridge.sh",
    "scripts/validate_agentteams_update.sh",
    "scripts/check_methodology_coverage.sh",
    "scripts/check_citation_integrity.sh",
    "scripts/agentteams_autosync_gate.sh",
    "scripts/build_literature_library.py",
    "scripts/query_literature_library.py",
    "scripts/check_literature_library_integrity.sh",
]

# How each managed file is reconciled on update.
# Default (any file NOT listed here) = "overwrite": wholesale replacement from upstream — the
# historical behavior, unchanged for every doc, script, and CLAUDE.md (which agentteams fences
# separately). "fenced-preserve": only the upstream-owned block delimited by FENCE_BEGIN/FENCE_END
# is replaced; every line OUTSIDE that fence is a derived-repo addition and survives the sync.
# See docs/gitignore-preservation-handoff.md and docs/agentteams-update-policy.md.
MERGE_STRATEGIES = {
    ".gitignore": "fenced-preserve",
}

# Sentinel comment lines delimiting the upstream-owned region of a fenced-preserve file. Matched
# on the stripped line, so surrounding whitespace is tolerated. Mirrors the AGENTTEAMS begin/end
# fence idiom the framework already uses for agent files.
FENCE_BEGIN = "# >>> researchteam:managed"
FENCE_END = "# <<< researchteam:managed"

# Path prefixes (and exact paths) excluded when scaffolding a new derived repo.
# The workflow file is handled separately via bundled scaffold template.
INIT_SKIP_PREFIXES = [
    "Projects/",
    ".git/",
    "tmp/",
    ".github/agents/.agentteams-backups/",
    ".github/workflows/",          # replaced by bundled derived-repo template
    "references/plans/",
    "researchteam/",               # the Python package itself
    "pyproject.toml",              # packaging metadata, not for derived repos
    ".researchteam",               # generated fresh by init
    "workSummaries/",
]

# Scaffold files bundled in the package that replace upstream files during init.
# Keys are destination paths in the derived repo; values are filenames in researchteam/scaffold/.
INIT_SCAFFOLD_REPLACEMENTS = {
    ".github/workflows/agentteams-sync.yml": "agentteams-sync-derived.yml",
}
