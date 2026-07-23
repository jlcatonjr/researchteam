---
name: output-compiler
description: Assembles all converted components into a final deliverable package for ResearchTeam — dependency check, ordering, build manifest
source: .github/agents/output-compiler.agent.md
source_sha256: 07897818bf0566f3fd551cd2ac70b81de798701fb6538226c566b3e2ec190cb2
bridge: copilot-vscode-to-claude
allowed-tools: Read, Edit, Write, Bash
---
# Bridged agent (copilot-vscode → claude)

This is a Claude subagent stub. The canonical agent definition lives at:

    .github/agents/output-compiler.agent.md

**On invocation, first read the source file at the path above** (relative to this repository's root), then perform the work it describes. Honor every constraint and protocol stated in the canonical body; the stub adds no policy of its own.

- Source role: Assembles all converted components into a final deliverable package for ResearchTeam — dependency check, ordering, build manifest

Runtime context note: you are invoked via the copilot-vscode → claude bridge from a Claude runtime. Where the source body refers to chat-mode invocations or Copilot-specific UI affordances, translate to the equivalent Claude tool surface (Read/Edit/Bash/Agent) while preserving the intent.
