"""Shared core of the survey toolkit (docs/survey-toolkit.md, version 1).

Standard library only (contract rule 1.7); Python 3.10 to 3.13. Nothing here reads the clock (rule 1.5) or the
network. The modules of this folder import each other by file name: each command puts its own directory first on
``sys.path``, so the commands also run under ``python3 -I``.

What lives here: the gate names, findings (an error id, where, a message), folded text (rule 1.10), canonical JSON
and the manifest's file hashing (6.1), size-capped reading, file identity, and the path rule (1.6).
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import stat
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

#: The gates of 6.1, in the order every command lists them. The one definition; the other modules import it.
GATES = ("S0", "S5", "S6", "S8")

#: The suffixes of a text file, matched case-sensitively (6.1). A text file is hashed with each CRLF made LF.
TEXT_SUFFIXES = (".json", ".jsonl", ".csv", ".tsv", ".md", ".txt", ".py", ".R", ".sh", ".yaml", ".yml")

#: The prefix that roots a path at the repository (rule 1.6).
REPO_PREFIX = "repo:"

#: The most bytes the tools read from a specification, a manifest file or a JSON file of the ledger folder, and
#: from the ledger's decisions log. Larger files are refused, not read. The caps are the toolkit's own.
MAX_JSON_BYTES = 16 * 1024 * 1024
MAX_LOG_BYTES = 64 * 1024 * 1024
_CHUNK = 1024 * 1024


@dataclass(frozen=True)
class Finding:
    """One violation: a stable error id, where it is (a file and a JSON pointer, or a path), and what is wrong."""

    rule: str
    where: str
    message: str

    def line(self, label: str = "ERROR") -> str:
        """The finding as one output line. Every control character is escaped, whatever produced the text: a cell, a
        path declared in a specification, a file name or a pattern can never forge another output line."""
        return safe(f"{label} [{self.rule}] {self.where}: {self.message}")


def safe(text: str) -> str:
    """*text* with every control, format, surrogate, private-use or line/paragraph-separator character escaped
    (``\\xNN``, ``\\uNNNN``), so that what a file holds cannot add a line or move the cursor in the output."""
    out = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat[0] == "C" or cat in ("Zl", "Zp"):
            code = ord(ch)
            out.append(f"\\x{code:02x}" if code < 0x100 else f"\\u{code:04x}" if code < 0x10000 else f"\\U{code:08x}")
        else:
            out.append(ch)
    return "".join(out)


class SurveyUsageError(Exception):
    """A usage or environment error: no such project, no repository root. Exit 2."""


def environment() -> dict:
    """What the output of a run depends on beyond its inputs: the Python version and the Unicode database that
    folded text (rule 1.10) is computed with."""
    return {
        "python": "%d.%d.%d" % sys.version_info[:3],
        "unicodedata": unicodedata.unidata_version,
    }


# --------------------------------------------------------------------------- folded text (rule 1.10)
SOFT_HYPHEN = "\u00ad"
_HYPHEN_BREAK = re.compile(r"-\s+")
_WS = re.compile(r"\s+")


def fold(text: str, *, spaces: bool = True) -> str:
    """Fold *text* as rule 1.10 says: decompose (NFD) and remove combining marks, lower-case, remove soft hyphens,
    remove a hyphen followed by white space together with that white space, and make each remaining run of white
    space one space with none at either end. With ``spaces=False`` (*folded without spaces*) the white space is
    removed altogether.

    Step A only pins it in a test; the later steps use it (bucket tables 4.8, forbidden vocabulary 5.3, receipt
    ids 4.4, identity candidates). A *combining mark* is read as a character of Unicode general category M (Mn,
    Mc, Me), and a hyphen as U+002D. The result depends on the running Python's Unicode database
    (:func:`environment`)."""
    decomposed = unicodedata.normalize("NFD", text)
    out = "".join(ch for ch in decomposed if not unicodedata.category(ch).startswith("M"))
    out = out.lower().replace(SOFT_HYPHEN, "")
    out = _HYPHEN_BREAK.sub("", out)
    if spaces:
        return _WS.sub(" ", out).strip()
    return _WS.sub("", out)


# --------------------------------------------------------------------------- canonical JSON and hashing (6.1)
def canonical_json(value) -> bytes:
    """Canonical JSON (6.1): keys sorted, no white space, UTF-8, one trailing line feed."""
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return text.encode("utf-8") + b"\n"


def is_text_file(path: str) -> bool:
    """A file is text by its suffix alone, matched case-sensitively (6.1)."""
    return path.endswith(TEXT_SUFFIXES)


def file_sha256(path: Path, rel: str) -> str:
    """Lower-case hex SHA-256 of a file's bytes, read in chunks, with each CRLF replaced by LF when *rel* has a
    text suffix (6.1). A CR at the end of one chunk is held back until the next chunk shows what follows it."""
    digest, text, held = hashlib.sha256(), is_text_file(rel), b""
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(_CHUNK)
            if not chunk:
                break
            if text:
                chunk = held + chunk
                held = b""
                if chunk.endswith(b"\r"):
                    chunk, held = chunk[:-1], b"\r"
                chunk = chunk.replace(b"\r\n", b"\n")
            digest.update(chunk)
    digest.update(held)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class NotARegularFile(OSError):
    """The path is not a regular file (a link, FIFO, socket, device or directory), so it was not read."""


def _open_regular(path: Path) -> int:
    """An open descriptor on the regular file at *path*: opened without following a final symbolic link
    (``O_NOFOLLOW``, where the platform has it) and without blocking on a FIFO (``O_NONBLOCK``), then checked by
    ``fstat`` on the descriptor itself, so nothing can swap the file between the check and the read. Raises
    NotARegularFile for anything but a regular file, and OSError as opening does (a link gives ``ELOOP``)."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0)
    fd = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise NotARegularFile(f"{getattr(path, 'name', path)!r} is not a regular file")
    except BaseException:
        os.close(fd)
        raise
    return fd


