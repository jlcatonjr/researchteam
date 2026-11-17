"""``researchteam workflow-sync`` (#186): bring a derived repo's workflow up to the installed scaffold.

Two workflows are known (``WORKFLOWS``). ``autosync`` is the one ``init`` installs and the default.
``validate`` is opt-in: a read-only workflow that runs the bridge validator on pull requests, so the checks
inside ``validate`` (the term-index gate among them) cannot be skipped. What follows describes both, except
where it names one.

The autosync workflow is written at ``init`` and otherwise only by this command; the validate workflow is
written only by this command. ``update`` never touches ``.github/workflows/``. A whole-file copy of a scaffold
would also replace the repository's trigger section, which for autosync can turn a weekly schedule on (or off)
without anyone deciding to. This command takes everything from the scaffold **except the top-level** ``on:``
**block**, which it keeps exactly as the repository has it.

With no workflow present it writes the scaffold as shipped (for autosync, the schedule is commented out, so it
runs only when dispatched). For the validate workflow it refuses to keep an ``on:`` block that names
``pull_request_target`` or ``workflow_run``: either would run a fork's scripts with more than a read-only token.
It shows a unified diff and asks before writing unless ``--yes`` is given; ``--dry-run`` writes
nothing. It refuses a symlink, a non-regular or non-UTF-8 file, a file without exactly one block-style top-level
``on:`` key, and column-0 content other than comments inside that block. It never writes through a link.
"""

import difflib
import importlib.resources
import os
import re
import sys
from pathlib import Path
from typing import NamedTuple

WORKFLOW = ".github/workflows/agentteams-sync.yml"
SCAFFOLD = "agentteams-sync-derived.yml"


class Workflow(NamedTuple):
    """One workflow this command knows: where it lives, its packaged scaffold, and what an absent one gets."""
    path: str
    scaffold: str
    when_absent: str


# The first entry is the default.
WORKFLOWS = {
    "autosync": Workflow(WORKFLOW, SCAFFOLD, "Its weekly schedule is commented out, so autosync runs only when "
                         "dispatched until you enable it."),
    "validate": Workflow(".github/workflows/researchteam-validate.yml", "researchteam-validate-derived.yml",
                         "It is read-only and runs `bash scripts/claude_researchteam_bridge.sh validate` on pull "
                         "requests and on pushes to main."),
}
# Triggers that hand a workflow more than a fork's read-only token. The validate workflow runs the scripts of
# the commit under test, so it must never run on one of these.
PRIVILEGED_TRIGGERS = ("pull_request_target", "workflow_run")

# A top-level ``on`` key: ``on:``, ``"on":`` or ``'on':``, optionally followed by a comment.
_ON_KEY = re.compile(r"""^(on|"on"|'on')\s*:\s*(#.*)?$""")
# Any other top-level key (column 0, not a comment, not a document marker).
_TOP_KEY = re.compile(r"^[^\s#-][^:]*:")


class WorkflowSyncError(Exception):
    """A condition under which ``workflow-sync`` refuses before writing anything."""


def on_block(text: str) -> tuple[int, int]:
    """``(start, end)`` line indexes of the top-level ``on:`` block.

    The block runs from the ``on:`` line to the next top-level key. Blank lines and column-0 comments just
    before that key belong to the key, so they are left out. Raises ``WorkflowSyncError`` when there is no
    block-style top-level ``on:`` (for example ``on: [push]`` on one line), or there is more than one.
    """
    lines = text.splitlines(keepends=True)
    starts = [i for i, ln in enumerate(lines) if _ON_KEY.match(ln.rstrip("\n"))]
    if len(starts) != 1:
        raise WorkflowSyncError(
            "expected exactly one block-style top-level `on:` key, found " + str(len(starts)))
    start = starts[0]
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if _TOP_KEY.match(lines[i]):
            end = i
            break
    while end > start + 1 and (not lines[end - 1].strip() or lines[end - 1].startswith("#")):
        end -= 1
    # Inside the block, only blank lines, indented lines and column-0 comments belong to `on:`. Anything else at
    # column 0 (a `- ` item, a `---` document marker, ...) would be carried into the merged file, so refuse.
    stray = [i + 1 for i in range(start + 1, end)
             if lines[i].strip() and not lines[i][0].isspace() and not lines[i].startswith("#")]
    if stray:
        raise WorkflowSyncError(f"unexpected column-0 content inside the `on:` block (line {stray[0]})")
    return start, end


def merge(scaffold: str, existing: str) -> str:
    """The scaffold with its ``on:`` block replaced by the existing workflow's ``on:`` block."""
    s_lines = scaffold.splitlines(keepends=True)
    e_lines = existing.splitlines(keepends=True)
    s0, s1 = on_block(scaffold)
    e0, e1 = on_block(existing)
    kept = e_lines[e0:e1]
    if kept and not kept[-1].endswith("\n"):
        kept[-1] += "\n"
    return "".join(s_lines[:s0] + kept + s_lines[s1:])


def load_scaffold(name: str = SCAFFOLD) -> str:
    return (importlib.resources.files("researchteam") / "scaffold" / name).read_text(encoding="utf-8")


def _known(which: str) -> Workflow:
    if which not in WORKFLOWS:
        raise ValueError(f"unknown workflow {which!r}; one of: {', '.join(WORKFLOWS)}")
    return WORKFLOWS[which]


