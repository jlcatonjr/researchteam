# Plan: Harden Validator Against Nested Mirror Reappearance

Trigger: User requested recommended hardening after deduplication.
Date: 2026-05-20

Goal:
- Ensure CI validation explicitly blocks any reintroduction of `.github/agents/.github/**`.

Steps:
1. Update validator script with explicit forbidden-path check.
2. Validate script diagnostics and syntax.
3. Record completion.

Success criteria:
- Validation fails when forbidden nested mirror path is present in changed files.
- Existing allowed path checks continue to function.

Rollback:
- Revert validator script to prior version if this rule causes false positives.

Completion: 2026-05-20