def read_capped(path: Path, cap: int) -> bytes | None:
    """The bytes of the regular file at *path* (see :func:`_open_regular`), or None when it holds more than *cap*
    bytes."""
    fd = _open_regular(path)
    try:
        if os.fstat(fd).st_size > cap:
            return None
        chunks, total = [], 0
        while total <= cap:  # O_NONBLOCK does not affect reads of a regular file
            chunk = os.read(fd, min(_CHUNK, cap + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
    finally:
        os.close(fd)
    data = b"".join(chunks)
    return None if len(data) > cap else data


class TooLarge(OSError):
    """The file holds more bytes than the cap allows; it was not read to the end."""


class _CappedRaw(io.RawIOBase):
    """A raw reader over a descriptor that raises TooLarge once more than *cap* bytes have been read."""

    def __init__(self, fd: int, cap: int):
        self._fd, self._left = fd, cap + 1

    def readable(self) -> bool:
        return True

    def readinto(self, buffer) -> int:
        data = os.read(self._fd, min(len(buffer), self._left))
        self._left -= len(data)
        if self._left <= 0:
            raise TooLarge("larger than the cap")
        buffer[: len(data)] = data
        return len(data)

    def close(self) -> None:
        if not self.closed:
            os.close(self._fd)
        super().close()


def open_text_capped(path: Path, cap: int):
    """The regular file at *path* (see :func:`_open_regular`) as a UTF-8 text stream with ``newline=""`` (as the csv
    module needs), read in chunks. Reading past *cap* bytes raises TooLarge; the file is never held whole."""
    fd = _open_regular(path)
    if os.fstat(fd).st_size > cap:
        os.close(fd)
        raise TooLarge("larger than the cap")
    return io.TextIOWrapper(io.BufferedReader(_CappedRaw(fd, cap)), encoding="utf-8", newline="")


# --------------------------------------------------------------------------- paths (rule 1.6)
def inside(path: str, root: str) -> bool:
    """Whether the real path *path* is *root* or below it (both already real paths)."""
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:
        return False


def file_identity(real: str) -> tuple:
    """What makes two paths the same file (rule 1.6, "however each is written"): the device and inode of a place
    that exists, so two spellings on a case-insensitive file system are one file; otherwise the real path."""
    try:
        st = os.stat(real)
    except OSError:
        return ("path", real)
    return ("inode", st.st_dev, st.st_ino)


@dataclass(frozen=True)
class ResolvedPath:
    """A specification path under rule 1.6: as declared, as a repository-relative path, and where it resolves."""

    declared: str
    repo_rel: str  # repository-relative with forward slashes: the declared text, joined to the study folder
    real: str  # os.path.realpath of the place it names

    @property
    def identity(self) -> tuple:
        return file_identity(self.real)


def resolve_path(declared: str, study_rel: str, repo_root: Path, where: str) -> tuple:
    """Apply rule 1.6 to one declared path. Returns ``(ResolvedPath, [])`` or ``(None, findings)``.

    *study_rel* is the study folder, repository-relative ("" for the root itself). The path is relative to it, or
    to the repository root when it starts with ``repo:``. Errors: an absolute path, a ``..`` segment, a path that
    resolves outside the repository through a link (rule 1.6); and, the toolkit's own refusals, a backslash, a NUL,
    and a ``.`` or empty segment, so that the manifest can carry the path exactly as declared (6.1)."""
    if not isinstance(declared, str) or declared == "":
        return None, [Finding("path-empty", where, "a path must be a non-empty string")]
    rooted = declared.startswith(REPO_PREFIX)
    rest = declared[len(REPO_PREFIX):] if rooted else declared
    if rest == "":
        return None, [Finding("path-empty", where, f"{declared!r} names nothing after {REPO_PREFIX!r}")]
    findings: list = []
    if "\x00" in rest:
        return None, [Finding("path-nul", where, f"{declared!r} contains a NUL character")]
    if "\\" in rest:
        findings.append(Finding("path-backslash", where,
                                f"{declared!r} contains a backslash; write paths with forward slashes"))
    if rest.startswith("/") or re.match(r"^[A-Za-z]:", rest):
        findings.append(Finding("path-absolute", where, f"{declared!r} is absolute; rule 1.6 allows only a path "
                                "relative to the study's folder or a repo:-rooted one"))
    segments = rest.replace("\\", "/").split("/")
    if ".." in segments:
        findings.append(Finding("path-dotdot", where, f"{declared!r} has a '..' segment (rule 1.6)"))
    if not rest.startswith("/") and ("." in segments or "" in segments):
        findings.append(Finding("path-segment", where, f"{declared!r} has a '.' or empty segment (a doubled or "
                                "trailing slash); write the path without it"))
    if findings:
        return None, findings
    repo_rel = f"{study_rel}/{rest}" if (study_rel and not rooted) else rest
    root_real = os.path.realpath(repo_root)
    real = os.path.realpath(os.path.join(root_real, *repo_rel.split("/")))
    if not inside(real, root_real):
        return None, [Finding("path-outside", where,
                              f"{declared!r} resolves outside the repository through a link (rule 1.6)")]
    return ResolvedPath(declared, repo_rel, real), []


def symlink_components(repo_root: Path, repo_rel: str) -> list:
    """The components of *repo_rel* (below the repository root) that are symbolic links, as repo-relative paths."""
    links, current = [], Path(repo_root)
    parts = repo_rel.split("/")
    for i, part in enumerate(parts):
        current = current / part
        if os.path.islink(current):
            links.append("/".join(parts[: i + 1]))
    return links


# --------------------------------------------------------------------------- strict JSON
class _DuplicateKey(ValueError):
    pass


def _no_duplicates(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise _DuplicateKey(key)
        seen[key] = value
    return seen


def _no_constant(name):
    raise ValueError(f"{name} is not JSON")


def load_json_strict(data: bytes, where: str) -> tuple:
    """Parse UTF-8 JSON, refusing a key given twice in one object, the non-JSON constants NaN and Infinity, and
    nesting too deep for the parser. Returns ``(value, [])`` or ``(None, findings)``."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        return None, [Finding("json", where, f"not UTF-8: {exc}")]
    try:
        return json.loads(text, object_pairs_hook=_no_duplicates, parse_constant=_no_constant), []
    except _DuplicateKey as exc:
        return None, [Finding("json-duplicate-key", where, f"the key {exc.args[0]!r} is given twice in one object")]
    except RecursionError:
        return None, [Finding("json", where, "nested too deeply to read")]
    except ValueError as exc:
        return None, [Finding("json", where, f"not valid JSON: {exc}")]


def print_findings(findings, stream=None) -> None:
    stream = stream or sys.stdout
    for f in findings:
        print(f.line(), file=stream)


# --------------------------------------------------------------------------- command lines
#: The repository a command runs in by default: the one this folder is synced into (scripts/survey/ -> root).
DEFAULT_ROOT = Path(__file__).resolve().parent.parent.parent


def parse_args(argv: list, prog: str, extra: tuple = ()) -> tuple:
    """``[--root DIR] <project> <extra...>``. Returns ``(repo_root, project, extras)``; raises SurveyUsageError.
    ``--root`` is for tests; the bridge refuses it, and always works on its own repository."""
    args = list(argv)
    root = DEFAULT_ROOT
    if args[:1] == ["--root"]:
        if len(args) < 2:
            raise SurveyUsageError("--root needs a directory")
        root = Path(os.path.abspath(args[1]))
        args = args[2:]
    if len(args) != 1 + len(extra) or any(a.startswith("-") for a in args):
        raise SurveyUsageError(f"usage: {prog} [--root DIR] <project>" + "".join(f" <{e}>" for e in extra))
    if not os.path.lexists(root / ".git"):
        raise SurveyUsageError(f"{root.name or root} is not a repository root (no .git); paths in a "
                               "specification are judged against the repository (rule 1.6)")
    return root, args[0], args[1:]


def usage_exit(exc: Exception) -> int:
    print(f"error: {exc}", file=sys.stderr)
    return 2
