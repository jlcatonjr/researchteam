"""Shared core of the survey toolkit (docs/survey-toolkit.md, version 1).

Standard library only (contract rule 1.7); Python 3.10 to 3.13. Nothing here reads the clock (rule 1.5) or the
network. The modules of this folder import each other by file name: each command puts its own directory first on
``sys.path``, so the commands also run under ``python3 -I``.

What lives here: findings (an error id, where, a message), folded text (rule 1.10), canonical JSON and the
manifest's file hashing (6.1), the repository root, and the path rule (1.6).
"""
from __future__ import annotations

import hashlib
import json
import os
import posixpath
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

CONTRACT = "docs/survey-toolkit.md"
CONTRACT_VERSION = "1"

#: The suffixes of a text file, matched case-sensitively (6.1). A text file is hashed with each CRLF made LF.
TEXT_SUFFIXES = (".json", ".jsonl", ".csv", ".tsv", ".md", ".txt", ".py", ".R", ".sh", ".yaml", ".yml")

#: The prefix that roots a path at the repository (rule 1.6).
REPO_PREFIX = "repo:"


@dataclass(frozen=True)
class Finding:
    """One violation: a stable error id, where it is (a file and a JSON pointer, or a path), and what is wrong."""

    rule: str
    where: str
    message: str

    def line(self) -> str:
        return f"ERROR [{self.rule}] {self.where}: {self.message}"


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
_HYPHEN_BREAK = re.compile(r"-\s+")
_WS = re.compile(r"\s+")


def fold(text: str, *, spaces: bool = True) -> str:
    """Fold *text* as rule 1.10 says: decompose (NFD) and remove combining marks, lower-case, remove soft hyphens,
    remove a hyphen followed by white space together with that white space, and make each remaining run of white
    space one space with none at either end. With ``spaces=False`` (*folded without spaces*) the white space is
    removed altogether.

    A *combining mark* is read as a character of Unicode general category M (Mn, Mc, Me). The result depends on
    the Unicode database of the running Python (:func:`environment`)."""
    decomposed = unicodedata.normalize("NFD", text)
    out = "".join(ch for ch in decomposed if not unicodedata.category(ch).startswith("M"))
    out = out.lower().replace("­", "")
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
    """Lower-case hex SHA-256 of a file's bytes, with each CRLF replaced by LF when *rel* has a text suffix (6.1)."""
    data = path.read_bytes()
    if is_text_file(rel):
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------- repository root and paths (rule 1.6)
def find_repo_root(start: Path) -> Path | None:
    """The nearest directory at or above *start* that holds a ``.git`` entry of any kind, or None."""
    here = Path(os.path.abspath(start))
    for candidate in (here, *here.parents):
        if os.path.lexists(candidate / ".git"):
            return candidate
    return None


def inside(path: str, root: str) -> bool:
    """Whether the real path *path* is *root* or below it (both already real paths)."""
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:
        return False


@dataclass(frozen=True)
class ResolvedPath:
    """A specification path under rule 1.6: as declared, as a repository-relative path, and where it resolves."""

    declared: str
    repo_rel: str  # repository-relative, forward slashes, lexically normalised
    real: str  # os.path.realpath of the place it names

    def path(self, repo_root: Path) -> Path:
        return repo_root / self.repo_rel


def resolve_path(declared: str, study_rel: str, repo_root: Path, where: str) -> tuple[ResolvedPath | None, list[Finding]]:
    """Apply rule 1.6 to one declared path.

    *study_rel* is the study folder, repository-relative. The path is relative to it, or to the repository root
    when it starts with ``repo:``. An absolute path, a ``..`` segment, a backslash, or a path that resolves outside
    the repository through a link is an error. Returns the resolved path, or None with the findings."""
    findings: list[Finding] = []
    if not isinstance(declared, str) or declared == "":
        return None, [Finding("path-empty", where, "a path must be a non-empty string")]
    rooted = declared.startswith(REPO_PREFIX)
    rest = declared[len(REPO_PREFIX):] if rooted else declared
    if rest == "":
        return None, [Finding("path-empty", where, f"{declared!r} names nothing after {REPO_PREFIX!r}")]
    if "\\" in rest:
        findings.append(Finding("path-backslash", where,
                                f"{declared!r} contains a backslash; write paths with forward slashes"))
    if rest.startswith("/") or re.match(r"^[A-Za-z]:", rest) or "\x00" in rest:
        findings.append(Finding("path-absolute", where, f"{declared!r} is absolute; rule 1.6 allows only a path "
                                "relative to the study's folder or a repo:-rooted one"))
    if ".." in rest.replace("\\", "/").split("/"):
        findings.append(Finding("path-dotdot", where, f"{declared!r} has a '..' segment (rule 1.6)"))
    if findings:
        return None, findings
    base = "" if rooted else study_rel
    repo_rel = posixpath.normpath(posixpath.join(base, rest)) if base else posixpath.normpath(rest)
    if repo_rel in (".", "") or repo_rel.startswith("../") or repo_rel == "..":
        return None, [Finding("path-outside", where, f"{declared!r} does not name a place inside the repository")]
    root_real = os.path.realpath(repo_root)
    real = os.path.realpath(os.path.join(root_real, *repo_rel.split("/")))
    if not inside(real, root_real):
        return None, [Finding("path-outside", where,
                              f"{declared!r} resolves outside the repository through a link (rule 1.6)")]
    return ResolvedPath(declared, repo_rel, real), []


def symlink_components(repo_root: Path, repo_rel: str) -> list[str]:
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


def load_json_strict(data: bytes, where: str) -> tuple[object, list[Finding]]:
    """Parse UTF-8 JSON, refusing a key given twice in one object and the non-JSON constants NaN and Infinity."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        return None, [Finding("json", where, f"not UTF-8: {exc}")]
    try:
        return json.loads(text, object_pairs_hook=_no_duplicates, parse_constant=_no_constant), []
    except _DuplicateKey as exc:
        return None, [Finding("json-duplicate-key", where, f"the key {exc.args[0]!r} is given twice in one object")]
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
    """``[--root DIR] <project> <extra...>``. Returns ``(repo_root, project, extras)``; raises SurveyUsageError."""
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
