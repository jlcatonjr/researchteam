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
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from survey_core import (
    MAX_JSON_BYTES, Finding, canonical_json, file_identity, inside, load_json_strict, q, read_capped, reason,
    resolve_path, sha256_bytes, symlink_components,
)

SUFFIX = ".provenance.json"
#: The most bytes read back from one recorded input when its hash is compared (the row-file cap of step B).
MAX_INPUT_BYTES = 64 * 1024 * 1024
RECORD_KEYS = ("output", "tool", "study", "schema_version", "inputs", "gates", "plugins", "legacy_exceptions")
GATE_KEYS = ("state", "mode", "enforce")
NOT_DECLARED = "NOT DECLARED"
#: The ``sha256`` recorded for a declared input that was absent when the output was built (a proposal: 4.6 lists
#: only files read, so an input that appears later would otherwise go unnoticed).
ABSENT = ""


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


def check_current(root: Path, rel: str, expect_tool: str | None = None,
                  expect_schema_version: str | None = None) -> Currency:
    """Read the record at *rel* and compare each ``inputs`` and ``plugins`` entry with the file as it is now (4.6,
    lines 566-568). Missing, malformed, or any mismatch: not built, with the reasons. An input recorded as absent
    (``"sha256": ""``, a declared file that was not there at build time) that is there now is a mismatch too. With
    *expect_tool* or *expect_schema_version*, a record written by another tool, or for another ``schema_version``,
    is not built either. (4.6 has no field for the toolkit's own version, so a record written by an older release of
    the same tool cannot be told apart: a proposal.)"""
    path = root / rel
    if not os.path.lexists(path):
        return Currency(False, [f"the record {q(rel)} is missing"])
    try:
        data = read_capped(path, MAX_JSON_BYTES)
    except OSError as exc:
        return Currency(False, [f"the record {q(rel)} cannot be read: {reason(exc)}"])
    if data is None:
        return Currency(False, [f"the record {q(rel)} is larger than {MAX_JSON_BYTES} bytes"])
    doc, errs = load_json_strict(data, rel)
    errs = errs or check_record_shape(doc, rel)
    if errs:
        return Currency(False, [f.message for f in errs])
    reasons = []
    if expect_tool is not None and doc["tool"] != expect_tool:
        reasons.append(f"the record was written by {q(doc['tool'])}, not {q(expect_tool)}")
    if expect_schema_version is not None and doc["schema_version"] != expect_schema_version:
        reasons.append(f"the record is for schema_version {q(doc['schema_version'])}, not {q(expect_schema_version)}")
    root_real = os.path.realpath(root)
    for entry in [*doc["inputs"], *({"path": p["file"], "sha256": p["sha256"]} for p in doc["plugins"])]:
        name = q(entry["path"])
        place = os.path.realpath(root.joinpath(*entry["path"].split("/")))
        if not inside(place, root_real):
            reasons.append(f"{name} resolves outside the repository")
            continue
        if entry["sha256"] == ABSENT:
            if os.path.lexists(root.joinpath(*entry["path"].split("/"))):
                reasons.append(f"{name} was absent when the output was built and is there now")
            continue
        if not os.path.isfile(place):
            reasons.append(f"{name} is gone")
            continue
        try:
            now = read_capped(Path(place), MAX_INPUT_BYTES)
        except OSError as exc:
            reasons.append(f"{name} cannot be read: {reason(exc)}")
            continue
        if now is None or sha256_bytes(now) != entry["sha256"]:
            reasons.append(f"{name} changed since the output was built")
    return Currency(not reasons, reasons)


# --------------------------------------------------------------------------- where an output may go
#: The first path component that no output may be written under, case-folded: the whole of ``.github`` (workflows
#: and the agent team), as well as ``.git`` and every generated team location (the ledger's reserved places).
RESERVED_TOPS = (".github",)


def _norm(path: str) -> str:
    """A path as names are compared here: Unicode NFC, then case-folded."""
    return unicodedata.normalize("NFC", path).casefold()


def _within(rel: str, folder: str) -> bool:
    """Whether *rel* is *folder* or inside it, comparing normalised repository-relative paths."""
    a, b = _norm(rel), _norm(folder)
    return a == b or a.startswith(b + "/")


def _nearest_existing(root: Path, rel: str) -> Path:
    """The deepest existing folder on the way to *rel* (the repository root at worst)."""
    parts = rel.split("/")[:-1]
    here = root
    for part in parts:
        nxt = here / part
        if not os.path.isdir(nxt):
            break
        here = nxt
    return here


