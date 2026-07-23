---
name: orchestrator
description: Coordinates all agent operations for ResearchTeam: routes work to domain agents, enforces constitutional rules, and closes every multi-file session with a consistency check.
source: .github/agents/orchestrator.agent.md
source_sha256: bdaad3e3721ca2b5e3ab5b70a0d3ce1830e7dcee7c444104ab824a4e09420841
bridge: copilot-vscode-to-claude
allowed-tools: Read, Edit, Write, Grep, Glob, Bash, TodoWrite, Task
---
# Bridged agent (copilot-vscode → claude)

This is a Claude subagent stub. The canonical agent definition lives at:

    .github/agents/orchestrator.agent.md

**On invocation, first read the source file at the path above** (relative to this repository's root), then perform the work it describes. Honor every constraint and protocol stated in the canonical body; the stub adds no policy of its own.

- Source role: Coordinates all agent operations for ResearchTeam: routes work to domain agents, enforces constitutional rules, and closes every multi-file session with a consistency check.

Runtime context note: you are invoked via the copilot-vscode → claude bridge from a Claude runtime. Where the source body refers to chat-mode invocations or Copilot-specific UI affordances, translate to the equivalent Claude tool surface (Read/Edit/Bash/Agent) while preserving the intent.
