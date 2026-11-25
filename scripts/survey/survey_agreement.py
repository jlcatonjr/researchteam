"""``survey-agreement <project>`` (contract section 7, line 932; 4.2, lines 400-401): report agreement between
passes A and B, per outcome, with the number of units each figure rests on. It writes nothing.

Reported: raw agreement, as "k of n units", where n is the units with both an A and a B row and k those with the same
code in both; and the units with only one of the two passes. Cohen's κ and Gwet's AC1, which 4.2 also names, are not
computed: the contract gives no formula for either, and the toolkit does not pick one silently (proposal). It refuses
when the study, its row files or its code files have an error (fail closed, rule 1.2).

Exit 0 when reported, 1 when refused, 2 on a usage error. Not a gated stage (6.1).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from survey_codes import agreement, coded_outcomes  # noqa: E402
from survey_core import SurveyUsageError, parse_args, print_findings, safe, usage_exit  # noqa: E402
from survey_evidence import check_row_files  # noqa: E402
from survey_spec import load_study  # noqa: E402

PROG = "survey_agreement.py"
NOT_COMPUTED = ("Cohen's kappa and Gwet's AC1: not computed; the contract names them without a formula (a proposal "
                "names the formulas for the operator to adopt)")


def main(argv=None) -> int:
    try:
        root, project, _ = parse_args(sys.argv[1:] if argv is None else argv, PROG)
        study = load_study(project, root)
    except SurveyUsageError as exc:
        return usage_exit(exc)
    if study.spec is None or not study.ok:
        print_findings(study.findings)
        print(safe(f"REFUSED: {study.spec_rel} is malformed"))
        return 1
    if not coded_outcomes(study.spec):
        print(safe(f"REFUSED: {study.spec_rel} declares no outcome whose source is codes"))
        return 1
    report = check_row_files(study)
    if report.findings:
        print_findings(report.findings)
        print(f"REFUSED: the row or code files have {len(report.findings)} error(s); no agreement is reported on them")
        return 1
    for a in agreement(report.codes):
        print(safe(f"{a.outcome}: raw agreement {a.agreeing} of {a.units} unit(s) with both passes; "
                   f"{a.missing_pass} unit(s) with one pass only"))
    for outcome in sorted(set(coded_outcomes(study.spec)) - set(report.codes.rows)):
        print(safe(f"{outcome}: raw agreement 0 of 0 unit(s) with both passes; no code rows"))
    print(NOT_COMPUTED)
    return 0


if __name__ == "__main__":
    sys.exit(main())
