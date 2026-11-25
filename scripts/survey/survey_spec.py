"""The study specification (``study.json``, contract section 3): its rule table, loader and validator.

The rule table (:data:`STUDY`, :data:`DEFS`) is the single source of the specification's shape. The validator
walks it, and ``survey_schema.py`` generates the published JSON Schema from it, so the two cannot drift. The checks
beyond shape (section 3, "Checks beyond shape") are listed in :data:`SEMANTIC_RULES` with their ids; a JSON Schema
cannot express them, so the generated schema names them in its description only.

Error ids are the toolkit's own: section 3 gives none. They are stable, and the check table
(references/plans/post-1.3.0-h5-step-a-check-table.md) maps each to its contract line.
"""
from __future__ import annotations

import os
import re
import stat
from dataclasses import dataclass, field
from pathlib import Path

from survey_core import (
    GATES, MAX_JSON_BYTES, Finding, SurveyUsageError, inside, load_json_strict, read_capped, reason, resolve_path,
)

SLUG = "^[a-z0-9][a-z0-9_-]*$"
PLUGIN_ATTR = "^[A-Za-z_][A-Za-z0-9_]*$"
PERIOD_NUMBER = "^[1-9][0-9]*$"
MIXED = "mixed"  # the reserved output code (4.2)
DEFAULT_MISSING = "NE"


# --------------------------------------------------------------------------- the shape DSL
class Node:
    """A node of the rule table."""


@dataclass
class Str(Node):
    min_len: int = 0
    pattern: str | None = None
    enum: tuple | None = None
    is_path: bool = False


@dataclass
class Int(Node):
    minimum: int | None = None


@dataclass
class Num(Node):
    minimum: float | None = None
    maximum: float | None = None


@dataclass
class Null(Node):
    pass


@dataclass
class AnyObject(Node):
    """An object whose shape the toolkit does not own (``analysis``)."""


@dataclass
class Arr(Node):
    items: Node
    min_items: int = 0


@dataclass
class Cond:
    """When ``field`` equals ``equals`` the fields ``then_required`` are required; otherwise ``else_forbidden``
    are not allowed. ``rule_required`` and ``rule_forbidden`` are the error ids."""

    field: str
    equals: str
    then_required: tuple
    rule_required: str
    else_forbidden: tuple = ()
    rule_forbidden: str = ""


@dataclass
class Obj(Node):
    props: dict  # name -> (Node, required: bool)
    conds: tuple = ()


@dataclass
class MapOf(Node):
    values: Node
    key_enum: tuple | None = None


@dataclass
class AnyOf(Node):
    options: tuple


@dataclass
class ByKind(Node):
    """One of several objects told apart by their ``kind`` field. Each object carries only its own fields."""

    variants: dict  # kind -> Obj (each with a "kind" prop)


@dataclass
class Ref(Node):
    name: str


def PathStr() -> Str:  # noqa: N802 - a constructor of the DSL
    return Str(min_len=1, is_path=True)


def R(node, required=True):  # noqa: N802
    return (node, required)


def O(node):  # noqa: N802 - optional field
    return (node, False)


STR = Str()
STRS = Arr(Str())
NONEMPTY = Str(min_len=1)

DEFS = {
    "Level": Obj({"code": R(STR), "label": R(STR), "order": O(Int())}),
    "LevelSet": Obj({"key": R(Str(pattern=SLUG)), "label": R(STR), "levels": R(Arr(Ref("Level"), 1))}),
    "Plugin": Obj({"file": R(PathStr()), "attr": R(Str(pattern=PLUGIN_ATTR)), "version": R(NONEMPTY)}),
    "Bucketer": ByKind({
        "table": Obj({"kind": R(Str(enum=("table",))), "table": R(PathStr()),
                      "match": O(Str(enum=("first", "all"))), "fallback": O(STR)}),
        "period": Obj({"kind": R(Str(enum=("period",)))}),
        "plugin": Obj({"kind": R(Str(enum=("plugin",))), "plugin": R(Ref("Plugin")), "fallback": O(STR)}),
    }),
    "Gate": Obj({"covers": R(Arr(PathStr())), "enforce": R(Str(enum=("blocking", "build-only"))),
                 "mode": R(Str(enum=("prospective", "retroactive")))}),
}

