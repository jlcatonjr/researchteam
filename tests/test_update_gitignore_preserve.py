"""Tests for the `.gitignore` fenced-preserve merge strategy in `researchteam update`.

Covers the acceptance matrix in docs/gitignore-preservation-handoff.md §7. Exercises the pure
reconcile helpers directly — no network, no filesystem, no agentteams.
"""

from researchteam._manifest import FENCE_BEGIN, FENCE_END, MERGE_STRATEGIES
from researchteam._update_cmd import _fence_body, _reconcile_fenced, _split_fence


def _fenced(body: str, *, pre: str = "", post: str = "") -> str:
    """Build a fenced file: optional pre-region, the managed body, optional derived post-region."""
    return f"{pre}{FENCE_BEGIN}\n{body}{FENCE_END}\n{post}"


UPSTREAM = _fenced("tmp/\n.venv/\n**/references/corpus/text/\n")


# --- helpers -----------------------------------------------------------------------------------

def test_split_fence_roundtrip():
    pre, managed, post = _split_fence(_fenced("a/\nb/\n", post="derived/\n"))
    assert pre == ""
    assert managed == f"{FENCE_BEGIN}\na/\nb/\n{FENCE_END}\n"
    assert post == "derived/\n"


def test_split_fence_absent_returns_none():
    assert _split_fence("tmp/\n.venv/\n") is None


def test_split_fence_tolerates_marker_trailing_prose():
    # Upstream markers are self-documenting (spec §5.2), so matching must be prefix-based.
    text = (
        f"{FENCE_BEGIN} — do not edit inside this block; replaced on update\n"
        "tmp/\n"
        f"{FENCE_END}\n"
        "# derived-owned below\n"
        "derived/\n"
    )
    split = _split_fence(text)
    assert split is not None
    _pre, managed, post = split
    assert "tmp/\n" in managed
    assert post == "# derived-owned below\nderived/\n"


def test_fence_body_strips_markers():
    _, managed, _ = _split_fence(UPSTREAM)
    assert _fence_body(managed) == "tmp/\n.venv/\n**/references/corpus/text/\n"


# --- acceptance criterion 1: derived lines survive --yes ---------------------------------------

def test_derived_lines_survive_under_yes():
    local = _fenced("tmp/\n.venv/\n", post="Projects/.HiddenManuscript/\nworkSummaries/\n")
    # upstream adds a pattern inside the fence:
    remote = _fenced("tmp/\n.venv/\nnew-upstream-pattern/\n", post="")
    write, _diff, warn = _reconcile_fenced(".gitignore", local, remote, yes=True)
    assert warn == ""
    assert write is not None
    # derived post-region preserved byte-for-byte
    assert "Projects/.HiddenManuscript/\nworkSummaries/\n" in write
    # criterion 2: upstream addition landed
    assert "new-upstream-pattern/" in write


# --- acceptance criterion 3: upstream removals inside the fence apply ---------------------------

def test_upstream_removal_inside_fence_applies():
    local = _fenced("tmp/\n.venv/\nstale/\n", post="derived/\n")
    remote = _fenced("tmp/\n.venv/\n", post="")
    write, _diff, _warn = _reconcile_fenced(".gitignore", local, remote, yes=True)
    assert "stale/" not in write
    assert "derived/\n" in write  # derived region untouched by an upstream removal


# --- acceptance criterion 4: no spurious deletions in preview ----------------------------------

def test_preview_diff_excludes_derived_lines():
    local = _fenced("tmp/\n.venv/\n", post="Projects/.HiddenManuscript/\n")
    remote = _fenced("tmp/\n.venv/\nadded/\n", post="")
    _write, diff, _warn = _reconcile_fenced(".gitignore", local, remote, yes=False)
    joined = "".join(diff)
    # the derived line must NEVER appear as a deletion in the shown diff
    assert "Projects/.HiddenManuscript/" not in joined
    assert "+added/" in joined  # the genuine upstream addition is shown


# --- acceptance criterion 5: pre-fence migration is non-destructive ----------------------------

def test_unfenced_divergent_local_kept_under_yes():
    # A derived repo whose .gitignore predates the fence and carries extra lines.
    local = "tmp/\n.venv/\nProjects/.HiddenManuscript/\n"
    write, _diff, warn = _reconcile_fenced(".gitignore", local, UPSTREAM, yes=True)
    assert write is None  # nothing written — derived lines are NOT wiped
    assert warn  # operator is told why


def test_unfenced_divergent_local_offered_overwrite_interactively():
    local = "tmp/\n.venv/\nProjects/.HiddenManuscript/\n"
    write, diff, warn = _reconcile_fenced(".gitignore", local, UPSTREAM, yes=False)
    assert write == UPSTREAM  # interactive path may replace, but only after showing the diff...
    assert "-Projects/.HiddenManuscript/" in "".join(diff)  # ...with the loss made visible
    assert warn


def test_unfenced_local_equal_to_upstream_body_is_wrapped():
    # First-time wrap with no derived additions: adopting the fenced upstream loses nothing.
    local = "tmp/\n.venv/\n**/references/corpus/text/\n"
    write, _diff, warn = _reconcile_fenced(".gitignore", local, UPSTREAM, yes=True)
    assert write == UPSTREAM
    assert warn == ""


# --- acceptance criterion 6: strategy is opt-in (defaults to overwrite) -------------------------

def test_only_gitignore_opts_into_preserve():
    assert MERGE_STRATEGIES.get(".gitignore") == "fenced-preserve"
    assert MERGE_STRATEGIES.get("CLAUDE.md", "overwrite") == "overwrite"
    assert MERGE_STRATEGIES.get("scripts/claude_researchteam_bridge.sh", "overwrite") == "overwrite"


# --- acceptance criterion 7: idempotent ---------------------------------------------------------

def test_identical_managed_block_is_noop():
    local = _fenced("tmp/\n.venv/\n", post="derived/\n")
    remote = _fenced("tmp/\n.venv/\n")  # same managed block, no post
    write, _diff, warn = _reconcile_fenced(".gitignore", local, remote, yes=True)
    assert write is None
    assert warn == ""


# --- degrade-safe: upstream not yet fenced ------------------------------------------------------

def test_unfenced_upstream_never_overwrites():
    local = _fenced("tmp/\n", post="derived/\n")
    remote_unfenced = "tmp/\n.venv/\n"
    write, _diff, warn = _reconcile_fenced(".gitignore", local, remote_unfenced, yes=True)
    assert write is None  # refuse to wholesale-overwrite under a preserve strategy
    assert "no researchteam:managed fence" in warn
