"""Implementation of `researchteam init --adopt` (#59): scaffold around an existing, non-empty directory.

Invariants:

* **No existing file is modified**, with one exception. An existing ``.gitignore`` or ``CLAUDE.md`` with no
  ``researchteam:managed`` fence gets the managed block appended below its unchanged content
  (``ADOPT_APPEND_FENCED``).
* **No write follows a link.** New files are created with ``O_CREAT | O_EXCL | O_NOFOLLOW``, so a path that
  already exists in any form (including a dangling symlink) is refused at the moment of the write, not only by
  an earlier check. Appends open with ``O_NOFOLLOW``. A path under a symlinked or non-directory parent is a
  conflict and is skipped.
* **Fail before writing.** :func:`preflight` refuses, with nothing written, every condition that would
  otherwise fail half-way: a key file that is a symlink or directory, an unreadable ``brief.json``, or a
  ``CLAUDE.md`` / ``.gitignore`` that is not UTF-8. The ``.researchteam`` marker is written **last**, so a run
  that fails anyway can be retried.
* **Git is never staged or committed.** ``git init`` runs only when the target is not already inside a work
  tree. ``README.md`` / ``CLAUDE.md`` are rendered only when absent, so ``personalize`` never touches a file
  that was already there.
"""

import errno
import importlib.resources
import json
import os
import subprocess
import sys
from pathlib import Path

#: The ``fenced-preserve`` files adopt may append to (see ``_manifest.MERGE_STRATEGIES``).
ADOPT_APPEND_FENCED = (".gitignore", "CLAUDE.md")

#: Agent-infrastructure trees that ``materialize`` / ``update``'s agentteams pass regenerate.
_AGENT_TREES = (".github/agents/", ".claude/agents/", ".codex/", ".goose/", ".agentteams/")

#: Files adopt writes or reads outside the archive; each must be absent or a plain regular file.
_KEY_FILES = (".researchteam", "brief.json", "README.md", "CLAUDE.md", ".gitignore")


class AdoptError(Exception):
    """A condition under which ``init --adopt`` refuses before writing anything."""


class AdoptReport:
    """What ``init --adopt`` added, kept, appended to and skipped, and which paths a later sync will replace."""

    def __init__(self) -> None:
        self.added: list[str] = []
        self.kept: list[str] = []
        self.appended: list[str] = []
        self.conflicts: list[str] = []  # in the way: a directory, a symlink, or under a non-directory parent
        self.notes: list[str] = []
        self.profile: str | None = None  # brief.json layer2_profile, for at_risk()

    def at_risk(self) -> list[str]:
        """Kept or conflicting paths that ``researchteam update`` / ``materialize`` will replace wholesale."""
        from ._manifest import MERGE_STRATEGIES, managed_files_for

        managed = {p for p in managed_files_for(self.profile) if MERGE_STRATEGIES.get(p) != "fenced-preserve"}
        return sorted({p for p in self.kept + self.conflicts if p in managed or p.startswith(_AGENT_TREES)})

    def print(self) -> None:
        print(f"\n[researchteam] Adopt report: {len(self.added)} added, {len(self.kept)} existing kept unchanged, "
              f"{len(self.appended)} appended to, {len(self.conflicts)} conflicts.")
        for p in self.appended:
            print(f"  appended the researchteam:managed block to {p} (existing lines unchanged above it)")
        for p in self.conflicts:
            print(f"  CONFLICT {p}: an existing directory, symlink or file is in the way; kept it, scaffold skipped")
        risk = self.at_risk()
        if risk:
            print("  WARNING: these paths are framework-managed. They were kept now, but `researchteam update` / "
                  "`materialize` will replace them (writing through any symlink). Move or back them up first:")
            for p in risk:
                print(f"    {p}")
        others = [p for p in self.kept if p not in risk]
        if others:
            print(f"  kept {len(others)} other existing file(s) where the scaffold has a file of the same name:")
            for p in others:
                print(f"    {p}")
        for n in self.notes:
            print(f"  note: {n}")