STUDY = Obj({
    "schema_version": R(Str(enum=("1", "0"))),
    "id": R(Str(pattern=SLUG)),
    "title": R(NONEMPTY),
    "question": R(NONEMPTY),
    "status": R(Str(enum=("draft", "active", "legacy"))),
    "vantage": O(Obj({"module": R(AnyOf((Ref("Plugin"), Null()))), "guide": O(PathStr()),
                      "inclusion": O(AnyOf((STR, Null())))})),
    "vocabulary": O(Obj({"forbidden": R(PathStr()), "exempt_columns": O(STRS)})),
    "corpus": O(Obj({"text": R(PathStr()), "works": O(PathStr())})),
    "identity": R(Obj({"registry": R(PathStr()), "overrides": R(PathStr()), "stop_words": O(PathStr())})),
    "unit": R(Obj({
        "kind": R(Str(enum=("passage", "work", "author"))),
        "attribution": O(Obj({"file": R(PathStr()), "statuses": R(STRS), "counted_statuses": R(STRS)})),
        "passage_attributes": O(Arr(Ref("LevelSet"))),
        "rollup_by": O(STRS),
        "rollup_types": O(STR),
        "exclude_from_rollup": O(MapOf(Arr(STR, 1))),
        "collective": O(Obj({"kinds": R(STRS), "analysis": R(Str(enum=("apart", "with-authors")))})),
    })),
    "enumerations": R(Arr(Obj({
        "id": R(Str(pattern=SLUG)), "label": R(STR),
        "window": R(Obj({"from": R(AnyOf((Int(), Null()))), "to": R(AnyOf((Int(), Null())))})),
        "seeds": O(STRS), "query_plan": O(PathStr()), "log": R(PathStr()),
        "stopping_rule": R(Obj({
            "kind": R(Str(enum=("saturation", "exhaustive-corpus", "closed-list", "legacy-unrecorded"))),
            "rounds_without_new": O(Int(minimum=1)),
            "min_new_share": O(Num(minimum=0, maximum=1)),
            "note": O(STR),
        }, conds=(Cond("kind", "saturation", ("rounds_without_new", "min_new_share"), "saturation-fields"),))),
    }), 1)),
    "evidence": R(Obj({
        "file": R(PathStr()),
        "format": R(Str(enum=("survey-evidence-0", "plugin"))),
        "reader": O(Ref("Plugin")),
        "tiers": R(STRS),
        "counted_tiers": R(STRS),
        "not_established_tier": R(STR),
        "receipts": O(PathStr()),
        "legacy_exceptions": O(PathStr()),
        "attribute_kinds": O(STRS),
    }, conds=(Cond("format", "plugin", ("reader",), "reader-missing", ("reader",), "reader-unexpected"),))),
    "outcomes": R(Arr(Obj({
        "key": R(Str(pattern=SLUG)), "label": R(STR),
        "source": R(ByKind({
            "evidence-attribute": Obj({"kind": R(Str(enum=("evidence-attribute",))), "attribute": R(STR)}),
            "codes": Obj({"kind": R(Str(enum=("codes",))), "codes_file": R(PathStr()),
                          "adjudications": R(PathStr())}),
        })),
        "codebook": O(PathStr()),
        "scale": R(Str(enum=("nominal", "ordinal"))),
        "levels": R(Arr(Ref("Level"), 2)),
        "na_codes": O(STRS),
        "missing": O(STR),
        "merges": O(MapOf(STR)),
        "rollup": R(Str(enum=("single-code", "mixed-if-conflict", "max-order", "any-present", "none"))),
        "present_code": O(STR),
    }, conds=(Cond("rollup", "any-present", ("present_code",), "present-code-missing",
                   ("present_code",), "present-code-unexpected"),)), 1)),
    "attributes": R(Arr(Obj({
        "key": R(Str(pattern=SLUG)), "label": R(STR),
        "kind": R(Str(enum=("categorical", "flags", "period"))),
        "source_attributes": O(STRS),
        "bucketer": R(Ref("Bucketer")),
        "levels": O(STRS), "flags": O(STRS),
        "missing": O(STR),
    }), 1)),
    "periods": R(Obj({
        "basis": R(Arr(Str(enum=("work_date", "life_dates")))),
        "cuts": R(Arr(Int(), 1)),
        "labels": R(Arr(STR, 2)),
        "strata": O(MapOf(STR)),
    })),
    "frame_rules": R(Obj({
        "exclude": R(Arr(Obj({
            "rule": R(Str(enum=("institutions", "not-on-question", "unit-ids", "id-contains"))),
            "values": O(STRS), "reason": R(STR),
        }))),
        "change_log": R(PathStr()),
        "post_steps": O(Arr(PathStr())),
    })),
    "analysis": O(AnyObject()),
    "signoffs": R(Obj({
        "ledger": R(STR),
        "gates": R(MapOf(Ref("Gate"), key_enum=GATES)),
    })),
})


