"""``survey-frame <project> <final file> --out <frame> --passages <path>`` (contract section 7, line 935; 4.7, 4.4,
4.5): write the frame of a passage or work study and its passage list, each with a provenance record beside it.

- It refuses in an author study (4.7, line 580), and where a bucketer is a plug-in (line 639, open point 6), the
  identity source is a vantage module, or the evidence is in a plug-in format (code this version does not load).
- The final file must be a current ``survey-finalize`` output and exactly what finalising gives from the study's
  inputs (4.7, line 653; the rollup's checks, shared through ``load_final``).
- Every cell is checked before anything is written (lines 651-653); on any breach nothing is written.
- The frame-change log (4.4, lines 461-476) must end with the entry for the frame about to be written; where it does
  not, nothing is written and the entry the log needs is printed, its ``id``, ``date``, ``reason`` and
  ``results_seen`` left for the author.
- Post-steps (4.5) are not run by this version: a study that declares any is refused once each step file's path and
  the gate that covers it have been checked (a blocking gate not cleared refuses, rule 1.7 and 6.1).
- The rule ``not-on-question`` (lines 641-644) is not yet applied: the dropped list's file name is an open point
  (the check table), so a study that declares the rule is refused.
- The records list gates S5 and S6 (line 653), every file read, and the legacy exceptions. An existing output is
  never appended to: identical bytes are "unchanged", anything else is refused.

Exit 0 when written (or unchanged), 1 when refused, 2 on a usage error.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from survey_cells import PASSAGE_COLUMNS, build, drops_not_on_question, quoted_csv  # noqa: E402
from survey_changelog import check_frame, frame_sha256, needed_entry, read_log  # noqa: E402
from survey_core import (  # noqa: E402
    Finding, SurveyUsageError, parse_args, print_findings, q, read_capped, reason, safe, sha256_bytes, usage_exit,
)
from survey_evidence import COLUMNS as EVIDENCE_COLUMNS, REGISTRY_COLUMNS  # noqa: E402
from survey_final import locate_in_study  # noqa: E402
from survey_finalize import load_final, write_outputs  # noqa: E402
from survey_gates import REFUSES, require_gate  # noqa: E402
from survey_identity import identity_refusals  # noqa: E402
from survey_provenance import ABSENT, MAX_INPUT_BYTES, gate_entries, make_record, record_bytes  # noqa: E402
from survey_spec import load_study  # noqa: E402
from survey_tables import check_table, rows_from_bytes  # noqa: E402

PROG = "survey_frame.py"
TOOL = "survey-frame"
#: The gates the frame's record lists (4.7, line 653); the passage list, an output of the same stage, lists them too.
GATES = ("S5", "S6")


def refuse(msg: str) -> int:
    print(safe(f"REFUSED: {msg}"))
    return 1


def parse(argv: list) -> tuple:
    args = list(argv)
    usage = f"usage: {PROG} [--root DIR] <project> <final file> --out <frame> --passages <path>"
    found = {}
    for flag in ("--out", "--passages"):
        if args.count(flag) != 1 or args.index(flag) == len(args) - 1:
            raise SurveyUsageError(usage)
        i = args.index(flag)
        found[flag] = args[i + 1]
        del args[i:i + 2]
    root, project, extra = parse_args(args, PROG, ("final file",))
    return root, project, extra[0], found["--out"], found["--passages"]


def unsupported(study) -> list:
    """What this version does not load or define in a frame, each refused (fail closed)."""
    out = list(identity_refusals(study))
    for i, a in enumerate(study.spec["attributes"]):
        if a["bucketer"]["kind"] == "plugin":
            out.append(Finding("frame-plugin-bucketer", f"{study.spec_rel}#/attributes/{i}/bucketer",
                               f"attribute {q(a['key'])} has a plug-in bucketer, which is refused in a frame, and "
                               "nothing is written (4.7, line 639; open point 6)"))
    rule = drops_not_on_question(study.spec)
    if rule is not None:
        out.append(Finding("frame-dropped-name", f"{study.spec_rel}#/frame_rules/exclude",
                           "the study declares not-on-question, whose dropped list is written to <frame>.dropped.csv "
                           "(4.7, line 643); whether that is the frame's path with .dropped.csv added or with its "
                           "suffix replaced is an open point awaiting the operator's ruling, so no frame is written"))
    return out


def check_post_steps(study) -> list:
    """Post-steps (4.5) are not run by this version. Each declared step is checked first: its path (rule 1.6, inside
    the study's folder, no link, a regular file) and every gate that covers it (``require_gate``: a blocking gate not
    cleared, or a gate that is not declared, refuses). Where all of that passes, the finding says that running
    post-steps is not yet available. Returns the findings; any finding refuses the build."""
    findings = []
    steps = [(ptr, rp) for ptr, rp in study.paths.items() if ptr.startswith("/frame_rules/post_steps/")]
    for ptr, rp in steps:
        where = f"{study.spec_rel}#{ptr}"
        located, errors = locate_in_study(study, rp.declared, "post-step")
        if errors:
            findings += errors
            continue
        real = located.real
        if os.path.islink(real) or not os.path.isfile(real):
            findings.append(Finding("post-step-file", where, f"{q(rp.declared)} is not a regular file"))
            continue
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
        root, project, final_arg, out_arg, passages_arg = parse(sys.argv[1:] if argv is None else argv)
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
        return refuse("the frame needs what this version does not load or define; nothing was written")
    steps = check_post_steps(study)
    if steps:
        print_findings(steps)
        return refuse("the study's post-steps cannot be run (4.5); nothing was written")
    out, errors = locate_in_study(study, out_arg, "output")
    passages, p_errors = locate_in_study(study, passages_arg, "output")
    if errors or p_errors:
        print_findings(errors + p_errors)
        return refuse("a path is not allowed; nothing was written")
    loaded, code = load_final(root, study, final_arg, [out.repo_rel, passages.repo_rel])
    if loaded is None:
        return code
    ev_rel = study.paths["/evidence/file"].repo_rel
    evidence, _sha = rows_from_bytes(loaded.data.get(ev_rel, b""), ev_rel, EVIDENCE_COLUMNS, "columns")
    if evidence.findings:
        print_findings(evidence.findings)
        return refuse("the evidence file cannot be read; nothing was written")
    evidence = [r for _n, r in evidence.rows]
    stops = merged_ids(study, loaded, evidence)
    tables, table_findings = load_tables(study)
    if stops or table_findings:
        print_findings(stops + table_findings)
        return refuse("the frame cannot be built from these inputs; nothing was written")
    built = build(spec, loaded.rows, loaded.attribution, evidence, tables)
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
    sha = frame_sha256(frame)
    log_findings += [] if log_findings else check_frame(entries, log_rp.repo_rel, sha, built.units)
    if log_findings:
        print_findings(log_findings)
        if not read_log_errors(log_findings):
            print(safe(f"the entry the log needs (id, date, reason and results_seen are yours to give): "
                       f"{needed_entry(entries, sha, built.units)}"))
        return refuse("the frame-change log does not end with this frame's entry (4.4, lines 475-476); nothing was "
                      "written")
    inputs = list(loaded.inputs) + [(log_rp.repo_rel, sha256_bytes(log_data) if log_data is not None else ABSENT)]
    guards = dict(loaded.guards)
    guards[log_rp.repo_rel] = sha256_bytes(log_data) if log_data is not None else None
    gates = gate_entries(study, GATES)
    items = []
    for rel, data in ((out.repo_rel, frame), (passages.repo_rel, passage_bytes)):
        items.append((rel, data, record_bytes(make_record(study, rel, TOOL, inputs, gates, plugins=[],
                                                          legacy_exceptions=loaded.exceptions))))
    code = write_outputs(root, study, items, guards, TOOL)
    if code == 0:
        print(safe(f"frame: {len(built.rows)} cell(s); passage list: {len(built.passages)} row(s); frame_sha256 {sha}"))
    return code


def read_log_errors(findings: list) -> bool:
    """Whether the log itself is malformed (then no entry is proposed: the log must be corrected first)."""
    return any(f.rule == "change-log" for f in findings)


def merged_ids(study, loaded, evidence: list) -> list:
    """An open point stops the build: an id the registry lists in a person's ``merged_from`` that the attribution or
    evidence file still names. 4.7 reads "the author's rows" and the cell's ``person_id`` without saying whether a
    merged id is its person (the check table), so such a study is refused, nothing inferred (rule 1.3)."""
    rp = study.paths.get("/identity/registry")
    data = loaded.data.get(rp.repo_rel) if rp is not None else None
    if data is None:
        return []
    reg, _sha = rows_from_bytes(data, rp.repo_rel, REGISTRY_COLUMNS, "registry-columns")
    aliases = {m for _n, r in reg.rows for m in r["merged_from"].split(";") if m != ""}
    named = {a["person_id"] for a in loaded.attribution.values()} | {r["person_id"] for r in evidence}
    hit = sorted(aliases & named)
    if not hit:
        return []
    return [Finding("frame-merged-id", rp.repo_rel, f"the ids {', '.join(map(q, hit))} are merged into another person "
                    "but still named by the attribution or evidence file; whether the frame reads them as that person "
                    "is an open point awaiting the operator's ruling, so no frame is written")]


def load_tables(study) -> tuple:
    """Each non-period attribute's bucket table, checked (4.8): ``({key: rows}, findings)``."""
    tables, findings = {}, []
    for i, a in enumerate(study.spec["attributes"]):
        if a["kind"] == "period":
            continue
        rp = study.paths.get(f"/attributes/{i}/bucketer/table")
        if rp is None or not os.path.lexists(rp.real):
            findings.append(Finding("frame-table", f"{study.spec_rel}#/attributes/{i}/bucketer/table",
                                    f"attribute {q(a['key'])} has no bucket table to read"))
            continue
        allowed = a.get("flags") if a["kind"] == "flags" else a.get("levels")
        rows, errs = check_table(Path(rp.real), rp.repo_rel, allowed)
        findings += errs
        tables[a["key"]] = rows
    return tables, findings


if __name__ == "__main__":
    sys.exit(main())
