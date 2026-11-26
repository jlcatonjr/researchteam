"""``survey-frame <project> <final file> --out <frame> --passages <path>`` and, to record a change,
``--change-id <id> --date <date> --reason <text> --results-seen yes|no`` (contract section 7, line 935; 4.7, 4.4,
4.5): write the frame of a passage or work study, its passage list and, where the study declares ``not-on-question``,
its dropped list, each with a provenance record beside it.

- It refuses in an author study (4.7, line 580), and where a bucketer is a plug-in (line 639, open point 6), the
  identity source is a vantage module, or the evidence is in a plug-in format (code this version does not load).
- ``--out`` takes the frame's full path, which ends in ``.csv``; the dropped list is that path with ``.csv`` replaced
  by ``.dropped.csv`` (4.7, line 643; operator ruling A, "Replace .csv"). With the rule declared it is written even
  when nothing is dropped (its header only); without the rule, a dropped list at that path is refused.
- A merged id counts as the person it was merged into, through the overrides file's recorded merges, as in the
  rollup (operator ruling D, "Read through the registry").
- The final file must be a current ``survey-finalize`` output and exactly what finalising gives from the study's
  inputs (4.7, line 653; the rollup's checks, shared through ``load_final``).
- Every cell is checked before anything is written (lines 651-653); on any breach nothing is written.
- The frame-change log (4.4, lines 461-476) must end with the entry for the frame about to be written. Without the
  change arguments, where it does not, nothing is written and the entry the log needs is printed. With them, the
  entry is appended in the same guarded write as the frame (operator rulings B and B2): the log grows by one line,
  has no record of its own, and every record lists it as it stands after the append. With the change arguments and
  an unchanged frame, no entry is written and it says so.
- Since the log's last entry names the frame being written, the command replaces its own earlier frame, passage list
  and dropped list at the same paths (operator ruling B3); a file with no record of this tool's beside it is
  refused. Every other command keeps refusing to write over an output with other bytes (D2, D5).
- Post-steps (4.5) are not run by this version: a study that declares any is refused once each step file's path and
  the gate that covers it have been checked (a blocking gate not cleared refuses, rule 1.7 and 6.1).
- The records list gates S5 and S6 (lines 569, 653), every file read, and the legacy exceptions. An existing output
  is never appended to: identical bytes are "unchanged", anything else is refused.

Exit 0 when written (or unchanged), 1 when refused, 2 on a usage error.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from survey_cells import DROPPED_COLUMNS, PASSAGE_COLUMNS, build, drops_not_on_question, quoted_csv  # noqa: E402
from survey_changelog import check_frame, frame_sha256, needed_entry, read_log  # noqa: E402
from survey_core import (  # noqa: E402
    Finding, SurveyUsageError, parse_args, print_findings, q, read_capped, reason, safe, sha256_bytes, usage_exit,
)
from survey_evidence import COLUMNS as EVIDENCE_COLUMNS  # noqa: E402
from survey_final import locate_in_study, merged_persons  # noqa: E402
from survey_finalize import load_final, overrides_bytes, write_outputs  # noqa: E402
from survey_gates import REFUSES, require_gate  # noqa: E402
from survey_identity import identity_refusals  # noqa: E402
from survey_provenance import ABSENT, MAX_INPUT_BYTES, gate_entries, make_record, record_bytes  # noqa: E402
from survey_spec import load_study  # noqa: E402
from survey_tables import check_table_bytes, rows_from_bytes  # noqa: E402

PROG = "survey_frame.py"
TOOL = "survey-frame"
#: The gates every output's record lists: the frame's by line 653; the passage list and the dropped list are outputs
#: of the same stage, and a record lists "each gate the stage depends on" (line 569).
GATES = ("S5", "S6")
CHANGE_FLAGS = ("--change-id", "--date", "--reason", "--results-seen")


def refuse(msg: str) -> int:
    print(safe(f"REFUSED: {msg}"))
    return 1


def parse(argv: list) -> tuple:
    """``(root, project, final file, frame, passages, change)``, where *change* is None or the author's facts for a
    frame-change entry: all four change arguments, or none (operator ruling B)."""
    args = list(argv)
    usage = (f"usage: {PROG} [--root DIR] <project> <final file> --out <frame> --passages <path> "
             "[--change-id <id> --date <date> --reason <text> --results-seen yes|no]")
    found = {}
    for flag in ("--out", "--passages", *CHANGE_FLAGS):
        if flag in CHANGE_FLAGS and flag not in args:
            continue
        if args.count(flag) != 1 or args.index(flag) == len(args) - 1:
            raise SurveyUsageError(usage)
        i = args.index(flag)
        found[flag] = args[i + 1]
        del args[i:i + 2]
    given = [f for f in CHANGE_FLAGS if f in found]
    if given and len(given) != len(CHANGE_FLAGS):
        raise SurveyUsageError(f"{usage}\nthe change arguments go together: {', '.join(CHANGE_FLAGS)}")
    change = None
    if given:
        if found["--results-seen"] not in ("yes", "no"):
            raise SurveyUsageError(f"{usage}\n--results-seen is yes or no")
        change = {"id": found["--change-id"], "date": found["--date"], "reason": found["--reason"],
                  "results_seen": found["--results-seen"] == "yes"}
    root, project, extra = parse_args(args, PROG, ("final file",))
    return root, project, extra[0], found["--out"], found["--passages"], change


def dropped_path(frame_rel: str) -> str | None:
    """The dropped list's path: the frame's with ``.csv`` replaced by ``.dropped.csv`` (ruling A); None when the
    frame's path does not end in ``.csv``."""
    return frame_rel[:-len(".csv")] + ".dropped.csv" if frame_rel.endswith(".csv") else None


