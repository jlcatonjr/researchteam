# Research Task Preflight Checklist

Use this checklist before multi-step edits.

1. Confirm target files and scope boundaries.
2. Confirm whether references need verification updates.
3. Create or update plan artifacts in `tmp/by-week/YYYY-Www/`.
4. Check for existing related docs in `reports/`, `Projects/`, and `references/`.
5. Ensure no destructive action is taken without explicit approval.
6. Run repository validation after edits:
   ```bash
   bash scripts/claude_researchteam_bridge.sh validate
   ```
7. If the task touched a project's deliverables or bibliography, run the 2-fold citation & claim
   audit and resolve any `DEFECT` before compiling:
   ```bash
   bash scripts/claude_researchteam_bridge.sh citation-audit <project>
   ```
   Route `NEEDS-REVIEW` items and the doubled semantic audit per
   `docs/citation-claim-audit-protocol.md`.
8. Summarize assumptions and residual risks in the plan artifact for this task.
