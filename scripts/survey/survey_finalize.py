"""``survey-finalize <project> --out <path>`` (contract section 7, line 933; 4.2, lines 397-400; the operator's
decisions of 2026-11-25, D2 to D4 and D6): write the final codes of every coded outcome to a file of their own, with a
provenance record beside it, fail-closed.

- Every row and code file must pass its checks first (rule 1.2).
- Agreed passes give pass A's row, with ``coder`` and ``note`` ``agreed`` (``agreed; evidence differed`` where the
  passes cite other evidence) and ``level`` empty (D3). A disagreement, or a unit with one pass, takes the
  adjudication's coder, basis, reporter, evidence and note. Without one, nothing is written and the units are listed.
  A unit with no pass at all refuses too (D4). No code is ever filled in (rule 1.3).
- A ``final`` row the codes file already holds must equal the derived row, cell for cell; one that differs, or has no
  derived row, refuses (operator decision O2).
- The output lies inside the study's folder and is not a file the study declares or a gate covers
  (``check_output_target``), nor named as a record. The passes file is only read. An existing output is never
  appended to: identical bytes are "unchanged", anything else is refused. A file at the record's path that is not
  this output's record is never written over.
- The record lists every file read (4.6, line 563), gate S5 with its state, and the legacy exceptions the evidence is
  read with (D6).

Exit 0 when written (or unchanged), 1 when refused, 2 on a usage error. Not a refusing stage (D6).
"""
from __future__ import annotations

import os
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from survey_attribution import columns as attribution_columns  # noqa: E402
from survey_codes import CODES_COLUMNS, coded_outcomes  # noqa: E402
from survey_core import (  # noqa: E402
    SurveyUsageError, load_json_strict, parse_args, print_findings, q, read_capped, reason, safe, sha256_bytes,
    symlink_components, usage_exit,
)
from survey_evidence import check_row_files  # noqa: E402
from survey_final import csv_bytes, finalise, locate_in_study, study_units  # noqa: E402
from survey_provenance import (  # noqa: E402
    ABSENT, MAX_INPUT_BYTES, SUFFIX, WriteRefused, check_current, check_output_target, check_record_shape,
    gate_entries, make_record, record_bytes, record_rel, write_all,
)
from survey_spec import load_study  # noqa: E402
from survey_tables import rows_from_bytes  # noqa: E402

PROG = "survey_finalize.py"
TOOL = "survey-finalize"
#: The gates the final codes' record lists (operator decision D6).
GATES = ("S5",)


def refuse(msg: str) -> int:
    print(safe(f"REFUSED: {msg}"))
    return 1


def input_paths(study) -> list:
    """Every declared file the final codes are worked out from or checked against (4.6, line 563: "the files the tool
    actually read"), in a fixed order: the specification is listed apart; then each coded outcome's codes file and
    adjudications file, the evidence file and its exceptions file, the attribution file (passage or work), the
    registry, the overrides file (read unless the identity source is one this version refuses), the forbidden
    vocabulary and each attribute's bucket table, as the row checks read them (rule 1.2). No fetch receipt is read:
    the row checks run without the 5.4 citation check (``check_row_files(citations=False)``)."""
    from survey_identity import identity_refusals

    spec = study.spec
    ptrs = []
    for i, o in enumerate(spec["outcomes"]):
        if o["source"]["kind"] == "codes":
            ptrs += [f"/outcomes/{i}/source/codes_file", f"/outcomes/{i}/source/adjudications"]
    ptrs += ["/evidence/file", "/evidence/legacy_exceptions"]
    if spec["unit"]["kind"] in ("passage", "work"):
        ptrs.append("/unit/attribution/file")
    ptrs.append("/identity/registry")
    if not identity_refusals(study):
        ptrs.append("/identity/overrides")
    ptrs.append("/vocabulary/forbidden")
    ptrs += [f"/attributes/{i}/bucketer/table" for i in range(len(spec.get("attributes", [])))]
    seen, out = {study.spec_rel}, []
    for ptr in ptrs:
        rp = study.paths.get(ptr)
        if rp is not None and rp.repo_rel not in seen:
            seen.add(rp.repo_rel)
            out.append(rp)
    return out


