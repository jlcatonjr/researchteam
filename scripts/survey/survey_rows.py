"""``survey-rows <project> <batch>`` (contract section 7, line 929; 4.1, lines 322-326; 4.4, lines 515-523): check a
batch of evidence rows together with the evidence file it joins and merge it, renewing the registry's provenance
record, or refuse and write nothing. ``survey-rows <project> --draft-exceptions`` prints a first exceptions file for a
legacy study (4.1, lines 364-365) and writes nothing.

The merge, in order, everything before anything is written:

1. the batch: a regular file inside the study's folder (rule 1.6), with exactly the evidence columns, not empty;
2. the merged file: the evidence file's bytes as they are, the batch's rows appended after them in batch order
   ("nothing is appended unless every row passes"); existing rows are never rewritten;
3. every check of 4.1, 4.3 and 4.8 over the merged file, "checked in full, together with the file it joins"; no
   legacy exception covers a batch row; a merge into a ``plugin`` format is refused;
4. the registry must be built (4.6: its record is there and its inputs match), and a build over the merged file
   must give the registry's present rows; otherwise "the registry must be built first" (this also finds a registry
   edited by hand);
5. the targets (the evidence file and the registry's record) must be allowed places (``check_output_target``);
6. the evidence file is written, then the registry's renewed record, last (``write_all``).

Exit 0 when merged (or the draft printed), 1 when refused, 2 on a usage error. Not a gated stage (6.1).
"""
from __future__ import annotations

import csv
import io
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from survey_core import (  # noqa: E402
    Finding, SurveyUsageError, file_identity, parse_args, print_findings, q, read_capped, reason, resolve_path, safe,
    usage_exit,
)
from survey_evidence import COLUMNS, REGISTRY_COLUMNS, check_row_files, current_breaches  # noqa: E402
from survey_identity import plan_registry  # noqa: E402
from survey_provenance import (  # noqa: E402
    WriteRefused, check_current, check_output_target, write_all,
)
from survey_spec import load_study  # noqa: E402
from survey_tables import MAX_CSV_BYTES, read_rows, rows_from_bytes  # noqa: E402

PROG = "survey_rows.py"


def refuse(msg: str) -> int:
    print(safe(f"REFUSED: {msg}"))
    return 1


def _norm(path: str) -> str:
    import unicodedata
    return unicodedata.normalize("NFC", path).casefold()


def locate_batch(study, declared: str):
    """The batch path, under rule 1.6 (relative to the study's folder, or ``repo:``-rooted), which must lie inside
    the study's folder and be a regular file other than the evidence file (proposal 1). Returns
    ``(ResolvedPath, findings)``."""
    rp, errors = resolve_path(declared, study.study_rel, study.repo_root, "batch")
    if errors:
        return None, errors
    study_real = os.path.realpath(study.repo_root.joinpath(*study.study_rel.split("/"))) if study.study_rel else ""
    inside_by_path = study.study_rel and _norm(rp.repo_rel).startswith(_norm(study.study_rel) + "/")
    inside_by_real = study_real and os.path.commonpath([rp.real, study_real]) == study_real and rp.real != study_real
    if not (inside_by_path and inside_by_real):
        return None, [Finding("batch-place", rp.repo_rel, "a batch lies inside the study's folder (contract silent "
                              "on where a batch is; refused elsewhere)")]
    ev = study.paths["/evidence/file"]
    if os.path.exists(rp.real) and os.path.exists(ev.real) and file_identity(rp.real) == file_identity(ev.real):
        return None, [Finding("batch-place", rp.repo_rel, "the batch is the evidence file itself")]
    return rp, []


def merged_bytes(existing: bytes | None, batch_rows: list) -> bytes:
    """The evidence file's bytes as they are, then the batch's rows in batch order, written as CSV with the line
    ending the file already uses (LF unless it uses CRLF). Without an evidence file yet (a draft), the header first.
    A file whose last line has no line ending gets one before the first appended row."""
    text = existing.decode("utf-8") if existing is not None else ""
    ending = "\r\n" if "\r\n" in text else "\n"
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator=ending)
    if existing is None:
        writer.writerow(COLUMNS)
    for r in batch_rows:
        writer.writerow([r[c] for c in COLUMNS])
    head = text if (text == "" or text.endswith(("\n", "\r"))) else text + ending
    return (head + buf.getvalue()).encode("utf-8")


