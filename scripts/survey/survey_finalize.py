"""``survey-finalize <project> --out <path>`` (contract section 7, line 933; 4.2, lines 397-400; the operator's
decisions of 2026-11-25, D2 to D4 and D6): write the final codes of every coded outcome to a file of their own, with a
provenance record beside it, fail-closed.

- Every row and code file must pass its checks first (rule 1.2).
- Agreed passes give pass A's row, with ``coder`` and ``note`` ``agreed`` (``agreed; evidence differed`` where the
  passes cite other evidence) and ``level`` empty (D3). A disagreement, or a unit with one pass, takes the
  adjudication's coder, basis, reporter, evidence and note. Without one, nothing is written and the units are listed.
  A unit with no pass at all refuses too (D4). No code is ever filled in (rule 1.3).
- The output lies inside the study's folder and is not a file the study declares or a gate covers
  (``check_output_target``). The passes file is only read. An existing output is never appended to: identical bytes
  are "unchanged", anything else is refused.
- The record lists the inputs read, gate S5 with its state, and the legacy exceptions the evidence is read with (D6).

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

from survey_codes import CODES_COLUMNS, coded_outcomes  # noqa: E402
from survey_core import (  # noqa: E402
    SurveyUsageError, parse_args, print_findings, q, read_capped, reason, safe, sha256_bytes, usage_exit,
)
from survey_evidence import check_row_files  # noqa: E402
from survey_final import csv_bytes, finalise, locate_in_study, study_units  # noqa: E402
from survey_provenance import (  # noqa: E402
    ABSENT, WriteRefused, check_output_target, gate_entries, make_record, record_bytes, record_rel, write_all,
)
from survey_spec import load_study  # noqa: E402
from survey_tables import MAX_CSV_BYTES  # noqa: E402

PROG = "survey_finalize.py"
TOOL = "survey-finalize"
#: The gates the final codes' record lists (operator decision D6).
GATES = ("S5",)


def refuse(msg: str) -> int:
    print(safe(f"REFUSED: {msg}"))
    return 1


def input_paths(study) -> list:
    """The declared files the final codes rest on, in a fixed order: the specification is listed apart; then each
    coded outcome's codes file and adjudications file, the evidence file and its exceptions file, and the attribution
    file (passage or work) or the registry (author study), which give the units."""
    ptrs = []
    for i, o in enumerate(study.spec["outcomes"]):
        if o["source"]["kind"] == "codes":
            ptrs += [f"/outcomes/{i}/source/codes_file", f"/outcomes/{i}/source/adjudications"]
    ptrs += ["/evidence/file", "/evidence/legacy_exceptions"]
    ptrs.append("/unit/attribution/file" if study.spec["unit"]["kind"] in ("passage", "work") else
                "/identity/registry")
    seen, out = set(), []
    for ptr in ptrs:
        rp = study.paths.get(ptr)
        if rp is not None and rp.repo_rel not in seen:
            seen.add(rp.repo_rel)
            out.append(rp)
    return out


def hash_inputs(root: Path, study) -> tuple:
    """``(inputs for the record, guards for the write, error)``: each input file's SHA-256 as read now (``""``, ABSENT,
    when a declared file is not there)."""
    inputs, guards = [(study.spec_rel, sha256_bytes(study.spec_bytes))], {study.spec_rel: sha256_bytes(study.spec_bytes)}
    for rp in input_paths(study):
        path = root.joinpath(*rp.repo_rel.split("/"))
        if not os.path.lexists(path):
            inputs.append((rp.repo_rel, ABSENT))
            guards[rp.repo_rel] = None
            continue
        try:
            data = read_capped(path, MAX_CSV_BYTES)
        except OSError as exc:
            return [], {}, f"{q(rp.repo_rel)} cannot be read: {reason(exc)}"
        if data is None:
            return [], {}, f"{q(rp.repo_rel)} is larger than {MAX_CSV_BYTES} bytes"
        digest = sha256_bytes(data)
        inputs.append((rp.repo_rel, digest))
        guards[rp.repo_rel] = digest
    return inputs, guards, ""


def write_output(root: Path, study, out_rel: str, data: bytes, record: bytes, guards: dict) -> int:
    """Write an output and its record (the output first, the record last), or report it unchanged. An existing
    output is never appended to: identical bytes are "unchanged" (its record renewed if the inputs moved), anything
    else is refused (D2)."""
    rec_rel = record_rel(out_rel)
    try:
        check_output_target(study, out_rel)
        check_output_target(study, rec_rel)
    except WriteRefused as exc:
        return refuse(f"{reason(exc)}; nothing was written")
    out_path = root.joinpath(*out_rel.split("/"))
    rec_path = root.joinpath(*rec_rel.split("/"))
    try:
        existing = read_capped(out_path, MAX_CSV_BYTES) if os.path.lexists(out_path) else None
        old_record = read_capped(rec_path, MAX_CSV_BYTES) if os.path.lexists(rec_path) else None
    except OSError as exc:
        return refuse(f"{q(out_rel)} cannot be read: {reason(exc)}; nothing was written")
    if existing is not None and existing != data:
        return refuse(f"{q(out_rel)} exists with other contents; an output is never appended to or overwritten with "
                      "different codes (operator decision D2); nothing was written")
    guards = dict(guards)
    guards[out_rel] = sha256_bytes(existing) if existing is not None else None
    guards[rec_rel] = sha256_bytes(old_record) if old_record is not None else None
    outputs = [] if existing == data else [(out_rel, data)]
    if old_record != record:
        outputs.append((rec_rel, record))
    if outputs:
        try:
            # The output first, its record last. Interrupted between them, the old record (if any) names other
            # inputs or is missing, so the output reads as not built; a refusal at a late check, or a guarded input
            # that changed since it was read, changes nothing (write_all).
            write_all(root, outputs, guards)
        except WriteRefused as exc:
            return refuse(f"{reason(exc)}; nothing was written")
        except OSError as exc:
            return refuse(f"{reason(exc)}; the write did not complete")
    state = "unchanged" if existing == data else "wrote"
    print(safe(f"{state}: {out_rel}"))
    print(safe(f"{'renewed' if existing == data and old_record != record else state}: {rec_rel}"))
    return 0


def parse(argv: list) -> tuple:
    args = list(argv)
    if "--out" not in args or args.index("--out") == len(args) - 1:
        raise SurveyUsageError(f"usage: {PROG} [--root DIR] <project> --out <path>")
    i = args.index("--out")
    out = args[i + 1]
    del args[i:i + 2]
    root, project, _ = parse_args(args, PROG)
    return root, project, out


def main(argv=None) -> int:
    try:
        root, project, out_arg = parse(sys.argv[1:] if argv is None else argv)
        study = load_study(project, root)
    except SurveyUsageError as exc:
        return usage_exit(exc)
    if study.spec is None or not study.ok:
        print_findings(study.findings)
        return refuse(f"{study.spec_rel} is malformed; nothing was written")
    if not coded_outcomes(study.spec):
        return refuse(f"{study.spec_rel} declares no outcome whose source is codes")
    out, errors = locate_in_study(study, out_arg, "output")
    if errors:
        print_findings(errors)
        return refuse("the output path is not allowed; nothing was written")
    inputs, guards, error = hash_inputs(root, study)
    if error:
        return refuse(f"{error}; nothing was written")
    report = check_row_files(study)
    if report.findings:
        print_findings(report.findings)
        return refuse(f"the row or code files have {len(report.findings)} error(s); nothing was written")
    units, unit_findings = study_units(study)
    final = finalise(study, report.codes, units)
    if unit_findings or final.findings:
        print_findings(unit_findings + final.findings)
        return refuse("final codes cannot be written for every unit (4.2, lines 397-399; operator decision D4); "
                      "nothing was written")
    data = csv_bytes(CODES_COLUMNS, final.rows)
    record = record_bytes(make_record(study, out.repo_rel, TOOL, inputs, gate_entries(study, GATES), plugins=[],
                                      legacy_exceptions=report.exceptions))
    return write_output(root, study, out.repo_rel, data, record, guards)


if __name__ == "__main__":
    sys.exit(main())
