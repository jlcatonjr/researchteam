"""Survey toolkit core: folded text (rule 1.10), canonical JSON and hashing (6.1), the path rule (1.6)."""
import ast
import hashlib
import os
import unicodedata

import pytest

from survey_support import SURVEY, survey_core as core

# A fixed sample: a decomposable capital, a soft hyphen, a hyphen at a line break, upper case with accents, a tab,
# an em space, and a combining diaeresis written as its own character.
SAMPLE = "  \u00c7a\u00adva-\n  t-il  \u00c9T\u00c9\tS\u00dbR\u2003? Ma\u0308rz  "


def test_fold_pins_a_fixed_sample():
    assert core.fold(SAMPLE) == "cavat-il ete sur ? marz"
    assert core.fold(SAMPLE, spaces=False) == "cavat-iletesur?marz"


def test_environment_reports_the_unicode_database():
    env = core.environment()
    assert env["unicodedata"] == unicodedata.unidata_version
    assert env["python"].count(".") == 2


def test_canonical_json_sorts_keys_has_no_white_space_and_one_line_feed():
    data = core.canonical_json({"b": 1, "a": ["x", {"d": None, "c": "\u00e9"}]})
    assert data == '{"a":["x",{"c":"\u00e9","d":null}],"b":1}\n'.encode("utf-8")
    assert data.endswith(b"}\n") and not data.endswith(b"\n\n")


@pytest.mark.parametrize("name,text", [
    ("a.md", True), ("a.json", True), ("a.jsonl", True), ("a.csv", True), ("a.tsv", True), ("a.txt", True),
    ("a.py", True), ("a.R", True), ("a.sh", True), ("a.yaml", True), ("a.yml", True),
    ("a.MD", False), ("a.r", False), ("a.pdf", False), ("a.md.bak", False), ("md", False),
])
def test_text_is_by_suffix_alone_case_sensitive(name, text):
    assert core.is_text_file(name) is text


def test_text_files_hash_with_crlf_made_lf_and_others_as_they_are(tmp_path):
    raw = b"one\r\ntwo\r\n"
    for name in ("x.md", "x.MD", "x.bin"):
        (tmp_path / name).write_bytes(raw)
    lf = hashlib.sha256(b"one\ntwo\n").hexdigest()
    assert core.file_sha256(tmp_path / "x.md", "x.md") == lf
    assert core.file_sha256(tmp_path / "x.MD", "x.MD") == hashlib.sha256(raw).hexdigest()
    assert core.file_sha256(tmp_path / "x.bin", "x.bin") == hashlib.sha256(raw).hexdigest()


# --------------------------------------------------------------------------- rule 1.6
@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    (root / "Projects" / "p" / "sub").mkdir(parents=True)
    (root / ".git").mkdir()
    (root / "Projects" / "p" / "sub" / "f.csv").write_text("x\n")
    return root


def _resolve(repo, declared):
    return core.resolve_path(declared, "Projects/p", repo, "where")


def test_paths_are_study_relative_or_repo_rooted(repo):
    a, _ = _resolve(repo, "sub/f.csv")
    b, _ = _resolve(repo, "repo:Projects/p/sub/f.csv")
    assert a.repo_rel == b.repo_rel == "Projects/p/sub/f.csv"  # the declared text, joined to the study folder
    assert a.real == b.real and a.identity == b.identity  # the same file, however each is written


def test_two_spellings_on_a_case_insensitive_file_system_are_one_file(repo):
    if not os.path.exists(repo / "Projects" / "p" / "SUB" / "F.csv"):
        pytest.skip("this file system is case-sensitive")
    a, _ = _resolve(repo, "sub/f.csv")
    b, _ = _resolve(repo, "SUB/F.csv")
    assert a.identity == b.identity and b.repo_rel == "Projects/p/SUB/F.csv"


def test_a_place_that_does_not_exist_is_identified_by_its_real_path(repo):
    a, _ = _resolve(repo, "sub/none.csv")
    assert a.identity == ("path", a.real)


