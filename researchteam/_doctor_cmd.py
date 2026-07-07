"""Implementation of `researchteam doctor` — toolchain health check.

Validates the `researchteam` ↔ `agentteams` integration end-to-end and prints a
green/red report. Designed to diagnose (before it bites) the exact failure class that
produced this repo's outage: a stale editable `agentteams` install whose finder points at
a deleted temporary path.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

_EPHEMERAL_MARKERS = ("/tmp/", "/private/tmp/", "-worktree", "scratchpad", "/var/folders/")


def run_doctor(root: Path) -> None:
    problems = 0

    def ok(msg: str) -> None:
        print(f"  [ok]   {msg}")

    def warn(msg: str) -> None:
        print(f"  [warn] {msg}")

    def fail(msg: str) -> None:
        nonlocal problems
        problems += 1
        print(f"  [FAIL] {msg}", file=sys.stderr)

    print("[researchteam] doctor — checking researchteam ↔ agentteams toolchain\n")

    # --- 1. agentteams resolves on PATH ------------------------------------------------
    exe = shutil.which("agentteams")
    if exe is None:
        fail(
            "agentteams not found on PATH — Layer-1 `researchteam update` will fail.\n"
            "         Install from the canonical checkout: pip install -e <path-to-agentteams>"
        )
    else:
        ok(f"agentteams on PATH: {exe}")

        # --- 2. agentteams is runnable (import assertion via --version) ----------------
        probe = subprocess.run([exe, "--version"], capture_output=True, text=True)
        if probe.returncode != 0:
            tail = ((probe.stderr or probe.stdout).strip().splitlines() or ["(no output)"])[-1]
            fail(
                "agentteams is installed but not runnable — likely a stale editable install "
                "pointing at a deleted path.\n"
                f"         Reinstall: <that-python> -m pip install -e <path-to-agentteams>\n"
                f"         Detail: {tail[:200]}"
            )
        else:
            ok(f"agentteams runnable: {(probe.stdout or probe.stderr).strip()}")

            # --- 3. ephemeral-install smell -------------------------------------------
            interp = _script_interpreter(exe)
            src = _agentteams_source(interp)
            if src is None:
                warn("could not resolve agentteams source path for the ephemeral-install check")
            elif any(marker in src for marker in _EPHEMERAL_MARKERS):
                fail(
                    f"agentteams is installed from an EPHEMERAL path:\n         {src}\n"
                    "         This will break the moment that path is cleaned up. Reinstall "
                    "from a stable checkout:\n"
                    f"         {interp} -m pip install -e <stable-agentteams-checkout>"
                )
            else:
                ok(f"agentteams source is stable: {src}")

    # --- 4. descriptor health (content vs roster reconciliation) -----------------------
    brief = root / "brief.json"
    manifest = root / ".github" / "agents" / "_build-description.json"
    brief_doc = _load(brief)
    manifest_doc = _load(manifest)

    if not brief.exists():
        warn("brief.json missing — cannot supply content fields (authority_sources, style_rules).")
    else:
        missing = [f for f in ("authority_sources", "style_rules") if not brief_doc.get(f)]
        if missing:
            warn(
                f"brief.json is missing {missing}; the corresponding managed fences "
                "(authority_sources_list / style_rules_summary) may render as placeholders."
            )
        else:
            ok("brief.json carries authority_sources + style_rules (content fences safe).")

    if not manifest.exists():
        warn(
            ".github/agents/_build-description.json missing — an update from brief.json alone "
            "may orphan registered archetypes."
        )
    else:
        roster = manifest_doc.get("selected_archetypes") or []
        if roster:
            ok(f"_build-description.json roster: {len(roster)} archetype(s) recorded.")
        else:
            warn("_build-description.json has no selected_archetypes.")

    if brief.exists() and manifest.exists():
        brief_has_roster = bool(brief_doc.get("selected_archetypes"))
        if brief_has_roster:
            ok("brief.json already carries the roster; update uses it directly.")
        else:
            ok(
                "update will reconcile brief.json (content) + _build-description.json (roster) "
                "into a union descriptor — no orphaned archetypes, no shrunk content fences."
            )

    # --- summary ----------------------------------------------------------------------
    print()
    if problems == 0:
        print("[researchteam] doctor: all critical checks passed.")
    else:
        print(
            f"[researchteam] doctor: {problems} problem(s) found (see [FAIL] above).",
            file=sys.stderr,
        )
        sys.exit(1)


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _script_interpreter(exe: str) -> str:
    """Read the console script's shebang to find the interpreter that owns it."""
    try:
        first = Path(exe).read_text(encoding="utf-8", errors="replace").splitlines()[0]
        if first.startswith("#!"):
            return first[2:].strip().split()[0]
    except (OSError, IndexError):
        pass
    return sys.executable


def _agentteams_source(interp: str) -> str | None:
    """Ask the owning interpreter where build_team is imported from (for the smell check)."""
    try:
        result = subprocess.run(
            [interp, "-c", "import build_team, os; print(os.path.dirname(os.path.abspath(build_team.__file__)))"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except OSError:
        pass
    return None
