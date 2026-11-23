"""The concept map: the exporter's checks, the DOT it writes, who each node ties to, and the template's fixed
properties (templates/concept-map/CONTRACT.md).

Most tests need neither Graphviz nor Node: membership is computed on a synthetic layout. The tests that run
Graphviz (the example's currency, determinism, fail-closed output) or Node (the component test) are skipped when
the program is missing, and say so.
"""
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "concept-map"
EXAMPLE = TEMPLATE / "example"
SCRIPT = ROOT / "scripts" / "build_concept_map.py"

sys.path.insert(0, str(ROOT / "scripts"))
import build_concept_map as cm  # noqa: E402

HAS_DOT = shutil.which("dot") is not None
HAS_NODE = shutil.which("node") is not None


def spec():
    return json.loads((EXAMPLE / "spec.json").read_text(encoding="utf-8"))


def errors(s, registry=None):
    return cm.check_spec(s, registry)[0]


def fake_geo(s):
    """A layout with every node and edge present, so build_map runs without Graphviz."""
    nodes = {n["id"]: {"x": 10.0 * i, "y": 5.0, "w": 40.0, "h": 20.0} for i, n in enumerate(s["nodes"])}
    edges = {f"e{i}": {"path": [[0, 0], [1, 1], [2, 2], [3, 3]], "tip": [4, 4]} for i in range(len(s["edges"]))}
    return {"width": 100.0, "height": 50.0, "nodes": nodes, "bands": {}, "edges": edges}


def build(s, registry=None):
    return cm.build_map(s, registry, fake_geo(s), [{"name": "spec.json", "sha256": "0" * 64}], "test")


def node(data, nid):
    return next(n for n in data["nodes"] if n["id"] == nid)


# --------------------------------------------------------------------------- checks
def test_the_example_is_clean_apart_from_its_declared_warnings():
    errs, warns = cm.check_spec(spec(), None)
    assert errs == []
    assert any("Unsigned pamphlet" in w for w in warns)
    assert any(w.startswith("REVIEW edge F_date -> chron") for w in warns)


def _mut(path, value):
    def f(s):
        obj = s
        for k in path[:-1]:
            obj = obj[k]
        if value is KeyError:
            del obj[path[-1]]
        else:
            obj[path[-1]] = value
    return f


BAD = {
    "unknown top-level key": (_mut(["extra"], 1), "unknown key"),
    "wrong schema": (_mut(["schema"], "x"), "spec.schema"),
    "other major version": (_mut(["schema_version"], "2.0"), "major version"),
    "malformed node id": (_mut(["nodes", 0, "id"], "-bad"), "does not match"),
    "duplicate node id": (_mut(["nodes", 1, "id"], "ada"), "duplicated"),
    "node id equals a band id": (_mut(["nodes", 0, "id"], "b1"), "also a band id"),
    "unknown kind": (_mut(["nodes", 0, "kind"], "nope"), "not a node_kinds id"),
    "unknown band": (_mut(["nodes", 0, "band"], "b9"), "not a bands id"),
    "missing band": (_mut(["nodes", 0, "band"], KeyError), "required when the spec has bands"),
    "actor without persons": (_mut(["nodes", 0, "persons"], KeyError), "must list its persons"),
    "topic with persons": (_mut(["nodes", 2, "persons"], [{"id": "x", "name": "X"}]), "only actor nodes"),
    "person with id and unregistered": (_mut(["nodes", 0, "persons"], [{"id": "a", "name": "A", "unregistered": "r"}]), "not both"),
    "person without id needs a reason": (_mut(["nodes", 0, "persons"], [{"name": "A"}]), "unregistered: required"),
    "id without name and no registry": (_mut(["nodes", 0, "persons"], [{"id": "a"}]), "name is required"),
    "bad colour": (_mut(["vocab", "fills", 0, "color"], "red"), "#rrggbb"),
    "bad stroke": (_mut(["vocab", "relations", 0, "stroke"], "green"), "stroke"),
    "bad head": (_mut(["vocab", "relations", 1, "head"], "diamond"), "head"),
    "unknown relation": (_mut(["edges", 0, "relation"], "likes"), "not a relations id"),
    "dangling edge": (_mut(["edges", 0, "to"], "nowhere"), "not a node id"),
    "self edge": (_mut(["edges", 0, "to"], "ada"), "to itself"),
    "only names a stranger": (_mut(["edges", 5, "only"], ["dov-pell"]), "is not a person of node"),
    "only names everyone": (_mut(["edges", 5, "only"], ["esk-ruan", "fia-lund"]), "leave it out"),
    "only on a topic-topic edge": (_mut(["edges", 7, "only"], ["x"]), "exactly one actor end"),
    "all_members with only": (_mut(["edges", 5, "all_members"], True), "all_members"),
    "all_members not true": (_mut(["edges", 1, "all_members"], False), "all_members"),
}


@pytest.mark.parametrize("name", sorted(BAD))
def test_each_violation_is_an_error(name):
    s = spec()
    change, message = BAD[name]
    change(s)
    errs = errors(s)
    assert any(message in e for e in errs), errs


