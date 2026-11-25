"""Step B part 2a: the provenance record (4.6), the overrides file and the identity registry (4.4), and the
survey-registry command (section 7)."""
import json
import os
import shutil

import pytest

from survey_support import (
    FIXTURES, STUDY_REL, make_repo, run, survey_identity as ident, survey_provenance as prov,
    survey_registry, survey_spec as sp, survey_validate, tree,
)

ROWS = f"{STUDY_REL}/rows"
REGISTRY = f"{ROWS}/registry.csv"
RECORD = f"{REGISTRY}.provenance.json"
HEADER = "alias_id,target_id,decision,decided_by,reason\n"
WHO = "Ines Marlow (invented reviewer)"


def _overrides(root, lines):
    """Write the overrides file's bytes directly (a value may be one csv.writer cannot write on every Python)."""
    body = "".join(",".join(cells) + "\n" for cells in lines)
    (root / ROWS / "overrides.csv").write_bytes((HEADER + body).encode("utf-8"))


def _row(alias, target, decision, who=WHO, reason="an invented reason"):
    return [alias, target, decision, who, reason]


def _build(root):
    return run(survey_registry, "--root", str(root), "tidebell")


def _study(root):
    return sp.load_study("tidebell", root)


# --------------------------------------------------------------------------- the build
def test_the_registry_is_built_from_the_rows(tmp_path):
    root = make_repo(tmp_path)
    code, out, _ = _build(root)
    assert code == 0 and f"wrote: {REGISTRY} (3 person(s)" in out and f"wrote: {RECORD}" in out
    assert (root / REGISTRY).read_bytes() == (
        b"person_id,display_name,identity_id,merged_from\n"
        b"guild-01,guild-01,,\nwarden-01,warden-01,,\nwarden-02,warden-02,,\n")


def test_persons_come_from_the_attribution_file_before_any_evidence(tmp_path):
    """4.4, lines 509-511: a study builds its registry before its first evidence row."""
    root = make_repo(tmp_path, lambda s: s.update(status="draft"))
    (root / ROWS / "evidence.csv").unlink()
    assert _build(root)[0] == 0
    assert b"warden-02" in (root / REGISTRY).read_bytes()


def test_the_record_is_4_6s_shape(tmp_path):
    root = make_repo(tmp_path)
    _overrides(root, [_row("guild-01", "guild-01", "link")])
    _build(root)
    data = (root / RECORD).read_bytes()
    doc = json.loads(data)
    assert list(doc) == sorted(prov.RECORD_KEYS) and prov.check_record_shape(doc, "r") == []
    assert doc["output"] == REGISTRY and doc["tool"] == "survey-registry" and doc["study"] == "tidebell-survey"
    assert doc["gates"] == {} and doc["plugins"] == [] and doc["legacy_exceptions"] == 0
    assert [e["path"] for e in doc["inputs"]] == [f"{STUDY_REL}/study.json", f"{ROWS}/evidence.csv",
                                                  f"{ROWS}/attribution.csv", f"{ROWS}/overrides.csv"]
    import hashlib
    for e in doc["inputs"]:
        assert e["sha256"] == hashlib.sha256((root / e["path"]).read_bytes()).hexdigest()
    assert data.endswith(b"}\n") and b" " not in data.split(b'"tool"')[0]  # canonical JSON, no date
    assert prov.check_current(root, RECORD).built


def test_an_input_that_changes_leaves_the_registry_not_built(tmp_path):
    root = make_repo(tmp_path)
    _build(root)
    (root / ROWS / "evidence.csv").write_bytes((root / ROWS / "evidence.csv").read_bytes() + b"\n")
    cur = prov.check_current(root, RECORD)
    assert not cur.built and any("evidence.csv changed" in r for r in cur.reasons)
    (root / RECORD).unlink()
    assert prov.check_current(root, RECORD).reasons == [f"the record {RECORD} is missing"]


def test_the_build_is_deterministic(tmp_path):
    root = make_repo(tmp_path)
    _build(root)
    first = tree(root)
    code, out, _ = _build(root)
    assert code == 0 and out.startswith("unchanged:") and tree(root) == first
    other = make_repo(tmp_path / "again")
    _build(other)
    assert (other / REGISTRY).read_bytes() == (root / REGISTRY).read_bytes()
    assert (other / RECORD).read_bytes() == (root / RECORD).read_bytes()


def test_outputs_are_mode_0644(tmp_path):
    root = make_repo(tmp_path)
    _build(root)
    assert all(os.stat(root / r).st_mode & 0o777 == 0o644 for r in (REGISTRY, RECORD))


