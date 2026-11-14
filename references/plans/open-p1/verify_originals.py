"""P1 check: is each published copy exactly its tmp/ original with only the recorded scrub applied?

Run from the repository root: python3 -I references/plans/open-p1/verify_originals.py
Prints one CSV row per original: tmp_path,sha256,check  (check: match | differ:<reason> | missing-copy).
The scrub below is the one recorded in references/plans/archive/README.md (three passes, all applied on 2026-11-14).
"""
import csv
import hashlib
import re
import sys
from pathlib import Path

# The literal patterns (home path, user@host, the operator's name, the noreply address) are kept OUT of this
# published file. They are loaded at run time from the ignored tmp/scrub-patterns.local.json, whose keys are
# pass1/pass2/pass3, each a list of [regex, replacement]. The replacements are those in archive/README.md.
import json as _json
_P = _json.load(open("tmp/scrub-patterns.local.json", encoding="utf-8"))
PASS1, PASS2, PASS3 = ([(re.compile(rx), rep) for rx, rep in _P[k]] for k in ("pass1", "pass2", "pass3"))


def scrub(line, key_pass):
    for rx, rep in PASS1:
        line = rx.sub(rep, line)
    if key_pass:
        for rx, rep in PASS2:
            line = rx.sub(rep, line)
    for rx, rep in PASS3:  # third pass, 2026-11-14: names, as infrastructureManagement's @security required
        line = rx.sub(rep, line)
    return line


def check(orig: Path, copy: Path) -> str:
    if not copy.exists():
        return "missing-copy"
    a = orig.read_text(encoding="utf-8", errors="surrogateescape").splitlines(keepends=True)
    b = copy.read_text(encoding="utf-8", errors="surrogateescape").splitlines(keepends=True)
    if len(a) != len(b):
        return f"differ:line-count {len(a)}!={len(b)}"
    for i, (x, y) in enumerate(zip(a, b), 1):
        if x != y and scrub(x, True) != y and scrub(x, False) != y:
            return f"differ:line {i}"
    return "match"


def main(pairs):
    w = csv.writer(sys.stdout)
    w.writerow(["tmp_path", "sha256", "check"])
    for orig, copy in pairs:
        w.writerow([str(orig), hashlib.sha256(orig.read_bytes()).hexdigest(), check(orig, copy)])


if __name__ == "__main__":
    arch = Path("references/plans/archive")
    pairs = []
    for c in sorted(arch.rglob("*")):
        if not c.is_file() or c.parent == arch:  # skip README and manifest at the archive root
            continue
        rel = c.relative_to(arch)
        o = Path("tmp/by-week") / rel
        if rel.name == "state.vars.txt":
            o = o.with_name("state.env")
        if o.exists():
            pairs.append((o, c))
        else:
            print(f"# no original for {rel}", file=sys.stderr)
    main(pairs)
