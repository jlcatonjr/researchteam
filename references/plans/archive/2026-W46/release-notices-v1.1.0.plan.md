# RT-8: release notices for researchteam v1.1.0 to derived repositories

Date: 2026-11-09. Coordinated-release step RT-8. Operator instruction 2026-11-09: "Proceed with remaining work".
The notices are information, not approval. Each repository adopts through its own session.

| Repo | Pinned now | Notice |
|---|---|---|
| mathAgents | researchteam v1.1.0-rc.4, agentteams rc.15 | move to v1.1.0 via refresh_agent_surfaces.sh |
| Batallion | researchteam v1.1.0-rc.3, agentteams rc.12 (1.1 line) | move to v1.1.0 |
| baseAgent | researchteam v1.0.2, agentteams v1.0.4 (1.0 line) | target for when the #283 / Experiment 1 hold lifts |

The 5 unlocked repos (OrthodoxLLM, SocialScienceHumanities, agenticExperimentation, biographies, legalResearch) are
excluded: they get release-lock adoption PRs through infrastructureManagement (P11-9).

Facts: researchteam v1.1.0, object 4f0fb292, peeled 938dd663. It pins agentteams v1.1.0, object 093c38fd, peeled
9b16fb54. Verified 2026-11-09.

Delivery: Jim picks the recipient sessions (AskUserQuestion). An unpicked repository keeps a file-only notice in
notices/.
