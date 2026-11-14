# Citation audit: close two fail-open paths (report from masterteacher-1f)

User decisions 2026-10-18: fix on main, offer to researchteam-f6 for release/1.0; bib scope = find + fail closed.
1. Temp dir: honour TMPDIR, exit 2 when no writable WORK (and when $WORK/out can't be written). Reproduced: mktemp refused -> PASS exit 0.
2. Bib discovery: --bib PATH (repeatable, needs target) > project *.bib > repo-level references/*.bib. Cited deliverables with no bib -> DEFECT[NOBIB].
Tests: 14 new bash scenarios (54 total, bash 3.2 + 5) + tests/test_citation_integrity_suite.py so CI runs them.
Worktree ../researchteam-wt-citint, branch fix/citation-audit-fail-open.
