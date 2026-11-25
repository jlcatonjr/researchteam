"""Gates (contract 6.1, 6.2): the gate list, the manifest builder, the three states, sign-off verification, and the
rule that turns a gate's state into "runs" or "refuses".

**A request** is the manifest file ``survey-manifest`` writes beside the log (``<ledger>/references/<study id>.<gate>
.manifest.json``): the bytes the operator is asked to sign, and the file agentteams' ``--clearance-file`` check hashes
to form the action it looks up. The agentteams side of a request is the signed row whose ``action_reviewed`` names
that hash, with the ``date`` the operator gives (rule 1.5). A gate is ``CLEARED`` only through its request, when the
request is exactly the manifest built now (see :func:`gate_status` for the order).

**Verification** (:func:`verify_signoff`) applies the tools' own rules to the row that decides, before and
independently of agentteams, and only then asks agentteams, in a child process (``survey_verify``), whether it
clears the action. The tools enforce the contract's rules themselves and do not rely on agentteams alone to refuse.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import survey_ledger
import survey_verify
from survey_core import (
    GATES, MAX_JSON_BYTES, Finding, canonical_json, file_identity, file_sha256, load_json_strict, read_capped,
    reason, sha256_bytes,
)

__all__ = ["GATES"]  # re-exported: the commands take the gate list from here or from survey_core
CLEARED, UNCLEARED, UNAVAILABLE = "CLEARED", "UNCLEARED", "UNAVAILABLE"
NOT_DECLARED = "NOT DECLARED"  # 4.6
MANIFEST_KIND = "survey-signoff"
MANIFEST_KEYS = {"kind", "gate", "project", "mode", "schema_version", "files"}
#: Why agentteams did not clear an action. Its own message is never read (the tools decide from its exit status and
#: one JSON line), so this says what its check covers, and the two consequences the operator accepted.
NOT_CLEARED = (
    "agentteams' own check (6.2) did not clear this action: it found no Ed25519 PASS it accepts for the current "
    "manifest hash, or an unretracted HALT on the scope or the action in the ledger log, a generated team log or the "
    "parent_team's log. A HALT on a study id that extends this one with '-', '_', '.' or ':' (demo-2 against demo) "
    "also blocks it (a stricter default the session adopted, Q2). A retraction signed with a shared secret never counts here: the check "
    "runs with an empty HOME, so no shared-secret key is found (Q11)")
#: agentteams' checkout-signing mark: ``--allow-checkout-signing`` writes it into the signed ``conditions_verified``
#: (agentteams 1.3.0, ``operator_signing.sign_decision``). Such a row is refused (a stricter default the session adopted, Q4).
CHECKOUT_MARK = "signed-from-checkout"
#: Row columns that must be empty in a sign-off row (a stricter default the session adopted, Q6): no lineage, no scope column, no declared
#: effect. Each is a signed axis in agentteams and would change what the row authorizes or which HALTs bind it.
EMPTY_COLUMNS = ("derives_from", "scope", "effect_class", "effect_grants", "effect_targets", "effect_relaxes",
                 "effect_destructive", "effect_cross_repo", "effect_bulk")
#: A key id is a plain file stem (agentteams' own pattern), and never holds ``..`` (@security case 44).
KEY_ID = re.compile(r"[A-Za-z0-9._-]+")


def scope(gate: str, study_id: str) -> str:
    """The name a sign-off is checked under (6.2)."""
    return f"{MANIFEST_KIND}/{gate}/{study_id}"


def action(gate: str, study_id: str, manifest_sha256: str) -> str:
    """The action a sign-off reviews (6.2)."""
    return f"{scope(gate, study_id)}:sha256-{manifest_sha256}"


def manifest_rel(ledger_rel: str, study_id: str, gate: str) -> str:
    """Where a gate's manifest file is written: beside the log (6.2: "a per-study log beside the manifests"), and
    the log is ``<ledger>/references/security-decisions.log.csv``. The file name is the toolkit's own."""
    return f"{ledger_rel}/references/{study_id}.{gate}.manifest.json"


class ManifestError(Exception):
    """The manifest cannot be built: a covered file is missing or is not a regular file."""


def manifest_files(study, gate: str) -> list:
    """The specification first, then the gate's ``covers`` in declared order, repeats removed (two paths are the same
    file when they resolve to the same place, rule 1.6). Each entry is ``(repo_rel, real path)``."""
    spec_real = os.path.realpath(study.repo_root / study.spec_rel)
    files, seen = [(study.spec_rel, spec_real)], {file_identity(spec_real)}
    covers = study.spec["signoffs"]["gates"][gate]["covers"]
    for i in range(len(covers)):
        rp = study.paths[f"/signoffs/gates/{gate}/covers/{i}"]
        if rp.identity in seen:
            continue
        seen.add(rp.identity)
        files.append((rp.repo_rel, rp.real))
    return files


