"""The study specification (contract section 3): shape, the checks beyond shape, files and coverage, the schema."""
import json
import os

import pytest

from survey_support import (
    FIXTURES, edit_spec, make_repo, rules, run, survey_schema as schema, survey_spec as sp, survey_validate,
)

VALID = sorted((FIXTURES / "specs" / "valid").glob("*.json"))
INVALID = sorted((FIXTURES / "specs" / "invalid").glob("*.json"))


def _shape(spec):
    out, paths = [], []
    sp.check_shape(sp.STUDY, spec, "", out, paths)
    return out


# --------------------------------------------------------------------------- the shared valid and invalid set
def test_the_shared_set_is_not_empty():
    assert len(VALID) >= 3 and len(INVALID) >= 25


@pytest.mark.parametrize("path", VALID, ids=lambda p: p.stem)
def test_shared_valid_specifications_pass_the_shape_checks(path):
    assert _shape(json.loads(path.read_text())) == []


@pytest.mark.parametrize("path", INVALID, ids=lambda p: p.stem)
def test_shared_invalid_specifications_fail_with_the_named_rule(path):
    expected = path.stem.split("--")[0]
    assert expected in rules(_shape(json.loads(path.read_text())))


@pytest.mark.parametrize("path", VALID + INVALID, ids=lambda p: p.stem)
def test_a_json_schema_library_gives_the_same_verdict(path):
    """Run only where a JSON Schema library is installed; researchteam's CI installs none (section 3)."""
    jsonschema = pytest.importorskip("jsonschema")
    validator = jsonschema.Draft202012Validator(schema.generate())
    ok = not list(validator.iter_errors(json.loads(path.read_text())))
    assert ok is (path in VALID)


# --------------------------------------------------------------------------- the published schema
def test_the_tracked_schema_is_the_generators_output():
    assert schema.SCHEMA_FILE.read_bytes() == schema.render()
    assert schema.main(["--check"]) == 0


def test_the_schema_generator_is_deterministic():
    assert schema.render() == schema.render()


def _fields(node, seen=None):
    """Every field name in the rule table."""
    seen = set() if seen is None else seen
    if isinstance(node, sp.Ref):
        if node.name not in seen:
            seen.add(node.name)
            yield from _fields(sp.DEFS[node.name], seen)
    elif isinstance(node, sp.Obj):
        for name, (sub, _req) in node.props.items():
            yield name
            yield from _fields(sub, seen)
    elif isinstance(node, sp.Arr):
        yield from _fields(node.items, seen)
    elif isinstance(node, sp.MapOf):
        yield from _fields(node.values, seen)
    elif isinstance(node, sp.AnyOf):
        for o in node.options:
            yield from _fields(o, seen)
    elif isinstance(node, sp.ByKind):
        for v in node.variants.values():
            yield from _fields(v, seen)


def _schema_props(s):
    if isinstance(s, dict):
        for k, v in s.items():
            if k == "properties":
                yield from v
            yield from _schema_props(v)
    elif isinstance(s, list):
        for v in s:
            yield from _schema_props(v)


