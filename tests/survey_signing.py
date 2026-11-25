"""Signed sign-off rows for the survey toolkit's step F tests, made with a key pair generated at run time.

Nothing here is a real key: each test generates a throwaway Ed25519 pair in its temporary folder, puts the public half
in the invented ledger folder, and never writes the private half anywhere but that folder's sibling.

**Why the rows are not made with ``agentteams --sign-decision``.** The tools refuse a row carrying agentteams'
checkout-signing mark (operator decision Q4). agentteams' signer refuses to run from an install inside a git work
tree (a virtual environment inside a checkout counts) unless ``--allow-checkout-signing`` is passed, and that flag
writes the mark into the signed row. A signer outside every work tree would need a second agentteams install in the
temporary folder (a network fetch or a wheel). So, as @security allowed for tests only, the rows are built with
agentteams' own payload builder (``decision_log._decision_signature_values``, a private name), signed with its public
``signed_ledger.ed25519_sign``, chained with the public ``decision_chain.chain_tip``, text-bound with
``decision_text.bind_text_digest`` and written with the public ``decision_log.append_signed_decision_row``: every
step ``--sign-decision`` takes after its operator gates. The survey tools themselves never import any of this.

Importing this module needs agentteams and ``cryptography``; tests import it only after ``require_signing()``.
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

import pytest

from survey_support import survey_ledger

DATE = "2026-11-25"


def require_signing():
    """Skip the calling test, with the reason, unless agentteams 1.3.0 and cryptography are importable here."""
    pytest.importorskip("cryptography", reason="the signing tests need cryptography (agentteams' signing extra)")
    pytest.importorskip("agentteams.cli.decision_log", reason="the signing tests need agentteams 1.3.0 installed")


def new_key(folder: Path, key_id: str = "op-test") -> str:
    """Generate a throwaway Ed25519 pair; write the public PEM into the ledger folder's key store as
    ``<key_id>.pub.pem`` (replacing any file of that name) and return the private PEM text."""
    from cryptography.hazmat.primitives import serialization as ser
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    key = Ed25519PrivateKey.generate()
    pub = key.public_key().public_bytes(ser.Encoding.PEM, ser.PublicFormat.SubjectPublicKeyInfo)
    (folder / "references" / "authorized-verify-keys" / f"{key_id}.pub.pem").write_bytes(pub)
    return key.private_bytes(ser.Encoding.PEM, ser.PrivateFormat.PKCS8, ser.NoEncryption()).decode()


def sign_row(folder: Path, private_pem: str, action: str, *, key_id: str = "op-test", author: str = "operator",
             verdict: str = "PASS", conditions_verified: str = "", evidence: str = "invented test sign-off",
             **extra) -> None:
    """Append one Ed25519-signed row to the folder's log, as ``--sign-decision`` would after its gates."""
    from agentteams.cli import decision_log as dl
    from agentteams.cli import signed_ledger as sl
    from agentteams.cli.decision_chain import chain_tip
    from agentteams.cli.decision_text import bind_text_digest

    log = folder / "references" / "security-decisions.log.csv"
    before = log.read_bytes()
    reader = csv.DictReader(io.StringIO(before.decode("utf-8"), newline=""))
    rows, fields = list(reader), list(reader.fieldnames or survey_ledger.LOG_HEADER)
    row = {c: "" for c in survey_ledger.LOG_HEADER}
    row.update(timestamp=DATE, date=DATE, action_reviewed=action, verdict=verdict, author=author, key_id=key_id,
               evidence=evidence, conditions_verified=conditions_verified, sig_scheme="ed25519", **extra)
    row["prev_digest"] = chain_tip(rows, fields, signing_active=True)
    bind_text_digest(row)
    row["signature"] = sl.ed25519_sign(private_pem, dl._decision_signature_values(row))
    dl.append_signed_decision_row(folder, row, before=before)
