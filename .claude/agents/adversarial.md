---
name: adversarial
description: Presupposition critic: challenges the assumptions underlying any plan, proposal, or diagnosis produced by the agent team. Traces how justified changes in presuppositions cascade through dependent l...
source: .github/agents/adversarial.agent.md
source_sha256: 86cab35df4972d10a45d28b33b838629676eecc75aad2b83be8987fe4ee3ce1a
bridge: copilot-vscode-to-claude
allowed-tools: Read, Grep, Glob
---
# Bridged agent (copilot-vscode → claude)

This is a Claude subagent stub. The canonical agent definition lives at:

    .github/agents/adversarial.agent.md

**On invocation, first read the source file at the path above** (relative to this repository's root), then perform the work it describes. Honor every constraint and protocol stated in the canonical body; the stub adds no policy of its own.

- Source role: Presupposition critic: challenges the assumptions underlying any plan, proposal, or diagnosis produced by the agent team. Traces how justified changes in presuppositions cascade through dependent l...

Runtime context note: you are invoked via the copilot-vscode → claude bridge from a Claude runtime. Where the source body refers to chat-mode invocations or Copilot-specific UI affordances, translate to the equivalent Claude tool surface (Read/Edit/Bash/Agent) while preserving the intent.
