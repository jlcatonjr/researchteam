"""#186: the derived scaffold ships with its schedule off, and `researchteam workflow-sync` keeps a repo's `on:` block."""

import os
from pathlib import Path

import pytest

from researchteam._workflow_sync import (WORKFLOW, WorkflowSyncError, load_scaffold, merge, on_block, plan,
                                         run_workflow_sync)

ROOT = Path(__file__).resolve().parent.parent

ON_SCHEDULED = '''on:
  workflow_dispatch:
  schedule:
    - cron: "0 6 * * 1"
'''
ON_DISPATCH_ONLY = '''on:
  workflow_dispatch:
'''


def _old_workflow(on_text: str) -> str:
    return ("name: old autosync\n\n" + on_text + "\n# old comment for permissions\npermissions:\n  contents: write\n\n"
            "jobs:\n  autosync:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo old\n")


def _repo(tmp_path, text=None):
    if text is not None:
        (tmp_path / ".github/workflows").mkdir(parents=True)
        (tmp_path / WORKFLOW).write_text(text, encoding="utf-8")
    return tmp_path


def _yaml(text):
    yaml = pytest.importorskip("yaml")
    doc = yaml.safe_load(text)
    return doc.get("on", doc.get(True))  # PyYAML 1.1 reads a bare `on` key as True


# --- the scaffold default ------------------------------------------------------------------------

def test_scaffold_ships_with_the_schedule_off():
    on = _yaml(load_scaffold())
    assert "schedule" not in on and "workflow_dispatch" in on
    assert '# schedule:\n  #   - cron: "0 6 * * 1"' in load_scaffold()  # one uncomment away


def test_upstream_workflow_keeps_its_schedule():
    on = _yaml((ROOT / ".github/workflows/agentteams-sync.yml").read_text())
    assert on["schedule"] == [{"cron": "0 6 * * 1"}]


def test_packaged_scaffold_is_the_repo_file():
    assert load_scaffold() == (ROOT / "researchteam/scaffold/agentteams-sync-derived.yml").read_text()


# --- on_block / merge ----------------------------------------------------------------------------

def test_on_block_excludes_the_next_keys_leading_comment():
    text = _old_workflow(ON_SCHEDULED)
    lines = text.splitlines(keepends=True)
    s, e = on_block(text)
    assert "".join(lines[s:e]) == ON_SCHEDULED


@pytest.mark.parametrize("on_text", [ON_SCHEDULED, ON_DISPATCH_ONLY,
                                     'on:\n  workflow_dispatch:\n  # schedule:\n  #   - cron: "0 6 * * 1"\n'])
def test_merge_keeps_the_existing_on_block_and_takes_everything_else(on_text):
    out = merge(load_scaffold(), _old_workflow(on_text))
    assert on_text in out
    scaffold = load_scaffold()
    s0, s1 = on_block(scaffold)
    lines = scaffold.splitlines(keepends=True)
    assert out.startswith("".join(lines[:s0]))
    assert out.endswith("".join(lines[s1:]))
    assert "echo old" not in out and "evergreen_pr" in out


def test_a_scheduled_repo_stays_scheduled_and_an_unscheduled_one_stays_off():
    assert _yaml(merge(load_scaffold(), _old_workflow(ON_SCHEDULED)))["schedule"] == [{"cron": "0 6 * * 1"}]
    assert "schedule" not in _yaml(merge(load_scaffold(), _old_workflow(ON_DISPATCH_ONLY)))


def test_merge_is_idempotent():
    once = merge(load_scaffold(), _old_workflow(ON_SCHEDULED))
    assert merge(load_scaffold(), once) == once


@pytest.mark.parametrize("bad", ["name: x\non: [push]\njobs: {}\n", "name: x\njobs: {}\n",
                                 "on:\n  push:\non:\n  pull_request:\n"])
def test_no_single_block_on_key_is_refused(bad):
    with pytest.raises(WorkflowSyncError):
        merge(load_scaffold(), bad)


def test_quoted_on_key_is_recognised():
    text = _old_workflow(ON_SCHEDULED).replace("on:\n", '"on":\n', 1)
    assert '"on":\n  workflow_dispatch:' in merge(load_scaffold(), text)


# --- run_workflow_sync ---------------------------------------------------------------------------

def test_absent_workflow_gets_the_scaffold_as_shipped(tmp_path):
    root = _repo(tmp_path)
    assert run_workflow_sync(root, yes=True) == 0
    assert (root / WORKFLOW).read_text() == load_scaffold()


def test_yes_writes_and_keeps_the_schedule(tmp_path):
    root = _repo(tmp_path, _old_workflow(ON_SCHEDULED))
    assert run_workflow_sync(root, yes=True) == 0
    written = (root / WORKFLOW).read_text()
    assert ON_SCHEDULED in written and "evergreen_pr" in written
    assert run_workflow_sync(root, yes=True) == 0  # second run: nothing to do
    assert (root / WORKFLOW).read_text() == written


def test_dry_run_writes_nothing(tmp_path, capsys):
    old = _old_workflow(ON_DISPATCH_ONLY)
    root = _repo(tmp_path, old)
    assert run_workflow_sync(root, dry_run=True) == 0
    assert (root / WORKFLOW).read_text() == old
    assert "+++ b/.github/workflows/agentteams-sync.yml" in capsys.readouterr().out


def test_declining_the_prompt_writes_nothing(tmp_path, monkeypatch):
    old = _old_workflow(ON_SCHEDULED)
    root = _repo(tmp_path, old)
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")
    assert run_workflow_sync(root) == 1
    assert (root / WORKFLOW).read_text() == old


def test_symlinked_workflow_is_refused(tmp_path):
    target = tmp_path / "elsewhere.yml"
    target.write_text(_old_workflow(ON_SCHEDULED))
    (tmp_path / ".github/workflows").mkdir(parents=True)
    os.symlink(target, tmp_path / WORKFLOW)
    assert run_workflow_sync(tmp_path, yes=True) == 1
    assert target.read_text() == _old_workflow(ON_SCHEDULED)


def test_symlinked_parent_is_refused(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    (tmp_path / ".github").mkdir()
    os.symlink(real, tmp_path / ".github/workflows")
    with pytest.raises(WorkflowSyncError):
        plan(tmp_path)
    assert run_workflow_sync(tmp_path, yes=True) == 1
    assert not any(real.iterdir())


def test_unparseable_on_block_is_refused_and_untouched(tmp_path):
    old = "name: x\non: [push, workflow_dispatch]\njobs: {}\n"
    root = _repo(tmp_path, old)
    assert run_workflow_sync(root, yes=True) == 1
    assert (root / WORKFLOW).read_text() == old
