---
name: work-summarizer
description: Synthesizes daily, weekly, and monthly work summaries from canonical plan artifacts and git evidence for ResearchTeam; supports append-first daily capture, legacy tmp/ fallback, and required advers...
source: .github/agents/work-summarizer.agent.md
source_sha256: d596ef235fcd72bc76a2e57609bbfae2228c92896e3128ca03c903cdad86c655
bridge: copilot-vscode-to-claude
tools: Read, Grep, Glob, Bash, Edit, Write, Task
---
<!-- AGENTTEAMS:BEGIN content v=1 -->
# Bridged agent (copilot-vscode → claude)

This is a Claude subagent stub. The canonical agent definition lives at:

    .github/agents/work-summarizer.agent.md

**On invocation, first read the source file at the path above** (relative to this repository's root), then perform the work it describes. Honor every constraint and protocol stated in the canonical body; the stub adds no policy of its own.

- Source role: Synthesizes daily, weekly, and monthly work summaries from canonical plan artifacts and git evidence for ResearchTeam; supports append-first daily capture, legacy tmp/ fallback, and required advers...

Runtime context note: you are invoked via the copilot-vscode → claude bridge from a Claude runtime. Where the source body refers to chat-mode invocations or Copilot-specific UI affordances, translate to the equivalent Claude tool surface (Read/Edit/Bash/Agent) while preserving the intent.
<!-- AGENTTEAMS:END content -->

## Project-Specific Notes

> ⚙️ **USER-EDITABLE** — project-specific rules, overrides, and extensions for this agent. This section lies outside every `AGENTTEAMS` fence and is preserved verbatim across `agentteams --update --merge`.
