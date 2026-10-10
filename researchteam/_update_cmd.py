"""Implementation of `researchteam update`."""

import datetime
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ._manifest import (
    BRIEF_PLACEHOLDER,
    FENCE_CORE_BEGIN,
    FENCE_CORE_END,
    MERGE_STRATEGIES,
    UPSTREAM_REPO,
    managed_files_for,
)
from ._fetch import fetch_raw


def _split_fence(text: str) -> tuple[str, str, str] | None:
    """Split ``text`` around the researchteam:managed fence.

    Returns ``(pre, managed, post)`` where ``managed`` INCLUDES both marker lines, or ``None``
    when a well-formed fence (BEGIN then END, in order) is absent. A marker line is recognized by
    the presence of its sentinel CORE anywhere in the stripped line, so BOTH the shell-comment
    idiom (``# >>> researchteam:managed …``) used by ``.gitignore`` and the HTML-comment idiom
    (``<!-- >>> researchteam:managed … -->``) used by markdown files match, along with any
    self-documenting trailing prose. ``>>>`` vs ``<<<`` keep BEGIN and END unambiguous.
    """
    lines = text.splitlines(keepends=True)
    begin_idx = end_idx = None
    for i, ln in enumerate(lines):
        stripped = ln.strip()
        if begin_idx is None and FENCE_CORE_BEGIN in stripped:
            begin_idx = i
        elif begin_idx is not None and FENCE_CORE_END in stripped:
            end_idx = i
            break
    if begin_idx is None or end_idx is None:
        return None
    pre = "".join(lines[:begin_idx])
    managed = "".join(lines[begin_idx : end_idx + 1])
    post = "".join(lines[end_idx + 1 :])
    return pre, managed, post


def _fence_body(managed_block: str) -> str:
    """Return the managed block with its two marker lines removed (the payload only)."""
    lines = managed_block.splitlines(keepends=True)
    return "".join(lines[1:-1])


_NOTES_HEADING_RE = re.compile(r"^## Project-Specific Notes[ \t]*$", re.M)


def _split_above_notes(text: str) -> tuple[str, str] | None:
    """``(upstream-owned head, repo-owned tail)`` split at the Notes heading, or None without one."""
    m = _NOTES_HEADING_RE.search(text)
    return (text[:m.start()], text[m.start():]) if m else None


def _reconcile_above_notes(rel_path: str, local: str, remote: str) -> tuple[str | None, list[str]]:
    """Reconcile an ``above-notes`` file: upstream's head + the repo's own Notes section and tail.

    Returns ``(content or None, diff of the upstream-owned part)``. ``None`` with a non-empty diff
    list means the upstream copy has no Notes heading, so the local file is kept (a warning line is
    returned as the "diff"); ``None`` with an empty list means nothing to do.
    """
    r = _split_above_notes(remote)
    if r is None:
        msg = f"  [above-notes] {rel_path}: upstream copy has no Notes heading; kept local unchanged.\n"
        print(msg, end="")
        return None, [msg]
    l = _split_above_notes(local)
    l_head, l_tail = l if l is not None else (local, r[1])  # no local Notes yet: adopt upstream's
    new = r[0] + l_tail
    if new == local:
        return None, []
    diff = list(difflib.unified_diff(l_head.splitlines(keepends=True), r[0].splitlines(keepends=True),
                                     fromfile=f"local/{rel_path} (above Notes)",
                                     tofile=f"upstream/{rel_path} (above Notes)"))
    return new, diff


def _new_backup_stamp() -> str:
    """A per-run backup folder name (UTC, microseconds, so two runs never share one)."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


_BACKUP_STAMP = _new_backup_stamp()  # reset at the start of every run_update


def _backup(root: Path, rel_path: str, content: str) -> Path:
    """Save ``content`` under the gitignored ``tmp/researchteam-backups/<run stamp>/<rel_path>``."""
    dest = root / "tmp" / "researchteam-backups" / _BACKUP_STAMP / rel_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    return dest


_GRANT_KEYS = ("tools", "agents")


def _front_matter_grants(text: str) -> dict[str, set[str]]:
    """``{"tools"|"agents"|"handoffs": names}`` declared in a markdown agent's front matter.

    A small reader for the shapes agentteams emits (``key: ['a', 'b']`` and ``agent: x`` under
    ``handoffs:``); stdlib only. Anything it cannot read counts as no grant, so an unreadable upstream
    front matter never looks like a narrowing.
    """
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    out: dict[str, set[str]] = {k: set() for k in (*_GRANT_KEYS, "handoffs")}
    if not m:
        return out
    for line in m.group(1).splitlines():
        km = re.match(r"^(tools|agents):\s*\[(.*)\]\s*$", line)
        if km:
            out[km.group(1)] |= {x.strip().strip("'\"") for x in km.group(2).split(",") if x.strip()}
        hm = re.match(r"^\s+agent:\s*(\S+)\s*$", line)
        if hm:
            out["handoffs"].add(hm.group(1).strip("'\""))
    return out


def _grant_widening(local: str, remote: str) -> list[str]:
    """Capability grants upstream's front matter adds over the local one (C-3: widening needs review)."""
    old, new = _front_matter_grants(local), _front_matter_grants(remote)
    return [f"{k}: +{', '.join(sorted(new[k] - old[k]))}" for k in new if new[k] - old[k]]


