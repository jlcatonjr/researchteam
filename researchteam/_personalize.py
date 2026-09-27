"""Render project-specific ``README.md`` and ``CLAUDE.md`` from ``brief.json``.

These two files are project-facing identity, not framework infrastructure: a derived instance must
describe ITS project, not the researchteam framework. They are therefore generated from the bundled
scaffold templates (``scaffold/README.template.md`` / ``scaffold/CLAUDE.template.md``) at ``init``
and re-rendered on demand by ``researchteam personalize`` — never wholesale-synced from upstream.

Two safety invariants:

* **Never personalize the upstream repository.** The ``.researchteam`` marker declares
  ``is_upstream = true`` there; personalize refuses so the framework's own README/CLAUDE are never
  overwritten with a rendered project scaffold.
* **Never silently clobber a hand-edited file.** Each generated file (and, for the fenced
  ``CLAUDE.md``, its project-owned header region) carries a trailing ``researchteam:generated``
  marker holding a SHA-256 of the generated body. On re-render, a file whose body still matches its
  marker is refreshed in place; a file that diverged (or was hand-authored without a marker) is left
  untouched unless ``force`` is set.
"""

import hashlib
import importlib.resources
import json
import re
import sys
from pathlib import Path

from ._manifest import FENCE_CORE_BEGIN, FENCE_CORE_END, INIT_RENDER_TEMPLATES

GEN_MARKER_PREFIX = "<!-- researchteam:generated sha256="
_SHA_RE = re.compile(r"sha256=([0-9a-f]{64})")


# --------------------------------------------------------------------------- marker helpers
def read_marker(root: Path) -> dict[str, str]:
    """Parse the ``.researchteam`` marker into a flat ``key -> value`` dict (values stripped)."""
    marker = root / ".researchteam"
    out: dict[str, str] = {}
    if not marker.exists():
        return out
    for line in marker.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if "=" in s and not s.startswith("["):
            key, _, value = s.partition("=")
            out[key.strip()] = value.strip()
    return out


def is_upstream(root: Path) -> bool:
    """True when the marker declares ``is_upstream = true`` (literal)."""
    return read_marker(root).get("is_upstream", "").lower() == "true"


# --------------------------------------------------------------------------- rendering
def _render(template: str, brief: dict) -> str:
    deliverables = brief.get("deliverables") or []
    if isinstance(deliverables, list) and deliverables:
        deliv_md = "\n".join(f"- {d}" for d in deliverables)
    else:
        deliv_md = "- _(define `deliverables` in brief.json)_"
    subs = {
        "{{PROJECT_NAME}}": str(brief.get("project_name", "")).strip() or "Untitled Project",
        "{{PROJECT_GOAL}}": str(brief.get("project_goal", "")).strip()
        or "_(describe this project's goal in brief.json)_",
        "{{OUTPUT_FORMAT}}": str(brief.get("output_format", "")).strip() or "Markdown",
        "{{PRIMARY_OUTPUT_DIR}}": str(brief.get("primary_output_dir", "")).strip() or "reports/",
        "{{DELIVERABLES}}": deliv_md,
    }
    for token, value in subs.items():
        template = template.replace(token, value)
    return template


def _marker_line(body: str) -> str:
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return (
        f"{GEN_MARKER_PREFIX}{digest} — regenerate with `researchteam personalize`; "
        f"edits to generated regions are overwritten -->\n"
    )


def _wrap(body: str) -> str:
    """Append the generation marker as a trailing line to ``body`` (which ends with a newline)."""
    if not body.endswith("\n"):
        body += "\n"
    return body + _marker_line(body)


def _generation_status(region: str) -> bool | None:
    """Return True if ``region`` is an untouched generated region, False if it diverged, None if it
    carries no generation marker (hand-authored)."""
    lines = region.splitlines(keepends=True)
    marker = next((ln for ln in lines if GEN_MARKER_PREFIX in ln), None)
    if marker is None:
        return None
    match = _SHA_RE.search(marker)
    if not match:
        return None
    body = "".join(ln for ln in lines if GEN_MARKER_PREFIX not in ln)
    return hashlib.sha256(body.encode("utf-8")).hexdigest() == match.group(1)


