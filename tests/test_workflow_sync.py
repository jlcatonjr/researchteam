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
                                 "on:\n  push:\non:\n  pull_request:\n",
                                 "on:\n  push:\n---\npermissions: write-all\n",
                                 "on:\n  push:\n- stray\njobs: {}\n",
                                 "on:\n  push:\n? permissions\n: write-all\njobs: {}\n"])
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


def test_stale_temp_file_is_cleared(tmp_path):
    root = _repo(tmp_path, _old_workflow(ON_SCHEDULED))
    stale = root / ".github/workflows/.agentteams-sync.yml.workflow-sync.tmp"
    stale.write_text("left over")
    assert run_workflow_sync(root, yes=True) == 0
    assert not stale.exists() and "evergreen_pr" in (root / WORKFLOW).read_text()


def test_symlinked_temp_path_is_refused(tmp_path):
    root = _repo(tmp_path, _old_workflow(ON_SCHEDULED))
    victim = tmp_path / "victim"
    victim.write_text("keep")
    os.symlink(victim, root / ".github/workflows/.agentteams-sync.yml.workflow-sync.tmp")
    assert run_workflow_sync(root, yes=True) == 1
    assert victim.read_text() == "keep" and "echo old" in (root / WORKFLOW).read_text()


def test_existing_mode_is_kept(tmp_path):
    root = _repo(tmp_path, _old_workflow(ON_SCHEDULED))
    os.chmod(root / WORKFLOW, 0o600)
    assert run_workflow_sync(root, yes=True) == 0
    assert (root / WORKFLOW).stat().st_mode & 0o777 == 0o600


def test_directory_at_the_workflow_path_is_refused(tmp_path):
    (tmp_path / WORKFLOW).mkdir(parents=True)
    assert run_workflow_sync(tmp_path, yes=True) == 1


def test_non_utf8_workflow_is_refused(tmp_path):
    root = _repo(tmp_path, "")
    (root / WORKFLOW).write_bytes(b"on:\n  push:\n\xff\xfe\n")
    assert run_workflow_sync(root, yes=True) == 1


def test_crlf_workflow_keeps_its_on_block(tmp_path):
    root = _repo(tmp_path, "")
    (root / WORKFLOW).write_bytes(_old_workflow(ON_SCHEDULED).replace("\n", "\r\n").encode())
    assert run_workflow_sync(root, yes=True) == 0
    assert 'cron: "0 6 * * 1"' in (root / WORKFLOW).read_text()


def test_eof_at_the_prompt_writes_nothing_and_says_why(tmp_path, monkeypatch, capsys):
    old = _old_workflow(ON_SCHEDULED)
    root = _repo(tmp_path, old)
    def eof(_prompt):
        raise EOFError
    monkeypatch.setattr("builtins.input", eof)
    assert run_workflow_sync(root) == 1
    assert (root / WORKFLOW).read_text() == old
    err = capsys.readouterr().err
    assert "no answer on standard input" in err and "--yes" in err


