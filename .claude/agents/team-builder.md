---
name: team-builder
description: Interactively constructs a complete agent team for a new or existing VS Code Copilot project by conducting an intake interview and invoking the build_team pipeline
source: .github/agents/team-builder.agent.md
source_sha256: 9dcf3f165ffd2bcebcdb47ee49151f82c740f6fef21b3dc15ea1fdb5a0a6f2c9
bridge: copilot-vscode-to-claude
allowed-tools: Read, Edit, Write, Grep, Glob, Bash, TodoWrite
---
# Bridged agent (copilot-vscode → claude)

This is a Claude subagent stub. The canonical agent definition lives at:

    .github/agents/team-builder.agent.md

**On invocation, first read the source file at the path above** (relative to this repository's root), then perform the work it describes. Honor every constraint and protocol stated in the canonical body; the stub adds no policy of its own.

- Source role: Interactively constructs a complete agent team for a new or existing VS Code Copilot project by conducting an intake interview and invoking the build_team pipeline

Runtime context note: you are invoked via the copilot-vscode → claude bridge from a Claude runtime. Where the source body refers to chat-mode invocations or Copilot-specific UI affordances, translate to the equivalent Claude tool surface (Read/Edit/Bash/Agent) while preserving the intent.
