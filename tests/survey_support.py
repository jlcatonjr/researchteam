"""Shared helpers for the survey toolkit's tests (tests/test_survey_*.py).

Every repository a test needs is built here in a temporary directory with ``git init``: the invented example study
(tests/fixtures/survey/example) is copied under ``Projects/tidebell/`` and its ledger folder is built with an
invented, non-functional public key. No helper reads this repository's own team folders.
"""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SURVEY = ROOT / "scripts" / "survey"
FIXTURES = ROOT / "tests" / "fixtures" / "survey"
EXAMPLE = FIXTURES / "example"
PROJECT = "tidebell"
STUDY_REL = f"Projects/{PROJECT}"

_saved = sys.dont_write_bytecode
sys.dont_write_bytecode = True  # importing the survey modules leaves no __pycache__ in scripts/survey
if str(SURVEY) not in sys.path:
    sys.path.insert(0, str(SURVEY))
import survey_core  # noqa: E402,F401
import survey_gates  # noqa: E402,F401
import survey_ledger  # noqa: E402,F401
import survey_manifest  # noqa: E402,F401
import survey_schema  # noqa: E402,F401
import survey_spec  # noqa: E402,F401
import survey_status  # noqa: E402,F401
import survey_validate  # noqa: E402,F401
sys.dont_write_bytecode = _saved

#: An invented PEM-shaped block. It is not a key of anyone's and does not decode to a usable key.
FAKE_PEM = ("-----BEGIN PUBLIC KEY-----\n"
            "MCowBQYDK2VwAyEAaW52ZW50ZWQtdGVzdC1ibG9jay1ub3QtYS1rZXk=\n"
            "-----END PUBLIC KEY-----\n")
LOG_HEADER = ("date,action_reviewed,verdict,scope,conditions,conditions_verified,evidence,author,derives_from,"
              "effect_class,effect_grants,effect_targets,effect_relaxes,effect_destructive,effect_cross_repo,"
              "effect_bulk,text_digest,sig_scheme,key_id,prev_digest,signature\n")


def git_init(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)


def build_ledger(folder: Path, *, approvers: str = "operator\n", keys=None, privilege=None, log=LOG_HEADER) -> None:
    refs = folder / "references"
    (refs / "authorized-verify-keys").mkdir(parents=True, exist_ok=True)
    (refs / "agent-privilege.json").write_text(json.dumps(privilege if privilege is not None else {}) + "\n")
    (refs / "security-decisions.log.csv").write_text(log)
    (refs / "security-approvers.txt").write_text(approvers)
    for key_id, pem in (keys if keys is not None else {"op-test": FAKE_PEM}).items():
        (refs / "authorized-verify-keys" / f"{key_id}.pub.pem").write_text(pem)


def make_repo(tmp_path: Path, mutate=None, *, ledger: bool = True) -> Path:
    """A git repository holding the invented study at Projects/tidebell, its ledger at Projects/tidebell/ledger."""
    root = tmp_path / "repo"
    git_init(root)
    shutil.copytree(EXAMPLE, root / STUDY_REL)
    if ledger:
        build_ledger(root / STUDY_REL / "ledger")
    if mutate is not None:
        edit_spec(root, mutate)
    return root


def spec_path(root: Path) -> Path:
    return root / STUDY_REL / "study.json"


def load_spec(root: Path) -> dict:
    return json.loads(spec_path(root).read_text(encoding="utf-8"))


def edit_spec(root: Path, mutate) -> None:
    spec = load_spec(root)
    mutate(spec)  # edits in place; its return value is ignored
    spec_path(root).write_text(json.dumps(spec, indent=2) + "\n")


def run(module, *args) -> tuple:
    """Run a command's ``main`` in-process; return (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = module.main(list(args))
    return code, out.getvalue(), err.getvalue()


def rules(findings) -> set:
    return {f.rule for f in findings}


def tree(root: Path) -> dict:
    """Every file under *root* (outside .git) with its bytes: to prove a run wrote nothing."""
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*"))
            if p.is_file() and ".git" not in p.relative_to(root).parts}
