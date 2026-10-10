"""Upstream-authored Project-Specific Notes, synced into every surface (OrthodoxLLM Item 1).

agentteams treats an agent's ``## Project-Specific Notes`` as repo-owned and preserves it verbatim, so
rules researchteam itself writes there (history, literature-library, news-perspective, ...) never
reached derived repos except by hand-copying. researchteam now keeps them in a fenced block at the top
of each listed agent's Notes::

    ## Project-Specific Notes

    > ⚙️ **USER-EDITABLE** — ...

    <!-- >>> researchteam:notes — upstream-authored; synced by `researchteam update`. Edit upstream. -->
    ### Historical setting (...)
    ...
    <!-- <<< researchteam:notes -->

    ### A repo's own rule            <- outside the block: never touched

The source of truth is the block in upstream researchteam's ``.github/agents/<agent>.agent.md``.
``update`` writes it into the agent's file on every surface the repo carries: ``.github/agents``
(markdown), ``.claude/agents`` (markdown) and ``.goose/recipes`` (inside the recipe's indented
``instructions:`` block). Codex is projected from ``.github`` and follows automatically.

First adoption folds in hand-copied duplicates: an outside-block ``###`` subsection whose heading
matches one in the block, or a top-level bullet item identical to one in the block, is removed, since
the block now carries it. Nothing else outside the block is ever touched.

All functions expect LF line endings (``Path.read_text`` already translates CRLF). Files reached through
a symlink that resolves outside the repository are refused.
"""
from __future__ import annotations

import re
from pathlib import Path

NOTES_AGENTS = (
    "interpretation-advisor",
    "topic-scoping-expert",
    "literature-review-expert",
    "main-analysis-expert",
)
BEGIN = "<!-- >>> researchteam:notes — upstream-authored; synced by `researchteam update`. Edit upstream. -->"
END = "<!-- <<< researchteam:notes -->"
BEGIN_CORE = ">>> researchteam:notes"
END_CORE = "<<< researchteam:notes"
NOTES_HEADING = "## Project-Specific Notes"


def source_path(agent: str) -> str:
    """Where the upstream block lives (and where a derived repo's copilot surface keeps it)."""
    return f".github/agents/{agent}.agent.md"


def surfaces(root: Path, agent: str) -> list[tuple[Path, str]]:
    """``(file, indent)`` for every surface of ``agent`` present in ``root``."""
    cands = [(root / source_path(agent), ""), (root / ".claude" / "agents" / f"{agent}.md", ""),
             (root / ".goose" / "recipes" / f"{agent}.yaml", "  ")]
    return [(p, ind) for p, ind in cands if p.is_file() and inside(root, p)]


def inside(root: Path, path: Path) -> bool:
    """Whether ``path`` (following symlinks) stays inside ``root``: never write through a link out."""
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


class NotesError(ValueError):
    """A file or block that cannot be reconciled safely; the caller keeps the file as it is."""


def _notes_region(lines: list[str], indent: str) -> tuple[int, int]:
    """``(heading index, end index)`` of the Notes section at ``indent``; end is exclusive."""
    head = next((i for i, ln in enumerate(lines)
                 if ln.rstrip("\n").rstrip() == indent + NOTES_HEADING), None)
    if head is None:
        raise NotesError(f"no '{NOTES_HEADING}' heading")
    def ends(ln: str) -> bool:
        # the next level-2 heading; inside a Goose block scalar also the first line that leaves the
        # block (e.g. a following `extensions:` key) when Notes is the recipe's last section
        return ln.startswith(indent + "## ") or bool(indent and ln.strip() and not ln.startswith(indent))
    end = next((i for i in range(head + 1, len(lines)) if ends(lines[i])), len(lines))
    return head, end


