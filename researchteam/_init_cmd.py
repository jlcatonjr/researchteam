"""Implementation of `researchteam init`."""

import importlib.resources
import io
import subprocess
import sys
import tarfile
from pathlib import Path, PurePosixPath

from ._manifest import (
    INIT_SCAFFOLD_REPLACEMENTS,
    INIT_SKIP_PREFIXES,
    UPSTREAM_REPO,
)
from ._fetch import fetch_tarball

# is_upstream = false is written EXPLICITLY (never omitted): the personalize / materialize guards
# refuse only on a literal `is_upstream = true`, and a derived repo must always be personalizable.
# The upstream repository is the only place that carries `is_upstream = true`; it is never produced
# by `init`. See test_init_personalization for the invariant that this template never emits `true`.
_MARKER_TEMPLATE = """\
[researchteam]
upstream = https://github.com/{repo}
ref = {ref}
is_upstream = false
"""


def run_init(name: str | None, ref: str, remote_url: str | None) -> None:
    if name:
        target = Path(name).resolve()
        if target.exists():
            print(f"Error: '{name}' already exists.", file=sys.stderr)
            sys.exit(1)
        target.mkdir(parents=True)
        print(f"[researchteam] Initializing new project at {target} ...")
    else:
        target = Path.cwd().resolve()
        existing = list(target.iterdir())
        if existing:
            print(
                "Error: current directory is not empty. "
                "Pass a name to create a new directory.",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"[researchteam] Initializing project in current directory ...")

    print(f"[researchteam] Downloading template from {UPSTREAM_REPO}@{ref} ...")
    tarball = fetch_tarball(UPSTREAM_REPO, ref)

    print("[researchteam] Extracting template files ...")
    _extract(tarball, target)

    # Replace selected files with bundled scaffold versions.
    _apply_scaffold_replacements(target)

    # Seed a neutral placeholder brief.json (the framework's own brief.json is skipped on extract).
    _seed_brief(target)

    # Write marker BEFORE personalize: the is_upstream guard reads it, and a marker written after a
    # personalize failure would leave a half-initialized repo. is_upstream = false ⇒ personalizable.
    marker = target / ".researchteam"
    marker.write_text(_MARKER_TEMPLATE.format(repo=UPSTREAM_REPO, ref=ref))

    # Render project-specific README.md and CLAUDE.md from the placeholder brief. A failure here is
    # fatal: init must not commit a repo missing its two identity files.
    from ._personalize import run_personalize

    try:
        run_personalize(target, force=True, quiet=False)
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[researchteam] init failed while personalizing: {exc}", file=sys.stderr)
        sys.exit(1)

    # Initialise git repo.
    subprocess.run(["git", "init"], cwd=str(target), check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=str(target), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "chore: initialize from researchteam template"],
        cwd=str(target),
        check=True,
        capture_output=True,
    )

    if remote_url:
        subprocess.run(
            ["git", "remote", "add", "origin", remote_url],
            cwd=str(target),
            check=True,
            capture_output=True,
        )

    print(f"\n[researchteam] Done. Project initialized at {target}")
    if name:
        print(f"\nNext steps:\n  cd {name}")
    print("  1. Edit brief.json — set project_name, project_goal, deliverables, authority_sources.")
    print("       (Set layer2_profile to \"generic\" for a non-scholarly project.)")
    print("  2. researchteam personalize   # regenerate README.md / CLAUDE.md header from brief.json")
    print("  3. researchteam materialize   # render the agent team from your edited brief.json")
    print("  bash scripts/claude_researchteam_bridge.sh help")
    print(
        "\nNote: the agent team is generated with agentteams' decision-signing gate DISABLED "
        "(enforce_decision_signing:false in brief.json), so 'materialize' can re-render freely. "
        "Set it to true in brief.json to require signed clearances for destructive regeneration."
    )


def _extract(tarball: bytes, target: Path) -> None:
    with tarfile.open(fileobj=io.BytesIO(tarball), mode="r:gz") as tf:
        for member in tf.getmembers():
            # Strip top-level GitHub archive directory (e.g. "researchteam-main/")
            parts = PurePosixPath(member.name).parts
            if len(parts) < 2:
                continue
            rel_path = "/".join(parts[1:])

            if _should_skip(rel_path):
                continue

            dest = target / rel_path
            if member.isdir():
                dest.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                dest.parent.mkdir(parents=True, exist_ok=True)
                f = tf.extractfile(member)
                if f:
                    content = f.read()
                    dest.write_bytes(content)
                    # Preserve executable bit for scripts.
                    if member.mode & 0o111:
                        dest.chmod(dest.stat().st_mode | 0o111)


def _should_skip(rel_path: str) -> bool:
    for prefix in INIT_SKIP_PREFIXES:
        clean = prefix.rstrip("/")
        if rel_path == clean or rel_path.startswith(clean + "/"):
            return True
    return False


def _seed_brief(target: Path) -> None:
    """Write a neutral placeholder brief.json from the bundled scaffold template.

    The framework's own brief.json is excluded on extract (INIT_SKIP_PREFIXES), so a derived repo
    never inherits the ResearchTeam identity. The user edits this before generating the team.
    """
    pkg = importlib.resources.files("researchteam") / "scaffold"
    dest = target / "brief.json"
    dest.write_bytes((pkg / "brief.template.json").read_bytes())


def _apply_scaffold_replacements(target: Path) -> None:
    """Overwrite selected paths with files bundled in the package scaffold directory."""
    pkg = importlib.resources.files("researchteam") / "scaffold"
    for dest_rel, scaffold_name in INIT_SCAFFOLD_REPLACEMENTS.items():
        dest = target / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        scaffold_file = pkg / scaffold_name
        dest.write_bytes(scaffold_file.read_bytes())
