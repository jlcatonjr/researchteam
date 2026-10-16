"""Release-locked pins: researchteam/_release.py, check_toolchain's lock handling, the gate, update's ref."""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

from researchteam import _release as rel

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location("check_toolchain", ROOT / "scripts" / "check_toolchain.py")
ct = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ct)

A, B, C = "a" * 40, "b" * 40, "c" * 40
RT, AT = "jlcatonjr/researchteam", "jlcatonjr/agentteams"


def _vcs(sha):
    return {"version": "1", "direct_url": {"url": "https://example.invalid/pkg", "vcs_info": {"commit_id": sha}}}


# --- tag ordering and release lines ---------------------------------------------------------------

def test_tag_order_puts_a_final_after_its_rcs():
    tags = ["v1.0.1", "v1.0.0", "v1.0.0-rc.10", "v1.0.0-rc.9", "v1.0.0-rc.1"]
    assert sorted(tags, key=rel.tag_key) == ["v1.0.0-rc.1", "v1.0.0-rc.9", "v1.0.0-rc.10", "v1.0.0", "v1.0.1"]
    assert rel.release_line("v1.0.0-rc.10") == rel.release_line("v1.0.3") == "v1.0"
    with pytest.raises(rel.ReleaseError):
        rel.tag_key("main")


def test_newest_on_line_stays_on_the_line_and_moves_forward(monkeypatch):
    monkeypatch.setattr(rel, "remote_tags", lambda repo: dict.fromkeys(
        ["v1.0.0-rc.9", "v1.0.0-rc.10", "v1.0.0", "v1.1.0", "v0.9.0"], "x"))
    assert rel.newest_on_line(AT, "v1.0.0-rc.9") == "v1.0.0"
    assert rel.newest_on_line(AT, "v1.0.0") is None
    assert rel.newest_on_line(AT, "v1.1.0") is None