def _block_span(lines: list[str], start: int, end: int) -> tuple[int, int] | None:
    """``(begin, end)`` marker line indices (inclusive) of the block within ``[start, end)``."""
    b = next((i for i in range(start, end) if BEGIN_CORE in lines[i]), None)
    if b is None:
        return None
    e = next((i for i in range(b + 1, end) if END_CORE in lines[i]), None)
    if e is None:
        raise NotesError("researchteam:notes block has no end marker")
    return b, e


def extract_block(text: str) -> str | None:
    """The block's inner text (unindented) from an upstream ``.github`` agent file, or None if it has
    none. Raises NotesError for a malformed block (no end marker before the next level-2 heading)."""
    lines = text.splitlines(keepends=True)
    try:
        head, end = _notes_region(lines, "")
    except NotesError:
        return None  # no Notes section: no block
    span = _block_span(lines, head + 1, end)  # a malformed block raises: never skipped silently
    if span is None:
        return None
    inner = "".join(lines[span[0] + 1:span[1]])
    if re.search(r"^ {0,3}## ", inner, re.M):
        raise NotesError("researchteam:notes block must not contain a level-2 heading")
    return inner.strip("\n") + "\n"


def _units(lines: list[str], indent: str) -> list[tuple[str, int, int]]:
    """Top-level units in ``lines``: ``("h:<heading>", start, end)`` for a ``###`` subsection and
    ``("b:<normalised text>", start, end)`` for a top-level bullet item (with its continuation)."""
    units: list[tuple[str, int, int]] = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith(indent + "### "):
            j = i + 1
            while j < len(lines) and not lines[j].startswith(indent + "### ") and BEGIN_CORE not in lines[j]:
                j += 1
            units.append(("h:" + ln[len(indent) + 4:].strip(), i, j))
            i = j
        elif ln.startswith(indent + "- "):
            j = i + 1
            while j < len(lines) and lines[j].startswith(indent + "  ") and lines[j].strip():
                j += 1
            text = " ".join(x.strip() for x in lines[i:j])
            units.append(("b:" + text, i, j))
            i = j
        else:
            i += 1
    return units


def apply_block(text: str, inner: str, indent: str = "") -> tuple[str, list[str]]:
    """Put ``inner`` into ``text``'s Notes block (creating it, folding duplicates) at ``indent``.

    Returns ``(new text, folded unit labels)``. Raises NotesError when the file has no Notes section.
    """
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    head, end = _notes_region(lines, indent)
    block = [indent + BEGIN + "\n"] + [(indent + ln if ln.strip() else "\n")
                                       for ln in inner.splitlines(keepends=True)] + [indent + END + "\n"]
    span = _block_span(lines, head + 1, end)
    folded: list[str] = []
    if span is not None:
        lines[span[0]:span[1] + 1] = block
        return "".join(lines), folded

    # First adoption: drop outside units the block now carries, then insert the block.
    wanted = {key for key, _, _ in _units([ln + "\n" if not ln.endswith("\n") else ln
                                           for ln in inner.splitlines(keepends=True)], "")}
    region = lines[head + 1:end]
    keep, i = [], 0
    for key, s_, e_ in _units(region, indent):
        if key in wanted:
            keep.extend(region[i:s_])
            folded.append(key[2:])
            i = e_
            # a removed unit leaves no extra blank line behind (seam only; other text untouched)
            while i < len(region) and not region[i].strip() and (not keep or not keep[-1].strip()):
                i += 1
    keep.extend(region[i:])
    region = keep
    # insert after the USER-EDITABLE blockquote (if any), else right under the heading
    at = 0
    while at < len(region) and not region[at].strip():
        at += 1
    if at < len(region) and region[at].lstrip().startswith(">"):
        while at < len(region) and region[at].lstrip().startswith(">"):
            at += 1
    else:
        at = 0
    before = ["\n"] if not (at and not region[at - 1].strip()) else []
    after = ["\n"] if at < len(region) and region[at].strip() else []
    lines[head + 1:end] = region[:at] + before + block + after + region[at:]
    return "".join(lines), folded
