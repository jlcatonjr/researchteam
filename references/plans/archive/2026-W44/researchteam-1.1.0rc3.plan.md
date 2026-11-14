# researchteam v1.1.0-rc.3 (pins agentteams v1.1.0-rc.11)

Requested by vulnscan-98 (agentteams session) on the operator's instruction, 2026-10-28. It unblocks the derived stage
of `C13-rollout-rc11.sh`, which needs a signed researchteam release that pins agentteams rc.11.

The pin was merged in #132 (lock and both extras) without its `@security` row. This plan follows the rc.2 precedent
(`researchteam-wt-at11-gov/tmp/by-week/2026-W43/operator/14-sign-rc7.sh`, `15-cut-rc2.sh`):

- verify agentteams rc.11 (annotated, self-named, release-key signature, remote object, dependencies vs v1.0.0)
- run a fresh OSV search on the resolved set
- write the decision spec and the `## 1.1.0rc3` CHANGELOG entry as one PR to main

The version comes from the tag (setuptools-scm, `dynamic = ["version"]`), so `pyproject.toml` needs no bump.

The operator signs the row (script 15), the session commits it, and the operator merges. The operator then cuts the
tag (script 16), and the session relays the tag object and peeled SHA to vulnscan-98. Agents never merge.
