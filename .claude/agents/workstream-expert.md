---
name: workstream-expert
description: Parametric workstream-expert subagent; takes a component slug and loads the corresponding canonical brief.
source_dir: .github/agents
collapsed_experts: 4
bridge: copilot-vscode-to-claude
---
# Workstream Expert (parametric, bridged)

This subagent stands in for N component-specific Workstream Expert agents in the canonical copilot-vscode source. Each invocation must include a `component` slug identifying which brief to load.

**On invocation:**

1. Read the canonical brief at `.github/agents/<component>-expert.agent.md`.
2. Follow every constraint and protocol stated in that body.
3. Translate Copilot-runtime affordances (chat-mode invocations, etc.) to the equivalent Claude tool surface (Read/Edit/Bash/Agent).
4. Treat the brief as authoritative; the stub adds no policy of its own.

Drift detection: the bridge maintains per-brief SHA-256 provenance separately; if a brief changes, re-emit the bridge.
