"""The frame-change log (contract 4.4, lines 461-476): one JSON Lines entry per change to the frame.

``{ "id", "date", "reason", "results_seen", "frame_sha256", "n_units", "added", "removed", "units" }``

The log is the project's: its ``id``, ``date``, ``reason`` and ``results_seen`` are an author's, so no tool writes an
entry (rule 1.5: a tool does not read the clock to fill in a date). The check (line 475): the current frame's hash,
taken as a manifest takes a text file's (6.1), must be the last entry's ``frame_sha256``; a frame cannot change
without an entry. ``survey-frame`` runs it on the frame it is about to write and, where it fails, writes nothing and
prints the entry the log needs, with the four fields that are the author's left for the author.
"""
from __future__ import annotations

import hashlib
import json
import re

from survey_core import Finding, load_json_strict, q

ENTRY_KEYS = ("id", "date", "reason", "results_seen", "frame_sha256", "n_units", "added", "removed", "units")
_HEX64 = re.compile(r"[0-9a-f]{64}")


def frame_sha256(data: bytes) -> str:
    """The frame file's hash as a manifest computes a text file's (6.1, line 807): each CRLF made LF."""
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def read_log(data: bytes, rel: str) -> tuple:
    """``(entries, findings)``: each line one JSON object with exactly the entry's fields and their types (lines
    463-467). The toolkit's own checks (tightenings, listed in the check table): no blank line; a non-empty, unique
    ``id``; ``frame_sha256`` 64 lower-case hex digits; ``n_units`` the number of ``units``; ``units`` without repeats;
    the first entry lists every unit as added and removes none (line 473); a later entry's ``added`` and ``removed``
    are exactly what its ``units`` gained and lost since the entry before."""
    findings, entries = [], []
    add = lambda n, msg: findings.append(Finding("change-log", f"{rel}:{n}", msg))  # noqa: E731
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines = lines[:-1]
    ids = set()
    previous = None
    for n, line in enumerate(lines, start=1):
        if line.strip() == b"":
            add(n, "a blank line (one entry per line)")
            continue
        doc, errs = load_json_strict(line, f"{rel}:{n}")
        if errs or not isinstance(doc, dict):
            add(n, "not a JSON object")
            continue
        if set(doc) != set(ENTRY_KEYS):
            add(n, f"an entry has exactly the fields {', '.join(ENTRY_KEYS)}")
            continue
        bad = [k for k in ("id", "date", "reason", "frame_sha256") if not isinstance(doc[k], str)]
        bad += [] if isinstance(doc["results_seen"], bool) else ["results_seen"]
        bad += [] if isinstance(doc["n_units"], int) and not isinstance(doc["n_units"], bool) else ["n_units"]
        bad += [k for k in ("added", "removed", "units")
                if not (isinstance(doc[k], list) and all(isinstance(v, str) for v in doc[k]))]
        if bad:
            add(n, f"{', '.join(bad)} not of the entry's types (4.4, lines 463-467)")
            continue
        if doc["id"] == "" or doc["id"] in ids:
            add(n, f"id {q(doc['id'])} is empty or given twice; it is what a report cites (line 474)")
        ids.add(doc["id"])
        if not _HEX64.fullmatch(doc["frame_sha256"]):
            add(n, "frame_sha256 is not 64 lower-case hex digits")
        units = doc["units"]
        if len(set(units)) != len(units):
            add(n, "units lists a unit twice")
        if doc["n_units"] != len(units):
            add(n, f"n_units {doc['n_units']} is not the number of units ({len(units)})")
        before = set(previous["units"]) if previous is not None else set()
        gained, lost = sorted(set(units) - before), sorted(before - set(units))
        if sorted(doc["added"]) != gained or sorted(doc["removed"]) != lost:
            what = "the first entry lists every unit as added and removes none (line 473)" if previous is None \
                else "added and removed are what units gained and lost since the entry before"
            add(n, what)
        entries.append(doc)
        previous = doc
    return entries, findings


def check_frame(entries: list, rel: str, sha: str, units: list) -> list:
    """The check of line 475: the frame about to be written must be the last entry's (its hash, and so its units)."""
    if not entries:
        return [Finding("change-log-entry", rel, "the log has no entry for this frame; a frame cannot change without "
                        "an entry (4.4, lines 473-476)")]
    last = entries[-1]
    if last["frame_sha256"] != sha:
        return [Finding("change-log-entry", rel, f"the last entry ({q(last['id'])}) is for frame "
                        f"{q(last['frame_sha256'])}, not for this frame {q(sha)}; a frame cannot change without an "
                        "entry (4.4, lines 475-476)")]
    if last["units"] != units:
        return [Finding("change-log-entry", rel, f"the last entry ({q(last['id'])}) names this frame's hash but other "
                        "units, or the units in another order")]
    return []


def needed_entry(entries: list, sha: str, units: list) -> str:
    """The entry the log needs for this frame, as one JSON line, with ``id``, ``date``, ``reason`` and
    ``results_seen`` left for the author (``"<...>"`` and ``null``): no tool fills them in."""
    before = set(entries[-1]["units"]) if entries else set()
    entry = {"id": "<the entry's id>", "date": "<the date you give it>", "reason": "<why the frame changed>",
             "results_seen": None, "frame_sha256": sha, "n_units": len(units),
             "added": sorted(set(units) - before), "removed": sorted(before - set(units)), "units": list(units)}
    return json.dumps(entry, ensure_ascii=True, separators=(", ", ": "))
