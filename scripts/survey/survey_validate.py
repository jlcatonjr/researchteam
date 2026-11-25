"""``survey-validate <project>`` (contract section 7): check the specification, the ledger's folder and the gates'
manifest files, and every row file sections 4.1, 4.3 and 4.8 define that is present (the evidence file with the
registry it needs, the attribution file, the legacy exceptions, the vocabulary file, the bucket tables). Writes
nothing. Exit 0 when well-formed, 1 on any error, 2 on a usage error.

A clean run means the study is well-formed and internally consistent (rule 1.9); it says nothing about whether a
gate is cleared (``survey-status``), nor that a quotation is at its locus: re-finding quotations is step G.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from survey_core import SurveyUsageError, parse_args, print_findings, safe, usage_exit  # noqa: E402
from survey_evidence import EvidenceReport, check_row_files  # noqa: E402
from survey_gates import GATES, gate_status  # noqa: E402
from survey_ledger import check_ledger  # noqa: E402
from survey_spec import load_study  # noqa: E402

PROG = "survey_validate.py"


def validate(root: Path, project: str) -> tuple:
    """Every check. Returns ``(study, findings, notes, rows)``: notes are the reasons the gates read UNAVAILABLE
    that are not errors (6.2: what the HALT scan would read); rows is the row-file report."""
    study = load_study(project, root)
    findings = list(study.findings)
    rows = EvidenceReport()
    if study.spec is None or not study.ok:
        return study, findings, [], rows
    ledger = check_ledger(study)
    findings += ledger.findings
    for gate in GATES:
        _st, extra = gate_status(study, gate, ledger)
        findings += extra
    rows = check_row_files(study)
    findings += rows.findings
    return study, findings, list(ledger.unavailable), rows


def main(argv=None) -> int:
    try:
        root, project, _ = parse_args(sys.argv[1:] if argv is None else argv, PROG)
        study, findings, notes, rows = validate(root, project)
    except SurveyUsageError as exc:
        return usage_exit(exc)
    for f in rows.reported:
        print(f.line("REPORTED"))
    print_findings(findings)
    # Printed on every run, failing runs included: a listed breach "is reported, with counts by rule" (4.1, line 356)
    # and an unfindable quotation in a legacy study is "reported and counted" (5.4, line 774).
    excused = ", ".join(f"{rule} {n}" for rule, n in sorted(rows.excused.items())) or "none"
    print(f"evidence: {rows.rows} row(s); read with {rows.exceptions} legacy exception(s); breaches excused by rule: "
          f"{excused}")
    print(f"quotations: {rows.not_refound} counted quotation(s) not re-found ({len(rows.reported)} reported); "
          "re-finding is not in this version")
    if findings:
        print(f"FAIL: {study.spec_rel}: {len(findings)} error(s)")
        return 1
    for reason in notes:
        print(safe(f"note: the gates read UNAVAILABLE: {reason}"))
    print(f"OK: {study.spec_rel} is well-formed (specification, ledger folder, manifest files, row files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
