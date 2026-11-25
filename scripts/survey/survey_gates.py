"""Gates (contract 6.1): the gate list, the manifest builder, the three states, and the rule that turns a gate's
state into "runs" or "refuses".

Step A verifies no signature, so it never reports ``CLEARED``. A gate whose files have changed since a request was
made is ``UNCLEARED`` (6.1). A sign-off *request* is an ``agentteams`` record (rule 1.5 calls its date a field of
``agentteams``), which step A does not read. As its stand-in, step A compares the manifest built now with the
manifest file ``survey-manifest`` last wrote (the bytes the operator is asked to sign): when they differ, the
covered files changed since that manifest was written. Otherwise the state is ``UNAVAILABLE``, because signature
verification is not in this version. Step F replaces :func:`verify_signoff` and revisits the order in
:func:`gate_status`.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from survey_core import (
    GATES, MAX_JSON_BYTES, Finding, canonical_json, file_identity, file_sha256, load_json_strict, read_capped,
    sha256_bytes,
)

__all__ = ["GATES"]  # re-exported: the commands take the gate list from here or from survey_core
CLEARED, UNCLEARED, UNAVAILABLE = "CLEARED", "UNCLEARED", "UNAVAILABLE"
NOT_DECLARED = "NOT DECLARED"  # 4.6
MANIFEST_KIND = "survey-signoff"
MANIFEST_KEYS = {"kind", "gate", "project", "mode", "schema_version", "files"}
NO_VERIFICATION = "signature verification is not in this version of the survey tools"


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
            raise ManifestError(f"{rel} cannot be read: {exc}") from exc
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


def verify_signoff(study, gate: str, manifest_sha256: str, ledger) -> tuple:
    """THE VERIFICATION SEAM. Step F replaces this function with the check of 6.2 (an Ed25519 PASS for the action,
    by a key in the folder and an author on its list, with no binding HALT). Step A cannot verify, so a gate is never
    cleared here."""
    return UNAVAILABLE, NO_VERIFICATION


def gate_status(study, gate: str, ledger) -> tuple:
    """The gate's state (6.1) and any finding that makes the run malformed (a malformed manifest file).

    Order: no declaration; the manifest file malformed (``UNAVAILABLE``); the covered files changed since the stored
    manifest was written, including a covered file now missing (``UNCLEARED``); the ledger malformed
    (``UNAVAILABLE``); a reason the HALT scan could not be made (``UNAVAILABLE``, not a malformed ledger: 6.2); the
    manifest cannot be built (``UNAVAILABLE``); otherwise what :func:`verify_signoff` says."""
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
        cannot_build = str(exc)
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
                    data, findings = None, [Finding("manifest-malformed", rel, f"cannot be read: {exc}")]
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
        # 6.1: UNCLEARED "whether or not signatures can be verified", so step A decides it before the ledger's state.
        # STEP F MUST REVISIT THIS ORDER: CLEARED is "a valid signature exists for the current manifest hash" (6.1),
        # and the request is an agentteams record, not this file. A signature over the current hash may exist although
        # the stored manifest file is older, so the stored file cannot decide UNCLEARED once signatures are read.
        st.state = UNCLEARED
        now = f"now: {cannot_build}" if cannot_build else f"now {st.manifest_sha256}"
        st.reason = (f"the covered files changed since the stored manifest file was written (stored manifest sha256 "
                     f"{stored}, {now}); step A reads that file in place of the agentteams sign-off request. Run "
                     "survey-manifest and have the new manifest signed")
    elif not ledger.ok:
        st.state, st.reason = UNAVAILABLE, "the ledger folder is malformed (see the errors above)"
    elif ledger.unavailable:
        st.state, st.reason = UNAVAILABLE, "the HALT scan cannot be made: " + "; ".join(ledger.unavailable)
    elif cannot_build:
        st.state, st.reason = UNAVAILABLE, f"the manifest cannot be built: {cannot_build}"
    else:
        st.state, st.reason = verify_signoff(study, gate, st.manifest_sha256, ledger)
        if stored is None:
            st.reason += "; no manifest file has been written yet"
    return st, findings


RUNS, REFUSES = "runs", "refuses"


def stage_decision(state: str, enforce: str, declared: bool, legacy: bool) -> tuple:
    """Whether a stage runs, by the table and sentences of 6.1. Returns ``(RUNS|REFUSES, what the output records)``.

    No step-A command is a gated stage; the later steps call this (step D's post-steps, 4.5; step G's enumeration
    and packets).

    - A gate the specification does not declare: the stage refuses, except in a ``legacy`` study, where it runs and
      its output records ``NOT DECLARED``.
    - ``blocking``: runs only when ``CLEARED``; ``UNCLEARED`` or ``UNAVAILABLE`` refuses.
    - ``build-only``: runs in every state; the output records the gate's state and mode.
    """
    if not declared:
        return (RUNS, NOT_DECLARED) if legacy else (REFUSES, NOT_DECLARED)
    if state not in (CLEARED, UNCLEARED, UNAVAILABLE):
        raise ValueError(f"unknown gate state {state!r}")
    if enforce == "blocking":
        return (RUNS, state) if state == CLEARED else (REFUSES, state)
    if enforce == "build-only":
        return RUNS, state
    raise ValueError(f"unknown enforce value {enforce!r}")