# --------------------------------------------------------------------------- the shape walker
def _ptr(base: str, key) -> str:
    return f"{base}/{str(key).replace('~', '~0').replace('/', '~1')}"


def _type_name(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _fullmatch(pattern: str, value: str) -> bool:
    """A table pattern is anchored with ^ and $ for the schema; the validator matches the whole string, so that a
    trailing line feed cannot pass as Python's ``$`` would let it."""
    assert pattern.startswith("^") and pattern.endswith("$") and not pattern.endswith("\\$"), pattern
    return re.fullmatch(pattern[1:-1], value) is not None


def check_shape(node: Node, value, where: str, out: list, paths: list) -> None:
    """Check *value* against *node*; append findings to *out* and (pointer, declared) of every path to *paths*."""
    if isinstance(node, Ref):
        return check_shape(DEFS[node.name], value, where, out, paths)
    if isinstance(node, Str):
        if not isinstance(value, str):
            out.append(Finding("type", where, f"expected a string, found {_type_name(value)}"))
            return
        if node.enum is not None and value not in node.enum:
            out.append(Finding("enum", where, f"{value!r} is not one of {', '.join(map(repr, node.enum))}"))
        if len(value) < node.min_len:
            out.append(Finding("empty", where, "must not be empty"))
        if node.pattern and not _fullmatch(node.pattern, value):
            out.append(Finding("pattern", where, f"{value!r} does not match {node.pattern}"))
        if node.is_path and value:
            paths.append((where, value))
        return
    if isinstance(node, Int):
        if isinstance(value, bool) or not isinstance(value, int):
            out.append(Finding("type", where, f"expected an integer, found {_type_name(value)}"))
            return
        if node.minimum is not None and value < node.minimum:
            out.append(Finding("minimum", where, f"{value} is less than {node.minimum}"))
        return
    if isinstance(node, Num):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            out.append(Finding("type", where, f"expected a number, found {_type_name(value)}"))
            return
        if node.minimum is not None and value < node.minimum:
            out.append(Finding("minimum", where, f"{value} is less than {node.minimum}"))
        if node.maximum is not None and value > node.maximum:
            out.append(Finding("maximum", where, f"{value} is greater than {node.maximum}"))
        return
    if isinstance(node, Null):
        if value is not None:
            out.append(Finding("type", where, f"expected null, found {_type_name(value)}"))
        return
    if isinstance(node, AnyObject):
        if not isinstance(value, dict):
            out.append(Finding("type", where, f"expected an object, found {_type_name(value)}"))
        return
    if isinstance(node, Arr):
        if not isinstance(value, list):
            out.append(Finding("type", where, f"expected an array, found {_type_name(value)}"))
            return
        if len(value) < node.min_items:
            out.append(Finding("min-items", where, f"needs at least {node.min_items} item(s), has {len(value)}"))
        for i, item in enumerate(value):
            check_shape(node.items, item, _ptr(where, i), out, paths)
        return
    if isinstance(node, MapOf):
        if not isinstance(value, dict):
            out.append(Finding("type", where, f"expected an object, found {_type_name(value)}"))
            return
        for key in value:
            if node.key_enum is not None and key not in node.key_enum:
                out.append(Finding("unknown-key", _ptr(where, key),
                                   f"{key!r} is not one of {', '.join(node.key_enum)}"))
                continue
            check_shape(node.values, value[key], _ptr(where, key), out, paths)
        return
    if isinstance(node, AnyOf):
        trials = []
        for option in node.options:
            sub, sub_paths = [], []
            check_shape(option, value, where, sub, sub_paths)
            if not sub:
                paths.extend(sub_paths)
                return
            trials.append(sub)
        # Report the option whose own checks got furthest: the one with the fewest type errors at this place.
        best = min(trials, key=lambda s: (sum(1 for f in s if f.where == where and f.rule == "type"), len(s)))
        if all(any(f.where == where and f.rule == "type" for f in s) for s in trials):
            kinds = [_describe(o) for o in node.options]
            out.append(Finding("type", where, f"expected {' or '.join(kinds)}, found {_type_name(value)}"))
        else:
            out.extend(best)
        return
    if isinstance(node, ByKind):
        if not isinstance(value, dict):
            out.append(Finding("type", where, f"expected an object, found {_type_name(value)}"))
            return
        kind = value.get("kind")
        if "kind" not in value:
            out.append(Finding("required", _ptr(where, "kind"), "required field is missing"))
            return
        if kind not in node.variants:
            out.append(Finding("enum", _ptr(where, "kind"),
                               f"{kind!r} is not one of {', '.join(map(repr, node.variants))}"))
            return
        return check_shape(node.variants[kind], value, where, out, paths)
    if isinstance(node, Obj):
        if not isinstance(value, dict):
            out.append(Finding("type", where, f"expected an object, found {_type_name(value)}"))
            return
        for key in value:
            if key not in node.props:
                out.append(Finding("unknown-key", _ptr(where, key), f"{key!r} is not a field here"))
        for key, (sub, required) in node.props.items():
            if key in value:
                check_shape(sub, value[key], _ptr(where, key), out, paths)
            elif required:
                out.append(Finding("required", _ptr(where, key), "required field is missing"))
        for cond in node.conds:
            if value.get(cond.field) == cond.equals:
                for name in cond.then_required:
                    if name not in value:
                        out.append(Finding(cond.rule_required, _ptr(where, name),
                                           f"required when {cond.field} is {cond.equals!r}"))
            else:
                for name in cond.else_forbidden:
                    if name in value:
                        out.append(Finding(cond.rule_forbidden, _ptr(where, name),
                                           f"allowed only when {cond.field} is {cond.equals!r}"))
        return
    raise TypeError(f"unknown rule-table node {node!r}")


def _describe(node: Node) -> str:
    if isinstance(node, Ref):
        return node.name
    return {Str: "a string", Int: "an integer", Num: "a number", Null: "null",
            Arr: "an array"}.get(type(node), "an object")


# --------------------------------------------------------------------------- checks beyond shape
#: Every check beyond shape that step A makes: (id, contract line, what it checks). The check functions below
#: emit these ids; a test asserts that each id here is emitted by some fixture.
SEMANTIC_RULES = (
    ("key-duplicate", 188, "a key used twice among the outcomes and attributes together"),
    ("level-duplicate", 188, "a level code used twice within an outcome"),
    ("max-order-scale", 189, "rollup max-order without scale ordinal"),
    ("max-order-order", 189, "rollup max-order with a level that has no order"),
    ("merge-source", 190, "a merge whose source is not a declared level code or NA code"),
    ("cuts-order", 191, "cuts not strictly ascending"),
    ("labels-count", 191, "labels not one longer than cuts"),
    ("strata-key", 191, "a strata key that is not a period number from 1 to the number of labels"),
    ("codes-outcome-missing", 193, "a passage or work study with no outcome whose source is codes"),
    ("counted-tiers-subset", 194, "counted_tiers not a subset of tiers"),
    ("ne-tier-undeclared", 194, "not_established_tier not in tiers"),
    ("ne-tier-counted", 194, "not_established_tier counted"),
    ("present-code-missing", 195, "rollup any-present without a present_code"),
    ("present-code-level", 195, "a present_code that is not a level code of the outcome"),
    ("present-code-unexpected", 196, "a present_code on a rollup other than any-present"),
    ("exclude-key", 197, "an exclude_from_rollup key that is not a passage_attributes key"),
    ("exclude-value", 197, "an exclude_from_rollup value that is not one of that key's level codes"),
    ("mixed-code", 198, "a level, NA or missing code equal to the reserved code mixed"),
    ("any-present-order", 199, "rollup any-present on an ordinal outcome with a level that has no order"),
    ("rollup-types-key", 200, "a rollup_types that is not a passage_attributes key"),
    ("rollup-by-key", 200, "a rollup_by entry that is not a passage_attributes key"),
    ("period-multiple", 201, "more than one attribute of kind period"),
    ("period-bucketer", 201, "a period attribute whose bucketer is not of kind period, or the reverse"),
    ("frame-column-duplicate", 203, "two frame columns with the same name (4.7)"),
    ("match-all", 207, "match all on the bucketer of an attribute that is not of kind flags"),
    ("match-first-flags", 207, "match first on the bucketer of a flags attribute"),
    ("fallback-flags", 208, "a fallback on the bucketer of a flags attribute"),
    ("match-missing-flags", 690, "a flags attribute's table bucketer without match (the default is first; "
                                 "contract silent, refused)"),
    ("outcome-codes-distinct", 209, "an outcome's level codes, NA codes and missing value not all different"),
    ("attribute-missing", 210, "an attribute whose missing value is one of its levels or flags"),
    ("rollup-by-pipe", 211, "a | in a level code of a rollup_by level set"),
    ("exclude-rule-cells", 212, "a passage or work study with an exclude rule other than not-on-question"),
    ("attribution-missing", 214, "a passage or work study without unit.attribution"),
    ("saturation-fields", 215, "a saturation stopping rule without rounds_without_new and min_new_share"),
    ("legacy-unrecorded-status", 216, "a legacy-unrecorded stopping rule in a study that is not legacy"),
    ("reader-missing", 122, "evidence.format plugin without evidence.reader"),
    ("reader-unexpected", 122, "evidence.reader when evidence.format is not plugin (contract silent; refused)"),
    ("file-missing", 217, "a referenced input file that does not exist, unless status is draft"),
    ("not-covered-s0", 220, "a plug-in, bucket table, vocabulary file or stop-words file not covered by gate S0"),
    ("legacy-exceptions-status", 224, "evidence.legacy_exceptions in a study that is not legacy"),
    ("legacy-exceptions-uncovered", 224, "evidence.legacy_exceptions naming a file that no gate covers"),
    ("post-step-uncovered", 226, "a post_steps file that no gate covers"),
    ("covers-empty", 227, "a gate that covers no file"),
    ("covers-missing", 227, "a covers path that does not exist, unless status is draft"),
    ("covers-not-file", 803, "a covers path that is not a regular file (cannot be hashed; contract silent)"),
)

#: Paths that may be absent because a stage writes them or they start empty (section 3, line 218).
MAY_BE_ABSENT = (
    re.compile(r"^/enumerations/\d+/log$"),
    re.compile(r"^/frame_rules/change_log$"),
    re.compile(r"^/identity/registry$"),
    re.compile(r"^/identity/overrides$"),
    re.compile(r"^/evidence/receipts$"),
    re.compile(r"^/outcomes/\d+/source/adjudications$"),
)
_COVERS = re.compile(r"^/signoffs/gates/(%s)/covers/\d+$" % "|".join(map(re.escape, GATES)))
#: The files that gate S0 must cover (section 3, line 220; 5.1, 5.3).
MUST_BE_S0 = (
    re.compile(r"^/evidence/reader/file$"),
    re.compile(r"^/attributes/\d+/bucketer/plugin/file$"),
    re.compile(r"^/vantage/module/file$"),
    re.compile(r"^/attributes/\d+/bucketer/table$"),
    re.compile(r"^/vocabulary/forbidden$"),
    re.compile(r"^/identity/stop_words$"),
)


def _outcome_codes(o: dict):
    levels = [lv["code"] for lv in o["levels"]]
    return levels, list(o.get("na_codes", [])), o.get("missing", DEFAULT_MISSING)


def frame_columns(spec: dict) -> list[str]:
    """The frame's columns (4.7), generated from the keys, in order."""
    unit = spec["unit"]
    cols = ["unit_id", "author", *unit.get("rollup_by", []), "unit_kind"]
    period = [a for a in spec["attributes"] if a["kind"] == "period"]
    pkey = period[0]["key"] if period else "period"
    cols += [pkey, f"{pkey}_num"]
    for a in spec["attributes"]:
        if a["kind"] == "categorical":
            cols.append(a["key"])
        elif a["kind"] == "flags":
            cols += [f"{a['key']}_{flag}" for flag in a.get("flags", [])]
            cols.append(f"{a['key']}_{a.get('missing', DEFAULT_MISSING)}")
    for o in spec["outcomes"]:
        if o["source"]["kind"] == "codes" and o["rollup"] != "none":
            cols.append(o["key"])
    return cols


def check_semantics(spec: dict) -> list[Finding]:
    """The checks of section 3 that need no file system, on a specification whose shape is valid."""
    out: list[Finding] = []
    add = lambda rule, where, msg: out.append(Finding(rule, where, msg))  # noqa: E731
    unit, evidence = spec["unit"], spec["evidence"]
    passage_study = unit["kind"] in ("passage", "work")
    pattrs = {ls["key"]: ls for ls in unit.get("passage_attributes", [])}

    seen: dict = {}
    for kind in ("outcomes", "attributes"):
        for i, item in enumerate(spec[kind]):
            if item["key"] in seen:
                add("key-duplicate", f"/{kind}/{i}/key", f"{item['key']!r} is also the key of {seen[item['key']]}")
            else:
                seen[item["key"]] = f"/{kind}/{i}"

    for i, o in enumerate(spec["outcomes"]):
        at = f"/outcomes/{i}"
        levels, na, missing = _outcome_codes(o)
        dup = sorted({c for c in levels if levels.count(c) > 1})
        for c in dup:
            add("level-duplicate", f"{at}/levels", f"level code {c!r} is used twice")
        everything = levels + na + [missing]
        clashes = sorted({c for c in everything if everything.count(c) > 1} - set(dup))
        for c in clashes:
            add("outcome-codes-distinct", at, f"{c!r} is used more than once among level codes, NA codes and missing")
        for c in sorted(set(everything)):
            if c == MIXED:
                add("mixed-code", at, f"{MIXED!r} is a reserved output code (4.2) and cannot be declared")
        no_order = [lv["code"] for lv in o["levels"] if "order" not in lv]
        if o["rollup"] == "max-order":
            if o["scale"] != "ordinal":
                add("max-order-scale", f"{at}/rollup", "max-order needs scale 'ordinal'")
            if no_order:
                add("max-order-order", f"{at}/levels", f"max-order needs an order on every level; none on {no_order}")
        if o["rollup"] == "any-present":
            if "present_code" in o and o["present_code"] not in levels:
                add("present-code-level", f"{at}/present_code", f"{o['present_code']!r} is not a level code")
            if o["scale"] == "ordinal" and no_order:
                add("any-present-order", f"{at}/levels",
                    f"any-present on an ordinal outcome needs an order on every level; none on {no_order}")
        for src in o.get("merges", {}):
            if src not in levels and src not in na:
                add("merge-source", f"{at}/merges", f"merge source {src!r} is not a level code or NA code")

    periods = spec["periods"]
    cuts, labels = periods["cuts"], periods["labels"]
    if any(b <= a for a, b in zip(cuts, cuts[1:])):
        add("cuts-order", "/periods/cuts", "cuts must be strictly ascending")
    if len(labels) != len(cuts) + 1:
        add("labels-count", "/periods/labels", f"{len(labels)} labels for {len(cuts)} cuts; needs {len(cuts) + 1}")
    for key in periods.get("strata", {}):
        if not re.fullmatch(PERIOD_NUMBER[1:-1], key) or int(key) > len(labels):
            add("strata-key", f"/periods/strata/{key}", f"{key!r} is not a period number from 1 to {len(labels)}")

    if passage_study and not any(o["source"]["kind"] == "codes" for o in spec["outcomes"]):
        add("codes-outcome-missing", "/outcomes", f"a {unit['kind']} study needs an outcome whose source is codes")
    if passage_study and "attribution" not in unit:
        add("attribution-missing", "/unit", f"a {unit['kind']} study needs unit.attribution")

    tiers = evidence["tiers"]
    for t in evidence["counted_tiers"]:
        if t not in tiers:
            add("counted-tiers-subset", "/evidence/counted_tiers", f"{t!r} is not in tiers")
    ne = evidence["not_established_tier"]
    if ne not in tiers:
        add("ne-tier-undeclared", "/evidence/not_established_tier", f"{ne!r} is not in tiers")
    if ne in evidence["counted_tiers"]:
        add("ne-tier-counted", "/evidence/not_established_tier", f"{ne!r} is a counted tier")

    for key, values in unit.get("exclude_from_rollup", {}).items():
        if key not in pattrs:
            add("exclude-key", f"/unit/exclude_from_rollup/{key}", f"{key!r} is not a passage_attributes key")
            continue
        codes = [lv["code"] for lv in pattrs[key]["levels"]]
        for v in values:
            if v not in codes:
                add("exclude-value", f"/unit/exclude_from_rollup/{key}", f"{v!r} is not a level code of {key!r}")
    if "rollup_types" in unit and unit["rollup_types"] not in pattrs:
        add("rollup-types-key", "/unit/rollup_types", f"{unit['rollup_types']!r} is not a passage_attributes key")
    for i, key in enumerate(unit.get("rollup_by", [])):
        if key not in pattrs:
            add("rollup-by-key", f"/unit/rollup_by/{i}", f"{key!r} is not a passage_attributes key")
        else:
            for lv in pattrs[key]["levels"]:
                if "|" in lv["code"]:
                    add("rollup-by-pipe", f"/unit/rollup_by/{i}", f"level code {lv['code']!r} of {key!r} has a '|'")

    period_attrs = [i for i, a in enumerate(spec["attributes"]) if a["kind"] == "period"]
    if len(period_attrs) > 1:
        add("period-multiple", "/attributes", f"{len(period_attrs)} attributes of kind period; at most one")
    for i, a in enumerate(spec["attributes"]):
        at, b = f"/attributes/{i}", a["bucketer"]
        if (a["kind"] == "period") != (b["kind"] == "period"):
            add("period-bucketer", f"{at}/bucketer", "an attribute of kind period has a bucketer of kind period, "
                "and only it")
        if b.get("match") == "all" and a["kind"] != "flags":
            add("match-all", f"{at}/bucketer/match", "match 'all' is for a flags attribute only (4.8)")
        if a["kind"] == "flags" and b.get("match") == "first":
            add("match-first-flags", f"{at}/bucketer/match", "a flags attribute's bucketer matches 'all' (4.8)")
        if a["kind"] == "flags" and b["kind"] == "table" and "match" not in b:
            add("match-missing-flags", f"{at}/bucketer", "a flags attribute's table bucketer must say match 'all': "
                "without it the default is 'first' (4.8), which a flags attribute cannot use")
        if a["kind"] == "flags" and "fallback" in b:
            add("fallback-flags", f"{at}/bucketer/fallback", "a flags attribute's bucketer has no fallback (4.8)")
        missing = a.get("missing", DEFAULT_MISSING)
        if missing in a.get("levels", []) or missing in a.get("flags", []):
            add("attribute-missing", at, f"the missing value {missing!r} is one of the attribute's levels or flags")

    cols = frame_columns(spec)
    for c in sorted({c for c in cols if cols.count(c) > 1}):
        add("frame-column-duplicate", "/", f"the frame would have two columns named {c!r} (4.7)")

    if passage_study:
        for i, rule in enumerate(spec["frame_rules"]["exclude"]):
            if rule["rule"] != "not-on-question":
                add("exclude-rule-cells", f"/frame_rules/exclude/{i}/rule",
                    f"{rule['rule']!r} is not defined over cells in version 1 (4.7)")

    for i, e in enumerate(spec["enumerations"]):
        if e["stopping_rule"]["kind"] == "legacy-unrecorded" and spec["status"] != "legacy":
            add("legacy-unrecorded-status", f"/enumerations/{i}/stopping_rule/kind",
                "legacy-unrecorded is allowed only in a legacy study")
    if "legacy_exceptions" in evidence and spec["status"] != "legacy":
        add("legacy-exceptions-status", "/evidence/legacy_exceptions", "allowed only in a legacy study")
    for gate, g in spec["signoffs"]["gates"].items():
        if not g["covers"]:
            add("covers-empty", f"/signoffs/gates/{gate}/covers", "a gate must cover at least one file")
    return out


# --------------------------------------------------------------------------- the study as loaded
@dataclass
class Study:
    """A loaded study: its specification, where it is, and every path it names, resolved under rule 1.6."""

    project: str
    repo_root: Path
    spec_rel: str  # repository-relative path of study.json
    spec_bytes: bytes
    spec: dict | None
    findings: list = field(default_factory=list)
    paths: dict = field(default_factory=dict)  # JSON pointer -> ResolvedPath

    @property
    def study_rel(self) -> str:
        return self.spec_rel.rsplit("/", 1)[0] if "/" in self.spec_rel else ""

    @property
    def ok(self) -> bool:
        return not self.findings

    def covered(self, gate: str) -> set:
        """The identities (rule 1.6) of the files the gate covers."""
        return {rp.identity for ptr, rp in self.paths.items() if ptr.startswith(f"/signoffs/gates/{gate}/covers/")}


SPEC_NAME = "study.json"
PROJECT_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._ -]*")


