---
name: quality-auditor
description: Read-only audit agent that inspects deliverables in ResearchTeam for structural defects, logical inconsistencies, and LLM-generated prose patterns; does not rewrite
source: .github/agents/quality-auditor.agent.md
source_sha256: 787dc0fd0f5d8b56b2954f7e04d6ec2bf397d8912e79cbebd7298f75d320afaa
bridge: copilot-vscode-to-claude
---
# Bridged agent (copilot-vscode → claude)

This is a Claude subagent stub. The canonical agent definition lives at:

    .github/agents/quality-auditor.agent.md

**On invocation, first read the source file at the absolute path below**, then perform the work it describes. Honor every constraint and protocol stated in the canonical body; the stub adds no policy of its own.

- Source absolute path: `/Users/jamescaton/githubrepositories/researchteam/.github/agents/quality-auditor.agent.md`
- Source role: Read-only audit agent that inspects deliverables in ResearchTeam for structural defects, logical inconsistencies, and LLM-generated prose patterns; does not rewrite

Runtime context note: you are invoked via the copilot-vscode → claude bridge from a Claude runtime. Where the source body refers to chat-mode invocations or Copilot-specific UI affordances, translate to the equivalent Claude tool surface (Read/Edit/Bash/Agent) while preserving the intent.
