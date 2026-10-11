"""Implementation of `researchteam doctor` — toolchain health check.

Validates the `researchteam` ↔ `agentteams` integration end-to-end and prints a
green/red report. Designed to diagnose (before it bites) the exact failure class that
produced this repo's outage: a stale editable `agentteams` install whose finder points at
a deleted temporary path.
"""

import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

_EPHEMERAL_MARKERS = ("/tmp/", "/private/tmp/", "-worktree", "scratchpad", "/var/folders/")


def run_doctor(root: Path, drift: bool = False) -> None:
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

    from ._update_cmd import _resolve_agentteams, layer1_enabled

    layer1 = layer1_enabled(root)
    if not layer1:
        ok(".researchteam declares layer1 = off: `update` syncs layer 2 only; agentteams checks skipped.")
    else:
        # --- 1. agentteams resolves (beside this researchteam first, else PATH) -------------

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

    # --- 3d. frozen fences (offline; from the last update's shrink review report) -------
    _check_frozen_fences(root, ok, warn)

    # --- 3e. seeded files + bridges (opt-in: network / agentteams) ---------------------
    if drift:
        _check_seeded_files(root, ok, warn)
        _check_bridges(root, ok, warn)

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


def _check_frozen_fences(root: Path, ok, warn) -> None:
    """List the sections the shrink guard kept frozen at the last update, with age and intent."""
    from ._drift import age_days, clean, first_seen, load_frozen, load_intentional

    items = load_frozen(root)
    if not items:
        ok("frozen fences: none recorded at the last `researchteam update` (or none run yet here).")
        return
    intentional, seen = load_intentional(root), first_seen(root)
    review = [i for i in items if i["section"] not in intentional]
    (warn if review else ok)(f"frozen fences: {len(items)} kept by the shrink guard "
                             f"({len(items) - len(review)} intentional, {len(review)} to review).")
    for i in items:
        since = seen.get(f"{i['surface']}|{i['section']}")
        days = age_days(since) if since else None
        age = f"frozen {days}d (since {clean(since)})" if days is not None else "age unknown"
        where = clean(f"{i['surface']}: {i['section']}")
        if i["section"] in intentional:
            ok(f"  {where} — intentional: {clean(intentional[i['section']]) or '(no reason given)'}; {age}")
        else:
            hint = " — every lost token is retired upstream; safe to release" if i["all_retired"] else ""
            release = shlex.quote(f"AGENTTEAMS_SHRINK_ALLOW={clean(i['entry'])}")
            # A section above the agents dir ('../' entry) is releasable only from agentteams 5f8503e
            # (#192); older agentteams refused such grants (researchteam keeps the report either way).
            needs = " (needs agentteams 5f8503e or later)" if clean(i["entry"]).startswith("../") else ""
            warn(f"  {where} — {age}{hint}. Release after review: {release}{needs}")


def _check_seeded_files(root: Path, ok, warn) -> None:
    """Seeded-but-unsynced files whose upstream-owned part differs from upstream at the pinned commit."""
    from ._drift import SAFE_REF, clean, comparable_body
    from ._fetch import fetch_raw
    from ._manifest import SEEDED_FILES, UPSTREAM_REPO

    if not SEEDED_FILES:
        ok("seeded files: none (every file init seeds is now managed or project-owned).")
        return
    ref, how = _upstream_ref(root)
    if not SAFE_REF.match(ref):
        warn(f"seeded files: not checked; the upstream ref {clean(ref)!r} ({how}) is not a plain commit or name")
        return
    behind = failed = 0
    for rel in SEEDED_FILES:
        local = root / rel
        try:
            upstream = fetch_raw(UPSTREAM_REPO, ref, rel)
        except RuntimeError as exc:
            warn(f"seeded {rel}: could not fetch upstream @{ref[:12]} ({clean(exc)})")
            failed += 1
            continue
        if not local.exists():
            warn(f"seeded {rel}: missing locally (upstream @{ref[:12]} has it)")
            behind += 1
        elif comparable_body(local.read_text(encoding="utf-8")) != comparable_body(upstream):
            warn(f"seeded {rel}: differs from upstream @{ref[:12]} ({how}) outside Project-Specific Notes")
            behind += 1
    if not behind and not failed:
        ok(f"seeded files match upstream @{ref[:12]} ({how}) outside Project-Specific Notes.")


def _upstream_ref(root: Path) -> tuple[str, str]:
    """The researchteam commit to compare against: toolchain.lock's pin, else the marker ref, else main."""
    lock = root / "toolchain.lock"
    if lock.exists():
        for line in lock.read_text(encoding="utf-8").splitlines():
            if line.startswith("researchteam=") and "@" in line:
                return line.rsplit("@", 1)[1].strip(), "toolchain.lock pin"
    marker = None
    try:
        m = re.search(r"^ref\s*=\s*(\S+)", (root / ".researchteam").read_text(encoding="utf-8"), re.M)
        marker = m.group(1).strip("\"'") if m else None
    except OSError:
        pass
    return (marker or "main"), ("marker ref" if marker else "main")


def _check_bridges(root: Path, ok, warn) -> None:
    """Run agentteams --bridge-check for every recorded copilot-vscode bridge."""
    from ._drift import BRIDGES_DIR, bridge_frameworks, clean, parse_bridge_report
    from ._update_cmd import _preflight_agentteams

    frameworks = bridge_frameworks(root)
    if not frameworks:
        ok("bridges: none recorded under references/bridges/.")
        return
    try:
        exe = _preflight_agentteams()  # the same resolution + provenance check a render gets
    except SystemExit as exc:
        warn(f"bridges: not checked; agentteams did not pass the pre-flight ({clean(exc)})")
        return
    for fw in frameworks:
        report = root / BRIDGES_DIR / f"copilot-vscode-to-{fw}" / "bridge-check.report.md"
        report.unlink(missing_ok=True)  # never show an earlier run's verdict as this one's
        try:
            r = subprocess.run([exe, "--bridge-from", ".github/agents", "--framework", fw, "--output", ".",
                                "--bridge-check"], cwd=str(root), capture_output=True, text=True, timeout=300)
        except (OSError, subprocess.TimeoutExpired) as exc:
            warn(f"bridge copilot-vscode→{clean(fw)}: --bridge-check could not run ({clean(exc)})")
            continue
        result, changed = parse_bridge_report(report.read_text(encoding="utf-8")) if report.exists() else ("UNKNOWN", [])
        if r.returncode == 0 and result == "PASS":
            ok(f"bridge copilot-vscode→{clean(fw)}: PASS")
            continue
        detail = f"; changed since last merge: {clean(', '.join(changed[:5]))}" if changed else ""
        if result == "UNKNOWN":
            tail = ((r.stderr or r.stdout).strip().splitlines() or ["(no output)"])[-1]
            detail += f"; agentteams said: {clean(tail[:200])}"
        refresh = shlex.join(["agentteams", "--bridge-from", ".github/agents", "--framework", fw,
                              "--output", ".", "--bridge-merge"])
        warn(f"bridge copilot-vscode→{clean(fw)}: {clean(result)}{detail}. Refresh: {clean(refresh)}")