def locate(project: str) -> str:
    """The repository-relative path of a project's specification: ``Projects/<project>/study.json`` (section 3)."""
    return f"Projects/{project}/{SPEC_NAME}"


def load_study(project: str, repo_root: Path) -> Study:
    """Load and check a project's specification: shape, paths (rule 1.6), checks beyond shape, and the checks that
    read the file system. Raises SurveyUsageError when the project or its specification cannot be found."""
    if not PROJECT_NAME.fullmatch(project) or project in (".", ".."):
        raise SurveyUsageError(f"{project!r} is not a project name (a directory name under Projects/)")
    spec_rel = locate(project)
    spec_path = repo_root / spec_rel
    root_real = os.path.realpath(repo_root)
    if not os.path.lexists(spec_path):
        raise SurveyUsageError(f"no specification at {spec_rel}")
    spec_real = os.path.realpath(spec_path)  # computed once: the check and the read use the same place
    if not inside(spec_real, root_real):
        study = Study(project, repo_root, spec_rel, b"", None)
        study.findings.append(Finding("path-outside", spec_rel, "the specification resolves outside the repository"))
        return study
    if not os.path.isfile(spec_real):
        raise SurveyUsageError(f"{spec_rel} is not a file")
    try:
        data = read_capped(Path(spec_real), MAX_JSON_BYTES)  # links inside the repository are allowed
    except OSError as exc:
        raise SurveyUsageError(f"{spec_rel} cannot be read: {reason(exc)}") from exc
    study = Study(project, repo_root, spec_rel, data or b"", None)
    if data is None:
        study.findings.append(Finding("too-large", spec_rel, f"larger than {MAX_JSON_BYTES} bytes; not read"))
        return study
    spec, errors = load_json_strict(data, spec_rel)
    if errors:
        study.findings += errors
        return study
    shape, declared = [], []
    check_shape(STUDY, spec, "", shape, declared)
    study.findings += [Finding(f.rule, f"{spec_rel}#{f.where or '/'}", f.message) for f in shape]
    if shape:
        return study
    study.spec = spec
    for ptr, value in declared:
        rp, errs = resolve_path(value, study.study_rel, repo_root, f"{spec_rel}#{ptr}")
        study.findings += errs
        if rp is not None:
            study.paths[ptr] = rp
    study.findings += [Finding(f.rule, f"{spec_rel}#{f.where}", f.message) for f in check_semantics(spec)]
    study.findings += check_files(study)
    return study