def unsupported(study) -> list:
    """What this version does not load in a frame, each refused (fail closed)."""
    out = list(identity_refusals(study))
    for i, a in enumerate(study.spec["attributes"]):
        if a["bucketer"]["kind"] == "plugin":
            out.append(Finding("frame-plugin-bucketer", f"{study.spec_rel}#/attributes/{i}/bucketer",
                               f"attribute {q(a['key'])} has a plug-in bucketer, which is refused in a frame, and "
                               "nothing is written (4.7, line 639; open point 6)"))
    return out


def check_post_steps(study) -> list:
    """Post-steps (4.5) are not run by this version. Each declared step is checked in two passes, in this order:

    1. its path, for every step: rule 1.6, inside the study's folder, no symbolic link on its way (``locate_in_study``)
       and a regular file;
    2. then, for each step whose path passed, every gate that covers it (``require_gate``: a blocking gate not
       cleared, or a gate that is not declared, refuses). A step whose path fails is not passed to a gate: a gate
       clears the file at a place, and a place that is refused has nothing to clear.

    Where every step passes both, the finding says that running post-steps is not yet available. Returns the
    findings; any finding refuses the build."""
    findings, placed = [], []
    steps = [(ptr, rp) for ptr, rp in study.paths.items() if ptr.startswith("/frame_rules/post_steps/")]
    for ptr, rp in steps:
        located, errors = locate_in_study(study, rp.declared, "post-step")
        if errors:
            findings += errors
        elif not os.path.isfile(located.real):
            findings.append(Finding("post-step-file", f"{study.spec_rel}#{ptr}",
                                    f"{q(rp.declared)} is not a regular file"))
        else:
            placed.append((ptr, rp))
    for ptr, rp in placed:
        where = f"{study.spec_rel}#{ptr}"
        gates = [g for g in study.spec["signoffs"]["gates"] if rp.identity in study.covered(g)]
        if not gates:
            findings.append(Finding("post-step-uncovered", where, f"{q(rp.declared)} is covered by no gate (4.5)"))
            continue
        for gate in gates:
            decision, record, _st = require_gate(study, gate)
            if decision == REFUSES:
                findings.append(Finding("post-step-gate", where, f"gate {gate} covers {q(rp.declared)} and is "
                                        f"{record['state']} ({record.get('enforce') or 'not declared'}); the frame "
                                        "build refuses to run the step (4.5, lines 542-544; 6.1)"))
    if steps and not findings:
        findings.append(Finding("post-steps-unavailable", f"{study.spec_rel}#/frame_rules/post_steps",
                                "the study declares post-steps and their gates allow them, but running post-steps is "
                                "not yet available in this version; no frame is written"))
    return findings


