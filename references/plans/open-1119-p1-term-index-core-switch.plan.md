# P1: term-index core switch (researchteam 1.3.0, pinned to agentteams 1.3)

Written 2026-11-19 by the researchteam agent session, for the agent that takes this over.

## Goal
Replace the generic half of `scripts/term_index_engine.py` with a byte-identical copy of agentteams' public
term-index module, keep the research adapters here, and ship that as researchteam 1.3.0.

## Rulings and sources (do not re-decide)
- "Core in agentteams 1.3" (operator, 2026-11-16) and "the switch moves to researchteam 1.3.0" (operator,
  2026-11-19): `docs/term-index-protocol.md`, "Planned placement".
- Design: option C of the fleet coordinator's placement report (a sha256-pinned copy, so the base install needs
  no agentteams). The upstream work is agentteams issue #548.
- Until the switch, the term index takes bug fixes only, and nothing is renamed.

## State on 2026-11-19 (checked)
- agentteams: latest release `v1.2.1`. `agentteams/term_index.py` does not exist on `dev`. Issue #548 is open.
- researchteam: `main` at `db5cdfd`, pinned to agentteams `v1.2.1`. Engine: 674 lines; build, check and query
  scripts; `tests/test_term_index.py` (1,001 lines).
- `researchteam/_frozen.py` imports two private agentteams symbols (`_latest_security_decision`,
  `_latest_security_waiver`) from `agentteams.cli.security_gate`.

## Update, 2026-11-20
- Phase 0 is done; see the step file. The state above is out of date in one point: `agentteams/term_index.py`
  now exists on agentteams `dev` (read at `b4b732f`, unreleased), with a private helper `agentteams/_term_text.py`.
- Phase 1 starts from `open-1119-p1-seam-table.md` and `open-1119-p1-copy-integrity-design.md`. Section 8 of
  the design note lists what to re-check against the signed 1.3.x tag, and section 10 binds phase 1.
- The request to the agentteams lane (single-file or shim-free core, three small gaps, public equivalents of
  two private symbols) is drafted in the seam table and was held by the operator's choice. It is not sent.

## Phase 0: preparation that needs no agentteams 1.3 (start now)
0.1 **Seam map.** A function-level table of `term_index_engine.py`: core or adapter, and for each adapter point
    the parameter the core must offer (scope root, discovery, pruned directories, skip-heading patterns, source
    validator, generator and schema names, messages). Compare it with the parameter list in agentteams #548.
    Send any gap to the agentteams lane through the fleet coordinator, by message, together with one request
    the copy design depends on: the upstream module must be a **single file that imports only the standard
    library**. No write to another repository.
0.2 **Characterization tests.** First take stock: `tests/test_term_index.py` already asserts many bytes, hashes
    and gate codes. List what it covers and add tests only for the gaps, in a new file
    (`tests/test_term_index_characterization.py`). Mark each assertion as **invariant** (matches, occurrences,
    gate codes, exit codes) or **allowed to change at the swap** (generator and schema identifiers), so the
    swap does not rewrite the tests that are meant to prove it. Tests only, so they do not break the
    bug-fix-only freeze. `@code-hygiene` audit.
0.3 **Copy-integrity design.** A design note in `references/plans/` (it moves to `docs/` only when the
    mechanism is built, in phase 1). It states: where the copy lives (under `scripts/`, because that is what a
    derived repository receives); that the sha256 constant lives **next to the copy**, so a synced copy and
    its constant always come from the same researchteam version; which command compares them with no network;
    how `researchteam doctor` reports it; and which test proves the copy equals the file at the pinned
    agentteams commit. `@adversarial` reviews the design before any code.
0.4 **Private-import inventory.** List every private agentteams symbol researchteam uses and the public
    replacement each needs. Find them by text search, not by import parsing: the two known ones sit inside a
    code string that runs under agentteams' interpreter. Send the list through the coordinator.

## Phase 1: after agentteams 1.3.0 is signed (blocked until then)
Entry conditions, all required: a verified signed agentteams 1.3.x tag; the operator's ruling for the
cross-line pin move, confirmed in this repository's session; the coordinator's assignment.
1.1 **Pin PR**, on the model of `references/plans/release-line-1.2.plan.md`: operator-signed row
    `release-line-agentteams-1.3`; drop `agentteams.tag=`, then `check_toolchain.py --write-lock --tag
    agentteams=<tag> --sync-extras`; S-10 vulnerability search; regenerate the team; `--verify-toolchain-pin`;
    `@security` PASS naming `toolchain.lock`, the extras and `.github/agents/`. Lessons from the 1.2 line, all
    required:
    - `.github/agentteams-autosync-ref` moves with the lock;
    - run `scripts/validate_agentteams_update.sh` and re-project the Project-Specific Rules
      (`agentteams --sync-project-rules`), then check that PS-1 to PS-3 survive in every projected copy;
    - before asking for `@security`, search the regenerated team, the memory indexes included, for a home
      path, a username or any personal detail (S-8). This is what caused the HALT on PR #214;
    - the head that carries the operator-signed row gets its own final `@security` PASS;
    - re-check agentteams #511 (every rendered Claude agent declares `tools:`).
1.2 **Swap PR.** Copy the core; reduce the engine to adapters; build the integrity check from 0.3; keep the
    `researchteam-term-register` reader so committed indexes do not turn `[STALE]`; prove it with the 0.2
    tests and with `term-check` on every project under `Projects/`. `@code-hygiene` and `@security`.
1.3 **Private imports.** Replace them if agentteams 1.3 exports public equivalents; otherwise keep them and
    record why.
1.4 **Docs.** `docs/term-index-protocol.md` ("Planned placement" becomes the placement); the layering rule
    ("generic library code lives in agentteams; researchteam carries pinned copies or imports public API
    only"); changelog.

## Phase 2: release
2.1 `v1.3.0-rc.1` from `main` onto a new `release/1.3`; the cut script includes P2's identity checks. Nothing
    else merges to `main` between the candidate and the final (the final's script allows the candidate plus
    release files only).
2.2 Dry-run pin check in the next repository of the release order, reported by the coordinator.
2.3 `v1.3.0`.
2.4 Record: work summary (`@work-summarizer`), then `@conflict-auditor`.

## Operator decisions
The cross-line ruling; the signed line row; every merge into `main` (live answer naming PR and head);
creating `release/1.3` at a named commit and each later move of it; both tags.

## Risks
- The upstream module's parameters may not cover an adapter point: 0.1 exists to find that before 1.3.0 is cut.
- A schema rename upstream could stale every committed index: 1.2 tests exactly that.
- A copy with no integrity check is an unverified vendored file: 1.2 does not merge without the check.

## Done when
researchteam 1.3.0 is tagged with the core copied and checked, the adapters and tests green, and the
protocol page describing the placement as built.