# --------------------------------------------------------------------------- applying overrides
def test_a_merge_folds_the_alias_into_the_target(tmp_path):
    root = make_repo(tmp_path)
    _overrides(root, [_row("warden-02", "warden-01", "merge")])
    assert _build(root)[0] == 0
    text = (root / REGISTRY).read_text(encoding="utf-8")
    assert "warden-01,warden-01,,warden-02\n" in text and "\nwarden-02," not in text


def test_a_link_records_the_identity(tmp_path):
    root = make_repo(tmp_path)
    _overrides(root, [_row("guild-01", "guild-01", "link"), _row("warden-02", "warden-01", "distinct")])
    assert _build(root)[0] == 0
    assert "guild-01,guild-01,guild-01,\n" in (root / REGISTRY).read_text(encoding="utf-8")


def test_the_invented_overrides_fixture_applies(tmp_path):
    root = make_repo(tmp_path)
    shutil.copy(FIXTURES / "identity" / "overrides.csv", root / ROWS / "overrides.csv")
    assert _build(root)[0] == 0


def test_a_distinct_row_changes_no_registry_row(tmp_path):
    root = make_repo(tmp_path)
    _build(root)
    before = (root / REGISTRY).read_bytes()
    _overrides(root, [_row("warden-02", "warden-01", "distinct")])
    _build(root)
    assert (root / REGISTRY).read_bytes() == before


# --------------------------------------------------------------------------- every overrides check
OVERRIDE_CASES = {
    "overrides-empty": [_row("warden-02", "warden-01", "merge", who="")],
    "overrides-decision": [_row("warden-02", "warden-01", "same")],
    "overrides-alias": [_row("warden-99", "warden-01", "merge")],
    "overrides-target": [_row("warden-02", "warden-99", "merge")],
    "overrides-self": [_row("warden-02", "warden-02", "merge")],
    "overrides-repeat": [_row("warden-02", "warden-01", "distinct"), _row("warden-01", "warden-02", "distinct")],
    "overrides-second": [_row("warden-02", "warden-01", "merge"), _row("warden-02", "guild-01", "link")],
    "overrides-conflict": [_row("warden-02", "warden-01", "merge"), _row("warden-01", "warden-02", "distinct")],
    "overrides-chain": [_row("warden-02", "warden-01", "merge"), _row("warden-01", "guild-01", "merge")],
    "overrides-shared-identity": [_row("warden-01", "guild-01", "link"), _row("warden-02", "guild-01", "link")],
}


@pytest.mark.parametrize("rule", sorted(OVERRIDE_CASES))
def test_each_overrides_check_refuses_and_writes_nothing(tmp_path, rule):
    root = make_repo(tmp_path)
    _overrides(root, OVERRIDE_CASES[rule])
    before = tree(root)
    code, out, _ = _build(root)
    assert code == 1 and f"[{rule}]" in out and "nothing was written" in out
    assert tree(root) == before
    code, out, _ = run(survey_validate, "--root", str(root), "tidebell")
    assert code == 1 and f"[{rule}]" in out  # survey-validate checks the overrides file too


@pytest.mark.parametrize("lines", [
    [_row("warden-02", "warden-02", "distinct")],                 # distinct with itself (line 503)
    [_row("warden-02", "guild-01", "link"), _row("warden-02", "warden-01", "link")],  # two links (lines 501-502)
    [_row("warden-02", "warden-01", "link"), _row("warden-01", "warden-02", "distinct")],  # distinct and linked
    [_row("warden-02", "warden-01", "merge"), _row("guild-01", "warden-02", "link")],  # link to a merged person
])
def test_more_overrides_breaches(tmp_path, lines):
    root = make_repo(tmp_path)
    _overrides(root, lines)
    assert _build(root)[0] == 1


def test_overrides_columns(tmp_path):
    root = make_repo(tmp_path)
    (root / ROWS / "overrides.csv").write_bytes(b"alias_id,target_id,decision\nwarden-02,warden-01,merge\n")
    code, out, _ = _build(root)
    assert code == 1 and "[overrides-columns]" in out


def test_a_link_may_name_the_alias_itself(tmp_path):
    """4.4, line 496: a link's target "may equal alias_id"."""
    root = make_repo(tmp_path)
    _overrides(root, [_row("warden-01", "warden-01", "link")])
    assert _build(root)[0] == 0


def test_several_distinct_rows_for_one_alias(tmp_path):
    root = make_repo(tmp_path)
    _overrides(root, [_row("warden-02", "warden-01", "distinct"), _row("warden-02", "guild-01", "distinct")])
    assert _build(root)[0] == 0


