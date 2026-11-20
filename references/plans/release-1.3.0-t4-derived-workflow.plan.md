# T4: the derived autosync workflow scaffold (version 2, 2026-11-20, revised after audit)

Target of `release-1.3.0.metaplan.md`. Covers F10 (issue #228) and closes F11's issue (#176). One file,
`researchteam/scaffold/agentteams-sync-derived.yml`. Needs nothing from agentteams 1.3.0.

1. **F11 is already on `main`.** Both checkout steps set `persist-credentials: false`, tests assert it, and the
   push job has its own credentials since the job split. Read issue #176 against the file; if nothing it asks
   for is missing, close it with that evidence. If something is missing, it joins step 2.
2. **F10.** The release-locked check fetches the tag with `--depth=1 --filter=tree:0` and retries once with
   `--depth=1`, as `researchteam/_release.py` `verify_tag` does. A fetch that fails both ways fails the check
   (fail closed). Every check after the fetch is unchanged. No token is written into a remote URL or
   `.git/config`.
3. **Tests:** the scaffold's existing tests, plus assertions that pin the fetch arguments and the failure path.
4. **Review:** `@security` PASS naming the scaffold path (a derived repository installs it under
   `.github/workflows/`); `@code-hygiene`.
5. **Delivery:** a derived repository receives the file only through its own sync and review. The release
   notes say so. If the PR also touches this repository's own workflow, the `@security` PASS names
   `.github/workflows/` too.

Done when #228 is closed by a merged PR, #176 is closed with evidence, and the notes carry the delivery
sentence.