def hash_inputs(root: Path, study, keep: dict | None = None) -> tuple:
    """``(inputs for the record, guards for the write, error)``: each input file's SHA-256 as read now (``""``, ABSENT,
    when a declared file is not there). With *keep*, the bytes read are kept there by repository-relative path, so a
    caller parses exactly what was hashed."""
    spec_sha = sha256_bytes(study.spec_bytes)
    inputs, guards = [(study.spec_rel, spec_sha)], {study.spec_rel: spec_sha}
    for rp in input_paths(study):
        path = root.joinpath(*rp.repo_rel.split("/"))
        if not os.path.lexists(path):
            inputs.append((rp.repo_rel, ABSENT))
            guards[rp.repo_rel] = None
            continue
        try:
            data = read_capped(path, MAX_INPUT_BYTES)
        except OSError as exc:
            return [], {}, f"{q(rp.repo_rel)} cannot be read: {reason(exc)}"
        if data is None:
            return [], {}, f"{q(rp.repo_rel)} is larger than {MAX_INPUT_BYTES} bytes"
        digest = sha256_bytes(data)
        inputs.append((rp.repo_rel, digest))
        guards[rp.repo_rel] = digest
        if keep is not None:
            keep[rp.repo_rel] = data
    return inputs, guards, ""


def write_output(root: Path, study, out_rel: str, data: bytes, record: bytes, guards: dict, tool: str = TOOL) -> int:
    """Write one output and its record: :func:`write_outputs` with one item."""
    return write_outputs(root, study, [(out_rel, data, record)], guards, tool)


def write_outputs(root: Path, study, items: list, guards: dict, tool: str = TOOL, *, replace: bool = False,
                  unrecorded: tuple | None = None) -> int:
    """Write each ``(output, bytes, record bytes)`` of *items* and its record in one ``write_all``: every output first,
    then *unrecorded*, then every record, or report them unchanged. Everything is checked before anything is written.

    - An existing output is never appended to: identical bytes are "unchanged" (its record renewed if the inputs
      moved), anything else is refused (D2). A file at a record's path that is not the record *tool* wrote for that
      output is never written over.
    - With *replace* (``survey-frame`` only, operator ruling B3), an existing output with other bytes is replaced, but
      only where the record beside it is *tool*'s record for that output: an output with no record, or a foreign
      file, is still refused. Every other command keeps the default, refuse.
    - *unrecorded* is ``(path, bytes, own pointer)``: one declared file written with no record of its own (the
      frame-change log, operator ruling B2). It passes the same output checks, its declared pointer allowed; the
      caller guards it with the bytes it read, so a change on disk since then refuses the write."""
    fold = lambda p: unicodedata.normalize("NFC", p).casefold()  # noqa: E731
    named = [fold(p) for out_rel, _d, _r in items for p in (out_rel, record_rel(out_rel))]
    if unrecorded is not None:
        named.append(fold(unrecorded[0]))
    if len(set(named)) != len(named):
        return refuse("two of the outputs, or an output and a record, are the same path; nothing was written")
    guards = dict(guards)
    data_out, record_out, report = [], [], []
    if unrecorded is not None:
        log_rel, log_data, pointer = unrecorded
        try:
            check_output_target(study, log_rel, own_pointer=pointer)
        except WriteRefused as exc:
            return refuse(f"{reason(exc)}; nothing was written")
        links = symlink_components(root, log_rel)
        if links:
            return refuse(f"a component of {q(log_rel)} is a symbolic link ({', '.join(map(q, links))}); nothing "
                          "was written")
        if log_rel not in guards:
            return refuse(f"{q(log_rel)} was not read before it is written; nothing was written")
    for out_rel, data, record in items:
        rec_rel = record_rel(out_rel)
        if is_record_name(out_rel):
            return refuse(f"{q(out_rel)} ends in {SUFFIX!r}, the name of a provenance record (4.6, line 562); an "
                          "output is not named as a record; nothing was written")
        try:
            check_output_target(study, out_rel)
            check_output_target(study, rec_rel)
        except WriteRefused as exc:
            return refuse(f"{reason(exc)}; nothing was written")
        links = symlink_components(root, rec_rel)
        if links:
            return refuse(f"a component of the record path {q(rec_rel)} is a symbolic link "
                          f"({', '.join(map(q, links))}); nothing was written")
        out_path = root.joinpath(*out_rel.split("/"))
        rec_path = root.joinpath(*rec_rel.split("/"))
        try:
            existing = read_capped(out_path, MAX_INPUT_BYTES) if os.path.lexists(out_path) else None
            old_record = read_capped(rec_path, MAX_INPUT_BYTES) if os.path.lexists(rec_path) else None
        except OSError as exc:
            return refuse(f"{q(out_rel)} or its record cannot be read: {reason(exc)}; nothing was written")
        if os.path.lexists(rec_path):
            doc, errs = load_json_strict(old_record, rec_rel) if old_record is not None else (None, ["too large"])
            if errs or check_record_shape(doc, rec_rel) or doc["output"] != out_rel or doc["tool"] != tool \
                    or doc["study"] != study.spec["id"]:
                return refuse(f"{q(rec_rel)} exists and is not the provenance record {tool} wrote for {q(out_rel)} "
                              f"in study {q(study.spec['id'])} (4.6); a record is never written over another file; "
                              "nothing was written")
        if existing is not None and existing != data and not (replace and old_record is not None):
            if replace:
                return refuse(f"{q(out_rel)} exists with other contents and no record of {tool}'s beside it; only "
                              f"{tool}'s own output is replaced (operator ruling B3); nothing was written")
            return refuse(f"{q(out_rel)} exists with other contents; an output is never appended to or overwritten "
                          "(operator decision D2); nothing was written")
        guards[out_rel] = sha256_bytes(existing) if existing is not None else None
        guards[rec_rel] = sha256_bytes(old_record) if old_record is not None else None
        if existing != data:
            data_out.append((out_rel, data))
        if old_record != record:
            record_out.append((rec_rel, record))
        state = "unchanged" if existing == data else ("replaced" if existing is not None else "wrote")
        report += [f"{state}: {out_rel}",
                   f"{'renewed' if existing == data and old_record != record else state}: {rec_rel}"]
    middle = []
    if unrecorded is not None:
        middle = [(unrecorded[0], unrecorded[1])]
        report.append(f"appended one entry: {unrecorded[0]}")
    outputs = data_out + middle + record_out
    if outputs:
        try:
            # Every output first, the records last. Interrupted between them, an old record (if any) names other
            # inputs or is missing, so the output reads as not built; a refusal at a late check, or a guarded input
            # that changed since it was read, changes nothing (write_all).
            write_all(root, outputs, guards)
        except WriteRefused as exc:
            return refuse(f"{reason(exc)}; nothing was written")
        except OSError as exc:
            return refuse(f"{reason(exc)}; the write did not complete")
    for line in report:
        print(safe(line))
    return 0