def merge(root: Path, project: str, batch_arg: str) -> int:
    study = load_study(project, root)
    if study.spec is None or not study.ok:
        print_findings(study.findings)
        return refuse(f"{study.spec_rel} is malformed; nothing was merged")
    spec = study.spec
    if spec["evidence"]["format"] == "plugin":
        return refuse("merging into a plugin format is the project's own write path and is refused (4.1, line 325)")
    ev = study.paths["/evidence/file"]

    rp, errors = locate_batch(study, batch_arg)
    if errors:
        print_findings(errors)
        return refuse("the batch cannot be read; nothing was merged")
    try:
        batch_data = read_capped(Path(rp.real), MAX_CSV_BYTES)
    except OSError as exc:
        return refuse(f"the batch {q(rp.repo_rel)} cannot be read: {reason(exc)}; nothing was merged")
    if batch_data is None:
        return refuse(f"the batch {q(rp.repo_rel)} is larger than {MAX_CSV_BYTES} bytes; nothing was merged")
    batch, _digest = rows_from_bytes(batch_data, rp.repo_rel, COLUMNS, "columns")
    if batch.findings:
        print_findings(batch.findings)
        return refuse("the batch does not have exactly the evidence columns, in order (4.1, line 322); nothing was "
                      "merged")
    if not batch.rows:
        print_findings([Finding("batch-empty", rp.repo_rel, "the batch has no rows")])
        return refuse("an empty batch merges nothing (contract silent; refused)")

    existing = None
    if os.path.lexists(ev.real):
        try:
            existing = read_capped(Path(ev.real), MAX_CSV_BYTES)
        except OSError as exc:
            return refuse(f"the evidence file cannot be read: {reason(exc)}; nothing was merged")
        if existing is None:
            return refuse(f"the evidence file is larger than {MAX_CSV_BYTES} bytes; nothing was merged")
    before, _d = rows_from_bytes(existing, ev.repo_rel, COLUMNS, "columns") if existing is not None else (None, None)
    if before is not None and before.findings:
        print_findings(before.findings)
        return refuse("the evidence file is malformed; nothing was merged")
    data = merged_bytes(existing, [r for _n, r in batch.rows])
    if len(data) > MAX_CSV_BYTES:
        return refuse(f"the merged file would be larger than {MAX_CSV_BYTES} bytes; nothing was merged")
    merged, _d = rows_from_bytes(data, ev.repo_rel, COLUMNS, "columns")
    first_batch = len(before.rows) if before is not None else 0
    if merged.findings or len(merged.rows) != first_batch + len(batch.rows):
        print_findings(merged.findings)
        return refuse("the merged file does not read back as the file and the batch; nothing was merged")

    report = check_row_files(study, merged, first_batch)
    if report.findings:
        for f in report.reported:
            print(f.line("REPORTED"))
        print_findings(report.findings)
        return refuse(f"the batch, checked together with the file it joins, has {len(report.findings)} error(s); "
                      "nothing was appended (4.1, line 323)")

    reg = study.paths["/identity/registry"]
    plan = plan_registry(study, data)
    current = check_current(root, plan.record_rel or (reg.repo_rel + ".provenance.json"),
                            expect_tool="survey-registry", expect_schema_version=spec["schema_version"])
    if not current.built:
        for why in current.reasons:
            print(safe(f"note: {why}"))
        return refuse("the registry is not built: build it first with survey-registry (4.4, line 516); nothing was "
                      "merged")
    if plan.findings:
        print_findings(plan.findings)
        return refuse(f"a build over the merged file could not be worked out ({plan.refusal}); nothing was merged")
    present = read_rows(Path(reg.real), reg.repo_rel, REGISTRY_COLUMNS, "registry-columns")
    if present.findings or [r for _n, r in present.rows] != plan.rows:
        print_findings(present.findings)
        return refuse("a build over the merged file would change the registry's rows (the overrides, the attribution "
                      "file, the batch's persons, or the registry itself differ from the last build): build the "
                      "registry first with survey-registry (4.4, lines 518-521); nothing was merged")

    try:
        check_output_target(study, ev.repo_rel, own_pointer="/evidence/file")
        check_output_target(study, plan.record_rel)
    except WriteRefused as exc:
        return refuse(f"{reason(exc)}; nothing was merged")
    try:
        # The evidence file first, the registry's renewed record last (4.4, lines 521-523). No state an interruption
        # leaves reads as built wrongly. Interrupted after the evidence file was replaced and before the record: the
        # old record names the evidence file's old hash, which no longer matches, so the registry reads as not built
        # until survey-registry runs again; it is never wrongly current. Interrupted before the first replace, or
        # refused at either write's last check (write_all checks both again before either replace): nothing changed.
        write_all(root, [(ev.repo_rel, data), (plan.record_rel, plan.record)])
    except WriteRefused as exc:
        return refuse(f"{reason(exc)}; nothing was merged")
    except OSError as exc:
        return refuse(f"{reason(exc)}; the write did not complete")
    print(safe(f"merged: {len(batch.rows)} row(s) from {rp.repo_rel} into {ev.repo_rel} "
               f"({len(merged.rows)} row(s) now)"))
    print(safe(f"renewed: {plan.record_rel}"))
    return 0


def draft_exceptions(root: Path, project: str) -> int:
    """A first exceptions file "from the current breaches for a person to review; it never adds to an existing one"
    (4.1, lines 364-365). It is printed, not written: the text names no place for a draft, and the exceptions file
    itself is covered by a gate, so it is the person who saves it there (proposal)."""
    study = load_study(project, root)
    if study.spec is None or not study.ok:
        print_findings(study.findings)
        return refuse(f"{study.spec_rel} is malformed")
    spec = study.spec
    if spec["status"] != "legacy" or "legacy_exceptions" not in spec["evidence"]:
        return refuse("a first exceptions file is for a legacy study that declares evidence.legacy_exceptions (4.1, "
                      "line 363)")
    if spec["evidence"]["format"] == "plugin":
        return refuse("evidence in a plugin format is not read in this version")
    exc = study.paths["/evidence/legacy_exceptions"]
    if os.path.lexists(exc.real):
        return refuse(f"{q(exc.repo_rel)} already exists; the tool never adds to an existing one (4.1, line 365)")
    breaches, stops = current_breaches(study)
    if stops:
        print_findings(stops)
        return refuse("no first exceptions file can be written while these breaches stand")
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(("id", "rule"))
    for row in breaches:
        writer.writerow(row)
    for line in buf.getvalue().splitlines():
        print(safe(line))
    print(safe(f"# {len(breaches)} breach(es); a draft for a person to review and save as {exc.repo_rel}; "
               "nothing was written"), file=sys.stderr)
    return 0


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    drafting = "--draft-exceptions" in args
    args = [a for a in args if a != "--draft-exceptions"]
    try:
        root, project, extra = parse_args(args, PROG, () if drafting else ("batch",))
        return draft_exceptions(root, project) if drafting else merge(root, project, extra[0])
    except SurveyUsageError as exc:
        return usage_exit(exc)


if __name__ == "__main__":
    sys.exit(main())
