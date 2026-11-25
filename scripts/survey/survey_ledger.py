"""The ledger: the per-study log's folder that ``signoffs.ledger`` names (contract 6.2).

Step A makes every check of the folder that needs no signature. Two kinds of result are kept apart:

- **findings**: the folder is malformed (the ``agentteams-clearance:`` form, the path rule, a link on the way, the
  four parts of the layout, a waivers file, the shape of the key store and the approver list, keys and approvers
  that differ from the team's). ``survey-validate`` fails and ``survey-status`` exits 1.
- **unavailable**: reasons the HALT scan of 6.2 could not be made, exactly the causes lines 910-913 list (a team
  directory reached through a symbolic link, a ``parent_team`` that is absolute, leaves the repository, is not a
  team directory, names the folder itself or declares a parent of its own). By 6.2 these leave every gate
  ``UNAVAILABLE``; the toolkit reads them as not making the folder malformed. A ``parent_team`` value that is no
  usable path at all is a ``ledger-privilege`` finding.

Reading rows for HALTs and verifying signatures need ``agentteams`` and are step F (:func:`survey_gates.verify_signoff`).
Nothing here reads a file that is not a regular file, or lists a directory that is not a plain one.
"""
from __future__ import annotations

import csv
import io
import os
import re
import stat
from dataclasses import dataclass, field
from pathlib import Path

from survey_core import (
    MAX_JSON_BYTES, MAX_LOG_BYTES, REPO_PREFIX, Finding, file_identity, load_json_strict, read_capped, resolve_path,
    symlink_components,
)

LEDGER_PREFIX = "agentteams-clearance:"
#: Every generated team location under a repository root (6.2, the HALT rule).
TEAM_LOCATIONS = (".claude/agents", ".github/agents", ".codex/agents", ".goose/recipes", ".grok/agents")
PRIVILEGE = "references/agent-privilege.json"
LOG = "references/security-decisions.log.csv"
KEYS = "references/authorized-verify-keys"
APPROVERS = "references/security-approvers.txt"
WAIVERS = "references/security-waivers.log.csv"
PARENT_TEAM_KEY = "parent_team"
#: The header the log must have, exactly (6.2 "with the signature columns"; operator decision, 2026-11-25: adopt
#: agentteams' own new-log header). Read from agentteams 1.3.0: ``decision_log.append_signed_decision_row`` creates a
#: missing log with ``["timestamp", "requesting_agent", *SIGNED_DECISION_COLUMNS]``. agentteams refuses a header
#: without ``timestamp`` and ``requesting_agent`` (its legacy schema), and ``--sign-decision`` then will not extend it.
LOG_HEADER = (
    "timestamp", "requesting_agent", "date", "action_reviewed", "verdict", "scope", "conditions",
    "conditions_verified", "evidence", "author", "derives_from", "effect_class", "effect_grants", "effect_targets",
    "effect_relaxes", "effect_destructive", "effect_cross_repo", "effect_bulk", "text_digest", "sig_scheme", "key_id",
    "prev_digest", "signature",
)
KEY_FILE = re.compile(r"([A-Za-z0-9._-]+)\.pub\.pem")
PEM_BEGIN = b"-----BEGIN PUBLIC KEY-----"
PEM_END = b"-----END PUBLIC KEY-----"
MAX_KEY_BYTES = 64 * 1024


@dataclass
class Ledger:
    """The result of the checks. ``rel`` is the folder, repository-relative, when its path is valid."""

    declared: str
    rel: str | None = None
    findings: list = field(default_factory=list)
    unavailable: list = field(default_factory=list)  # reasons the HALT scan cannot be made (6.2)

    @property
    def ok(self) -> bool:
        return not self.findings


def _mode(path: Path):
    try:
        return os.lstat(path).st_mode
    except OSError:
        return None


def is_regular(path: Path) -> bool:
    """A regular file, not reached through a final symbolic link (and not a FIFO, socket or device)."""
    m = _mode(path)
    return m is not None and stat.S_ISREG(m)


def is_plain_dir(path: Path) -> bool:
    """A directory that is not a symbolic link."""
    m = _mode(path)
    return m is not None and stat.S_ISDIR(m)


def is_team_dir(path: Path) -> bool:
    """An agentteams team dir holds ``references/agent-privilege.json`` or ``references/build-log.json``."""
    return os.path.isfile(path / PRIVILEGE) or os.path.isfile(path / "references" / "build-log.json")


