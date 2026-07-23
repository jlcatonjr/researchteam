---
name: primary-producer
description: Drafts and revises deliverables in ResearchTeam from Component Briefs provided by workstream expert agents
source: .github/agents/primary-producer.agent.md
source_sha256: 01a9c2ee57aeddf2c8b00afb4eb3e8f2eb1d73dc10a895719b48054483551e6e
bridge: copilot-vscode-to-claude
allowed-tools: Read, Edit, Write, Grep, Glob
---
# Bridged agent (copilot-vscode → claude)

This is a Claude subagent stub. The canonical agent definition lives at:

    .github/agents/primary-producer.agent.md

**On invocation, first read the source file at the path above** (relative to this repository's root), then perform the work it describes. Honor every constraint and protocol stated in the canonical body; the stub adds no policy of its own.

- Source role: Drafts and revises deliverables in ResearchTeam from Component Briefs provided by workstream expert agents

Runtime context note: you are invoked via the copilot-vscode → claude bridge from a Claude runtime. Where the source body refers to chat-mode invocations or Copilot-specific UI affordances, translate to the equivalent Claude tool surface (Read/Edit/Bash/Agent) while preserving the intent.
