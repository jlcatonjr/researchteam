# Correct the PR #27 item-1 diagnosis; pin researchteam/.venv agentteams to main

User go-ahead 2026-10-07 (option: reinstall + correct note). Source: baseagent-07, quoting
agentteams-a9's reproduction of CA-033 with the exact argv. The shared WIP checkout kept the rows;
researchteam/.venv's non-editable snapshot (5090eb0, which predates agentteams #106) dropped them.

1. Reinstall researchteam/.venv agentteams as a VCS pin: git+https://github.com/jlcatonjr/agentteams.git@729a0ad.
2. Verify with direct_url.json, `agentteams --version` and `researchteam doctor`.
3. Correct the note's status section on a branch; @security; validate; push; PR; merge.
4. Reply to baseagent-07.
