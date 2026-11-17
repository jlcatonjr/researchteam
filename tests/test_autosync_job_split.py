"""#182: the autosync gate runs in a job with no write token; a separate job, which runs no integrated code,
checks the gate's patch and opens the PR. The two step scripts are run here as the workflows ship them."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = [ROOT / ".github" / "workflows" / "agentteams-sync.yml",
             ROOT / "researchteam" / "scaffold" / "agentteams-sync-derived.yml"]
GATE = ROOT / "scripts" / "agentteams_autosync_gate.sh"
PACKAGE, APPLY = "Package the proposed change (patch + PR body)", "Check and apply the proposed change"
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@example.invalid", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
both = pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)


def _jobs(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))["jobs"]


def _run_of(path, job, name):
    return next(s["run"] for s in _jobs(path)[job]["steps"] if s.get("name") == name)


def git(cwd, *args):
    r = subprocess.run(["git", *args], cwd=cwd, env={**os.environ, **GIT_ENV}, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


@pytest.fixture
def repos(tmp_path):
    """`gate`: a repository the gate job changed. `fresh`: the write job's checkout of the same commit."""
    gate = tmp_path / "gate"
    (gate / "scripts").mkdir(parents=True)
    shutil.copy(GATE, gate / "scripts" / GATE.name)
    (gate / "docs").mkdir()
    (gate / "docs" / "a.md").write_text("one\n")
    (gate / "toolchain.lock").write_text("researchteam=jlcatonjr/researchteam@" + "a" * 40 + "\n")
    git(gate, "init", "-q", "-b", "main")
    git(gate, "add", "-A")
    git(gate, "commit", "-q", "-m", "base")
    fresh = tmp_path / "fresh"
    git(tmp_path, "clone", "-q", str(gate), str(fresh))
    return gate, fresh, tmp_path


def package(path, repos):
    gate, _fresh, tmp = repos
    body = tmp / "body.md"
    if not body.exists():
        body.write_text("gate text\n")
    out = tmp / "autosync-change"
    r = subprocess.run(["bash", "-c", _run_of(path, "autosync", PACKAGE)], cwd=gate, capture_output=True, text=True,
                       env={**os.environ, **GIT_ENV, "BODY": str(body), "OUT": str(out)})
    assert r.returncode == 0, r.stderr
    return out


SHA = "ab12ab12ab12ab12ab12ab12ab12ab12ab12ab12"


def apply(path, repos, change_dir, new_sha=SHA, sensitive="false", head=None):
    _gate, fresh, tmp = repos
    output = tmp / "output"
    output.write_text("")
    runner_temp = tmp / "runner-temp"
    runner_temp.mkdir(exist_ok=True)
    env = {**os.environ, **GIT_ENV, "NEW_SHA": new_sha, "GATE_SENSITIVE": sensitive, "CHANGE_DIR": str(change_dir),
           "EXPECTED_HEAD": head or git(fresh, "rev-parse", "HEAD"), "RUNNER_TEMP": str(runner_temp),
           "GITHUB_OUTPUT": str(output), "TMPDIR": str(runner_temp)}
    r = subprocess.run(["bash", "-c", _run_of(path, "open_pr", APPLY)], cwd=fresh, env=env, capture_output=True, text=True)
    outputs = dict(line.split("=", 1) for line in output.read_text().splitlines())
    return r, outputs


