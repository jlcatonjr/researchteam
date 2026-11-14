"""S-10 re-vet of pyproject [build-system] requirements: PyPI upload dates + OSV (read-only, public APIs).

Run: python3 -I docs/release/build-requirements-2026-11-14.query.py
Rule: the latest stable release at least 14 days old with no OSV advisory.
"""
import datetime as dt
import json
import re
import urllib.request

NOW = dt.datetime.now(dt.timezone.utc)
CUR = {"setuptools": "84.1.0", "setuptools-scm": "10.3.4", "vcs-versioning": "2.5.0", "packaging": "26.3"}
STABLE = re.compile(r"^\d+(\.\d+)*$")


def get(url, data=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
                                 headers={"User-Agent": "s10-vetting-script", "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))


def key(v):
    return tuple(int(x) for x in v.split("."))


def osv(pkg, v):
    r = get("https://api.osv.dev/v1/query", {"package": {"name": pkg, "ecosystem": "PyPI"}, "version": v})
    return [x["id"] for x in r.get("vulns", [])] or ["none"]


print("queried", NOW.isoformat(timespec="minutes"))
for pkg, cur in CUR.items():
    d = get(f"https://pypi.org/pypi/{pkg}/json")
    rel = {}
    for v, files in d["releases"].items():
        files = [f for f in files if not f.get("yanked")]
        if STABLE.match(v) and files:
            rel[v] = min(dt.datetime.fromisoformat(f["upload_time_iso_8601"].replace("Z", "+00:00")) for f in files)
    vs = sorted(rel, key=key)
    cand = [v for v in vs if (NOW - rel[v]).days >= 14][-1]
    info = get(f"https://pypi.org/pypi/{pkg}/{cand}/json")["info"]
    deps = [r for r in (info["requires_dist"] or []) if "extra ==" not in r]
    print(f"{pkg}: cur={cur} latest={vs[-1]} cand={cand} uploaded={rel[cand].date()} age={(NOW - rel[cand]).days}d "
          f"OSV[cand]={osv(pkg, cand)} OSV[cur]={osv(pkg, cur)} requires_python={info['requires_python']} deps={deps}")
