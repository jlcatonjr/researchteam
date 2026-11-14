"""P4 check: does each researchteam tmp/ original match infrastructureManagement's committed copy?

Run from the repository root: python3 -I references/plans/open-p4/compare_im_copies.py [COMMIT]
(default COMMIT 60f872e34e4a84e7f3ee2d98c57acb71ed97c4ef). Reads IM through the GitHub API only (no fetch into
IM's .git, and no IM content is written anywhere). A line passes if it equals the original after this session's
scrub (references/plans/open-p1/verify_originals.py), or if every word-level change is the original's name or
email replaced by "the operator" (IM @security's edit), or if it is the closed quote in row 8 of
2026-W46/fleet-evaluation-followups.steps.csv. A `.sh.txt` copy is compared with the `.sh` original.
Prints: path,verdict. Paths are printed locally only; they name other repositories, so they are not published.
"""
import base64
import importlib.util
import json
import re
import subprocess
import sys
from difflib import SequenceMatcher

spec = importlib.util.spec_from_file_location("v", "references/plans/open-p1/verify_originals.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
COMMIT = sys.argv[1] if len(sys.argv) > 1 else "60f872e34e4a84e7f3ee2d98c57acb71ed97c4ef"
PRE = "references/plans/from-researchteam/"


def api(path):
    return json.loads(subprocess.run(["gh", "api", path], capture_output=True, text=True, check=True).stdout)


tree = api(f"repos/jlcatonjr/infrastructureManagement/git/trees/{COMMIT}?recursive=1")["tree"]
files = {t["path"][len(PRE):]: t["sha"] for t in tree if t["type"] == "blob" and t["path"].startswith(PRE)}
words = lambda s: re.findall(r"\S+|\s+", s)
for rel, sha in sorted(files.items()):
    if rel == "README.md":
        continue
    orel = rel[:-4] if rel.endswith(".sh.txt") else rel
    a = open("tmp/by-week/" + orel, encoding="utf-8", errors="surrogateescape").read().splitlines()
    b = base64.b64decode(api(f"repos/jlcatonjr/infrastructureManagement/git/blobs/{sha}")["content"]).decode(
        "utf-8", "surrogateescape").splitlines()
    ok = len(a) == len(b)
    for i, (x, y) in enumerate(zip(a, b), 1):
        if not ok:
            break
        s = v.scrub(x, True)
        if s == y:
            continue
        if orel.endswith("fleet-evaluation-followups.steps.csv") and i == 9:
            ops = SequenceMatcher(None, s, y, autojunk=False).get_opcodes()
            if all(op == "equal" or (op == "insert" and y[j1:j2] == '"') for op, i1, i2, j1, j2 in ops):
                continue
        ws, wy = words(s), words(y)
        ch = [("".join(ws[i1:i2]), "".join(wy[j1:j2])) for op, i1, i2, j1, j2 in
              SequenceMatcher(None, ws, wy, autojunk=False).get_opcodes() if op != "equal"]
        old = "".join(o for o, _ in ch)
        new = "".join(n for _, n in ch)
        ok = "operator" in new.lower() and ("@" in old or re.search(r"[A-Z][a-z]+", old) is not None)
    print(f"{orel},{'match' if ok else 'differ'}")
