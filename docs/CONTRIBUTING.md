# Working with researchteam: branches, releases and contributions

**For:** collaborators: Kevin Vallier (`@selfreferencing`), John Schuler (`@jsschuler`) and anyone else contributing.
The binding rules are in [`docs/release-policy.md`](release-policy.md); this guide explains how to work within them. agentteams, researchteam, mathAgents
and baseAgent all follow the same model, so what you learn here applies to all four.

## The model in brief

- **`main`** is where development happens. Every change, fixes included, lands there first, through a pull request.
- **Releases are signed tags,** `v1.0.0`, `v1.0.1`, …, and they are what users install and pin.
- **`release/1.0`** collects the reviewed fixes for the next patch release. It changes only when Jim copies in a fix
  that is already on `main` (a *backport*). Between tags its commits are unsigned, so it is not for installing or
  pinning.
- **Each tag is cut on `release/1.0`** and signed by Jim. After each tag, `release/1.0` is merged back into `main`.
- **The next minor version gets its own branch.** `release/1.1` will be cut from `main` at its first release
  candidate.

## Branches and tags

| Ref | What it is | Who changes it |
|---|---|---|
| `main` | Development, the next minor version | Anyone, through a pull request |
| `release/1.0` | Reviewed fixes queued for the next patch release; unsigned between tags; not for pinning | Jim only, by backport |
| `vX.Y.Z`, `vX.Y.Z-rc.N` | One exact release, signed by Jim, never moved; what you install and pin | Jim only |
| Your work branch (`feat/…`, `fix/…`, `docs/…`, `chore/…`) | One change, deleted after merge | Its author |

researchteam takes its version from git tags (setuptools-scm), and has no version file. `release/1.0` builds `1.0.0` at the `v1.0.0` tag. `main` builds `1.0.1.devN` until a `v1.1.0` tag exists. That is scm's default, explained in the release policy, and it doesn't mean `main` is a 1.0 patch.

**Older lines:** none. The 1.0 line is the first maintained line.

The name `release/<X.Y>` is reserved for maintained lines. Never create a `release/*` branch, locally or on GitHub.

## Using researchteam

Install a signed release tag: `v1.0.0`, and later `v1.0.N`.

```bash
pip install "researchteam @ git+https://github.com/jlcatonjr/researchteam.git@v1.0.0"
```

**Verified install,** for a governed team, an experiment or a paper. Clone the tag into a directory of its own, check its signature with repository config neutralised, then install from that checkout:

```bash
git clone --branch v1.0.0 https://github.com/jlcatonjr/researchteam.git researchteam-v1.0.0
cd researchteam-v1.0.0
git -c gpg.format=ssh -c gpg.ssh.program=/usr/bin/ssh-keygen \
    -c gpg.ssh.allowedSignersFile=$HOME/.config/agentteams/allowed_signers \
    -c gpg.program=/usr/bin/gpg -c core.fsmonitor=false -c core.hooksPath=/dev/null \
    tag -v v1.0.0 && pip install .
```

The `&&` stops the install if the signature check fails. The output must also show the release key's full fingerprint, which begins `SHA256:IPdnLwlF`, not just "Good signature"; if it doesn't, stop and uninstall. "Verifying a release" below explains how to set up `allowed_signers` once. For a patch release, repeat this with the new tag in a new directory.

Then run `researchteam init <project>` or `researchteam update`, as the README explains.

**`release/1.0` is not an install source.** It holds reviewed fixes queued for the next patch release. Those commits are unsigned between tags, so don't install from the branch or pin it.

**For development,** work on `main` in a clone of your fork, and install it with `pip install -e .`. "Contributing a change" below covers setting up the fork.

**Pins between repositories** (`toolchain.lock`, pinned extras) always name the commit of a verified signed tag, never
a branch.

## Contributing a change

researchteam is public, and you have read access only. Contribute from a fork; Jim reviews and merges your pull request.

1. **Set up once.** Fork the repository on GitHub, then clone your fork and add the original as `upstream`:

   ```bash
   git clone https://github.com/<your-login>/researchteam.git && cd researchteam
   git remote add upstream https://github.com/jlcatonjr/researchteam.git
   ```

2. **Start each change from an up-to-date `main`:**

   ```bash
   git switch main && git pull --ff-only upstream main
   ```