def test_verify_needs_allowed_signers(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTTEAMS_ALLOWED_SIGNERS", str(tmp_path / "absent"))
    with pytest.raises(rel.ReleaseError, match="no allowed_signers"):
        rel.verify_tag(AT, "v1.0.0-rc.10")


class _FakeGit:
    """Canned git: an annotated tag whose verify output and remote advertisement a test controls."""

    def __init__(self, signer="SHA256:IPdnLwlFdHNhr7QGKVWU40BOKyYzv2u8qxP/qxnzTNM", good=True, kind="tag",
                 obj="d" * 40, advertised="d" * 40):
        self.signer, self.good, self.kind, self.obj, self.advertised = signer, good, kind, obj, advertised

    def __call__(self, args, cwd=None, timeout=60):
        def done(out="", err="", rc=0):
            return subprocess.CompletedProcess(args, rc, out, err)
        if args[0] == "ls-remote":
            return done(f"{self.advertised}\trefs/tags/v1.0.0-rc.10\n{C}\trefs/tags/v1.0.0-rc.10^{{}}\n")
        cmd = [a for a in args if not a.startswith("gpg.ssh.allowedSignersFile")]
        if "rev-parse" in cmd:
            return done((C if cmd[-1].endswith("^{commit}") else self.obj) + "\n")
        if "cat-file" in cmd:
            return done(self.kind + "\n")
        if "tag" in cmd and "-v" in cmd:
            msg = f'Good "git" signature for op@example.com with RSA key {self.signer}\n'
            # stdout carries the tagger-controlled message: a forged "Good signature" there must not count
            forged = f'object {C}\ntag v1.0.0-rc.10\n\nGood "git" signature for a@b with RSA key {next(iter(rel.RELEASE_KEY_FINGERPRINTS))}\n'
            return done(out=forged, err=msg if self.good else "Could not verify signature.\n", rc=0 if self.good else 1)
        return done()


@pytest.fixture
def signers(tmp_path, monkeypatch):
    f = tmp_path / "allowed_signers"
    f.write_text("op@example.com ssh-rsa AAAA\n")
    monkeypatch.setenv("AGENTTEAMS_ALLOWED_SIGNERS", str(f))
    monkeypatch.setattr(rel, "release_signers", lambda path, dest: 1)  # the file's key counts as a release key
    return f


def test_signers_without_a_release_key_are_refused(signers, monkeypatch):
    monkeypatch.setattr(rel, "release_signers", lambda path, dest: 0)
    monkeypatch.setattr(rel, "_git", _FakeGit())
    with pytest.raises(rel.ReleaseError, match="holds no release key"):
        rel.verify_tag(AT, "v1.0.0-rc.10")


def test_release_signers_keeps_only_pinned_fingerprints(tmp_path, monkeypatch):
    src, dest = tmp_path / "in", tmp_path / "out"
    src.write_text("# comment\nok@x namespaces=\"git\" ssh-rsa AAAAgood\nbad@x ssh-ed25519 AAAAbad\n")
    fp = next(iter(rel.RELEASE_KEY_FINGERPRINTS))

    def keygen(cmd, input, **kw):
        return subprocess.CompletedProcess(cmd, 0, f"4096 {fp if 'good' in input else 'SHA256:other'} x (RSA)\n", "")
    monkeypatch.setattr(rel.subprocess, "run", keygen)
    assert rel.release_signers(str(src), str(dest)) == 1
    assert dest.read_text() == 'ok@x namespaces="git" ssh-rsa AAAAgood\n'


def test_verify_returns_the_peeled_commit(signers, monkeypatch):
    monkeypatch.setattr(rel, "_git", _FakeGit())
    assert rel.verify_tag(AT, "v1.0.0-rc.10") == ("d" * 40, C)


@pytest.mark.parametrize("fake, why", [
    (_FakeGit(good=False), "does not verify"),
    (_FakeGit(signer="SHA256:someoneelse"), "not a release key"),
    (_FakeGit(kind="commit"), "lightweight"),
    (_FakeGit(advertised="e" * 40), "differs from advertised"),
])
def test_verify_refuses_anything_but_a_release_signed_annotated_tag(signers, monkeypatch, fake, why):
    monkeypatch.setattr(rel, "_git", fake)
    with pytest.raises(rel.ReleaseError, match=why):
        rel.verify_tag(AT, "v1.0.0-rc.10")


# --- lock format ----------------------------------------------------------------------------------

def test_tag_lines_roundtrip_and_old_readers_still_parse(tmp_path):
    lock = tmp_path / "toolchain.lock"
    ct.write_lock({"researchteam": (RT, A), "agentteams": (AT, B)}, str(lock), tags={"agentteams": "v1.0.0-rc.10"})
    text = lock.read_text()
    assert f"agentteams={AT}@{B}\nagentteams.tag=v1.0.0-rc.10\n" in text
    assert ct.read_lock(str(lock)) == {"researchteam": (RT, A), "agentteams": (AT, B)}
    assert ct.read_tags(str(lock)) == {"agentteams": "v1.0.0-rc.10"}
    # bootstrap_toolchain.sh reads pins with `grep -E "^name="`: the tag line must not match it
    assert [ln for ln in text.splitlines() if ln.startswith("agentteams=")] == [f"agentteams={AT}@{B}"]


def test_an_unlocked_lock_is_byte_identical_to_the_old_format(tmp_path):
    lock = tmp_path / "toolchain.lock"
    ct.write_lock({"researchteam": (RT, A), "agentteams": (AT, B)}, str(lock))
    assert lock.read_text() == ct.LOCK_HEADER + f"researchteam={RT}@{A}\nagentteams={AT}@{B}\n"


class _Rel:
    """Stand-in for researchteam._release: every tag verifies and peels to ``peeled``."""
    ReleaseError = rel.ReleaseError
    tag_key, release_line = staticmethod(rel.tag_key), staticmethod(rel.release_line)

    def __init__(self, peeled):
        self.peeled = peeled

    def verify_tag(self, repo, tag):
        return "d" * 40, self.peeled


def _tags(commits, old_pins, old_tags, new_tags, peeled=B):
    return ct.lock_tags(commits, old_pins, old_tags, new_tags, lambda: _Rel(peeled))


def test_a_locked_pin_keeps_its_tag_while_unchanged():
    pins = {"researchteam": (RT, A), "agentteams": (AT, B)}
    assert _tags(pins, pins, {"agentteams": "v1.0.0-rc.10"}, {}) == ({"agentteams": "v1.0.0-rc.10"}, "")


def test_a_locked_pin_never_moves_to_an_untagged_commit():
    old = {"researchteam": (RT, A), "agentteams": (AT, B)}
    new = {"researchteam": (RT, A), "agentteams": (AT, C)}  # e.g. agentteams main
    tags, why = _tags(new, old, {"agentteams": "v1.0.0-rc.10"}, {})
    assert tags is None and "release-locked at v1.0.0-rc.10" in why


def test_a_locked_pin_moves_to_a_newer_verified_tag_on_its_line():
    old = {"researchteam": (RT, A), "agentteams": (AT, B)}
    new = {"researchteam": (RT, A), "agentteams": (AT, C)}
    assert _tags(new, old, {"agentteams": "v1.0.0-rc.10"}, {"agentteams": "v1.0.0"}, peeled=C) == (
        {"agentteams": "v1.0.0"}, "")


@pytest.mark.parametrize("new_tag, peeled, why", [
    ("v1.1.0", C, "not on v1.0.0-rc.10's release line"),
    ("v1.0.0-rc.9", C, "or is older"),
    ("v1.0.0", "f" * 40, "is not v1.0.0's peeled commit"),
])
def test_a_locked_pin_refuses_other_lines_older_tags_and_wrong_commits(new_tag, peeled, why):
    old = {"researchteam": (RT, A), "agentteams": (AT, B)}
    new = {"researchteam": (RT, A), "agentteams": (AT, C)}
    tags, msg = _tags(new, old, {"agentteams": "v1.0.0-rc.10"}, {"agentteams": new_tag}, peeled=peeled)
    assert tags is None and why in msg


def test_write_lock_refuses_and_leaves_a_locked_lock_untouched(tmp_path, monkeypatch, capsys):
    lock = tmp_path / "toolchain.lock"
    ct.write_lock({"researchteam": (RT, A), "agentteams": (AT, B)}, str(lock), tags={"agentteams": "v1.0.0-rc.10"})
    before = lock.read_text()
    monkeypatch.setattr(ct, "LOCK", str(lock))
    monkeypatch.setattr(ct, "installed", lambda py: {"researchteam": _vcs(A), "agentteams": _vcs(C)})
    assert ct.main(["--python", "py", "--write-lock"]) == 1
    assert "release-locked" in capsys.readouterr().out and lock.read_text() == before


def test_a_locked_status_check_ignores_upstream_main(tmp_path, monkeypatch, capsys):
    lock = tmp_path / "toolchain.lock"
    ct.write_lock({"researchteam": (RT, A), "agentteams": (AT, B)}, str(lock), tags={"agentteams": "v1.0.0-rc.10"})
    monkeypatch.setattr(ct, "LOCK", str(lock))
    monkeypatch.setattr(ct, "installed", lambda py: {"researchteam": _vcs(A), "agentteams": _vcs(B)})
    monkeypatch.setattr(ct, "remote_main", lambda repo: C)
    ct.main(["--python", "py"])
    out = capsys.readouterr().out
    assert "agentteams: upstream main" not in out and "researchteam: upstream main" in out


# --- the autosync gate ----------------------------------------------------------------------------

def _gate_repo(tmp_path, shim_body):
    """A throwaway derived repo whose `python` is a shim answering the gate's check_toolchain calls."""
    repo, bin_dir = tmp_path / "repo", tmp_path / "bin"
    (repo / "scripts").mkdir(parents=True)
    bin_dir.mkdir()
    (repo / "scripts" / "agentteams_autosync_gate.sh").write_text(
        (ROOT / "scripts" / "agentteams_autosync_gate.sh").read_text())
    (repo / "scripts" / "check_toolchain.py").write_text("")
    (repo / "toolchain.lock").write_text(f"researchteam={RT}@{A}\nagentteams={AT}@{B}\nagentteams.tag=v1.0.0-rc.10\n")
    shim = bin_dir / "python"
    shim.write_text("#!/usr/bin/env bash\n" + shim_body)
    shim.chmod(0o755)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    env = dict(os.environ, PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}", TMPDIR=str(tmp_path),
               AGENTTEAMS_GIT="https://invalid.example/never-contacted.git")
    env.pop("AUTOSYNC_GATE_REEXEC", None)
    env.pop("GITHUB_OUTPUT", None)
    return repo, env