def test_duplicate_edge_is_an_error():
    s = spec()
    s["edges"].append(copy.deepcopy(s["edges"][0]))
    assert any("given twice" in e for e in errors(s))


def test_registry_ids_are_checked_and_names_taken_from_it():
    s = spec()
    reg = {p["id"]: p["name"].upper() for n in s["nodes"] for p in n.get("persons", []) if "id" in p}
    errs, warns = cm.check_spec(s, reg)
    assert errs == []
    # with a registry, the register's name is used, and a different name in the spec is reported
    assert node(build(s, reg), "ada")["persons"][0]["name"] == "ADA FENWRIGHT"
    assert any("'ada-fenwright' is named 'Ada Fenwright' in the spec" in w for w in warns)
    del s["nodes"][0]["persons"][0]["name"]
    assert node(build(s, reg), "ada")["persons"][0]["name"] == "ADA FENWRIGHT"
    reg.pop("dov-pell")
    assert any("not in the registry" in e for e in errors(s, reg))


def test_an_id_may_not_use_the_unregistered_prefix():
    s = spec()
    s["nodes"][0]["persons"] = [{"id": "name:ada", "name": "Ada"}]
    assert any("may not start with 'name:'" in e for e in errors(s))


def test_a_node_may_be_called_legend():
    s = spec()
    s["nodes"][0]["id"] = "legend"
    for e in s["edges"]:
        for end in ("from", "to"):
            if e[end] == "ada":
                e[end] = "legend"
    assert errors(s) == []
    assert '"legend" [id="legend"' in cm.to_dot(s) and '"__legend" [shape=plaintext' in cm.to_dot(s)


@pytest.mark.parametrize("change", [
    lambda s: s["nodes"][0].__setitem__("kind", ["actor"]),
    lambda s: s["edges"][0].__setitem__("from", ["ada"]),
    lambda s: s["nodes"][1].__setitem__("persons", 5),
    lambda s: s["layout"].__setitem__("fontname", 5),
    lambda s: s["edges"].append("not an edge"),
])
def test_malformed_values_fail_closed_without_a_traceback(tmp_path, change):
    s = spec()
    change(s)
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(s), encoding="utf-8")
    out = tmp_path / "map.json"
    out.write_text("stale", encoding="utf-8")
    report = tmp_path / "r.txt"
    assert cm.main([str(p), "--out", str(out), "--report", str(report), "--dot-bin", str(tmp_path / "no-dot")]) == 1
    assert not out.exists()
    assert "nothing written" in report.read_text(encoding="utf-8")


def test_a_registry_without_a_persons_list_is_an_error(tmp_path):
    reg = tmp_path / "reg.json"
    reg.write_text(json.dumps({"schema": "researchteam.bibliography-explorer", "persons": {"a": 1}}), encoding="utf-8")
    out = tmp_path / "map.json"
    assert cm.main([str(EXAMPLE / "spec.json"), "--out", str(out), "--registry", str(reg)]) == 1
    assert not out.exists()


def test_a_group_edge_is_listed_for_review_until_it_says_who():
    s = spec()
    _, warns = cm.check_spec(s, None)
    assert any("REVIEW edge F_date -> chron" in w for w in warns)
    s["edges"][8]["all_members"] = True
    _, warns = cm.check_spec(s, None)
    assert not any(w.startswith("REVIEW") for w in warns)


# --------------------------------------------------------------------------- members
def test_members_are_computed_from_the_edges_with_direction():
    data = build(spec())
    guild = node(data, "C_guild")["members"]
    assert [(m["person"]["name"], m["relation"], m["active"]) for m in guild] == [
        ("Ada Fenwright", "affirms", True), ("Bram Oakes", "affirms", True), ("Cel Varro", "affirms", True),
        ("Dov Pell", "denies", True)]
    date = {(m["person"]["name"], m["relation"], m["active"]) for m in node(data, "F_date")["members"]}
    # F_date -| chron: the chroniclers are rebutted BY the finding, not denying it
    assert ("Bram Oakes", "denies", False) in date and ("Cel Varro", "denies", False) in date


def test_only_limits_a_group_edge_to_the_persons_it_names():
    late = node(build(spec()), "C_late")["members"]
    names = [m["person"]["name"] for m in late if m["relation"] == "affirms"]
    assert names == ["Dov Pell", "Fia Lund"]      # Esk Ruan is in the box but the edge says Lund only


def test_members_cannot_be_supplied_and_actor_nodes_have_none():
    s = spec()
    s["nodes"][2]["members"] = []
    assert any("unknown key" in e for e in errors(s))
    assert "members" not in node(build(spec()), "ada")


def test_a_person_in_two_boxes_appears_once_per_relation_with_both_ways_in():
    s = spec()
    s["nodes"][3]["persons"].append({"id": "ada-fenwright", "name": "Ada Fenwright"})   # Ada also in Dov's box
    guild = node(build(s), "C_guild")["members"]
    ada = [m for m in guild if m["person"]["key"] == "id:ada-fenwright"]
    assert sorted(m["relation"] for m in ada) == ["affirms", "denies"]
    assert all(len(m["via"]) == 1 for m in ada)


