"""researchteam CLI entry point."""

import argparse
import sys
from pathlib import Path

from . import __version__
from ._manifest import UPSTREAM_BRANCH


def main() -> None:
    # Line-buffer stdout so progress and errors (stderr) appear in order in CI logs; with a pipe,
    # stdout is otherwise block-buffered and a failure message can print before the lines leading up
    # to it (Batallion run 38081664174 looked silent for that reason).
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass
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
    init_p.add_argument(
        "--vulnscan-level",
        choices=("off", "scan"),
        default=None,
        help="brief.json vulnerability_scanning level (default: scan, from the scaffold). 'remediate' is "
        "an operator choice: agentteams --set-vulnscan",
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
        help="Upstream git ref to fetch from (overrides a release-locked toolchain.lock and the "
        ".researchteam marker; default: the lock's verified researchteam tag, else the marker, else main)",
    )
    update_p.add_argument(
        "--accept-upstream",
        action="append",
        default=[],
        metavar="PATH",
        help="Replace this above-notes file's part above '## Project-Specific Notes' with upstream's "
        "even though the repo customised it (Notes kept, previous file backed up). Repeatable. "
        "Without it a customised file is kept, also under --yes.",
    )
    update_p.add_argument(
        "--no-codex",
        action="store_true",
        help="Skip refreshing the Codex surface (.codex/agents, .agents/skills); for repositories "
        "that keep Codex frozen for 1.0 (adopted agents; release policy section 5)",
    )

    # ---- personalize ---------------------------------------------------------
    personalize_p = sub.add_parser(
        "personalize",
        help="Regenerate project-specific README.md and CLAUDE.md's header from brief.json",
    )
    personalize_p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite generated regions even if they were hand-edited since generation",
    )

    # ---- materialize ---------------------------------------------------------
    materialize_p = sub.add_parser(
        "materialize",
        help="Re-render the agent team from brief.json (cleared --overwrite pass) on every "
        "agent surface (copilot-vscode plus any native claude/goose teams) after a "
        "domain/identity change, then re-personalize README.md / CLAUDE.md",
    )
    materialize_p.add_argument(
        "--copilot-only",
        action="store_true",
        help="Re-render only the copilot-vscode surface (.github/agents); skip native surfaces",
    )
    materialize_p.add_argument(
        "--adopt-orphans",
        action="store_true",
        help="Keep bespoke agents (no agentteams template) in every surface's roster "
        "(passes agentteams --adopt-orphans to each render)",
    )
    materialize_p.add_argument(
        "--discard-user-regions",
        action="store_true",
        help="Drop the user-editable '## Project-Specific Notes' / '## Project-Specific Rules' regions "
        "instead of carrying them into the re-rendered files (passes agentteams --discard-user-regions)",
    )
    materialize_p.add_argument(
        "--no-codex",
        action="store_true",
        help="Skip refreshing the Codex surface (.codex/agents, .agents/skills) after rendering",
    )
    materialize_p.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip the destructive-overwrite confirmation prompt",
    )
    materialize_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing any files",
    )

    # ---- status --------------------------------------------------------------
    sub.add_parser("status", help="Show marker info and CLI version")

    doctor_p = sub.add_parser(
        "doctor",
        help="Diagnose researchteam↔agentteams toolchain health (agentteams resolvable, "
        "runnable, non-ephemeral install; toolchain pin; frozen fences; descriptor reconciliation)",
    )
    doctor_p.add_argument(
        "--drift",
        action="store_true",
        help="Also check drift that needs the network or agentteams: seeded files vs upstream at the "
        "pinned commit, and --bridge-check per bridge (rewrites the gitignored bridge-check reports)",
    )

    args = parser.parse_args()

    if args.command == "init":
        from ._init_cmd import run_init
        run_init(args.name, args.ref, args.remote, vulnscan_level=args.vulnscan_level)

    elif args.command == "update":
        root = _find_repo_root(require_marker=True)
        locked = None if args.ref or args.layer1_only else _release_locked_ref(root)
        ref = args.ref or locked or _read_marker_ref(root)
        from ._drift import is_safe_ref
        if not is_safe_ref(ref):
            sys.exit(f"[researchteam] refusing the upstream ref {ref!r}: not a plain branch, tag or commit name "
                     "(check --ref and the .researchteam marker's ref).")
        if ref != locked and not args.layer1_only:
            _check_commit_ref(ref)
        from ._update_cmd import run_update
        run_update(
            root,
            ref=ref,
            yes=args.yes,
            dry_run=args.dry_run,
            layer2_only=args.layer2_only,
            layer1_only=args.layer1_only,
            accept_upstream=args.accept_upstream,
            codex=not args.no_codex,
        )

    elif args.command == "personalize":
        root = _find_repo_root(require_marker=True)
        from ._personalize import run_personalize
        run_personalize(root, force=args.force, quiet=False)

    elif args.command == "materialize":
        root = _find_repo_root(require_marker=True)
        from ._update_cmd import run_materialize
        run_materialize(root, yes=args.yes, dry_run=args.dry_run, copilot_only=args.copilot_only,
                        adopt_orphans=args.adopt_orphans, codex=not args.no_codex,
                        discard_user_regions=args.discard_user_regions)

    elif args.command == "status":
        _cmd_status()

    elif args.command == "doctor":
        root = _find_repo_root(require_marker=False)
        from ._doctor_cmd import run_doctor
        run_doctor(root, drift=args.drift)


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