def _reconcile_fenced(
    rel_path: str, local_content: str, remote_content: str, yes: bool
) -> tuple[str | None, list[str], str]:
    """Reconcile a ``fenced-preserve`` file without deleting derived-only lines.

    Returns ``(write_content, preview_diff, warn)``:
      * ``write_content is None`` — nothing to write (already current, or a safe no-op skip).
      * ``preview_diff`` — the unified diff to show interactively; for the fenced case it covers
        ONLY the managed block, so derived lines never render as spurious deletions.
      * ``warn`` — a human-readable note printed regardless of mode (empty string if none).
    """
    remote_split = _split_fence(remote_content)
    if remote_split is None:
        # Upstream copy is not fenced yet. A preserve strategy must never fall back to a wholesale
        # overwrite — that is the exact silent-deletion this fix removes. Keep local, warn.
        return None, [], (
            "upstream copy has no researchteam:managed fence; kept local unchanged "
            "(fenced-preserve refuses to wholesale-overwrite)."
        )
    _, remote_managed, _ = remote_split

    local_split = _split_fence(local_content)
    if local_split is not None:
        local_pre, local_managed, local_post = local_split
        if local_managed == remote_managed:
            return None, [], ""  # managed region already current — idempotent no-op
        new_content = local_pre + remote_managed + local_post
        diff = list(
            difflib.unified_diff(
                local_managed.splitlines(keepends=True),
                remote_managed.splitlines(keepends=True),
                fromfile=f"local/{rel_path} (managed block)",
                tofile=f"upstream/{rel_path} (managed block)",
            )
        )
        return new_content, diff, ""

    # Local has no fence — migration path.
    if local_content.strip() == _fence_body(remote_managed).strip():
        # Local is byte-equal (modulo trailing whitespace) to the upstream body: this is a
        # first-time wrap with no derived additions, so adopting the fenced upstream loses nothing.
        diff = list(
            difflib.unified_diff(
                local_content.splitlines(keepends=True),
                remote_content.splitlines(keepends=True),
                fromfile=f"local/{rel_path}",
                tofile=f"upstream/{rel_path} (fenced)",
            )
        )
        return remote_content, diff, ""

    # Local is unfenced AND diverges from upstream — it may carry derived-only lines. Never wipe
    # it under the blind path; require an explicit interactive approval that shows the full diff.
    if yes:
        return None, [], (
            "local copy is unfenced and diverges from upstream; kept as-is so derived lines are "
            "not deleted. Add the researchteam:managed fence markers to opt this file into sync."
        )
    diff = list(
        difflib.unified_diff(
            local_content.splitlines(keepends=True),
            remote_content.splitlines(keepends=True),
            fromfile=f"local/{rel_path}",
            tofile=f"upstream/{rel_path} (fenced)",
        )
    )
    return remote_content, diff, (
        "local copy is unfenced and diverges from upstream — approving REPLACES it wholesale "
        "(any derived lines shown as deletions below will be lost)."
    )


