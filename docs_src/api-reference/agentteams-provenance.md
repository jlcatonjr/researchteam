# `_agentteams_provenance` — ResearchTeam

Check which agentteams code a layer-1 render is about to run, and refuse unreviewed code. Adapted from mathAgents' `scripts/lib/agentteams_provenance.py`, the guard written after mathAgents renders dropped every adopted routing row because the agentteams that ran was an unrecorded local snapshot taken before the fix (CA-033). The check classifies the install that the resolved `agentteams` launcher imports, using its PEP 610 `direct_url.json`. "The code" is both modules the launcher runs: its entry module `build_team` (a top-level module beside the package) and the `agentteams` package. The check runs in two stages: `check(exe)` runs under researchteam's interpreter, finds the interpreter the launcher uses, and re-runs this file there with `--inner`, so the install it inspects is the one the launcher imports. The file is stdlib-only for that reason. `researchteam update` runs this check before a render and refuses on a non-zero result.

> *Source: `researchteam/_agentteams_provenance.py`*

> **Stability.** researchteam's modules are underscore-prefixed. The supported interface is the `researchteam` CLI ([CLI reference](../cli-reference.md)). The functions on this page are documented for contributors and may change between releases.

---

## Classification

| Install | Result |
|---------|--------|
| Editable (`dir_info.editable`), or no installed distribution (a bare source tree on `sys.path`) | Refused unless the checkout's `HEAD` is an ancestor of `origin/main` and the imported package directory and `build_team` module have no uncommitted or untracked sources (bytecode caches excepted). |
| VCS install (`vcs_info.commit_id`) from `github.com/jlcatonjr/agentteams` (see `is_canonical_repo`) | Passes; prints the source URL and the first 12 characters of the commit. |
| VCS install from any other repository (a fork or mirror at a commit not reviewed upstream) | Unverified: refused unless `RESEARCHTEAM_ALLOW_UNVERIFIED_AGENTTEAMS=1`. |
| Local-folder snapshot (non-editable `file:` URL, no commit) | Refused, unless `RESEARCHTEAM_ALLOW_AGENTTEAMS_SNAPSHOT=1`, which runs it and prints a `WARNING` to stderr. |
| Archive install (a non-`file:` URL without VCS info) | Unverified: no commit is recorded, so the code cannot be matched to a reviewed one. |
| Index install (no URL in `direct_url.json`, or no `direct_url.json`) | Unverified: agentteams is not published on PyPI, so a package of that name from an index is not the reviewed source. Prints the distribution version. |

An unverified install is refused (`... REFUSED: <reason>; install a reviewed commit (pip install "agentteams @ git+https://github.com/jlcatonjr/agentteams@<sha>"), or set RESEARCHTEAM_ALLOW_UNVERIFIED_AGENTTEAMS=1 to run it anyway`). With `RESEARCHTEAM_ALLOW_UNVERIFIED_AGENTTEAMS=1` it runs, and a `WARNING: running an unverified agentteams install (...): <reason>` line goes to stderr. The snapshot override (`RESEARCHTEAM_ALLOW_AGENTTEAMS_SNAPSHOT`) is separate and does not cover unverified installs, nor the reverse.

The autosync gate (`scripts/agentteams_autosync_gate.sh`) accepts `AGENTTEAMS_GIT` to override the agentteams git URL. A mirror or fork there is not `github.com/jlcatonjr/agentteams`, so this guard refuses the resulting install unless `RESEARCHTEAM_ALLOW_UNVERIFIED_AGENTTEAMS=1`.

For any non-editable install, if the `build_team` or `agentteams` module that Python would import is not one of the files the distribution's record lists (a checkout earlier on `sys.path` shadows it), the check refuses, since the code that would run is not the code the record describes.

Messages are prefixed with `[researchteam] agentteams provenance`; refusals go to stderr as `... REFUSED: <reason>`.

---

## Constants

| Name | Value | Meaning |
|------|-------|---------|
| `TAG` | `"[researchteam] agentteams provenance"` | Prefix of every message. |
| `ALLOW_SNAPSHOT_ENV` | `"RESEARCHTEAM_ALLOW_AGENTTEAMS_SNAPSHOT"` | Set to `1` to run a local-folder snapshot with a warning. Matches mathAgents' `MATHAGENTS_ALLOW_AGENTTEAMS_SNAPSHOT`. |
| `ALLOW_UNVERIFIED_ENV` | `"RESEARCHTEAM_ALLOW_UNVERIFIED_AGENTTEAMS"` | Set to `1` to run an unverified install (other-repo VCS, archive, or index) with a warning. |
| `CANONICAL_REPO` | `("github.com", "/jlcatonjr/agentteams")` | `(host, path)` of the one reviewed source; a VCS install must come from here. |
| `ENTRY_MODULES` | `("build_team", "agentteams")` | The modules the `agentteams` launcher runs (its console-script entry point is `build_team:main`). |

