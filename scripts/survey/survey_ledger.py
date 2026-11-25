"""The ledger: the per-study log's folder that ``signoffs.ledger`` names (contract 6.2).

Step A makes every structural check of the folder that needs no signature: the ``agentteams-clearance:`` form,
the path rule, no symbolic link on the way, the four parts of the layout, no waivers file, the shape of the key
store and the approver list, the ``parent_team`` rules, and that the folder's keys and approvers are the same as
the repository team's where the team has any. Reading rows for HALTs and verifying signatures need ``agentteams``
and are step F: see :func:`survey_gates.verify_signoff`.
"""
from __future__ import annotations

import csv
import io
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from survey_core import Finding, inside, load_json_strict, resolve_path, symlink_components

LEDGER_PREFIX = "agentteams-clearance:"
#: Every generated team location under a repository root (6.2, the HALT rule).
TEAM_LOCATIONS = (".claude/agents", ".github/agents", ".codex/agents", ".goose/recipes", ".grok/agents")
PRIVILEGE = "references/agent-privilege.json"
LOG = "references/security-decisions.log.csv"
KEYS = "references/authorized-verify-keys"
APPROVERS = "references/security-approvers.txt"
WAIVERS = "references/security-waivers.log.csv"
PARENT_TEAM_KEY = "parent_team"
#: Columns the log must carry. 6.2 says "with the signature columns"; the set is the one agentteams 1.3.0
#: requires before it appends a signed row, plus the two every decision row is matched on.
LOG_COLUMNS = ("action_reviewed", "verdict", "signature", "sig_scheme", "key_id", "derives_from")
KEY_FILE = re.compile(r"^([A-Za-z0-9._-]+)\.pub\.pem$")
PEM_BEGIN = b"-----BEGIN PUBLIC KEY-----"
PEM_END = b"-----END PUBLIC KEY-----"


@dataclass
class Ledger:
    """The result of the structural checks. ``rel`` is the folder, repository-relative, when its path is valid."""

    declared: str
    rel: str | None = None
    findings: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.findings


def _regular(path: Path) -> bool:
    return os.path.isfile(path) and not os.path.islink(path)


def _plain_dir(path: Path) -> bool:
    return os.path.isdir(path) and not os.path.islink(path)


def is_team_dir(path: Path) -> bool:
    """An agentteams team dir holds ``references/agent-privilege.json`` or ``references/build-log.json``."""
    return os.path.isfile(path / PRIVILEGE) or os.path.isfile(path / "references" / "build-log.json")


def read_approvers(path: Path) -> set:
    """The names on an approver list: one per line, ``#`` comments and blank lines skipped, compared as agentteams
    compares an author (lower-cased, a leading ``@`` removed)."""
    names = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            names.add(s.lower().lstrip("@").strip())
    return names


def read_keys(directory: Path) -> dict:
    """``{file name: bytes}`` of the ``*.pub.pem`` files in a key store; an absent store is empty."""
    if not os.path.isdir(directory):
        return {}
    return {p.name: p.read_bytes() for p in sorted(directory.iterdir()) if KEY_FILE.match(p.name)}


def _git_roots(path: Path) -> list:
    roots = []
    for start in (Path(os.path.abspath(path)), Path(os.path.realpath(path))):
        for candidate in (start, *start.parents):
            if os.path.lexists(candidate / ".git") and candidate not in roots:
                roots.append(candidate)
    return roots


def check_ledger(study) -> Ledger:
    """Every structural check of 6.2 that needs no signature. A finding leaves every gate ``UNAVAILABLE``."""
    spec = study.spec
    declared = spec["signoffs"]["ledger"]
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
    folder = root / rp.repo_rel
    led.rel = rp.repo_rel
    at = lambda rel: f"{rp.repo_rel}/{rel}"  # noqa: E731
    if not _plain_dir(folder):
        add("ledger-missing", rp.repo_rel, "the ledger folder does not exist or is not a directory")
        return led
    if not _plain_dir(folder / "references"):
        add("ledger-layout", at("references"), "missing, or not a plain directory (6.2)")
        return led

    privilege = None
    if not _regular(folder / PRIVILEGE):
        add("ledger-privilege", at(PRIVILEGE), "missing, or not a regular file; it makes the folder a team dir")
    else:
        privilege, errs = load_json_strict((folder / PRIVILEGE).read_bytes(), at(PRIVILEGE))
        if errs or not isinstance(privilege, dict):
            add("ledger-privilege", at(PRIVILEGE), "not a JSON object")
            privilege = None

    if not _regular(folder / LOG):
        add("ledger-log", at(LOG), "missing, or not a regular file")
    else:
        _check_log(folder / LOG, at(LOG), add)

    store = folder / KEYS
    if not _plain_dir(store):
        add("ledger-keys", at(KEYS), "missing, or not a plain directory")
    else:
        found = 0
        for entry in sorted(store.iterdir(), key=lambda p: p.name):
            name = f"{KEYS}/{entry.name}"
            if not KEY_FILE.match(entry.name):
                add("ledger-keys", at(name), "the key store holds only <key_id>.pub.pem files")
            elif not _regular(entry):
                add("ledger-keys", at(name), "not a regular file")
            else:
                data = entry.read_bytes().strip()
                if not (data.startswith(PEM_BEGIN) and data.endswith(PEM_END)):
                    add("ledger-keys", at(name), "not a PEM public key")
                else:
                    found += 1
        if found == 0:
            add("ledger-keys-empty", at(KEYS), "the folder holds no verify key; no sign-off could clear a gate")

    if not _regular(folder / APPROVERS):
        add("ledger-approvers", at(APPROVERS), "missing, or not a regular file")
    else:
        try:
            names = read_approvers(folder / APPROVERS)
        except (OSError, UnicodeDecodeError) as exc:
            add("ledger-approvers", at(APPROVERS), f"cannot be read: {exc}")
            names = None
        if names is not None and not names:
            add("ledger-approvers-empty", at(APPROVERS), "names no approver; agentteams would then fall back to "
                "its default authors, so an empty list is refused")

    if os.path.lexists(folder / WAIVERS):
        add("ledger-waiver", at(WAIVERS), "a waivers log in the ledger folder is an error; no gate clears while it "
            "is there (6.2)")

    parent = _check_parent(study, folder, privilege, at(PRIVILEGE), add)
    _check_team_dirs(study, folder, parent, add)
    return led


