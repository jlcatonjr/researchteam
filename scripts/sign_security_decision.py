#!/usr/bin/env python3
"""Append an operator-signed (HMAC) security decision to the agentteams decisions log.

OPERATOR-ONLY. The signing key is read from AGENTTEAMS_DECISION_SIGNING_KEY, which must be set in
the operator's own shell and never in a file in the repository or in an agent's environment. With
`enforce_decision_signing: true` (the scaffold default), agentteams refuses unsigned clearances,
so this is how a human authorizes a routine destructive action such as the `overwrite` pass run
by `researchteam materialize`.

Constraint-relaxing exceptions need an Ed25519 row minted with `agentteams --sign-decision`
instead; this helper does not produce those.

The key must be at least 32 bytes and not a placeholder (agentteams 1.0.0rc12 refuses anything else, and
rows signed with a shorter key stop verifying). Generate one with:
  python3 -c 'import secrets; print(secrets.token_hex(32))'

Usage:
  export AGENTTEAMS_DECISION_SIGNING_KEY=...
  python scripts/sign_security_decision.py --action overwrite --conditions "first render"
  researchteam materialize --yes        # same shell: verification needs the key too
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

LOG = Path(".github/agents/references/security-decisions.log.csv")
REQUIRED = ("timestamp", "requesting_agent", "action_reviewed", "verdict", "conditions", "conditions_verified")


MIN_KEY_BYTES = 32
_PLACEHOLDERS = ("...", "changeme", "change-me", "secret", "placeholder", "xxx", "todo", "your-key", "<")


def key_problem(key: str) -> str:
    """Why an HMAC signing key is unusable, or "" (agentteams 1.0.0rc12: >= 32 bytes, not a placeholder)."""
    if not key:
        return "is not set in this shell"
    low = key.strip().lower()
    if any(low == p or low.startswith(p) for p in _PLACEHOLDERS) or len(set(low)) <= 2:
        return "looks like a placeholder"
    if len(key.encode("utf-8")) < MIN_KEY_BYTES:
        return f"is shorter than {MIN_KEY_BYTES} bytes"
    return ""


def write_atomic(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    """Write the log via a temp file in the same directory and os.replace, so a failure can never
    leave the audit log truncated."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".decisions-", suffix=".csv")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--action", required=True, help="agentteams action id, e.g. overwrite or prune")
    ap.add_argument("--conditions", required=True, help="what was reviewed and why it is cleared")
    ap.add_argument("--log", type=Path, default=LOG)
    args = ap.parse_args()

    why = key_problem(os.environ.get("AGENTTEAMS_DECISION_SIGNING_KEY", ""))
    if why:
        print(f"AGENTTEAMS_DECISION_SIGNING_KEY {why} — refusing. Generate one with: "
              "python3 -c 'import secrets; print(secrets.token_hex(32))'", file=sys.stderr)
        return 1
    try:
        from agentteams.cli.decision_log import sign_decision_row
        from agentteams.cli.security_gate import check_clearance
    except ImportError:
        print("agentteams is not importable in this interpreter (run `researchteam doctor`).", file=sys.stderr)
        return 1
    if not args.log.exists() or args.log.parent.name != "references":
        print(f"decisions log not found at <agents-dir>/references/: {args.log}", file=sys.stderr)
        return 1

    with args.log.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    missing = [c for c in REQUIRED if c not in fields]
    if missing:
        print(f"decisions log lacks expected columns {missing}; refusing to modify it.", file=sys.stderr)
        return 1
    if "prev_digest" in fields:
        print("this log is hash-chained (prev_digest); sign it with agentteams tooling instead.", file=sys.stderr)
        return 1
    original_fields = list(fields)
    if "signature" not in fields:
        fields.append("signature")  # existing rows keep an empty signature

    row = {f: "" for f in fields}
    row.update({
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "requesting_agent": "security",
        "action_reviewed": args.action,
        "verdict": "PASS",
        "conditions": f"operator-signed: {args.conditions}",
        "conditions_verified": "verified",
    })
    row["signature"] = sign_decision_row(row)

    write_atomic(args.log, fields, rows + [row])

    ok, reason = check_clearance(args.log.parent.parent, action=args.action)
    if not ok:
        write_atomic(args.log, original_fields, rows)  # roll back: never leave an unaccepted PASS
        print(f"the gate rejected the signed row, log restored: {reason}", file=sys.stderr)
        return 1
    print(f"signed PASS for '{args.action}' appended and verified by the agentteams gate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
