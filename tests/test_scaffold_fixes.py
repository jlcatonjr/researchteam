"""Regression tests for scaffold fixes found while bootstrapping a derived instance (H-1..H-4)."""
from __future__ import annotations

import csv
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SIGNER = ROOT / "scripts" / "sign_security_decision.py"


def _workspace(tmp_path: Path) -> Path:
    refs = tmp_path / ".github" / "agents" / "references"
    refs.mkdir(parents=True)
    (refs / "agent-privilege.json").write_text('{"enforce_decision_signing": true}\n')
    (refs / "security-decisions.log.csv").write_text(
        "timestamp,requesting_agent,action_reviewed,verdict,conditions,conditions_verified\n"
        "2026-01-01T00:00:00Z,security,overwrite,VOID,old,not-executed\n"
    )
    return tmp_path


def _sign(ws: Path, key: str | None) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k != "AGENTTEAMS_DECISION_SIGNING_KEY"}
    if key is not None:
        env["AGENTTEAMS_DECISION_SIGNING_KEY"] = key
    return subprocess.run([sys.executable, str(SIGNER), "--action", "overwrite", "--conditions", "test"],
                          cwd=ws, env=env, capture_output=True, text=True)


def test_signer_appends_verified_row(tmp_path, monkeypatch):
    pytest.importorskip("agentteams")
    ws = _workspace(tmp_path)
    r = _sign(ws, "throwaway-test-key")
    assert r.returncode == 0, r.stderr
    rows = list(csv.DictReader((ws / ".github/agents/references/security-decisions.log.csv").open()))
    assert rows[0]["verdict"] == "VOID" and rows[0]["signature"] == ""   # history preserved
    assert rows[-1]["verdict"] == "PASS" and len(rows[-1]["signature"]) == 64
    from agentteams.cli.security_gate import check_clearance
    monkeypatch.setenv("AGENTTEAMS_DECISION_SIGNING_KEY", "a-different-key")
    ok, reason = check_clearance(ws / ".github" / "agents", action="overwrite")
    assert not ok and "signature verification" in reason                  # wrong key fails closed


def test_signer_refuses_unexpected_log_layout_without_touching_it(tmp_path):
    ws = _workspace(tmp_path)
    log = ws / ".github/agents/references/security-decisions.log.csv"
    log.write_text("date,decision,status\n2026-01-01,overwrite,VOID\n")
    before = log.read_text()
    r = _sign(ws, "throwaway-test-key")
    assert r.returncode == 1 and log.read_text() == before


def test_signer_refuses_without_key(tmp_path):
    ws = _workspace(tmp_path)
    r = _sign(ws, None)
    assert r.returncode == 1 and "not set" in r.stderr


def test_init_accepts_existing_empty_dir_and_refuses_nonempty(tmp_path, monkeypatch):
    from researchteam import _init_cmd
    monkeypatch.chdir(tmp_path)
    (tmp_path / "full").mkdir()
    (tmp_path / "full" / "x").write_text("x")
    with pytest.raises(SystemExit):
        _init_cmd.run_init("full", "main", None)
    (tmp_path / "empty").mkdir()
    def stop(*_a, **_k):
        raise RuntimeError("stop-before-network")
    monkeypatch.setattr(_init_cmd, "fetch_tarball", stop)
    with pytest.raises(RuntimeError, match="stop-before-network"):  # got past the existence check
        _init_cmd.run_init("empty", "main", None)


def _scope(cwd, files: str | None, skip: str = "0") -> subprocess.CompletedProcess:
    script = ROOT / "scripts" / "validate_agentteams_update.sh"
    env = dict(os.environ, VALIDATION_SKIP_SCOPE=skip)
    env.pop("VALIDATION_CHANGED_FILES", None)
    if files is not None:
        env["VALIDATION_CHANGED_FILES"] = files
    return subprocess.run(["bash", str(script)], cwd=cwd, env=env, capture_output=True, text=True)


