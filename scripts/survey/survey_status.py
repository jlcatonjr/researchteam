"""``survey-status <project>`` (contract section 7): print each gate's manifest hash, state, ``enforce`` and
``mode``, with the reason. Exit 0 whatever the states; 1 only when the specification, a manifest file or the ledger
is malformed; 2 on a usage error. Writes nothing in the repository.

A gate reads ``CLEARED`` only after the tools' own rules and agentteams' check (run as a child process, in this
interpreter's agentteams) both pass (``survey_gates.verify_signoff``). The output says where that agentteams is
installed (inside or outside the repository's work tree; never a home-directory path), and ends with what a
sign-off proves (6.2) and what no tool can check. Every value read from a log is escaped before printing.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from survey_core import SurveyUsageError, environment, parse_args, print_findings, safe, usage_exit  # noqa: E402
from survey_gates import GATES, gate_status  # noqa: E402
from survey_ledger import check_ledger  # noqa: E402
from survey_spec import load_study  # noqa: E402
from survey_verify import Verifier, installed_version, location  # noqa: E402

PROG = "survey_status.py"
#: What a sign-off proves while its keys live in the repository (6.2, lines 874-880; open point 7), and what it does
#: not bind (operator decision Q10).
LIMIT = ("note: a CLEARED gate proves that its manifest was signed by a key that was in the ledger folder when the "
         "gate was checked, by an author on the folder's approver list as it then stood; it does not prove who put "
         "the key there (6.2; open point 7). A sign-off binds the manifest's bytes, not a repository: a row signed "
         "for the same project, study id and files elsewhere clears here too (accepted for version 1).")
#: What no tool can close (6.2, lines 874-880).
GAPS = ("note: no tool can detect every edit to a decisions log's history; review of the ledger folder's history "
        "is the control (6.2).")


def main(argv=None, verifier=None) -> int:
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
    print(safe(f"ledger: {ledger.rel or spec['signoffs']['ledger']}"))
    for reason in ledger.unavailable:
        print(safe(f"ledger note: {reason}"))
    verifier = verifier if verifier is not None else Verifier()
    malformed = list(ledger.findings)
    ran = None
    for gate in GATES:
        st, extra = gate_status(study, gate, ledger, verifier)
        malformed += extra
        if not st.declared:
            print(f"{gate}: NOT DECLARED")
            continue
        print(f"{gate}: {st.state} manifest_sha256={st.manifest_sha256 or '-'} enforce={st.enforce} mode={st.mode}")
        print(safe(f"    reason: {st.reason}"))
        info = st.evidence.get("verifier") or {}
        if info:
            ran = ran or info
            if st.state == "CLEARED":
                print(f"    verified by agentteams {safe(info.get('version', '?'))}, "
                      f"{safe(location(info, root))}")
    if ran:
        print(f"verifier: agentteams {safe(ran.get('version', '?'))}, {safe(location(ran, root))}")
    else:
        why = verifier.probe()
        print(f"verifier: {safe(why)}" if why else
              f"verifier: agentteams {safe(installed_version() or '?')} (not run: no gate reached the check)")
    print(LIMIT)
    print(GAPS)
    if malformed:
        print_findings(malformed)
        print("FAIL: a manifest file or the ledger is malformed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
