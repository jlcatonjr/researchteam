"""``survey-validate <project>`` (contract section 7): check the specification, the ledger's folder and the gates'
manifest files. Writes nothing. Exit 0 when well-formed, 1 on any error, 2 on a usage error.

A clean run means the study is well-formed and internally consistent (rule 1.9); it says nothing about whether a
gate is cleared (``survey-status``). The row checks of section 4 are not in this version (step B).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from survey_core import SurveyUsageError, parse_args, print_findings, usage_exit  # noqa: E402
from survey_gates import GATES, gate_status  # noqa: E402
from survey_ledger import check_ledger  # noqa: E402
from survey_spec import load_study  # noqa: E402

PROG = "survey_validate.py"


def validate(root: Path, project: str) -> tuple:
    """Every step-A check. Returns ``(study, findings)``."""
    study = load_study(project, root)
    findings = list(study.findings)
    if study.spec is None or not study.ok:
        return study, findings
    ledger = check_ledger(study)
    findings += ledger.findings
    for gate in GATES:
        _st, extra = gate_status(study, gate, ledger)
        findings += extra
    return study, findings


def main(argv=None) -> int:
    try:
        root, project, _ = parse_args(sys.argv[1:] if argv is None else argv, PROG)
        study, findings = validate(root, project)
    except SurveyUsageError as exc:
        return usage_exit(exc)
    if findings:
        print_findings(findings)
        print(f"FAIL: {study.spec_rel}: {len(findings)} error(s)")
        return 1
    print(f"OK: {study.spec_rel} is well-formed (specification, ledger folder, manifest files).")
    print("note: row checks (section 4) are not in this version; gate state is reported by survey-status.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