def preflight(target: Path) -> dict:
    """Refuse (``AdoptError``) before any write; return the existing brief.json as a dict, or ``{}``."""
    for rel in _KEY_FILES:
        p = target / rel
        if p.is_symlink():
            raise AdoptError(f"{rel} is a symlink; adopt never writes through a link. Replace it with a regular "
                             "file (or remove it) and retry.")
        if p.exists() and not p.is_file():
            raise AdoptError(f"{rel} exists and is not a regular file; move it aside and retry.")
    for rel in ADOPT_APPEND_FENCED:
        p = target / rel
        if p.exists():
            try:
                p.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                raise AdoptError(f"{rel} is not UTF-8 text ({exc.reason}); adopt cannot append its managed "
                                 "block safely.") from exc
    brief = target / "brief.json"
    if not brief.exists():
        return {}
    try:
        data = json.loads(brief.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdoptError(f"the existing brief.json cannot be read as JSON ({exc}); fix it and retry.") from exc
    if not isinstance(data, dict):
        raise AdoptError("the existing brief.json is not a JSON object; fix it and retry.")
    return data


def populate_adopt(target: Path, tarball: bytes, members: set[str], links: list[str], ref: str,
                   remote_url: str | None, vulnscan_level: str | None, report: AdoptReport) -> None:
    """Add the scaffold around existing files, then the brief, identity files, git repo and (last) the marker."""
    from ._init_cmd import _MARKER_TEMPLATE, _extract, _seed_brief, warn_links
    from ._manifest import INIT_RENDER_TEMPLATES, INIT_SCAFFOLD_REPLACEMENTS, UPSTREAM_REPO
    from ._personalize import _load_template, _render, _split_fence, _wrap

    brief = preflight(target)
    print("[researchteam] Extracting template files (skipping every path that already exists) ...")
    warn_links(links)
    _extract(tarball, target, members, adopt=report)

    pkg = importlib.resources.files("researchteam") / "scaffold"
    for dest_rel, scaffold_name in INIT_SCAFFOLD_REPLACEMENTS.items():
        adopt_write(target, dest_rel, (pkg / scaffold_name).read_bytes(), report)

    if (target / "brief.json").exists():  # existence, not truthiness: a `{}` brief is still the user's
        report.kept.append("brief.json")
        if vulnscan_level is not None:
            report.notes.append("--vulnscan-level ignored; the existing brief.json is kept as is "
                                "(change it with: agentteams --set-vulnscan).")
    else:
        _seed_brief(target, vulnscan_level)  # preflight proved brief.json absent and not a link
        report.added.append("brief.json")
        brief = json.loads((target / "brief.json").read_text(encoding="utf-8"))

    # README.md / CLAUDE.md: render only what is absent (personalize never sees an existing file); an
    # existing unfenced CLAUDE.md gets the rendered managed block appended instead.
    for dest_rel, template_name in INIT_RENDER_TEMPLATES.items():
        rendered = _render(_load_template(template_name), brief)
        split = _split_fence(rendered)
        if (target / dest_rel).exists():
            if dest_rel in ADOPT_APPEND_FENCED and split is not None:
                _append_fenced(target / dest_rel, dest_rel, split[1], report)
            else:
                report.kept.append(dest_rel)
            continue
        content = (_wrap(split[0]) + split[1] + split[2]) if split is not None else _wrap(rendered)
        adopt_write(target, dest_rel, content.encode("utf-8"), report)

    inside = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=str(target),
                            capture_output=True, text=True)
    enclosing = (inside.returncode == 0 and inside.stdout.strip() == "true"
                 and not (target / ".git").exists())
    if enclosing:
        report.notes.append("the directory is inside an existing git work tree; no nested `git init` was run.")
        if remote_url:
            report.notes.append("--remote ignored; it would change the enclosing repository's remotes.")
            remote_url = None
    elif inside.returncode != 0 or inside.stdout.strip() != "true":
        subprocess.run(["git", "init"], cwd=str(target), check=True, capture_output=True)
        report.added.append(".git/ (git init)")
    if remote_url:
        has_origin = subprocess.run(["git", "remote", "get-url", "origin"], cwd=str(target),
                                    capture_output=True).returncode == 0
        if has_origin:
            report.notes.append("--remote ignored; this repository already has an 'origin'.")
        else:
            subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=str(target), check=True,
                           capture_output=True)

    # Last: once the marker exists the directory is a researchteam project and adopt refuses to re-run.
    adopt_write(target, ".researchteam", _MARKER_TEMPLATE.format(repo=UPSTREAM_REPO, ref=ref).encode(), report)
    if ".researchteam" not in report.added:
        raise OSError("could not create the .researchteam marker (a path appeared there during adopt)")
    report.profile = brief.get("layer2_profile")


