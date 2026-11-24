"""The pinned agentteams term-index core: the copy, its manifest, the loader and import shim, the offline check,
doctor's report, the byte-exact sync and (opt-in) the comparison with the signed tag.

Design: references/plans/open-1119-p1-copy-integrity-design.md (section 10 wins). Layers:
- L1, always, offline: the copy matches the manifest; the manifest is well formed; the loader works with no
  agentteams, with a hostile agentteams on the path, and with agentteams modules already in sys.modules (left as
  they were); the check fails closed on a tampered byte, a missing file, a link and an unlisted code file.
  Tests that expect a failure run in a subprocess (section 10, point 5).
- L2, only with RT_NETWORK_TESTS=1: the manifest equals the signed agentteams tag it names.
CI runs this file on Python 3.10 and 3.13, which proves the copied core (agentteams declares >=3.11) loads on 3.10.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import json
import os
import shutil
import subprocess
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
CORE = SCRIPTS / "term-index-core"
TERM_SCRIPTS = ("term_index_engine.py", "build_term_index.py", "check_term_index.py", "query_term_index.py",
                "check_term_core.py")
PINNED = {"repository": "jlcatonjr/agentteams", "tag": "v1.3.0", "commit": "536306d2502e3db338846677f2d37489531ac8e7"}
REGISTER = {"schema": "researchteam-term-register", "terms": [
    {"id": "t", "label": "term register", "definition": "d", "discouraged": ["term registry"],
     "source": "project definition"}]}


def manifest() -> dict:
    return json.loads((CORE / "PINNED.json").read_text(encoding="utf-8"))


def repo_copy(tmp_path: Path, project: bool = True) -> Path:
    """A repository with the term-index scripts, the pinned core and (optionally) one built project."""
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    for name in TERM_SCRIPTS:
        shutil.copy(SCRIPTS / name, repo / "scripts")
    shutil.copytree(CORE, repo / "scripts" / "term-index-core")
    if project:
        proj = repo / "Projects" / "Demo"
        (proj / "terminology").mkdir(parents=True)
        (proj / "01-review.md").write_text("A term register and a term registry.\n")
        (proj / "terminology" / "terms.json").write_text(json.dumps(REGISTER))
        assert run(repo, "build_term_index.py", "build").returncode == 0
    return repo


def run(repo: Path, script: str, *args: str, env: dict | None = None, stdin: str | None = None,
        python: str = sys.executable) -> subprocess.CompletedProcess:
    full = {k: v for k, v in os.environ.items() if k not in ("RT_ROOT", "TERM_INDEX_ADVISORY", "PYTHONPATH")}
    full.update(env or {})
    return subprocess.run([python, "-B", str(repo / "scripts" / script), *args], capture_output=True, text=True,
                          env=full, input=stdin, timeout=120, cwd=repo)


def load_script(name: str, path: Path | None = None):
    """Import a script in-process as the term-index tests do, leaving sys.path as it was."""
    saved = list(sys.path)
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec = importlib.util.spec_from_file_location(f"_term_core_pin_{name}", path or SCRIPTS / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path[:] = saved


def snapshot(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


# --------------------------------------------------------------------------- the copy and its manifest
def test_the_copy_matches_its_manifest_which_names_the_signed_tag():
    r = subprocess.run([sys.executable, "-B", str(SCRIPTS / "check_term_core.py")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
    assert r.stdout.splitlines() == [
        "[term-core] OK scripts/term-index-core/_term_text.py",
        "[term-core] OK scripts/term-index-core/term_index.py",
        "[term-core] OK scripts/term-index-core/LICENSE",
        "[term-core] SUMMARY agentteams v1.3.0 (536306d2502e): 3 of 3 files match; 0 mismatched, 0 missing or refused, "
        "0 unlisted"]
    m = manifest()
    assert m["format"] == "researchteam-pinned-copy/1" and m["upstream"] == PINNED and m["entry"] == "term_index"
    assert [(f["upstream_path"], f["local_path"]) for f in m["files"] + m["data_files"]] == [
        ("agentteams/_term_text.py", "scripts/term-index-core/_term_text.py"),
        ("agentteams/term_index.py", "scripts/term-index-core/term_index.py"),
        ("LICENSE", "scripts/term-index-core/LICENSE")]
    sizes = {f["upstream_path"]: (ROOT / f["local_path"]).stat().st_size for f in m["files"]}
    assert sizes == {"agentteams/_term_text.py": 15226, "agentteams/term_index.py": 35475}
    assert (CORE / "LICENSE").read_text(encoding="utf-8").startswith("MIT License")


def test_the_pin_is_on_the_locks_agentteams_line():
    """Doctor warns on a different vX.Y line; at a release the commits must be equal (the network form checks it)."""
    from researchteam._release import read_lock_pin, release_line

    _, commit, tag = read_lock_pin(ROOT, "agentteams")
    assert tag is not None and release_line(tag) == release_line(manifest()["upstream"]["tag"])
    if commit != manifest()["upstream"]["commit"]:
        pytest.skip("toolchain.lock moved within the line; the core pin must follow it before the next release")


def test_every_file_in_the_core_directory_is_listed_managed_and_synced_as_bytes():
    from researchteam._manifest import BYTE_EXACT_PREFIXES, FRAMEWORK_MANAGED_FILES, SCHOLARLY_MANAGED_FILES

    m = manifest()
    # .gitattributes is researchteam's own file, not upstream's, so it is managed but not in PINNED.json (which lists
    # only files with an upstream counterpart); the check ignores it as a file that is not code.
    pinned = {f["local_path"] for f in m["files"] + m["data_files"]}
    listed = pinned | {"scripts/term-index-core/PINNED.json", "scripts/term-index-core/.gitattributes"}
    on_disk = {p.relative_to(ROOT).as_posix() for p in CORE.rglob("*")}
    assert on_disk == listed
    for rel in listed | {"scripts/check_term_core.py"}:
        assert rel in SCHOLARLY_MANAGED_FILES and rel not in FRAMEWORK_MANAGED_FILES, rel
    assert {rel for rel in SCHOLARLY_MANAGED_FILES if rel.startswith(BYTE_EXACT_PREFIXES)} == listed


def test_git_never_converts_the_copied_bytes():
    """The directory carries its own .gitattributes, so a derived repository that receives it gets the rule too."""
    assert "* -text -ident -filter" in (CORE / ".gitattributes").read_text().splitlines()
    if shutil.which("git") is None or not (ROOT / ".git").exists():
        pytest.skip("no git checkout")
    r = subprocess.run(["git", "-C", str(ROOT), "check-attr", "text", "ident", "filter", "--",
                        "scripts/term-index-core/term_index.py"], capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.count(": unset") == 3, r.stdout


def test_the_copied_core_is_python_3_10_syntax():
    """agentteams declares >=3.11; researchteam supports 3.10. CI's 3.10 job runs the core for real; this catches
    newer grammar on any interpreter."""
    for f in manifest()["files"]:
        ast.parse((ROOT / f["local_path"]).read_bytes(), filename=f["local_path"], feature_version=(3, 10))


# --------------------------------------------------------------------------- the loader and the shim
def test_the_loader_registers_a_private_package_and_shims_the_upstream_import():
    check = load_script("check_term_core")
    core = check.load()
    assert core is check.load()  # the verified copy loads once per process
    package = sys.modules["_researchteam_term_core"]
    assert package.__path__ == [] and core is sys.modules["_researchteam_term_core.term_index"]
    text = sys.modules["_researchteam_term_core._term_text"]
    assert core.Matcher is text.Matcher and core.mask is text.mask and core.form_key is text.form_key
    assert core.Matcher.__module__ == "_researchteam_term_core._term_text"
    assert "agentteams" not in sys.modules or not hasattr(sys.modules["agentteams"], "_researchteam_term_core")
    do_import = core.__builtins__["__import__"]
    assert do_import("agentteams._term_text", fromlist=("WORD",)) is text
    for refused in (("agentteams",), ("agentteams.cli", None, None, ("x",)), ("agentteams._term_text",),
                    ("pytest",), ("researchteam",)):
        with pytest.raises(ImportError):
            do_import(*refused)
    assert do_import("json") is sys.modules["json"]
    # A function's own builtins: a lazy import inside the core goes through the same restricted __import__.
    assert core.assess.__builtins__["__import__"] is do_import
    assert "def assess(" in inspect.getsource(core.assess)  # tracebacks show the checked source


LOADER_PROBE = r"""
import importlib.abc, json, sys, types
mode = sys.argv[1]
if mode == "blocked":
    class Block(importlib.abc.MetaPathFinder):
        def find_spec(self, name, path=None, target=None):
            if name == "agentteams" or name.startswith("agentteams."):
                raise ImportError("agentteams is blocked in this test")
    sys.meta_path.insert(0, Block())