def _release_locked_ref(root: Path) -> str | None:
    """The verified researchteam tag's commit when toolchain.lock release-locks researchteam.

    Layer 2 then syncs from that tag, not from main (release policy §4). A lock whose tag does not
    verify stops the update: fail closed, never fall back to main.
    """
    from ._manifest import UPSTREAM_REPO
    from ._release import ReleaseError, locked_layer2_ref
    try:
        locked = locked_layer2_ref(root, UPSTREAM_REPO)
    except ReleaseError as exc:
        sys.exit(f"[researchteam] toolchain.lock release-locks researchteam, but {exc}. Layer-2 sync "
                 "refused; fix the lock, or pass --ref to choose a ref deliberately.")
    if locked is None:
        return None
    print(f"[researchteam] release-locked: syncing layer 2 from researchteam {locked[1]} ({locked[0][:12]}).")
    return locked[0]


def _check_commit_ref(ref: str) -> None:
    """A commit ref must be in researchteam's reviewed history (GitHub serves fork commits under its URL too).

    Exits when GitHub says it is not on main or a release branch; warns and continues when that cannot be
    determined (offline or rate-limited). Branch and tag names, and the verified release-locked commit, skip this.
    """
    import re
    if not re.fullmatch(r"[0-9a-f]{7,40}", ref):
        return
    from ._fetch import commit_is_reviewed
    from ._manifest import UPSTREAM_REPO
    reviewed = commit_is_reviewed(UPSTREAM_REPO, ref)
    if reviewed is False:
        sys.exit(f"[researchteam] refusing commit {ref[:12]}: it is not on main or a release branch of "
                 f"{UPSTREAM_REPO}.")
    if reviewed is None:
        print(f"[researchteam] WARNING: could not confirm that commit {ref[:12]} is on {UPSTREAM_REPO} main or a "
              "release branch (offline or rate-limited; set GITHUB_TOKEN to raise the limit).", file=sys.stderr)


def _read_marker_ref(root: Path) -> str:
    """Read the upstream ref recorded in .researchteam, defaulting to UPSTREAM_BRANCH."""
    from ._manifest import UPSTREAM_BRANCH
    from ._personalize import read_marker
    try:
        return read_marker(root).get("ref") or UPSTREAM_BRANCH
    except OSError:
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