def adopt_write(target: Path, rel: str, content: bytes, report: AdoptReport, mode: int = 0) -> None:
    """Add one file if absent; keep it, or append the managed block (``ADOPT_APPEND_FENCED``), if present."""
    from ._personalize import _split_fence

    dest = target / rel
    if _blocked(target, dest):
        report.conflicts.append(rel)
        return
    if dest.exists():
        split = _split_fence(content.decode("utf-8", errors="replace")) if rel in ADOPT_APPEND_FENCED else None
        if split is not None:
            _append_fenced(dest, rel, split[1], report)
        else:
            report.kept.append(rel)
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    perms = 0o755 if mode & 0o111 else 0o644
    try:
        fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, perms)
    except FileExistsError:  # appeared (or is a dangling link) since the check: never write through it
        report.conflicts.append(rel)
        return
    with os.fdopen(fd, "wb") as f:
        f.write(content)
    report.added.append(rel)


def _blocked(target: Path, dest: Path) -> bool:
    """True when ``dest`` is a directory or symlink, a parent inside ``target`` is a file or symlink, or it
    resolves outside ``target``."""
    if dest.is_symlink() or dest.is_dir():
        return True
    for parent in dest.parents:
        if parent == target:
            break
        if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
            return True
    return target.resolve() not in dest.resolve().parents


def _append_fenced(dest: Path, rel: str, managed_block: str, report: AdoptReport) -> None:
    """Append ``managed_block`` below ``dest``'s content unless ``dest`` already carries a managed fence."""
    from ._personalize import _split_fence

    try:
        fd = os.open(dest, os.O_RDWR | os.O_APPEND | os.O_NOFOLLOW)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            report.conflicts.append(rel)
            return
        raise
    with os.fdopen(fd, "r+b") as f:
        existing = f.read().decode("utf-8")
        if _split_fence(existing) is not None:
            report.kept.append(rel)  # already fenced: `researchteam update` keeps the block current
            return
        sep = "" if existing.endswith("\n") or not existing else "\n"
        f.write((sep + "\n" + managed_block).encode("utf-8"))
    report.appended.append(rel)


def run_adopt(target: Path, tarball: bytes, members: set[str], links: list[str], ref: str,
              remote_url: str | None, vulnscan_level: str | None) -> None:
    """``run_init``'s adopt branch: populate, report, and turn every failure into exit 1 with what was done."""
    report = AdoptReport()
    try:
        populate_adopt(target, tarball, members, links, ref, remote_url, vulnscan_level, report)
    except AdoptError as exc:
        print(f"Error: {exc}\n  Nothing was written.", file=sys.stderr)
        sys.exit(1)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"[researchteam] init --adopt failed: {exc}\n"
              "  No existing file was overwritten. The .researchteam marker was not written, so it is safe to "
              "retry. Done so far:\n"
              + "".join(f"    added {p}\n" for p in report.added)
              + "".join(f"    appended to {p}\n" for p in report.appended), file=sys.stderr)
        sys.exit(1)
    report.print()
