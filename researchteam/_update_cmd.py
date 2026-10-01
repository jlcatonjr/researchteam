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
    BRIEF_PLACEHOLDER,
    FENCE_CORE_BEGIN,
    FENCE_CORE_END,
    MERGE_STRATEGIES,
    UPSTREAM_REPO,
    managed_files_for,
)
from ._fetch import fetch_raw


def _split_fence(text: str) -> tuple[str, str, str] | None:
    """Split ``text`` around the researchteam:managed fence.

    Returns ``(pre, managed, post)`` where ``managed`` INCLUDES both marker lines, or ``None``
    when a well-formed fence (BEGIN then END, in order) is absent. A marker line is recognized by
    the presence of its sentinel CORE anywhere in the stripped line, so BOTH the shell-comment
    idiom (``# >>> researchteam:managed …``) used by ``.gitignore`` and the HTML-comment idiom
    (``<!-- >>> researchteam:managed … -->``) used by markdown files match, along with any
    self-documenting trailing prose. ``>>>`` vs ``<<<`` keep BEGIN and END unambiguous.
    """
    lines = text.splitlines(keepends=True)
    begin_idx = end_idx = None
    for i, ln in enumerate(lines):
        stripped = ln.strip()
        if begin_idx is None and FENCE_CORE_BEGIN in stripped:
            begin_idx = i
        elif begin_idx is not None and FENCE_CORE_END in stripped:
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


