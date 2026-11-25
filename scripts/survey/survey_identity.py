"""The identity files (contract 4.4, lines 489-530): the overrides file, the registry build, and candidates.

Rule 1.3 holds throughout: no tool matches a name to an identity. A link or merge exists only because a named
person wrote it in the overrides file, with a reason; this module checks such rows and applies them, and it lists
candidates for a person to review without ever applying one. It never writes the overrides file.

The identity source (5.2, lines 733-735): with ``vantage.module`` null or absent, "identities are the persons the
project's own rows name", and the candidate search "compares those persons with one another". A vantage module is
project code (``identities()``), which this version does not load: a study that declares one is refused.
"""
from __future__ import annotations

import csv
import io
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from survey_attribution import columns as attribution_columns
from survey_core import MAX_JSON_BYTES, Finding, fold, q, read_capped
from survey_evidence import COLUMNS as EVIDENCE_COLUMNS
from survey_evidence import REGISTRY_COLUMNS
from survey_tables import read_rows_hashed

OVERRIDE_COLUMNS = ("alias_id", "target_id", "decision", "decided_by", "reason")
DECISIONS = ("link", "merge", "distinct")
#: The separator of ``merged_from`` (the contract names none; ``;`` as for ``evidence_ids`` and ``new_ids``).
MERGED_SEPARATOR = ";"
KIND_ORDER = ("same-id", "exact", "similar")


@dataclass
class Sources:
    """The project's persons and the files they were read from."""

    persons: list = field(default_factory=list)  # sorted, unique
    inputs: list = field(default_factory=list)  # (repo-relative path, sha256), in reading order
    findings: list = field(default_factory=list)


def identity_refusals(study) -> list:
    """What stops this version from building a registry for the study at all (not implemented, fails closed)."""
    out = []
    vantage = study.spec.get("vantage")
    if vantage and vantage.get("module") is not None:
        out.append(Finding("identity-vantage", f"{study.spec_rel}#/vantage/module", "the identity source is the "
                           "vantage module's identities() (5.2), project code this version does not load; not "
                           "implemented (fails closed)"))
    if study.spec["evidence"]["format"] == "plugin":
        out.append(Finding("evidence-plugin", f"{study.spec_rel}#/evidence/format", "evidence in a plugin format is "
                           "read through its reader plug-in, which this version does not load; not implemented"))
    return out


def project_persons(study) -> Sources:
    """The persons the registry takes (4.4, lines 509-511): every ``person_id`` of the evidence file and, in a
    passage or work study, of the attribution file. A file that is not there (a draft) gives none. An empty
    ``person_id`` is not given (section 4, line 276) and is not a person."""
    out = Sources()
    seen = set()
    sources = [("/evidence/file", EVIDENCE_COLUMNS, "columns")]
    if study.spec["unit"]["kind"] in ("passage", "work"):
        sources.append(("/unit/attribution/file", attribution_columns(study.spec), "attribution-columns"))
    for ptr, cols, rule in sources:
        rp = study.paths.get(ptr)
        if rp is None or not os.path.lexists(rp.real):
            continue
        rows, digest = read_rows_hashed(Path(rp.real), rp.repo_rel, cols, rule)
        out.findings += rows.findings
        if digest is not None:
            out.inputs.append((rp.repo_rel, digest))
        for _n, r in rows.rows:
            if r["person_id"] != "":
                seen.add(r["person_id"])
    out.persons = sorted(seen)
    return out


# --------------------------------------------------------------------------- overrides (4.4, lines 491-506)
@dataclass
class Overrides:
    rows: list = field(default_factory=list)  # (line, row) of the rows that passed
    inputs: list = field(default_factory=list)
    findings: list = field(default_factory=list)

    def pairs(self) -> set:
        """Every pair an override row names, whatever its decision: a candidate is decided only when a row names
        that pair (line 506)."""
        return {frozenset((r["alias_id"], r["target_id"])) for _n, r in self.rows}