@dataclass
class CurrentFinal:
    """What :func:`load_final` read: the final rows, the attribution rows, the bytes of each declared input it hashed
    (by repository-relative path), the record's inputs and the guards, and the legacy-exception count."""
    rel: str
    rows: list
    attribution: dict
    data: dict
    inputs: list
    guards: dict
    exceptions: int


def load_final(root: Path, study, final_arg: str, out_rels: list) -> tuple:
    """A stage's input of final codes (the rollup, the frame): ``(CurrentFinal, 0)`` or ``(None, exit code)`` with the
    refusal printed.

    - The final file lies inside the study's folder, and no output named in *out_rels* or its record is the final file
      or its record; the final file's record path has no link on its way.
    - Every declared input is hashed before the final codes are worked out again, and guarded until the write.
    - The final file must be exactly what ``survey-finalize`` gives from the study's inputs, in every status
      (operator decision O3, a tightening): the record holds no hash of its output (4.6, line 565).
    - Its record must exist and match its inputs; in a draft study a mismatch is reported and the stage runs (4.6,
      lines 566-568; O3)."""
    final, errors = locate_in_study(study, final_arg, "final-file")
    if errors:
        print_findings(errors)
        return None, refuse("a path is not allowed; nothing was written")
    final_rec = record_rel(final.repo_rel)
    fold = lambda p: unicodedata.normalize("NFC", p).casefold()  # noqa: E731
    mine = {fold(final.repo_rel), fold(final_rec)}
    for out_rel in out_rels:
        if {fold(out_rel), fold(record_rel(out_rel))} & mine:
            return None, refuse(f"the output {q(out_rel)} or its record would be the final file {q(final.repo_rel)} or "
                                "its record; nothing was written")
    links = symlink_components(root, final_rec)
    if links:
        return None, refuse(f"a component of the record path {q(final_rec)} is a symbolic link "
                            f"({', '.join(map(q, links))}); nothing was written")
    keep: dict = {}
    inputs, guards, error = hash_inputs(root, study, keep)
    if error:
        return None, refuse(f"{error}; nothing was written")
    try:
        final_path = root.joinpath(*final.repo_rel.split("/"))
        rec_path = root.joinpath(*final_rec.split("/"))
        final_data = read_capped(final_path, MAX_INPUT_BYTES) if os.path.lexists(final_path) else None
        record_data = read_capped(rec_path, MAX_INPUT_BYTES) if os.path.lexists(rec_path) else b""
    except OSError as exc:
        return None, refuse(f"an input cannot be read: {reason(exc)}; nothing was written")
    if final_data is None:
        return None, refuse(f"{q(final.repo_rel)} does not exist, or is larger than {MAX_INPUT_BYTES} bytes; nothing "
                            "was written")
    if record_data is None:
        return None, refuse("an input is larger than the cap; nothing was written")
    final_sha = sha256_bytes(final_data)
    rec_sha = sha256_bytes(record_data) if os.path.lexists(rec_path) else ABSENT
    guards[final.repo_rel] = final_sha
    guards[final_rec] = rec_sha if rec_sha != ABSENT else None
    inputs = inputs[:1] + [(final.repo_rel, final_sha), (final_rec, rec_sha)] + inputs[1:]
    expected, exceptions, findings = compute_final(study)
    if findings or expected != final_data:
        print_findings(findings)
        return None, refuse(f"{q(final.repo_rel)} is not what survey-finalize gives from the study's inputs (edited "
                            "by hand, or written from other inputs): run survey-finalize again; nothing was written")
    current = check_current(root, final_rec, expect_tool=TOOL, expect_schema_version=study.spec["schema_version"])
    if not current.built:
        for why in current.reasons:
            print(safe(f"note: {why}"))
        if study.spec["status"] != "draft":
            return None, refuse(f"{q(final.repo_rel)} is not a current output of survey-finalize; run it again first "
                                "(4.6, lines 566-567); nothing was written")
        print(safe(f"reported: the record of {q(final.repo_rel)} does not match its inputs; a draft study runs the "
                   "stage all the same (4.6, line 568)"))
    final_rows, _sha = rows_from_bytes(final_data, final.repo_rel, CODES_COLUMNS, "codes-columns")
    att_rp = study.paths["/unit/attribution/file"]
    att_rows, _sha = rows_from_bytes(keep.get(att_rp.repo_rel, b""), att_rp.repo_rel, attribution_columns(study.spec),
                                     "attribution-columns")
    if final_rows.findings or att_rows.findings:
        print_findings(final_rows.findings + att_rows.findings)
        return None, refuse("an input is malformed; nothing was written")
    return CurrentFinal(final.repo_rel, [r for _n, r in final_rows.rows], {r["unit_id"]: r for _n, r in att_rows.rows},
                        keep, inputs, guards, exceptions), 0