def _read_brief_profile(root: Path) -> str | None:
    """Return the brief's ``layer2_profile`` (``"scholarly"`` | ``"generic"``) or ``None``.

    A missing brief, unreadable JSON, or an absent field all return ``None`` so the caller falls
    back to the scholarly default (``managed_files_for(None)``).
    """
    brief = root / "brief.json"
    if not brief.exists():
        return None
    try:
        data = json.loads(brief.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    value = data.get("layer2_profile")
    return value if isinstance(value, str) else None


def _brief_has_placeholder(root: Path) -> bool:
    """True when brief.json still carries the scaffold placeholder identity.

    Running the layer-1 agentteams pass in that state would bake ``<YOUR PROJECT NAME>`` into every
    generated agent/persona file, so ``update`` and ``materialize`` refuse until the brief is
    edited.
    """
    brief = root / "brief.json"
    if not brief.exists():
        return False
    try:
        return BRIEF_PLACEHOLDER in brief.read_text(encoding="utf-8")
    except OSError:
        return False


def run_update(
    root: Path,
    ref: str,
    yes: bool,
    dry_run: bool,
    layer2_only: bool,
    layer1_only: bool = False,
) -> None:
    global _BACKUP_STAMP
    _BACKUP_STAMP = _new_backup_stamp()  # one backup folder per run
    if layer1_only and layer2_only:
        sys.exit("[researchteam] --layer1-only and --layer2-only are mutually exclusive.")

    layer1 = layer1_enabled(root)
    if layer1_only and not layer1:
        print("[researchteam] .researchteam declares layer1 = off: nothing to do for --layer1-only.")
        return
    if not layer1:
        print("[researchteam] .researchteam declares layer1 = off: syncing layer 2 only "
              "(no agentteams pass for this repository).")
    if layer1_only:
        # Integrate the current agent state only — the union-descriptor agentteams merge with
        # NO layer-2 file sync. This is the safe way to keep agent infrastructure integrated on
        # the upstream repo (a layer-2 sync there would overwrite local managed-file edits with
        # the older upstream versions). Used by the auto-integration git hook.
        print("[researchteam] Layer-1 only: integrating current agent state (no file sync) ...")
        _run_agentteams(root, yes=yes, dry_run=dry_run)
        # Native claude/goose surfaces too (merge mode), so their generated MCP/sandbox/hook output keeps up.
        _render_native_surfaces(root, yes=yes, dry_run=dry_run, overwrite=False)
        # The merge may change canonical agents; keep the Codex projection in step.
        _refresh_codex(root, dry_run=dry_run)
        # Bridges before the upstream Notes sync, so the Notes blocks are always written last.
        _merge_bridges(root, dry_run)
        from ._personalize import is_upstream
        if is_upstream(root):
            # Upstream is the source of the researchteam:notes blocks: carry its .github copies into
            # its own .claude/.goose surfaces (derived repos get them in the layer-2 sync).
            _sync_notes(root, None, yes=True, dry_run=dry_run)
        _print_frozen_summary(root, dry_run)
        return

    profile = _read_brief_profile(root)
    managed = managed_files_for(profile)
    print(
        f"[researchteam] Syncing layer-2 files from {UPSTREAM_REPO}@{ref} "
        f"(layer2_profile={profile or 'scholarly'}, {len(managed)} managed files) ..."
    )

    updated: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []

    for rel_path in managed:
        local_path = root / rel_path
        try:
            remote_content = fetch_raw(UPSTREAM_REPO, ref, rel_path)
        except RuntimeError as exc:
            errors.append(str(exc))
            continue

        if local_path.exists():
            local_content = local_path.read_text(encoding="utf-8")
            strategy = MERGE_STRATEGIES.get(rel_path, "overwrite")

            if strategy == "above-notes":
                write_content, diff_lines = _reconcile_above_notes(rel_path, local_content, remote_content)
                if write_content is None:
                    if diff_lines:  # upstream copy has no Notes heading: kept local, warned
                        skipped.append(rel_path)
                    continue
                widening = _grant_widening(local_content, remote_content)
                if widening:
                    # Constitutional C-3: widening a declared grant is a privileged change. Never apply
                    # it unattended; interactively the operator sees it in the prompt below.
                    print(f"  [above-notes] {rel_path}: upstream WIDENS capability grants ({'; '.join(widening)})")
                    if yes and not dry_run:
                        print("    kept local unchanged; re-run `researchteam update` interactively "
                              "(without --yes) to review and accept it.")
                        skipped.append(rel_path)
                        continue
            elif strategy == "fenced-preserve":
                write_content, diff_lines, warn = _reconcile_fenced(
                    rel_path, local_content, remote_content, yes
                )
                if warn:
                    print(f"  [fenced-preserve] {rel_path}: {warn}")
                if write_content is None:
                    # Already current, or a safe no-op skip (degrade/migration keeps local).
                    if warn:
                        skipped.append(rel_path)
                    continue
            else:
                if local_content == remote_content:
                    continue  # identical — nothing to do
                write_content = remote_content
                diff_lines = list(
                    difflib.unified_diff(
                        local_content.splitlines(keepends=True),
                        remote_content.splitlines(keepends=True),
                        fromfile=f"local/{rel_path}",
                        tofile=f"upstream/{rel_path}",
                    )
                )

            if dry_run:
                print(f"  [dry-run] Would update: {rel_path}")
                updated.append(rel_path)
                continue

            if not yes:
                print(f"\n--- {rel_path} ---")
                preview = diff_lines[:50]
                print("".join(preview), end="")
                if len(diff_lines) > 50:
                    print(f"  ... ({len(diff_lines) - 50} more lines)")
                answer = input("Apply? [y/N] ").strip().lower()
                if answer != "y":
                    skipped.append(rel_path)
                    print(f"  Skipped {rel_path}")
                    continue

            if strategy == "above-notes":
                # The upstream-owned part is replaced, never merged: keep the old file and show what
                # changed, even unattended (repo rules belong in Notes, which stay as they are).
                saved = _backup(root, rel_path, local_content)
                print(f"  [above-notes] {rel_path}: upstream part replaced; previous file saved to "
                      f"{saved.relative_to(root)}")
                if yes:
                    print("".join(diff_lines[:50]), end="")
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_text(write_content, encoding="utf-8")
            if rel_path.endswith(".sh"):  # preserve executability of managed shell scripts
                local_path.chmod(local_path.stat().st_mode | 0o111)
            updated.append(rel_path)
            print(f"  Updated {rel_path}")
        else:
            if dry_run:
                print(f"  [dry-run] Would create: {rel_path}")
                updated.append(rel_path)
                continue

            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_text(remote_content, encoding="utf-8")
            if rel_path.endswith(".sh"):  # preserve executability of managed shell scripts
                local_path.chmod(local_path.stat().st_mode | 0o111)
            updated.append(rel_path)
            print(f"  Created {rel_path}")

    if (profile or "scholarly").strip().lower() != "generic":
        _sync_notes(root, ref, yes=yes, dry_run=dry_run)

    # Summary
    if errors:
        print("\n[researchteam] Fetch errors:")
        for err in errors:
            print(f"  {err}", file=sys.stderr)

    verb = "would update" if dry_run else "updated"
    print(
        f"\n[researchteam] Layer-2 sync complete: "
        f"{len(updated)} {verb}, {len(skipped)} skipped, {len(errors)} errors."
    )

    note = _toolchain_hook_note(root)
    if note:
        print(note)

    if layer2_only or not layer1:
        return

    # Layer-1: delegate to agentteams
    _run_agentteams(root, yes=yes, dry_run=dry_run)
    # Native claude/goose surfaces too (merge mode), so their generated MCP/sandbox/hook output keeps up.
    _render_native_surfaces(root, yes=yes, dry_run=dry_run, overwrite=False)
    # The merge may change canonical agents; keep the Codex projection in step.
    _refresh_codex(root, dry_run=dry_run)
    _merge_bridges(root, dry_run)
    _print_frozen_summary(root, dry_run)


def _merge_bridges(root: Path, dry_run: bool) -> None:
    """Refresh every recorded copilot-vscode bridge after layer 1 (non-destructive ``--bridge-merge``).

    Layer 1 rewrites canonical agents on every run (e.g. the live vulnerability-watch section of
    ``security.agent.md``), which left each bridge stale until someone merged it by hand and made
    ``doctor --drift`` warn every time. A failed merge is reported, never fatal: the bridge just stays
    as it was, and ``doctor --drift`` still shows it.
    """
    from ._drift import bridge_frameworks

    frameworks = bridge_frameworks(root)
    if not frameworks:
        return
    if dry_run:
        print(f"[researchteam] [dry-run] Would refresh bridges: {', '.join(frameworks)}")
        return
    exe = _preflight_agentteams()
    for fw in frameworks:
        r = subprocess.run([exe, "--bridge-from", ".github/agents", "--framework", fw, "--output", ".",
                            "--bridge-merge"], cwd=str(root), capture_output=True, text=True)
        if r.returncode == 0:
            print(f"[researchteam] bridge copilot-vscode→{fw}: merged")
        else:
            tail = ((r.stderr or r.stdout).strip().splitlines() or ["(no output)"])[-1]
            print(f"[researchteam] bridge copilot-vscode→{fw}: --bridge-merge failed ({tail[:200]}); "
                  "left as it was", file=sys.stderr)


def _sync_notes(root: Path, ref: str | None, yes: bool, dry_run: bool) -> None:
    """Write each NOTES_AGENTS agent's upstream researchteam:notes block into every surface it has.

    ``ref`` names the upstream researchteam ref to read the blocks from; ``None`` reads this repo's
    own ``.github`` copies (the upstream repository itself). Repo-owned Notes outside the block are
    never touched; hand-copied duplicates are folded on first adoption (see ``_notes``).
    """
    from ._notes import NOTES_AGENTS, NotesError, apply_block, extract_block, source_path, surfaces

    changed = 0
    for agent in NOTES_AGENTS:
        rel = source_path(agent)
        try:
            source = (root / rel).read_text(encoding="utf-8") if ref is None else fetch_raw(UPSTREAM_REPO, ref, rel)
            inner = extract_block(source)
        except (OSError, RuntimeError, NotesError) as exc:
            print(f"  [notes] {agent}: upstream block unavailable ({exc}); surfaces left as they are")
            continue
        if inner is None:
            continue  # upstream carries no block for this agent (yet)
        for path, indent in surfaces(root, agent):
            shown = path.relative_to(root)
            text = path.read_text(encoding="utf-8")
            try:
                new, folded = apply_block(text, inner, indent)
            except NotesError as exc:
                print(f"  [notes] {shown}: {exc}; left as it is")
                continue
            if new == text:
                continue
            if dry_run:
                print(f"  [dry-run] Would sync upstream Notes into {shown}")
                changed += 1
                continue
            if not yes:
                diff = list(difflib.unified_diff(text.splitlines(keepends=True), new.splitlines(keepends=True),
                                                 fromfile=f"local/{shown}", tofile=f"synced/{shown}"))
                print(f"\n--- {shown} (upstream Notes block) ---")
                print("".join(diff[:50]), end="")
                if input("Apply? [y/N] ").strip().lower() != "y":
                    print(f"  Skipped {shown}")
                    continue
            saved = _backup(root, str(shown), text)
            path.write_text(new, encoding="utf-8")  # surfaces() only lists paths inside root
            changed += 1
            fold = f"; folded hand-copied: {', '.join(f[:60] for f in folded)}" if folded else ""
            print(f"  [notes] synced upstream Notes into {shown} (previous: {saved.relative_to(root)}){fold}")
    if changed:
        print(f"[researchteam] Upstream Notes blocks: {changed} file(s) {'would change' if dry_run else 'synced'}.")


def _print_frozen_summary(root: Path, dry_run: bool) -> None:
    """Report the sections agentteams' shrink guard keeps frozen, per the latest report of every surface."""
    if dry_run:
        return
    from ._drift import frozen_summary
    print(frozen_summary(root))


# Launchers that already passed _preflight_agentteams in this process; a materialize renders several
# surfaces and must not re-probe (and re-print provenance for) the same launcher each time.
_VERIFIED_LAUNCHERS: set[str] = set()


TOOLCHAIN_HOOK_SCRIPT = "scripts/check_toolchain.py"
TOOLCHAIN_HOOK_EXAMPLE = ".claude/settings.toolchain.example.json"


def _toolchain_hook_installed(root: Path) -> bool:
    """Whether .claude/settings(.local).json runs the toolchain check at SessionStart."""
    for name in ("settings.json", "settings.local.json"):
        try:
            data = json.loads((root / ".claude" / name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        hooks = data.get("hooks") if isinstance(data, dict) else None
        entries = hooks.get("SessionStart") if isinstance(hooks, dict) else None
        for entry in entries if isinstance(entries, list) else []:
            inner = entry.get("hooks") if isinstance(entry, dict) else None
            for hook in inner if isinstance(inner, list) else []:
                if isinstance(hook, dict) and TOOLCHAIN_HOOK_SCRIPT in str(hook.get("command", "")):
                    return True
    return False


def _toolchain_hook_note(root: Path) -> str:
    """A nudge (printed on every update) while the toolchain check is present but not wired to SessionStart.

    researchteam never edits ``.claude/settings.json`` (hooks run code; merging them is an operator
    step, the same rule agentteams follows), so it only says what to merge.
    """
    if not (root / TOOLCHAIN_HOOK_SCRIPT).exists() or _toolchain_hook_installed(root):
        return ""
    return (
        "[researchteam] note: the toolchain check is not wired to SessionStart. To be warned at the\n"
        f"  start of each Claude session when researchteam/agentteams drift from toolchain.lock, merge\n"
        f"  the SessionStart entry from {TOOLCHAIN_HOOK_EXAMPLE} into .claude/settings.json."
    )


_LAYER1_OFF = {"off", "false", "no", "0"}


def layer1_enabled(root: Path) -> bool:
    """False when ``.researchteam`` declares ``layer1 = off``: a repo with no agentteams descriptor
    (brief.json / _build-description.json) whose agent files are maintained by hand, so `update`
    syncs layer 2 only instead of failing at layer 1."""
    try:
        text = (root / ".researchteam").read_text(encoding="utf-8")
    except OSError:
        return True
    m = re.search(r"^layer1\s*=\s*(\S+)", text, re.M)
    return not (m and m.group(1).strip("\"'").lower() in _LAYER1_OFF)


def _resolve_agentteams() -> tuple[str | None, str]:
    """``(launcher, where)``: the ``agentteams`` beside this interpreter first, else the PATH one.

    researchteam runs the agentteams installed in its OWN environment when there is one, so an
    unactivated ``.venv/bin/researchteam`` (e.g. from ``scripts/bootstrap_toolchain.sh``) runs the
    pinned agentteams, not whichever one happens to come first on PATH. ``sys.executable`` is not
    resolved: a venv's python is a symlink, and its ``bin/`` is the environment's.
    """
    sibling = Path(sys.executable).parent / "agentteams"
    if sibling.is_file() and os.access(sibling, os.X_OK):
        return str(sibling), "beside this researchteam"
    exe = shutil.which("agentteams")
    return exe, "from PATH (none installed beside this researchteam)"


def _preflight_agentteams() -> str:
    """Resolve and liveness-check the `agentteams` console script before shelling out.

    Converts the opaque failure modes of this integration into one-line, actionable
    errors instead of a raw ``ModuleNotFoundError`` traceback or a silently wrong render:
      1. `agentteams` absent from PATH.
      2. `agentteams` present but not runnable — the signature of a stale *editable*
         install whose finder points at a deleted path (e.g. a temporary git worktree).
      3. `agentteams` runnable but not reviewed code: an editable checkout off origin/main or
         with uncommitted sources, or a checkout shadowing the install
         (see ``_agentteams_provenance``; CA-033).

    The ``--version`` probe is a genuine import assertion: the console-script entry point
    is ``build_team:main``, so ``--version`` must import ``build_team`` before argparse
    runs. A green probe therefore proves the resolved interpreter can import the module —
    which is exactly the invariant a bare ``sys.executable`` invocation would violate here
    (researchteam's venv does not have ``build_team`` installed).

    Resolution: the agentteams beside ``sys.executable`` first, else PATH (``_resolve_agentteams``).

    Returns the resolved absolute path to the console script.
    """
    exe, where = _resolve_agentteams()
    if exe is not None and exe in _VERIFIED_LAUNCHERS:
        return exe
    if exe is not None:
        print(f"[researchteam] agentteams: {exe} ({where})")
    if exe is None:
        sys.exit(
            "[researchteam] Layer-1 update needs 'agentteams', found neither beside this researchteam\n"
            f"  ({Path(sys.executable).parent}) nor on PATH. In a derived repo:\n"
            "    bash scripts/bootstrap_toolchain.sh   (installs the pinned toolchain into .venv)\n"
            "  Install it into an environment on your PATH (agentteams pinned to a merged commit):\n"
            '    pip install "researchteam[update] @ git+https://github.com/jlcatonjr/researchteam.git"\n'
            "  An editable checkout (pip install -e) is accepted only while it is on origin/main and\n"
            "  clean; never install one from a temporary git worktree — the install pointer goes\n"
            "  stale when the worktree is removed (this repo's original outage).\n"
            "  To skip Layer-1 entirely:  researchteam update --layer2-only"
        )
    probe = subprocess.run([exe, "--version"], capture_output=True, text=True)
    if probe.returncode != 0:
        detail = (probe.stderr or probe.stdout).strip().splitlines()
        tail = detail[-1] if detail else "(no output)"
        sys.exit(
            f"[researchteam] 'agentteams' resolved {where} ({exe}) but is not runnable.\n"
            "  This is almost always a stale editable install whose finder points at a\n"
            "  deleted path (e.g. a temporary git worktree). Reinstall from the canonical\n"
            "  checkout, using the interpreter that owns the console script:\n"
            "    <that-python> -m pip install -e /path/to/agentteams --no-build-isolation\n"
            "  Run 'researchteam doctor' for a full diagnosis.\n"
            f"  Detail: {tail[:300]}"
        )
    # Check the launcher that will actually be executed (beside this interpreter, else the PATH one),
    # so a render never runs an unmerged or dirty agentteams (CA-033).
    from ._agentteams_provenance import check as _check_provenance
    if _check_provenance(exe) != 0:
        sys.exit(
            f"[researchteam] Refusing to run unreviewed agentteams code ({exe}); see the reason above.\n"
            "  Run researchteam from an environment whose agentteams is pinned to a merged commit, e.g.\n"
            '    pip install "researchteam[update] @ git+https://github.com/jlcatonjr/researchteam.git"\n'
            "  and put that environment first on PATH."
        )
    _VERIFIED_LAUNCHERS.add(exe)
    return exe


# P5a (agentteams f113f5d): --overwrite carries the user-editable '## Project-Specific Notes/Rules'
# regions into the new render. Its opt-out flag doubles as the capability marker.
_P5A_FLAG = "--discard-user-regions"


def _require_p5a(exe: str) -> None:
    """Refuse an overwrite render with an agentteams that would silently drop user-editable regions."""
    probe = subprocess.run([exe, "--help"], capture_output=True, text=True)
    if _P5A_FLAG not in probe.stdout:
        sys.exit(
            f"[researchteam] {exe} predates agentteams P5a (no {_P5A_FLAG}): its --overwrite would drop\n"
            "  every '## Project-Specific Notes' / '## Project-Specific Rules' region. Upgrade agentteams\n"
            "  to a commit on main at or after f113f5d before running materialize."
        )


def _resolve_descriptor(root: Path) -> tuple[str, Path | None]:
    """Reconcile the two descriptors into a single, complete one WITHOUT losing data.

    Two files carry complementary halves of the project definition, and each is missing
    what the other has:
      * ``brief.json``            — content of record: ``authority_sources``,
        ``style_rules``, ``conversion_pipeline``, ``reference_key_convention``, rich
        ``components``, and the output-path fields. **Lacks the archetype roster.**
      * ``.github/agents/_build-description.json`` — roster of record:
        ``selected_archetypes`` + ``governance_agents``. **Lacks all the content fields.**

    Passing either one alone to ``agentteams --update --merge`` silently loses data:
      * ``brief.json`` alone  → registered archetypes are treated as **orphans**
        (``--prune`` would delete them).
      * ``_build-description.json`` alone → the FENCED ``authority_sources_list`` and
        ``style_rules_summary`` sections regenerate to placeholders (only the external
        ``agentteams`` shrink-guard ``preserve`` policy currently prevents the write).

    The fix is a **union**, not a swap: use ``brief.json`` as the base (so every content
    field and today's output-path convention are preserved unchanged) and inject only the
    roster fields it lacks from ``_build-description.json``. The union is written to a
    short-lived temp descriptor beside ``brief.json`` so ``agentteams`` relative-path and
    sibling-advisory resolution behave exactly as before.

    Returns ``(descriptor_arg, tempfile_to_cleanup_or_None)`` where ``descriptor_arg`` is
    relative to ``root`` (agentteams runs with ``cwd=root``).
    """
    brief = root / "brief.json"
    manifest = root / ".github" / "agents" / "_build-description.json"

    if not brief.exists():
        if manifest.exists():
            return str(manifest.relative_to(root)), None
        sys.exit(
            "[researchteam] Neither brief.json nor .github/agents/_build-description.json found, so the\n"
            "  layer-1 agentteams pass cannot run here. Either describe the project in brief.json\n"
            "  (then `researchteam update` maintains its agent team), or, if this repository's agent\n"
            "  files are maintained by hand, add `layer1 = off` to .researchteam so `update` syncs\n"
            "  layer 2 only. To sync layer 2 just this once: researchteam update --layer2-only"
        )
    if not manifest.exists():
        return "brief.json", None

    try:
        base = json.loads(brief.read_text(encoding="utf-8"))
        roster = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(
            f"[researchteam] Could not read/parse a descriptor ({exc}); "
            "falling back to brief.json as-is.",
            file=sys.stderr,
        )
        return "brief.json", None

    injected: list[str] = []
    for field in ("selected_archetypes", "governance_agents"):
        if roster.get(field) and roster.get(field) != base.get(field):
            base[field] = roster[field]
            injected.append(field)

    if not injected:
        # brief.json already carries the roster (or the manifest adds nothing) — no union
        # needed; use brief.json directly so the dual-descriptor advisory can still fire.
        return "brief.json", None

    fd, tmp_name = tempfile.mkstemp(prefix=".rt-descriptor-", suffix=".json", dir=str(root))
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(base, fh, indent=2)
    tmp = Path(tmp_name)
    print(
        f"[researchteam] Reconciled descriptor: brief.json (content) + "
        f"{'/'.join(injected)} (roster) from _build-description.json"
    )
    return tmp.name, tmp


def _reconcile_manifest_back(root: Path) -> None:
    """Persist brief.json's content fields into ``.github/agents/_build-description.json`` (RT-5).

    ``_resolve_descriptor`` reconciles the two descriptors only into a throwaway temp file for the
    agentteams run, so the on-disk manifest stays stale and the ``[WARN] Dual descriptor detected``
    notice fires on every subsequent generation. This writes the reconciliation back: brief.json is
    the content-of-record, so every brief key EXCEPT the roster fields the manifest owns
    (``selected_archetypes`` / ``governance_agents``) is overlaid onto the manifest. Idempotent and
    silent when nothing changes or a descriptor is missing/unreadable.
    """
    brief_path = root / "brief.json"
    manifest_path = root / ".github" / "agents" / "_build-description.json"
    if not brief_path.exists() or not manifest_path.exists():
        return
    try:
        brief = json.loads(brief_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return

    roster_owned = {"selected_archetypes", "governance_agents"}
    changed = False
    for key, value in brief.items():
        if key in roster_owned:
            continue
        if manifest.get(key) != value:
            manifest[key] = value
            changed = True
    if not changed:
        return
    try:
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(
            "[researchteam] Reconciled _build-description.json content fields from brief.json "
            "(RT-5: dual-descriptor divergence resolved)."
        )
    except OSError as exc:
        print(f"[researchteam] Could not persist descriptor reconciliation: {exc}", file=sys.stderr)


#: Native agent surfaces besides the default copilot-vscode team (``.github/agents``) that a
#: scaffold may ship. Each is a separate agentteams render target with its own decisions log.
NATIVE_SURFACES: tuple[tuple[str, str], ...] = (("claude", ".claude/agents"), ("goose", ".goose/recipes"))


def _native_surfaces(root: Path) -> list[tuple[str, str]]:
    """Return the ``(framework, dir)`` native surfaces present in *root*.

    A surface counts as present when its directory holds a NATIVE agentteams build-log, i.e. a native
    team was rendered there before. A bare bridge directory is left alone, and so is a directory whose
    build-log is an interop projection marker (``origin: "interop"``) or unreadable: agentteams treats
    such a log as "no prior build", so ``--materialize-native`` would write a whole native team over
    the bridge (@security, 2026-10-10).
    """
    found = []
    for fw, d in NATIVE_SURFACES:
        log = root / d / "references" / "build-log.json"
        if not log.is_file():
            continue
        try:
            data = json.loads(log.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            print(f"[researchteam] skipping {d}: its build-log is unreadable", file=sys.stderr)
            continue
        if not isinstance(data, dict) or data.get("origin") == "interop":
            continue
        found.append((fw, d))
    return found


def _render_native_surfaces(root: Path, *, yes: bool, dry_run: bool, overwrite: bool,
                            adopt_orphans: bool = False, discard_user_regions: bool = False,
                            label: str = "update") -> None:
    """Render every native surface (see :func:`_native_surfaces`) after the copilot-vscode render.

    ``overwrite`` False is the merge path (``researchteam update``); True is ``materialize``. On a
    failure it reports which surfaces were rendered and which were not attempted, then re-raises the
    non-zero exit so an autosync opens no PR.
    """
    surfaces = _native_surfaces(root)
    done = [".github/agents (copilot-vscode)"]
    for i, (framework, directory) in enumerate(surfaces):
        print(f"[researchteam] {label}: native surface {directory} ({framework})")
        try:
            _run_agentteams(root, yes=yes, dry_run=dry_run, overwrite=overwrite, framework=framework,
                            adopt_orphans=adopt_orphans, discard_user_regions=discard_user_regions)
        except SystemExit:
            pending = [f"{d} ({fw})" for fw, d in surfaces[i + 1:]]
            print(
                f"[researchteam] {label}: FAILED on {directory} ({framework}).\n"
                f"  already rendered: {', '.join(done)}\n"
                f"  not attempted: {', '.join(pending) or 'none'}"
                f"{'; README/CLAUDE not re-personalized' if label == 'materialize' else ''}.\n"
                "  Fix the cause (usually a missing clearance in that surface's decisions log) and re-run.",
                file=sys.stderr,
            )
            raise
        done.append(f"{directory} ({framework})")
    if not surfaces:
        print(f"[researchteam] {label}: no native claude/goose surfaces present.")


def _run_agentteams(
    root: Path,
    yes: bool,
    dry_run: bool,
    overwrite: bool = False,
    framework: str | None = None,
    adopt_orphans: bool = False,
    discard_user_regions: bool = False,
) -> None:
    if _brief_has_placeholder(root):
        msg = (
            f"[researchteam] brief.json still contains the scaffold placeholder "
            f"'{BRIEF_PLACEHOLDER}'.\n"
            "  Edit brief.json (project_name, project_goal, deliverables, authority_sources) to\n"
            "  describe YOUR project before generating the agent team — otherwise the placeholder\n"
            "  identity is baked into every generated agent file.\n"
            "  Then re-run:  researchteam update   (or  researchteam materialize  to re-render)."
        )
        if dry_run:
            print(msg + "\n[researchteam] (dry-run) skipping layer-1 agentteams pass.")
            return
        sys.exit(msg)

    exe = _preflight_agentteams()
    descriptor, tmp = _resolve_descriptor(root)

    if overwrite:
        # RT-1/RT-2 re-render path (`researchteam materialize`): --overwrite REPLACES enriched
        # bodies so a brief/domain change actually re-brands the instance. This is the cleared
        # path the `--merge --shrink-policy preserve` default deliberately refuses; agentteams'
        # destructive-overwrite security gate must be satisfied by a clearance in the target
        # surface's own decisions log (see docs/researchteam-framework.md, Decision signing).
        target = f"{framework} surface" if framework else "copilot-vscode surface"
        print(
            f"\n[researchteam] Running agentteams --update --overwrite on the {target} "
            f"(descriptor: {descriptor}) — re-rendering agent bodies from the brief ..."
        )
        cmd = [exe, "--description", descriptor, "--update", "--overwrite"]
        if framework:
            # Native (non-copilot) surfaces sit behind a bridge marker; agentteams fails closed on
            # --update against a bridge unless the native re-render is requested explicitly.
            cmd += ["--framework", framework, "--project", ".", "--materialize-native"]
        if adopt_orphans:
            # Register bespoke agent files (no agentteams template) into the orchestrator roster
            # without generating or overwriting them. agentteams does not persist adoption, so it
            # must be requested on every render.
            cmd.append("--adopt-orphans")
        if discard_user_regions:
            # Opt out of P5a's carry: drop the user-editable Project-Specific Notes/Rules regions.
            cmd.append(_P5A_FLAG)
    else:
        print(
            f"\n[researchteam] Running agentteams --update --merge "
            f"(descriptor: {descriptor}) ..."
        )
        # Pin --shrink-policy preserve explicitly (it is agentteams' default, but this pipeline can pull an
        # unreviewed agentteams from main via the autosync CI, so a future default flip must never silently
        # shrink researchteam's enriched fences into an auto-PR). See docs/agentteams-update-policy.md.
        cmd = [exe, "--description", descriptor, "--update", "--merge", "--shrink-policy", "preserve"]
        if framework:
            # A native surface sits behind a bridge marker: agentteams fails closed on --update there unless
            # the native render is requested. Merge mode keeps enriched fenced content (never overwrite).
            cmd += ["--framework", framework, "--project", ".", "--materialize-native"]
    env = None
    if not dry_run:
        from ._drift import prepare_report
        report = prepare_report(root, framework)  # drop this surface's previous report either way
        if not overwrite:
            # Ask agentteams for the shrink review report (gitignored tmp/), so a section the guard keeps
            # frozen is counted every run instead of drifting silently (see _drift.py). An overwrite
            # render freezes nothing, so its surface simply has no report afterwards.
            env = dict(os.environ, AGENTTEAMS_SHRINK_REPORT=str(report))
    if yes:
        cmd.append("--yes")
    if dry_run:
        cmd.append("--dry-run")

    try:
        result = subprocess.run(cmd, cwd=str(root), env=env)
    finally:
        if tmp is not None:
            try:
                tmp.unlink()
            except OSError:
                pass

    if result.returncode != 0:
        print("[researchteam] agentteams update exited non-zero.", file=sys.stderr)
        sys.exit(result.returncode)

    # RT-5: persist the descriptor reconciliation so the dual-descriptor warning does not recur.
    if not dry_run and framework is None:
        _reconcile_manifest_back(root)


def _refresh_codex(root: Path, dry_run: bool) -> None:
    """Re-project the Codex surface after a render, if the instance carries one.

    Codex is an interop projection, not a native render target: agents come from the canonical
    copilot-vscode team (``.github/agents`` -> ``.codex/agents/*.toml``), and skills come from
    the Claude skills (``.claude/skills`` -> ``.agents/skills``, via ``--interop-skills-only``).
    Without this step a render leaves ``.codex`` on the previous roster.
    """
    if not (root / ".codex" / "agents").is_dir():
        return
    exe = _preflight_agentteams()
    # --overwrite is required: without it interop SKIPS existing files, so an already-projected
    # agent or skill would never pick up later canonical changes. Codex files are pure generated
    # projections (never hand-edited), so full replacement is correct.
    runs = [[exe, "--interop-from", ".github/agents", "--framework", "codex", "--output", ".",
             "--overwrite", "--yes"]]
    if (root / ".claude" / "skills").is_dir():
        runs.append([exe, "--interop-from", ".claude/agents", "--interop-source-framework", "claude",
                     "--framework", "codex", "--interop-skills-only", "--output", ".", "--overwrite", "--yes"])
    for cmd in runs:
        if dry_run:
            cmd.append("--dry-run")
        print(f"[researchteam] materialize: refreshing Codex projection ({' '.join(cmd[1:4])} ...)")
        result = subprocess.run(cmd, cwd=str(root))
        if result.returncode != 0:
            print("[researchteam] materialize: Codex projection FAILED; the rendered surfaces are "
                  "current, .codex is not. Fix the cause and re-run.", file=sys.stderr)
            sys.exit(result.returncode)
    _prune_stale_codex_agents(root, dry_run=dry_run)
    if not dry_run:
        _check_codex_team_marker(root)


def _check_codex_team_marker(root: Path) -> None:
    """Warn when the Codex projection left no team marker.

    Since agentteams ``d31d4a0`` an interop projection writes ``references/build-log.json`` (with
    ``"origin": "interop"``), so agentteams recognises ``.codex/agents`` as a team: verify-key store
    sentinel, roster stubs, launcher protection, fleet/--update discovery. An older agentteams writes
    none, and the Codex team stays unrecognised. This is a warning, not a failure: the projected
    agents themselves are still current.
    """
    marker = root / ".codex" / "agents" / "references" / "build-log.json"
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = None
    if not isinstance(data, dict):
        print("[researchteam] materialize: WARNING: the Codex projection wrote no team marker "
              "(.codex/agents/references/build-log.json). The installed agentteams predates the "
              "interop team-marker fix (agentteams d31d4a0); upgrade it so agentteams recognises the "
              "Codex team.", file=sys.stderr)


#: First line agentteams writes into every projected Codex agent. Only files carrying it are ever
#: pruned, so a hand-authored Codex agent is never deleted.
_CODEX_GENERATED_HEADER = "# Codex custom agent — generated by agentteams"


def _prune_stale_codex_agents(root: Path, dry_run: bool) -> None:
    """Remove generated Codex agents whose canonical source no longer exists.

    The interop projection only adds or updates ``.codex/agents/*.toml``; it never deletes one
    whose ``.github/agents/<slug>.agent.md`` was removed, so a retired agent would linger in Codex.
    Only files that carry the agentteams generation header are candidates.
    """
    canonical = {p.name[: -len(".agent.md")] for p in (root / ".github" / "agents").glob("*.agent.md")}
    for toml in sorted((root / ".codex" / "agents").glob("*.toml")):
        if toml.stem in canonical:
            continue
        try:
            first = toml.read_text(encoding="utf-8").splitlines()[0]
        except (OSError, IndexError):
            continue
        if not first.startswith(_CODEX_GENERATED_HEADER):
            continue
        verb = "would prune" if dry_run else "pruned"
        print(f"[researchteam] materialize: {verb} stale Codex agent {toml.name} (no canonical source)")
        if not dry_run:
            toml.unlink()


def run_materialize(
    root: Path,
    yes: bool,
    dry_run: bool,
    copilot_only: bool = False,
    adopt_orphans: bool = False,
    codex: bool = True,
    discard_user_regions: bool = False,
) -> None:
    """Re-render a derived instance from its (edited) brief.json — RT-1/RT-2 cleared re-render.

    ``update`` intentionally cannot re-brand an instance whose domain/identity changed, because it
    runs ``agentteams --merge --shrink-policy preserve`` (enriched bodies are protected). This is
    the distinct, explicit path that DOES replace them: it runs the destructive ``--overwrite``
    agentteams pass, then re-personalizes the layer-2 identity files (README.md / CLAUDE.md) from
    the current brief. Use it after materially changing brief.json (e.g. a new project domain).

    Every native surface the instance carries (``.claude/agents``, ``.goose/recipes``) is
    re-rendered too, from the SAME reconciled descriptor, so all surfaces share one roster.
    Rendering only copilot-vscode left the other surfaces on the scaffold's identity and let
    their rosters drift. ``copilot_only`` restores the old single-surface behaviour.

    ``adopt_orphans`` passes ``--adopt-orphans`` to every surface's render, so bespoke agents
    (files with no agentteams template) stay in the orchestrator roster. When the instance
    carries a Codex surface (``.codex/agents``), its agents and skills are re-projected after the
    renders unless ``codex`` is False.

    The overwrite carries every user-editable ``## Project-Specific Notes`` / ``## Project-Specific
    Rules`` region into the new files (agentteams P5a), so an agentteams without P5a is refused before
    anything runs. ``discard_user_regions`` passes ``--discard-user-regions`` to drop them instead.
    """
    from ._personalize import is_upstream, run_personalize

    if not layer1_enabled(root):
        sys.exit("[researchteam] materialize re-renders the agent team, but .researchteam declares "
                 "layer1 = off for this repository. Remove that line first if you mean it.")
    if is_upstream(root):
        sys.exit(
            "[researchteam] Refusing to materialize the UPSTREAM repository "
            "(.researchteam has is_upstream = true). Run this in a derived instance."
        )
    if _brief_has_placeholder(root):
        # _run_agentteams would also refuse, but fail early with the same actionable message.
        sys.exit(
            f"[researchteam] brief.json still contains the placeholder '{BRIEF_PLACEHOLDER}'. "
            "Edit it to describe your project before materializing."
        )

    # Fail before the prompt: the agentteams that will run must be reviewed code (provenance) and must
    # carry user-editable regions across --overwrite (P5a).
    _require_p5a(_preflight_agentteams())

    print(
        "[researchteam] materialize: this REPLACES generated agent bodies with a fresh render "
        "from brief.json (destructive to enriched fenced content)."
    )
    if not dry_run and not yes:
        answer = input("Proceed with the overwrite re-render? [y/N] ").strip().lower()
        if answer != "y":
            print("[researchteam] Aborted; nothing changed.")
            return

    # Layer-1: overwrite re-render (+ RT-5 write-back happens inside _run_agentteams on success).
    _run_agentteams(root, yes=yes, dry_run=dry_run, overwrite=True, adopt_orphans=adopt_orphans,
                    discard_user_regions=discard_user_regions)
    if not copilot_only:
        _render_native_surfaces(root, yes=yes, dry_run=dry_run, overwrite=True,
                                adopt_orphans=adopt_orphans, discard_user_regions=discard_user_regions,
                                label="materialize")
    if codex:
        _refresh_codex(root, dry_run=dry_run)

    # Layer-2 identity: re-render README/CLAUDE from the now-current brief. Files generated at init
    # and untouched since are refreshed in place; a hand-diverged file is left alone (see
    # run_personalize's content-hash guard) unless the operator passes force.
    if not dry_run:
        run_personalize(root, force=False, quiet=False)
    else:
        print("[researchteam] (dry-run) would re-personalize README.md / CLAUDE.md from brief.json.")
