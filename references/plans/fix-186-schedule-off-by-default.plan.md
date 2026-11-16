# Plan: derived autosync schedule off by default, plus a workflow-sync helper (#186)

Operator ruling (2026-11-16, picker in this session, matching IM-65's picker): "Off by default + helper".

1. `researchteam/scaffold/agentteams-sync-derived.yml` ships with `schedule:` commented out, so a new derived
   repository runs autosync only when dispatched. The upstream workflow keeps its weekly schedule.
2. New command `researchteam workflow-sync [--yes] [--dry-run]`.
   - It writes `.github/workflows/agentteams-sync.yml` from the installed package's scaffold, keeping the
     repository's own top-level `on:` block, whether the schedule is there, absent or commented out.
   - It shows a diff, and asks before writing unless `--yes` is given.
   - With no workflow present, it writes the scaffold as it is (schedule off).
   - It refuses a symlink, a non-file, and a file with no top-level `on:` block. It never follows a link.
3. Tests for the scaffold default and for each helper case. Docs: `docs/agentteams-update-policy.md` and a
   CHANGELOG Unreleased entry.

PS-2: the change touches the derived workflow scaffold, so `@security` names it; `@code-hygiene` reviews the new
module.
