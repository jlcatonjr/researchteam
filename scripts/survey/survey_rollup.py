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

import os
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from survey_attribution import columns as attribution_columns  # noqa: E402
from survey_codes import CODES_COLUMNS  # noqa: E402
from survey_core import (  # noqa: E402
    MAX_JSON_BYTES, SurveyUsageError, parse_args, print_findings, q, read_capped, reason, safe, sha256_bytes,
    symlink_components, usage_exit,
)
from survey_final import csv_bytes, locate_in_study, roll_up, rollup_columns  # noqa: E402
from survey_finalize import TOOL as FINALIZE, compute_final, hash_inputs, write_output  # noqa: E402
from survey_provenance import (  # noqa: E402
    ABSENT, check_current, gate_entries, make_record, record_bytes, record_rel,
)
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
    final_rec = record_rel(final.repo_rel)
    fold = lambda p: unicodedata.normalize("NFC", p).casefold()  # noqa: E731
    if {fold(out.repo_rel), fold(record_rel(out.repo_rel))} & {fold(final.repo_rel), fold(final_rec)}:
        return refuse(f"the output {q(out.repo_rel)} or its record would be the final file {q(final.repo_rel)} or its "
                      "record; nothing was written")
    links = symlink_components(root, final_rec)
    if links:
        return refuse(f"a component of the record path {q(final_rec)} is a symbolic link ({', '.join(map(q, links))}); "
                      "nothing was written")
    # Every file read is hashed now, before the final codes are worked out again, and guarded until the write.
    inputs, guards, error = hash_inputs(root, study)
    if error:
        return refuse(f"{error}; nothing was written")
    try:
        final_path = root.joinpath(*final.repo_rel.split("/"))
        rec_path = root.joinpath(*final_rec.split("/"))
        final_data = read_capped(final_path, MAX_CSV_BYTES) if os.path.lexists(final_path) else None
        record_data = read_capped(rec_path, MAX_JSON_BYTES) if os.path.lexists(rec_path) else b""
        att_rp = study.paths["/unit/attribution/file"]
        att_data = read_capped(root.joinpath(*att_rp.repo_rel.split("/")), MAX_CSV_BYTES)
    except OSError as exc:
        return refuse(f"an input cannot be read: {reason(exc)}; nothing was written")
    if final_data is None:
        return refuse(f"{q(final.repo_rel)} does not exist, or is larger than {MAX_CSV_BYTES} bytes; nothing was "
                      "written")
    if att_data is None or record_data is None:
        return refuse("an input is larger than the cap; nothing was written")
    final_sha = sha256_bytes(final_data)
    rec_sha = sha256_bytes(record_data) if os.path.lexists(rec_path) else ABSENT
    guards[final.repo_rel] = final_sha
    guards[final_rec] = rec_sha if rec_sha != ABSENT else None
    inputs = inputs[:1] + [(final.repo_rel, final_sha), (final_rec, rec_sha)] + inputs[1:]
    # The record holds no hash of the final file (4.6, line 565), so a hand edit leaves it "built": the final codes
    # are worked out again from their inputs, and the file must be exactly those bytes, in every status (operator
    # decision O3, a tightening).
    expected, exceptions, findings = compute_final(study)
    if findings or expected != final_data:
        print_findings(findings)
        return refuse(f"{q(final.repo_rel)} is not what survey-finalize gives from the study's inputs (edited by "
                      "hand, or written from other inputs): run survey-finalize again; nothing was written")
    # A record that no longer matches its inputs: the next stage refuses, except in a draft study, where the mismatch
    # is reported and the stage runs (4.6, lines 566-568; O3).
    current = check_current(root, final_rec, expect_tool=FINALIZE, expect_schema_version=study.spec["schema_version"])
    if not current.built:
        for why in current.reasons:
            print(safe(f"note: {why}"))
        if study.spec["status"] != "draft":
            return refuse(f"{q(final.repo_rel)} is not a current output of survey-finalize; run it again first (4.6, "
                          "lines 566-567); nothing was written")
        print(safe(f"reported: the record of {q(final.repo_rel)} does not match its inputs; a draft study runs the "
                   "stage all the same (4.6, line 568)"))
    final_rows, _sha = rows_from_bytes(final_data, final.repo_rel, CODES_COLUMNS, "codes-columns")
    att_rows, _sha = rows_from_bytes(att_data, att_rp.repo_rel, attribution_columns(study.spec), "attribution-columns")
    if final_rows.findings or att_rows.findings:
        print_findings(final_rows.findings + att_rows.findings)
        return refuse("an input is malformed; nothing was written")
    rolled = roll_up(study, [r for _n, r in final_rows.rows], {r["unit_id"]: r for _n, r in att_rows.rows})
    if rolled.findings:
        print_findings(rolled.findings)
        return refuse("an outcome's rule cannot give a value for a cell (4.2, lines 412-417); nothing was written")
    data = csv_bytes(rollup_columns(study.spec), rolled.rows)
    # The rollup rests on the evidence file through the final codes: it carries the count of legacy exceptions the
    # evidence was read with (4.1, line 366).
    record = record_bytes(make_record(study, out.repo_rel, TOOL, inputs, gate_entries(study, GATES), plugins=[],
                                      legacy_exceptions=exceptions))
    code = write_output(root, study, out.repo_rel, data, record, guards)
    if code == 0:
        print(f"rollup: {len(rolled.rows)} row(s); {rolled.left_out} author(s) left out, all of whose units were not "
              "counted or were excluded (4.2, lines 409-410)")
    return code


if __name__ == "__main__":
    sys.exit(main())
