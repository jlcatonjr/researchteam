# External-Dependency Conformance Audit — ResearchTeam Infrastructure

- **Date:** 2026-09-29 (2026-W40)
- **Scope:** ResearchTeam-specific infrastructure — the `researchteam` Python package, CI
  workflows, bridge/validator/gate scripts, packaging metadata, and the update-policy governance
  docs. Research deliverables under `Projects/` are out of scope.
- **Question answered:** Does any ResearchTeam-specific infrastructure need to change to stay in
  conformance with an external dependency, and what should be monitored and remediated?
- **Method:** each on-disk claim below was verified against the file cited; a separate adversarial
  pass recalibrated severities against the rubric and surfaced the enumeration gaps now folded in.

## External dependencies identified

The infrastructure conforms to these external dependencies:

1. **agentteams** — the sibling framework that regenerates layer-1 agent infrastructure. Installed
   from git, not PyPI. The central and most tightly-coupled dependency.
2. **GitHub Actions** — `actions/checkout`, `actions/setup-python`, and
   `peter-evans/create-pull-request`, plus GitHub *repository settings* the workflow relies on.
3. **The Python runtime** — declared floor `>=3.10`; CI runs 3.11.
4. **Pandoc** — the deliverable format-conversion engine named in `brief.json` (an
   agent-workflow dependency, not framework code — see F-2).