def test_validate_scope_skip_is_opt_in(tmp_path):
    strict = _scope(tmp_path, "environment.yml")
    assert strict.returncode != 0 and "Out-of-scope" in strict.stdout
    relaxed = _scope(tmp_path, "environment.yml", skip="1")
    assert relaxed.returncode == 0, relaxed.stdout + relaxed.stderr


def test_scope_allows_every_surface_a_layer1_run_writes(tmp_path):
    """Autosync run 37273449115 failed on .codex/agents/references/build-log.json (2026-10-05)."""
    written = "\n".join([
        ".codex/agents/references/build-log.json", ".codex/agents/orchestrator.toml",
        ".agents/skills/recall/SKILL.md", ".goose/recipes/orchestrator.yaml", "AGENTS.md",
        "references/bridges/claude.bridge.json", "sandbox/confine-run.sh",
        # exact layer-1 root artifacts (eaae749, 9fe245d, 3e3dc71) and the Codex role gate (agentteams b96e7e3)
        "references/architecture-graph.md", "references/architecture-graph.svg",
        "references/architecture-modules.svg", ".goosehints", "SETUP-REQUIRED.md",
        ".agentteams/bin/codex-role-gate.py",
    ])
    r = _scope(tmp_path, written)
    assert r.returncode == 0, r.stdout + r.stderr


def test_scope_still_refuses_user_owned_paths(tmp_path):
    for path in ("references/bibliography.bib", "Projects/x/report.md", "src/AGENTS.md", "environment.yml",
                 "AGENTS.md.bak", ".vscode/settings.json", "references/architecture-graph.md.bak",
                 "references/plans/x.md", ".agentteams/config.json", "Projects/SETUP-REQUIRED.md"):
        r = _scope(tmp_path, path)
        assert r.returncode != 0 and "Out-of-scope" in r.stdout, path


def test_scope_checks_new_untracked_files(tmp_path):
    """A brand-new out-of-scope file must not slip past because git diff lists only tracked files."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "x"],
                   cwd=tmp_path, check=True)
    (tmp_path / "AGENTS.md").write_text("x\n")
    assert _scope(tmp_path, None).returncode == 0
    (tmp_path / "environment.yml").write_text("x\n")
    r = _scope(tmp_path, None)
    assert r.returncode != 0 and "environment.yml" in r.stdout, r.stdout


def test_scope_reads_non_ascii_paths_unquoted(tmp_path):
    """git quotes non-ASCII names by default ("docs/\\303\\251.md"), which would fail the allowlist."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "x"],
                   cwd=tmp_path, check=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "théologie.md").write_text("x\n")
    r = _scope(tmp_path, None)
    assert r.returncode == 0, r.stdout + r.stderr
    (tmp_path / "données.txt").write_text("x\n")
    r = _scope(tmp_path, None)
    assert r.returncode != 0 and "données.txt" in r.stdout, r.stdout


def _sensitive(paths: list[str]) -> list[str]:
    gate = ROOT / "scripts" / "agentteams_autosync_gate.sh"
    r = subprocess.run(["bash", str(gate), "--classify-sensitive"], input="\n".join(paths) + "\n",
                       capture_output=True, text=True, check=True)
    return r.stdout.split()


def test_gate_flags_security_boundary_paths():
    sensitive = ["sandbox/confine-run.sh", ".agentteams/bin/codex-role-gate.py", ".github/workflows/x.yml",
                 ".github/actions/a/action.yml", ".github/agents/orchestrator.agent.md", "CODEOWNERS",
                 ".github/CODEOWNERS", ".claude/settings.json", ".claude/settings.local.json",
                 ".codex/config.toml", ".codex/hooks.json", ".goose/recipes/orchestrator.yaml",
                 ".vscode/tasks.json", "scripts/validate_agentteams_update.sh"]
    routine = [".github/agents/references/build-log.json", ".codex/agents/orchestrator.toml", "docs/x.md",
               "AGENTS.md", ".claude/agents/x.md", "references/bridges/claude.bridge.json",
               ".github/agents/sub/x.agent.md"]
    assert _sensitive(sensitive + routine) == sensitive


