"""Row files and bucket tables (contract section 4 and 4.8): the shared CSV reader, the project-pattern compiler,
the bucket-table checks and bucketer, and the year and period rule.

Every row file is CSV, UTF-8, "with exactly the columns listed, in this order. A missing or extra column is an
error. An empty cell means "not given"; a tool never treats it as a value" (section 4, lines 275-276). A row file is
opened at its resolved place under rule 1.6, like every file a specification names.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

from survey_core import Finding, TooLarge, fold, open_text_capped, q

#: The toolkit's own limits (proposals): the bytes of one row file; the length of one project pattern; the number
#: of patterns in one file; the length of the folded text one pattern is searched in.
MAX_CSV_BYTES = 64 * 1024 * 1024
MAX_PATTERN_CHARS = 1000
MAX_PATTERNS = 10000
MAX_MATCH_CHARS = 65536

TABLE_COLUMNS = ("field", "pattern", "unless", "bucket", "note")


@dataclass
class Rows:
    """A row file as read: its header, its rows as dicts (with the line each starts on), and what was wrong."""

    header: list = field(default_factory=list)
    rows: list = field(default_factory=list)  # (line number, {column: cell})
    findings: list = field(default_factory=list)


def _cells(values) -> str:
    return ", ".join(map(q, values)) or "none"


def read_rows(path: Path, where: str, columns: tuple, rule: str) -> Rows:
    """Read a CSV row file that must have exactly *columns*, in order. A header that differs, or a row whose width
    differs from the header's (4, line 276), is a finding with id *rule*; so is a blank line. A cell holding a NUL
    is a ``cell-nul`` finding. The file is streamed, at most MAX_CSV_BYTES, and only when it is a regular file.
    Line numbers are those a row starts on, so a quoted cell over several lines does not shift them."""
    out = Rows()
    try:
        stream = open_text_capped(path, MAX_CSV_BYTES)
    except TooLarge:
        out.findings.append(Finding(rule, where, f"larger than {MAX_CSV_BYTES} bytes; not read"))
        return out
    except OSError as exc:
        out.findings.append(Finding(rule, where, f"cannot be read: {exc}"))
        return out
    try:
        with stream:
            reader = csv.reader(stream)
            start = 1
            for record in reader:
                line, start = start, reader.line_num + 1
                if any("\x00" in cell for cell in record):
                    out.findings.append(Finding("cell-nul", f"{where}:{line}", "a cell holds a NUL character"))
                    continue
                if line == 1:
                    out.header = record
                    if tuple(record) != tuple(columns):
                        out.findings.append(Finding(rule, f"{where}:1", "the columns are not exactly "
                                                    f"{', '.join(columns)}, in this order (found {_cells(record)})"))
                        return out
                    continue
                if len(record) != len(columns):
                    out.findings.append(Finding(rule, f"{where}:{line}", f"has {len(record)} fields; the columns are "
                                                f"{len(columns)}"))
                    continue
                out.rows.append((line, dict(zip(columns, record))))
    except TooLarge:
        return Rows(findings=[Finding(rule, where, f"larger than {MAX_CSV_BYTES} bytes; not read")])
    except UnicodeDecodeError as exc:
        return Rows(findings=[Finding(rule, where, f"not UTF-8: {exc}")])
    except OSError as exc:  # a read that fails partway through the file
        return Rows(findings=[Finding(rule, where, f"cannot be read: {exc}")])
    except csv.Error as exc:
        rid = "cell-nul" if "NUL" in str(exc) else rule  # Python 3.10's csv refuses a NUL itself
        return Rows(findings=[Finding(rid, where, f"not CSV: {exc}")])
    if not out.header and not out.findings:
        out.findings.append(Finding(rule, where, f"has no header; the columns are {', '.join(columns)}"))
    return out


# --------------------------------------------------------------------------- project patterns
_ESCAPE = re.compile(r"\\.", re.S)


def compile_pattern(text: str, flags: int = 0, *, lower_only: bool = False) -> tuple:
    """Compile a pattern a project wrote. Returns ``(pattern, None)`` or ``(None, why)``. Refused: a pattern longer
    than MAX_PATTERN_CHARS, one the regular-expression engine cannot compile for any reason (an error, a repeat
    count too large, nesting too deep), and, with *lower_only*, one with an upper-case letter outside an escape: it
    is searched in folded, lower-cased text (4.8), where it could never match."""
    if len(text) > MAX_PATTERN_CHARS:
        return None, f"is longer than {MAX_PATTERN_CHARS} characters"
    if lower_only and any(ch.isupper() for ch in _ESCAPE.sub("", text)):
        return None, "has an upper-case letter; values are folded to lower case before they are searched (4.8)"
    try:
        return re.compile(text, flags), None
    except (re.error, OverflowError, RecursionError, ValueError) as exc:
        return None, f"does not compile: {type(exc).__name__}: {exc}"


def search(pattern: re.Pattern, folded: str) -> bool:
    """Search folded text no longer than MAX_MATCH_CHARS; raises ValueError for longer text, which the caller
    reports."""
    if len(folded) > MAX_MATCH_CHARS:
        raise ValueError(f"the text is longer than {MAX_MATCH_CHARS} characters")
    return pattern.search(folded) is not None


# --------------------------------------------------------------------------- bucket tables (4.8)
@dataclass
class TableRow:
    line: int
    field: str
    pattern: re.Pattern
    unless: re.Pattern | None
    bucket: str


def check_table(path: Path, where: str, allowed: list | None) -> tuple:
    """Read and check a bucket table. Returns ``(rows, findings)``. Errors (4.8, lines 686-687): other columns, an
    empty table, a row without ``pattern``, ``bucket`` or ``note``, an expression that does not compile. And the
    toolkit's own refusals: a ``bucket`` outside the attribute's declared levels or flags (*allowed*, when
    declared), an upper-case or over-long pattern, more than MAX_PATTERNS rows. It searches no text, so it never
    raises the ValueError that :func:`search` raises for text over MAX_MATCH_CHARS: every problem is a finding."""
    read = read_rows(path, where, TABLE_COLUMNS, "table-columns")
    findings, rows = list(read.findings), []
    if read.findings:
        return rows, findings
    if not read.rows:
        return rows, [Finding("table-empty", where, "a bucket table has at least one row (4.8)")]
    if len(read.rows) > MAX_PATTERNS:
        return rows, [Finding("table-pattern", where, f"more than {MAX_PATTERNS} rows")]
    for n, r in read.rows:
        at = f"{where}:{n}"
        missing = [c for c in ("pattern", "bucket", "note") if r[c] == ""]
        if missing:
            findings.append(Finding("table-row", at, f"no {', '.join(missing)}"))
            continue
        compiled = {}
        for col in ("pattern", "unless"):
            if r[col] == "":
                continue
            pattern, why = compile_pattern(r[col], lower_only=True)
            if pattern is None:
                findings.append(Finding("table-pattern", at, f"{col} {q(r[col])} {why}"))
            else:
                compiled[col] = pattern
        if allowed is not None and r["bucket"] not in allowed:
            findings.append(Finding("table-bucket", at, f"bucket {q(r['bucket'])} is not one of the attribute's "
                                    f"declared values ({_cells(allowed)})"))
        if "pattern" in compiled and (r["unless"] == "" or "unless" in compiled):
            rows.append(TableRow(n, r["field"], compiled["pattern"], compiled.get("unless"), r["bucket"]))
    return (rows if not findings else []), findings


def _fires(row: TableRow, kind: str, value: str) -> bool:
    if row.field != "*" and row.field != kind:
        return False
    folded = fold(value)  # spaces kept (4.8)
    if not search(row.pattern, folded):
        return False
    return not (row.unless is not None and search(row.unless, folded))


def bucket_first(rows: list, values: list, fallback: str | None, missing: str) -> str:
    """``match: "first"`` (4.8): rows are tried in order, and the first row that fires on any of the values decides.
    If none fires, the bucketer's ``fallback``, or the attribute's missing value. *values* is a list of
    ``(attribute_kind, value)``; an empty value is not given and never fires. A value whose folded text is longer
    than MAX_MATCH_CHARS raises ValueError: the caller (the frame, step D) must turn it into a finding."""
    for row in rows:
        if any(_fires(row, kind, v) for kind, v in values if v != ""):
            return row.bucket
    return fallback if fallback is not None else missing


def bucket_all(rows: list, values: list) -> set:
    """``match: "all"`` (4.8): every row that fires adds its bucket; no fallback. Raises ValueError for a value over
    MAX_MATCH_CHARS, as :func:`bucket_first` does; the caller must turn it into a finding."""
    return {row.bucket for row in rows if any(_fires(row, kind, v) for kind, v in values if v != "")}


# --------------------------------------------------------------------------- years and periods (4.8)
_BC = r"\s*(?:b\.c\.e\.|b\.c\.|bce|bc)(?![A-Za-z])"
#: A run of digits, with an optional sign before it and an optional BC/BCE marker after it.
_RUN = re.compile(r"(?<![0-9])(-?)([0-9]+)(?![0-9])(" + _BC + r")?", re.I)
#: A stated century: an ordinal number followed, as a whole token, by c, c., cent, cent., century or centuries,
#: in any case; an optional BC/BCE marker after it makes the century negative.
_CENTURY = re.compile(r"(?<![0-9])([0-9]{1,2})(?:st|nd|rd|th)\s*(?:centuries|century|cent\.?|c\.?)(?![A-Za-z])"
                      r"(" + _BC + r")?", re.I)


def _runs(value: str) -> list:
    """Runs of three or four digits that are not part of a longer number and not negative (4.8, lines 699-701).
    Negative: a ``-`` directly before the run that follows no digit (``-350``; after a digit, ``1740-1790`` is a
    range), or a BC/BCE marker directly after it (``350 BC``)."""
    years = []
    for m in _RUN.finditer(value):
        sign, digits, bc = m.group(1), m.group(2), m.group(3)
        if len(digits) not in (3, 4) or bc:
            continue
        if sign and (m.start() == 0 or not value[m.start() - 1].isdigit()):
            continue
        years.append(int(digits))
    return years


def _centuries(value: str) -> list:
    """The middle years of the centuries a value states (``4th c.`` -> 350); a century marked BC/BCE is negative
    and not read."""
    return [(int(m.group(1)) - 1) * 100 + 50 for m in _CENTURY.finditer(value)
            if int(m.group(1)) >= 1 and not m.group(2)]


def year_of(value: str, basis: str) -> int | None:
    """The year one value gives (4.8, lines 699-702): for ``work_date`` the first run of three or four digits that
    is not part of a longer number, for ``life_dates`` the largest; only where a value has no such run, a stated
    century gives its middle year (the first stated, or the largest, by the same basis); else none. Two-digit and
    negative years are not read."""
    if basis not in ("work_date", "life_dates"):
        raise ValueError(f"unknown basis {q(basis)}")
    years = _runs(value) or _centuries(value)
    if not years:
        return None
    return years[0] if basis == "work_date" else max(years)


def life_year(values: list) -> int | None:
    """For ``life_dates``, the largest year among the values (4.8)."""
    years = [y for y in (year_of(v, "life_dates") for v in values) if y is not None]
    return max(years) if years else None


def period_of(year: int, cuts: list) -> int:
    """The period, counted from 1, of a year: ``i - 1`` cuts are at or below it (4.8)."""
    return 1 + sum(1 for c in cuts if c <= year)
