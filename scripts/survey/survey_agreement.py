"""``survey-agreement <project>`` (contract section 7, line 932; 4.2, lines 400-401): report agreement between
passes A and B, per coded outcome, in the order the study declares them. It writes nothing.

One line per outcome: ``<outcome>: n=<n> raw=<d.ddd> kappa=<d.ddd|undefined> AC1=<d.ddd|undefined>``, then the units
with one pass only. n is the units with both an A and a B row; a unit with one pass is left out of the three
statistics. The definitions are the operator's decisions of 2026-11-25 (``survey_codes.statistics``): every code its
own category, kappa unweighted, AC1 over the codes the specification allows, exact arithmetic, three decimals rounded
half to even, ``undefined`` where a statistic is. It refuses when the study, its row files or its code files have an
error (rule 1.2).

Exit 0 when reported, 1 when refused, 2 on a usage error. Not a gated stage (6.1).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from survey_codes import agreement, coded_outcomes, three_decimals  # noqa: E402
from survey_core import SurveyUsageError, parse_args, print_findings, safe, usage_exit  # noqa: E402
from survey_evidence import check_row_files  # noqa: E402
from survey_spec import load_study  # noqa: E402

PROG = "survey_agreement.py"


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
    outcomes = coded_outcomes(study.spec)
    for a in agreement(report.codes, outcomes):  # one line per coded outcome, in the study's declared order
        empty = "" if report.codes.rows.get(a.outcome) else "; no code rows"
        print(safe(f"{a.outcome}: n={a.units} raw={three_decimals(a.raw)} kappa={three_decimals(a.kappa)} "
                   f"AC1={three_decimals(a.ac1)}; {a.missing_pass} unit(s) with one pass only{empty}"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
