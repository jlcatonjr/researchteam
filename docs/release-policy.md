# researchteam Release Policy (1.x)

researchteam adopts the **shared v1.0.0 release policy** of agentteams, researchteam, mathAgents and
baseAgent. The operator recorded this as decision `release-policy-1.0`, and the policy's text lives in
agentteams' `tmp/by-week/2026-W42/v1.0.0-shared-release-policy.md`. This page states it for researchteam.
researchteam may add rules to it but may not weaken it.

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
- Once `v1.0.0` is tagged, `main` builds `1.0.1.devN` until a `v1.1.0` tag is cut. setuptools-scm's guess-next-dev
  replaces the hand-set `1.1.0.dev0` of the shared policy.

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
- Each pin move gets its own `@security` row naming the tag object and the peeled SHA.
- **S-10:** a release-key tag that verifies is exempt from the 14-day cooldown. Third-party packages that
  resolve at install keep the cooldown and the OSV/GHSA search (`docs/release/`).
- `check_toolchain.py` fails when an extra and the lock disagree.

## Autosync and Layer 2
- During the joint cut, the weekly `agentteams-sync` schedule is disabled (`gh workflow disable`), and
  soak syncs are operator-dispatched with `force=true`. It is re-enabled once all four `v1.0.0` tags exist.
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

## Operator-only actions
Signing tags; installing `allowed_signers` and verify keys; the signed decision rows; merges that name the
head SHA; the go/no-go. The scripts in `tmp/by-week/2026-W42/operator/` (local, not committed) carry these
out for the 1.0 cut.