def build_manifest(study, gate: str) -> bytes:
    """The gate's manifest as canonical JSON bytes (6.1). Raises ManifestError when a covered file cannot be hashed."""
    entries = []
    for rel, real in manifest_files(study, gate):
        if not os.path.isfile(real):
            raise ManifestError(f"{rel} is missing or is not a regular file")
        try:
            entries.append({"path": rel, "sha256": file_sha256(Path(real), rel)})
        except OSError as exc:
            raise ManifestError(f"{rel} cannot be read: {reason(exc)}") from exc
    g = study.spec["signoffs"]["gates"][gate]
    return canonical_json({
        "kind": MANIFEST_KIND, "gate": gate, "project": study.project, "mode": g["mode"],
        "schema_version": study.spec["schema_version"], "files": entries,
    })


def check_stored_manifest(data: bytes, gate: str, project: str, where: str) -> list:
    """A manifest file is malformed unless it is canonical JSON of exactly the 6.1 shape, for this gate and project."""
    doc, errors = load_json_strict(data, where)
    if errors:
        return [Finding("manifest-malformed", where, errors[0].message)]
    bad = lambda msg: [Finding("manifest-malformed", where, msg)]  # noqa: E731
    if not isinstance(doc, dict) or set(doc) != MANIFEST_KEYS:
        return bad(f"a manifest has exactly the fields {', '.join(sorted(MANIFEST_KEYS))}")
    if doc["kind"] != MANIFEST_KIND or doc["gate"] != gate or doc["project"] != project:
        return bad(f"not the manifest of gate {gate} of project {project!r}")
    if not all(isinstance(doc[k], str) for k in ("mode", "schema_version")) or not isinstance(doc["files"], list):
        return bad("mode and schema_version are strings and files is an array")
    for entry in doc["files"]:
        if not (isinstance(entry, dict) and set(entry) == {"path", "sha256"}
                and all(isinstance(v, str) for v in entry.values())):
            return bad("each files entry is exactly {path, sha256}")
    if canonical_json(doc) != data:
        return bad("not canonical JSON (keys sorted, no white space, UTF-8, one trailing line feed)")
    return []


@dataclass
class GateStatus:
    gate: str
    declared: bool
    enforce: str = ""
    mode: str = ""
    manifest_sha256: str = ""  # empty when the manifest cannot be built
    state: str = NOT_DECLARED
    reason: str = ""
    request_sha256: str = ""  # the stored manifest file's hash, when one was written
    evidence: dict = field(default_factory=dict)  # for CLEARED: the row's line, author and key id; the verifier


def deciding_row(rows: list, act: str):
    """The row that decides (6.2, line 864: "the latest decision that matches the action"), found by the tools' own
    reading, with agentteams 1.3.0's selection rule (``security_gate._latest_security_decision``): newest first,
    ``HALT-RETRACTED`` rows skipped, the first whose ``action_reviewed`` is the action or the action followed by one
    of ``- _ . :``, compared case-insensitively. Using agentteams' rule means both pick the same row; the tools then
    require that row to name exactly the action the tools computed (:func:`row_refusal`), so a row for another study
    or another hash never decides. The exact header (``survey_ledger.LOG_HEADER``) has no ``consumed`` column, so such
    a log is refused; a check spends nothing (6.2, line 889)."""
    want = act.strip().lower()
    suffixed = tuple(want + sep for sep in "-_.:")
    for row in reversed(rows):
        if row["verdict"].strip().upper() == "HALT-RETRACTED":
            continue
        reviewed = row["action_reviewed"].strip().lower()
        if reviewed == want or reviewed.startswith(suffixed):
            return row
    return None


def row_author(row: dict) -> str:
    """The row's author as agentteams 1.3.0 reads it (``decision_log._decision_author``): the first non-empty of
    ``requesting_agent`` and ``author``, lower-cased, a leading ``@`` removed."""
    for column in ("requesting_agent", "author"):
        value = row.get(column, "").strip()
        if value:
            return value.lower().lstrip("@").strip() or value.lower()
    return ""