def _split_fence(text: str) -> tuple[str, str, str] | None:
    """Local copy of the fence splitter (avoids importing the update module)."""
    lines = text.splitlines(keepends=True)
    begin = end = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if begin is None and FENCE_CORE_BEGIN in s:
            begin = i
        elif begin is not None and FENCE_CORE_END in s:
            end = i
            break
    if begin is None or end is None:
        return None
    return "".join(lines[:begin]), "".join(lines[begin : end + 1]), "".join(lines[end + 1 :])


def _load_template(name: str) -> str:
    return (importlib.resources.files("researchteam") / "scaffold" / name).read_text(
        encoding="utf-8"
    )


# --------------------------------------------------------------------------- public API
def run_personalize(root: Path, force: bool = False, quiet: bool = False) -> list[str]:
    """Render README.md and CLAUDE.md into ``root`` from brief.json. Returns the paths written."""
    if is_upstream(root):
        sys.exit(
            "[researchteam] Refusing to personalize the UPSTREAM repository "
            "(.researchteam has is_upstream = true).\n"
            "  personalize generates project-specific docs for a DERIVED instance; the upstream "
            "framework repo keeps its own README.md / CLAUDE.md."
        )

    brief_path = root / "brief.json"
    if not brief_path.exists():
        sys.exit("[researchteam] brief.json not found; cannot personalize.")
    try:
        brief = json.loads(brief_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"[researchteam] Could not read brief.json: {exc}")

    written: list[str] = []
    for dest_rel, template_name in INIT_RENDER_TEMPLATES.items():
        rendered = _render(_load_template(template_name), brief)
        dest = root / dest_rel
        result = _write_generated(dest, dest_rel, rendered, force=force, quiet=quiet)
        if result:
            written.append(dest_rel)
    return written


def _write_generated(
    dest: Path, dest_rel: str, rendered: str, *, force: bool, quiet: bool
) -> bool:
    """Write one generated file, respecting the divergence guard. Returns True if written."""
    fence_split = _split_fence(rendered)
    existing = dest.read_text(encoding="utf-8") if dest.exists() else None

    if fence_split is not None:
        # Fenced file (CLAUDE.md): personalize owns ONLY the project header (pre-fence region).
        r_pre, r_managed, r_post = fence_split
        if existing is not None:
            e_split = _split_fence(existing)
            if e_split is not None:
                e_pre, e_managed, e_post = e_split
                status = _generation_status(e_pre)
                if status is False or status is None:
                    if not force:
                        _skip(dest_rel, status, quiet, header_only=True)
                        return False
                # Keep the existing managed block + post (owned by `researchteam update`);
                # regenerate only the project header.
                content = _wrap(r_pre) + e_managed + e_post
            else:
                # Existing file lost its fence; treat as hand-authored unless forced.
                if not force:
                    _skip(dest_rel, None, quiet, header_only=False)
                    return False
                content = _wrap(r_pre) + r_managed + r_post
        else:
            content = _wrap(r_pre) + r_managed + r_post
    else:
        # Unfenced file (README.md): personalize owns the whole file.
        if existing is not None:
            status = _generation_status(existing)
            if status is False or status is None:
                if not force:
                    _skip(dest_rel, status, quiet, header_only=False)
                    return False
        content = _wrap(rendered)

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    if not quiet:
        print(f"[researchteam] Personalized {dest_rel} from brief.json")
    return True


def _skip(dest_rel: str, status: bool | None, quiet: bool, *, header_only: bool) -> None:
    if quiet:
        return
    region = "project header" if header_only else "file"
    reason = (
        "was hand-authored (no generation marker)"
        if status is None
        else "has been edited since it was generated"
    )
    print(
        f"[researchteam] Skipped {dest_rel}: its {region} {reason}. "
        f"Re-run with --force to regenerate from brief.json and overwrite those edits.",
        file=sys.stderr,
    )
