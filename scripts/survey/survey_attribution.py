"""The attribution file of a passage or work study (contract 4.3).

Columns: ``unit_id, person_id, author_kind, work, locator, status``, one column per key in
``unit.passage_attributes``, then ``basis, note``. Its errors cannot be listed as legacy exceptions (4.3, lines
432-433). The contract gives these checks no ids; the ids here are the toolkit's own.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from survey_core import Finding, q
from survey_tables import read_rows

BASE = ("unit_id", "person_id", "author_kind", "work", "locator", "status")
TAIL = ("basis", "note")


def columns(spec: dict) -> tuple:
    return BASE + tuple(ls["key"] for ls in spec["unit"].get("passage_attributes", [])) + TAIL


@dataclass
class Attribution:
    """The units as read: ``units[unit_id] = row``, in file order."""

    units: dict = field(default_factory=dict)
    persons: list = field(default_factory=list)  # every non-empty person_id, in file order
    findings: list = field(default_factory=list)


def check_attribution(study, registry_persons: set | None, evidence_persons: set) -> Attribution:
    """Every check of 4.3, in one pass over the file. *registry_persons* are the person ids the registry holds.
    When there is no registry, the person ids of its own sources (this file and the evidence file, 4.4 lines
    509-511) stand in for it, which can only refuse more, never less. A file that is not there is not read: it may
    be absent only in a draft, and section 3's file check reports it otherwise."""
    spec = study.spec
    rp = study.paths.get("/unit/attribution/file")
    out = Attribution()
    if rp is None or not os.path.lexists(rp.real):
        return out
    where = rp.repo_rel
    rows = read_rows(Path(rp.real), where, columns(spec), "attribution-columns")
    out.findings += rows.findings
    if rows.findings:
        return out
    add = lambda rule, n, msg: out.findings.append(Finding(rule, f"{where}:{n}", msg))  # noqa: E731
    att = spec["unit"]["attribution"]
    kinds = ["person", *spec["unit"].get("collective", {}).get("kinds", [])]
    level_sets = {ls["key"]: [lv["code"] for lv in ls["levels"]] for ls in spec["unit"].get("passage_attributes", [])}
    kind_of: dict = {}
    for n, r in rows.rows:
        uid, pid = r["unit_id"], r["person_id"]
        if uid == "":
            add("attribution-unit-empty", n, "an empty unit_id")
        elif uid in out.units:
            add("attribution-unit-duplicate", n, f"unit_id {q(uid)} is repeated")
        else:
            out.units[uid] = r
        if pid == "":
            add("attribution-person-empty", n, "an empty person_id (contract silent; refused)")
        else:
            out.persons.append(pid)
        for col, value in (("unit_id", uid), ("person_id", pid)):
            if "|" in value:
                add("attribution-separator", n, f"a '|' in {col} {q(value)} (4.7)")
        if r["status"] not in att["statuses"]:
            add("attribution-status", n, f"status {q(r['status'])} is not one of {q(att['statuses'])}")
        if r["author_kind"] not in kinds:
            add("attribution-author-kind", n, f"author_kind {q(r['author_kind'])} is not one of {q(kinds)}")
        elif pid:
            kind_of.setdefault(pid, set()).add(r["author_kind"])
        for key, codes in level_sets.items():
            if r[key] == "" or r[key] not in codes:
                add("attribution-passage-attribute", n, f"{key} {q(r[key])} is not one of its level codes {q(codes)}")
    for pid, ks in kind_of.items():
        if len(ks) > 1:
            out.findings.append(Finding("attribution-author-kinds", where,
                                        f"person {q(pid)} has more than one author_kind: {q(sorted(ks))}"))
    persons = registry_persons if registry_persons is not None else set(out.persons) | set(evidence_persons)
    for uid in out.units:
        if uid in persons:
            out.findings.append(Finding("attribution-unit-is-person", where, f"unit_id {q(uid)} is also a person_id "
                                        "the registry holds; a passage would be indistinguishable from a person-level "
                                        "evidence row (4.1)"))
    return out
