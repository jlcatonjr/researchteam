"""Declared frozen surfaces: the shared agentteams/researchteam contract (researchteam 1.0.1).

``brief.json`` may carry ``frozen_surfaces``, a JSON array of unique framework ids. For every listed surface,
researchteam never renders, merges, projects, converts, bridges, Notes-syncs, managed-syncs, overwrites, deletes
over that surface's files (it only restores a frozen ``AGENTS.md``'s own earlier bytes), including the root paths it owns. The same key, with the same meaning, is
honoured by agentteams 1.0.x (agentteams ``tmp/by-week/2026-W42/f3-drafts/design/frozen-surfaces-1.0.x.design.md``,
"Shared contract with researchteam"); agentteams' freeze manifest and ``--freeze-surface`` are agentteams-only.

- An absent key or ``[]`` freezes nothing. An unknown id, a duplicate or a non-array value refuses the run: a value
  researchteam does not understand is never ignored.
- The root ``AGENTS.md`` is frozen when any surface that can own it (codex, goose, agents-md) is listed. Over-freezing
  it only narrows what is written.
- **Unfreeze.** researchteam records the frozen set it last honoured in ``.researchteam``. A surface that is recorded
  (in the working tree or at git HEAD, :func:`at_head`) but no longer listed is an unfreeze, which is
  constraint-relaxing. researchteam renders into it only when the
  pinned agentteams' own security gate says that an ``unfreeze-<surface>`` decision row clears, derives (never
  self-declares) as constraint-relaxing and needing the operator's signature, and is Ed25519-signed (:func:`verify_unfreeze`, run under agentteams' interpreter, so
  there is one security implementation). Anything less refuses, including an agentteams too old to say.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from subprocess import run as _run  # bound at import: callers' test fakes of subprocess.run never reach it

SURFACE_IDS = ("copilot-vscode", "copilot-cli", "claude", "goose", "agents-md", "codex", "grok")
# Paths each surface owns (relative to the repository root; a trailing "/" means the whole directory).
OWNED: dict[str, tuple[str, ...]] = {
    "copilot-vscode": (".github/agents/",),
    "copilot-cli": (".github/agents/",),
    "claude": (".claude/agents/",),
    "goose": (".goose/",),
    "agents-md": (),
    "codex": (".codex/", ".agents/skills/"),
    "grok": (".grok/",),
}
AGENTS_MD = "AGENTS.md"
AGENTS_MD_OWNERS = frozenset({"codex", "goose", "agents-md"})
MARKER_KEY = "frozen_surfaces"


class FrozenSurfacesError(ValueError):
    """A ``frozen_surfaces`` value researchteam cannot honour exactly; the run refuses."""


def load(root: Path) -> frozenset[str]:
    """The validated frozen set from ``brief.json`` (empty when the key is absent or the brief is missing)."""
    try:
        brief = json.loads((root / "brief.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        return frozenset()
    except (OSError, ValueError) as exc:
        raise FrozenSurfacesError(f"brief.json is unreadable, so frozen_surfaces can't be checked: {exc}") from exc
    if not isinstance(brief, dict) or MARKER_KEY not in brief:
        return frozenset()
    value = brief[MARKER_KEY]
    if not isinstance(value, list):
        raise FrozenSurfacesError(f"brief.json frozen_surfaces must be a JSON array, not {type(value).__name__}")
    unknown = [v for v in value if not isinstance(v, str) or v not in SURFACE_IDS]
    if unknown:
        raise FrozenSurfacesError(f"brief.json frozen_surfaces has unknown id(s) {unknown!r}; "
                                  f"allowed: {', '.join(SURFACE_IDS)}")
    if len(set(value)) != len(value):
        raise FrozenSurfacesError(f"brief.json frozen_surfaces has duplicates: {value!r}")
    return frozenset(value)


def owned_paths(frozen: frozenset[str]) -> tuple[str, ...]:
    """Every path a frozen set owns, including the root AGENTS.md when an owner is listed."""
    paths = sorted({p for s in frozen for p in OWNED[s]})
    if frozen & AGENTS_MD_OWNERS:
        paths.append(AGENTS_MD)
    return tuple(paths)


def is_frozen_path(rel: str, frozen: frozenset[str]) -> bool:
    """Whether ``rel`` (a repository-relative path) belongs to a frozen surface."""
    if rel.startswith("./"):
        rel = rel[2:]
    for p in owned_paths(frozen):
        if (p.endswith("/") and (rel + "/").startswith(p)) or rel == p:
            return True
    return False


def snapshot(root: Path, frozen: frozenset[str]) -> dict[str, str]:
    """``{relative path: sha256}`` of every file under the frozen paths (a missing file is recorded as absent)."""
    out: dict[str, str] = {}
    for p in owned_paths(frozen):
        base = root / p.rstrip("/")
        files = ([f for f in base.rglob("*") if f.is_file() and not f.is_symlink()] if p.endswith("/")
                 else [base] if base.is_file() else [])
        for f in files:
            out[str(f.relative_to(root))] = hashlib.sha256(f.read_bytes()).hexdigest()
        if not p.endswith("/") and not base.exists():
            out[p] = "absent"
    return out


def changed_since(root: Path, frozen: frozenset[str], before: dict[str, str]) -> list[str]:
    """Frozen files that were added, removed or modified since :func:`snapshot` returned ``before``."""
    after = snapshot(root, frozen)
    return sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))


# --- the recorded set (what researchteam last honoured) ---------------------------------------------------------

_MARKER_RE = re.compile(rf"^{MARKER_KEY}\s*=\s*(.*)$", re.M)


def recorded(root: Path) -> frozenset[str]:
    """The frozen set researchteam last honoured, from ``.researchteam`` (empty when never recorded)."""
    try:
        m = _MARKER_RE.search((root / ".researchteam").read_text(encoding="utf-8"))
    except OSError:
        return frozenset()
    return frozenset(s for s in (m.group(1).replace(",", " ").split() if m else []) if s in SURFACE_IDS)


def at_head(root: Path) -> frozenset[str]:
    """The frozen set ``brief.json`` and ``.researchteam`` declare at git HEAD (empty outside git or when absent)."""
    out: set[str] = set()
    for rel in ("brief.json", ".researchteam"):
        try:
            r = _run(["git", "-C", str(root), "-c", "core.hooksPath=/dev/null", "show", f"HEAD:{rel}"],
                               capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if r.returncode != 0:
            continue
        if rel == "brief.json":
            try:
                value = json.loads(r.stdout).get(MARKER_KEY, [])
            except (ValueError, AttributeError):
                continue
            out |= {v for v in value if isinstance(v, str) and v in SURFACE_IDS} if isinstance(value, list) else set()
        else:
            m = _MARKER_RE.search(r.stdout)
            out |= {v for v in (m.group(1).replace(",", " ").split() if m else []) if v in SURFACE_IDS}
    return frozenset(out)


def record(root: Path, frozen: frozenset[str]) -> bool:
    """Write the honoured frozen set to ``.researchteam`` (only when it changed); returns whether it wrote."""
    path = root / ".researchteam"
    if not path.exists() or recorded(root) == frozen:
        return False
    text = path.read_text(encoding="utf-8")
    line = f"{MARKER_KEY} = {', '.join(sorted(frozen))}" if frozen else ""
    if _MARKER_RE.search(text):
        text = _MARKER_RE.sub(line, text).replace("\n\n\n", "\n\n")
    elif line:
        text = text.rstrip("\n") + "\n" + line + "\n"
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    return True


# --- unfreeze, verified by the pinned agentteams' own gate ---------------------------------------------------------

_VERIFY = r"""
import json, sys
from pathlib import Path
team, action = Path(sys.argv[1]), sys.argv[2]
try:
    from agentteams.cli.security_gate import check_clearance, _latest_security_decision
    from agentteams.cli.effect_classifier import RELAXING, derive_effect_class, requires_operator_signature
