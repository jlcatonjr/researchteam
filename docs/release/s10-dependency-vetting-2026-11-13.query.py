import json, urllib.request, datetime as dt, re
NOW = dt.datetime(2026,11,13,tzinfo=dt.timezone.utc)
CUR = {"jsonschema":"4.26.0","attrs":"26.1.0","jsonschema-specifications":"2025.9.1","referencing":"0.37.0",
       "rpds-py":"2026.6.3","cryptography":"50.0.0","cffi":"2.1.1","pycparser":"3.0","typing-extensions":"4.16.0"}
def get(u, data=None):
    req = urllib.request.Request(u, data=json.dumps(data).encode() if data else None,
        headers={"User-Agent":"s10-vetting-script","Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))
stable = re.compile(r"^\d+(\.\d+)*$")
def key(v): return tuple(int(x) for x in v.split("."))
for p, cur in CUR.items():
    d = get(f"https://pypi.org/pypi/{p}/json")
    rel = {}
    for v, files in d["releases"].items():
        files = [f for f in files if not f.get("yanked")]
        if stable.match(v) and files:
            rel[v] = min(dt.datetime.fromisoformat(f["upload_time_iso_8601"].replace("Z","+00:00")) for f in files)
    vs = sorted(rel, key=key)
    latest = vs[-1]
    ok = [v for v in vs if (NOW-rel[v]).days >= 14]
    cand = ok[-1]
    newer = [f"{v}({rel[v].date()},{(NOW-rel[v]).days}d)" for v in vs if key(v) > key(cur)]
    def osv(v): 
        r = get("https://api.osv.dev/v1/query", {"package":{"name":p,"ecosystem":"PyPI"},"version":v})
        return [x["id"] for x in r.get("vulns",[])] or ["none"]
    print(f"{p}: cur={cur} latest={latest}({rel[latest].date()},{(NOW-rel[latest]).days}d) cand={cand}({rel[cand].date()},{(NOW-rel[cand]).days}d) OSV[cand]={osv(cand)} OSV[cur]={osv(cur)} newer={newer}")