# ----------------------------------------------------------------------------- shape
@both
def test_the_gate_job_cannot_write_and_the_write_job_runs_no_integrated_code(path):
    jobs = _jobs(path)
    gate, write = jobs["autosync"], jobs["open_pr"]
    assert gate["permissions"] == {"contents": "read"}
    assert not any("create-pull-request" in s.get("uses", "") for s in gate["steps"])
    assert gate["outputs"] == {k: "${{ steps.gate.outputs.%s }}" % k for k in ("changed", "new_sha", "sensitive")}
    assert write["permissions"] == {"contents": "write", "pull-requests": "write"}
    assert write["needs"] == "autosync"
    assert write["if"] == ("${{ !cancelled() && needs.autosync.result == 'success' && "
                           "needs.autosync.outputs.changed == 'true' }}")
    uses = [s["uses"].split("@")[0] for s in write["steps"] if "uses" in s]
    assert uses == ["actions/checkout", "actions/download-artifact", "peter-evans/create-pull-request"]
    scripts = "\n".join(s.get("run", "") for s in write["steps"])
    for word in ("pip ", "researchteam ", "agentteams ", "python", "--mode"):
        assert word not in scripts, f"the write job must not run integrated code: {word!r}"
    assert "${{" not in scripts, "values reach the write job's scripts through env, never by expression"
    checkout = write["steps"][0]["with"]
    # No `ref`: a named commit leaves a detached HEAD, and create-pull-request then refuses to run (found by
    # the first real run, 2026-11-16). The check step confirms the commit and the branch instead.
    assert checkout == {"fetch-depth": 0, "persist-credentials": False}


@both
def test_the_pr_is_built_from_the_check_steps_own_outputs(path):
    cpr = next(s for s in _jobs(path)["open_pr"]["steps"] if s.get("id") == "cpr")["with"]
    assert cpr["body-path"] == "${{ steps.change.outputs.body }}" and "body" not in cpr
    assert "steps.change.outputs.new_sha" in cpr["title"] and "steps.change.outputs.new_sha" in cpr["commit-message"]
    assert "steps.change.outputs.sensitive == 'true'" in cpr["labels"]
    assert "needs.autosync" not in str(cpr)


def _handover(path):
    """The steps this change added, without the PR title text, which differs between the two workflows."""
    jobs = _jobs(path)
    names = [s.get("name") for s in jobs["autosync"]["steps"]]
    write = jobs["open_pr"]
    for step in write["steps"]:
        if step.get("id") == "cpr":
            title = step["with"].pop("title")
            assert step["with"].pop("commit-message") == title
    return jobs["autosync"]["steps"][names.index(PACKAGE):], write, {k: v for k, v in jobs["autosync"].items() if k != "steps"}


def test_both_workflows_share_the_handover():
    """The scaffold must be self-contained, so the steps are written twice. This keeps the copies equal."""
    assert _handover(WORKFLOWS[0]) == _handover(WORKFLOWS[1])
    assert len(_handover(WORKFLOWS[0])[0]) == 2, "the package step and the upload step end the gate job"


# ----------------------------------------------------------------------------- behaviour
@both
def test_a_change_round_trips_from_the_gate_job_to_the_write_job(path, repos):
    gate, fresh, _tmp = repos
    (gate / "docs" / "a.md").write_text("two\n")
    (gate / "docs" / "new.bin").write_bytes(bytes(range(256)))
    (gate / "docs" / "gone.md").write_text("x\n")
    git(gate, "add", "-A")
    git(gate, "commit", "-q", "-m", "more")
    git(fresh, "pull", "-q")
    (gate / "docs" / "gone.md").unlink()
    (gate / "docs" / "a.md").write_text("three\n")
    r, out = apply(path, repos, package(path, repos))
    assert r.returncode == 0, r.stdout + r.stderr
    assert (fresh / "docs" / "a.md").read_text() == "three\n" and not (fresh / "docs" / "gone.md").exists()
    assert (fresh / "docs" / "new.bin").read_bytes() == bytes(range(256))
    assert out["new_sha"] == SHA and out["sensitive"] == "false"
    body = Path(out["body"]).read_text()
    assert "ran no integrated code" in body and body.rstrip().endswith("gate text") and "[!WARNING]" not in body


@both
def test_the_write_job_decides_the_label_itself(path, repos):
    gate, _fresh, _tmp = repos
    (gate / "scripts" / "extra.sh").write_text("echo\n")
    r, out = apply(path, repos, package(path, repos), sensitive="false")   # the gate job says "not sensitive"
    assert r.returncode == 0, r.stdout + r.stderr
    assert out["sensitive"] == "true"
    assert "> - scripts/extra.sh" in Path(out["body"]).read_text()


