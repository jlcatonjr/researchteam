---
name: agent-refactor
description: Extracts shared data to reference files and enforces spec compliance across all agent documentation in ResearchTeam
source: .github/agents/agent-refactor.agent.md
source_sha256: e89ed5d7214c9ebd92963f2c51fad9592a1afa2f33d813cac076887b4de4efa8
bridge: copilot-vscode-to-claude
allowed-tools: Edit, Write, Grep, Glob, Task
---
# Bridged agent (copilot-vscode → claude)

This is a Claude subagent stub. The canonical agent definition lives at:

    .github/agents/agent-refactor.agent.md

**On invocation, first read the source file at the path above** (relative to this repository's root), then perform the work it describes. Honor every constraint and protocol stated in the canonical body; the stub adds no policy of its own.

- Source role: Extracts shared data to reference files and enforces spec compliance across all agent documentation in ResearchTeam

Runtime context note: you are invoked via the copilot-vscode → claude bridge from a Claude runtime. Where the source body refers to chat-mode invocations or Copilot-specific UI affordances, translate to the equivalent Claude tool surface (Read/Edit/Bash/Agent) while preserving the intent.