def overrides_bytes(study, loaded: CurrentFinal) -> bytes | None:
    """The overrides file's bytes as :func:`load_final` hashed them, or None when it is not declared or absent."""
    rp = study.paths.get("/identity/overrides")
    return loaded.data.get(rp.repo_rel) if rp is not None else None


def is_record_name(rel: str) -> bool:
    """Whether a path is named as a provenance record (case and normalisation folded, as a file system may)."""
    return unicodedata.normalize("NFC", rel).casefold().endswith(SUFFIX)


def compute_final(study) -> tuple:
    """The final codes a run would write, worked out without writing: ``(bytes, exceptions, findings)``."""
    report = check_row_files(study, citations=False)  # no receipt is read (see check_row_files)
    if report.findings:
        return b"", 0, report.findings
    units, unit_findings = study_units(study)
    final = finalise(study, report.codes, units)
    if unit_findings or final.findings:
        return b"", 0, unit_findings + final.findings
    return csv_bytes(CODES_COLUMNS, final.rows), report.exceptions, []


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
    data, exceptions, findings = compute_final(study)
    if findings:
        print_findings(findings)
        return refuse("final codes cannot be written for every unit, or a row or code file has an error (4.2, lines "
                      "397-399; operator decision D4); nothing was written")
    record = record_bytes(make_record(study, out.repo_rel, TOOL, inputs, gate_entries(study, GATES), plugins=[],
                                      legacy_exceptions=exceptions))
    return write_output(root, study, out.repo_rel, data, record, guards)


if __name__ == "__main__":
    sys.exit(main())
