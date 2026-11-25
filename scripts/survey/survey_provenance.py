"""The provenance record every output carries (contract 4.6), and the one way outputs are written.

The record, exactly as 4.6 (lines 553-558) gives it::

    { "output": path, "tool": string, "study": slug, "schema_version": string,
      "inputs": [ { "path": path, "sha256": string } ],
      "gates": { "<gate>": { "state": string, "mode": string, "enforce": string, "manifest_sha256"?: string } },
      "plugins": [ { "file": path, "attr": string, "version": string, "sha256": string } ],
      "legacy_exceptions": int }

- A JSON output carries it as its top-level ``provenance`` field; any other output has it beside it, named as the
  output with ``.provenance.json`` added, written in the same run (561-562).
- ``inputs`` lists the files the tool actually read, the specification among them, each as it was read (563-564):
  the SHA-256 of the very bytes the tool parsed. It holds no hash of the output (565).
- An output whose record is missing, or whose ``inputs`` or ``plugins`` no longer match the files, is not built
  (566-568): :func:`check_current` says so.
- Canonical JSON, no date (572). Nothing here reads the clock.

Step B writes one record (the registry's); step C adds its own outputs through the same functions.
"""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from survey_core import (
    MAX_JSON_BYTES, Finding, canonical_json, inside, load_json_strict, q, read_capped, sha256_bytes,
    symlink_components,
)

SUFFIX = ".provenance.json"
#: The most bytes read back from one recorded input when its hash is compared (the row-file cap of step B).
MAX_INPUT_BYTES = 64 * 1024 * 1024
RECORD_KEYS = ("output", "tool", "study", "schema_version", "inputs", "gates", "plugins", "legacy_exceptions")
GATE_KEYS = ("state", "mode", "enforce")
NOT_DECLARED = "NOT DECLARED"


def record_rel(output_rel: str) -> str:
    """Where the record of a non-JSON output goes: beside it, ``.provenance.json`` added (4.6, line 562)."""
    return output_rel + SUFFIX


def gate_entry(status) -> dict:
    """One ``gates`` entry from a :class:`survey_gates.GateStatus`: its state, mode and enforce, and the manifest
    hash when one could be built. A gate the specification does not declare has the state ``NOT DECLARED`` (4.6,
    line 570); its ``mode`` and ``enforce`` are then empty (the contract names no value for them)."""
    if not status.declared:
        return {"state": NOT_DECLARED, "mode": "", "enforce": ""}
    entry = {"state": status.state, "mode": status.mode, "enforce": status.enforce}
    if status.manifest_sha256:
        entry["manifest_sha256"] = status.manifest_sha256
    return entry


def gate_entries(study, gates: tuple) -> dict:
    """The ``gates`` field for a stage that depends on *gates*, with each state as ``survey_gates.gate_status``
    returns it (in this version never ``CLEARED``)."""
    from survey_gates import gate_status
    from survey_ledger import check_ledger

    ledger = check_ledger(study)
    return {gate: gate_entry(gate_status(study, gate, ledger)[0]) for gate in gates}


def make_record(study, output_rel: str, tool: str, inputs: list, gates: dict, plugins: list | None = None,
                legacy_exceptions: int = 0) -> dict:
    """A record of 4.6. *inputs* is a list of ``(repository-relative path, sha256)`` in the order the tool read
    them, the specification first."""
    return {
        "output": output_rel,
        "tool": tool,
        "study": study.spec["id"],
        "schema_version": study.spec["schema_version"],
        "inputs": [{"path": path, "sha256": digest} for path, digest in inputs],
        "gates": gates,
        "plugins": list(plugins or []),
        "legacy_exceptions": legacy_exceptions,
    }


def record_bytes(record: dict) -> bytes:
    """The record as written: canonical JSON, like a manifest (4.6, line 572)."""
    return canonical_json(record)