def test_cli_wires_the_subcommand(tmp_path, monkeypatch):
    import sys
    from researchteam import cli
    root = _repo(tmp_path, _old_workflow(ON_DISPATCH_ONLY))
    (root / ".researchteam").write_text("")
    monkeypatch.chdir(root)
    monkeypatch.setattr(sys, "argv", ["researchteam", "workflow-sync", "--yes"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 0
    assert "schedule" not in _yaml((root / WORKFLOW).read_text())


# --- the opt-in validate workflow ----------------------------------------------------------------
VALIDATE = ".github/workflows/researchteam-validate.yml"


def test_validate_scaffold_is_read_only_and_runs_the_bridge_validator():
    text = load_scaffold("researchteam-validate-derived.yml")
    doc = pytest.importorskip("yaml").safe_load(text)
    assert doc["permissions"] == {"contents": "read"}
    triggers = doc.get("on", doc.get(True))
    assert set(triggers) == {"pull_request", "push"} and "pull_request_target" not in text
    job = doc["jobs"]["validate"]
    assert "permissions" not in job and job["timeout-minutes"] <= 15
    assert [s.get("run") for s in job["steps"] if "run" in s] == ["bash scripts/claude_researchteam_bridge.sh validate"]
    assert job["steps"][0]["with"] == {"persist-credentials": False}
    code = "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith("#"))
    assert "secrets." not in code and "GITHUB_TOKEN" not in code and "write" not in code
    assert (ROOT / "researchteam/scaffold/researchteam-validate-derived.yml").read_text() == text


def test_validate_workflow_is_opt_in():
    from researchteam._manifest import INIT_SCAFFOLD_REPLACEMENTS, MANAGED_FILES
    from researchteam._workflow_sync import WORKFLOWS

    assert list(WORKFLOWS) == ["autosync", "validate"] and WORKFLOWS["autosync"].path == WORKFLOW
    assert WORKFLOWS["validate"].path == VALIDATE
    # init and update leave it alone
    assert VALIDATE not in INIT_SCAFFOLD_REPLACEMENTS and VALIDATE not in MANAGED_FILES


def test_validate_workflow_is_written_only_when_asked_and_keeps_its_on_block(tmp_path, capsys):
    assert run_workflow_sync(tmp_path, yes=True) == 0  # the default writes the autosync workflow only
    assert (tmp_path / WORKFLOW).is_file() and not (tmp_path / VALIDATE).exists()
    assert run_workflow_sync(tmp_path, dry_run=True, which="validate") == 0
    assert not (tmp_path / VALIDATE).exists() and "read-only" in capsys.readouterr().out
    assert run_workflow_sync(tmp_path, yes=True, which="validate") == 0
    written = (tmp_path / VALIDATE).read_text()
    assert written == load_scaffold("researchteam-validate-derived.yml")
    assert run_workflow_sync(tmp_path, yes=True, which="validate") == 0  # idempotent
    narrowed = written.replace("on:\n  pull_request:\n  push:\n    branches: [main]\n", "on:\n  pull_request:\n")
    assert narrowed != written
    (tmp_path / VALIDATE).write_text(narrowed.replace("timeout-minutes: 10", "timeout-minutes: 99"))
    assert run_workflow_sync(tmp_path, yes=True, which="validate") == 0
    merged = (tmp_path / VALIDATE).read_text()
    assert merged == narrowed  # the repository's own triggers kept; everything else from the scaffold
    assert (tmp_path / WORKFLOW).read_text() == load_scaffold()  # the other workflow is untouched


def test_validate_workflow_refuses_links_too(tmp_path):
    (tmp_path / ".github/workflows").mkdir(parents=True)
    target = tmp_path / "elsewhere.yml"
    target.write_text("untouched")
    os.symlink(target, tmp_path / VALIDATE)
    with pytest.raises(WorkflowSyncError, match="researchteam-validate.yml is a symlink"):
        plan(tmp_path, which="validate")
    assert run_workflow_sync(tmp_path, yes=True, which="validate") == 1 and target.read_text() == "untouched"


def test_cli_wires_the_workflow_choice(tmp_path, monkeypatch):
    import sys
    from researchteam import cli
    (tmp_path / ".researchteam").write_text("")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["researchteam", "workflow-sync", "--workflow", "validate", "--yes"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 0 and (tmp_path / VALIDATE).is_file() and not (tmp_path / WORKFLOW).exists()


def test_an_unknown_workflow_name_is_a_clear_error(tmp_path):
    with pytest.raises(ValueError, match="unknown workflow 'deploy'; one of: autosync, validate"):
        plan(tmp_path, which="deploy")
    with pytest.raises(ValueError):
        run_workflow_sync(tmp_path, yes=True, which="deploy")
    assert not (tmp_path / ".github").exists()


UNSAFE_ON_BLOCKS = [
    "on: [push]\n",                                           # not a block-style `on:` at all
    "on:\n  pull_request_target:\n",
    "on:\n  workflow_run:\n    workflows: [x]\n",
    "on:\n  - pull_request\n  - pull_request_target\n",
    "on:\n  - pull_request_target  # for forks\n",
    'on:\n  "pull_request_target":\n',
    "on:\n  [push, pull_request_target]\n",                   # flow collections under a block key
    "on:\n  {pull_request_target: {}}\n",
    "on:\n  [push,\n   workflow_run]\n",
    'on:\n  {push: {branches: ["a#b"]}, pull_request_target: {}}\n',   # a `#` inside a word is not a comment
    "on:\n  push: {branches: [a#b]}\n  pull_request_target:\n",
]


@pytest.mark.parametrize("on_text", UNSAFE_ON_BLOCKS)
def test_validate_workflow_refuses_an_on_block_it_cannot_keep_safely(tmp_path, on_text):
    (tmp_path / ".github/workflows").mkdir(parents=True)
    existing = "name: mine\n\n" + on_text + "\npermissions:\n  contents: write\n\njobs: {}\n"
    (tmp_path / VALIDATE).write_text(existing)
    with pytest.raises(WorkflowSyncError):
        plan(tmp_path, which="validate")
    assert run_workflow_sync(tmp_path, yes=True, which="validate") == 1
    assert (tmp_path / VALIDATE).read_text() == existing  # untouched


def test_privileged_trigger_names_in_comments_or_job_text_are_not_refused(tmp_path):
    (tmp_path / ".github/workflows").mkdir(parents=True)
    existing = ("name: mine\n\non:\n  # never pull_request_target here\n  pull_request:  # not workflow_run\n\n"
                "jobs:\n  x:\n    steps:\n      - run: echo workflow_run\n")
    (tmp_path / VALIDATE).write_text(existing)
    current, proposed = plan(tmp_path, which="validate")
    assert "# never pull_request_target here" in proposed and "echo workflow_run" not in proposed


def test_autosync_keeps_whatever_triggers_the_repository_chose(tmp_path):
    """The privileged-trigger refusal is for the validate workflow only; autosync is unchanged."""
    (tmp_path / ".github/workflows").mkdir(parents=True)
    (tmp_path / WORKFLOW).write_text(_old_workflow("on:\n  workflow_run:\n    workflows: [x]\n"))
    current, proposed = plan(tmp_path)
    assert "workflow_run" in proposed


def test_validate_scaffold_uses_the_action_pins_of_this_repositorys_tests():
    import re
    uses = re.compile(r"uses:\s*(\S+)")
    mine = set(uses.findall(load_scaffold("researchteam-validate-derived.yml")))
    theirs = set(uses.findall((ROOT / ".github/workflows/tests.yml").read_text()))
    assert mine and mine <= theirs, mine - theirs