def check_output_target(study, rel: str, own_pointer: str | None = None) -> None:
    """Refuse (WriteRefused) an output target that is not an allowed place. Every writer calls this, for each output
    and each record, before it writes anything.

    **Allowlist.** An output lies inside the study's own folder, the folder that holds ``study.json`` (4.4 and 4.6
    only ever place an output in the study; a proposal). This is checked three ways, and all must agree: the
    repository-relative path (NFC, case-folded) is under the study folder's; the real path of the nearest existing
    parent is inside the study folder's real path; and walking up from that parent reaches the study folder (device
    and inode) before the repository root. A study whose folder is the repository root has no such place.

    **Within the study folder**, still refused: the specification, any other declared path (other than the output's
    own, *own_pointer*), anything inside a declared folder or inside a folder that holds a covered file (other than
    the study folder itself), and anything in the ledger folder: by NFC, case-folded path, and by device and inode
    where the file exists.

    **Second layer**: the reserved places (``.git``, ``.github``, the generated team locations), by name and by
    identity, whatever the first layer said."""
    from survey_ledger import LEDGER_PREFIX, reserved_by_identity, reserved_by_name

    root = study.repo_root
    study_rel = study.study_rel
    refuse = lambda why: WriteRefused(f"{q(rel)} {why}")  # noqa: E731
    if study_rel in ("", "."):
        raise refuse("cannot be written: the study's folder is the repository root, and an output lies inside the "
                     "study's own folder")
    study_dir = root.joinpath(*study_rel.split("/"))
    study_real = os.path.realpath(study_dir)
    parent = _nearest_existing(root, rel)
    by_path = _within(rel, study_rel) and _norm(rel) != _norm(study_rel)
    by_real = inside(os.path.realpath(parent), study_real)
    by_walk = False
    if os.path.isdir(study_dir):
        study_id = file_identity(study_real)
        here = Path(os.path.abspath(parent))
        root_abs = Path(os.path.abspath(root))
        while True:
            if file_identity(os.path.realpath(here)) == study_id:
                by_walk = True
                break
            if here == root_abs or here.parent == here:
                break
            here = here.parent
    if not (by_path and by_real and by_walk):
        raise refuse(f"is not inside the study's folder {q(study_rel)}; an output and its record lie there "
                     "(a repo:-rooted output outside it is refused)")

    target_real = os.path.realpath(root.joinpath(*rel.split("/")))
    target_id = file_identity(target_real) if os.path.exists(target_real) else None
    declared = [(study.spec_rel, os.path.realpath(root / study.spec_rel))]
    declared += [(rp.repo_rel, rp.real) for ptr, rp in study.paths.items() if ptr != own_pointer]
    for other_rel, other_real in declared:
        same = _norm(other_rel) == _norm(rel) or other_real == target_real or (
            target_id is not None and os.path.exists(other_real) and file_identity(other_real) == target_id)
        if same:
            raise refuse(f"is the same file as {q(other_rel)}, which the specification names; an output never "
                         "writes over a declared file")
        if _within(rel, other_rel) or inside(target_real, other_real):
            raise refuse(f"is inside {q(other_rel)}, which the specification declares; an output is not written "
                         "into another declared location")
    for ptr, rp in study.paths.items():
        if "/covers/" in ptr and "/" in rp.repo_rel:
            folder = rp.repo_rel.rsplit("/", 1)[0]
            if _norm(folder) != _norm(study_rel) and _within(rel, folder):
                raise refuse(f"is in {q(folder)}, a folder that holds a file a gate covers")
    ledger = study.spec["signoffs"]["ledger"]
    if ledger.startswith(LEDGER_PREFIX):
        lp, _errors = resolve_path(ledger[len(LEDGER_PREFIX):], study.study_rel, root, "ledger")
        if lp is not None and (_within(rel, lp.repo_rel) or inside(target_real, lp.real)):
            raise refuse("is in the ledger folder; no output goes there")

    parts = [_norm(p) for p in rel.split("/")]
    if reserved_by_name(rel) or any(p in RESERVED_TOPS for p in parts[:1]) or reserved_by_identity(root, rel) or \
            any(os.path.exists(root / top) and _under(root, rel, root / top) for top in RESERVED_TOPS):
        raise refuse("is under .git, .github or a generated team location; no output goes there")


def _under(root: Path, rel: str, top: Path) -> bool:
    """Whether a folder on the way to *rel* is the same directory as *top* (device and inode)."""
    top_id = file_identity(os.path.realpath(top))
    parts = rel.split("/")
    for i in range(len(parts)):
        here = root.joinpath(*parts[: i + 1])
        if os.path.exists(here) and file_identity(os.path.realpath(here)) == top_id:
            return True
    return False


# --------------------------------------------------------------------------- writing
class WriteRefused(Exception):
    """An output could not be written safely; nothing was written."""