@pytest.mark.parametrize("declared,rule", [
    ("/etc/passwd", "path-absolute"), ("repo:/etc/passwd", "path-absolute"), ("C:/x", "path-absolute"),
    ("../x", "path-dotdot"), ("sub/../../x", "path-dotdot"), ("repo:../x", "path-dotdot"),
    ("sub\\f.csv", "path-backslash"), ("", "path-empty"), ("repo:", "path-empty"),
    ("./sub/f.csv", "path-segment"), ("sub//f.csv", "path-segment"), ("sub/", "path-segment"),
    ("repo:./x", "path-segment"), ("sub/\x00f.csv", "path-nul"),
])
def test_path_rule_errors(repo, declared, rule):
    rp, findings = _resolve(repo, declared)
    assert rp is None and rule in {f.rule for f in findings}


def test_a_path_that_leaves_the_repository_through_a_link_is_an_error(repo, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    os.symlink(outside, repo / "Projects" / "p" / "away")
    rp, findings = _resolve(repo, "away/f.csv")
    assert rp is None and [f.rule for f in findings] == ["path-outside"]
    os.symlink(repo / "Projects" / "p" / "sub", repo / "Projects" / "p" / "inside")
    rp, findings = _resolve(repo, "inside/f.csv")  # a link that stays in the repository is allowed
    assert not findings and rp.real == os.path.realpath(repo / "Projects" / "p" / "sub" / "f.csv")


def test_strict_json_refuses_duplicate_keys_and_nan():
    assert core.load_json_strict(b'{"a":1,"a":2}', "w")[1][0].rule == "json-duplicate-key"
    assert core.load_json_strict(b'{"a":NaN}', "w")[1][0].rule == "json"
    assert core.load_json_strict(b"\xff", "w")[1][0].rule == "json"


def test_json_nested_too_deeply_is_a_finding_not_a_crash():
    value, findings = core.load_json_strict(b"[" * 200000 + b"]" * 200000, "w")
    assert value is None and findings[0].rule == "json" and "deep" in findings[0].message


def test_read_capped_refuses_a_link_without_following_it(tmp_path):
    (tmp_path / "f").write_bytes(b"data")
    os.symlink(tmp_path / "f", tmp_path / "link")
    with pytest.raises(OSError):
        core.read_capped(tmp_path / "link", 100)


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="os.mkfifo is not available here")
def test_read_capped_refuses_a_fifo_without_blocking(tmp_path):
    os.mkfifo(tmp_path / "fifo")  # with no writer, a blocking open would hang the test
    with pytest.raises(core.NotARegularFile):
        core.read_capped(tmp_path / "fifo", 100)


def test_read_capped_refuses_a_directory(tmp_path):
    with pytest.raises(OSError):
        core.read_capped(tmp_path, 100)


def test_read_capped_refuses_a_file_over_the_cap(tmp_path):
    (tmp_path / "f").write_bytes(b"12345")
    assert core.read_capped(tmp_path / "f", 5) == b"12345"
    assert core.read_capped(tmp_path / "f", 4) is None


def test_hashing_in_chunks_keeps_a_crlf_split_across_chunks(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "_CHUNK", 4)
    raw = b"abc\r\ndef\r\r\n\rghi\r"
    for name in ("x.md", "x.bin"):
        (tmp_path / name).write_bytes(raw)
    assert core.file_sha256(tmp_path / "x.md", "x.md") == hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    assert core.file_sha256(tmp_path / "x.bin", "x.bin") == hashlib.sha256(raw).hexdigest()


def test_the_soft_hyphen_is_written_as_an_escape():
    source = (SURVEY / "survey_core.py").read_text(encoding="utf-8")
    assert "\u00ad" not in source and core.SOFT_HYPHEN == "\u00ad"


def test_the_code_is_python_3_10_syntax_and_standard_library_only():
    """Rule 1.7, and the supported versions: nothing newer than 3.10's grammar, no import outside the stdlib."""
    import sys
    stdlib = set(getattr(sys, "stdlib_module_names", ())) or None
    own = {p.stem for p in SURVEY.glob("*.py")}
    for path in sorted(SURVEY.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), feature_version=(3, 10))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module.split(".")[0]]
            for name in names:
                assert name not in ("tomllib",), f"{path.name} imports {name}, which 3.10 lacks"
                if stdlib is not None:
                    assert name in stdlib or name in own, f"{path.name} imports {name}"