def test_gate_survives_replacing_itself_mid_run(tmp_path):
    """mathAgents run 38064339274: the derived layer-2 sync replaced the running gate, and bash read
    the new file from the old offset. The gate's self-copy prologue must make that harmless."""
    gate = (ROOT / "scripts" / "agentteams_autosync_gate.sh").read_text()
    prologue = gate[gate.index("# >>> self-copy"):gate.index("# <<< self-copy")]
    script = tmp_path / "gate.sh"
    body = (
        "#!/usr/bin/env bash\nset -uo pipefail\n" + prologue +
        # replace this very file mid-run with longer, different content (as `researchteam update` does)
        'python3 -c "import sys; open(sys.argv[1], \'w\').write(\'#\' * 4000 + chr(10) + \'echo WRONG; exit 7\' + chr(10))" '
        '"' + str(script) + '"\n'
        + "echo step-two-ran\n" * 50 + "echo done\n"
    )
    script.write_text(body)
    env = {k: v for k, v in os.environ.items() if k != "AUTOSYNC_GATE_REEXEC"}
    env["TMPDIR"] = str(tmp_path)
    r = subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip().endswith("done") and "WRONG" not in r.stdout, r.stdout + r.stderr
    assert not list(tmp_path.glob("agentteams_autosync_gate.*")), "the private copy must be removed on exit"


def test_gate_ignores_a_foreign_reexec_variable(tmp_path):
    """A planted AUTOSYNC_GATE_REEXEC must neither skip the copy nor get its target deleted."""
    victim = tmp_path / "keep.txt"
    victim.write_text("x")
    gate = ROOT / "scripts" / "agentteams_autosync_gate.sh"
    env = dict(os.environ, AUTOSYNC_GATE_REEXEC=str(victim), TMPDIR=str(tmp_path))
    r = subprocess.run(["bash", str(gate), "--classify-sensitive"], input="sandbox/x\n", env=env,
                       capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.split() == ["sandbox/x"], r.stdout + r.stderr
    assert victim.exists()
    assert not list(tmp_path.glob("agentteams_autosync_gate.*"))


def test_gate_refuses_a_second_reexec_and_keeps_itself(tmp_path):
    """The depth cap stops a re-exec loop; a planted depth must not delete the real gate either."""
    gate = ROOT / "scripts" / "agentteams_autosync_gate.sh"
    env = dict(os.environ, AUTOSYNC_GATE_DEPTH="1", TMPDIR=str(tmp_path))
    env.pop("AUTOSYNC_GATE_REEXEC", None)
    r = subprocess.run(["bash", str(gate), "--classify-sensitive"], input="sandbox/x\n", env=env,
                       capture_output=True, text=True)
    assert r.returncode == 1 and "second re-exec" in r.stderr, r.stdout + r.stderr
    assert gate.exists() and not list(tmp_path.glob("agentteams_autosync_gate.*"))

def test_gate_still_classifies_after_self_copy():
    assert _sensitive(["sandbox/x.sh", "docs/x.md"]) == ["sandbox/x.sh"]

def test_no_operator_home_paths_in_shipped_docs():
    home_path = re.compile(r"/(?:Users|home)/[^/\s`<>]+/")
    offenders = [str(p.relative_to(ROOT)) for p in (ROOT / "docs").rglob("*.md")
                 if home_path.search(p.read_text(encoding="utf-8"))]
    assert offenders == []


def test_no_flat_skill_files():
    """Claude Code loads only .claude/skills/<name>/SKILL.md; a flat <name>.md is never loaded."""
    flat = sorted(p.name for p in (ROOT / ".claude" / "skills").glob("*.md"))
    assert flat == [], f"flat skill files are never loaded by Claude Code: {flat}"


def test_every_skill_dir_has_front_matter():
    for p in (ROOT / ".claude" / "skills").glob("*/SKILL.md"):
        head = p.read_text(encoding="utf-8").split("---")
        assert len(head) >= 3 and "name:" in head[1] and "description:" in head[1], p