def read_approvers(path: Path) -> set:
    """The names on an approver list: one per line, ``#`` comments and blank lines skipped, compared as agentteams
    compares an author (lower-cased, a leading ``@`` removed). Raises OSError, UnicodeDecodeError, or ValueError
    when the file is not a regular file or is too large."""
    if not is_regular(path):
        raise ValueError("not a regular file")
    data = read_capped(path, MAX_JSON_BYTES)
    if data is None:
        raise ValueError(f"larger than {MAX_JSON_BYTES} bytes")
    names = set()
    for line in data.decode("utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            names.add(s.lower().lstrip("@").strip())
    return names


def read_keys(directory: Path) -> dict:
    """``{file name: bytes}`` of the regular ``<key_id>.pub.pem`` files of a key store. A store that is not a plain
    directory is empty; an entry that is not a regular file is not read. Raises OSError as reading does."""
    if not is_plain_dir(directory):
        return {}
    keys = {}
    for entry in sorted(os.listdir(directory)):
        path = directory / entry
        if KEY_FILE.fullmatch(entry) and is_regular(path):
            data = read_capped(path, MAX_KEY_BYTES)
            if data is not None:
                keys[entry] = data
    return keys


def _git_roots(path: Path) -> list:
    roots = []
    for start in (Path(os.path.abspath(path)), Path(os.path.realpath(path))):
        for candidate in (start, *start.parents):
            if os.path.lexists(candidate / ".git") and candidate not in roots:
                roots.append(candidate)
    return roots


def reserved_by_name(repo_rel: str) -> bool:
    """Whether *repo_rel* is inside ``.git`` or at or under a generated team location, comparing case-folded names
    (so ``.GIT/`` and ``.Claude/agents`` count on a case-insensitive file system, and are refused everywhere)."""
    parts = [p.casefold() for p in repo_rel.split("/")]
    if ".git" in parts:
        return True
    return any(parts[: len(loc.split("/"))] == loc.casefold().split("/") for loc in TEAM_LOCATIONS)


def reserved_by_identity(root: Path, repo_rel: str) -> bool:
    """Whether the folder, or a folder above it, is the same directory (device and inode) as the repository's
    existing ``.git`` or a generated team location."""
    reserved = {file_identity(os.path.realpath(root / name)) for name in (".git", *TEAM_LOCATIONS)
                if os.path.exists(root / name)}
    parts = repo_rel.split("/")
    for i in range(len(parts)):
        here = root.joinpath(*parts[: i + 1])
        if os.path.exists(here) and file_identity(os.path.realpath(here)) in reserved:
            return True
    return False


def check_ledger(study) -> Ledger:
    """Every check of 6.2 that needs no signature (see the module's docstring for the two kinds of result)."""
    declared = study.spec["signoffs"]["ledger"]
    where = f"{study.spec_rel}#/signoffs/ledger"
    led = Ledger(declared)
    add = lambda rule, w, msg: led.findings.append(Finding(rule, w, msg))  # noqa: E731
    if not declared.startswith(LEDGER_PREFIX) or declared == LEDGER_PREFIX:
        add("ledger-form", where, f"{declared!r} is not {LEDGER_PREFIX}<path> (6.2)")
        return led
    rp, errors = resolve_path(declared[len(LEDGER_PREFIX):], study.study_rel, study.repo_root, where)
    if errors:
        led.findings += errors
        return led
    root = study.repo_root
    links = symlink_components(root, rp.repo_rel)
    if links:
        add("ledger-link", where, f"no component of the ledger path may be a symbolic link: {', '.join(links)}")
        return led
    if reserved_by_name(rp.repo_rel) or reserved_by_identity(root, rp.repo_rel):
        add("ledger-location", where, f"{rp.repo_rel!r} is inside .git or a generated team location; the ledger "
            "folder is a team dir of its own (6.2)")
        return led
    folder = root / rp.repo_rel
    led.rel = rp.repo_rel
    at = lambda rel: f"{rp.repo_rel}/{rel}"  # noqa: E731
    if not is_plain_dir(folder):
        add("ledger-missing", rp.repo_rel, "the ledger folder does not exist or is not a directory")
        return led
    if not is_plain_dir(folder / "references"):
        add("ledger-layout", at("references"), "missing, or not a plain directory (6.2)")
        return led

    privilege = _read_json_object(folder / PRIVILEGE, at(PRIVILEGE), "ledger-privilege", add,
                                  "missing, or not a regular file; it makes the folder a team dir")
    _check_log(folder / LOG, at(LOG), add)
    _check_key_store(folder / KEYS, at(KEYS), add)
    _check_approvers(folder / APPROVERS, at(APPROVERS), add)
    if os.path.lexists(folder / WAIVERS):
        add("ledger-waiver", at(WAIVERS), "a waivers log in the ledger folder is an error; no gate clears while it "
            "is there (6.2)")

    parent = _check_parent(study, folder, privilege, led, at(PRIVILEGE))
    teams = _team_dirs(study, folder, led)
    if parent is not None:
        teams.append((os.path.relpath(parent, root).replace(os.sep, "/"), parent))
    if led.findings:
        led.unavailable.append("the comparison of the ledger's keys and approvers with the team's was not made, "
                               "because the ledger folder has errors")
    else:
        _check_parity(folder, teams, add)
    return led


def _read_json_object(path: Path, where: str, rule: str, add, missing: str):
    if not is_regular(path):
        add(rule, where, missing)
        return None
    try:
        data = read_capped(path, MAX_JSON_BYTES)
    except OSError as exc:
        add(rule, where, f"cannot be read: {exc}")
        return None
    if data is None:
        add(rule, where, f"larger than {MAX_JSON_BYTES} bytes")
        return None
    doc, errs = load_json_strict(data, where)
    if errs or not isinstance(doc, dict):
        add(rule, where, "not a JSON object")
        return None
    return doc


def _check_log(path: Path, where: str, add) -> None:
    if not is_regular(path):
        add("ledger-log", where, "missing, or not a regular file")
        return
    try:
        data = read_capped(path, MAX_LOG_BYTES)
        if data is None:
            add("ledger-log", where, f"larger than {MAX_LOG_BYTES} bytes; not read")
            return
        rows = list(csv.reader(io.StringIO(data.decode("utf-8"), newline="")))
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        add("ledger-log", where, f"cannot be read or parsed: {exc}")
        return
    if not rows:
        add("ledger-log", where, "has no header")
        return
    header = rows[0]
    if tuple(header) != LOG_HEADER:
        add("ledger-log", where, "the header is not exactly the one agentteams 1.3.0 writes for a new log: "
            + ",".join(LOG_HEADER))
    for n, row in enumerate(rows[1:], start=2):
        if row and len(row) != len(header):
            add("ledger-log", f"{where}:{n}", f"has {len(row)} fields; the header has {len(header)}")


def _check_key_store(store: Path, where: str, add) -> None:
    if not is_plain_dir(store):
        add("ledger-keys", where, "missing, or not a plain directory")
        return
    found = 0
    try:
        entries = sorted(os.listdir(store))
    except OSError as exc:
        add("ledger-keys", where, f"cannot be listed: {exc}")
        return
    for name in entries:
        entry, at = store / name, f"{where}/{name}"
        if not KEY_FILE.fullmatch(name):
            add("ledger-keys", at, "the key store holds only <key_id>.pub.pem files")
        elif not is_regular(entry):
            add("ledger-keys", at, "not a regular file (a link, FIFO or device is not read)")
        else:
            try:
                data = read_capped(entry, MAX_KEY_BYTES)
            except OSError as exc:
                add("ledger-keys", at, f"cannot be read: {exc}")
                continue
            data = (data or b"").strip()
            if not (data.startswith(PEM_BEGIN) and data.endswith(PEM_END)):
                add("ledger-keys", at, "not a PEM public key")
            else:
                found += 1
    if found == 0:
        add("ledger-keys-empty", where, "the folder holds no verify key; no sign-off could clear a gate")


def _check_approvers(path: Path, where: str, add) -> None:
    if not is_regular(path):
        add("ledger-approvers", where, "missing, or not a regular file")
        return
    try:
        names = read_approvers(path)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        add("ledger-approvers", where, f"cannot be read: {exc}")
        return
    if not names:
        add("ledger-approvers-empty", where, "names no approver; agentteams would then fall back to its default "
            "authors, so an empty list is refused")


def _check_parent(study, folder: Path, privilege, led: Ledger, where: str) -> Path | None:
    """The ``parent_team`` rules of 6.2. The causes lines 910-913 list (absolute, leaves the repository, is not a team
    directory, names the folder itself, declares a parent of its own, reached through a symbolic link) leave the gates
    UNAVAILABLE and are not errors of the folder. A value that is none of those, but is no usable path at all (not
    a string, empty, a NUL, ``repo:``-rooted, a backslash or a ``.`` segment), is a bad value in the folder's own
    ``agent-privilege.json``: a ``ledger-privilege`` finding. Returns the parent team dir when it is sound."""
    if not privilege or PARENT_TEAM_KEY not in privilege:
        return None
    value = privilege[PARENT_TEAM_KEY]
    unavailable = lambda why: led.unavailable.append(f"parent_team {value!r} {why}")  # noqa: E731
    malformed = lambda why: led.findings.append(  # noqa: E731
        Finding("ledger-privilege", where, f"parent_team {value!r} {why}"))
    if not isinstance(value, str) or not value:
        malformed("is not a non-empty string")
        return None
    if value.startswith(REPO_PREFIX):
        malformed("is a path relative to the repository root, without a repo: prefix")
        return None
    rp, errors = resolve_path(value, "", study.repo_root, "parent_team")
    if errors:
        rules = {f.rule for f in errors}
        if "path-absolute" in rules:
            unavailable("is absolute")
        elif "path-dotdot" in rules:
            unavailable("has a '..' segment, which is not followed")
        elif "path-outside" in rules:
            unavailable("leaves the repository")
        else:
            malformed("is not a usable path: " + "; ".join(f.message for f in errors))
        return None
    target = study.repo_root / rp.repo_rel
    if symlink_components(study.repo_root, rp.repo_rel) or _linked_inside(target):
        unavailable("is reached through a symbolic link")
        return None
    if not is_team_dir(target):
        unavailable("is not a team directory")
        return None
    if os.path.realpath(target) == os.path.realpath(folder):
        unavailable("names the ledger folder itself")
        return None
    doc = None
    if os.path.lexists(target / PRIVILEGE):
        try:
            data = read_capped(target / PRIVILEGE, MAX_JSON_BYTES)
            doc, errs = load_json_strict(data or b"", "parent_team")
        except OSError:
            errs = ["unreadable"]
        if errs or not isinstance(doc, dict):
            unavailable(f"has an unreadable {PRIVILEGE}")
            return None
    if doc is not None and PARENT_TEAM_KEY in doc:
        unavailable("declares a parent of its own")
        return None
    return target


def _linked_inside(team: Path) -> bool:
    """Whether a part of the team dir the comparison reads (``references/``, its key store, its approver list,
    its privilege file) is a symbolic link: a link there must not redirect what is read."""
    for rel in ("references", KEYS, APPROVERS, PRIVILEGE):
        if os.path.islink(team / rel):
            return True
    return False


def _team_dirs(study, folder: Path, led: Ledger) -> list:
    """The team dirs at the generated locations of this repository. A team directory reached through a symbolic
    link (under any git root above the folder) leaves the gates UNAVAILABLE (6.2)."""
    teams = []
    for groot in _git_roots(folder):
        own_repo = os.path.realpath(groot) == os.path.realpath(study.repo_root)
        for loc in TEAM_LOCATIONS:
            path = groot / loc
            if not os.path.lexists(path):
                continue
            parts = loc.split("/")
            if any(os.path.islink(groot.joinpath(*parts[: i + 1])) for i in range(len(parts))) or \
                    _linked_inside(path):
                rel = os.path.relpath(path, study.repo_root).replace(os.sep, "/")
                led.unavailable.append(f"the team directory {rel} is reached through a symbolic link")
                continue
            if own_repo and is_team_dir(path) and os.path.realpath(path) != os.path.realpath(folder):
                teams.append((loc, path))
    return teams


def _check_parity(folder: Path, teams: list, add) -> None:
    """6.2 (lines 869-873): where the repository's team directory has an approver list naming at least one approver
    and at least one verify key, the folder's list names the same approvers and the folder's keys are the same
    files. "A team directory with only the comment-only list agentteams generates, or with no key file, has
    neither; the folder is then the only place they live": a team that lacks either kind is compared on neither."""
    mine_names = read_approvers(folder / APPROVERS)
    mine_keys = read_keys(folder / KEYS)
    for rel, team in teams:
        try:
            names = read_approvers(team / APPROVERS) if os.path.lexists(team / APPROVERS) else set()
            keys = read_keys(team / KEYS)
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            add("ledger-parity", rel, f"the comparison was not made: the team's approver list or keys cannot be "
                f"read ({exc})")
            continue
        if not (names and keys):
            continue  # the team has neither (6.2); the folder is the only place they live
        if names != mine_names:
            add("ledger-parity", rel, "the ledger's approver list does not name the same approvers as this team's")
        if keys != mine_keys:
            add("ledger-parity", rel, "the ledger's verify keys are not the same files as this team's")