def _read_brief_profile(root: Path) -> str | None:
    """Return the brief's ``layer2_profile`` (``"scholarly"`` | ``"generic"``) or ``None``.

    A missing brief, unreadable JSON, or an absent field all return ``None`` so the caller falls
    back to the scholarly default (``managed_files_for(None)``).
    """
    brief = root / "brief.json"
    if not brief.exists():
        return None
    try:
        data = json.loads(brief.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    value = data.get("layer2_profile")
    return value if isinstance(value, str) else None


def _brief_has_placeholder(root: Path) -> bool:
    """True when brief.json still carries the scaffold placeholder identity.

    Running the layer-1 agentteams pass in that state would bake ``<YOUR PROJECT NAME>`` into every
    generated agent/persona file, so ``update`` and ``materialize`` refuse until the brief is
    edited.
    """
    brief = root / "brief.json"
    if not brief.exists():
        return False
    try:
        return BRIEF_PLACEHOLDER in brief.read_text(encoding="utf-8")
    except OSError:
        return False


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
        # The merge may change canonical agents; keep the Codex projection in step.
        _refresh_codex(root, dry_run=dry_run)
        return

    profile = _read_brief_profile(root)
    managed = managed_files_for(profile)
    print(
        f"[researchteam] Syncing layer-2 files from {UPSTREAM_REPO}@{ref} "
        f"(layer2_profile={profile or 'scholarly'}, {len(managed)} managed files) ..."
    )

    updated: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []

    for rel_path in managed:
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
    # The merge may change canonical agents; keep the Codex projection in step.
    _refresh_codex(root, dry_run=dry_run)


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


def _reconcile_manifest_back(root: Path) -> None:
    """Persist brief.json's content fields into ``.github/agents/_build-description.json`` (RT-5).

    ``_resolve_descriptor`` reconciles the two descriptors only into a throwaway temp file for the
    agentteams run, so the on-disk manifest stays stale and the ``[WARN] Dual descriptor detected``
    notice fires on every subsequent generation. This writes the reconciliation back: brief.json is
    the content-of-record, so every brief key EXCEPT the roster fields the manifest owns
    (``selected_archetypes`` / ``governance_agents``) is overlaid onto the manifest. Idempotent and
    silent when nothing changes or a descriptor is missing/unreadable.
    """
    brief_path = root / "brief.json"
    manifest_path = root / ".github" / "agents" / "_build-description.json"
    if not brief_path.exists() or not manifest_path.exists():
        return
    try:
        brief = json.loads(brief_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return

    roster_owned = {"selected_archetypes", "governance_agents"}
    changed = False
    for key, value in brief.items():
        if key in roster_owned:
            continue
        if manifest.get(key) != value:
            manifest[key] = value
            changed = True
    if not changed:
        return
    try:
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(
            "[researchteam] Reconciled _build-description.json content fields from brief.json "
            "(RT-5: dual-descriptor divergence resolved)."
        )
    except OSError as exc:
        print(f"[researchteam] Could not persist descriptor reconciliation: {exc}", file=sys.stderr)


#: Native agent surfaces besides the default copilot-vscode team (``.github/agents``) that a
#: scaffold may ship. Each is a separate agentteams render target with its own decisions log.
NATIVE_SURFACES: tuple[tuple[str, str], ...] = (("claude", ".claude/agents"), ("goose", ".goose/recipes"))


def _native_surfaces(root: Path) -> list[tuple[str, str]]:
    """Return the ``(framework, dir)`` native surfaces present in *root*.

    A surface counts as present when its directory holds an agentteams build-log, i.e. a native
    team was rendered there before. A bare bridge directory is left alone.
    """
    return [(fw, d) for fw, d in NATIVE_SURFACES if (root / d / "references" / "build-log.json").exists()]


def _run_agentteams(
    root: Path,
    yes: bool,
    dry_run: bool,
    overwrite: bool = False,
    framework: str | None = None,
    adopt_orphans: bool = False,
) -> None:
    if _brief_has_placeholder(root):
        msg = (
            f"[researchteam] brief.json still contains the scaffold placeholder "
            f"'{BRIEF_PLACEHOLDER}'.\n"
            "  Edit brief.json (project_name, project_goal, deliverables, authority_sources) to\n"
            "  describe YOUR project before generating the agent team — otherwise the placeholder\n"
            "  identity is baked into every generated agent file.\n"
            "  Then re-run:  researchteam update   (or  researchteam materialize  to re-render)."
        )
        if dry_run:
            print(msg + "\n[researchteam] (dry-run) skipping layer-1 agentteams pass.")
            return
        sys.exit(msg)

    exe = _preflight_agentteams()
    descriptor, tmp = _resolve_descriptor(root)

    if overwrite:
        # RT-1/RT-2 re-render path (`researchteam materialize`): --overwrite REPLACES enriched
        # bodies so a brief/domain change actually re-brands the instance. This is the cleared
        # path the `--merge --shrink-policy preserve` default deliberately refuses; agentteams'
        # destructive-overwrite security gate must be satisfied by a clearance in the target
        # surface's own decisions log (see docs/researchteam-framework.md, Decision signing).
        target = f"{framework} surface" if framework else "copilot-vscode surface"
        print(
            f"\n[researchteam] Running agentteams --update --overwrite on the {target} "
            f"(descriptor: {descriptor}) — re-rendering agent bodies from the brief ..."
        )
        cmd = [exe, "--description", descriptor, "--update", "--overwrite"]
        if framework:
            # Native (non-copilot) surfaces sit behind a bridge marker; agentteams fails closed on
            # --update against a bridge unless the native re-render is requested explicitly.
            cmd += ["--framework", framework, "--project", ".", "--materialize-native"]
        if adopt_orphans:
            # Register bespoke agent files (no agentteams template) into the orchestrator roster
            # without generating or overwriting them. agentteams does not persist adoption, so it
            # must be requested on every render.
            cmd.append("--adopt-orphans")
    else:
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

    # RT-5: persist the descriptor reconciliation so the dual-descriptor warning does not recur.
    if not dry_run and framework is None:
        _reconcile_manifest_back(root)


def _refresh_codex(root: Path, dry_run: bool) -> None:
    """Re-project the Codex surface after a render, if the instance carries one.

    Codex is an interop projection, not a native render target: agents come from the canonical
    copilot-vscode team (``.github/agents`` -> ``.codex/agents/*.toml``), and skills come from
    the Claude skills (``.claude/skills`` -> ``.agents/skills``, via ``--interop-skills-only``).
    Without this step a render leaves ``.codex`` on the previous roster.
    """
    if not (root / ".codex" / "agents").is_dir():
        return
    exe = _preflight_agentteams()
    # --overwrite is required: without it interop SKIPS existing files, so an already-projected
    # agent or skill would never pick up later canonical changes. Codex files are pure generated
    # projections (never hand-edited), so full replacement is correct.
    runs = [[exe, "--interop-from", ".github/agents", "--framework", "codex", "--output", ".",
             "--overwrite", "--yes"]]
    if (root / ".claude" / "skills").is_dir():
        runs.append([exe, "--interop-from", ".claude/agents", "--interop-source-framework", "claude",
                     "--framework", "codex", "--interop-skills-only", "--output", ".", "--overwrite", "--yes"])
    for cmd in runs:
        if dry_run:
            cmd.append("--dry-run")
        print(f"[researchteam] materialize: refreshing Codex projection ({' '.join(cmd[1:4])} ...)")
        result = subprocess.run(cmd, cwd=str(root))
        if result.returncode != 0:
            print("[researchteam] materialize: Codex projection FAILED; the rendered surfaces are "
                  "current, .codex is not. Fix the cause and re-run.", file=sys.stderr)
            sys.exit(result.returncode)
    _prune_stale_codex_agents(root, dry_run=dry_run)
    if not dry_run:
        _check_codex_team_marker(root)


def _check_codex_team_marker(root: Path) -> None:
    """Warn when the Codex projection left no team marker.

    Since agentteams ``d31d4a0`` an interop projection writes ``references/build-log.json`` (with
    ``"origin": "interop"``), so agentteams recognises ``.codex/agents`` as a team: verify-key store
    sentinel, roster stubs, launcher protection, fleet/--update discovery. An older agentteams writes
    none, and the Codex team stays unrecognised. This is a warning, not a failure: the projected
    agents themselves are still current.
    """
    marker = root / ".codex" / "agents" / "references" / "build-log.json"
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = None
    if not isinstance(data, dict):
        print("[researchteam] materialize: WARNING: the Codex projection wrote no team marker "
              "(.codex/agents/references/build-log.json). The installed agentteams predates the "
              "interop team-marker fix (agentteams d31d4a0); upgrade it so agentteams recognises the "
              "Codex team.", file=sys.stderr)


#: First line agentteams writes into every projected Codex agent. Only files carrying it are ever
#: pruned, so a hand-authored Codex agent is never deleted.
_CODEX_GENERATED_HEADER = "# Codex custom agent — generated by agentteams"


def _prune_stale_codex_agents(root: Path, dry_run: bool) -> None:
    """Remove generated Codex agents whose canonical source no longer exists.

    The interop projection only adds or updates ``.codex/agents/*.toml``; it never deletes one
    whose ``.github/agents/<slug>.agent.md`` was removed, so a retired agent would linger in Codex.
    Only files that carry the agentteams generation header are candidates.
    """
    canonical = {p.name[: -len(".agent.md")] for p in (root / ".github" / "agents").glob("*.agent.md")}
    for toml in sorted((root / ".codex" / "agents").glob("*.toml")):
        if toml.stem in canonical:
            continue
        try:
            first = toml.read_text(encoding="utf-8").splitlines()[0]
        except (OSError, IndexError):
            continue
        if not first.startswith(_CODEX_GENERATED_HEADER):
            continue
        verb = "would prune" if dry_run else "pruned"
        print(f"[researchteam] materialize: {verb} stale Codex agent {toml.name} (no canonical source)")
        if not dry_run:
            toml.unlink()


def run_materialize(
    root: Path,
    yes: bool,
    dry_run: bool,
    copilot_only: bool = False,
    adopt_orphans: bool = False,
    codex: bool = True,
) -> None:
    """Re-render a derived instance from its (edited) brief.json — RT-1/RT-2 cleared re-render.

    ``update`` intentionally cannot re-brand an instance whose domain/identity changed, because it
    runs ``agentteams --merge --shrink-policy preserve`` (enriched bodies are protected). This is
    the distinct, explicit path that DOES replace them: it runs the destructive ``--overwrite``
    agentteams pass, then re-personalizes the layer-2 identity files (README.md / CLAUDE.md) from
    the current brief. Use it after materially changing brief.json (e.g. a new project domain).

    Every native surface the instance carries (``.claude/agents``, ``.goose/recipes``) is
    re-rendered too, from the SAME reconciled descriptor, so all surfaces share one roster.
    Rendering only copilot-vscode left the other surfaces on the scaffold's identity and let
    their rosters drift. ``copilot_only`` restores the old single-surface behaviour.

    ``adopt_orphans`` passes ``--adopt-orphans`` to every surface's render, so bespoke agents
    (files with no agentteams template) stay in the orchestrator roster. When the instance
    carries a Codex surface (``.codex/agents``), its agents and skills are re-projected after the
    renders unless ``codex`` is False.
    """
    from ._personalize import is_upstream, run_personalize

    if is_upstream(root):
        sys.exit(
            "[researchteam] Refusing to materialize the UPSTREAM repository "
            "(.researchteam has is_upstream = true). Run this in a derived instance."
        )
    if _brief_has_placeholder(root):
        # _run_agentteams would also refuse, but fail early with the same actionable message.
        sys.exit(
            f"[researchteam] brief.json still contains the placeholder '{BRIEF_PLACEHOLDER}'. "
            "Edit it to describe your project before materializing."
        )

    print(
        "[researchteam] materialize: this REPLACES generated agent bodies with a fresh render "
        "from brief.json (destructive to enriched fenced content)."
    )
    if not dry_run and not yes:
        answer = input("Proceed with the overwrite re-render? [y/N] ").strip().lower()
        if answer != "y":
            print("[researchteam] Aborted; nothing changed.")
            return

    # Layer-1: overwrite re-render (+ RT-5 write-back happens inside _run_agentteams on success).
    _run_agentteams(root, yes=yes, dry_run=dry_run, overwrite=True, adopt_orphans=adopt_orphans)
    if not copilot_only:
        surfaces = _native_surfaces(root)
        done = [".github/agents (copilot-vscode)"]
        for i, (framework, directory) in enumerate(surfaces):
            print(f"[researchteam] materialize: native surface {directory} ({framework})")
            try:
                _run_agentteams(root, yes=yes, dry_run=dry_run, overwrite=True, framework=framework,
                                adopt_orphans=adopt_orphans)
            except SystemExit:
                pending = [f"{d} ({fw})" for fw, d in surfaces[i + 1:]]
                print(
                    f"[researchteam] materialize: FAILED on {directory} ({framework}).\n"
                    f"  already re-rendered: {', '.join(done)}\n"
                    f"  not attempted: {', '.join(pending) or 'none'}; README/CLAUDE not re-personalized.\n"
                    "  Fix the cause (usually a missing clearance in that surface's decisions log) and re-run.",
                    file=sys.stderr,
                )
                raise
            done.append(f"{directory} ({framework})")
        if not surfaces:
            print("[researchteam] materialize: no native claude/goose surfaces present.")
    if codex:
        _refresh_codex(root, dry_run=dry_run)

    # Layer-2 identity: re-render README/CLAUDE from the now-current brief. Files generated at init
    # and untouched since are refreshed in place; a hand-diverged file is left alone (see
    # run_personalize's content-hash guard) unless the operator passes force.
    if not dry_run:
        run_personalize(root, force=False, quiet=False)
    else:
        print("[researchteam] (dry-run) would re-personalize README.md / CLAUDE.md from brief.json.")
