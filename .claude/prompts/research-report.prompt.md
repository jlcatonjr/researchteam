# Research Report Prompt Template

Use this template when asking Claude to draft or revise a research report component.

## Request

Topic:
Scope and constraints:
Target file(s):
Required sections:
Source expectations:
Citation style:

## Mandatory Requirements

- No fabricated references.
- Every factual claim must map to a verifiable source.
- Distinguish evidence, interpretation, and uncertainty.
- Preserve existing repository structure.
- For multi-step implementation, create plan artifacts in `tmp/by-week/YYYY-Www/`.
- Before finalizing, run the 2-fold citation & claim audit
  (`bash scripts/claude_researchteam_bridge.sh citation-audit <project>`, then the doubled semantic
  audit in `docs/citation-claim-audit-protocol.md`). Unresolved citation/claim findings block
  release; a clean run is WELL-FORMED, not proof of non-fabrication.

## Output Expectations

- Clear section headings.
- Chicago author-date citations.
- Explicit list of unresolved verification risks.
