# Plan: Integrate Defense-in-Depth Guard into CI

Trigger: User requested to proceed with integration.
Date: 2026-05-20

Goal:
- Integrate explicit forbidden-path checks into CI workflow to prevent reintroduction of deprecated nested mirror paths.

Steps:
1. Update CI workflow with pre/post forbidden-path filesystem checks.
2. Align policy doc to mention defense-in-depth workflow guard.
3. Validate edited files and record completion.

Success criteria:
- Workflow fails immediately if `.github/agents/.github/` exists.
- Policy references the additional workflow-level guard.
- No syntax/diagnostic errors in changed files.

Rollback:
- Revert workflow/policy edits if guard creates unacceptable false positives.

Completion: 2026-05-20
