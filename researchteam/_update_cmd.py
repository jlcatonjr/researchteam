"""Implementation of `researchteam update`."""

import difflib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ._manifest import MANAGED_FILES, UPSTREAM_REPO
from ._fetch import fetch_raw


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
            if local_content == remote_content:
                continue  # identical — nothing to do

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
            local_path.write_text(remote_content, encoding="utf-8")
            updated.append(rel_path)
            print(f"  Updated {rel_path}")
        else:
            if dry_run:
                print(f"  [dry-run] Would create: {rel_path}")
                updated.append(rel_path)
                continue

            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_text(remote_content, encoding="utf-8")
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
    cmd = [exe, "--description", descriptor, "--update", "--merge"]
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
