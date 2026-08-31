"""Implementation of `researchteam update`."""

import difflib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ._manifest import (
    FENCE_BEGIN,
    FENCE_END,
    MANAGED_FILES,
    MERGE_STRATEGIES,
    UPSTREAM_REPO,
)
from ._fetch import fetch_raw


def _split_fence(text: str) -> tuple[str, str, str] | None:
    """Split ``text`` around the researchteam:managed fence.

    Returns ``(pre, managed, post)`` where ``managed`` INCLUDES both marker lines, or ``None``
    when a well-formed fence (BEGIN then END, in order) is absent. A marker line is recognized by
    its sentinel PREFIX, so the self-documenting trailing prose the upstream markers carry
    (``# >>> researchteam:managed — do not edit …``) still matches.
    """
    lines = text.splitlines(keepends=True)
    begin_idx = end_idx = None
    for i, ln in enumerate(lines):
        stripped = ln.strip()
        if begin_idx is None and stripped.startswith(FENCE_BEGIN):
            begin_idx = i
        elif begin_idx is not None and stripped.startswith(FENCE_END):
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


def run_update(
    root: Path,
    ref: str,
    yes: bool,
    dry_run: bool,
    layer2_only: bool,
    layer1_only: bool = False,
) -> None:
    if layer1_only and layer2_only:
        sys.exit("[researchteam] --layer1-only and --layer2-only are mutually exclusive.")

    if layer1_only:
        # Integrate the current agent state only — the union-descriptor agentteams merge with
        # NO layer-2 file sync. This is the safe way to keep agent infrastructure integrated on
        # the upstream repo (a layer-2 sync there would overwrite local managed-file edits with
        # the older upstream versions). Used by the auto-integration git hook.
        print("[researchteam] Layer-1 only: integrating current agent state (no file sync) ...")
        _run_agentteams(root, yes=yes, dry_run=dry_run)
        return

    print(f"[researchteam] Syncing layer-2 files from {UPSTREAM_REPO}@{ref} ...")

    updated: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []

    for rel_path in MANAGED_FILES:
        local_path = root / rel_path
        try:
            remote_content = fetch_raw(UPSTREAM_REPO, ref, rel_path)
        except RuntimeError as exc:
            errors.append(str(exc))
            continue

        if local_path.exists():
            local_content = local_path.read_text(encoding="utf-8")
            strategy = MERGE_STRATEGIES.get(rel_path, "overwrite")

            if strategy == "fenced-preserve":
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

    if layer2_only:
        return

    # Layer-1: delegate to agentteams
    _run_agentteams(root, yes=yes, dry_run=dry_run)


def _preflight_agentteams() -> str:
    """Resolve and liveness-check the `agentteams` console script before shelling out.

    Converts the two opaque failure modes of this integration into one-line, actionable
    errors instead of a raw ``ModuleNotFoundError`` traceback:
      1. `agentteams` absent from PATH.
      2. `agentteams` present but not runnable — the signature of a stale *editable*
         install whose finder points at a deleted path (e.g. a temporary git worktree).

    The ``--version`` probe is a genuine import assertion: the console-script entry point
    is ``build_team:main``, so ``--version`` must import ``build_team`` before argparse
    runs. A green probe therefore proves the resolved interpreter can import the module —
    which is exactly the invariant a bare ``sys.executable`` invocation would violate here
    (researchteam's venv does not have ``build_team`` installed).

    Returns the resolved absolute path to the console script.
    """
    exe = shutil.which("agentteams")
    if exe is None:
        sys.exit(
            "[researchteam] Layer-1 update needs 'agentteams', which is not on PATH.\n"
            "  Install it into an environment on your PATH (from the canonical checkout):\n"
            "    pip install -e /path/to/agentteams --no-build-isolation\n"
            "  Do NOT run 'pip install -e' from a temporary git worktree — the install\n"
            "  pointer goes stale when the worktree is removed (this repo's original outage).\n"
            "  To skip Layer-1 entirely:  researchteam update --layer2-only"
        )
    probe = subprocess.run([exe, "--version"], capture_output=True, text=True)
    if probe.returncode != 0:
        detail = (probe.stderr or probe.stdout).strip().splitlines()
        tail = detail[-1] if detail else "(no output)"
        sys.exit(
            f"[researchteam] 'agentteams' is on PATH ({exe}) but is not runnable.\n"
            "  This is almost always a stale editable install whose finder points at a\n"
            "  deleted path (e.g. a temporary git worktree). Reinstall from the canonical\n"
            "  checkout, using the interpreter that owns the console script:\n"
            "    <that-python> -m pip install -e /path/to/agentteams --no-build-isolation\n"
            "  Run 'researchteam doctor' for a full diagnosis.\n"
            f"  Detail: {tail[:300]}"
        )
    return exe


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
            "[researchteam] Neither brief.json nor .github/agents/_build-description.json "
            "found; cannot run the Layer-1 agentteams update."
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


def _run_agentteams(root: Path, yes: bool, dry_run: bool) -> None:
    exe = _preflight_agentteams()
    descriptor, tmp = _resolve_descriptor(root)

    print(
        f"\n[researchteam] Running agentteams --update --merge "
        f"(descriptor: {descriptor}) ..."
    )
    # Pin --shrink-policy preserve explicitly (it is agentteams' default, but this pipeline can pull an
    # unreviewed agentteams from main via the autosync CI, so a future default flip must never silently
    # shrink researchteam's enriched fences into an auto-PR). See docs/agentteams-update-policy.md.
    cmd = [exe, "--description", descriptor, "--update", "--merge", "--shrink-policy", "preserve"]
    if yes:
        cmd.append("--yes")
    if dry_run:
        cmd.append("--dry-run")

    try:
        result = subprocess.run(cmd, cwd=str(root))
    finally:
        if tmp is not None:
            try:
                tmp.unlink()
            except OSError:
                pass

    if result.returncode != 0:
        print("[researchteam] agentteams update exited non-zero.", file=sys.stderr)
        sys.exit(result.returncode)
