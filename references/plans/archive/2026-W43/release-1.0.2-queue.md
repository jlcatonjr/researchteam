# researchteam next patch after the agentteams 1.0.x pin: queued main-only items (Jim, 2026-10-19: ship with agentteams 1.0.x). Note: PR #104 cuts 1.0.2 now WITHOUT these, v1.0.2 shipped (5e5aeca → 10a3675), so these land in 1.0.3

| PR | Main merge | What | Owner |
|---|---|---|---|
| #98 | 302edd1 | frozen `goose` also owns `.goosehints` and `scripts/goose-{run-resilient,openrouter-route-proxy,coordination-mcp}.py` (f3 contract point 4) | a7; f6 post-merge review: no findings |
| #102 | 6e9a452 | pinned-fingerprint check in the trust-root step (scaffold + researchteam's own workflow), docs note (from f3) | f6 |

Cut: cherry-pick -x each onto release/1.0. Then a CHANGELOG `## 1.0.2`, an agentteams 1.0.x pin with an operator-signed pin row,
a 10-sign-release script derived from 09 (PREV=v1.0.1 b55e230), the operator signs, then merge-forward.
