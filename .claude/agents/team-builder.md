---
name: team-builder
description: Interactively constructs a complete agent team for a new or existing VS Code Copilot project by conducting an intake interview and invoking the build_team pipeline
source: .github/agents/team-builder.agent.md
source_sha256: a6818a1f3ca9eb8e7876cc6ac1c2f5f4cc67c4bf270784e89db20fe47809b74e
bridge: copilot-vscode-to-claude
---
# Bridged agent (copilot-vscode → claude)

This is a Claude subagent stub. The canonical agent definition lives at:

    .github/agents/team-builder.agent.md

**On invocation, first read the source file at the absolute path below**, then perform the work it describes. Honor every constraint and protocol stated in the canonical body; the stub adds no policy of its own.

- Source absolute path: `/Users/jamescaton/githubrepositories/researchteam/.github/agents/team-builder.agent.md`
- Source role: Interactively constructs a complete agent team for a new or existing VS Code Copilot project by conducting an intake interview and invoking the build_team pipeline

Runtime context note: you are invoked via the copilot-vscode → claude bridge from a Claude runtime. Where the source body refers to chat-mode invocations or Copilot-specific UI affordances, translate to the equivalent Claude tool surface (Read/Edit/Bash/Agent) while preserving the intent.
