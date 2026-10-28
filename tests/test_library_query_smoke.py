"""End-to-end smoke: build a tiny literature library, then query it with the real scripts."""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "scripts" / "build_literature_library.py"
QUERY = ROOT / "scripts" / "query_literature_library.py"
spec = importlib.util.spec_from_file_location("bll", BUILD)
bll = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bll)

BIB = """\
@article{fisher1933,
  title = {The Debt-Deflation Theory of Great Depressions},
  author = {Fisher, Irving},
  year = {1933},
  note = {Debt deflation spiral: falling prices raise real debt burdens during depressions.}
}
@book{cagan1956,
  title = {The Monetary Dynamics of Hyper-Inflation},
  author = {Cagan, Phillip},
  year = {1956},
  note = {Money demand during hyperinflation episodes; inflation expectations drive real balances.}
}
@article{coase1960,
  title = {The Problem of Social Cost},
  author = {Coase, Ronald},
  year = {1960},
  note = {Externalities, transaction costs and the assignment of property rights.}
}
"""


@pytest.fixture(scope="module")
def library(tmp_path_factory):
    root = tmp_path_factory.mktemp("rt")
    refs = root / "Projects" / "demo" / "references"
    refs.mkdir(parents=True)
    (refs / "bibliography.bib").write_text(BIB, encoding="utf-8")
    env = dict(os.environ, RT_ROOT=str(root))
    r = subprocess.run([sys.executable, str(BUILD), "demo"], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return root, env, refs / "library"


def _query(library, *argv):
    root, env, _ = library
    return subprocess.run([sys.executable, str(QUERY), "demo", *argv], env=env, capture_output=True, text=True)


def _candidates(stdout: str) -> list[str]:
    return [line.split("[", 1)[1].split("]", 1)[0] for line in stdout.splitlines() if line.startswith("  ") and "[" in line]


def test_a_clearly_relevant_record_ranks_first(library):
    r = _query(library, "debt deflation depressions")
    assert r.returncode == 0, r.stderr
    assert _candidates(r.stdout)[0] == "fisher1933"


def test_build_and_query_tokenize_alike(library):
    _, _, libdir = library
    vectors = {json.loads(l)["key"]: json.loads(l)["terms"]
               for l in (libdir / "term-vectors.jsonl").read_text().splitlines() if l.strip()}
    # The title's "Hyper-Inflation" was indexed with the same tokenizer the query uses.
    assert bll._tokenize("HYPER-inflation,") == ["hyper", "inflation"]
    assert {"hyper", "inflation"} <= set(vectors["cagan1956"])
    r = _query(library, "HYPER-inflation,")
    assert r.returncode == 0 and _candidates(r.stdout)[0] == "cagan1956"


@pytest.mark.parametrize("q", ["", "zzqx vvkw", "the and of"])  # empty, no overlap, stopwords only
def test_an_empty_or_unmatched_query_exits_cleanly_with_no_candidates(library, q):
    r = _query(library, q)
    assert r.returncode == 0, r.stderr
    assert _candidates(r.stdout) == [] and "no lexical overlap" in r.stdout