def read_overrides(study, persons: list) -> Overrides:
    """Read and check the overrides file. Without a vantage module the identity source holds the project's own
    persons (5.2), so a ``link`` target, a ``merge`` target and a ``distinct`` target are all project persons."""
    out = Overrides()
    rp = study.paths.get("/identity/overrides")
    if rp is None or not os.path.lexists(rp.real):
        return out  # it may be absent: a stage writes it or it starts empty (section 3, line 218)
    rows, digest = read_rows_hashed(Path(rp.real), rp.repo_rel, OVERRIDE_COLUMNS, "overrides-columns")
    out.findings += rows.findings
    if digest is not None:
        out.inputs.append((rp.repo_rel, digest))
    if rows.findings:
        return out
    where = rp.repo_rel
    known = set(persons)
    add = lambda rule, n, msg: out.findings.append(Finding(rule, f"{where}:{n}", msg))  # noqa: E731
    seen_pairs: dict = {}
    binding: dict = {}  # alias -> (line, decision) of its one link or merge
    distinct: list = []
    good = []
    for n, r in rows.rows:
        empty = [c for c in OVERRIDE_COLUMNS if r[c] == ""]
        if empty:
            add("overrides-empty", n, f"every column is required in every row; empty: {', '.join(empty)} (line 492)")
            continue
        alias, target, decision = r["alias_id"], r["target_id"], r["decision"]
        if decision not in DECISIONS:
            add("overrides-decision", n, f"decision {q(decision)} is not one of {', '.join(DECISIONS)} (line 493)")
            continue
        if alias not in known:
            add("overrides-alias", n, f"alias_id {q(alias)} is not a person of the project (contract silent; refused)")
            continue
        if target not in known:
            add("overrides-target", n, f"target_id {q(target)} is not a person of the project, which is the identity "
                "source when no vantage module is declared (5.2)")
            continue
        if decision in ("merge", "distinct") and target == alias:
            add("overrides-self", n, f"a {decision} row whose target_id equals its alias_id (line 503)")
            continue
        key = (frozenset((alias, target)), decision)
        if key in seen_pairs:
            add("overrides-repeat", n, f"the pair {q(alias)}, {q(target)} and decision {decision} are given twice "
                f"(first on line {seen_pairs[key]}); a pair is the same whichever id is written first (line 504)")
            continue
        seen_pairs[key] = n
        if decision in ("link", "merge"):
            if alias in binding:
                add("overrides-second", n, f"alias_id {q(alias)} already has a {binding[alias][1]} row (line "
                    f"{binding[alias][0]}); an alias has at most one link or merge (lines 501-502)")
                continue
            binding[alias] = (n, decision)
        else:
            distinct.append((n, r))
        good.append((n, r))
    bound_pairs = {frozenset((r["alias_id"], r["target_id"])): (n, r["decision"])
                   for n, r in good if r["decision"] in ("link", "merge")}
    for n, r in distinct:
        pair = frozenset((r["alias_id"], r["target_id"]))
        if pair in bound_pairs:
            add("overrides-conflict", n, f"a distinct row for a pair that is also {bound_pairs[pair][1]}ed (line "
                f"{bound_pairs[pair][0]}; lines 502-503)")
    merged_away = {a for a, (_n, d) in binding.items() if d == "merge"}
    linked_to: dict = {}
    for n, r in good:
        if r["decision"] == "merge" and r["target_id"] in merged_away:
            add("overrides-chain", n, f"merge target {q(r['target_id'])} is itself merged into another person; "
                "write the merge to the final person (contract silent; refused)")
        if r["decision"] == "link":
            if r["target_id"] in merged_away:
                add("overrides-chain", n, f"link target {q(r['target_id'])} is merged into another person (contract "
                    "silent; refused)")
            if r["alias_id"] in merged_away:
                continue
            linked_to.setdefault(r["target_id"], []).append((n, r["alias_id"]))
    for target, links in linked_to.items():
        if len(links) > 1:
            names = ", ".join(q(a) for _n, a in links)
            out.findings.append(Finding("overrides-shared-identity", f"{where}:{links[1][0]}", f"{names} are all "
                                        f"linked to identity {q(target)}; two persons of one identity are a merge "
                                        "(contract silent; refused)"))
    if not out.findings:
        out.rows = good
    return out


