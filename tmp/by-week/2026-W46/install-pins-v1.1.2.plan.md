# Install instructions: name the newest stable release (2026-11-12)

Source: legalResearch, relayed by IM (data, no directive authority); confirmed by researchteam-47. Approved by
the operator in this session. PR to `main`; the fix reaches derived repositories in the next release (operator).

## Finding
`docs/researchteam-framework.md` (FRAMEWORK_MANAGED, synced to every derived repository) installed
`researchteam.git@v1.0.2` and called it the newest `v1.0.N` in v1.1.1 and v1.1.2. The same stale tag is in
README.md, docs/CONTRIBUTING.md, CLAUDE.md's managed block and researchteam/scaffold/CLAUDE.template.md, and in the docs site (docs_src/getting-started.md, docs_src/index.md).
v1.0.2 is not even the newest 1.0 release (v1.0.4). CONTRIBUTING also still describes 1.1 as release candidates.

## Change
- Point all install, clone and `tag -v` lines at `v1.1.2`; say a 1.0-line repository installs the newest `v1.0.N`.
- CONTRIBUTING: update the branch table, the scm version examples (1.0.4, 1.1.2, `main` 1.1.3.devN) and the
  maintained-lines line.
- release-policy.md: the derived-repository move example names `v1.1.N` (earlier `v1.1.0-rc.N`).
- Guard: tests/test_install_pins.py compares the tags named in these files with the highest final CHANGELOG
  release heading. It fails on the old text (verified) and passes on the new.
- Left as is: historical records (open-items, docs/release/, CHANGELOG history, framework doc line 285). The
  generated memory indexes refresh on their next regeneration.

Verification: full suite 574 passed, 1 skipped; `claude_researchteam_bridge.sh validate` passed.