def _check_log(path: Path, where: str, add) -> None:
    try:
        text = path.read_bytes().decode("utf-8")
        rows = list(csv.reader(io.StringIO(text, newline="")))
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        add("ledger-log", where, f"cannot be read or parsed: {exc}")
        return
    if not rows:
        add("ledger-log", where, "has no header")
        return
    header = [c.strip() for c in rows[0]]
    missing = [c for c in LOG_COLUMNS if c not in header]
    if missing:
        add("ledger-log", where, f"lacks the signature column(s) {', '.join(missing)} (6.2)")
    for n, row in enumerate(rows[1:], start=2):
        if row and len(row) != len(header):
            add("ledger-log", f"{where}:{n}", f"has {len(row)} fields; the header has {len(header)}")


def _check_parent(study, folder: Path, privilege, where: str, add) -> Path | None:
    """The ``parent_team`` rules of 6.2: relative to the repository root, inside it, no link, a team dir, not the
    folder itself, and no parent of its own. Returns the parent team dir when it is sound."""
    if not privilege or PARENT_TEAM_KEY not in privilege:
        return None
    value = privilege[PARENT_TEAM_KEY]
    if not isinstance(value, str) or not value:
        add("ledger-parent", where, "parent_team must be a non-empty string")
        return None
    root = study.repo_root
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value) or "\\" in value:
        add("ledger-parent", where, f"parent_team {value!r} is absolute")
        return None
    if ".." in value.split("/"):
        add("ledger-parent", where, f"parent_team {value!r} leaves the repository")
        return None
    rel = os.path.normpath(value).replace(os.sep, "/")
    target = root / rel
    root_real = os.path.realpath(root)
    if not inside(os.path.realpath(target), root_real):
        add("ledger-parent", where, f"parent_team {value!r} leaves the repository")
        return None
    if symlink_components(root, rel):
        add("ledger-parent", where, f"parent_team {value!r} is reached through a symbolic link")
        return None
    if not is_team_dir(target):
        add("ledger-parent", where, f"parent_team {value!r} is not a team directory")
        return None
    if os.path.realpath(target) == os.path.realpath(folder):
        add("ledger-parent", where, "parent_team names the ledger folder itself")
        return None
    own = target / PRIVILEGE
    if os.path.isfile(own):
        doc, errs = load_json_strict(own.read_bytes(), f"{rel}/{PRIVILEGE}")
        if errs or not isinstance(doc, dict):
            add("ledger-parent", where, f"parent_team {value!r} has an unreadable {PRIVILEGE}")
            return None
        if PARENT_TEAM_KEY in doc:
            add("ledger-parent", where, f"parent_team {value!r} declares a parent of its own")
            return None
    return target


def _check_team_dirs(study, folder: Path, parent: Path | None, add) -> None:
    """No team dir at a generated location is reached through a symbolic link; and where the repository's team has
    approvers or keys, the folder's are the same (6.2, operator ruling 2026-11-24)."""
    teams = []
    for groot in _git_roots(folder):
        for loc in TEAM_LOCATIONS:
            path = groot / loc
            if not os.path.lexists(path):
                continue
            rel = os.path.relpath(path, study.repo_root).replace(os.sep, "/")
            if any(os.path.islink(groot / "/".join(loc.split("/")[: i + 1])) for i in range(len(loc.split("/")))):
                add("ledger-team-link", rel, "a team directory reached through a symbolic link; its HALTs cannot be "
                    "read safely (6.2)")
                continue
            own_repo = os.path.realpath(groot) == os.path.realpath(study.repo_root)
            if is_team_dir(path) and own_repo and os.path.realpath(path) != os.path.realpath(folder):
                teams.append((rel, path))
    if parent is not None:
        teams.append((os.path.relpath(parent, study.repo_root).replace(os.sep, "/"), parent))
    try:
        mine_names = read_approvers(folder / APPROVERS) if os.path.isfile(folder / APPROVERS) else set()
        mine_keys = read_keys(folder / KEYS)
    except (OSError, UnicodeDecodeError):
        return  # already reported by the checks above
    for rel, team in teams:
        try:
            names = read_approvers(team / APPROVERS) if os.path.isfile(team / APPROVERS) else set()
            keys = read_keys(team / KEYS)
        except (OSError, UnicodeDecodeError) as exc:
            add("ledger-parity", rel, f"the team's approver list or keys cannot be read: {exc}")
            continue
        if not names and not keys:
            continue
        if names != mine_names:
            add("ledger-parity", rel, "the ledger's approver list does not name the same approvers as this team's")
        if keys != mine_keys:
            add("ledger-parity", rel, "the ledger's verify keys are not the same files as this team's")
