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

    # --- 1. agentteams resolves (beside this researchteam first, else PATH) -------------
    from ._update_cmd import _resolve_agentteams

    exe, where = _resolve_agentteams()
    if exe is None:
        fail(
            "agentteams found neither beside this researchteam nor on PATH — Layer-1 "
            "`researchteam update` will fail.\n"
            "         In a derived repo: bash scripts/bootstrap_toolchain.sh"
        )
    else:
        ok(f"agentteams: {exe} ({where})")

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

            # --- 3b. F-CODEIDX capability probe (advisory) ----------------------------
            # The code & API index (retrieval surface #2) rides in on the agentteams
            # `update` extra. If the resolved agentteams predates it, `--query-code` /
            # `/code-recall` / the bridge `code-query` command are unavailable. Advisory,
            # not fatal (the base workflow does not require it).
            help_probe = subprocess.run([exe, "--help"], capture_output=True, text=True)
            help_text = (help_probe.stdout or "") + (help_probe.stderr or "")
            if "--query-code" in help_text:
                ok("agentteams exposes the code & API index (--query-code); surface #2 available.")
            else:
                warn(
                    "agentteams does not expose --query-code — the code & API index (F-CODEIDX) is "
                    "unavailable.\n"
                    "         Refresh the extra: pip install -U 'agentteams @ "
                    "git+https://github.com/jlcatonjr/agentteams'. See docs/retrieval-surfaces.md."
                )

    # --- 3c. toolchain pin (toolchain.lock) + SessionStart wiring (advisory) ------------
    _check_toolchain(root, ok, warn)

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


def _check_toolchain(root: Path, ok, warn) -> None:
    """Report the repo's toolchain.lock check for THIS interpreter, and whether it runs at SessionStart.

    Advisory only: a missing or stale pin never fails doctor (the autosync PR moves the pin).
    """
    from ._update_cmd import TOOLCHAIN_HOOK_EXAMPLE, TOOLCHAIN_HOOK_SCRIPT, _toolchain_hook_installed

    script = root / TOOLCHAIN_HOOK_SCRIPT
    if not script.exists():
        warn(f"{TOOLCHAIN_HOOK_SCRIPT} not present — run `researchteam update` to receive the toolchain check.")
        return
    try:
        r = subprocess.run([sys.executable, str(script), "--python", sys.executable],
                           capture_output=True, text=True, timeout=60)
        lines = [ln for ln in (r.stdout or "").splitlines() if ln.strip()]
    except (OSError, subprocess.TimeoutExpired) as exc:
        lines = [f"[toolchain] check could not run: {exc}"]
    for line in lines or ["[toolchain] (no output)"]:
        (ok if line.startswith("[toolchain] OK") else warn)(line.removeprefix("[toolchain] "))
    if _toolchain_hook_installed(root):
        ok("toolchain check runs at SessionStart (.claude/settings.json).")
    else:
        warn(f"toolchain check is not wired to SessionStart — merge {TOOLCHAIN_HOOK_EXAMPLE} "
             "into .claude/settings.json (operator step).")