# --------------------------------------------------------------------------- refusals of this version
def test_a_vantage_module_is_not_loaded(tmp_path):
    root = make_repo(tmp_path, lambda s: (s.update(vantage={"module": {"file": "rules/forbidden.txt", "attr": "V",
                                                                       "version": "1"}}),
                                          s["signoffs"]["gates"]["S0"]["covers"].append("rules/forbidden.txt")))
    code, out, _ = _build(root)
    assert code == 1 and "[identity-vantage]" in out and not (root / RECORD).exists()


def test_plugin_evidence_is_not_read(tmp_path):
    root = make_repo(tmp_path, lambda s: s["evidence"].update(
        format="plugin", reader={"file": "rules/forbidden.txt", "attr": "R", "version": "1"}))
    code, out, _ = _build(root)
    assert code == 1 and "[evidence-plugin]" in out


def test_a_malformed_source_file_refuses(tmp_path):
    root = make_repo(tmp_path)
    (root / ROWS / "attribution.csv").write_bytes(b"unit_id\n")
    before = tree(root)
    assert _build(root)[0] == 1 and tree(root) == before


def test_a_link_on_the_way_to_the_registry_refuses(tmp_path):
    root = make_repo(tmp_path, lambda s: s["identity"].update(registry="out/registry.csv"))
    (root / STUDY_REL / "real-out").mkdir()
    os.symlink("real-out", root / STUDY_REL / "out")
    code, out, _ = _build(root)
    assert code == 1 and "symbolic link" in out and not list((root / STUDY_REL / "real-out").iterdir())


def test_a_registry_path_that_is_a_directory_refuses(tmp_path):
    root = make_repo(tmp_path)
    (root / REGISTRY).unlink()
    (root / REGISTRY).mkdir()
    assert _build(root)[0] == 1 and not (root / RECORD).exists()


# --------------------------------------------------------------------------- interrupted writes
def test_an_interrupted_registry_write_leaves_the_old_file(tmp_path, monkeypatch):
    root = make_repo(tmp_path)
    before = (root / REGISTRY).read_bytes()
    _overrides(root, [_row("warden-02", "warden-01", "merge")])

    def interrupted(tmp, path):
        raise KeyboardInterrupt("interrupted before os.replace")
    monkeypatch.setattr(prov, "replace", interrupted)
    with pytest.raises(KeyboardInterrupt):
        _build(root)
    assert (root / REGISTRY).read_bytes() == before and not (root / RECORD).exists()
    assert not [p for p in (root / ROWS).iterdir() if p.name.startswith(".survey-")]


def test_an_interruption_before_the_record_leaves_the_registry_not_built(tmp_path, monkeypatch):
    """4.4, lines 521-523: the record is written last, so an interrupted run is never wrongly current."""
    root = make_repo(tmp_path)
    _build(root)
    _overrides(root, [_row("warden-02", "warden-01", "merge")])
    calls = []
    real = prov.replace

    def second_fails(tmp, path):
        calls.append(path)
        if len(calls) == 2:
            raise KeyboardInterrupt("interrupted before the record")
        real(tmp, path)
    monkeypatch.setattr(prov, "replace", second_fails)
    with pytest.raises(KeyboardInterrupt):
        _build(root)
    assert b"warden-02" in (root / REGISTRY).read_bytes().split(b"\n", 2)[2]  # the new registry landed
    assert not prov.check_current(root, RECORD).built  # but its old record no longer matches


# --------------------------------------------------------------------------- candidates
def test_candidates_are_listed_and_never_applied(tmp_path):
    root = make_repo(tmp_path)
    (root / STUDY_REL / "rules" / "stop_words.txt").write_text("", encoding="utf-8")  # leave no word out
    before = tree(root)
    code, out, _ = run(survey_registry, "--root", str(root), "tidebell", "--candidates")
    assert code == 0 and tree(root) == before
    assert "candidate similar: warden-01 ~ warden-02 (undecided)" in out
    assert "candidate similar: guild-01 ~ warden-01 (undecided)" in out  # they share the word "01"


def test_stop_words_leave_words_out(tmp_path):
    root = make_repo(tmp_path)  # the fixture's stop words include "warden"
    out = run(survey_registry, "--root", str(root), "tidebell", "--candidates")[1]
    assert "warden-01 ~ warden-02" not in out and "guild-01 ~ warden-01" in out


def test_a_candidate_named_by_an_override_is_decided(tmp_path):
    root = make_repo(tmp_path)
    _overrides(root, [_row("warden-01", "guild-01", "distinct")])
    out = run(survey_registry, "--root", str(root), "tidebell", "--candidates")[1]
    assert "guild-01 ~ warden-01 (decided)" in out


