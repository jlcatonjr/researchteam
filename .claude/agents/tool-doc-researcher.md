---
name: tool-doc-researcher
description: Locates and verifies official documentation, API surfaces, and usage patterns for tools in ResearchTeam that are missing metadata
source: .github/agents/tool-doc-researcher.agent.md
source_sha256: 597b5aa034348c0f1c114fb8610102ee3286cf354a26612b218d08dacba25cd6
bridge: copilot-vscode-to-claude
allowed-tools: Read, Grep, Glob
---
# Bridged agent (copilot-vscode → claude)

This is a Claude subagent stub. The canonical agent definition lives at:

    .github/agents/tool-doc-researcher.agent.md

**On invocation, first read the source file at the path above** (relative to this repository's root), then perform the work it describes. Honor every constraint and protocol stated in the canonical body; the stub adds no policy of its own.

- Source role: Locates and verifies official documentation, API surfaces, and usage patterns for tools in ResearchTeam that are missing metadata

Runtime context note: you are invoked via the copilot-vscode → claude bridge from a Claude runtime. Where the source body refers to chat-mode invocations or Copilot-specific UI affordances, translate to the equivalent Claude tool surface (Read/Edit/Bash/Agent) while preserving the intent.