except Exception as exc:  # too old to say: refuse
    print(json.dumps({"ok": False, "why": f"this agentteams can't evaluate an unfreeze ({exc.__class__.__name__})"})); sys.exit(0)
try:
    # Rule 15: the relaxing class must be DERIVED from the row's effect, never self-declared. Probe this
    # agentteams with a bare unfreeze row carrying no effect_* declarations: if it does not derive that as
    # relaxing on its own, it can't verify an unfreeze correctly (agentteams <= 1.0.0), so refuse.
    probe = {"timestamp": "", "requesting_agent": "security", "action_reviewed": action, "verdict": "PASS",
             "scope": action, "conditions": "", "conditions_verified": ""}
    if derive_effect_class(probe, kind="decision") != RELAXING:
        print(json.dumps({"ok": False, "why": "this agentteams does not derive an unfreeze as constraint-relaxing "
                          "by itself (it needs agentteams' frozen-surfaces support, 1.0.x)"})); sys.exit(0)
    ok, why = check_clearance(team, action=action)
    if not ok:
        print(json.dumps({"ok": False, "why": f"no clearing {action} row: {why}"})); sys.exit(0)
    # An unfreeze must be a signed DECISION row: the gate accepts a matching waiver before any row signature is
    # checked, so a waiver for this action is refused rather than read around.
    try:
        from agentteams.cli.security_gate import _latest_security_waiver
        if _latest_security_waiver(team, action=action):
            print(json.dumps({"ok": False, "why": f"a waiver exists for {action}; an unfreeze needs a signed decision row"})); sys.exit(0)
    except ImportError:
        print(json.dumps({"ok": False, "why": "this agentteams can't check for a waiver; refusing"})); sys.exit(0)
    row = _latest_security_decision(team, action=action) or {}
    if not row:
        print(json.dumps({"ok": False, "why": f"no {action} decision row"})); sys.exit(0)
    if not requires_operator_signature(row, kind="decision"):
        print(json.dumps({"ok": False, "why": f"{action} does not derive as constraint-relaxing (operator-signed); "
                          "an unfreeze row must name what it relaxes (effect_relaxes)"})); sys.exit(0)
    # The gate (check_clearance) verified the signature; here only the scheme column is read, never row text.
    if (row.get("sig_scheme") or "").strip().lower() != "ed25519" or not (row.get("signature") or "").strip():
        print(json.dumps({"ok": False, "why": f"{action} is not Ed25519-signed by the operator"})); sys.exit(0)
    print(json.dumps({"ok": True, "why": "clears; constraint-relaxing; Ed25519"}))
except Exception as exc:
    print(json.dumps({"ok": False, "why": f"gate error: {exc}"}))
"""


def verify_unfreeze(root: Path, surface: str, launcher: str | None) -> tuple[bool, str]:
    """Ask the pinned agentteams (under its own interpreter) whether ``unfreeze-<surface>`` is authorised."""
    from ._agentteams_provenance import launcher_interpreter

    if not launcher:
        return False, "agentteams is not available to verify the unfreeze"
    py = launcher_interpreter(launcher)
    if not py or not os.access(py, os.X_OK):
        return False, f"cannot find the interpreter of {launcher}"
    try:
        r = _run([py, "-I", "-c", _VERIFY, str(root / ".github" / "agents"), f"unfreeze-{surface}"],
                           capture_output=True, text=True, timeout=60, cwd="/")
        result = json.loads((r.stdout or "").strip().splitlines()[-1])
    except (OSError, subprocess.TimeoutExpired, ValueError, IndexError) as exc:
        return False, f"the unfreeze check could not run: {exc}"
    return bool(result.get("ok")), str(result.get("why", ""))
