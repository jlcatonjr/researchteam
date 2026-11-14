# Pin agentteams v1.1.0-rc.15 on researchteam main (supersedes #137, rc.14)

Source: baseAgent cross-surface hand-off 2026-11-03; operator decision "Hold #137 for rc.15".
Tag: v1.1.0-rc.15, object 167c89338b61bdaf9b0d5be22a261377dc6d7c87 -> 9900fbd3cee54d977f045b5ca0406ac5379ac541,
release-key signature verified (SHA256:IPdnLwlF…).

Depends on #138 (s10-release-cooldown-restored): the pin row derives from it (local-lineage carve-out).

1. New branch chore/agentteams-1.1.0-rc.15 from origin/main; carry the validate-scope fix (a60fd11) from #137.
2. Verify the tag, write the lock and the extras.
3. Install rc.15 in the worktree venv; run the autosync gate steps (layer1, scrub, validate, detectors) and pytest.
4. OSV search for agentteams 1.1.0rc15 and any changed dependency.
5. Unsigned decision spec pin-agentteams-v1.1.0-rc.15; operator scripts to sign the row and merge.
6. Supersede #137 (comment; operator closes).
Then: researchteam v1.1.0-rc.4 cut; 1.0 line (v1.0.6 pin, researchteam v1.0.4) as a separate plan.
