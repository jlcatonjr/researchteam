"""``survey-rollup <project> <final file> --out <path>`` (contract section 7, line 934; 4.2, lines 403-422; the
operator's decisions of 2026-11-25, D5 and D6): roll final codes of passage or work units up to their author, with a
provenance record beside the output.

- The final file must be exactly what ``survey-finalize`` gives from the study's inputs, in every status (operator
  decision O3), and its record must exist and still match its inputs (``check_current``); in a draft study a record
  that does not match is reported and the stage runs (4.6, line 568). It lies inside the study's folder; so does the
  output, which is not a file the study declares. The record lists every file read (4.6, line 563).
- Only ``final`` rows count, and only units whose attribution status is counted and which no
  ``unit.exclude_from_rollup`` value leaves out; NA codes and the missing value are skipped; each outcome's rule
  (``single-code``, ``mixed-if-conflict``, ``max-order``, ``any-present``) gives the cell, and a cell with nothing left
  gets the missing value; outcomes whose rollup is ``none``, or not from codes, are not in it.
- Columns: ``person_id``; each ``unit.rollup_by`` key; ``author_kind``; one per rolled-up outcome, with
  ``<outcome>__types`` beside it where ``unit.rollup_types`` is set. Rows: one per author and combination of
  ``rollup_by`` values, in code-point order of ``person_id``, then of those values.
- An existing output is never appended to: identical bytes are "unchanged", anything else is refused.

Exit 0 when written (or unchanged), 1 when refused, 2 on a usage error. Not a refusing stage (D6).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from survey_core import SurveyUsageError, parse_args, print_findings, safe, usage_exit  # noqa: E402
from survey_final import csv_bytes, locate_in_study, roll_up, rollup_columns  # noqa: E402
from survey_finalize import load_final, write_output  # noqa: E402
from survey_provenance import gate_entries, make_record, record_bytes  # noqa: E402
from survey_spec import load_study  # noqa: E402

PROG = "survey_rollup.py"
TOOL = "survey-rollup"
GATES = ("S5",)  # operator decision D6


def refuse(msg: str) -> int:
    print(safe(f"REFUSED: {msg}"))
    return 1


def parse(argv: list) -> tuple:
    args = list(argv)
    if "--out" not in args or args.index("--out") == len(args) - 1:
        raise SurveyUsageError(f"usage: {PROG} [--root DIR] <project> <final file> --out <path>")
    i = args.index("--out")
    out = args[i + 1]
    del args[i:i + 2]
    root, project, extra = parse_args(args, PROG, ("final file",))
    return root, project, extra[0], out


def main(argv=None) -> int:
    try:
        root, project, final_arg, out_arg = parse(sys.argv[1:] if argv is None else argv)
        study = load_study(project, root)
    except SurveyUsageError as exc:
        return usage_exit(exc)
    if study.spec is None or not study.ok:
        print_findings(study.findings)
        return refuse(f"{study.spec_rel} is malformed; nothing was written")
    if study.spec["unit"]["kind"] not in ("passage", "work"):
        return refuse("the rollup takes passage or work codes to their author (4.2, line 403); this is an author "
                      "study")
    out, errors = locate_in_study(study, out_arg, "output")
    if errors:
        print_findings(errors)
        return refuse("a path is not allowed; nothing was written")
    # The final file: current, and exactly what survey-finalize gives, every file read hashed and guarded (O3, S2).
    loaded, code = load_final(root, study, final_arg, [out.repo_rel])
    if loaded is None:
        return code
    rolled = roll_up(study, loaded.rows, loaded.attribution)
    if rolled.findings:
        print_findings(rolled.findings)
        return refuse("an outcome's rule cannot give a value for a cell (4.2, lines 412-417); nothing was written")
    data = csv_bytes(rollup_columns(study.spec), rolled.rows)
    # The rollup rests on the evidence file through the final codes: it carries the count of legacy exceptions the
    # evidence was read with (4.1, line 366).
    record = record_bytes(make_record(study, out.repo_rel, TOOL, loaded.inputs, gate_entries(study, GATES), plugins=[],
                                      legacy_exceptions=loaded.exceptions))
    code = write_output(root, study, out.repo_rel, data, record, loaded.guards, TOOL)
    if code == 0:
        print(f"rollup: {len(rolled.rows)} row(s); {rolled.left_out} author(s) left out, all of whose units were not "
              "counted or were excluded (4.2, lines 409-410)")
    return code


if __name__ == "__main__":
    sys.exit(main())