def test_edges_between_topics_or_between_actors_are_ties_not_members():
    data = build(spec())
    late = node(data, "C_late")
    assert any(t["node"] == "F_date" and t["outgoing"] for t in late["related"])
    assert all(m["person"]["key"] != "id:ada-fenwright" for m in node(data, "F_date")["members"])
    assert any(t["node"] == "chron" and t["outgoing"] for t in node(data, "ada")["related"])


# --------------------------------------------------------------------------- DOT
def test_dot_is_deterministic_and_carries_ids():
    a, b = cm.to_dot(spec()), cm.to_dot(spec())
    assert a == b
    assert 'id="e0"' in a and '"ada" [id="ada"' in a
    assert "rank=same" in a and '"__legend" [' in a


def test_dot_escapes_quotes_backslashes_and_markup():
    s = spec()
    s["nodes"][0]["label"] = 'He said "no" \\ <b>bold</b>'
    s["vocab"]["fills"][0]["label"] = "<script>"
    d = cm.to_dot(s)
    assert '"He said \\"no\\" \\\\ <b>bold</b>"' in d       # a plain DOT string: markup is not interpreted
    assert "&lt;script&gt;" in d and "<script>" not in d     # the legend is an HTML-like label: escaped


# --------------------------------------------------------------------------- with Graphviz
@pytest.mark.skipif(not HAS_DOT, reason="Graphviz (dot) is not installed")
def test_the_example_files_are_current(tmp_path):
    out = tmp_path / "map-data.json"
    assert cm.main([str(EXAMPLE / "spec.json"), "--out", str(out), "--dot", str(tmp_path / "map.dot")]) == 0
    assert (tmp_path / "map.dot").read_text(encoding="utf-8") == (EXAMPLE / "map.dot").read_text(encoding="utf-8")
    new = json.loads(out.read_text(encoding="utf-8"))
    old = json.loads((EXAMPLE / "map-data.json").read_text(encoding="utf-8"))
    if new["meta"]["layout_engine"] != old["meta"]["layout_engine"]:
        pytest.skip(f"layout made with {old['meta']['layout_engine']}, this machine has {new['meta']['layout_engine']}")
    assert out.read_bytes() == (EXAMPLE / "map-data.json").read_bytes()


@pytest.mark.skipif(not HAS_DOT, reason="Graphviz (dot) is not installed")
def test_builds_are_byte_identical(tmp_path):
    for name in ("a", "b"):
        assert cm.main([str(EXAMPLE / "spec.json"), "--out", str(tmp_path / f"{name}.json")]) == 0
    assert (tmp_path / "a.json").read_bytes() == (tmp_path / "b.json").read_bytes()


@pytest.mark.skipif(not HAS_DOT, reason="Graphviz (dot) is not installed")
def test_a_failed_build_writes_nothing_and_removes_old_outputs(tmp_path):
    out, dot = tmp_path / "map.json", tmp_path / "map.dot"
    assert cm.main([str(EXAMPLE / "spec.json"), "--out", str(out), "--dot", str(dot)]) == 0
    bad = spec()
    bad["edges"][0]["relation"] = "likes"
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    assert cm.main([str(p), "--out", str(out), "--dot", str(dot), "--report", str(tmp_path / "r.txt")]) == 1
    assert not out.exists() and not dot.exists()
    assert "nothing written" in (tmp_path / "r.txt").read_text(encoding="utf-8")


def test_a_missing_graphviz_is_an_error_not_a_crash(tmp_path):
    out = tmp_path / "map.json"
    rc = cm.main([str(EXAMPLE / "spec.json"), "--out", str(out), "--dot-bin", str(tmp_path / "no-such-dot")])
    assert rc == 1 and not out.exists()


# --------------------------------------------------------------------------- the component
def test_the_component_never_parses_markup_or_loads_anything():
    js = (TEMPLATE / "concept-map.js").read_text(encoding="utf-8")
    code = re.sub(r"//.*", "", js)
    for banned in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function",
                   "fetch(", "XMLHttpRequest", "localStorage", "sessionStorage", "location", "import("):
        assert banned not in code, banned


def test_the_stylesheet_is_scoped():
    css = (TEMPLATE / "concept-map.css").read_text(encoding="utf-8")
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    selectors = [s.strip() for block in re.findall(r"([^{}]+)\{", css) for s in block.split(",")]
    for s in selectors:
        if s.startswith("@"):
            continue
        assert s.startswith(".cmap"), s


@pytest.mark.skipif(not HAS_NODE, reason="Node is not installed")
def test_the_component_test_passes_in_node():
    r = subprocess.run(["node", str(TEMPLATE / "tests" / "component.test.mjs")], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr


def test_the_hash_list_is_current():
    lines = (TEMPLATE / "FILES.sha256").read_text(encoding="utf-8").splitlines()
    assert lines
    for line in lines:
        digest, rel = line.split("  ", 1)
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest, rel
