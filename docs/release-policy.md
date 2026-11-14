# researchteam Release Policy (1.x)

researchteam adopts the **shared v1.0.0 release policy** of agentteams, researchteam, mathAgents and
baseAgent. The operator recorded this as decision `release-policy-1.0`, and the policy's text lives in
agentteams' `tmp/by-week/2026-W42/v1.0.0-shared-release-policy.md`. This page states it for researchteam.
researchteam may add rules to it but may not weaken it.

How collaborators work within this policy (branches, installs, contributions, backports): [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Versions and branches
- SemVer. researchteam 1.x supports agentteams 1.x.
- The version comes from the tag (setuptools-scm): `v1.0.0-rc.1` builds `1.0.0rc1`, and `v1.0.0` builds
  `1.0.0`. Between tags, a build reports the next version as `.devN`, so there is no version file to bump.
- `main` is the trunk, and every fix lands on `main` first.
- `release/1.0` is cut at `1.0.0rc1`. After that it takes **selected fixes only**, already merged to `main`,
  through a regular merge or a `git cherry-pick -x` PR. It never takes a squash, so each backport keeps
  its link to the `main` commit.
- RC and final tags (`v1.0.0-rc.N`, `v1.0.0`, `v1.0.N`) are cut and signed **on `release/1.0` only**.
- After each tag, `release/1.0` is merged forward into `main` with a regular merge, so `main` always
  contains every tagged commit.
- After each tag is merged forward, `main` builds the next version's `.devN` from its nearest tag. With `v1.1.0-rc.N`
  on `main` that is `1.1.0rc(N+1).devN`; at the `v1.1.0-rc.2` commit itself it builds `1.1.0rc2`. setuptools-scm's guess-next-dev
  replaces the hand-set `1.1.0.dev0` of the shared policy.

### The 1.1 line
- researchteam 1.1 pins agentteams 1.1. `release/1.1` is cut from `main` at `1.1.0rc1`, after the agentteams 1.1 pin
  has merged to `main`. The 1.1 RC and final tags (`v1.1.0-rc.N`, `v1.1.0`, `v1.1.N`) are cut and signed **on
  `release/1.1` only**, and each tag is merged forward into `main` as above.
- `release/1.0` stays open for `v1.0.N` backports and keeps its own tags; it does not move to agentteams 1.1.
- Moving `toolchain.lock` from the 1.0 line to the 1.1 line is a trust change with its own `@security` row
  (`release-line-agentteams-1.1`), separate from the pin row. `check_toolchain.py` refuses a cross-line move under
  an existing lock, so the move drops the `agentteams.tag=` line and starts a new lock with
  `--write-lock --tag agentteams=<1.1 tag> --sync-extras`.
- The S-10 cooldown is in force again, with a carve-out for this toolchain's own repositories (see Pins). The
  release-key exemptions from before the 2026-10-26 deprecation (`s10-release-key-exemption`,
  `s10-release-key-exemption-1.1`) stay in the log as history; the local-lineage carve-out replaces them.
- Derived repositories move to 1.1 only by pinning a verified researchteam 1.1 tag
  (`--researchteam-tag v1.1.0-rc.N`), which keeps the order agentteams → researchteam → derived.

## Tags
- Annotated tags, **SSH-signed by the operator** with the agentteams release key, RSA
  `SHA256:IPdnLwlFdHNhr7QGKVWU40BOKyYzv2u8qxP/qxnzTNM` (agentteams SECURITY.md "Release signers"),
  from a plain terminal. No agent signs a tag.
- Consumers verify against `~/.config/agentteams/allowed_signers` with repository config neutralised.
  `researchteam/_release.py` does this, and also neutralises global and system git config.
- Tags are immutable. A defect is fixed forward with a new patch tag.

## Pins
- Every cross-repository pin (`toolchain.lock`, the pip extras) is the **peeled commit of a verified signed
  tag**, never a branch, a branch head or an unverified tag. A `<name>.tag=` line in `toolchain.lock` records
  the tag and release-locks the pin (`docs/agentteams-update-policy.md`, "Release-Locked Repositories").
- Each pin move gets its own `@security` row naming the tag object and the peeled SHA, except for the moves
  below.
- **Exception: first-party toolchain group members** (operator rulings T2 and R9, 2026-W46, and R16, confirmed
  by the operator in this repository's session on 2026-11-14). It covers only the repositories listed in
  `.agentteams/toolchain-group.json`, which today are agentteams, researchteam, baseAgent and mathAgents, and only
  while that operator-signed file verifies. A pin move to a member's release needs no decision-log row. Instead it
  needs:
  - a verified signed tag;
  - this repository's own `@security` review, recorded in the pin-move PR, naming the tag object and the peeled
    SHA and recording the S-10 known-vulnerability search;
  - the latest-stable rule, which still applies.

  The exception ends when the group file stops verifying, when its key is removed from the verify-key store, or
  on an unretracted HALT on `s10-toolchain-group`. Member moves then need their own rows again.
  `agentteams --verify-toolchain-pin` checks every group pin against the file. A tracked decision spec in
  `docs/release/` (for example `pin-agentteams-v1.1.3.decision-spec.json`) is the lasting copy of the review,
  because a PR body can be edited after the fact.
- **S-10:** the 14-day release cooldown is **in force** (operator ruling 2026-11-03, reversing the 2026-10-26
  deprecation `s10-release-cooldown-deprecated`; agentteams #349/#350 restore it in the rendered `@security`). Two
  carve-outs:
  - **Vulnerability remediation.** A release that fixes a vulnerability found by `pip-audit`, `npm audit`,
    `cargo audit` or an OSV.dev query may be adopted inside the cooldown.
  - **First-party toolchain group.** The cooldown does not apply to releases of the repositories the
    operator-signed `.agentteams/toolchain-group.json` lists (agentteams, researchteam, baseAgent, mathAgents), in
    the workspaces it lists. Until it lapses on 2027-02-01, the legacy `s10-cooldown-exempt:jlcatonjr/agentteams`
    entry also covers agentteams. Such a release-key tag may be adopted the day it is published once it passes the
    signature and remote-object checks (`agentteams --verify-toolchain-pin`), and its exact `name==version`, and
    any dependency it changes, passes the known-vulnerability search (OSV/GHSA, including MAL-* entries).
  Every pin move records that search in its row or, for a group-member move, in the PR's `@security` review. Third-party packages wait out the cooldown unless the
  remediation carve-out applies.
- `check_toolchain.py` fails when an extra and the lock disagree. In researchteam itself the upstream autosync
  moves them together (`--write-lock --sync-extras`); a derived repository's `pyproject.toml` is never rewritten.

## Autosync and Layer 2
- During the joint cut, the weekly `agentteams-sync` schedule is disabled (`gh workflow disable`), and
  soak syncs are operator-dispatched with `force=true`. Under shared-policy draft 9 (operator ruling 2026-10-18) it stays disabled until researchteam v1.0.1 is tagged
  and consumers pin it.
- Under a release lock, the gate follows verified tags on the line and never `main`. Derived repositories
  sync Layer 2 from the verified researchteam tag named in their lock.

## Codex (#210)
- **Frozen Codex (shared policy §5, draft 6).** agentteams 1.0 supports `write_policy` interop for claude and
  goose only. A repository whose roster includes adopted (bespoke) agents therefore keeps its Codex surface
  **frozen** for 1.0 (`researchteam update --no-codex`). Orchestrator-only applies to agentteams-rendered
  Codex teams; Codex interop arrives as a 1.0.x backport. researchteam's own Codex is native and
  orchestrator-only.
- **The upstream self-pin is advisory.** In researchteam's own `toolchain.lock`, the `researchteam=` line
  records the release commit the repo was last verified with. It carries no `researchteam.tag`, because the
  upstream autosync installs `main` editable and would refuse to rewrite a locked self-pin. Derived repos
  pin researchteam to a verified tag.
- Codex and Codex `AGENTS.md` are **orchestrator-only**, recorded in an Ed25519-signed decision row. A
  cooperative opt-in is not part of 1.0.

## Operator-only and delegated actions
Signing tags; installing `allowed_signers` and verify keys; the signed decision rows; the go/no-go. The
scripts that carried these out for the 1.0 cut are archived as records in
`references/plans/archive/2026-W42/operator/`.

**Merges are delegated (rule PS-2, operator ruling 2026-11-14).** The agent session merges PRs, as long as:
- the merge names the reviewed head SHA (`gh pr merge --match-head-commit <sha>`);
- CI is green on that head;
- every review the change needs (`@security`, `@code-hygiene` for code, `@conflict-auditor`) is recorded in the
  PR;
- no HALT or unmet condition stands.

PS-2 in `.claude/CLAUDE.md` is the authority on what is delegated and what is excluded. It excludes force-pushes
and history rewrites, `--admin` merges, changes to settings, secrets, collaborators or branch protection,
executor-opened remediation PRs (S-VM), and writes to other repositories. Its deletion rules (S-4,
`branch-delete`) also apply.

Releases still need an operator-signed tag, so the agent prepares the tag command and the operator signs it.
