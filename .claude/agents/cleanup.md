---
name: cleanup
description: Removes stale drafts, build artifacts, and orphaned files from ResearchTeam with mandatory safety checks
source: .github/agents/cleanup.agent.md
source_sha256: 7ea1a25823ff305f5f513224ec4de38e50be20d738610b5941370d8406f7e697
bridge: copilot-vscode-to-claude
allowed-tools: Edit, Write, Grep, Glob, Bash
---
# Bridged agent (copilot-vscode → claude)

This is a Claude subagent stub. The canonical agent definition lives at:

    .github/agents/cleanup.agent.md

**On invocation, first read the source file at the path above** (relative to this repository's root), then perform the work it describes. Honor every constraint and protocol stated in the canonical body; the stub adds no policy of its own.

- Source role: Removes stale drafts, build artifacts, and orphaned files from ResearchTeam with mandatory safety checks

Runtime context note: you are invoked via the copilot-vscode → claude bridge from a Claude runtime. Where the source body refers to chat-mode invocations or Copilot-specific UI affordances, translate to the equivalent Claude tool surface (Read/Edit/Bash/Agent) while preserving the intent.
