# T2: term-index core switch (version 1, 2026-11-20, written with the audit's findings)

Target of `release-1.3.0.metaplan.md`. Covers F2, F3, F4 and F5. It replaces phases 1 and 2 of
`open-1119-p1-term-index-core-switch` (phase 0 there is done). Still binding: the design note
`open-1119-p1-copy-integrity-design.md` (section 10 wins where it differs) and the seam table
`open-1119-p1-seam-table.md`. The upstream work is agentteams issue #548, first PR #551.

The term index's behaviour does not change. Until the switch has shipped, it takes bug fixes only.

1. **Rehearsal (can start after D2).** Build the swap against agentteams `dev` on a draft branch, after a
   recorded `@security` clearance naming the `dev` commit. The manifest is marked provisional. The network
   comparison is expected to be skipped or to fail there, because only a signed tag can satisfy it. The branch
   is never merged and goes to `archive/` after the final.
2. **Re-check at the tag (after T1).** The whole of the design note's section 8 against the signed `v1.3.0`.
3. **Swap PR.** Copy the core as bytes into `scripts/term-index-core/`; rebuild the manifest from the signed
   tag (nothing provisional carries over); reduce the engine to adapters; loader and import shim as in
   section 10 points 5 to 7; the reader for `researchteam-term-register`; the offline check; the doctor
   report; byte-exact layer-2 sync and `.gitattributes`; the upgrade-first message for an older installed
   researchteam. Proof: the characterization tests, the existing term-index tests, `term-check` on every
   project, and the network comparison. `@code-hygiene` and `@security`. Each move of the core pin is an S-10
   adoption: a vulnerability search at the tag and a recorded `@security` clearance for the beta module.
4. **CI job** that runs the network comparison on every pull request touching `scripts/term-index-core/**`
   (design note, section 10 point 4). It is a change under `.github/workflows/`, so its `@security` PASS names
   that path. Its own PR, or part of step 3's with the PASS naming both.
5. **PS-2 path list** (only if D4 says so): add `scripts/term-index-core/` to the paths that need a
   `@security` PASS. Its own PR on `.claude/CLAUDE.md` and its projected copies; `@security` names them. It
   takes its turn with PR #234 and T1 (metaplan, section 3).
6. **Private imports (F5).** Replace the two in `researchteam/_frozen.py` if agentteams 1.3.0 exports public
   equivalents; otherwise keep them and record why.
7. **Docs (F4).** `docs/term-index-protocol.md`: "Planned placement" becomes the placement as built; the
   layering rule. The lead writes the changelog entry, not this track.

Done when the swap, the check and the CI job are merged, every proof in step 3 is green on `main`, and the
manifest names the lock's agentteams commit.
