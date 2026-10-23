"""Implementation of `researchteam init`."""

import importlib.resources
import io
import re
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
    from ._drift import is_safe_ref

    if not is_safe_ref(ref):
        print(f"Error: --ref {ref!r} is not a plain branch, tag or commit name.", file=sys.stderr)
        sys.exit(1)
    if name:
        target = Path(name).resolve()
        if target.exists() and (not target.is_dir() or any(target.iterdir())):
            print(f"Error: '{name}' already exists and is not an empty directory.", file=sys.stderr)
            sys.exit(1)
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

    # Download and check the whole archive BEFORE creating anything, so a failed fetch or a bad archive
    # leaves no directory behind.
    print(f"[researchteam] Downloading template from {UPSTREAM_REPO}@{ref} ...")
    try:
        tarball = fetch_tarball(UPSTREAM_REPO, ref)
        members, links, top = _validate_archive(tarball)
    except (RuntimeError, ArchiveError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    # A commit ref is recorded in full (from the archive's top directory), so the marker is unambiguous.
    commit = top.rsplit("-", 1)[-1]
    if _HEX.match(ref) and _FULL_SHA.match(commit) and commit.startswith(ref):
        ref = commit

    created = name is not None and not target.exists()
    if name:
        target.mkdir(parents=True, exist_ok=True)
        print(f"[researchteam] Initializing new project at {target} ...")
    else:
        print("[researchteam] Initializing project in current directory ...")
    try:
        _populate(target, tarball, members, links, ref, remote_url)
    except (OSError, subprocess.CalledProcessError) as exc:
        where = "it" if created else "the files written there"
        print(f"[researchteam] init failed: {exc}\n"
              f"  The project at {target} is incomplete; remove {where} before retrying.", file=sys.stderr)
        sys.exit(1)

    print(f"\n[researchteam] Done. Project initialized at {target}")
    if name:
        print(f"\nNext steps:\n  cd {name}")
    print("  1. Edit brief.json — set project_name, project_goal, deliverables, authority_sources.")
    print("       (Set layer2_profile to \"generic\" for a non-scholarly project.)")
    print("  2. researchteam personalize   # regenerate README.md / CLAUDE.md header from brief.json")
    print("  3. researchteam materialize   # render the agent team from your edited brief.json")
    print("  bash scripts/claude_researchteam_bridge.sh help")
    print(
        "\nNote: strict decision signing is ON (enforce_decision_signing:true, agentteams' secure "
        "default), so an agent can never clear its own destructive action. 'materialize' therefore "
        "needs one operator-signed clearance first:\n"
        "  export AGENTTEAMS_DECISION_SIGNING_KEY=\"$(python3 -c 'import secrets; print(secrets.token_hex(32))')\"\n"
        "      # operator-held, >= 32 bytes; keep it outside the repo and every agent environment\n"
        "  python scripts/sign_security_decision.py --action overwrite --conditions \"first render\"\n"
        "  researchteam materialize --yes\n"
        "See docs/researchteam-framework.md (Decision signing)."
    )


def _populate(target: Path, tarball: bytes, members: set[str], links: list[str], ref: str,
              remote_url: str | None) -> None:
    """Write the checked archive into ``target``, then the scaffold, marker, identity files and git repo."""
    print("[researchteam] Extracting template files ...")
    if links:
        print(f"[researchteam] Warning: skipped {len(links)} link member(s) in the archive: "
              f"{', '.join(links[:5])}", file=sys.stderr)
    _extract(tarball, target, members)

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


class ArchiveError(Exception):
    """An upstream archive init will not extract: a member path that could escape the target."""


_HEX = re.compile(r"^[0-9a-f]{7,40}$")
_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


def _rel(name: str) -> str | None:
    """A member's path with the archive's top directory stripped; None for the top directory itself."""
    parts = PurePosixPath(name).parts
    return "/".join(parts[1:]) if len(parts) >= 2 else None


def _validate_archive(tarball: bytes) -> tuple[set[str], list[str], str]:
    """``(file and directory members to write, skipped link members, top directory)``.

    Refuses the whole archive (``ArchiveError``) when any member is absolute or has a ``..`` segment: the
    upstream archive never contains one, so it means tampering. Does not need ``tarfile``'s ``filter=``
    (absent before Python 3.10.12).
    """
    try:
        with tarfile.open(fileobj=io.BytesIO(tarball), mode="r:gz") as tf:
            infos = tf.getmembers()
    except (tarfile.TarError, OSError, EOFError) as exc:
        raise ArchiveError(f"the template archive cannot be read ({exc})") from exc
    members, links, tops = set(), [], set()
    for info in infos:
        path = PurePosixPath(info.name)
        if path.is_absolute() or ".." in path.parts or info.name.startswith("\\"):
            raise ArchiveError(f"the template archive has an unsafe member path {info.name!r}; refusing it")
        if path.parts:
            tops.add(path.parts[0])
        rel = _rel(info.name)
        if rel is None or _should_skip(rel):
            continue
        if info.issym() or info.islnk():
            links.append(rel)
        elif info.isfile() or info.isdir():
            members.add(info.name)
    if len(tops) != 1:
        raise ArchiveError(f"the template archive has {len(tops)} top-level directories, expected 1")
    return members, links, tops.pop()


def _extract(tarball: bytes, target: Path, members: set[str]) -> None:
    """Write the members :func:`_validate_archive` accepted; each destination must resolve inside ``target``."""
    root = target.resolve()
    with tarfile.open(fileobj=io.BytesIO(tarball), mode="r:gz") as tf:
        for member in tf.getmembers():
            if member.name not in members:
                continue
            dest = (target / _rel(member.name)).resolve()
            if root not in dest.parents:
                raise OSError(f"archive member {member.name!r} resolves outside {root}")
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
