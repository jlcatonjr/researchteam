---
name: todo-from-plan
description: Project a canonical agentteams plan-steps CSV into Claude's TodoWrite tool. Read-only on the CSV until an explicit status writeback is requested.
bridge: copilot-vscode-to-claude
---

# Plan-steps → TodoWrite projection

When the orchestrator activates on a plan with an associated
``*.steps.csv``, project the CSV rows into ``TodoWrite`` items so the
runtime task list mirrors the canonical plan-of-record.

**Projection (read-only):**

    from agentteams.plan_steps_todo import project_to_todos
    items = project_to_todos(Path("references/plans/<plan>.steps.csv"))
    # items: list of {content, activeForm, status} ready for TodoWrite.

**Status writeback (append-only mutation):**

The CSV is canonical. Only the ``status`` column may be mutated through
``plan_steps_todo.update_status(csv_path, step_id, new_status)``.
Structural edits (adding/removing/renaming steps) must go through the
CSV directly and trigger a re-projection.

**Divergence check:**

``plan_steps_todo.detect_divergence(csv_path, todo_items)`` returns the
three-list shape used by post-production-auditor's optional
``--check-todo-divergence`` mode.
