"""Implementation of `researchteam update`."""

import difflib
import subprocess
import sys
from pathlib import Path

from ._manifest import MANAGED_FILES, UPSTREAM_REPO
from ._fetch import fetch_raw


def run_update(
    root: Path,
    ref: str,
    yes: bool,
    dry_run: bool,
    layer2_only: bool,
) -> None:
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


def _run_agentteams(root: Path, yes: bool, dry_run: bool) -> None:
    print("\n[researchteam] Running agentteams --update --merge ...")

    cmd = ["agentteams", "--description", "brief.json", "--update", "--merge"]
    if yes:
        cmd.append("--yes")
    if dry_run:
        cmd.append("--dry-run")

    result = subprocess.run(cmd, cwd=str(root))
    if result.returncode != 0:
        print("[researchteam] agentteams update exited non-zero.", file=sys.stderr)
        sys.exit(result.returncode)
