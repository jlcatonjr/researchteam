"""scripts/briefing_library.py: the literature library's short-lived briefing record class (ingest, check, query)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "briefing_library.py"
TODAY = "2026-10-30"

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not available")


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def claim(text: str, domain: str = "reuters.com", kind: str = "reported", **kw) -> dict:
    return {"claim": text, "source_domain": domain, "attribution": f"{domain} reported (2026-10-28)",
            "published_at": "2026-10-28", "kind": kind, "single_source": True, "sensitive": False, **kw}


def briefing(tmp: Path, topic: str, claims: list[dict]) -> Path:
    p = tmp / f"{abs(hash(topic))}.json"
    p.write_text(json.dumps({"topic": topic, "claims": claims}), encoding="utf-8")
    return p


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text("var/\n", encoding="utf-8")
    return tmp_path


def records(store: Path) -> list[dict]:
    return [json.loads(l) for l in (store / "literature.jsonl").read_text().splitlines() if l.strip()]


def test_ingest_writes_the_library_layout_and_check_passes(repo: Path) -> None:
    store = repo / "var" / "briefings"
    b = briefing(repo, "power grids", [claim("Grid operators reported more intrusion attempts."),
                                       claim("Cascading failures can spread across grids.", "doi.org", "scholarly")])
    r = run("ingest", str(store), str(b), "--as-of", TODAY)
    assert r.returncode == 0, r.stderr
    assert {p.name for p in store.iterdir()} >= {"literature.jsonl", "term-vectors.jsonl", "library-manifest.json"}
    manifest = json.loads((store / "library-manifest.json").read_text())
    assert manifest["artifact_type"] == "briefing-index" and manifest["record_count"] == 2
    recs = {x["kind"]: x for x in records(store)}
    assert recs["reported"]["expires"] == "2026-11-06" and recs["scholarly"]["expires"] == "2027-10-30"
    assert all(x["verification_state"].startswith("UNVERIFIED") for x in recs.values())
    assert run("check", str(store), "--as-of", TODAY).returncode == 0


def test_a_tracked_store_is_refused(repo: Path) -> None:
    store = repo / "references" / "briefings"
    r = run("ingest", str(store), str(briefing(repo, "t", [claim("A plain claim about grids.")])))
    assert r.returncode == 2 and "never be committed" in r.stderr
    assert not store.exists()


def test_bad_claims_are_rejected_and_topics_replaced(repo: Path) -> None:
    store = repo / "var" / "b"
    bad = [claim("See https://example.com"), claim("x" * 241), claim("ok", kind="opinion"),
           claim("line\nbreak"), claim("fine claim about grids")]
    r = run("ingest", str(store), str(briefing(repo, "grids", bad)), "--as-of", TODAY)
    assert "1 records ingested, 4 rejected" in r.stdout
    run("ingest", str(store), str(briefing(repo, "grids", [claim("a newer claim about grids")])), "--as-of", TODAY)
    assert [x["claim"] for x in records(store)] == ["a newer claim about grids"]


def test_expired_records_are_advisory_pruned_and_never_queried(repo: Path) -> None:
    store = repo / "var" / "b"
    run("ingest", str(store), str(briefing(repo, "grids", [claim("Grid intrusion attempts rose.")])), "--as-of", TODAY)
    later = "2026-11-07"
    r = run("check", str(store), "--as-of", later)
    assert r.returncode == 0 and "EXPIRED" in r.stdout
    assert "no lexical overlap" in run("query", str(store), "grid intrusion", "--as-of", later).stdout
    assert "Grid intrusion" in run("query", str(store), "grid intrusion", "--as-of", TODAY).stdout
    run("ingest", str(store), str(briefing(repo, "other", [claim("Another topic entirely.")])), "--as-of", later)
    assert [x["topic"] for x in records(store)] == ["other"]


def test_hand_edits_and_stretched_ttls_are_defects(repo: Path) -> None:
    store = repo / "var" / "b"
    run("ingest", str(store), str(briefing(repo, "grids", [claim("Grid intrusion attempts rose.")])), "--as-of", TODAY)
    recs = records(store)
    recs[0]["expires"] = "2027-12-31"
    (store / "literature.jsonl").write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in recs))
    r = run("check", str(store), "--as-of", TODAY)
    assert r.returncode == 1 and "DEFECT[STALE]" in r.stdout and "TTL longer" in r.stdout


def test_a_store_outside_any_repo_is_allowed(tmp_path: Path) -> None:
    store = tmp_path / "loose"
    assert run("ingest", str(store), str(briefing(tmp_path, "t", [claim("A plain claim.")])),
               "--as-of", TODAY).returncode == 0


def test_usage_errors() -> None:
    assert run().returncode == 2
    assert run("query", "x", "terms", "-k", "0").returncode == 2
    assert run("check", "x", "--as-of", "yesterday").returncode == 2
