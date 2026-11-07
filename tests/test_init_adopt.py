"""`init --adopt` (#59): scaffold into a non-empty directory without overwriting any existing file."""
import io
import json
import subprocess
import tarfile

import pytest

from researchteam import _init_cmd
from researchteam._personalize import _split_fence, run_personalize

GITIGNORE = (b"# >>> researchteam:managed - synced\ntmp/\n.venv/\n# <<< researchteam:managed\n")


def _tarball(members: dict[str, bytes], exe: tuple[str, ...] = ()) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, data in members.items():
            info = tarfile.TarInfo(f"researchteam-main/{name}")
            info.size = len(data)
            info.mode = 0o755 if name in exe else 0o644
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


ARCHIVE = _tarball({
    ".gitignore": GITIGNORE,
    "docs/a.md": b"framework doc a\n",
    "docs/claude-interface-bridge.md": b"framework bridge doc\n",
    "scripts/claude_researchteam_bridge.sh": b"#!/bin/sh\necho hi\n",
}, exe=("scripts/claude_researchteam_bridge.sh",))


@pytest.fixture
def adopt(tmp_path, monkeypatch):
    monkeypatch.setattr(_init_cmd, "fetch_tarball", lambda *a: ARCHIVE)
    proj = tmp_path / "proj"
    proj.mkdir()

    def run(**kw):
        monkeypatch.chdir(proj)
        _init_cmd.run_init(None, "main", None, adopt=True, **kw)
        return proj
    return proj, run


def _git(proj, *args):
    return subprocess.run(["git", *args], cwd=proj, capture_output=True, text=True)


def test_acceptance_existing_docs_and_readme_stay_byte_identical(adopt):
    """The issue's acceptance test: existing docs/ and README.md unchanged, scaffold added around them."""
    proj, run = adopt
    (proj / "docs").mkdir()
    (proj / "docs/mine.md").write_bytes(b"my notes\n")
    (proj / "docs/a.md").write_bytes(b"MY a.md, not the framework's\n")
    (proj / "README.md").write_bytes(b"# My project\n\nHand-written.\n")
    run()
    assert (proj / "docs/mine.md").read_bytes() == b"my notes\n"
    assert (proj / "docs/a.md").read_bytes() == b"MY a.md, not the framework's\n"
    assert (proj / "README.md").read_bytes() == b"# My project\n\nHand-written.\n"
    assert (proj / "docs/claude-interface-bridge.md").read_bytes() == b"framework bridge doc\n"
    assert (proj / ".researchteam").read_text().count("is_upstream = false") == 1
    assert (proj / ".github/workflows/agentteams-sync.yml").is_file()
    assert json.loads((proj / "brief.json").read_text())["project_name"] == "<YOUR PROJECT NAME>"
    assert (proj / "scripts/claude_researchteam_bridge.sh").stat().st_mode & 0o111


def test_an_empty_directory_adopts_like_a_fresh_init(adopt):
    proj, run = adopt
    run()
    assert _split_fence((proj / "CLAUDE.md").read_text()) is not None
    assert (proj / "README.md").is_file() and (proj / ".gitignore").read_bytes() == GITIGNORE


def test_unfenced_claude_md_and_gitignore_get_the_block_appended_below_unchanged_content(adopt):
    proj, run = adopt
    mine_claude, mine_ignore = "# My Claude rules\n\nBe terse.\n", "*.log\nvar/\n"
    (proj / "CLAUDE.md").write_text(mine_claude)
    (proj / ".gitignore").write_text(mine_ignore)
    run()
    claude, ignore = (proj / "CLAUDE.md").read_text(), (proj / ".gitignore").read_text()
    assert claude.startswith(mine_claude) and ignore.startswith(mine_ignore)
    pre, block, _post = _split_fence(claude)
    assert pre.startswith(mine_claude) and "researchteam:managed" in block
    assert _split_fence(ignore)[1] == GITIGNORE.decode()
    # A later personalize (as `update` runs it) leaves the hand-written header alone.
    run_personalize(proj, force=False, quiet=True)
    assert (proj / "CLAUDE.md").read_text() == claude


def test_already_fenced_files_are_kept_unchanged(adopt):
    proj, run = adopt
    ignore = "mine/\n" + GITIGNORE.decode() + "below/\n"
    (proj / ".gitignore").write_text(ignore)
    run()
    assert (proj / ".gitignore").read_text() == ignore


