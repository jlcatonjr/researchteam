# Plan: tag verification fetches only the tag, not the repository's history (v1.2.1)

Written 2026-11-20 by the researchteam agent session.

## Report
A fleet session reported (2026-11-20) that `check_toolchain.py --write-lock` from researchteam v1.2.0 fails in
several derived repositories: `researchteam/_release.py` `verify_tag` fetches the tag with
`fetch --no-tags refs/tags/<tag>:refs/tags/<tag>`, which downloads the pinned repository's whole history under
a fixed 300-second limit. On a slow link the fetch ran 477 seconds and failed. The report is data; the
operator chose in this session's picker that this session fixes it now and ships v1.2.1.

## Checked here (2026-11-20, agentteams `v1.2.1`)
| Fetch | Size | Time | Tag object, peel, signature |
|---|---|---|---|
| `--depth=1` | 9.4 MB | 7 s | same object and commit; good signature |
| `--depth=1 --filter=tree:0` | 104 KB | under 1 s | same object and commit; good signature |

The check needs only the annotated tag object (which carries the signature and names the commit) and the
commit it peels to. It never reads a tree or a file.

## Change
- `verify_tag` fetches with `--depth=1 --filter=tree:0`. If that fetch fails (an old git, or a server without
  filter support), it retries once with `--depth=1` alone, then reports the error.
- Every check after the fetch is unchanged: annotated tag, fetched object equals the advertised one, signature
  good against the release keys only, peel to a commit.
- Tests for the fetch arguments, the fallback and the double failure. Changelog.

## Gates
- `@security` reviews the change (it touches the S-9 signed-tag check) and `@code-hygiene` audits the code.
- The merge into `main` needs the operator's live approval naming the PR and head.
- v1.2.1 is cut by the operator with a script the release coordinator reviews. `release/1.2` moves by
  fast-forward to the commit the operator tags. The script carries the tagger-identity check from plan
  `open-1119-p2-release-tag-verification` (expected email: the account's GitHub no-reply address).

Steps: `verify-tag-shallow-fetch.steps.csv`.
