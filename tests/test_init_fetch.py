"""`init` fetches a branch, tag or commit, checks the archive before writing, and never leaves a stray directory."""
import io
import tarfile
import urllib.error

import pytest

from researchteam import _fetch, _init_cmd
from researchteam._drift import is_safe_ref

SHA = "0c72a185a4aba138fc9ba5054a4c42642dfa9fd1"


def _tarball(members: dict[str, bytes | None], links: tuple[str, ...] = ()) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            if data is None:
                info.type = tarfile.DIRTYPE
                tf.addfile(info)
            else:
                info.size = len(data)
                tf.addfile(info, io.BytesIO(data))
        for name in links:
            info = tarfile.TarInfo(name)
            info.type, info.linkname = tarfile.SYMTYPE, "elsewhere"
            tf.addfile(info)
    return buf.getvalue()


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _opener(responses: dict[str, object], seen: list[str]):
    def urlopen(url, timeout=None):
        seen.append(url)
        result = responses.get(url, 404)
        if isinstance(result, int):
            raise urllib.error.HTTPError(url, result, "x", {}, None)
        if isinstance(result, Exception):
            raise result
        return _Resp(result)
    return urlopen


ARCHIVE = "https://github.com/o/r/archive"


def test_a_commit_falls_through_to_the_commit_archive(monkeypatch):
    seen: list[str] = []
    monkeypatch.setattr(_fetch.urllib.request, "urlopen", _opener({f"{ARCHIVE}/0c72a18.tar.gz": b"tgz"}, seen))
    assert _fetch.fetch_tarball("o/r", "0c72a18") == b"tgz"
    assert seen == [f"{ARCHIVE}/refs/heads/0c72a18.tar.gz", f"{ARCHIVE}/refs/tags/0c72a18.tar.gz",
                    f"{ARCHIVE}/0c72a18.tar.gz"]


def test_a_branch_or_tag_is_unchanged_and_never_tries_the_commit_url(monkeypatch):
    seen: list[str] = []
    monkeypatch.setattr(_fetch.urllib.request, "urlopen", _opener({f"{ARCHIVE}/refs/tags/v1.0.2.tar.gz": b"t"}, seen))
    assert _fetch.fetch_tarball("o/r", "v1.0.2") == b"t"
    with pytest.raises(RuntimeError, match="No branch or tag 'nope'"):
        _fetch.fetch_tarball("o/r", "nope")
    assert f"{ARCHIVE}/nope.tar.gz" not in seen


def test_network_and_server_errors_stop_at_once_as_runtime_errors(monkeypatch):
    seen: list[str] = []
    monkeypatch.setattr(_fetch.urllib.request, "urlopen",
                        _opener({f"{ARCHIVE}/refs/heads/main.tar.gz": OSError("offline")}, seen))
    with pytest.raises(RuntimeError, match="Network error"):
        _fetch.fetch_tarball("o/r", "main")
    assert len(seen) == 1
    monkeypatch.setattr(_fetch.urllib.request, "urlopen", _opener({f"{ARCHIVE}/refs/heads/main.tar.gz": 500}, []))
    with pytest.raises(RuntimeError, match="HTTP 500"):
        _fetch.fetch_tarball("o/r", "main")


@pytest.mark.parametrize("ref", ["main", "v1.0.2", "release/1.0", "0c72a18", SHA])
def test_safe_refs(ref):
    assert is_safe_ref(ref)


@pytest.mark.parametrize("ref", ["a/../b", "..", "-x", "a b", "", "x" * 101, None])
def test_unsafe_refs(ref):
    assert not is_safe_ref(ref)


def test_an_unsafe_ref_is_refused_before_any_fetch(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(_init_cmd, "fetch_tarball", lambda *a: pytest.fail("fetched"))
    with pytest.raises(SystemExit):
        _init_cmd.run_init("proj", "a/../b", None)
    assert not (tmp_path / "proj").exists()


def test_a_failed_fetch_creates_no_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    def fail(*_a):
        raise RuntimeError("offline")
    monkeypatch.setattr(_init_cmd, "fetch_tarball", fail)
    with pytest.raises(SystemExit):
        _init_cmd.run_init("proj", "main", None)
    assert not (tmp_path / "proj").exists()


@pytest.mark.parametrize("bad", ["top/../../escape.txt", "/etc/passwd", "../escape.txt"])
def test_an_unsafe_member_refuses_the_whole_archive_and_writes_nothing(tmp_path, monkeypatch, bad):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(_init_cmd, "fetch_tarball", lambda *a: _tarball({"top/ok.txt": b"ok", bad: b"x"}))
    with pytest.raises(SystemExit):
        _init_cmd.run_init("proj", "main", None)
    assert not (tmp_path / "proj").exists() and not (tmp_path / "escape.txt").exists()


def test_validation_lists_links_and_skips_init_excluded_paths():
    members, links, top = _init_cmd._validate_archive(_tarball(
        {"rt-main/": None, "rt-main/docs/a.md": b"a", "rt-main/Projects/p.md": b"p"}, links=("rt-main/l",)))
    assert top == "rt-main" and members == {"rt-main/docs/a.md"} and links == ["l"]


def test_extract_writes_only_validated_members(tmp_path):
    tgz = _tarball({"rt-main/docs/a.md": b"a", "rt-main/brief.json": b"{}"})
    members, _links, _top = _init_cmd._validate_archive(tgz)
    _init_cmd._extract(tgz, tmp_path, members)
    assert (tmp_path / "docs/a.md").read_bytes() == b"a" and not (tmp_path / "brief.json").exists()


def test_a_short_commit_is_recorded_in_full(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(_init_cmd, "fetch_tarball", lambda *a: _tarball({f"researchteam-{SHA}/docs/a.md": b"a"}))
    recorded = {}
    def populate(target, tarball, members, links, ref, remote):
        recorded["ref"] = ref
    monkeypatch.setattr(_init_cmd, "_populate", populate)
    _init_cmd.run_init("proj", "0c72a18", None)
    assert recorded["ref"] == SHA


def test_a_failure_after_creation_names_the_partial_project(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(_init_cmd, "fetch_tarball", lambda *a: _tarball({"rt-main/docs/a.md": b"a"}))
    def populate(*_a):
        raise FileNotFoundError("git")
    monkeypatch.setattr(_init_cmd, "_populate", populate)
    with pytest.raises(SystemExit):
        _init_cmd.run_init("proj", "main", None)
    err = capsys.readouterr().err
    assert "incomplete" in err and str(tmp_path / "proj") in err and (tmp_path / "proj").is_dir()
