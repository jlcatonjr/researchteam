<!-- AGENTTEAMS:BEGIN content v=1 -->
# Retrieval Trigger Contract

Project: ResearchTeam

Version: v1

## Allowed Trigger Sources

- env
- script
- workflow

## Requirements

1. Every maintenance entrypoint must map to at least one trigger source.
2. Every query entrypoint must identify a corresponding source-of-truth validation path.
3. Trigger changes must update this contract version and be reviewed by @adversarial and @conflict-auditor.

## Entrypoints

### Query

No retrieval query entrypoints declared.

### Maintenance

- scripts/agentteams_autosync_gate.sh
- scripts/claude_researchteam_bridge.sh
- scripts/tests/test_literature_library.sh
<!-- AGENTTEAMS:END content -->
