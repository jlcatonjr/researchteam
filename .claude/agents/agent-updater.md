---
name: agent-updater
description: Synchronizes agent documentation after project structure, deliverable, or reference changes in ResearchTeam
source: .github/agents/agent-updater.agent.md
source_sha256: d69e5774ae01ecbf177b41f9913123d2c408502650ff170367542eb3fe23eeb5
bridge: copilot-vscode-to-claude
tools: Edit, Write, Grep, Glob, Bash, Task
---
<!-- AGENTTEAMS:BEGIN content v=1 -->
# Bridged agent (copilot-vscode → claude)

This is a Claude subagent stub. The canonical agent definition lives at:

    .github/agents/agent-updater.agent.md

**On invocation, first read the source file at the path above** (relative to this repository's root), then perform the work it describes. Honor every constraint and protocol stated in the canonical body; the stub adds no policy of its own.

- Source role: Synchronizes agent documentation after project structure, deliverable, or reference changes in ResearchTeam

Runtime context note: you are invoked via the copilot-vscode → claude bridge from a Claude runtime. Where the source body refers to chat-mode invocations or Copilot-specific UI affordances, translate to the equivalent Claude tool surface (Read/Edit/Bash/Agent) while preserving the intent.
<!-- AGENTTEAMS:END content -->

## Project-Specific Notes

> ⚙️ **USER-EDITABLE** — project-specific rules, overrides, and extensions for this agent. This section lies outside every `AGENTTEAMS` fence and is preserved verbatim across `agentteams --update --merge`.