def test_an_existing_brief_is_kept_and_vulnscan_level_is_ignored(adopt, capsys):
    proj, run = adopt
    brief = '{"project_name": "Tutor", "layer2_profile": "generic"}\n'
    (proj / "brief.json").write_text(brief)
    run(vulnscan_level="off")
    assert (proj / "brief.json").read_text() == brief
    assert "--vulnscan-level ignored" in capsys.readouterr().out


def test_no_repository_gets_git_init_but_no_commit(adopt):
    proj, run = adopt
    run()
    assert (proj / ".git").is_dir()
    assert _git(proj, "rev-parse", "--verify", "HEAD").returncode != 0  # no commit
    assert _git(proj, "diff", "--cached", "--name-only").stdout == ""   # nothing staged


def test_an_existing_repository_is_never_staged_or_committed(adopt):
    proj, run = adopt
    _git(proj, "init", "-q")
    (proj / "work.txt").write_text("uncommitted user work\n")
    _git(proj, "add", "work.txt")
    _git(proj, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")
    (proj / "work.txt").write_text("more uncommitted work\n")
    head = _git(proj, "rev-parse", "HEAD").stdout
    run()
    assert _git(proj, "rev-parse", "HEAD").stdout == head
    assert _git(proj, "diff", "--cached", "--name-only").stdout == ""
    assert (proj / "work.txt").read_text() == "more uncommitted work\n"


def test_kept_files_on_managed_paths_are_reported_as_at_risk(adopt, capsys):
    proj, run = adopt
    (proj / "docs").mkdir()
    (proj / "docs/claude-interface-bridge.md").write_text("mine\n")
    run()
    out = capsys.readouterr().out
    assert (proj / "docs/claude-interface-bridge.md").read_text() == "mine\n"
    warning = out.split("WARNING:", 1)[1]
    assert "docs/claude-interface-bridge.md" in warning.split("kept 1 other", 1)[0]


def test_a_symlink_under_the_scaffold_is_never_written_through(adopt, tmp_path, capsys):
    proj, run = adopt
    outside = tmp_path / "outside"
    outside.mkdir()
    (proj / "docs").symlink_to(outside)                  # a symlinked directory
    (proj / "scripts").mkdir()
    (proj / "scripts/claude_researchteam_bridge.sh").symlink_to(outside / "dangling")  # a dangling link
    run()
    assert list(outside.iterdir()) == []
    out = capsys.readouterr().out
    assert "CONFLICT docs/a.md" in out and "CONFLICT scripts/claude_researchteam_bridge.sh" in out


def test_an_existing_project_is_refused(adopt, capsys):
    proj, run = adopt
    (proj / ".researchteam").write_text("[researchteam]\n")
    with pytest.raises(SystemExit):
        run()
    assert "already a researchteam project" in capsys.readouterr().err


def test_plain_init_still_refuses_a_non_empty_directory_and_names_adopt(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "x.txt").write_text("x")
    with pytest.raises(SystemExit):
        _init_cmd.run_init(None, "main", None)
    assert "--adopt" in capsys.readouterr().err


def test_the_cli_passes_adopt(monkeypatch):
    from researchteam import cli
    seen = {}
    monkeypatch.setattr(_init_cmd, "run_init", lambda *a, **kw: seen.update(kw))
    monkeypatch.setattr("sys.argv", ["researchteam", "init", "--adopt"])
    cli.main()
    assert seen["adopt"] is True


# --- review findings (code-hygiene audit, 2026-11-06) ------------------------------------------------------------

def _tree(proj):
    return sorted(str(p.relative_to(proj)) for p in proj.rglob("*") if ".git" not in p.parts)


@pytest.mark.parametrize("rel", ["CLAUDE.md", "README.md", "brief.json", ".researchteam", ".gitignore"])
def test_a_symlinked_key_file_is_refused_before_anything_is_written(adopt, tmp_path, capsys, rel):
    proj, run = adopt
    real = tmp_path / "real.md"
    real.write_text("linked\n")
    (proj / rel).symlink_to(tmp_path / "dangling" if rel in ("README.md", ".researchteam") else real)
    before = _tree(proj)
    with pytest.raises(SystemExit):
        run()
    assert f"{rel} is a symlink" in capsys.readouterr().err
    assert _tree(proj) == before and real.read_text() == "linked\n" and not (tmp_path / "dangling").exists()


@pytest.mark.parametrize("setup, says", [
    (lambda p: (p / "brief.json").write_text("{not json"), "cannot be read as JSON"),
    (lambda p: (p / "brief.json").write_text("[1, 2]"), "not a JSON object"),
    (lambda p: (p / "CLAUDE.md").write_bytes(b"\xff\xfe bad"), "not UTF-8"),
    (lambda p: (p / "CLAUDE.md").mkdir(), "not a regular file"),
])
def test_unreadable_inputs_are_refused_before_anything_is_written(adopt, capsys, setup, says):
    proj, run = adopt
    setup(proj)
    before = _tree(proj)
    with pytest.raises(SystemExit):
        run()
    err = capsys.readouterr().err
    assert says in err and "Nothing was written" in err and _tree(proj) == before


def test_the_marker_is_written_last_so_a_failed_run_can_be_retried(adopt, monkeypatch, capsys):
    proj, run = adopt
    real_run = subprocess.run

    def failing_git(cmd, *a, **kw):
        if cmd[:2] == ["git", "init"]:
            raise subprocess.CalledProcessError(1, cmd)
        return real_run(cmd, *a, **kw)
    monkeypatch.setattr("researchteam._adopt.subprocess.run", failing_git)
    with pytest.raises(SystemExit):
        run()
    assert not (proj / ".researchteam").exists() and "safe to retry" in capsys.readouterr().err
    monkeypatch.setattr("researchteam._adopt.subprocess.run", real_run)
    run()
    assert (proj / ".researchteam").is_file()


def test_a_generated_readme_with_a_matching_marker_is_not_rewritten(adopt, tmp_path, monkeypatch):
    """Files copied from another researchteam project carry valid generation markers; adopt still keeps them."""
    proj, run = adopt
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.chdir(other)
    _init_cmd.run_init(None, "main", None, adopt=True)
    readme = (other / "README.md").read_text().replace("<YOUR PROJECT NAME>", "Other Project")
    (proj / "README.md").write_text(readme)
    (proj / "brief.json").write_text('{"project_name": "Mine"}\n')
    run()
    assert (proj / "README.md").read_text() == readme


def test_a_subdirectory_of_a_repository_gets_no_nested_git_init(adopt, tmp_path, capsys):
    proj, run = adopt
    _git(tmp_path, "init", "-q")
    run()
    assert not (proj / ".git").exists() and "no nested `git init`" in capsys.readouterr().out


def test_a_symlinked_managed_directory_is_reported_at_risk(adopt, tmp_path, capsys):
    proj, run = adopt
    (tmp_path / "elsewhere").mkdir()
    (proj / "docs").symlink_to(tmp_path / "elsewhere")
    run()
    warning = capsys.readouterr().out.split("WARNING:", 1)[1]
    assert "docs/claude-interface-bridge.md" in warning


def test_an_already_fenced_claude_md_is_listed_once(adopt, capsys):
    proj, run = adopt
    run()  # fresh: renders a fenced CLAUDE.md
    (proj / ".researchteam").unlink()
    from researchteam._adopt import AdoptReport, populate_adopt
    report = AdoptReport()
    populate_adopt(proj, ARCHIVE, _init_cmd._validate_archive(ARCHIVE)[0], [], "main", None, None, report)
    assert report.kept.count("CLAUDE.md") == 1 and "CLAUDE.md" not in report.appended


# --- re-review findings -------------------------------------------------------------------------------------------

def test_an_empty_object_brief_is_still_kept(adopt):
    proj, run = adopt
    (proj / "brief.json").write_text("{}\n")
    run()
    assert (proj / "brief.json").read_text() == "{}\n"


def test_remote_is_never_added_to_an_enclosing_repository(adopt, tmp_path, monkeypatch, capsys):
    proj, _run = adopt
    _git(tmp_path, "init", "-q")
    monkeypatch.chdir(proj)
    _init_cmd.run_init(None, "main", "https://example.invalid/x.git", adopt=True)
    assert _git(tmp_path, "remote").stdout == "" and "--remote ignored" in capsys.readouterr().out


def test_a_failed_marker_write_is_an_error_not_done(adopt, monkeypatch, capsys):
    proj, run = adopt
    from researchteam import _adopt
    real = _adopt.adopt_write

    def no_marker(target, rel, content, report, mode=0):
        if rel == ".researchteam":
            report.conflicts.append(rel)
            return
        real(target, rel, content, report, mode)
    monkeypatch.setattr(_adopt, "adopt_write", no_marker)
    with pytest.raises(SystemExit):
        run()
    assert "could not create the .researchteam marker" in capsys.readouterr().err