def _run_gate(repo, env, *args):
    return subprocess.run(["bash", "scripts/agentteams_autosync_gate.sh", "--mode", "derived", *args],
                          cwd=repo, env=env, capture_output=True, text=True)


def test_gate_is_a_noop_on_a_locked_line_with_no_newer_tag(tmp_path):
    repo, env = _gate_repo(tmp_path, 'case "$*" in *--release-candidate*) exit 0;; esac; exit 9\n')
    r = _run_gate(repo, env, "--check-only")
    assert r.returncode == 0 and "nothing to integrate" in r.stdout
    assert "agentteams main" not in r.stdout and "invalid.example" not in r.stdout  # main was never consulted


def test_gate_fails_closed_when_the_candidate_does_not_verify(tmp_path):
    repo, env = _gate_repo(tmp_path, 'case "$*" in *--release-candidate*) echo v1.0.0;; *--verify-tag*) exit 1;; esac\n')
    r = _run_gate(repo, env, "--check-only")
    assert r.returncode == 1 and "did not verify" in r.stdout


def test_gate_targets_the_verified_peeled_commit(tmp_path):
    repo, env = _gate_repo(tmp_path, f'case "$*" in *--release-candidate*) echo v1.0.0;; '
                                     f'*--verify-tag*) echo {C};; esac\n')
    r = _run_gate(repo, env, "--check-only")
    assert r.returncode == 0 and f"verified: peeled commit {C}" in r.stdout and C in r.stdout