def row_refusal(row, act: str, keys: dict, approvers: set) -> str:
    """Why the deciding row cannot clear the gate under the tools' own rules (6.2 and the operator's decisions of
    2026-11-25), or ``""``. Values from the log are quoted raw; every command escapes them where it prints (@security case 45)."""
    if row is None:
        return ("no row in the ledger log names this action; the operator signs the action survey-manifest prints "
                "(6.2)")
    at = f"ledger log line {row['_line']}"
    if row["action_reviewed"] != act:
        return (f"the latest row for this action ({at}) names '{row['action_reviewed']}', not exactly the "
                "action; the tools compare actions exactly, case included (@security case 46)")
    verdict, conditions = row["verdict"], row["conditions_verified"]
    if CHECKOUT_MARK in conditions.lower():
        return (f"the row that decides ({at}) was signed from a checkout (agentteams' --allow-checkout-signing "
                "mark); the operator signs from a trusted install (6.2, line 840; a stricter default the session adopted, Q4)")
    if verdict == "HALT":
        return f"the latest row for this action ({at}) is a HALT"
    if not (verdict == "PASS" or (verdict == "CONDITIONAL PASS" and conditions.strip().lower() == "verified")):
        return (f"the row that decides ({at}) has verdict '{verdict}' with conditions_verified "
                f"'{conditions}'; only a PASS, or a CONDITIONAL PASS whose conditions are verified, clears "
                "(6.2, lines 889-891)")
    filled = [c for c in EMPTY_COLUMNS if row.get(c, "").strip()]
    if filled:
        return (f"the row that decides ({at}) fills {', '.join(filled)}; a sign-off row leaves them empty "
                "(a stricter default the session adopted, Q6)")
    key_id = row["key_id"]
    if not KEY_ID.fullmatch(key_id) or ".." in key_id:
        return (f"the row that decides ({at}) names the key id '{key_id}', which is not a plain file stem "
                "(@security case 44)")
    if f"{key_id}.pub.pem" not in keys:
        return (f"the row that decides ({at}) names the key '{key_id}', which is not a key file in the "
                "ledger folder's authorized-verify-keys/ (6.2, line 862)")
    author = row_author(row)
    if author not in approvers:
        return (f"the row that decides ({at}) is by '{author}', who is not on the ledger folder's approver "
                "list (6.2, lines 841-842)")
    return ""


def _snapshot(folder: Path, request: Path):
    """Everything the check depends on in the folder, read once: ``(digest, keys, approvers)``. *digest* holds the
    hashes of the request, the log, the approver list and the keys, and whether the folder holds a waiver file (an
    error, 6.2); *keys* and *approvers* are what the tools' rules are then applied to, so what is compared is what
    was snapshotted (@security S7). Raises OSError, UnicodeDecodeError or ValueError when something cannot be read."""
    parts = []
    for path in (request, folder / survey_ledger.LOG):
        data = read_capped(path, survey_ledger.MAX_LOG_BYTES)
        parts.append(None if data is None else sha256_bytes(data))
    approver_bytes = survey_ledger.read_approver_bytes(folder / survey_ledger.APPROVERS)
    parts.append(sha256_bytes(approver_bytes))
    keys = survey_ledger.read_keys(folder / survey_ledger.KEYS)
    parts.append(tuple(sorted((name, sha256_bytes(data)) for name, data in keys.items())))
    parts.append(os.path.lexists(folder / survey_ledger.WAIVERS))
    return tuple(parts), keys, survey_ledger.parse_approvers(approver_bytes)


