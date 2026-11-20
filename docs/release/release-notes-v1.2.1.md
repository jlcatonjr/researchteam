Patch release on the 1.2 line. Still pins agentteams v1.2.1 (a7ab95e2); the pin does not move in this release.

- **Fix: verifying a release tag no longer downloads the pinned repository's history.** `check_toolchain.py --write-lock` and `--verify-tag` (and so `researchteam update` on a release-locked pin) fetched the tag with the repository's full history under a 300-second limit. On a slow link that timed out, and the lock could not be written. The check now fetches only the tag object and the commit it names. Everything it verifies is unchanged: an annotated tag, the fetched object equal to the advertised one, a good signature from a release key, and the peeled commit.
- **Docs: the pin-move record in a workspace without decision signing (#213).** `docs/agentteams-update-policy.md` now names both kinds of workspace where a first-party member's release needs no decision-log row, and says what verifies the tag where there is no toolchain-group file. No rule changes.

**Moving a derived repository:** install the release first, because the lock writer runs the installed code: `pip install "git+https://github.com/jlcatonjr/researchteam.git@v1.2.1"`. Then `researchteam update --ref v1.2.1`, then `python3 scripts/check_toolchain.py --write-lock --tag researchteam=v1.2.1 --tag agentteams=<the v1.2.N it uses>`. It is a same-line move, so no tag line is dropped from `toolchain.lock`.

Not in this release: a move of researchteam's own agentteams pin to a later v1.2.N, and the same shallow fetch in the derived autosync workflow (#228). Full list: `CHANGELOG.md`.