5. **GitHub raw/archive HTTP endpoints** — the transport for layer-2 file sync in `_fetch.py`.
6. **Build/VCS toolchain** — `setuptools>=68` ([pyproject.toml:2](../pyproject.toml#L2)) for the
   build, and the `git` binary the autosync gate shells to (`ls-remote`/`show`/`checkout`). Both are
   implicit but load-bearing; listed here for completeness.

**Severity rubric:** likelihood × blast radius *on the framework's own operation*. A finding that
is real but touches only human-facing prose, or fails loudly with a clear cause, is rated below one
that can silently break integration.

## Findings

### F-1 — HIGH — Both frameworks install from a floating git branch (unpinned)

The `[update]`/`[research]` extras declare `agentteams @ git+https://github.com/jlcatonjr/agentteams`
with **no `@ref`** ([pyproject.toml:22,27](../pyproject.toml#L22-L27)), and CI installs *researchteam
itself* unpinned — `pip install "git+https://github.com/jlcatonjr/researchteam.git"`
([agentteams-sync.yml:45](../.github/workflows/agentteams-sync.yml#L45)) — then uses that floating
CLI to run the regen. The CLAUDE.md quick-start installs both the same way. So the tool performing
the integration and the tool being integrated are *both* floating-`main` installs.

- **Why it matters (corrected framing):** the architecture *deliberately* tracks agentteams `main`
  — the autosync gate installs `main` HEAD every week and SHA-pins only to close the ls-remote/pip
  race *within a single run* ([agentteams_autosync_gate.sh:63,89-91](../scripts/agentteams_autosync_gate.sh#L63-L91)),
  not to freeze on a reviewed tag. The residual risk is therefore not "pulls unreviewed HEAD" (CI
  integrates HEAD too, but behind blocking gates). It is that **manual / developer / quick-start
  installs are non-reproducible at a point in time and skip the blocking gates CI runs**, so a
  broken agentteams HEAD breaks local regeneration. agentteams' version string does not move on
  every change (it held `1.0.0rc6` across eight commits, now `1.0.0rc7`), so nothing in the version
  reveals the drift.
- **Monitor:** agentteams `main` for breaking CLI-surface changes; `researchteam doctor`'s
  runnable/ephemeral checks and `--query-code` capability probe are the existing early-warning
  signals ([_doctor_cmd.py:35-87](../researchteam/_doctor_cmd.py#L35-L87)).
- **Remediate:** do **not** freeze the extras to a fixed tag — that would diverge dev installs from
  what CI integrates. Instead document a reproducible post-install pin for dev environments (install
  the exact SHA recorded in `.github/agentteams-autosync-ref`), and consider pinning researchteam's
  own CI install to the release under test.

### F-2 — MEDIUM — Pandoc has no presence/version preflight

`brief.json` sets `conversion_pipeline` to `pandoc --from markdown --to html …`
([brief.json:96](../brief.json#L96)), with a `@tool-pandoc` agent and skill. It is **not** a
framework-code dependency — no Python code shells out to pandoc; the string appears only in a
docstring ([_update_cmd.py:332](../researchteam/_update_cmd.py#L332)) and as inert config the
format-converter agent executes at deliverable time. A missing pandoc therefore fails *loudly and
immediately* (`pandoc: command not found`), not silently — but nothing verifies it *before* a
compile, and no minimum version is declared.

- **Monitor:** pandoc availability and version on machines that compile deliverables.
- **Remediate:** add a pandoc presence/version probe to the format-converter / compile preflight
  (its natural home; `researchteam doctor` is toolchain-integration health, so pandoc is optional
  there).

### F-3 — MEDIUM — The update-policy baseline narrative lags the recorded agentteams ref

`docs/agentteams-update-policy.md` states the *Integrated AgentTeams Baseline* as `61849fb`
(2026-08-15) ([agentteams-update-policy.md:12](../docs/agentteams-update-policy.md#L12)), but the
machine record, `.github/agentteams-autosync-ref`, holds
`f3a8b8c0a489ab87dfc432531479291952dc29d3`, `build-log.json` records `agentteams_version: 1.0.0rc7`,
and commit `eaae749` integrated agentteams rc7 (`386f983` is the work-summary capturing it, not
itself an integration). The prose baseline lags the actual dependency state by a full release.

- **Blast radius is low** — CI reads `.github/agentteams-autosync-ref`, not the prose, so no code
  consumes the stale narrative — which is why this is Medium, not High. But it is the most direct
  *documentation*-conformance gap and cheap to fix, and the doc itself records that its baseline had
  lagged before (the five-week figure in that doc belongs to CI silently discarding PRs, a distinct
  incident, not to the narrative-lag duration).
- **Monitor:** divergence between the *Integrated ref* prose and `.github/agentteams-autosync-ref`.
- **Remediate:** refresh the baseline to the recorded SHA/rc7, and consider generating that line
  from `agentteams-autosync-ref` so prose cannot drift again.

### F-4 — MEDIUM — GitHub Actions pinned to mutable major tags

The workflow uses `actions/checkout@v4`, `actions/setup-python@v5`, and
`peter-evans/create-pull-request@v6` ([agentteams-sync.yml:33,38,70](../.github/workflows/agentteams-sync.yml#L33-L70)).
These are mutable major tags, not commit SHAs, so a republished tag changes behavior silently. The
third-party `create-pull-request` is the higher-risk one; its current upstream major is unverified
here and should be checked before any bump.

- **Monitor:** new majors and security advisories for the three actions.
- **Remediate:** SHA-pin the third-party action at minimum; first-party `actions/*` tags are
  lower-risk.

### F-5 — MEDIUM — The autosync path has two silent single-points-of-failure

The weekly autosync depends on external state that can fail invisibly, in two distinct ways that
share one fingerprint (a week that integrates nothing):

1. **A GitHub repository setting.** The policy doc records that autosync produced correct
   integrations and silently discarded every one for five straight weeks because
   `can_approve_pull_request_reviews` was off, blocking Actions from opening PRs
   ([agentteams-update-policy.md:14-21](../docs/agentteams-update-policy.md#L14-L21)). The code
   cannot see this setting, and it can regress again.
2. **The SHA-gate fails open.** If `git ls-remote` to agentteams returns empty — a network blip, or
   the repo being renamed/moved/made private — the gate emits `changed=false; exit 0`, a silent
   no-op rather than an error ([agentteams_autosync_gate.sh:64-67](../scripts/agentteams_autosync_gate.sh#L64-L67)).

- **Monitor:** any week the gate reports `changed=false` while agentteams `main` has in fact
  advanced; any run reporting a change that opens no PR.
- **Remediate:** alert on "change but no PR"; make `ls-remote` failure a warning, not a silent
  success.

### F-6 — MEDIUM — Declared Python floor `>=3.10` is untested and nears end-of-life

`requires-python = ">=3.10"` ([pyproject.toml:10](../pyproject.toml#L10)) while CI pins a single
`python-version: "3.11"` ([agentteams-sync.yml:40](../.github/workflows/agentteams-sync.yml#L40)),
so 3.10, 3.12, and 3.13 are asserted-compatible but never exercised. The floor is genuinely
load-bearing, not arbitrary: the package uses `X | None` union-type annotations evaluated at
definition time (e.g. [_doctor_cmd.py:159](../researchteam/_doctor_cmd.py#L159)), which require
3.10+. CPython 3.10 reaches end-of-life in October 2026.

- **Monitor:** the 3.10 EOL date; new CPython releases against the floor.
- **Remediate:** add a CI version matrix (3.10 + latest); decide whether to raise the floor once
  3.10 retires.

### F-7 — MEDIUM — Standing watch: agentteams' constitutional red-team battery is not integrated

The policy doc excludes agentteams' `--redteam` audit and its C-5 enforcement work because, **as of
2026-08-07**, that upstream branch failed its own `tests/test_constitutional_redteam.py` (probe E3:
`C-5 has no mechanical enforcement for agent-initiated destruction` measured `EXPLOITED`)
([agentteams-update-policy.md:77-83](../docs/agentteams-update-policy.md#L77-L83)). As of that
snapshot, ResearchTeam's Constitutional Core C-5 ("Clearance precedes destruction") had no
mechanical enforcement behind it upstream; the current status has not been re-verified in this
audit.

- **Monitor:** the upstream red-team branch and that test battery.
- **Remediate:** re-verify upstream status; integrate once the battery is green on `main`, then
  re-run the local validate + detector gates.

### F-8 — LOW — Neither framework is on PyPI, so operation needs git + network + build toolchain

By design the base install is dependency-free and both frameworks install from git
([pyproject.toml:12-27](../pyproject.toml#L12-L27)). Layer-1 regeneration, `researchteam update`'s
agent pass, and `code-query` all require the agentteams repository to be reachable and buildable
(`setuptools>=68`, the `git` binary). If either repo is renamed, moved, or made private, these
break; `researchteam doctor` diagnoses the resulting failure.

- **Monitor:** agentteams/researchteam repository URL and visibility.
- **Remediate:** none needed now — the trade-off is deliberate and documented.

### F-9 — LOW — Layer-2 fetch is single-attempt against hardcoded endpoints, with an unwrapped fallback

`_fetch.py` hardcodes `raw.githubusercontent.com` and `github.com/.../archive` with fixed 20s/60s
timeouts and no retry/backoff ([_fetch.py:6-37](../researchteam/_fetch.py#L6-L37)). A transient blip
fails a sync file individually (errors are collected, not fatal). Two smaller edges: a change to
GitHub's raw-URL scheme would break sync wholesale, and the tags-archive *fallback* `urlopen`
([_fetch.py:34-36](../researchteam/_fetch.py#L34-L36)) is not wrapped in the friendly `RuntimeError`
the primary path uses, so a failure there surfaces a raw urllib error.

- **Monitor:** GitHub raw/archive endpoint stability and URL-scheme announcements.
- **Remediate:** optional — one retry with backoff; wrap the fallback `urlopen`. Low urgency.

## Summary table

| ID  | Area | Issue | Severity | Primary remediation |
|-----|------|-------|----------|---------------------|
| F-1 | agentteams / researchteam | Both install from a floating git branch; manual installs non-reproducible + ungated | High | Document a reproducible dev pin (record SHA), not a frozen tag |
| F-2 | Pandoc | No presence/version preflight | Medium | Add pandoc probe to the compile preflight |
| F-3 | docs | Policy baseline narrative lags recorded ref (rc7) | Medium | Refresh + auto-generate the baseline line |
| F-4 | CI | Actions on mutable major tags | Medium | SHA-pin the third-party action |
| F-5 | CI / GitHub | Autosync fails silently two ways (repo setting; ls-remote fails open) | Medium | Alert on change-but-no-PR; warn on ls-remote failure |
| F-6 | Python | Floor `>=3.10` untested; 3.10 EOL Oct 2026 | Medium | Add a CI version matrix |
| F-7 | agentteams | Red-team/C-5 enforcement not yet integrated | Medium | Re-verify; integrate when green upstream |
| F-8 | agentteams / researchteam | Git-only install; needs git + network + build toolchain | Low | None (documented trade-off) |
| F-9 | fetch | Single-attempt hardcoded endpoints; unwrapped fallback | Low | Optional retry/backoff; wrap fallback |

## Recommended monitoring cadence

- **Weekly (already automated):** the autosync SHA-gate tracks agentteams `main`. Add F-5's
  "change-but-no-PR" and "ls-remote-failed" alerts to this run.
- **On every agentteams integration:** refresh F-3's baseline narrative (or generate it).
- **Continuously / on upstream activity:** watch F-7's agentteams red-team branch; integrate when
  its test battery is green.
- **Quarterly:** review F-4 action versions and F-6 Python-version support against upstream EOL.
- **Before any deliverable compile:** confirm F-2 (pandoc present and current).