def main(argv=None) -> int:
    try:
        root, project, final_arg, out_arg, passages_arg, change = parse(sys.argv[1:] if argv is None else argv)
        study = load_study(project, root)
    except SurveyUsageError as exc:
        return usage_exit(exc)
    if study.spec is None or not study.ok:
        print_findings(study.findings)
        return refuse(f"{study.spec_rel} is malformed; nothing was written")
    spec = study.spec
    if spec["unit"]["kind"] not in ("passage", "work"):
        return refuse("an author study's frame is not part of version 1, and the frame tool refuses to run in one "
                      "(4.7, lines 579-580; open point 2)")
    stops = unsupported(study)
    if stops:
        print_findings(stops)
        return refuse("the frame needs what this version does not load; nothing was written")
    steps = check_post_steps(study)
    if steps:
        print_findings(steps)
        return refuse("the study's post-steps cannot be run (4.5); nothing was written")
    out, errors = locate_in_study(study, out_arg, "output")
    passages, p_errors = locate_in_study(study, passages_arg, "output")
    if errors or p_errors:
        print_findings(errors + p_errors)
        return refuse("a path is not allowed; nothing was written")
    dropped_rel = dropped_path(out.repo_rel)
    if dropped_rel is None:
        return refuse(f"{q(out.repo_rel)} does not end in .csv: the dropped list is the frame's path with .csv "
                      "replaced by .dropped.csv (4.7, line 643; ruling A); nothing was written")
    rule = drops_not_on_question(spec)
    if rule is None and os.path.lexists(root.joinpath(*dropped_rel.split("/"))):
        return refuse(f"{q(dropped_rel)} is there, but the study does not declare not-on-question, so this build "
                      "writes no dropped list, and one from an earlier build would stand beside a frame it does not "
                      "describe (ruling A); remove it first; nothing was written")
    outs = [out.repo_rel, passages.repo_rel] + ([dropped_rel] if rule is not None else [])
    loaded, code = load_final(root, study, final_arg, outs)
    if loaded is None:
        return code
    ev_rel = study.paths["/evidence/file"].repo_rel
    evidence, _sha = rows_from_bytes(loaded.data.get(ev_rel, b""), ev_rel, EVIDENCE_COLUMNS, "columns")
    if evidence.findings:
        print_findings(evidence.findings)
        return refuse("the evidence file cannot be read; nothing was written")
    evidence = [r for _n, r in evidence.rows]
    tables, table_findings = load_tables(study, loaded.data)
    if table_findings:
        print_findings(table_findings)
        return refuse("a bucket table cannot be read; nothing was written")
    persons = merged_persons(study, overrides_bytes(study, loaded))
    built = build(spec, loaded.rows, loaded.attribution, evidence, tables, persons)
    if built.findings:
        print_findings(built.findings)
        return refuse("a cell breaks the frame's checks (4.7, lines 651-652); nothing was written")
    frame = quoted_csv(built.columns, built.rows)
    passage_bytes = quoted_csv(PASSAGE_COLUMNS, built.passages)
    # The frame-change log: read, hashed and guarded like every input; the frame must be its last entry's.
    log_rp = study.paths["/frame_rules/change_log"]
    log_path = root.joinpath(*log_rp.repo_rel.split("/"))
    try:
        log_data = read_capped(log_path, MAX_INPUT_BYTES) if os.path.lexists(log_path) else None
    except OSError as exc:
        return refuse(f"{q(log_rp.repo_rel)} cannot be read: {reason(exc)}; nothing was written")
    if log_data is None and os.path.lexists(log_path):
        return refuse(f"{q(log_rp.repo_rel)} is larger than {MAX_INPUT_BYTES} bytes; nothing was written")
    entries, log_findings = read_log(log_data, log_rp.repo_rel) if log_data is not None else ([], [])
    if log_findings:
        print_findings(log_findings)
        return refuse("the frame-change log is malformed (4.4, lines 461-473); correct it first; nothing was written")
    sha = frame_sha256(frame)
    mismatch = check_frame(entries, log_rp.repo_rel, sha, built.units)
    if mismatch and change is None:
        print_findings(mismatch)
        print(safe("the entry the log needs (id, date, reason and results_seen are yours to give): "
                   f"{needed_entry(entries, sha, built.units)}"))
        return refuse("the frame-change log does not end with this frame's entry (4.4, lines 475-476); nothing was "
                      "written")
    new_log = None
    if mismatch:
        new_log, code = appended_log(entries, log_data, log_rp.repo_rel, sha, built.units, change)
        if new_log is None:
            return code
    elif change is not None:
        print(safe(f"no entry: the frame is the log's last entry ({q(entries[-1]['id'])}); the log has one entry per "
                   "change to the frame (4.4, line 461), so the change arguments were not used"))
    # The records list the log as it stands after this run (ruling B2: the log has no record of its own); the guard
    # holds the bytes read, so a log changed on disk since then refuses the whole write.
    after = new_log if new_log is not None else log_data
    inputs = list(loaded.inputs) + [(log_rp.repo_rel, sha256_bytes(after) if after is not None else ABSENT)]
    guards = dict(loaded.guards)
    guards[log_rp.repo_rel] = sha256_bytes(log_data) if log_data is not None else None
    gates = gate_entries(study, GATES)
    outputs = [(out.repo_rel, frame), (passages.repo_rel, passage_bytes)]
    if rule is not None:
        outputs.append((dropped_rel, quoted_csv(DROPPED_COLUMNS, built.dropped)))
    items = [(rel, data, record_bytes(make_record(study, rel, TOOL, inputs, gates, plugins=[],
                                                  legacy_exceptions=loaded.exceptions))) for rel, data in outputs]
    # The log's last entry names this frame (checked above, after this run's append if any), so the command may
    # replace its own earlier outputs at these paths (ruling B3); a foreign file or an output with no record of this
    # tool's is still refused.
    unrecorded = (log_rp.repo_rel, new_log, "/frame_rules/change_log") if new_log is not None else None
    code = write_outputs(root, study, items, guards, TOOL, replace=True, unrecorded=unrecorded)
    if code == 0:
        dropped_note = f"; dropped: {len(built.dropped)} cell(s)" if rule is not None else ""
        print(safe(f"frame: {len(built.rows)} cell(s); passage list: {len(built.passages)} row(s){dropped_note}; "
                   f"frame_sha256 {sha}"))
    return code


