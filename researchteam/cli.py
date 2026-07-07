"""researchteam CLI entry point."""

import argparse
import sys
from pathlib import Path

from . import __version__
from ._manifest import UPSTREAM_BRANCH


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="researchteam",
        description="ResearchTeam — agent-based research workflow framework",
    )
    parser.add_argument(
        "--version", action="version", version=f"researchteam {__version__}"
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # ---- init ----------------------------------------------------------------
    init_p = sub.add_parser(
        "init",
        help="Scaffold a new project from the researchteam template",
    )
    init_p.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Directory name for the new project (defaults to current directory)",
    )
    init_p.add_argument(
        "--ref",
        default=UPSTREAM_BRANCH,
        metavar="REF",
        help="Upstream git ref to scaffold from (branch, tag, or SHA; default: main)",
    )
    init_p.add_argument(
        "--remote",
        default=None,
        metavar="URL",
        help="Git remote URL to set as 'origin' after init",
    )

    # ---- update --------------------------------------------------------------
    update_p = sub.add_parser(
        "update",
        help="Sync layer-2 managed files from upstream, then run agentteams update",
    )
    update_p.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Apply all file changes without interactive confirmation",
    )
    update_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing any files",
    )
    update_p.add_argument(
        "--layer2-only",
        action="store_true",
        help="Only sync layer-2 files; skip agentteams --update --merge",
    )
    update_p.add_argument(
        "--layer1-only",
        action="store_true",
        help="Only run the agentteams --update --merge (union descriptor); skip layer-2 file "
        "sync. Use to integrate the current agent state without touching managed files "
        "(safe on the upstream repo; used by the auto-integration git hook).",
    )
    update_p.add_argument(
        "--ref",
        default=None,
        metavar="REF",
        help="Upstream git ref to fetch from (overrides .researchteam marker; default: main)",
    )

    # ---- status --------------------------------------------------------------
    sub.add_parser("status", help="Show marker info and CLI version")

    sub.add_parser(
        "doctor",
        help="Diagnose researchteam↔agentteams toolchain health (agentteams resolvable, "
        "runnable, non-ephemeral install; descriptor reconciliation)",
    )

    args = parser.parse_args()

    if args.command == "init":
        from ._init_cmd import run_init
        run_init(args.name, args.ref, args.remote)

    elif args.command == "update":
        root = _find_repo_root(require_marker=True)
        ref = args.ref or _read_marker_ref(root)
        from ._update_cmd import run_update
        run_update(
            root,
            ref=ref,
            yes=args.yes,
            dry_run=args.dry_run,
            layer2_only=args.layer2_only,
            layer1_only=args.layer1_only,
        )

    elif args.command == "status":
        _cmd_status()

    elif args.command == "doctor":
        root = _find_repo_root(require_marker=False)
        from ._doctor_cmd import run_doctor
        run_doctor(root)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_repo_root(require_marker: bool = False) -> Path:
    """Walk up from CWD looking for .researchteam or .git."""
    cwd = Path.cwd()
    marker_root: Path | None = None
    git_root: Path | None = None

    for candidate in [cwd, *cwd.parents]:
        if marker_root is None and (candidate / ".researchteam").exists():
            marker_root = candidate
        if git_root is None and (candidate / ".git").exists():
            git_root = candidate
        if marker_root and git_root:
            break

    if require_marker and marker_root is None:
        print(
            "Error: .researchteam marker not found.\n"
            "This command runs inside a derived researchteam repo.\n"
            "  • To create one: researchteam init <name>\n"
            "  • If you are working in the upstream repo, layer-2 sync is not needed.",
            file=sys.stderr,
        )
        sys.exit(1)

    root = marker_root or git_root
    if root is None:
        print("Error: not inside a git repository.", file=sys.stderr)
        sys.exit(1)
    return root


def _read_marker_ref(root: Path) -> str:
    """Read the upstream ref recorded in .researchteam, defaulting to UPSTREAM_BRANCH."""
    from ._manifest import UPSTREAM_BRANCH
    marker = root / ".researchteam"
    if not marker.exists():
        return UPSTREAM_BRANCH
    for line in marker.read_text().splitlines():
        if line.startswith("ref ="):
            return line.split("=", 1)[1].strip()
    return UPSTREAM_BRANCH


def _cmd_status() -> None:
    root = _find_repo_root(require_marker=False)
    marker = root / ".researchteam"
    print(f"researchteam {__version__}")
    if marker.exists():
        print(f"Marker: {marker}")
        print(marker.read_text().strip())
    else:
        print("No .researchteam marker found (upstream repo or uninitialized).")
