---
name: tool-pandoc
description: Manages Pandoc () in ResearchTeam — configuration, execution, output interpretation, and CI integration
source: .github/agents/tool-pandoc.agent.md
source_sha256: b555c1b28b5d2f7e1965bb459099462e3a98cf643c7aa81b86bb53eed8470c9b
bridge: copilot-vscode-to-claude
allowed-tools: Read, Edit, Write, Bash, Grep, Glob
---
# Bridged agent (copilot-vscode → claude)

This is a Claude subagent stub. The canonical agent definition lives at:

    .github/agents/tool-pandoc.agent.md

**On invocation, first read the source file at the path above** (relative to this repository's root), then perform the work it describes. Honor every constraint and protocol stated in the canonical body; the stub adds no policy of its own.

- Source role: Manages Pandoc () in ResearchTeam — configuration, execution, output interpretation, and CI integration

Runtime context note: you are invoked via the copilot-vscode → claude bridge from a Claude runtime. Where the source body refers to chat-mode invocations or Copilot-specific UI affordances, translate to the equivalent Claude tool surface (Read/Edit/Bash/Agent) while preserving the intent.