def appended_log(entries: list, log_data: bytes | None, rel: str, sha: str, units: list, change: dict) -> tuple:
    """The change arguments were given and the frame changed (operator ruling B2): ``(the log's new bytes, 0)`` or
    ``(None, exit code)`` with the refusal printed.

    - The author's facts are checked: an ``id`` not empty and not already in the log (4.4, line 474); a ``date`` and a
      ``reason`` not empty (rule 1.5: the tool never takes the date from the clock). The tool supplies
      ``frame_sha256``, ``n_units``, ``added``, ``removed`` and ``units``, all from the frame.
    - The log grows by exactly one line at its end: its bytes as read, then the entry and a line feed. A log whose
      last line does not end in a line feed is refused (JSON Lines; the contract does not say how to join a line to
      one), so nothing in the log as read ever changes.
    - A log that does not exist yet is created: section 3 lets ``change_log`` be absent "because a stage writes them"
      (line 218)."""
    problems = []
    if change["id"] == "" or change["id"] in {e["id"] for e in entries}:
        problems.append(Finding("change-log-id", rel, f"--change-id {q(change['id'])} is empty or already in the log; "
                                "an id is what a report cites (4.4, line 474)"))
    for key in ("date", "reason"):
        if change[key] == "":
            problems.append(Finding("change-log-fact", rel, f"--{key} is empty; the author gives it (rule 1.5)"))
    if log_data and not log_data.endswith(b"\n"):
        problems.append(Finding("change-log-end", rel, "the log's last line does not end in a line feed; an entry is "
                                "appended only after a complete line (correct the log first)"))
    if problems:
        print_findings(problems)
        return None, refuse("the frame-change entry cannot be appended; nothing was written")
    entry = json.loads(needed_entry(entries, sha, units))
    entry.update(change)
    new = (log_data or b"") + json.dumps(entry, ensure_ascii=True).encode("utf-8") + b"\n"
    grown, findings = read_log(new, rel)
    findings += [] if findings else check_frame(grown, rel, sha, units)
    if findings or len(grown) != len(entries) + 1:
        print_findings(findings)
        return None, refuse("the entry does not make a well-formed log for this frame; nothing was written")
    return new, 0


def load_tables(study, data: dict) -> tuple:
    """Each non-period attribute's bucket table, checked (4.8), parsed from the bytes ``load_final`` hashed (*data*,
    by repository-relative path): ``({key: rows}, findings)``."""
    tables, findings = {}, []
    for i, a in enumerate(study.spec["attributes"]):
        if a["kind"] == "period":
            continue
        rp = study.paths.get(f"/attributes/{i}/bucketer/table")
        if rp is None or rp.repo_rel not in data:
            findings.append(Finding("frame-table", f"{study.spec_rel}#/attributes/{i}/bucketer/table",
                                    f"attribute {q(a['key'])} has no bucket table to read"))
            continue
        allowed = a.get("flags") if a["kind"] == "flags" else a.get("levels")
        rows, errs = check_table_bytes(data[rp.repo_rel], rp.repo_rel, allowed)
        findings += errs
        tables[a["key"]] = rows
    return tables, findings


if __name__ == "__main__":
    sys.exit(main())