# --------------------------------------------------------------------------- the registry (4.4, lines 507-523)
def build_rows(persons: list, overrides: Overrides) -> list:
    """The registry's rows, one per person not merged into another, in code-point order of ``person_id``:
    ``identity_id`` from the person's ``link`` row; ``display_name`` the linked identity's name, else the
    ``person_id`` (the only names the project's own rows carry); ``merged_from`` the persons merged into it."""
    link = {r["alias_id"]: r["target_id"] for _n, r in overrides.rows if r["decision"] == "link"}
    merge = {r["alias_id"]: r["target_id"] for _n, r in overrides.rows if r["decision"] == "merge"}
    merged_into: dict = {}
    for alias, target in merge.items():
        merged_into.setdefault(target, []).append(alias)
    rows = []
    for pid in persons:
        if pid in merge:
            continue
        identity = link.get(pid, "")
        rows.append({"person_id": pid, "display_name": identity_name(identity) or pid, "identity_id": identity,
                     "merged_from": MERGED_SEPARATOR.join(sorted(merged_into.get(pid, [])))})
    return rows


def identity_name(identity_id: str) -> str:
    """The ``display_name`` of an identity. Without a vantage module the identity source holds only the project's
    persons, who carry no name but their id, so there is none to give and the ``person_id`` is used (4.4, lines
    513-514)."""
    return ""


def registry_bytes(rows: list) -> bytes:
    """The registry as written: CSV, UTF-8, the four columns, rows in code-point order of ``person_id``, line feeds,
    cells quoted only where CSV needs it."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(REGISTRY_COLUMNS)
    for r in rows:
        writer.writerow([r[c] for c in REGISTRY_COLUMNS])
    return buf.getvalue().encode("utf-8")


# --------------------------------------------------------------------------- candidates (4.4, lines 524-528)
def read_stop_words(study) -> tuple:
    """The stop words (4.4, lines 529-530): one per line, folded; blank lines are not words. Without the file, no
    word is left out. Returns ``(words, findings)``."""
    rp = study.paths.get("/identity/stop_words")
    if rp is None or not os.path.lexists(rp.real):
        return set(), []
    try:
        data = read_capped(Path(rp.real), MAX_JSON_BYTES)
        if data is None:
            return set(), [Finding("stop-words-file", rp.repo_rel, f"larger than {MAX_JSON_BYTES} bytes")]
        text = data.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return set(), [Finding("stop-words-file", rp.repo_rel, f"cannot be read: {exc}")]
    return {fold(line) for line in text.splitlines() if line.strip()}, []


_TOKEN = re.compile(r"\w+")


def tokens(name: str, stop_words: set) -> set:
    """The words of a folded name that are not stop words."""
    return {t for t in _TOKEN.findall(fold(name)) if t not in stop_words}


@dataclass(frozen=True)
class Candidate:
    person_id: str
    other_id: str
    kind: str
    decided: bool


def candidates(persons: list, names: dict, stop_words: set, overrides: Overrides) -> list:
    """Possible matches (4.4, lines 524-526), each with its kind: ``same-id`` (the two ids are equal), ``exact`` (the
    folded names are equal), ``similar`` (the names share a word that is not a stop word). Without a vantage module
    the identity source is the project's own persons, and the search "compares those persons with one another"
    (5.2, lines 733-734): each pair of persons once, so ``same-id`` cannot arise here. A pair is listed with its
    strongest kind and marked decided when an override row names it (line 506). A candidate is never a link (lines
    526-527): nothing here writes or applies one. *names* maps each person to its name."""
    decided = overrides.pairs()
    out = []
    for i, a in enumerate(persons):
        for b in persons[i + 1:]:
            if a == b:
                kind = "same-id"
            elif fold(names[a]) == fold(names[b]):
                kind = "exact"
            elif tokens(names[a], stop_words) & tokens(names[b], stop_words):
                kind = "similar"
            else:
                continue
            out.append(Candidate(a, b, kind, frozenset((a, b)) in decided))
    return sorted(out, key=lambda c: (KIND_ORDER.index(c.kind), c.person_id, c.other_id))