def check_files(study: Study) -> list[Finding]:
    """The checks of section 3 that read the file system: files that must exist, and gate coverage."""
    out: list[Finding] = []
    spec, draft = study.spec, study.spec["status"] == "draft"
    where = lambda ptr: f"{study.spec_rel}#{ptr}"  # noqa: E731
    for ptr, rp in study.paths.items():
        exists = os.path.exists(rp.real)  # a dangling link names nothing
        if _COVERS.match(ptr):
            if not exists and not draft:
                out.append(Finding("covers-missing", where(ptr), f"{rp.declared!r} does not exist"))
            elif exists and not _is_regular(rp.real):
                out.append(Finding("covers-not-file", where(ptr), f"{rp.declared!r} is not a regular file, so a "
                                   "manifest cannot hash it"))
            continue
        if not exists and not draft and not any(p.match(ptr) for p in MAY_BE_ABSENT):
            out.append(Finding("file-missing", where(ptr), f"{rp.declared!r} does not exist"))
    s0 = study.covered("S0")
    for ptr, rp in study.paths.items():
        if any(p.match(ptr) for p in MUST_BE_S0) and rp.identity not in s0:
            out.append(Finding("not-covered-s0", where(ptr), f"{rp.declared!r} must be covered by gate S0 "
                               "(section 3; 5.1, 5.3)"))
    any_gate = set().union(*(study.covered(g) for g in spec["signoffs"]["gates"])) if spec["signoffs"]["gates"] \
        else set()
    rp = study.paths.get("/evidence/legacy_exceptions")
    if rp is not None and rp.identity not in any_gate:
        out.append(Finding("legacy-exceptions-uncovered", where("/evidence/legacy_exceptions"),
                           f"{rp.declared!r} is covered by no gate"))
    for ptr, rp in study.paths.items():
        if ptr.startswith("/frame_rules/post_steps/") and rp.identity not in any_gate:
            out.append(Finding("post-step-uncovered", where(ptr), f"{rp.declared!r} is covered by no gate (4.5)"))
    return out


def _is_regular(real: str) -> bool:
    try:
        return stat.S_ISREG(os.stat(real).st_mode)
    except OSError:
        return False
