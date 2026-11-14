# Fix: the release-line candidate from a stable lock must be stable (researchteam 1.1.1)

Reported by infrastructureManagement on 2026-11-09 (agentteams row 691; agentteams-6c verified it in source).

**Defect.** `researchteam._release.newest_on_line` keeps every tag on the line with `tag_key > current`. Because
`tag_key` orders `v1.1.1-rc.1` above `v1.1.0`, a STABLE lock gets an rc as its candidate. `check_toolchain.py
--release-candidate` then prints it, and the autosync gate integrates it. baseAgent #324 (v1.1.0 → v1.1.1-rc.1)
shows this. It breaks the latest-stable rule: adopting an rc requires a recorded `@security` clearance.

**Fix.**
- `newest_on_line(repo, current, include_prerelease=None)`: from a stable `current`, only stable tags are
  eligible. From an rc, newer rcs and the final stay eligible. `include_prerelease=True` is an explicit opt-in.
- `check_toolchain.py --release-candidate NAME [--include-prerelease]`. The autosync gate never passes the flag.
- `--write-lock --tag name=<rc>` is unchanged: a deliberate rc pin is still possible, with its own signed row.

**Tests:** stable→rc refused, stable→stable, rc→final, rc→rc, the opt-in, and the existing line tests.

**Release.** researchteam v1.1.1, a patch on release/1.1: PR to main, then the operator fast-forwards
release/1.1 and signs v1.1.1. Derived repos move with `--researchteam-tag v1.1.1`, which re-syncs
check_toolchain.py and installs the fixed `_release.py`. Until they do, keep autosync held for v1.1-locked repos.