@both
@pytest.mark.parametrize("name", ['a"b.sh', "a\\b.sh", "a\tb.sh", "caf\u00e9.sh"])
def test_a_name_git_would_quote_is_still_classified(path, repos, name):
    """git wraps such a name in quotes in its plain listing, which would hide the leading `scripts/`."""
    gate, _fresh, _tmp = repos
    (gate / "scripts" / name).write_text("echo\n")
    r, out = apply(path, repos, package(path, repos), sensitive="false")
    assert r.returncode == 0, r.stdout + r.stderr
    assert out["sensitive"] == "true"


@both
def test_a_name_with_a_line_break_is_sensitive(path, repos):
    gate, _fresh, _tmp = repos
    (gate / "docs" / "a\nb.md").write_text("x\n")
    r, out = apply(path, repos, package(path, repos), sensitive="false")
    assert r.returncode == 0, r.stdout + r.stderr
    assert out["sensitive"] == "true" and "line break in its name" in Path(out["body"]).read_text()


@both
def test_a_name_ending_in_line_breaks_is_sensitive(path, repos):
    """The names are counted from the listing itself: `$(...)` drops trailing line breaks."""
    gate, _fresh, _tmp = repos
    (gate / "docs" / "a.md\n\n").write_text("x\n")
    r, out = apply(path, repos, package(path, repos), sensitive="false")
    assert r.returncode == 0, r.stdout + r.stderr
    assert out["sensitive"] == "true"


@both
def test_no_expression_is_expanded_inside_a_gate_job_script(path):
    for step in _jobs(path)["autosync"]["steps"]:
        if step.get("id") in ("gate",) or step.get("name") == PACKAGE:
            assert "${{" not in step["run"], step.get("name")
    gate = next(s for s in _jobs(path)["autosync"]["steps"] if s.get("id") == "gate")
    assert gate["env"]["FORCE_INPUT"] == "${{ inputs.force }}" and gate["env"]["EVENT_NAME"] == "${{ github.event_name }}"


@both
def test_a_detached_checkout_is_refused(path, repos):
    out_dir = package(path, repos)
    git(repos[1], "checkout", "-q", "--detach")
    r, _out = apply(path, repos, out_dir)
    assert r.returncode == 1 and "not on a branch" in r.stdout


@both
def test_the_gate_jobs_answer_can_only_add(path, repos):
    gate, _fresh, _tmp = repos
    (gate / "docs" / "a.md").write_text("two\n")
    r, out = apply(path, repos, package(path, repos), sensitive="true")
    assert r.returncode == 0 and out["sensitive"] == "true"
    assert "(reported by the gate job)" in Path(out["body"]).read_text()


@both
def test_a_changed_pinned_repository_is_sensitive(path, repos):
    gate, _fresh, _tmp = repos
    (gate / "toolchain.lock").write_text("researchteam=someone/else@" + "a" * 40 + "\n")
    r, out = apply(path, repos, package(path, repos))
    assert r.returncode == 0 and out["sensitive"] == "true"
    assert "toolchain.lock (pinned repository or release tag changed)" in Path(out["body"]).read_text()


@both
def test_a_moved_pin_alone_is_routine(path, repos):
    gate, _fresh, _tmp = repos
    (gate / "toolchain.lock").write_text("researchteam=jlcatonjr/researchteam@" + "b" * 40 + "\n")
    r, out = apply(path, repos, package(path, repos))
    assert r.returncode == 0 and out["sensitive"] == "false"


@both
def test_without_a_committed_gate_script_everything_is_sensitive(path, repos):
    gate, fresh, _tmp = repos
    git(gate, "rm", "-q", "scripts/" + GATE.name)
    git(gate, "commit", "-q", "-m", "no gate")
    git(fresh, "pull", "-q")
    (gate / "docs" / "a.md").write_text("two\n")
    r, out = apply(path, repos, package(path, repos))
    assert r.returncode == 0 and out["sensitive"] == "true"


@both
def test_an_empty_patch_applies_nothing_and_passes(path, repos):
    r, out = apply(path, repos, package(path, repos))
    assert r.returncode == 0, r.stdout + r.stderr
    assert git(repos[1], "status", "--porcelain") == "" and out["sensitive"] == "false"


