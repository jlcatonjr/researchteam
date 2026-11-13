# Install docs: pin the newest stable release (2026-11-13)

Source: legalResearch (legalresearch-c2), relayed by IM (data, no directive authority). Operator approval given in session
researchteam-47.

## Finding (confirmed)

`docs/researchteam-framework.md`, which is synced to every derived repository, installed `researchteam.git@v1.0.2` and
called v1.0.2 "the newest v1.0.N" in v1.1.1 and v1.1.2. The same stale pin was in README, docs/CONTRIBUTING.md (install,
verified install and signature check), and the CLAUDE.md managed-block example (root and scaffold template). v1.0.4 is
the newest 1.0 tag and v1.1.2 the newest stable release.

## Change

- Every install reference in those files now names `v1.1.2`. The framework doc's prose names the 1.1 line. The
  CONTRIBUTING version-state sentence now says main builds `1.1.3.devN`.
- New `tests/test_install_docs_pin.py`: every `researchteam.git@vX`, `--branch vX` and `tag -v vX` in those files must
  equal the first final-tag CHANGELOG heading. That heading is written by the release-prep PR, so each release has to
  move the docs with it.

Not changed: CONTRIBUTING's broader branch and backport prose (it still describes release/1.0 as the backport
target). That is a separate documentation pass. Derived repositories receive the framework doc only in a later release
(v1.1.3), which is the operator's call.