def _refuse_privileged_triggers(existing: str) -> None:
    """Refuse an ``on:`` block that would run the validate job with more than a read-only token.

    Any mention of a privileged trigger in the block, outside a comment, is refused: as a key, a list item or
    inside a flow collection. That can refuse a harmless mention (a branch named after a trigger); the
    message says what to remove. It is a guard against a mistake, not a YAML analysis: an alias or anchor
    defined elsewhere is not followed, nor is a name written with escapes, and the diff is always shown.

    A comment starts at a ``#`` that begins the line or follows white space, as in YAML. A ``#`` inside a
    word (a branch called ``a#b``) does not, so text after it is still checked.
    """
    start, end = on_block(existing)
    block = [re.split(r"(?:^|\s)#", ln, maxsplit=1)[0] for ln in existing.splitlines()[start:end]]
    used = [t for t in PRIVILEGED_TRIGGERS if any(re.search(rf"\b{re.escape(t)}\b", ln) for ln in block)]
    if used:
        raise WorkflowSyncError(f"its `on:` block uses {', '.join(used)}, which would run the scripts of an "
                                "untrusted commit with a privileged token; remove that trigger first")


def plan(root: Path, scaffold: str | None = None, which: str = "autosync") -> tuple[str | None, str]:
    """``(current, proposed)`` for ``root``; ``current`` is None when no workflow exists yet."""
    workflow, scaffold_name, _ = _known(which)
    scaffold = load_scaffold(scaffold_name) if scaffold is None else scaffold
    path = root / workflow
    if path.is_symlink():
        raise WorkflowSyncError(f"{workflow} is a symlink; replace it with a regular file and retry.")
    for parent in path.relative_to(root).parents:
        p = root / parent
        if parent != Path(".") and p.is_symlink():
            raise WorkflowSyncError(f"{parent}/ is a symlink; workflow-sync never writes through a link.")
    if path.exists() and not path.is_file():
        raise WorkflowSyncError(f"{workflow} exists and is not a regular file.")
    if not path.exists():
        return None, scaffold
    try:
        current = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise WorkflowSyncError(f"{workflow} is not UTF-8 text ({exc.reason}).") from exc
    try:
        if which == "validate":
            _refuse_privileged_triggers(current)
        return current, merge(scaffold, current)
    except WorkflowSyncError as exc:
        raise WorkflowSyncError(f"{workflow}: {exc}; port the scaffold's changes by hand.") from exc


def _write(path: Path, content: str, workflow: str) -> None:
    """Write without following a link: a new temp file (``O_EXCL | O_NOFOLLOW``), then ``os.replace``.

    A regular temp file left by an interrupted run is removed first; a temp path that is a link or a directory is
    refused. An existing workflow's permission bits are kept.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.workflow-sync.tmp")
    if tmp.is_symlink() or (tmp.exists() and not tmp.is_file()):
        raise WorkflowSyncError(f"{tmp.name} beside the workflow is a link or a directory; remove it and retry.")
    if tmp.exists():
        tmp.unlink()  # left by an interrupted run
    mode = (path.stat().st_mode & 0o777) if path.is_file() and not path.is_symlink() else 0o644
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            os.fchmod(f.fileno(), mode)  # the umask may have narrowed the O_CREAT mode
            f.write(content)
        if path.is_symlink():
            raise WorkflowSyncError(f"{workflow} became a symlink during the run; nothing written.")
        os.replace(tmp, path)
    finally:
        if tmp.is_file() and not tmp.is_symlink():
            tmp.unlink()


def run_workflow_sync(root: Path, yes: bool = False, dry_run: bool = False, which: str = "autosync") -> int:
    workflow, _, when_absent = _known(which)
    try:
        current, proposed = plan(root, which=which)
    except WorkflowSyncError as exc:
        print(f"[researchteam] workflow-sync: {exc} Nothing was written.", file=sys.stderr)
        return 1
    if current == proposed:
        print(f"[researchteam] {workflow} already matches the scaffold (its own `on:` block kept). Nothing to do.")
        return 0
    diff = difflib.unified_diff((current or "").splitlines(keepends=True), proposed.splitlines(keepends=True),
                                fromfile=f"a/{workflow}", tofile=f"b/{workflow}")
    sys.stdout.writelines(diff)
    if current is None:
        print(f"\n[researchteam] {workflow} does not exist; this writes the scaffold as shipped. {when_absent}")
    else:
        print(f"\n[researchteam] Your `on:` block in {workflow} is kept as it is; everything else comes from the "
              "scaffold.")
    print("[researchteam] A workflow change gets this repository's own @security review.")
    if dry_run:
        print("[researchteam] --dry-run: nothing written.")
        return 0
    if not yes:
        try:
            answer = input("Apply? [y/N] ").strip().lower()
        except EOFError:
            # No terminal to answer from (a script, a pipe, CI). Say so: "Not applied." alone reads as a choice.
            print(f"\n[researchteam] workflow-sync: no answer on standard input, so {workflow} was not "
                  "written. Run it in a terminal, or pass --yes to apply without asking.", file=sys.stderr)
            return 1
        if answer != "y":
            print("[researchteam] Not applied.")
            return 1
    try:
        _write(root / workflow, proposed, workflow)
    except (OSError, WorkflowSyncError) as exc:
        print(f"[researchteam] workflow-sync failed: {exc}", file=sys.stderr)
        return 1
    print(f"[researchteam] Wrote {workflow}.")
    return 0
