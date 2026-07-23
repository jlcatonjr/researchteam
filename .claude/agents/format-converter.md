---
name: format-converter
description: Converts deliverables from their source format to Markdown with Chicago citations for final output in ResearchTeam
source: .github/agents/format-converter.agent.md
source_sha256: e484c886631c7e5021c67c89f2507002d75810b82f97a2010a6ac83909458b5f
bridge: copilot-vscode-to-claude
allowed-tools: Read, Edit, Write, Bash
---
# Bridged agent (copilot-vscode → claude)

This is a Claude subagent stub. The canonical agent definition lives at:

    .github/agents/format-converter.agent.md

**On invocation, first read the source file at the path above** (relative to this repository's root), then perform the work it describes. Honor every constraint and protocol stated in the canonical body; the stub adds no policy of its own.

- Source role: Converts deliverables from their source format to Markdown with Chicago citations for final output in ResearchTeam

Runtime context note: you are invoked via the copilot-vscode → claude bridge from a Claude runtime. Where the source body refers to chat-mode invocations or Copilot-specific UI affordances, translate to the equivalent Claude tool surface (Read/Edit/Bash/Agent) while preserving the intent.
