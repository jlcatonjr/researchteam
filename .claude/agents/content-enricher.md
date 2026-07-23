---
name: content-enricher
description: Fills in default template placeholders and underdeveloped sections in generated agent files for ResearchTeam using the project's source materials
source: .github/agents/content-enricher.agent.md
source_sha256: 2ff237a293a35cdc7430393cbefcd0af2e3d7b5ffc87aef0206f1e7f697fe7c3
bridge: copilot-vscode-to-claude
allowed-tools: Read, Edit, Write, Grep, Glob
---
# Bridged agent (copilot-vscode → claude)

This is a Claude subagent stub. The canonical agent definition lives at:

    .github/agents/content-enricher.agent.md

**On invocation, first read the source file at the path above** (relative to this repository's root), then perform the work it describes. Honor every constraint and protocol stated in the canonical body; the stub adds no policy of its own.

- Source role: Fills in default template placeholders and underdeveloped sections in generated agent files for ResearchTeam using the project's source materials

Runtime context note: you are invoked via the copilot-vscode → claude bridge from a Claude runtime. Where the source body refers to chat-mode invocations or Copilot-specific UI affordances, translate to the equivalent Claude tool surface (Read/Edit/Bash/Agent) while preserving the intent.
