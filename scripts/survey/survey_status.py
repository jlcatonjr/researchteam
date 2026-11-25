"""``survey-status <project>`` (contract section 7): print each gate's manifest hash, state, ``enforce`` and
``mode``. Exit 0 whatever the states; 1 only when the specification, a manifest file or the ledger is malformed;
2 on a usage error. Writes nothing.

This version verifies no signature: a gate reads ``UNCLEARED`` when its files changed since its manifest file was
written, and ``UNAVAILABLE`` otherwise. It never reads ``CLEARED``. A reason the HALT scan of 6.2 cannot be made
(a team directory reached through a link, an unusable ``parent_team``) leaves the gates ``UNAVAILABLE`` and is
printed; it does not make the exit status non-zero.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from survey_core import SurveyUsageError, environment, parse_args, print_findings, usage_exit  # noqa: E402
from survey_gates import GATES, gate_status  # noqa: E402
from survey_ledger import check_ledger  # noqa: E402
from survey_spec import load_study  # noqa: E402

PROG = "survey_status.py"


def main(argv=None) -> int:
    try:
        root, project, _ = parse_args(sys.argv[1:] if argv is None else argv, PROG)
        study = load_study(project, root)
    except SurveyUsageError as exc:
        return usage_exit(exc)
    if study.spec is None or not study.ok:
        print_findings(study.findings)
        print(f"FAIL: {study.spec_rel} is malformed; run survey-validate")
        return 1
    spec = study.spec
    ledger = check_ledger(study)
    env = environment()
    print(f"study {spec['id']} ({study.spec_rel}): status {spec['status']}, schema_version {spec['schema_version']}")
    print(f"environment: python {env['python']}, unicodedata {env['unicodedata']}")
    print(f"ledger: {ledger.rel or spec['signoffs']['ledger']}")
    for reason in ledger.unavailable:
        print(f"ledger note: {reason}")
    malformed = list(ledger.findings)
    for gate in GATES:
        st, extra = gate_status(study, gate, ledger)
        malformed += extra
        if not st.declared:
            print(f"{gate}: NOT DECLARED")
            continue
        print(f"{gate}: {st.state} manifest_sha256={st.manifest_sha256 or '-'} enforce={st.enforce} mode={st.mode}")
        print(f"    reason: {st.reason}")
    print("note: this version verifies no signature, so no gate reads CLEARED.")
    if malformed:
        print_findings(malformed)
        print("FAIL: a manifest file or the ledger is malformed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
