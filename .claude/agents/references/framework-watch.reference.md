# Framework Watch — ResearchTeam

<!--
SECTION MANIFEST — framework-watch.reference.template.md
| section_id      | designation | notes                                                |
|-----------------|-------------|------------------------------------------------------|
| framework_data  | FENCED      | Live upstream framework spec snapshot (Claude Code)  |
| operational_integration_process| FENCED      | Template-owned section                               |
-->

This reference is refreshed during team initialization and update workflows.
It records the most recent observed upstream agent-framework specification
(currently Claude Code sub-agents) and the diff against this project's
framework adapter constants. Use it when reviewing `@framework-adapters-expert`,
`@docs-research-expert`, and `@agent-updater` proposals — it is the
canonical signal that the local adapter may need attention.

The detection is intentionally coarse. The machine-readable snapshot lives
at `tmp/daily-pipeline/framework-research/latest.json` and is the
authoritative source; the table below is a human-readable projection
re-rendered on every `--update --merge`.

<!-- AGENTTEAMS:BEGIN framework_data v=1 -->
> ⚠️ **UNVERIFIED DATA** — no framework doc was fetched for this snapshot (every fetch was skipped or failed). Run the daily research stage online.

Generated on: `2026-11-24`
Source: https://docs.anthropic.com/en/docs/claude-code/sub-agents
Fetch status: `skipped`
Diff summary: `matched=0 new_upstream=0 missing_upstream=4`

| Framework | Fetch | Tokens observed | Locations observed | Drift (missing keys ↓) |
|---|---|---|---|---|
| claude (Claude Code Sub-Agents) | `skipped` | — | — | ↓ description, model, name, tools |
| copilot_vscode (GitHub Copilot — VS Code Custom Agents) | `skipped` | — | — | ↓ description, model, tools |
| copilot_cli (GitHub Copilot — CLI Custom Agents) | `skipped` | — | — | ↓ description, model, tools |
| goose (Goose (AAIF) Recipes) | `skipped` | — | — | ↓ description, instructions, prompt, title |
| agents_md (AGENTS.md Cross-Tool Standard) | `skipped` | — | — | — |
| codex (OpenAI Codex CLI) | `skipped` | — | — | ↓ developer_instructions, mcp_servers, project_doc_max_bytes, sandbox_mode |
| grok (xAI Grok Build) | `skipped` | — | — | ↓ mcp_servers, permission, plugins |

Local Claude adapter constants (parsed from claude.py source):
- strictly-required keys (_CLAUDE_REQUIRED_KEYS): description, name
- default_allowed_tools: Read, Grep, Glob
- claude diff (vs expected_doc_tokens) — matched: —; new_upstream: —; missing_upstream: description, model, name, tools
<!-- AGENTTEAMS:END framework_data -->

<!-- AGENTTEAMS:BEGIN operational_integration_process v=1 -->
## Operational Integration Process

1. Refresh this reference on every team initialization and update.
2. Route `new_upstream` keys to `@framework-adapters-expert` for triage.
3. Route `documented_locally_not_upstream` keys to `@docs-research-expert`
   for verification — they may indicate doc drift or a missed rename.
4. Escalate persistent unresolved drift to `@orchestrator` with a
   re-render request when adapter constants are out of date.
<!-- AGENTTEAMS:END operational_integration_process -->

<!-- AGENTTEAMS:BEGIN conformance_standard_check v=1 -->

<!-- AGENTTEAMS:END conformance_standard_check -->

