#!/usr/bin/env bash
# 03 — Undo what remains of the 2026-11-09 rc12 fleet sweep, outside visualknowledge (operator ruling 2026-11-09).
# OPERATOR ONLY, plain Terminal:
#   bash ~/githubrepositories/researchteam/tmp/by-week/2026-W46/operator/03-revert-rc12-leftovers.sh           # dry run (default): lists actions only
#   bash ~/githubrepositories/researchteam/tmp/by-week/2026-W46/operator/03-revert-rc12-leftovers.sh --apply   # act, after a y/N prompt
#
# Source of truth: the fleet's own report, ~/.local/logs/fleet/20261109-143008/report.json. For each git workspace
# it records snapshot_ref, a commit-tree of the pre-fleet working state, and diff_file, the fleet's change.
# Only two kinds of change are made:
#   A. TRACKED: a file whose current `git diff <snapshot_ref> -- <file>` is byte-identical to its section of the
#      fleet's recorded diff, so it is unchanged since the fleet wrote it. It is restored from the snapshot, working
#      tree only (`git restore --source=<snap> --worktree`). Pre-fleet uncommitted edits come back as they were, and
#      the index is untouched.
#   B. UNTRACKED rc12 leftovers: a file named sandbox-handoff.reference.md, or a directory
#      .agentteams-backups/20261109-*. It must be untracked, not present in the snapshot, and modified during the run
#      window (2026-11-09 09:30–16:51). It is MOVED, never deleted, to ~/.local/logs/fleet/20261109-143008-cleanup/<ws>/.
# Never touched: workspaces under visualknowledge/ (handed to collector-management; for that fleet only, its owner
# runs SCOPE=visualknowledge <this script> [--apply]), any file changed since the
# fleet wrote it, anything outside those two patterns. Each acted-on workspace's `git status` and `git diff` are
# saved first. No commits, no stash, no index changes.
set -euo pipefail
[ -z "${CLAUDECODE:-}${CLAUDE_CODE_ENTRYPOINT:-}" ] || [ "${1:-}" != "--apply" ] || { echo "run --apply in your own terminal, not an agent session" >&2; exit 1; }
MODE="${1:-dry-run}"
[ "$MODE" = dry-run ] || [ "$MODE" = --apply ] || { echo "usage: $0 [--apply]" >&2; exit 2; }
if [ "$MODE" = --apply ]; then
  read -r -p "Restore/move the files listed by the dry run (same rules, re-checked now)? [y/N] " a
  [ "$a" = y ] || { echo "stopped; nothing changed"; exit 1; }
fi
exec /usr/bin/python3 -I - "$MODE" "${SCOPE:-default}" <<'PY'
import json, os, re, shutil, subprocess, sys, datetime as dt
from pathlib import Path

APPLY = sys.argv[1] == "--apply"
SCOPE = sys.argv[2]   # "default" = everything except visualknowledge/; "visualknowledge" = only visualknowledge/
HOME = Path.home()
REPORT = HOME / ".local/logs/fleet/20261109-143008/report.json"
OUT = HOME / ".local/logs/fleet/20261109-143008-cleanup"
SKIP_PREFIX = str(HOME / "githubrepositories/visualknowledge") + "/"
T0 = dt.datetime(2026, 11, 9, 9, 30).timestamp()
T1 = dt.datetime(2026, 11, 9, 16, 51).timestamp()
AGENT_DIRS = (".github", ".claude", ".goose", ".codex", ".agents")

def git(ws, *a, check=False):
    r = subprocess.run(["git", "-c", "core.quotePath=false", "-C", str(ws), *a], capture_output=True)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(a)} in {ws}: {r.stderr.decode(errors='replace')[:200]}")
    return r

def split_diff(text: bytes):
    """{path: section bytes} from a `git diff` (sections start at 'diff --git a/<p> b/<p>')."""
    out, cur, buf = {}, None, []
    for line in text.splitlines(keepends=True):
        m = re.match(rb"^diff --git a/(.+?) b/(.+?)\n$", line)
        if m:
            if cur is not None: out[cur] = b"".join(buf)
            cur, buf = m.group(2).decode("utf-8", "surrogateescape"), [line]
        elif cur is not None:
            buf.append(line)
    if cur is not None: out[cur] = b"".join(buf)
    return out

