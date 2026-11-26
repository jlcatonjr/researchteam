"""``survey-rollup <project> <final file> --out <path>`` (contract section 7, line 934; 4.2, lines 403-422; the
operator's decisions of 2026-11-25, D5 and D6): roll final codes of passage or work units up to their author, with a
provenance record beside the output.

- The final file must be one ``survey-finalize`` wrote: its record exists and still matches its inputs
  (``check_current``). It lies inside the study's folder; so does the output, which is not a file the study declares.
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

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from survey_attribution import columns as attribution_columns  # noqa: E402
from survey_codes import CODES_COLUMNS  # noqa: E402
from survey_core import (  # noqa: E402
    MAX_JSON_BYTES, SurveyUsageError, load_json_strict, parse_args, print_findings, q, read_capped, reason, safe,
    sha256_bytes, usage_exit,
)
from survey_final import csv_bytes, locate_in_study, roll_up, rollup_columns  # noqa: E402
from survey_finalize import TOOL as FINALIZE, write_output  # noqa: E402
from survey_provenance import check_current, gate_entries, make_record, record_bytes, record_rel  # noqa: E402
from survey_spec import load_study  # noqa: E402
from survey_tables import MAX_CSV_BYTES, rows_from_bytes  # noqa: E402

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
    final, errors = locate_in_study(study, final_arg, "final-file")
    out, out_errors = locate_in_study(study, out_arg, "output")
    if errors or out_errors:
        print_findings(errors + out_errors)
        return refuse("a path is not allowed; nothing was written")
    current = check_current(root, record_rel(final.repo_rel), expect_tool=FINALIZE,
                            expect_schema_version=study.spec["schema_version"])
    if not current.built:
        for why in current.reasons:
            print(safe(f"note: {why}"))
        return refuse(f"{q(final.repo_rel)} is not a current output of survey-finalize; run it again first (4.6, "
                      "lines 566-567); nothing was written")
    try:
        final_data = read_capped(root.joinpath(*final.repo_rel.split("/")), MAX_CSV_BYTES)
        record_data = read_capped(root.joinpath(*record_rel(final.repo_rel).split("/")), MAX_JSON_BYTES)
        att_rp = study.paths["/unit/attribution/file"]
        att_data = read_capped(root.joinpath(*att_rp.repo_rel.split("/")), MAX_CSV_BYTES)
    except OSError as exc:
        return refuse(f"an input cannot be read: {reason(exc)}; nothing was written")
    if final_data is None or att_data is None or record_data is None:
        return refuse("an input is larger than the cap; nothing was written")
    final_rows, final_sha = rows_from_bytes(final_data, final.repo_rel, CODES_COLUMNS, "codes-columns")
    att_rows, att_sha = rows_from_bytes(att_data, att_rp.repo_rel, attribution_columns(study.spec),
                                        "attribution-columns")
    if final_rows.findings or att_rows.findings:
        print_findings(final_rows.findings + att_rows.findings)
        return refuse("an input is malformed; nothing was written")
    final_record, _errs = load_json_strict(record_data, record_rel(final.repo_rel))
    rolled = roll_up(study, [r for _n, r in final_rows.rows], {r["unit_id"]: r for _n, r in att_rows.rows})
    if rolled.findings:
        print_findings(rolled.findings)
        return refuse("an outcome's rule cannot give a value; nothing was written (4.2, line 412)")
    data = csv_bytes(rollup_columns(study.spec), rolled.rows)
    spec_sha = sha256_bytes(study.spec_bytes)
    inputs = [(study.spec_rel, spec_sha), (final.repo_rel, final_sha), (att_rp.repo_rel, att_sha)]
    guards = {study.spec_rel: spec_sha, final.repo_rel: final_sha, att_rp.repo_rel: att_sha}
    # The rollup rests on the final codes, which rest on the evidence file: it carries the count of legacy exceptions
    # the final codes were read with (4.1, line 366).
    exceptions = final_record.get("legacy_exceptions", 0) if isinstance(final_record, dict) else 0
    record = record_bytes(make_record(study, out.repo_rel, TOOL, inputs, gate_entries(study, GATES), plugins=[],
                                      legacy_exceptions=exceptions))
    code = write_output(root, study, out.repo_rel, data, record, guards)
    if code == 0:
        print(f"rollup: {len(rolled.rows)} row(s); {rolled.left_out} author(s) left out, all of whose units were not "
              "counted or were excluded (4.2, lines 409-410)")
    return code


if __name__ == "__main__":
    sys.exit(main())