def check_record_shape(doc, where: str) -> list:
    """A record is malformed unless it has exactly the fields of 4.6 with their types."""
    bad = lambda msg: [Finding("provenance-malformed", where, msg)]  # noqa: E731
    if not isinstance(doc, dict) or set(doc) != set(RECORD_KEYS):
        return bad(f"a provenance record has exactly the fields {', '.join(RECORD_KEYS)}")
    if not all(isinstance(doc[k], str) for k in ("output", "tool", "study", "schema_version")):
        return bad("output, tool, study and schema_version are strings")
    if not isinstance(doc["legacy_exceptions"], int) or isinstance(doc["legacy_exceptions"], bool) \
            or doc["legacy_exceptions"] < 0:
        return bad("legacy_exceptions is a whole number")
    if not isinstance(doc["inputs"], list) or not all(
            isinstance(e, dict) and set(e) == {"path", "sha256"} and all(isinstance(v, str) for v in e.values())
            for e in doc["inputs"]):
        return bad("each inputs entry is exactly {path, sha256}")
    if not isinstance(doc["plugins"], list) or not all(
            isinstance(e, dict) and set(e) == {"file", "attr", "version", "sha256"}
            and all(isinstance(v, str) for v in e.values()) for e in doc["plugins"]):
        return bad("each plugins entry is exactly {file, attr, version, sha256}")
    if not isinstance(doc["gates"], dict):
        return bad("gates is an object")
    for gate, entry in doc["gates"].items():
        keys = set(entry) if isinstance(entry, dict) else set()
        if not (set(GATE_KEYS) <= keys <= set(GATE_KEYS) | {"manifest_sha256"}) or \
                not all(isinstance(v, str) for v in entry.values()):
            return bad(f"gates entry {q(gate)} is not {{state, mode, enforce, manifest_sha256?}}")
    return []


@dataclass
class Currency:
    """Whether an output is built: its record is there, well-formed, and every input and plug-in it lists still has
    the hash it was read with."""

    built: bool
    reasons: list


def check_current(root: Path, rel: str) -> Currency:
    """Read the record at *rel* and compare each ``inputs`` and ``plugins`` entry with the file as it is now (4.6,
    lines 566-568). Missing, malformed, or any mismatch: not built, with the reasons."""
    path = root / rel
    if not os.path.lexists(path):
        return Currency(False, [f"the record {rel} is missing"])
    try:
        data = read_capped(path, MAX_JSON_BYTES)
    except OSError as exc:
        return Currency(False, [f"the record {rel} cannot be read: {exc}"])
    if data is None:
        return Currency(False, [f"the record {rel} is larger than {MAX_JSON_BYTES} bytes"])
    doc, errs = load_json_strict(data, rel)
    errs = errs or check_record_shape(doc, rel)
    if errs:
        return Currency(False, [f.message for f in errs])
    reasons = []
    root_real = os.path.realpath(root)
    for entry in [*doc["inputs"], *({"path": p["file"], "sha256": p["sha256"]} for p in doc["plugins"])]:
        place = os.path.realpath(root.joinpath(*entry["path"].split("/")))
        if not inside(place, root_real) or not os.path.isfile(place):
            reasons.append(f"{entry['path']} is gone")
            continue
        try:
            now = read_capped(Path(place), MAX_INPUT_BYTES)
        except OSError as exc:
            reasons.append(f"{entry['path']} cannot be read: {exc}")
            continue
        if now is None or sha256_bytes(now) != entry["sha256"]:
            reasons.append(f"{entry['path']} changed since the output was built")
    return Currency(not reasons, reasons)


# --------------------------------------------------------------------------- writing
class WriteRefused(Exception):
    """An output could not be written safely; nothing was written."""


def check_writable(root: Path, rel: str) -> None:
    """Refuse (WriteRefused) unless *rel* can be replaced safely: its folder is a plain directory reached without a
    symbolic link, and the path is absent or a regular file, not a link."""
    folder_rel = rel.rsplit("/", 1)[0] if "/" in rel else ""
    links = symlink_components(root, rel)
    if links:
        raise WriteRefused(f"a component of {rel} is a symbolic link: {', '.join(links)}")
    folder = root / folder_rel if folder_rel else root
    if not os.path.isdir(folder) or os.path.islink(folder):
        raise WriteRefused(f"the folder of {rel} does not exist or is not a plain directory")
    path = root / rel
    if os.path.lexists(path) and (os.path.islink(path) or not os.path.isfile(path)):
        raise WriteRefused(f"{rel} exists and is not a regular file")


def write_atomic(root: Path, rel: str, data: bytes) -> None:
    """Write *data* to *rel* as survey-manifest writes a manifest: checked just before writing (no link on the way,
    a regular file or nothing there), a temporary file in the same folder, mode 0644, then ``os.replace``. An
    interruption before the replace leaves the old file as it was."""
    check_writable(root, rel)
    path = root / rel
    fd, tmp = tempfile.mkstemp(prefix=".survey-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.chmod(tmp, 0o644)
        replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def replace(tmp: str, path: Path) -> None:
    """``os.replace``; a seam tests use to interrupt a write before it lands."""
    os.replace(tmp, path)
