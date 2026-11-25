"""Generate the published JSON Schema (2020-12) of ``study.json`` from the validator's rule table.

The schema is a description for editors (contract section 3); the validator in ``survey_spec.py`` is the
authority. Both come from one table, so a field cannot be in one and not the other. The checks beyond shape cannot
be written in JSON Schema and are named in the schema's description.

    python3 scripts/survey/survey_schema.py            # write scripts/survey/study.schema.json
    python3 scripts/survey/survey_schema.py --check    # exit 1 when the tracked file differs from the output
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from survey_spec import (  # noqa: E402
    DEFS, SEMANTIC_RULES, STUDY, AnyObject, AnyOf, Arr, Bool, ByKind, Int, MapOf, Null, Num, Obj, Ref, Str,
)

SCHEMA_FILE = HERE / "study.schema.json"


def to_schema(node) -> dict:
    """One rule-table node as a JSON Schema."""
    if isinstance(node, Ref):
        return {"$ref": f"#/$defs/{node.name}"}
    if isinstance(node, Str):
        s: dict = {"type": "string"}
        if node.enum is not None:
            s = {"const": node.enum[0]} if len(node.enum) == 1 else {"enum": list(node.enum)}
        if node.min_len:
            s["minLength"] = node.min_len
        if node.pattern:
            s["pattern"] = node.pattern
        if node.is_path:
            s["description"] = "a path under rule 1.6: relative to the study's folder, or repo:-rooted"
        return s
    if isinstance(node, Int):
        s = {"type": "integer"}
        if node.minimum is not None:
            s["minimum"] = node.minimum
        return s
    if isinstance(node, Num):
        s = {"type": "number"}
        if node.minimum is not None:
            s["minimum"] = node.minimum
        if node.maximum is not None:
            s["maximum"] = node.maximum
        return s
    if isinstance(node, Bool):
        return {"type": "boolean"}
    if isinstance(node, Null):
        return {"type": "null"}
    if isinstance(node, AnyObject):
        return {"type": "object"}
    if isinstance(node, Arr):
        s = {"type": "array", "items": to_schema(node.items)}
        if node.min_items:
            s["minItems"] = node.min_items
        return s
    if isinstance(node, MapOf):
        s = {"type": "object", "additionalProperties": to_schema(node.values)}
        if node.key_enum is not None:
            s["propertyNames"] = {"enum": list(node.key_enum)}
        elif node.key_pattern:
            s["propertyNames"] = {"pattern": node.key_pattern}
        return s
    if isinstance(node, AnyOf):
        return {"anyOf": [to_schema(o) for o in node.options]}
    if isinstance(node, ByKind):
        return {"oneOf": [to_schema(v) for v in node.variants.values()]}
    if isinstance(node, Obj):
        s = {"type": "object",
             "properties": {k: to_schema(sub) for k, (sub, _req) in node.props.items()},
             "additionalProperties": False}
        required = [k for k, (_sub, req) in node.props.items() if req]
        if required:
            s["required"] = required
        conds = []
        for c in node.conds:
            rule = {"if": {"properties": {c.field: {"const": c.equals}}, "required": [c.field]},
                    "then": {"required": list(c.then_required)}}
            if c.else_forbidden:
                rule["else"] = {"not": {"anyOf": [{"required": [f]} for f in c.else_forbidden]}}
            conds.append(rule)
        if conds:
            s["allOf"] = conds
        return s
    raise TypeError(f"unknown rule-table node {node!r}")


def generate() -> dict:
    checks = "; ".join(f"{rid} ({desc})" for rid, _line, desc in SEMANTIC_RULES)
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Survey study specification (study.json), contract version 1",
        "description": ("Generated from the rule table of scripts/survey/survey_spec.py by survey_schema.py; do not "
                        "edit. A description for editors: the validator (survey-validate) is the authority "
                        "(docs/survey-toolkit.md, section 3). It also makes these checks, which this schema cannot "
                        f"express, and the path rule (1.6): {checks}."),
    }
    schema.update(to_schema(STUDY))
    schema["$defs"] = {name: to_schema(node) for name, node in DEFS.items()}
    return schema


def render() -> bytes:
    """The schema file's bytes: indented for reading, keys in table order, one trailing line feed."""
    return (json.dumps(generate(), indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv not in ([], ["--check"]):
        print("usage: survey_schema.py [--check]", file=sys.stderr)
        return 2
    data = render()
    if argv == ["--check"]:
        if not SCHEMA_FILE.is_file() or SCHEMA_FILE.read_bytes() != data:
            print(f"{SCHEMA_FILE.name} differs from the rule table; run survey_schema.py to regenerate it")
            return 1
        print(f"{SCHEMA_FILE.name} matches the rule table")
        return 0
    SCHEMA_FILE.write_bytes(data)
    print(f"wrote {SCHEMA_FILE.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
