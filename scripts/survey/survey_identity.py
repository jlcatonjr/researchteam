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
from survey_core import MAX_JSON_BYTES, Finding, fold, in_file, q, read_capped, reason, unsafe_chars
from survey_evidence import COLUMNS as EVIDENCE_COLUMNS
from survey_evidence import REGISTRY_COLUMNS
from survey_provenance import ABSENT
from survey_tables import read_rows_hashed, rows_from_bytes

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


def project_persons(study, evidence_bytes: bytes | None = None) -> Sources:
    """The persons the registry takes (4.4, lines 509-511): every ``person_id`` of the evidence file and, in a
    passage or work study, of the attribution file. A file that is not there (a draft) gives none. An empty
    ``person_id`` is not given (section 4, line 276) and is not a person. With *evidence_bytes*, the evidence file is
    those bytes (a merge works out the registry a build over the merged file would give, 4.4 lines 516-518)."""
    out = Sources()
    seen = set()
    sources = [("/evidence/file", EVIDENCE_COLUMNS, "columns")]
    if study.spec["unit"]["kind"] in ("passage", "work"):
        sources.append(("/unit/attribution/file", attribution_columns(study.spec), "attribution-columns"))
    for ptr, cols, rule in sources:
        rp = study.paths.get(ptr)
        if rp is None:
            continue
        if ptr == "/evidence/file" and evidence_bytes is not None:
            rows, digest = rows_from_bytes(evidence_bytes, rp.repo_rel, cols, rule)
        elif not os.path.lexists(rp.real):
            out.inputs.append((rp.repo_rel, ABSENT))  # declared, absent: its appearing later makes the output stale
            continue
        else:
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
    """Read and check the overrides file, from its declared inputs only. Without a vantage module the identity source
    holds the project's own persons (5.2), so a ``link`` target, a ``merge`` target and a ``distinct`` target are all
    project persons; and every alias is one too: a link names "the project's person" (4.4, line 496), a merge "two of
    the project's ids" (line 497). The registry holds merged ids, so the alias's rows keep the alias."""
    out = Overrides()
    rp = study.paths.get("/identity/overrides")
    if rp is None:
        return out
    if not os.path.lexists(rp.real):  # it may be absent: it starts empty (section 3, line 218)
        out.inputs.append((rp.repo_rel, ABSENT))
        return out
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
            remedy = ("; keep the alias in the rows (the registry holds merged ids), or remove this merge row if the "
                      "rows were rewritten to the target" if decision == "merge" else "")
            add("overrides-alias", n, f"alias_id {q(alias)} is not a person of the project (line 496: a link names "
                "\"the project's person\"; line 497: a merge joins \"two of the project's ids\"; for distinct the "
                f"contract is silent){remedy}")
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
    link_of = {r["alias_id"]: r["target_id"] for _n, r in good if r["decision"] == "link"}
    linked_to: dict = {}
    for n, r in good:
        if r["decision"] == "merge" and r["target_id"] in merged_away:
            add("overrides-chain", n, f"merge target {q(r['target_id'])} is itself merged into another person; "
                "write the merge to the final person (contract silent; refused)")
        if r["decision"] == "link":
            if r["target_id"] in merged_away:
                add("overrides-chain", n, f"link target {q(r['target_id'])} is merged into another person (contract "
                    "silent; refused)")
            elif link_of.get(r["target_id"], r["target_id"]) != r["target_id"]:
                add("overrides-chain", n, f"link target {q(r['target_id'])} is itself linked to "
                    f"{q(link_of[r['target_id']])}; a link names the identity \"as the registry records them\" (5.2, "
                    "line 733), so link to that one (refused)")
            if r["alias_id"] in merged_away:
                continue
            linked_to.setdefault(r["target_id"], []).append((n, r["alias_id"]))
    for target, links in linked_to.items():
        if len(links) > 1:
            names = ", ".join(q(a) for _n, a in links)
            out.findings.append(Finding("overrides-shared-identity", f"{where}:{links[1][0]}", f"{names} are all "
                                        f"linked to identity {q(target)}; two persons of one identity are a merge "
                                        "(contract silent; refused)"))
    out.findings = in_file(out.findings, where)
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
    """The ``display_name`` of an identity (4.4, line 513). Without a vantage module the identity source holds the
    project's own persons, whose only name is their id, so a person linked to another shows that person's id."""
    return identity_id


def unsafe_values(rows: list, where: str) -> list:
    """Findings for any registry cell holding a control character, a format character (a bidirectional override, a
    zero-width character: one id could be made to look like another), a line or paragraph separator, or a NUL. The
    contract gives a ``person_id`` no pattern (only "no ``|``", 4.1 line 309; 4.3 line 438), so these are refused
    before anything is written (a proposal): the registry never holds a cell with a line break in it."""
    out = []
    for r in rows:
        for col in REGISTRY_COLUMNS:
            bad = unsafe_chars(r[col])
            if bad:
                codes = ", ".join(f"U+{ord(c):04X}" for c in bad)
                out.append(Finding("registry-value", where, f"{col} {q(r[col])} of person {q(r['person_id'])} holds "
                                   f"a control, format or line-separator character ({codes}); the registry is not written"))
    return out


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
        return set(), [Finding("stop-words-file", rp.repo_rel, f"cannot be read: {reason(exc)}")]
    return {fold(line) for line in text.splitlines() if line.strip()}, []


_TOKEN = re.compile(r"[^\W_]+")


def tokens(name: str, stop_words: set) -> set:
    """The words of a folded name that are not stop words: runs of letters and digits, so ``_`` separates words as
    ``-`` and white space do."""
    return {t for t in _TOKEN.findall(fold(name)) if t not in stop_words}