def verify_signoff(study, gate: str, manifest_sha256: str, ledger, verifier) -> tuple:
    """The check of 6.2 for a gate whose request is exactly the current manifest. Returns ``(state, reason,
    evidence)``.

    1. Whether agentteams can run here at all (``survey_verify.probe``): else ``UNAVAILABLE``. Rule 1.7 (line 45)
       and lines 915-917: without a usable agentteams (absent, as always on Python 3.10, or older than 1.3.0) a
       gate's state is ``UNAVAILABLE``, so this comes before every rule that would give ``UNCLEARED`` (technical
       review T1). Only the stale-request and no-request steps of :func:`gate_status` come earlier.
    2. One snapshot of the folder: the request must still be the current manifest, the log the one the rows were
       read from, and no waiver file (an error, 6.2) may be there.
    3. The tools' own rules on the row that decides (:func:`deciding_row`, :func:`row_refusal`), with the keys and
       approver list from that snapshot: a failure is ``UNCLEARED``.
    4. agentteams' own check in a child process, about exactly the computed action; then a second snapshot, and any
       difference is ``UNAVAILABLE``. Only a well-formed "cleared" answer for exactly this action is ``CLEARED``
       (``survey_verify.interpret``)."""
    folder = study.repo_root / ledger.rel
    request = study.repo_root / manifest_rel(ledger.rel, study.spec["id"], gate)
    act = action(gate, study.spec["id"], manifest_sha256)
    why = verifier.probe()
    if why:
        return UNAVAILABLE, why, {}
    try:
        before, keys, approvers = _snapshot(folder, request)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return UNAVAILABLE, f"the ledger folder cannot be read: {reason(exc)}", {}
    if before[0] != manifest_sha256 or before[1] != ledger.log_sha256 or before[4]:
        return UNAVAILABLE, "the request or the ledger folder changed since they were checked; run again", {}
    row = deciding_row(ledger.rows, act)
    why = row_refusal(row, act, keys, approvers)
    if why:
        return UNCLEARED, why, {}
    result = verifier.check(study.repo_root, Path(os.path.realpath(folder)), scope(gate, study.spec["id"]),
                            Path(os.path.realpath(request)), act)
    try:
        after = _snapshot(folder, request)[0]
    except (OSError, UnicodeDecodeError, ValueError):
        after = None
    if after != before:
        return UNAVAILABLE, "the ledger folder changed while agentteams checked it; run again", {}
    evidence = {"line": row["_line"], "author": row_author(row), "key_id": row["key_id"], "verifier": result.info}
    if result.outcome == survey_verify.CLEARED:
        return CLEARED, f"signed by '{evidence['author']}' with key '{row['key_id']}' (ledger log " \
                        f"line {row['_line']})", evidence
    if result.outcome == survey_verify.NOT_CLEARED:
        return UNCLEARED, NOT_CLEARED, {"verifier": result.info}
    return UNAVAILABLE, result.why, {"verifier": result.info}


def gate_status(study, gate: str, ledger, verifier=None) -> tuple:
    """The gate's state (6.1) and any finding that makes the run malformed (a malformed manifest file).

    The order, and why (6.1, lines 815-818):

    1. Not declared: ``NOT DECLARED``.
    2. The stored manifest file (the request) malformed: ``UNAVAILABLE``, and a finding.
    3. A request exists and the manifest built now differs from it, or cannot be built (a covered file is gone):
       ``UNCLEARED``. Line 817 says so "whether or not signatures can be verified", so it is decided here, with the
       standard library, before the ledger and before agentteams. It does not contradict line 815 ("a valid
       signature exists for the current manifest hash"): the signature is looked up through the request, so it can
       be found only when the request is the current manifest. When the covered files are put back to an earlier,
       signed state while the request is newer, the gate reads ``UNCLEARED`` until ``survey-manifest`` rewrites the
       file; the rewritten file has the signed bytes, so no new signature is needed (a default the session adopted,
       Q8; line 815 read alone would give ``CLEARED``).
    4. The ledger folder malformed: ``UNAVAILABLE``.
    5. A reason the HALT scan cannot be made (6.2, lines 910-913; more than one git root, @security case 39):
       ``UNAVAILABLE``.
    6. A HALT row on a family name in any scanned log (the interim rule, operator decision Q1): ``UNAVAILABLE``.
    7. No request: ``UNCLEARED`` (a default the session adopted, Q7): there is nothing to verify. This includes a
       manifest that cannot be built now, which is not one of the causes of ``UNAVAILABLE`` line 816 lists (T5).
    8. :func:`verify_signoff`: agentteams usable here, else ``UNAVAILABLE`` (rule 1.7; on Python 3.10 always);
       then the tools' rules (``UNCLEARED``); then ``CLEARED``, ``UNCLEARED`` or ``UNAVAILABLE``."""
    verifier = verifier if verifier is not None else survey_verify.Verifier()
    gates = study.spec["signoffs"]["gates"]
    if gate not in gates:
        return GateStatus(gate, False), []
    g = gates[gate]
    st = GateStatus(gate, True, g["enforce"], g["mode"])
    findings = []
    try:
        st.manifest_sha256 = sha256_bytes(build_manifest(study, gate))
    except ManifestError as exc:
        st.manifest_sha256 = ""
        cannot_build = reason(exc)
    else:
        cannot_build = ""
    stored = None
    if ledger.rel is not None:
        rel = manifest_rel(ledger.rel, study.spec["id"], gate)
        path = study.repo_root / rel
        if os.path.lexists(path):
            if not os.path.isfile(path) or os.path.islink(path):
                findings.append(Finding("manifest-malformed", rel, "not a regular file"))
            else:
                try:
                    data = read_capped(path, MAX_JSON_BYTES)
                except OSError as exc:
                    data, findings = None, [Finding("manifest-malformed", rel, f"cannot be read: {reason(exc)}")]
                if data is None and not findings:
                    findings.append(Finding("manifest-malformed", rel, f"larger than {MAX_JSON_BYTES} bytes"))
                if data is not None:
                    findings += check_stored_manifest(data, gate, study.project, rel)
                if not findings:
                    stored = sha256_bytes(data)
                    st.request_sha256 = stored
    if findings:
        st.state, st.reason = UNAVAILABLE, "the gate's manifest file is malformed"
    elif stored is not None and (cannot_build or stored != st.manifest_sha256):
        st.state = UNCLEARED
        now = f"now: {cannot_build}" if cannot_build else f"now {st.manifest_sha256}"
        st.reason = (f"the covered files changed since the request (stored manifest sha256 {stored}, {now}). Run "
                     "survey-manifest; if the files are back to a signed state, the rewritten request is cleared "
                     "again without a new signature, otherwise have the new manifest signed")
    elif not ledger.ok:
        st.state, st.reason = UNAVAILABLE, "the ledger folder is malformed (see the errors above)"
    elif ledger.unavailable:
        st.state, st.reason = UNAVAILABLE, "the HALT scan cannot be made: " + "; ".join(ledger.unavailable)
    elif gate in ledger.family_halts:
        st.state, st.reason = UNAVAILABLE, "; ".join(ledger.family_halts[gate])
    elif stored is None:
        st.state = UNCLEARED  # Q7; with a manifest that cannot be built too (T5: not a cause line 816 lists)
        st.reason = "no sign-off request: run survey-manifest, then have its action signed" + (
            f" (the manifest cannot be built now: {cannot_build})" if cannot_build else "")
    else:
        st.state, st.reason, st.evidence = verify_signoff(study, gate, st.manifest_sha256, ledger, verifier)
    return st, findings


