# ResearchTeam

Conduct rigorous, source-grounded scholarly research with agent-based workflows and robust update safety.

---

## What It Is

`researchteam` is a pip-installable framework that scaffolds and maintains an agent-based research project:
a team of governance and domain agents (generated from `brief.json` by the companion
[`agentteams`](https://jlcatonjr.github.io/agentteams/) tool), plus the docs, scripts, and checklists that
support them. Deliverables are Markdown research reports with Chicago-style citations, every claim traceable to
a scholarly source.

A derived repository describes **its own project**. The framework keeps the shared infrastructure current
without touching your research content: `brief.json`, `Projects/` and `references/` are never written by an
update.

---

## Two Update Layers

| Layer | What it covers | Update mechanism |
|---|---|---|
| **Layer 1** (agentteams-managed) | `.github/agents/`, `copilot-instructions.md`, native Claude / Goose / Codex surfaces | `agentteams --update --merge`, run by `researchteam update` |
| **Layer 2** (researchteam-managed) | `docs/`, `scripts/`, `.claude/`, and the managed block of `CLAUDE.md` | `researchteam update --layer2-only` |
| **Project identity** (generated, not synced) | `README.md` and `CLAUDE.md`'s title + *Project Purpose* header | `researchteam personalize` (from `brief.json`) |

---

## Where to Go Next

| If you want to… | Read |
|---|---|
| Install and start a project | [Getting Started](getting-started.md) |
| Look up a command or flag | [CLI Reference](cli-reference.md) |
| Run the in-repo checks (validate, citation audit, history check, library) | [Bridge Reference](bridge-reference.md) |
| Follow a research protocol (citation audit, historical context, literature library) | [Guides](guides.md) |
| Read or change the framework's code | [API Reference](api-reference/index.md) |

---

## Install

```bash
# recommended — pulls agentteams in, enabling the layer-1 (agent-team) pass
pip install "researchteam[update] @ git+https://github.com/jlcatonjr/researchteam.git@v1.0.2"
```

Then:

```bash
researchteam init my-research-project
cd my-research-project
researchteam doctor
```

See [Getting Started](getting-started.md) for the other install variants and the onboarding steps.