@both
def test_a_long_body_is_cut_not_refused(path, repos):
    gate, _fresh, tmp = repos
    (tmp / "body.md").write_text("x" * 70000)
    (gate / "docs" / "a.md").write_text("two\n")
    r, out = apply(path, repos, package(path, repos))
    assert r.returncode == 0
    body = Path(out["body"]).read_text()
    assert len(body) < 51000 and "cut at 50,000 bytes" in body


@both
@pytest.mark.parametrize("new_sha,sensitive", [("abc1234", "false"), (SHA[:39], "false"), (SHA + "a", "false"),
                                               (SHA[:33] + "; id", "false"), (SHA.upper(), "false"), ("", "false"),
                                               (SHA, ""), (SHA, "TRUE"), (SHA + "\nx=1", "false")],
                         ids=["short", "39", "41", "shell", "upper", "empty", "no-flag", "TRUE", "second-line"])
def test_bad_gate_outputs_are_refused(path, repos, new_sha, sensitive):
    r, out = apply(path, repos, package(path, repos), new_sha=new_sha, sensitive=sensitive)
    assert r.returncode == 1 and "::error::autosync open_pr:" in r.stdout and out == {}


@both
def test_a_checkout_of_another_commit_is_refused(path, repos):
    r, _out = apply(path, repos, package(path, repos), head="0" * 40)
    assert r.returncode == 1 and "not the commit the gate ran on" in r.stdout


@both
@pytest.mark.parametrize("spoil", ["extra", "missing", "link"])
def test_an_artifact_that_is_not_exactly_two_regular_files_is_refused(path, repos, spoil):
    out_dir = package(path, repos)
    if spoil == "extra":
        (out_dir / "more.txt").write_text("x")
    elif spoil == "missing":
        (out_dir / "pr-body.md").unlink()
    else:
        (out_dir / "pr-body.md").unlink()
        (out_dir / "pr-body.md").symlink_to(repos[2] / "body.md")
    r, _out = apply(path, repos, out_dir)
    assert r.returncode == 1 and "the artifact" in r.stdout


@both
def test_a_new_symbolic_link_is_refused(path, repos):
    gate, _fresh, _tmp = repos
    (gate / "docs" / "link").symlink_to("a.md")
    r, _out = apply(path, repos, package(path, repos))
    assert r.returncode == 1 and "symbolic link" in r.stdout


@both
def test_a_file_turned_into_a_symbolic_link_is_refused(path, repos):
    gate, _fresh, _tmp = repos
    (gate / "docs" / "a.md").unlink()
    (gate / "docs" / "a.md").symlink_to("../toolchain.lock")
    r, _out = apply(path, repos, package(path, repos))
    assert r.returncode == 1 and "symbolic link" in r.stdout


@both
def test_a_gitattributes_filter_is_refused(path, repos):
    gate, _fresh, _tmp = repos
    (gate / "docs" / ".gitattributes").write_text("* filter=lfs\n")
    r, _out = apply(path, repos, package(path, repos))
    assert r.returncode == 1 and ".gitattributes" in r.stdout


@both
def test_a_patch_for_a_git_path_is_refused(path, repos):
    out_dir = package(path, repos)
    (out_dir / "change.patch").write_text(
        "diff --git a/.git/hooks/pre-commit b/.git/hooks/pre-commit\nnew file mode 100755\n"
        "index 0000000000000000000000000000000000000000..8b137891791fe96927ad78e64b0aad7bded08bdc\n"
        "--- /dev/null\n+++ b/.git/hooks/pre-commit\n@@ -0,0 +1 @@\n+\n")
    r, _out = apply(path, repos, out_dir)
    # git apply itself refuses the path, so the step's own `.git` check is a backstop this test cannot reach.
    assert r.returncode == 1 and "the patch does not apply" in r.stdout
    assert not (repos[1] / ".git" / "hooks" / "pre-commit").exists()


@both
def test_a_patch_that_does_not_apply_is_refused(path, repos):
    out_dir = package(path, repos)
    (out_dir / "change.patch").write_text("not a patch\n")
    r, _out = apply(path, repos, out_dir)
    assert r.returncode == 1 and "does not apply" in r.stdout
