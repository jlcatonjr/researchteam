"""One `.researchteam` reader: `update`'s fetch ref and drift's comparison ref always agree."""
import sys

import pytest

from researchteam import _drift, _update_cmd, cli
from researchteam._personalize import is_upstream, read_marker


@pytest.mark.parametrize("line", ["ref=foo", "ref = foo", 'ref = "foo"', "ref = 'foo'", "ref = foo  # pinned"])
def test_every_spelling_gives_the_same_ref_in_both_readers(tmp_path, line):
    (tmp_path / ".researchteam").write_text(f"[researchteam]\n{line}\n")
    assert cli._read_marker_ref(tmp_path) == "foo"
    assert _drift.pinned_ref(tmp_path) == ("foo", "marker ref")


def test_missing_or_empty_ref_is_main(tmp_path):
    assert cli._read_marker_ref(tmp_path) == "main" and _drift.pinned_ref(tmp_path) == ("main", "main")
    (tmp_path / ".researchteam").write_text("ref =\n")
    assert cli._read_marker_ref(tmp_path) == "main" and _drift.pinned_ref(tmp_path) == ("main", "main")


def test_the_first_occurrence_of_a_key_wins(tmp_path):
    (tmp_path / ".researchteam").write_text("ref = first\nref = second\n")
    assert read_marker(tmp_path)["ref"] == "first" and cli._read_marker_ref(tmp_path) == "first"


def test_layer1_and_is_upstream_use_the_same_rules(tmp_path):
    (tmp_path / ".researchteam").write_text('layer1 = "off"\nis_upstream = "true"\n')
    assert not _update_cmd.layer1_enabled(tmp_path) and is_upstream(tmp_path)
    (tmp_path / ".researchteam").write_text("layer1 = on\nis_upstream = false\n")
    assert _update_cmd.layer1_enabled(tmp_path) and not is_upstream(tmp_path)


def test_update_refuses_an_unsafe_ref_before_running(tmp_path, monkeypatch):
    (tmp_path / ".researchteam").write_text("ref = a/../b\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["researchteam", "update", "--dry-run"])
    monkeypatch.setattr(cli, "_release_locked_ref", lambda root: None)
    import researchteam._update_cmd as upd
    monkeypatch.setattr(upd, "run_update", lambda *a, **k: pytest.fail("ran update"))
    with pytest.raises(SystemExit, match="refusing the upstream ref"):
        cli.main()