def check_writable(root: Path, rel: str) -> None:
    """Refuse (WriteRefused) unless *rel* can be replaced safely: its folder is a plain directory reached without a
    symbolic link, and the path is absent or a regular file, not a link."""
    folder_rel = rel.rsplit("/", 1)[0] if "/" in rel else ""
    links = symlink_components(root, rel)
    if links:
        raise WriteRefused(f"a component of {q(rel)} is a symbolic link: {', '.join(map(q, links))}")
    folder = root / folder_rel if folder_rel else root
    if not os.path.isdir(folder) or os.path.islink(folder):
        raise WriteRefused(f"the folder of {q(rel)} does not exist or is not a plain directory")
    path = root / rel
    if os.path.lexists(path) and (os.path.islink(path) or not os.path.isfile(path)):
        raise WriteRefused(f"{q(rel)} exists and is not a regular file")


def write_atomic(root: Path, rel: str, data: bytes) -> None:
    """Write one output; see :func:`write_all`."""
    write_all(root, [(rel, data)])


#: Whether this platform can write relative to an open folder: open the folder once (``O_DIRECTORY | O_NOFOLLOW``),
#: create the temporary file in it with ``O_EXCL`` and replace relative to the same descriptor, so the write lands in
#: the folder that was checked even if a parent is swapped meanwhile. Linux and macOS can; elsewhere the plain path
#: code below is used, with the same checks, and the window between the last check and ``os.replace`` remains.
#: ``os.replace`` takes ``src_dir_fd``/``dst_dir_fd`` wherever ``os.rename`` does (both are ``renameat``); only
#: ``os.rename`` is listed in ``os.supports_dir_fd``.
DIR_FD_WRITES = (os.name == "posix" and hasattr(os, "O_DIRECTORY") and hasattr(os, "O_NOFOLLOW")
                 and {os.open, os.rename, os.unlink} <= os.supports_dir_fd)


def write_all(root: Path, outputs: list) -> None:
    """Write several outputs, each as survey-manifest writes a manifest, in the order given: every target is checked
    (no link on the way, a regular file or nothing there), every temporary file is written in its target's folder
    (mode 0644), every target is checked again, and only then is each temporary file moved into place, in order. A
    refusal at any check leaves every file as it was; only an interruption between two replaces leaves the earlier
    ones replaced and the later ones not (the caller orders them so that this is safe). The temporary files are
    removed on every failure. The caller has already called :func:`check_output_target` for each."""
    for rel, _data in outputs:
        check_writable(root, rel)
    if DIR_FD_WRITES:
        _write_all_dir_fd(root, outputs)
    else:
        _write_all_paths(root, outputs)


def _write_all_paths(root: Path, outputs: list) -> None:
    temps = []
    try:
        for rel, data in outputs:
            fd, tmp = tempfile.mkstemp(prefix=".survey-", dir=(root / rel).parent)
            temps.append(tmp)
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
            os.chmod(tmp, 0o644)
        for rel, _data in outputs:
            check_writable(root, rel)  # again, just before anything lands
        for (rel, _data), tmp in zip(outputs, temps):
            replace(tmp, str(root / rel), None)
    finally:
        for tmp in temps:
            if os.path.lexists(tmp):
                os.unlink(tmp)


def _write_all_dir_fd(root: Path, outputs: list) -> None:
    folders = {}  # folder path -> open descriptor
    temps = []  # (descriptor, temporary name)
    try:
        for rel, data in outputs:
            folder = (root / rel).parent
            if folder not in folders:
                expected = os.stat(folder)  # check_writable has just found it a plain directory reached without links
                dfd = os.open(folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                folders[folder] = dfd
                got = os.fstat(dfd)
                if (got.st_dev, got.st_ino) != (expected.st_dev, expected.st_ino):
                    raise WriteRefused(f"the folder of {q(rel)} changed while it was being opened")
            dfd = folders[folder]
            name = f".survey-{os.urandom(8).hex()}"
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_BINARY", 0), 0o644,
                         dir_fd=dfd)
            temps.append((dfd, name))
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
                os.fchmod(fh.fileno(), 0o644)
        for rel, _data in outputs:
            check_writable(root, rel)  # again, just before anything lands
        for (rel, _data), (dfd, name) in zip(outputs, temps):
            replace(name, (root / rel).name, dfd)
    finally:
        for dfd, name in temps:
            try:
                os.unlink(name, dir_fd=dfd)
            except FileNotFoundError:
                pass
        for dfd in folders.values():
            os.close(dfd)


def replace(src: str, dst: str, dir_fd) -> None:
    """``os.replace``, relative to *dir_fd* when one is given; a seam tests use to interrupt a write before it
    lands."""
    if dir_fd is None:
        os.replace(src, dst)
    else:
        os.replace(src, dst, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