rep = json.loads(REPORT.read_text())
tot_a = tot_b = 0
for w in rep["workspaces"]:
    ws = Path(w["path"]); snap = w.get("snapshot_ref"); dfile = w.get("diff_file")
    if not (w.get("is_git") and snap and dfile and Path(dfile).is_file()): continue
    rel_ws = str(ws.relative_to(HOME / "githubrepositories")) if str(ws).startswith(str(HOME / "githubrepositories") + "/") else ""
    # visualknowledge scope: visualknowledge/* and the agentteams-wt-fleet-* clones, which are visualknowledge
    # checkouts (infrastructureManagement scope correction, 2026-11-09).
    in_vk = str(ws).startswith(SKIP_PREFIX) or rel_ws.startswith("agentteams-wt-fleet-")
    if (in_vk if SCOPE == "default" else not in_vk) or not ws.is_dir(): continue
    if git(ws, "rev-parse", "--verify", "-q", f"{snap}^{{commit}}").returncode:
        print(f"! {ws}: snapshot {snap[:12]} missing; skipped"); continue
    recorded = split_diff(Path(dfile).read_bytes())
    acts_a, left = [], []
    for path, sec in recorded.items():
        now = git(ws, "diff", snap, "--", path).stdout
        if now and now == sec: acts_a.append(path)
        elif now: left.append(path)
    # B: untracked rc12 leftovers
    acts_b = []
    unt = git(ws, "ls-files", "--others", "--exclude-standard", "--directory", "--", *AGENT_DIRS).stdout.decode().splitlines()
    for rel in unt:
        p = ws / rel.rstrip("/"); name = p.name
        is_handoff = name == "sandbox-handoff.reference.md" and p.is_file()
        is_backup = p.is_dir() and p.parent.name == ".agentteams-backups" and name.startswith("20261109-")
        if rel.endswith("/") and not is_backup:
            # a whole untracked dir: look inside for the handoff file only
            for q in p.rglob("sandbox-handoff.reference.md"):
                r2 = str(q.relative_to(ws))
                if git(ws, "cat-file", "-e", f"{snap}:{r2}").returncode and T0 <= q.stat().st_mtime <= T1: acts_b.append(r2)
            continue
        if not (is_handoff or is_backup): continue
        rel = rel.rstrip("/")
        if git(ws, "cat-file", "-e", f"{snap}:{rel}").returncode == 0: continue   # existed before the fleet
        if T0 <= p.stat().st_mtime <= T1: acts_b.append(rel)
    if not (acts_a or acts_b): continue
    tot_a += len(acts_a); tot_b += len(acts_b)
    print(f"\n▸ {ws}  (snapshot {snap[:12]})")
    for a in acts_a: print(f"    restore  {a}")
    for b in acts_b: print(f"    move     {b}")
    for l in left: print(f"    LEFT     {l}  (changed since the fleet wrote it)")
    if APPLY:
        dest = OUT / str(ws.relative_to(HOME / "githubrepositories")).replace("/", "__")
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "status.before.txt").write_bytes(git(ws, "status", "--porcelain").stdout)
        (dest / "working-tree.before.diff").write_bytes(git(ws, "diff").stdout)
        for a in acts_a:
            if git(ws, "diff", snap, "--", a).stdout != recorded[a]:
                print(f"    LEFT     {a}  (changed between dry run and apply)"); continue
            git(ws, "restore", f"--source={snap}", "--worktree", "--", a, check=True)
        for b in acts_b:
            tgt = dest / "moved" / b; tgt.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(ws / b), str(tgt))
        print(f"    done; backup in {dest}")
print(f"\n{'APPLIED' if APPLY else 'DRY RUN'}: {tot_a} tracked file(s) to restore, {tot_b} untracked leftover(s) to move"
      + ("" if APPLY else ". Re-run with --apply to act."))
PY
