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
    ".claude/README.md",
    ".claude/checklists/research-task-preflight.md",
    ".claude/prompts/research-report.prompt.md",
    "scripts/claude_researchteam_bridge.sh",
    "scripts/validate_agentteams_update.sh",
    "scripts/check_methodology_coverage.sh",
    "scripts/check_citation_integrity.sh",
    "scripts/build_literature_library.py",
    "scripts/query_literature_library.py",
    "scripts/check_literature_library_integrity.sh",
]

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
