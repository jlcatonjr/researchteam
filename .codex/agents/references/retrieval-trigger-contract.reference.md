<!-- AGENTTEAMS:BEGIN content v=1 -->
# Retrieval Trigger Contract

Project: ResearchTeam

Version: v1

## Allowed Trigger Sources

- cli
- script
- manual

## Requirements

1. Every maintenance entrypoint must map to at least one trigger source.
2. Every query entrypoint must identify a corresponding source-of-truth validation path.
3. Trigger changes must update this contract version and be reviewed by @adversarial and @conflict-auditor.

## Entrypoints

### Query

- scripts/query_literature_library.py
- bash scripts/claude_researchteam_bridge.sh library-query <project> "<terms>"

### Maintenance

- scripts/build_literature_library.py
- scripts/check_literature_library_integrity.sh
<!-- AGENTTEAMS:END content -->