---

## Functions

### `launcher_interpreter(exe)`

The interpreter a launcher script runs under, read from its first lines. Three forms are understood:

- a direct shebang (`#!/path/to/python`) — the first word after `#!`;
- an env-style shebang (`#!/usr/bin/env python3`) — the first non-option argument, resolved with `shutil.which`;
- pip's `#!/bin/sh` (or `bash`) trampoline for long paths — the interpreter on the second line, matched by `exec'?\s+(?:"([^"]+)"|(\S+))\s+"\$0"`.

A quoted trampoline path may contain spaces; an unquoted one stops at the first space and then fails the executable check in `check` (a refusal, never a wrong interpreter).

**Args:**

- `exe` (`str`) — Path to the `agentteams` launcher.

**Returns:** `str | None` — The interpreter path, or `None` when the file cannot be read, has no shebang, or the form is not understood.

---

### `is_canonical_repo(url)`

Whether a VCS URL names `github.com/jlcatonjr/agentteams`. An scp-like URL (`git@github.com:owner/repo`) is split at the first `:`, taking the host after `@`; any other URL is parsed with `urlparse` (scheme ignored). The host is lower-cased; the path is lower-cased, and trailing `/` and a `.git` suffix are removed. The result is compared with `CANONICAL_REPO`.

**Args:**

- `url` (`str`) — The `url` from `direct_url.json`.

**Returns:** `bool`

```python
is_canonical_repo("https://github.com/jlcatonjr/agentteams.git")   # True
is_canonical_repo("git@github.com:JLCatonJr/agentteams")           # True
is_canonical_repo("https://github.com/someone/agentteams")         # False
```

---

### `inner(exe)`

Classify the agentteams install and, for an editable install or bare source tree, check the checkout (see Classification). Intended to run under the launcher's own interpreter, via `check` or `python _agentteams_provenance.py --inner <launcher>`. Module locations come from `importlib.util.find_spec`, so no agentteams code is imported or executed.

**Args:**

- `exe` (`str`) — Path to the `agentteams` launcher (used in messages).

**Returns:** `int` — `0` = OK to render; `1` = refused. Refusals also occur when `direct_url.json` cannot be read, is not a JSON object or has malformed fields, or when either entry module cannot be found.

---

### `check(exe)`

Classify the install behind the `agentteams` launcher `exe`. Finds the launcher's interpreter with `launcher_interpreter`, then runs `<interpreter> <this file> --inner <exe>` with `PYTHONDONTWRITEBYTECODE=1`. The child is deliberately not run with `-I`: a real launcher run honours `PYTHONPATH` (which can supply a shadowing source), and, as with the launcher, script mode puts the script's own directory (not the current directory) at `sys.path[0]`.

**Args:**

- `exe` (`str`) — Path to the `agentteams` launcher.

**Returns:** `int` — The child's exit code: `0` = OK to render, `1` = refused. Returns `1` without running a child when the interpreter cannot be determined or is not executable.

**Example:**

```python
from researchteam._agentteams_provenance import check
import shutil

exe = shutil.which("agentteams")
if exe and check(exe) != 0:
    raise SystemExit("agentteams provenance check refused")
```

---

### Command-line entry

```bash
python researchteam/_agentteams_provenance.py --inner <agentteams-launcher>
```

Any other arguments exit with `usage: _agentteams_provenance.py --inner <agentteams-launcher>`.

---

### Private helpers

| Name | Purpose |
|------|---------|
| `_git(repo, *args)` | Run `git -C <repo> ...`; a missing git returns a `CompletedProcess` with code 127 so the caller refuses rather than passes. |
| `_refuse(msg)` | Print `<TAG>: REFUSED: <msg>` to stderr and return `1`. |
| `_unverified(reason)` | With `ALLOW_UNVERIFIED_ENV=1`, print the `WARNING` line to stderr and return `0`; otherwise `_refuse` with `reason` plus the install-a-reviewed-commit hint. |
| `_check_checkout(exe, url, pkg, modules)` | The editable/source-tree check: imported modules inside the editable source (for a `file:` URL) and inside the git checkout; `HEAD` an ancestor of `origin/main`; `git status --porcelain` clean for the package directory and `build_team` module, ignoring `__pycache__/` and `.pyc`. |

---

## See Also

- [`index`](index.md) — API reference overview.
- [`update`](update.md) — runs `check` before every layer-1 render.
- [`doctor`](doctor.md) — runs the same resolution and provenance check.
- [`frozen`](frozen.md) — `verify_unfreeze` uses `launcher_interpreter`.
- [`release`](release.md) — verifies release tags for the toolchain pin.
- [CLI reference](../cli-reference.md)