before = {}
if mode == "preloaded":
    for name in ("agentteams", "agentteams._term_text"):
        sys.modules[name] = types.ModuleType(name)
    sys.modules["agentteams._term_text"].Matcher = "the installed one"
    before = {k: id(v) for k, v in sys.modules.items() if k.partition(".")[0] == "agentteams"}
sys.path.insert(0, "scripts")
import term_index_engine as engine
proj = engine.discover(engine.repo_root())[0]
a = engine.assess(proj)
after = {k: id(v) for k, v in sys.modules.items() if k.partition(".")[0] == "agentteams"}
print(json.dumps({"usable": a.usable, "docs": sorted(a.docs), "core": engine.core.__name__,
                  "matcher": engine.core.Matcher.__module__, "agentteams_modules_unchanged": before == after,
                  "agentteams_loaded": [k for k in sys.modules if k.partition(".")[0] == "agentteams"]}))
"""


@pytest.mark.parametrize("mode", ["blocked", "hostile", "preloaded"])
def test_the_core_never_reaches_an_installed_agentteams(tmp_path, mode):
    """No agentteams at all; an agentteams on the path whose modules raise on import; agentteams modules already
    in sys.modules (left exactly as they were). In each, the pinned core runs."""
    repo = repo_copy(tmp_path)
    env = {}
    if mode == "hostile":
        fake = tmp_path / "site" / "agentteams"
        fake.mkdir(parents=True)
        for name in ("__init__.py", "_term_text.py", "term_index.py"):
            (fake / name).write_text("raise RuntimeError('the installed agentteams must never be imported')\n")
        env["PYTHONPATH"] = str(fake.parent)
    r = subprocess.run([sys.executable, "-B", "-c", LOADER_PROBE, mode], capture_output=True, text=True, cwd=repo,
                       env={**{k: v for k, v in os.environ.items() if k not in ("RT_ROOT", "PYTHONPATH")}, **env},
                       timeout=120)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["usable"] and out["docs"] == ["01-review.md"]
    assert out["core"] == "_researchteam_term_core.term_index" and out["matcher"] == "_researchteam_term_core._term_text"
    assert out["agentteams_modules_unchanged"]
    assert out["agentteams_loaded"] == ([] if mode != "preloaded" else ["agentteams", "agentteams._term_text"])
    if mode == "hostile":  # the commands too, end to end
        assert run(repo, "check_term_index.py", env=env).returncode == 1  # the discouraged form: DISC


def test_no_bare_core_function_is_exported_and_reuse_is_keyword_only(tmp_path):
    """The core's neutral defaults change results, so every engine callable is the engine's own wrapper."""
    engine = load_script("term_index_engine")
    from_core = [name for name in dir(engine) if not name.startswith("_")
                 and isinstance(getattr(engine, name), (types.FunctionType, type))
                 and str(getattr(engine, name).__module__).startswith("_researchteam_term_core")]
    assert from_core == ["Assessment"]  # a plain dataclass the core returns; it takes no configuration
    wrappers = [n for n in dir(engine) if isinstance(getattr(engine, n), types.FunctionType) and not n.startswith("_")]
    assert all(getattr(engine, n).__module__ == engine.__name__ for n in wrappers)
    assert engine.Assessment is engine.core.Assessment and issubclass(engine.Matcher, engine.core.Matcher)
    proj = repo_copy(tmp_path) / "Projects" / "Demo"
    with pytest.raises(TypeError):
        engine.assess(proj, True)  # positional `reuse` would be the core's `config`
    assert engine.CONFIG.generator == engine.GENERATOR and engine.CONFIG.schemas == (engine.REGISTER_SCHEMA,)
    assert engine.CONFIG.skip_heading is engine.REFS_HEADING and engine.CONFIG.rebuild_hint == "term-build"


# --------------------------------------------------------------------------- the offline check fails closed
def _flip_byte(core: Path) -> None:
    data = bytearray((core / "term_index.py").read_bytes())
    data[100] ^= 0x01
    (core / "term_index.py").write_bytes(bytes(data))


def _link(core: Path) -> None:
    shutil.move(core / "term_index.py", core.parent / "term_index_real.py")
    (core / "term_index.py").symlink_to(core.parent / "term_index_real.py")


def _edit_manifest(**change):
    def apply(core: Path) -> None:
        m = json.loads((core / "PINNED.json").read_text())
        for key, value in change.items():
            if key == "file0":
                m["files"][0].update(value)
            elif value is None:
                del m[key]
            else:
                m[key] = value
        (core / "PINNED.json").write_text(json.dumps(m))
    return apply


FAILURES = {
    "tampered byte": (1, _flip_byte, "[term-core] MISMATCH scripts/term-index-core/term_index.py: sha256 "),
    "crlf conversion": (1, lambda c: (c / "_term_text.py").write_bytes((c / "_term_text.py").read_bytes().replace(b"\n", b"\r\n")),
                        "[term-core] MISMATCH scripts/term-index-core/_term_text.py"),
    "missing module": (1, lambda c: (c / "_term_text.py").unlink(), "[term-core] MISSING scripts/term-index-core/_term_text.py: missing"),
    "missing licence": (1, lambda c: (c / "LICENSE").unlink(), "[term-core] MISSING scripts/term-index-core/LICENSE"),
    "extra .py file": (1, lambda c: (c / "helper.py").write_text("x = 1\n"), "[term-core] UNLISTED scripts/term-index-core/helper.py"),
    "extra bytecode": (1, lambda c: ((c / "__pycache__").mkdir(), (c / "__pycache__" / "term_index.cpython-313.pyc").write_bytes(b"\0"))[1],
                       "[term-core] UNLISTED scripts/term-index-core/__pycache__/term_index.cpython-313.pyc"),
    "symbolic link": (1, _link, "[term-core] LINK scripts/term-index-core/term_index.py: a symbolic link (refused)"),
    "manifest not json": (2, lambda c: (c / "PINNED.json").write_text("{"), "not valid JSON"),
    "manifest missing": (2, lambda c: (c / "PINNED.json").unlink(), "PINNED.json: missing"),
    "manifest extra key": (2, _edit_manifest(note="x"), "needs exactly the keys"),
    "manifest bad hash": (2, _edit_manifest(file0={"sha256": "ABC"}), "sha256 must be 64 lower-case"),
    "manifest escapes": (2, _edit_manifest(file0={"local_path": "scripts/term-index-core/../evil.py"}), "local_path must be"),
    "manifest absolute": (2, _edit_manifest(file0={"local_path": "/etc/passwd"}), "local_path must be"),
    "manifest upstream": (2, _edit_manifest(upstream={"repository": "x", "tag": "main", "commit": "abc"}), "upstream must be"),
    "manifest entry": (2, _edit_manifest(entry="os"), "entry must name"),
    "manifest format": (2, _edit_manifest(format="other/1"), "format must be"),
    "directory missing": (2, lambda c: shutil.rmtree(c), "MISSING scripts/term-index-core/"),
    "directory link": (2, lambda c: (shutil.move(c, c.parent / "core-real"), c.symlink_to(c.parent / "core-real"))[1],
                       "LINK scripts/term-index-core/"),
}


@pytest.mark.parametrize("case", sorted(FAILURES))
def test_the_check_and_every_command_fail_closed(tmp_path, case):
    code, damage, expected = FAILURES[case]
    repo = repo_copy(tmp_path)
    if "link" in case and not hasattr(os, "symlink"):
        pytest.skip("needs symbolic links")
    damage(repo / "scripts" / "term-index-core")
    r = run(repo, "check_term_core.py")
    assert r.returncode == code and expected in r.stdout, r.stdout
    assert "upgrade researchteam" in r.stdout and "There is no override" in r.stdout
    before = snapshot(repo / "Projects")
    for args in (("check_term_index.py",), ("build_term_index.py", "build"), ("query_term_index.py", "Demo", "t")):
        c = run(repo, *args)
        assert c.returncode == 2 and expected in c.stderr and "Traceback" not in c.stderr, (args, c.stderr)
    hook = run(repo, "build_term_index.py", "hook", stdin=json.dumps({"tool_input": {"file_path": "Projects/Demo/01-review.md"}}))
    assert hook.returncode == 2 and expected in hook.stderr and "Traceback" not in hook.stderr
    advisory = run(repo, "check_term_index.py", env={"TERM_INDEX_ADVISORY": "1"})
    assert advisory.returncode == 2  # the advisory switch does not soften it
    assert snapshot(repo / "Projects") == before  # nothing written


def test_an_unlisted_file_that_is_not_code_is_allowed(tmp_path):
    repo = repo_copy(tmp_path, project=False)
    (repo / "scripts" / "term-index-core" / "README.txt").write_text("notes\n")
    assert run(repo, "check_term_core.py").returncode == 0


def test_an_engine_without_its_loader_says_to_upgrade_researchteam_first(tmp_path):
    """What an older researchteam leaves behind when it syncs a newer ref: the adapters, without the loader."""
    repo = repo_copy(tmp_path)
    (repo / "scripts" / "check_term_core.py").unlink()
    r = run(repo, "check_term_index.py")
    assert r.returncode == 2 and "Traceback" not in r.stderr
    assert "MISSING scripts/check_term_core.py" in r.stderr and "Upgrade researchteam first" in r.stderr


def test_the_check_takes_no_arguments():
    r = subprocess.run([sys.executable, "-B", str(SCRIPTS / "check_term_core.py"), "--fix"], capture_output=True, text=True)
    assert r.returncode == 2 and "usage" in r.stderr


# --------------------------------------------------------------------------- doctor
def _lines():
    out: list[tuple[str, str]] = []
    return out, (lambda m: out.append(("ok", m))), (lambda m: out.append(("warn", m))), (lambda m: out.append(("FAIL", m)))


def test_doctor_reports_the_pin_and_compares_it_with_the_lock(tmp_path):
    from researchteam import _doctor_cmd

    repo = repo_copy(tmp_path, project=False)
    out, ok, warn, fail = _lines()
    assert _doctor_cmd._check_term_core(repo, ok, warn, fail) is True
    assert out[0] == ("ok", "term-index core: agentteams v1.3.0 (536306d2502e): 3 of 3 files match; 0 mismatched, "
                            "0 missing or refused, 0 unlisted")
    assert out[1][0] == "ok" and "never an installed agentteams" in out[1][1]
    assert out[2][0] == "warn" and "names no agentteams.tag" in out[2][1]
    for lock_tag, expected in (("v1.3.4", None), ("v1.4.0", "move the core pin with the lock")):
        (repo / "toolchain.lock").write_text(f"agentteams=jlcatonjr/agentteams@{'a' * 40}\nagentteams.tag={lock_tag}\n")
        out, ok, warn, fail = _lines()
        _doctor_cmd._check_term_core(repo, ok, warn, fail)
        warns = [m for kind, m in out if kind == "warn"]
        assert (warns == []) if expected is None else (len(warns) == 1 and expected in warns[0]), out


def test_doctor_fails_on_a_tampered_core_and_reports_it_once(tmp_path, monkeypatch, capsys):
    from researchteam import _doctor_cmd, _update_cmd

    repo = repo_copy(tmp_path)
    _flip_byte(repo / "scripts" / "term-index-core")
    out, ok, warn, fail = _lines()
    assert _doctor_cmd._check_term_core(repo, ok, warn, fail) is False
    assert len(out) == 1 and out[0][0] == "FAIL" and "MISMATCH scripts/term-index-core/term_index.py" in out[0][1]
    (repo / ".researchteam").write_text("layer1 = off\n")
    monkeypatch.setattr(_update_cmd, "_resolve_agentteams", lambda: (None, "nowhere"))
    with pytest.raises(SystemExit) as stop:
        _doctor_cmd.run_doctor(repo)
    assert stop.value.code == 1
    captured = capsys.readouterr()
    assert "[FAIL] term-index core: the pinned copy does not verify" in captured.err
    assert "term index: gate" not in captured.out  # one fault, reported once


@pytest.mark.parametrize("missing", ["scripts/check_term_core.py", "scripts/term-index-core"])
def test_doctor_fails_when_the_gate_is_present_without_its_core(tmp_path, missing):
    from researchteam import _doctor_cmd

    repo = repo_copy(tmp_path, project=False)
    target = repo / missing
    shutil.rmtree(target) if target.is_dir() else target.unlink()
    out, ok, warn, fail = _lines()
    assert _doctor_cmd._check_term_core(repo, ok, warn, fail) is False
    assert len(out) == 1 and out[0][0] == "FAIL" and "missing" in out[0][1] and "Upgrade researchteam first" in out[0][1]


def test_doctor_is_silent_without_the_term_index_scripts(tmp_path):
    from researchteam import _doctor_cmd

    out, ok, warn, fail = _lines()
    assert _doctor_cmd._check_term_core(tmp_path, ok, warn, fail) is True and out == []


# --------------------------------------------------------------------------- byte-exact layer-2 sync
def _served_core(extra: dict | None = None) -> dict[str, bytes]:
    """A consistent upstream set: two files (one with CRLF and a byte that is not UTF-8) and a manifest naming them."""
    files = {"scripts/term-index-core/_term_text.py": b"x = 1\r\n# \xff\r\n", "scripts/term-index-core/LICENSE": b"MIT\n",
             "scripts/term-index-core/.gitattributes": b"* -text -ident -filter\n"}
    entry = lambda rel, up: {"upstream_path": up, "local_path": rel, "sha256": hashlib.sha256(files[rel]).hexdigest()}
    pinned = {"format": "researchteam-pinned-copy/1", "upstream": PINNED, "entry": "_term_text",
              "files": [entry("scripts/term-index-core/_term_text.py", "agentteams/_term_text.py")],
              "data_files": [entry("scripts/term-index-core/LICENSE", "LICENSE")]}
    return {**files, "scripts/term-index-core/PINNED.json": json.dumps(pinned).encode(), **(extra or {})}


def _byte_update(tmp_path, monkeypatch, served, *, yes=True, answers=None):
    from researchteam import _update_cmd

    monkeypatch.setattr(_update_cmd, "managed_files_for", lambda profile: sorted(served))
    monkeypatch.setattr(_update_cmd, "fetch_raw", lambda *a: pytest.fail("a byte-exact file must not be decoded"))
    monkeypatch.setattr(_update_cmd, "fetch_raw_bytes", lambda repo, ref, path: served[path])
    monkeypatch.setattr(_update_cmd, "_sync_notes", lambda *a, **k: None)
    asked = []
    monkeypatch.setattr("builtins.input", lambda prompt="": asked.append(prompt) or (answers or ["y"])[len(asked) - 1])
    _update_cmd.run_update(tmp_path, ref="main", yes=yes, dry_run=False, layer2_only=True, layer1_only=False)
    return asked


def test_update_syncs_the_core_as_exact_bytes_and_verifies_the_result(tmp_path, monkeypatch, capsys):
    served = _served_core()
    _byte_update(tmp_path, monkeypatch, served)
    assert {r: (tmp_path / r).read_bytes() for r in served} == served
    out = capsys.readouterr().out
    assert "4 updated" in out and "0 errors" in out
    _byte_update(tmp_path, monkeypatch, served)
    assert "0 updated" in capsys.readouterr().out  # identical bytes: nothing to do


def test_update_writes_nothing_from_a_set_that_does_not_verify(tmp_path, monkeypatch, capsys):
    served = _served_core()
    served["scripts/term-index-core/LICENSE"] = b"changed\n"  # no longer the manifest's bytes
    _byte_update(tmp_path, monkeypatch, served)
    assert not (tmp_path / "scripts").exists()
    assert "does not match the fetched manifest" in capsys.readouterr().err


def test_update_asks_once_for_the_whole_core_set(tmp_path, monkeypatch, capsys):
    served = _served_core()
    asked = _byte_update(tmp_path, monkeypatch, served, yes=False, answers=["n"])
    assert len(asked) == 1 and "Apply all 4?" in asked[0]
    assert not (tmp_path / "scripts" / "term-index-core").exists()  # declined: no file written
    asked = _byte_update(tmp_path, monkeypatch, served, yes=False, answers=["y"])
    assert len(asked) == 1 and all((tmp_path / r).read_bytes() == b for r, b in served.items())


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="needs symbolic links")
@pytest.mark.parametrize("link", ["directory", "parent", "file"])
def test_update_never_writes_the_core_through_a_link(tmp_path, monkeypatch, capsys, link):
    outside = tmp_path / "outside"
    outside.mkdir()
    repo = tmp_path / "repo"
    if link == "directory":   # scripts/term-index-core itself is a link to a directory outside the repository
        (repo / "scripts").mkdir(parents=True)
        (repo / "scripts" / "term-index-core").symlink_to(outside, target_is_directory=True)
    elif link == "parent":    # scripts/ is a link
        repo.mkdir()
        (repo / "scripts").symlink_to(outside, target_is_directory=True)
    else:                     # one file is a link
        (repo / "scripts" / "term-index-core").mkdir(parents=True)
        (repo / "scripts" / "term-index-core" / "LICENSE").symlink_to(outside / "victim")
    _byte_update(repo, monkeypatch, _served_core())
    assert list(outside.rglob("*")) == []  # nothing written outside the repository
    assert "a symbolic link on the path, or outside the repository; nothing" in capsys.readouterr().out


# --------------------------------------------------------------------------- the network comparison (L2)
def test_blob_mismatches_names_absent_and_different_files():
    from researchteam._term_core_upstream import blob_mismatches

    m = {"upstream": PINNED, "files": [{"upstream_path": "a.py", "sha256": hashlib.sha256(b"a").hexdigest()},
                                       {"upstream_path": "b.py", "sha256": hashlib.sha256(b"b").hexdigest()}],
         "data_files": [{"upstream_path": "LICENSE", "sha256": hashlib.sha256(b"l").hexdigest()}]}
    blobs = {"a.py": b"a", "b.py": b"B"}
    lines = blob_mismatches(m, blobs.get)
    assert len(lines) == 2 and "MISMATCH b.py" in lines[0] and "ABSENT LICENSE at 536306d2502e" in lines[1]
    assert blob_mismatches(m, {"a.py": b"a", "b.py": b"b", "LICENSE": b"l"}.get) == []


@pytest.mark.skipif(os.environ.get("RT_NETWORK_TESTS") != "1", reason="network: set RT_NETWORK_TESTS=1")
def test_the_manifest_equals_the_signed_agentteams_tag():
    from researchteam._term_core_upstream import compare

    code, lines = compare(ROOT)
    assert code == 0, "\n".join(lines)


FAILING_LOAD = r"""
import json, sys
sys.path.insert(0, "scripts")
import check_term_core
try:
    check_term_core.load()
