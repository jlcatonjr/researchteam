# P1: the unscrubbed tmp/ originals of the 110 published records (revised)

**State.** The 110 scrubbed copies are on `main` under `references/plans/archive/<week>/` (#162, #163). The
originals are in ignored `tmp/by-week/<week>/`. Keeping them breaks no rule (PS-1 forbids material kept *only*
in an ignored path), so deletion is optional. It needs the operator's S-4 confirmation of the listed paths, and
keeping is the default.

**Steps**
1. Placeholder-diff check. Compare each original with its copy line by line. A line may differ only where the
   copy's version is the original with the substitutions in `archive/README.md` applied. That means all three
   passes: (1) `~`, `<signer>`, `<scratchpad>`, `user@host`, `<email>`; (2) `<release-key-file>` and
   `<decision-key-file>`; (3) `the operator`, `<noreply>` and one pronoun. The `state.env` → `state.vars.txt`
   rename is also allowed. The check script is `open-p1/verify_originals.py`. It loads its literal patterns from
   the ignored `tmp/scrub-patterns.local.json`, so the published script contains none of them. Any other difference sends the file to the keep list. If more than 5
   files fail, stop and report.
2. Manifest. Write `archive/originals-manifest-2026-11-14.csv` with columns `category`, `tmp_path`, `sha256`, `check` and `verdict`.
   It uses relative paths only, and each name is already public in the archive. Never listed as P1: P4's 27 notes (they get their own `P4` row), the P2 seed answer, `tmp/frozen-fences.state.json`, this week's plan working copies, and
   `tmp/signing/`.
3. `@security` and `@cleanup` clearance, then the metaplan's Phase 2 operator ask.
4. Delete only the confirmed paths, by explicit path after a hash check, and update `verdict`.
5. The manifest goes into the metaplan's Phase 4 PR.

**Outcome (2026-11-14).** All 110 match. The Rule 9 `@adversarial` pass found the S-4 ask not worth making:
keeping breaks no rule, and the originals are the only unscrubbed copies. So nothing is deleted, and the
manifest's `verdict` reads `kept (default)`. Deletion can be raised later as an optional, non-blocking item.
