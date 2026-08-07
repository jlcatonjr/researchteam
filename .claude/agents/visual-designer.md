---
name: visual-designer
description: Creates and revises diagrams and figures for ResearchTeam using the approved diagram toolchain
source: .github/agents/visual-designer.agent.md
source_sha256: 31198e666f8e5383c91e00f5f60904322bda54517d45ec44fc43bec27ffa74eb
bridge: copilot-vscode-to-claude
tools: Read, Edit, Write, Bash, Grep, Glob
---
<!-- AGENTTEAMS:BEGIN content v=1 -->
# Bridged agent (copilot-vscode → claude)

This is a Claude subagent stub. The canonical agent definition lives at:

    .github/agents/visual-designer.agent.md

**On invocation, first read the source file at the path above** (relative to this repository's root), then perform the work it describes. Honor every constraint and protocol stated in the canonical body; the stub adds no policy of its own.

- Source role: Creates and revises diagrams and figures for ResearchTeam using the approved diagram toolchain

Runtime context note: you are invoked via the copilot-vscode → claude bridge from a Claude runtime. Where the source body refers to chat-mode invocations or Copilot-specific UI affordances, translate to the equivalent Claude tool surface (Read/Edit/Bash/Agent) while preserving the intent.
<!-- AGENTTEAMS:END content -->

## Project-Specific Notes

> ⚙️ **USER-EDITABLE** — project-specific rules, overrides, and extensions for this agent. This section lies outside every `AGENTTEAMS` fence and is preserved verbatim across `agentteams --update --merge`.