def test_every_rule_table_field_appears_in_the_schema():
    generated = schema.generate()
    assert generated["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert set(_fields(sp.STUDY)) <= set(_schema_props(generated))
    for rid, _line, _desc in sp.SEMANTIC_RULES:
        assert rid in generated["description"]
    json.loads(schema.SCHEMA_FILE.read_text())  # well-formed


# --------------------------------------------------------------------------- the invented study
def _validate(root):
    return sp.load_study("tidebell", root)


def test_the_invented_example_study_is_valid(tmp_path):
    root = make_repo(tmp_path)
    assert run(survey_validate, "--root", str(root), "tidebell")[0] == 0
    assert _validate(root).findings == []


def _outcome(s, i=0):
    return s["outcomes"][i]


def _attr(s, key):
    return next(a for a in s["attributes"] if a["key"] == key)


def _set(path, value):
    def mutate(s):
        node = s
        for k in path[:-1]:
            node = node[k]
        node[path[-1]] = value
    return mutate


def _pop(path):
    def mutate(s):
        node = s
        for k in path[:-1]:
            node = node[k]
        del node[path[-1]]
    return mutate


def _seq(*fns):
    def mutate(s):
        for f in fns:
            f(s)
    return mutate


CO = ["outcomes", 0]
SEMANTIC_CASES = {
    "key-duplicate": _set(["attributes", 0, "key"], "slack_bell"),
    "level-duplicate": _set(CO + ["levels", 1, "code"], "against"),
    "max-order-scale": _set(CO + ["scale"], "nominal"),
    "max-order-order": _pop(CO + ["levels", 0, "order"]),
    "merge-source": _set(CO + ["merges"], {"unknown": "x"}),
    "cuts-order": _set(["periods", "cuts"], [1800, 1750]),
    "labels-count": _set(["periods", "labels"], ["a", "b"]),
    "strata-key": _set(["periods", "strata"], {"4": "past the last period"}),
    "codes-outcome-missing": lambda s: s.update(outcomes=[s["outcomes"][1]]),
    "counted-tiers-subset": _set(["evidence", "counted_tiers"], ["quoted", "hearsay"]),
    "ne-tier-undeclared": _set(["evidence", "not_established_tier"], "unknown"),
    "ne-tier-counted": _set(["evidence", "counted_tiers"], ["quoted", "not-established"]),
    "present-code-missing": _set(CO + ["rollup"], "any-present"),
    "present-code-level": _seq(_set(CO + ["rollup"], "any-present"), _set(CO + ["present_code"], "NA")),
    "present-code-unexpected": _set(CO + ["present_code"], "for"),
    "exclude-key": _set(["unit", "exclude_from_rollup"], {"tone": ["x"]}),
    "exclude-value": _set(["unit", "exclude_from_rollup"], {"genre": ["sermon"]}),
    "mixed-code": _set(CO + ["na_codes"], ["mixed"]),
    "any-present-order": _seq(_set(CO + ["rollup"], "any-present"), _set(CO + ["present_code"], "for"),
                              _pop(CO + ["levels", 1, "order"])),
    "rollup-types-key": _set(["unit", "rollup_types"], "tone"),
    "rollup-by-key": _set(["unit", "rollup_by"], ["tone"]),
    "period-multiple": lambda s: s["attributes"].append(
        {"key": "era2", "label": "Era 2", "kind": "period", "bucketer": {"kind": "period"}}),
    "period-bucketer": _set(["attributes", 0, "bucketer"], {"kind": "period"}),
    "frame-column-duplicate": _set(["attributes", 0, "key"], "unit_id"),
    "match-all": _set(["attributes", 0, "bucketer", "match"], "all"),
    "match-first-flags": _set(["attributes", 1, "bucketer", "match"], "first"),
    "fallback-flags": _set(["attributes", 1, "bucketer", "fallback"], "none"),
    "outcome-codes-distinct": _set(CO + ["missing"], "NA"),
    "attribute-missing": _set(["attributes", 0, "missing"], "north"),
    "rollup-by-pipe": _set(["unit", "passage_attributes", 0, "levels", 0, "code"], "log|book"),
    "exclude-rule-cells": lambda s: s["frame_rules"]["exclude"].append(
        {"rule": "unit-ids", "values": ["p-001"], "reason": "an invented exclusion"}),
    "attribution-missing": _pop(["unit", "attribution"]),
    "saturation-fields": _pop(["enumerations", 0, "stopping_rule", "min_new_share"]),
    "legacy-unrecorded-status": _set(["enumerations", 0, "stopping_rule"], {"kind": "legacy-unrecorded"}),
    "reader-missing": _set(["evidence", "format"], "plugin"),
    "reader-unexpected": _set(["evidence", "reader"], {"file": "rules/forbidden.txt", "attr": "R", "version": "1"}),
    "file-missing": _set(["evidence", "file"], "rows/absent.csv"),
    "not-covered-s0": _set(["signoffs", "gates", "S0", "covers"], ["rules/forbidden.txt", "plans/query_plan.md"]),
    "legacy-exceptions-status": _set(["evidence", "legacy_exceptions"], "rules/forbidden.txt"),
    "legacy-exceptions-uncovered": _seq(_set(["status"], "legacy"),
                                        _set(["evidence", "legacy_exceptions"], "rows/attribution.csv")),
    "post-step-uncovered": _set(["frame_rules", "post_steps"], ["rows/evidence.csv"]),
    "covers-empty": _set(["signoffs", "gates", "S5", "covers"], []),
    "covers-missing": _set(["signoffs", "gates", "S5", "covers"], ["codebooks/absent.md"]),
    "covers-not-file": _set(["signoffs", "gates", "S5", "covers"], ["codebooks"]),
}


def test_every_semantic_rule_has_a_case():
    assert set(SEMANTIC_CASES) == {rid for rid, _l, _d in sp.SEMANTIC_RULES}


@pytest.mark.parametrize("rule", sorted(SEMANTIC_CASES))
def test_each_check_beyond_shape_is_triggered(tmp_path, rule):
    root = make_repo(tmp_path, SEMANTIC_CASES[rule])
    study = _validate(root)
    assert rule in rules(study.findings), [f.line() for f in study.findings]
    code, out, _ = run(survey_validate, "--root", str(root), "tidebell")
    assert code == 1 and f"[{rule}]" in out


@pytest.mark.parametrize("column_case", [
    _set(["outcomes", 0, "key"], "era_num"),               # an outcome named like the period's <key>_num
    _set(["attributes", 0, "key"], "genre"),               # a key equal to a rollup_by key
    _set(["attributes", 0, "key"], "author"),
    _set(["attributes", 0, "key"], "unit_kind"),
    _seq(_set(["attributes", 0, "key"], "duties_lamp")),   # equal to a flag column <key>_<flag>
    _seq(_set(["attributes", 1, "missing"], "none"),        # equal to the flags' <key>_<missing> column
         _set(["attributes", 0, "key"], "duties_none")),
    _seq(_pop(["attributes", 2]), _set(["attributes", 0, "key"], "period")),  # no period attribute: 'period'
])
def test_frame_column_collisions_from_the_contract_examples(tmp_path, column_case):
    assert "frame-column-duplicate" in rules(_validate(make_repo(tmp_path, column_case)).findings)


def test_a_draft_may_name_files_that_do_not_exist_yet(tmp_path):
    root = make_repo(tmp_path, _seq(_set(["status"], "draft"), _set(["evidence", "file"], "rows/absent.csv"),
                                    _set(["signoffs", "gates", "S5", "covers"], ["codebooks/absent.md"])))
    assert _validate(root).findings == []


def test_files_that_a_stage_writes_may_be_absent(tmp_path):
    root = make_repo(tmp_path)  # registry, overrides, log, change_log, receipts and adjudications are not there
    for rel in ("rows/registry.csv", "rows/overrides.csv", "rows/enumeration-log.csv", "rows/frame-changes.jsonl",
                "rows/receipts", "rows/adjudications-slack_bell.csv"):
        assert not (root / "Projects" / "tidebell" / rel).exists()
    assert _validate(root).findings == []


def test_schema_version_0_is_read_like_1(tmp_path):
    assert _validate(make_repo(tmp_path, _set(["schema_version"], "0"))).findings == []


def test_coverage_is_judged_on_resolved_paths(tmp_path):
    root = make_repo(tmp_path, _set(["vocabulary", "forbidden"], "repo:Projects/tidebell/rules/forbidden.txt"))
    assert _validate(root).findings == []
    os.symlink("rules", root / "Projects" / "tidebell" / "alias")
    edit_spec(root, _set(["identity", "stop_words"], "alias/stop_words.txt"))
    assert _validate(root).findings == []  # the link resolves to a covered file


def test_paths_in_the_specification_follow_rule_1_6(tmp_path):
    for value, rule in (("/abs/evidence.csv", "path-absolute"), ("../evidence.csv", "path-dotdot")):
        assert rule in rules(_validate(make_repo(tmp_path / rule, _set(["evidence", "file"], value))).findings)


def test_a_draft_is_held_to_the_path_rule_too(tmp_path):
    root = make_repo(tmp_path, _seq(_set(["status"], "draft"), _set(["evidence", "file"], "../outside.csv")))
    assert "path-dotdot" in rules(_validate(root).findings)


def test_malformed_json_and_duplicate_keys_are_errors(tmp_path):
    root = make_repo(tmp_path)
    spec = root / "Projects" / "tidebell" / "study.json"
    spec.write_text('{"id": "a", "id": "b"}')
    assert rules(_validate(root).findings) == {"json-duplicate-key"}
    spec.write_text("{not json")
    assert rules(_validate(root).findings) == {"json"}
    assert run(survey_validate, "--root", str(root), "tidebell")[0] == 1


def test_shape_errors_stop_before_the_checks_beyond_shape(tmp_path):
    study = _validate(make_repo(tmp_path, _seq(_set(["colour"], "blue"), _set(["periods", "cuts"], [2, 1]))))
    assert rules(study.findings) == {"unknown-key"}