@dataclass(frozen=True)
class Candidate:
    person_id: str
    other_id: str
    kind: str
    decided: bool


#: The most candidates one listing shows; the rest are counted (up to MAX_COUNTED), in the same order.
MAX_CANDIDATES = 1000
MAX_COUNTED = 100000


@dataclass
class CandidateList:
    shown: list
    more: int  # candidates beyond the shown ones
    more_is_lower_bound: bool  # counting stopped at MAX_COUNTED
    decided: int = 0  # pairs an override row already names: not listed (a lower bound too when counting stopped)


def candidates(persons: list, names: dict, stop_words: set, overrides: Overrides,
               limit: int | None = None, counted: int | None = None) -> CandidateList:
    """Possible matches (4.4, lines 524-526), each with its kind: ``same-id`` (the two ids are equal), ``exact`` (the
    folded names are equal), ``similar`` (the names share a word that is not a stop word). Without a vantage module
    the identity source is the project's own persons, and the search "compares those persons with one another"
    (5.2, lines 733-734): each pair of persons once, so ``same-id`` cannot arise here. A pair is listed with its
    strongest kind. A pair an override row names is decided (line 506): it is not listed and takes no place in the
    cap, so deciding the shown candidates always reveals the next ones. A candidate is never a link (lines 526-527):
    nothing here writes or applies one. *names* maps each person to its name.

    Persons are indexed by folded name and by word, so only persons that share one are compared. The order is fixed
    (kind, then the two ids); the first *limit* are shown and the rest counted, up to *counted*."""
    limit = MAX_CANDIDATES if limit is None else limit
    counted = MAX_COUNTED if counted is None else counted
    decided = overrides.pairs()
    persons = sorted(set(persons))
    by_name: dict = {}
    by_token: dict = {}
    words = {}
    for p in persons:
        by_name.setdefault(fold(names[p]), []).append(p)
        words[p] = tokens(names[p], stop_words)
        for t in words[p]:
            by_token.setdefault(t, []).append(p)
    shown, total, decided_count = [], 0, 0

    def emit(a, b, kind) -> bool:
        nonlocal total, decided_count
        if frozenset((a, b)) in decided:
            decided_count += 1  # decided pairs are not candidates any more and take no place in the cap
            return True
        total += 1
        if len(shown) < limit:
            shown.append(Candidate(a, b, kind, False))
        return total < counted

    going = True
    exact_pairs = set()
    for a in persons:  # exact, in (a, b) order
        for b in by_name[fold(names[a])]:
            if b > a:
                exact_pairs.add((a, b))
                if going and not emit(a, b, "exact"):
                    going = False
    for a in persons:  # similar, in (a, b) order
        if not going:
            break
        near = sorted({b for t in words[a] for b in by_token[t] if b > a})
        for b in near:
            if (a, b) in exact_pairs:
                continue
            if not emit(a, b, "similar"):
                going = False
                break
    return CandidateList(shown, total - len(shown), not going, decided_count)


# --------------------------------------------------------------------------- planning a build (no writing)
@dataclass
class RegistryPlan:
    """What a registry build would write, worked out without writing: the rows, the registry's bytes, its record's
    bytes, and where both go. ``findings`` stops the build."""

    rows: list = field(default_factory=list)
    data: bytes = b""
    record: bytes = b""
    rel: str = ""
    record_rel: str = ""
    findings: list = field(default_factory=list)
    refusal: str = ""  # a short reason to print after the findings


TOOL = "survey-registry"


def plan_registry(study, evidence_bytes: bytes | None = None) -> RegistryPlan:
    """The registry and record a build would write over the study's declared inputs, with the evidence file read as
    *evidence_bytes* when given. Used by ``survey-registry`` to build, and by ``survey-rows`` to work out "the
    registry that a build over [the merged file] would give" (4.4, lines 516-518) and the record it renews. Writes
    nothing. The caller checks the output targets."""
    from survey_evidence import read_exceptions_hashed
    from survey_provenance import make_record, record_bytes, record_rel
    from survey_core import sha256_bytes

    plan = RegistryPlan()
    plan.findings = identity_refusals(study)
    if plan.findings:
        plan.refusal = "the study needs what this version does not load"
        return plan
    persons = project_persons(study, evidence_bytes)
    overrides = read_overrides(study, persons.persons)
    plan.findings = persons.findings + overrides.findings
    if plan.findings:
        plan.refusal = "a source file or an override row is malformed"
        return plan
    listed, exc_findings, exc_digest = read_exceptions_hashed(study)
    if exc_findings:
        plan.findings, plan.refusal = exc_findings, "the evidence's exceptions file is malformed"
        return plan
    rp = study.paths["/identity/registry"]
    plan.rel, plan.record_rel = rp.repo_rel, record_rel(rp.repo_rel)
    plan.rows = build_rows(persons.persons, overrides)
    plan.findings = unsafe_values(plan.rows, plan.rel)
    if plan.findings:
        plan.refusal = "a registry value is unsafe"
        return plan
    plan.data = registry_bytes(plan.rows)
    inputs = [(study.spec_rel, sha256_bytes(study.spec_bytes)), *persons.inputs, *overrides.inputs]
    if exc_digest is not None:
        inputs.append((study.paths["/evidence/legacy_exceptions"].repo_rel, exc_digest))
    # The registry rests on the evidence file, so it records how many exceptions that file is read with (4.1,
    # line 366). The build applies no row rule; the count is the exceptions file's, as every later stage reads it.
    plan.record = record_bytes(make_record(study, plan.rel, TOOL, inputs, gates={}, plugins=[],
                                           legacy_exceptions=len(listed)))
    return plan
