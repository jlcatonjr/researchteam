"""``survey-registry <project> [--candidates]`` (contract section 7, line 928; 4.4): build the identity registry,
applying the recorded overrides; or, with ``--candidates``, list candidate matches for a person to review.

Building writes the registry (``identity.registry``) and then its provenance record (4.6), last, beside it (4.4,
lines 521-523); no state an interruption leaves reads as built wrongly (see ``build``). Neither target may be a
reserved place or a file the specification declares (``check_output_target``). It refuses, and writes
nothing, when the specification is malformed, a source file is malformed, an override row breaks a rule of 4.4, or
the study needs what this version does not load (a vantage module, a plugin evidence reader). Listing candidates
writes nothing at all: a candidate is never a link, and the overrides file is the project's (rule 1.3).

Exit 0 when built (or unchanged) or listed, 1 when refused, 2 on a usage error. Not a gated stage (6.1).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from survey_core import (  # noqa: E402
    SurveyUsageError, parse_args, print_findings, read_capped, reason, safe, sha256_bytes, usage_exit,
)
from survey_evidence import read_exceptions_hashed  # noqa: E402
from survey_identity import (  # noqa: E402
    build_rows, candidates, identity_refusals, project_persons, read_overrides, read_stop_words, registry_bytes,
    unsafe_values,
)
from survey_provenance import (  # noqa: E402
    WriteRefused, check_output_target, make_record, record_bytes, record_rel, write_all,
)
from survey_spec import load_study  # noqa: E402

PROG = "survey_registry.py"
TOOL = "survey-registry"


def refuse(msg: str) -> int:
    print(safe(f"REFUSED: {msg}"))
    return 1


def prepare(root: Path, project: str):
    """Everything a build needs, worked out before anything is written. Returns ``(study, persons, overrides,
    findings)``."""
    study = load_study(project, root)
    if study.spec is None or not study.ok:
        return study, None, None, list(study.findings)
    findings = identity_refusals(study)
    if findings:
        return study, None, None, findings
    persons = project_persons(study)
    overrides = read_overrides(study, persons.persons)
    return study, persons, overrides, persons.findings + overrides.findings


def build(root: Path, project: str) -> int:
    study, persons, overrides, findings = prepare(root, project)
    if findings:
        print_findings(findings)
        return refuse(f"{study.spec_rel}: the registry was not built; nothing was written")
    rp = study.paths["/identity/registry"]
    rel, rec_rel = rp.repo_rel, record_rel(rp.repo_rel)
    listed, exc_findings, exc_digest = read_exceptions_hashed(study)
    if exc_findings:
        print_findings(exc_findings)
        return refuse(f"{study.spec_rel}: the evidence's exceptions file is malformed; nothing was written")
    try:
        check_output_target(study, rel, own_pointer="/identity/registry")
        check_output_target(study, rec_rel)
    except WriteRefused as exc:
        return refuse(f"{reason(exc)}; nothing was written")
    rows = build_rows(persons.persons, overrides)
    unsafe = unsafe_values(rows, rel)
    if unsafe:
        print_findings(unsafe)
        return refuse(f"{study.spec_rel}: the registry was not built; nothing was written")
    data = registry_bytes(rows)
    inputs = [(study.spec_rel, sha256_bytes(study.spec_bytes)), *persons.inputs, *overrides.inputs]
    if exc_digest is not None:
        inputs.append((study.paths["/evidence/legacy_exceptions"].repo_rel, exc_digest))
    # The registry rests on the evidence file, so it records how many exceptions that file is read with (4.1,
    # line 366). The build applies no row rule; the count is the exceptions file's, as every later stage reads it.
    record = record_bytes(make_record(study, rel, TOOL, inputs, gates={}, plugins=[],
                                      legacy_exceptions=len(listed)))
    try:
        unchanged = all(_same(root, r, b) for r, b in ((rel, data), (rec_rel, record)))
        if not unchanged:
            # The registry first, its record last (4.4, lines 521-523). No state between them reads as built wrongly.
            # Interrupted after the registry was replaced and before the record: the old record (if any) lists the
            # inputs of the old build, with a declared input that was absent recorded as absent. If no input changed,
            # the new registry is the old one, byte for byte (the build is deterministic), so the old record is
            # still true. If an input changed, appeared or went, the old record no longer matches it, and the
            # registry reads as not built. A refusal at either write's last check comes before both replaces
            # (write_all), so nothing changes at all.
            write_all(root, [(rel, data), (rec_rel, record)])
    except WriteRefused as exc:
        return refuse(f"{reason(exc)}; nothing was written")
    except OSError as exc:
        return refuse(f"{reason(exc)}; the write did not complete")
    state = "unchanged" if unchanged else "wrote"
    merged = sum(1 for r in rows if r["merged_from"])
    linked = sum(1 for r in rows if r["identity_id"])
    print(safe(f"{state}: {rel} ({len(rows)} person(s); {linked} linked; {merged} with merges)"))
    print(safe(f"{state}: {rec_rel}"))
    return 0


def _same(root: Path, rel: str, data: bytes) -> bool:
    """Whether *rel* already holds exactly *data* (read without following a link, and capped)."""
    path = root / rel
    if not os.path.lexists(path):
        return False
    try:
        return read_capped(path, len(data)) == data
    except OSError:
        return False


def list_candidates(root: Path, project: str) -> int:
    study, persons, overrides, findings = prepare(root, project)
    stop_words, sw_findings = (read_stop_words(study) if study.spec is not None and study.ok else (set(), []))
    findings += sw_findings
    if findings:
        print_findings(findings)
        return refuse(f"{study.spec_rel}: candidates were not listed")
    names = {p: p for p in persons.persons}  # the only names the project's own rows carry (4.4, lines 513-514)
    found = candidates(persons.persons, names, stop_words, overrides)
    for c in found.shown:
        print(safe(f"candidate {c.kind}: {c.person_id} ~ {c.other_id}"))
    bound = "at least " if found.more_is_lower_bound else ""
    print(f"candidates: {len(found.shown)} undecided shown; {bound}{found.decided} already decided in the overrides "
          "file and not listed. A candidate is never a link: a person decides each in the overrides file (link, merge "
          "or distinct), with a reason.")
    if found.more:
        print(f"candidates not shown: {'at least ' if found.more_is_lower_bound else ''}{found.more} more, in the "
              "same order (the listing shows the first MAX_CANDIDATES)")
    return 0


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    listing = "--candidates" in args
    args = [a for a in args if a != "--candidates"]
    try:
        root, project, _ = parse_args(args, PROG)
    except SurveyUsageError as exc:
        return usage_exit(exc)
    try:
        return list_candidates(root, project) if listing else build(root, project)
    except SurveyUsageError as exc:
        return usage_exit(exc)


if __name__ == "__main__":
    sys.exit(main())