def test_gate_force_reintegrates_the_locked_tag_for_a_soak(tmp_path):
    repo, env = _gate_repo(tmp_path, f'case "$*" in *--release-candidate*) exit 0;; '
                                     f'*"--verify-tag agentteams v1.0.0-rc.10"*) echo {B};; *) exit 9;; esac\n')
    r = _run_gate(repo, env, "--check-only", "--force")
    assert r.returncode == 0 and f"v1.0.0-rc.10 verified: peeled commit {B}" in r.stdout


# --- update's Layer-2 ref -------------------------------------------------------------------------

def test_unlocked_researchteam_syncs_from_the_marker_ref(tmp_path):
    (tmp_path / "toolchain.lock").write_text(f"researchteam={RT}@{A}\nagentteams={AT}@{B}\n")
    assert rel.locked_layer2_ref(tmp_path, RT) is None


def test_locked_researchteam_syncs_from_its_verified_tag(tmp_path, monkeypatch):
    (tmp_path / "toolchain.lock").write_text(f"researchteam={RT}@{A}\nresearchteam.tag=v1.0.0-rc.1\n")
    monkeypatch.setattr(rel, "verify_tag", lambda repo, tag: ("d" * 40, A))
    assert rel.locked_layer2_ref(tmp_path, RT) == (A, "v1.0.0-rc.1")


@pytest.mark.parametrize("lock, peeled, why", [
    (f"researchteam=evil/researchteam@{A}\nresearchteam.tag=v1.0.0-rc.1\n", A, "not jlcatonjr/researchteam"),
    (f"researchteam={RT}@{A}\nresearchteam.tag=v1.0.0-rc.1\n", C, "but v1.0.0-rc.1 is"),
])
def test_a_bad_locked_researchteam_ref_is_refused(tmp_path, monkeypatch, lock, peeled, why):
    (tmp_path / "toolchain.lock").write_text(lock)
    monkeypatch.setattr(rel, "verify_tag", lambda repo, tag: ("d" * 40, peeled))
    with pytest.raises(rel.ReleaseError, match=why):
        rel.locked_layer2_ref(tmp_path, RT)


def test_cli_fails_closed_on_an_unverifiable_locked_ref(tmp_path, monkeypatch):
    from researchteam import cli
    (tmp_path / "toolchain.lock").write_text(f"researchteam={RT}@{A}\nresearchteam.tag=v1.0.0-rc.1\n")

    def boom(repo, tag):
        raise rel.ReleaseError("signature does not verify")
    monkeypatch.setattr(rel, "verify_tag", boom)
    with pytest.raises(SystemExit, match="Layer-2 sync refused"):
        cli._release_locked_ref(tmp_path)