def test_kinds_of_candidates():
    ov = ident.Overrides()
    found = ident.candidates(["a-1", "A-1x", "b"], {"a-1": "Orla Vennick", "A-1x": "orla  VENNICK", "b": "Vennick"},
                             set(), ov)
    kinds = {(c.person_id, c.other_id): c.kind for c in found}
    assert kinds[("a-1", "A-1x")] == "exact" or kinds[("A-1x", "a-1")] == "exact"
    assert ("a-1", "b") in kinds and kinds[("a-1", "b")] == "similar"
    assert ident.candidates(["x", "x"], {"x": "x"}, set(), ov)[0].kind == "same-id"


def test_candidates_refuse_a_vantage_study(tmp_path):
    root = make_repo(tmp_path, lambda s: (s.update(vantage={"module": {"file": "rules/forbidden.txt", "attr": "V",
                                                                       "version": "1"}}),
                                          s["signoffs"]["gates"]["S0"]["covers"].append("rules/forbidden.txt")))
    assert run(survey_registry, "--root", str(root), "tidebell", "--candidates")[0] == 1


# --------------------------------------------------------------------------- the provenance module (shared)
def test_gate_entries_record_each_state_as_gate_status_gives_it(tmp_path):
    root = make_repo(tmp_path)
    entries = prov.gate_entries(_study(root), ("S0", "S8"))
    assert entries["S8"] == {"state": "NOT DECLARED", "mode": "", "enforce": ""}
    assert entries["S0"]["state"] == "UNAVAILABLE" and entries["S0"]["enforce"] == "blocking"
    assert len(entries["S0"]["manifest_sha256"]) == 64


@pytest.mark.parametrize("doc", [
    {}, {k: "" for k in prov.RECORD_KEYS},
    dict(output="o", tool="t", study="s", schema_version="1", inputs=[{"path": "p"}], gates={}, plugins=[],
         legacy_exceptions=0),
    dict(output="o", tool="t", study="s", schema_version="1", inputs=[], gates={"S0": {"state": "X"}}, plugins=[],
         legacy_exceptions=0),
    dict(output="o", tool="t", study="s", schema_version="1", inputs=[], gates={}, plugins=[], legacy_exceptions=-1),
    dict(output="o", tool="t", study="s", schema_version="1", inputs=[], gates={}, plugins=[{"file": "f"}],
         legacy_exceptions=0),
])
def test_a_malformed_record_is_refused(doc):
    assert [f.rule for f in prov.check_record_shape(doc, "r")] == ["provenance-malformed"]


def test_a_malformed_record_file_is_not_built(tmp_path):
    root = make_repo(tmp_path)
    _build(root)
    (root / RECORD).write_text("{}", encoding="utf-8")
    assert not prov.check_current(root, RECORD).built


def test_a_recorded_plugin_that_changes_is_not_built(tmp_path):
    root = make_repo(tmp_path)
    study = _study(root)
    plugin_rel = f"{STUDY_REL}/rules/forbidden.txt"
    import hashlib
    digest = hashlib.sha256((root / plugin_rel).read_bytes()).hexdigest()
    record = prov.make_record(study, "o.csv", "t", [], {}, plugins=[{"file": plugin_rel, "attr": "a", "version": "1",
                                                                     "sha256": digest}])
    (root / "o.csv.provenance.json").write_bytes(prov.record_bytes(record))
    assert prov.check_current(root, "o.csv.provenance.json").built
    (root / plugin_rel).write_text("changed\n", encoding="utf-8")
    assert not prov.check_current(root, "o.csv.provenance.json").built


def test_the_record_name_is_the_output_plus_provenance_json():
    assert prov.record_rel("a/b.csv") == "a/b.csv.provenance.json"



def test_the_bridge_runs_survey_registry_and_refuses_root(tmp_path):
    import subprocess
    import sys
    from survey_support import ROOT
    root = make_repo(tmp_path)
    (root / "scripts").mkdir()
    shutil.copy(ROOT / "scripts" / "claude_researchteam_bridge.sh", root / "scripts")
    shutil.copytree(ROOT / "scripts" / "survey", root / "scripts" / "survey",
                    ignore=shutil.ignore_patterns("__pycache__"))
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    bridge = ["bash", str(root / "scripts" / "claude_researchteam_bridge.sh")]
    res = subprocess.run([*bridge, "survey-registry", "tidebell"], capture_output=True, text=True, env=env)
    assert res.returncode == 0 and f"wrote: {REGISTRY}" in res.stdout
    res = subprocess.run([*bridge, "survey-registry", "tidebell", "--candidates"], capture_output=True, text=True,
                         env=env)
    assert res.returncode == 0 and "candidates:" in res.stdout
    res = subprocess.run([*bridge, "survey-registry", "--root", str(tmp_path), "tidebell"], capture_output=True,
                         text=True, env=env)
    assert res.returncode == 2 and "--root is not accepted" in res.stderr
    assert not list((root / "scripts" / "survey").glob("__pycache__"))