3. **Branch:** `git switch -c fix/<short-topic>`. Use `feat/`, `fix/`, `docs/` or `chore/`. Keep one change per
   branch.
4. **Push to your fork and open a pull request** against `jlcatonjr/researchteam` `main`:

   ```bash
   git push -u origin fix/<short-topic>
   ```

5. **CI.** `tests.yml` runs on every pull request to `main` and must pass. Before you push, run `python -m pytest -q tests`.
6. **Merge.** Jim reviews and merges. You can't merge into this repository.
7. **Delete your branch after it merges.**

## Getting a fix into a release

1. **Land the fix on `main` first,** as above.
2. **Ask for a backport.** On the merged pull request, add the label `needs-backport-1.0`. If you can't add labels,
   leave a comment instead: "please backport to 1.0". Either way, say why. Only these qualify:
   - security fixes;
   - correctness fixes;
   - documentation fixes.

   New features wait for the next minor release.
3. **Jim does the rest.** He copies the fix to `release/1.0` in his own pull request, labelled `backport-1.0`, using
   `git cherry-pick -x` and never a squash. When he releases, he signs `v1.0.N`.
4. **Urgent?** Say so in the pull request and message Jim.

## What only Jim does

- Pushing or merging to any `release/*` branch.
- Creating a `release/*` branch.
- Creating, moving or deleting tags.
- Signing a release.
- Moving a cross-repository pin.
- Signed decision rows and the security-decision logs.
- Re-enabling autosync.

If you work through this repository's agent team (Claude, Copilot, Codex or Goose), the agents will stop and ask
before any of these actions. In your own session, they are asking *you*: answer no, and contact Jim.

## Please don't

- Commit straight to `main` or `release/*`. Use a branch and a pull request.
- Force-push `main` or `release/*`, or delete or move a tag. A defect is fixed forward, in a new patch release.
- Put a branch name into `toolchain.lock` or a pinned extra.

## Enforcement

Nothing enforces the rules yet. The repository is public, but it has no rulesets, so the rules in this guide are procedural for now. Jim plans to apply the same release rulesets agentteams uses.

## How a release happens

You only need this for context:

1. **Fixes accumulate.** They land on `main`, and the ones requested for backport are copied to `release/1.0`.
2. **Jim releases.** He signs the tag `vX.Y.Z` on `release/1.0` from his own terminal. The version comes from the tag, so there is no version file to bump. Then he publishes the GitHub release and merges `release/1.0` forward into `main`.
3. **Repositories release in order:** agentteams → researchteam → mathAgents → baseAgent. Each one moves its pins only
   after verifying the upstream tag's signature.
4. **Next minor.** When `1.1` reaches its first release candidate, Jim cuts `release/1.1` from `main`. From then on,
   `release/1.0` takes fixes only on request, and installs move to the `v1.1.N` tags.

## Verifying a release

Each tag is SSH-signed with Jim's release key. Its fingerprint begins `SHA256:IPdnLwlF`; the full fingerprint and the
`allowed_signers` line are in agentteams `SECURITY.md`, under "Release signers". Read them on GitHub, not from a
copy inside the repository you are checking, or confirm the fingerprint with Jim.

1. On your own machine, add that line to your own `~/.config/agentteams/allowed_signers`. (Agents never write this
   file; it's yours.)
2. Run this from a checkout of the tag (the verified install above does this for you):

   ```bash
   git -c gpg.format=ssh -c gpg.ssh.program=/usr/bin/ssh-keygen \
       -c gpg.ssh.allowedSignersFile=$HOME/.config/agentteams/allowed_signers \
       -c gpg.program=/usr/bin/gpg -c core.fsmonitor=false -c core.hooksPath=/dev/null \
       tag -v v1.0.0
   ```

3. Check that the output shows the full fingerprint from `SECURITY.md`, not just "Good signature".

## Notes for researchteam

- **researchteam is pinned to agentteams** through `toolchain.lock`. That pin moves only to a verified agentteams tag, and only Jim moves it.
- **Downstream use.** mathAgents pins researchteam the same way, by a verified tag's commit.
- **Autosync is paused.** The weekly `agentteams-sync.yml` is disabled until researchteam v1.0.1 ships the frozen-surfaces fix.

## Questions

Open an issue, or ask Jim directly.