except check_term_core.CoreCheckFailed as exc:
    print(json.dumps({"failed": exc.code, "lines": exc.lines,
                      "left": sorted(k for k in sys.modules if k.startswith("_researchteam_term_core"))}))
"""


@pytest.mark.parametrize("tail", [b"\nraise RuntimeError('fails while running')\n", b"\nMatcher = object\n"],
                         ids=["raises", "wrong-matcher"])
def test_a_failed_load_leaves_nothing_in_sys_modules(tmp_path, tail):
    """A copy whose manifest was edited with it verifies, then fails to load: no partial package is left behind."""
    repo = repo_copy(tmp_path, project=False)
    core = repo / "scripts" / "term-index-core"
    data = (core / "term_index.py").read_bytes() + tail
    (core / "term_index.py").write_bytes(data)
    m = json.loads((core / "PINNED.json").read_text())
    m["files"][1]["sha256"] = hashlib.sha256(data).hexdigest()
    (core / "PINNED.json").write_text(json.dumps(m))
    r = subprocess.run([sys.executable, "-B", "-c", FAILING_LOAD], capture_output=True, text=True, cwd=repo, timeout=60)
    out = json.loads(r.stdout)
    assert out["failed"] == 2 and out["left"] == [], out


def test_the_network_form_checks_the_copy_without_the_repositorys_check_script(tmp_path):
    """A check script changed to pass everything cannot vouch for a tampered copy: the package hashes it itself."""
    from researchteam._term_core_upstream import compare, local_mismatches

    repo = repo_copy(tmp_path, project=False)
    (repo / "scripts" / "check_term_core.py").write_text("def verify():\n    raise SystemExit('never called')\n")
    manifest, problems = local_mismatches(repo)
    assert manifest["upstream"] == PINNED and problems == []
    _flip_byte(repo / "scripts" / "term-index-core")
    (repo / "scripts" / "term-index-core" / "extra.py").write_text("")
    code, lines = compare(repo)  # stops before any network step
    assert code == 1 and any("MISMATCH scripts/term-index-core/term_index.py" in ln for ln in lines)
    assert any("UNLISTED scripts/term-index-core/extra.py" in ln for ln in lines)
    (repo / "scripts" / "term-index-core" / "PINNED.json").write_text("{}")
    assert compare(repo)[0] == 2
