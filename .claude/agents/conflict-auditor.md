---
name: conflict-auditor
description: Detects logical conflicts across deliverables, agent documentation, reference files, and source material in ResearchTeam
source: .github/agents/conflict-auditor.agent.md
source_sha256: 9389a35d2a66f7db7f58f2060d3206537c4412f94fea46961e4e24cc7dab9d54
bridge: copilot-vscode-to-claude
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---
# Bridged agent (copilot-vscode → claude)

This is a Claude subagent stub. The canonical agent definition lives at:

    .github/agents/conflict-auditor.agent.md

**On invocation, first read the source file at the path above** (relative to this repository's root), then perform the work it describes. Honor every constraint and protocol stated in the canonical body; the stub adds no policy of its own.

- Source role: Detects logical conflicts across deliverables, agent documentation, reference files, and source material in ResearchTeam

Runtime context note: you are invoked via the copilot-vscode → claude bridge from a Claude runtime. Where the source body refers to chat-mode invocations or Copilot-specific UI affordances, translate to the equivalent Claude tool surface (Read/Edit/Bash/Agent) while preserving the intent.
