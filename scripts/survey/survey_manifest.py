"""``survey-manifest <project> <gate>`` (contract sections 6.1, 6.2, 7): write the gate's manifest file into the
ledger folder and print what the operator signs. It signs nothing and writes no ledger row (rule 1.4).

Exit 0 when written (or unchanged), 1 when it refuses (a malformed specification or ledger, an undeclared gate, a
covered file that cannot be hashed, an existing manifest path that is not a well-formed manifest file), 2 on a
usage error. On a refusal nothing is written (rule 1.2).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from survey_core import (  # noqa: E402
    MAX_JSON_BYTES, SurveyUsageError, parse_args, print_findings, read_capped, sha256_bytes, symlink_components, usage_exit,
)
from survey_gates import (  # noqa: E402
    GATES, ManifestError, action, build_manifest, check_stored_manifest, manifest_rel, scope,
)
from survey_ledger import check_ledger  # noqa: E402
from survey_spec import load_study  # noqa: E402

PROG = "survey_manifest.py"


def refuse(msg: str) -> int:
    print(f"REFUSED: {msg}")
    return 1


def main(argv=None) -> int:
    try:
        root, project, (gate,) = parse_args(sys.argv[1:] if argv is None else argv, PROG, ("gate",))
        if gate not in GATES:
            raise SurveyUsageError(f"{gate!r} is not a gate; the gates are {', '.join(GATES)}")
        study = load_study(project, root)
    except SurveyUsageError as exc:
        return usage_exit(exc)
    if study.spec is None or not study.ok:
        print_findings(study.findings)
        return refuse(f"{study.spec_rel} is malformed; run survey-validate")
    spec = study.spec
    if gate not in spec["signoffs"]["gates"]:
        return refuse(f"gate {gate} is not declared in {study.spec_rel}")
    ledger = check_ledger(study)
    if not ledger.ok:
        print_findings(ledger.findings)
        return refuse("the ledger folder is malformed")
    try:
        data = build_manifest(study, gate)
    except ManifestError as exc:
        return refuse(f"the manifest cannot be built: {exc}")
    rel = manifest_rel(ledger.rel, spec["id"], gate)
    path = root / rel
    state = "wrote"
    if os.path.lexists(path):
        if not os.path.isfile(path) or os.path.islink(path):
            return refuse(f"{rel} exists and is not a regular file")
        old = read_capped(path, MAX_JSON_BYTES) or b""
        problems = check_stored_manifest(old, gate, project, rel)
        if problems:
            print_findings(problems)
            return refuse(f"{rel} exists and is not a well-formed manifest of this gate; remove it first")
        if old == data:
            state = "unchanged"
    if state == "wrote":
        # The folder was checked above; check again just before writing that no component became a link.
        links = symlink_components(root, rel.rsplit("/", 1)[0])
        if links:
            return refuse(f"a component of {rel} is a symbolic link: {', '.join(links)}")
        fd, tmp = tempfile.mkstemp(prefix=".survey-manifest-", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
            os.chmod(tmp, 0o644)
            os.replace(tmp, path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
    digest = sha256_bytes(data)
    print(f"{state}: {rel}")
    print(f"manifest_sha256: {digest}")
    print(f"scope: {scope(gate, spec['id'])}")
    print(f"action: {action(gate, spec['id'], digest)}")
    print(f"mode: {spec['signoffs']['gates'][gate]['mode']}")
    print("The operator signs the action above with agentteams (an Ed25519 row in the ledger folder, 6.2), from a")
    print("trusted install outside every agent's write root. This tool signs nothing and writes no ledger row.")
    print(f"verify: agentteams --check-clearance {scope(gate, spec['id'])} --clearance-file {rel} "
          f"--output {ledger.rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
