"""`query_literature_library.py -k N` removes exactly the flag and its value; usage errors exit 2."""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("qll", ROOT / "scripts" / "query_literature_library.py")
qll = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qll)


@pytest.fixture
def run(tmp_path, monkeypatch):
    lib = tmp_path / "p" / "references" / "library"
    lib.mkdir(parents=True)
    (lib / "term-vectors.jsonl").write_text("")
    seen = {}

    def fake_query(libdir, q, k):
        seen.update(q=q, k=k, libdir=libdir)
        return [], {}

    monkeypatch.setattr(qll, "query", fake_query)
    monkeypatch.setattr(qll, "_resolve_project", lambda root, project: tmp_path / project)
    monkeypatch.setattr(qll, "_root", lambda: tmp_path)

    def go(*argv):
        monkeypatch.setattr(sys, "argv", ["q", *argv])
        qll.main()
        return seen
    return go


def test_a_query_word_equal_to_k_is_kept(run):
    seen = run("p", "phase", "5", "-k", "5")
    assert seen["q"] == "phase 5" and seen["k"] == 5


@pytest.mark.parametrize("argv", [("-k", "3", "p", "a", "b"), ("p", "-k", "3", "a", "b"), ("p", "a", "b", "-k", "3")])
def test_k_works_anywhere(run, argv):
    seen = run(*argv)
    assert seen["q"] == "a b" and seen["k"] == 3


def test_a_project_named_like_k_is_kept(run, tmp_path):
    (tmp_path / "3" / "references" / "library").mkdir(parents=True)
    (tmp_path / "3" / "references" / "library" / "term-vectors.jsonl").write_text("")
    seen = run("3", "terms", "-k", "3")
    assert seen["q"] == "terms" and seen["libdir"] == tmp_path / "3" / "references" / "library"


@pytest.mark.parametrize("argv", [("p", "a", "-k"), ("p", "a", "-k", "x"), ("p", "a", "-k", "0"), ("p",), ()])
def test_usage_errors_exit_2(run, argv, capsys):
    with pytest.raises(SystemExit) as exc:
        run(*argv)
    assert exc.value.code == 2 and "usage:" in capsys.readouterr().err
