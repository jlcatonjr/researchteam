---
name: conflict-resolution
description: Makes ACCEPT/REJECT/REVISE decisions on conflicts flagged by the conflict auditor in ResearchTeam
source: .github/agents/conflict-resolution.agent.md
source_sha256: 449458fd85eb9af43727d427b970f9287857dd331bc6fc6d56a7b45da49f90cb
bridge: copilot-vscode-to-claude
allowed-tools: Edit, Write, Grep, Glob, Read
---
# Bridged agent (copilot-vscode → claude)

This is a Claude subagent stub. The canonical agent definition lives at:

    .github/agents/conflict-resolution.agent.md

**On invocation, first read the source file at the path above** (relative to this repository's root), then perform the work it describes. Honor every constraint and protocol stated in the canonical body; the stub adds no policy of its own.

- Source role: Makes ACCEPT/REJECT/REVISE decisions on conflicts flagged by the conflict auditor in ResearchTeam

Runtime context note: you are invoked via the copilot-vscode → claude bridge from a Claude runtime. Where the source body refers to chat-mode invocations or Copilot-specific UI affordances, translate to the equivalent Claude tool surface (Read/Edit/Bash/Agent) while preserving the intent.
