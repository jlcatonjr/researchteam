"""`layer1 = off` in .researchteam: layer-2-only repos (Batallion run 38081664174)."""
from __future__ import annotations

import pytest

from researchteam import _update_cmd


@pytest.mark.parametrize("marker, expect", [
    (None, True),
    ("[researchteam]\nref = main\n", True),
    ("[researchteam]\nref = main\nlayer1 = off\n", False),
    ("layer1 = \"False\"\n", False),
    ("layer1 = on\n", True),
])
def test_layer1_flag_parsing(tmp_path, marker, expect):
    if marker is not None:
        (tmp_path / ".researchteam").write_text(marker)
    assert _update_cmd.layer1_enabled(tmp_path) is expect


@pytest.fixture
def no_layer1(tmp_path, monkeypatch):
    (tmp_path / ".researchteam").write_text("[researchteam]\nref = main\nlayer1 = off\n")
    calls = []
    monkeypatch.setattr(_update_cmd, "_run_agentteams", lambda *a, **k: calls.append("agentteams"))
    monkeypatch.setattr(_update_cmd, "_render_native_surfaces", lambda *a, **k: calls.append("native"))
    monkeypatch.setattr(_update_cmd, "_refresh_codex", lambda *a, **k: calls.append("codex"))
    monkeypatch.setattr(_update_cmd, "managed_files_for", lambda profile: [])
    monkeypatch.setattr(_update_cmd, "_sync_notes", lambda *a, **k: None)
    return calls


def test_full_update_skips_layer1_when_off(tmp_path, no_layer1, capsys):
    _update_cmd.run_update(tmp_path, ref="main", yes=True, dry_run=False, layer2_only=False)
    assert no_layer1 == [] and "layer1 = off" in capsys.readouterr().out


def test_layer1_only_is_a_noop_when_off(tmp_path, no_layer1):
    _update_cmd.run_update(tmp_path, ref="main", yes=True, dry_run=False, layer2_only=False, layer1_only=True)
    assert no_layer1 == []


def test_materialize_refuses_when_off(tmp_path, no_layer1):
    with pytest.raises(SystemExit, match="layer1 = off"):
        _update_cmd.run_materialize(tmp_path, yes=True, dry_run=False)


def test_missing_descriptor_explains_both_ways_out(tmp_path):
    with pytest.raises(SystemExit) as exc:
        _update_cmd._resolve_descriptor(tmp_path)
    assert "layer1 = off" in str(exc.value) and "brief.json" in str(exc.value)


def test_doctor_skips_agentteams_checks_when_off(tmp_path, monkeypatch, capsys):
    from researchteam import _doctor_cmd
    (tmp_path / ".researchteam").write_text("layer1 = off\n")
    monkeypatch.setattr(_update_cmd, "_resolve_agentteams", lambda: (None, "nowhere"))
    _doctor_cmd.run_doctor(tmp_path)  # no agentteams anywhere: must not FAIL (no SystemExit)
    out = capsys.readouterr()
    assert "agentteams checks skipped" in out.out and "[FAIL]" not in out.err


def test_layer1_only_message_when_off(tmp_path, no_layer1, capsys):
    _update_cmd.run_update(tmp_path, ref="main", yes=True, dry_run=False, layer2_only=False, layer1_only=True)
    assert "nothing to do for --layer1-only" in capsys.readouterr().out