RUNS, REFUSES = "runs", "refuses"


def stage_decision(state: str, enforce: str, declared: bool, legacy: bool, folder_malformed: bool = False) -> tuple:
    """Whether a stage runs, by the table and sentences of 6.1. Returns ``(RUNS|REFUSES, what the output records)``.

    The callers are the gated stages (step D's post-steps, 4.5, under S6; step G's enumeration and packets, under S0
    and S5); they use :func:`require_gate`.

    - A gate the specification does not declare: the stage refuses, except in a ``legacy`` study, where it runs and
      its output records ``NOT DECLARED``.
    - The sign-off folder malformed (*folder_malformed*: a ledger finding, or a malformed manifest file): the stage
      refuses, ``build-only`` included (operator decision Q9, 2026-11-25; the 6.1 table alone would let a
      ``build-only`` stage run, so this is recorded as a contract proposal).
    - ``blocking``: runs only when ``CLEARED``; ``UNCLEARED`` or ``UNAVAILABLE`` refuses.
    - ``build-only``: runs in every state; the output records the gate's state and mode.
    """
    if not declared:
        return (RUNS, NOT_DECLARED) if legacy else (REFUSES, NOT_DECLARED)
    if state not in (CLEARED, UNCLEARED, UNAVAILABLE):
        raise ValueError(f"unknown gate state {state!r}")
    if enforce not in ("blocking", "build-only"):
        raise ValueError(f"unknown enforce value {enforce!r}")
    if folder_malformed:
        return REFUSES, state
    if enforce == "blocking":
        return (RUNS, state) if state == CLEARED else (REFUSES, state)
    return RUNS, state


def require_gate(study, gate: str, ledger=None, verifier=None) -> tuple:
    """For a gated stage: ``(RUNS|REFUSES, record, status)``, where *record* is the gate's entry of the provenance
    record (4.6: ``state``, ``mode``, ``enforce``, and ``manifest_sha256`` when it could be built).

    Note for the stages that run a plug-in or a post-step (steps D and G; @security case 43): the gate is checked
    before the code runs, so a stage must run exactly the bytes the cleared manifest lists (hash each file it loads
    against its manifest entry and refuse on any difference), or a file swapped between the check and the run would
    execute uncleared."""
    ledger = ledger if ledger is not None else survey_ledger.check_ledger(study)
    st, findings = gate_status(study, gate, ledger, verifier)
    legacy = study.spec.get("status") == "legacy"
    if not st.declared:
        decision, recorded = stage_decision(NOT_DECLARED, "", False, legacy)
        return decision, {"state": recorded, "mode": "", "enforce": ""}, st
    decision, recorded = stage_decision(st.state, st.enforce, True, legacy,
                                        folder_malformed=bool(findings) or not ledger.ok)
    record = {"state": recorded, "mode": st.mode, "enforce": st.enforce}
    if st.manifest_sha256:
        record["manifest_sha256"] = st.manifest_sha256
    return decision, record, st
