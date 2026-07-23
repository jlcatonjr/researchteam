<!-- AGENTTEAMS:BEGIN content v=1 -->
# Goose CLI Capabilities Reference — ResearchTeam

This file documents what Goose's builtin extensions can actually do, and how to
tell which ones are wired in for *you specifically*. It is generated once per
project and does not change as agents are added or removed.

## Check your own capability set first

Only the extensions listed in **your own** `.goose/recipes/<your-slug>.yaml`
`extensions:` block are callable by you. This reference describes what each
builtin extension can do *if present* — it is not a claim that every extension
listed below is active for every agent in this team. When in doubt, read your
own recipe file.

## `developer` — present for effectively every agent by default

Read/write files and execute shell commands. The shell tool has **no code-level
network sandbox**: `curl`, `wget`, and any other CLI network client work exactly
as they would in a normal terminal, unless a specific deployment has deliberately
restricted egress. The extension's own built-in system prompt frames this tool
entirely around software work (reading/editing code, running tests, using `rg`)
and never mentions network use — do not treat that framing as a capability limit.
If a user asks for something that needs live external data (a webpage, an API
response, a public data feed) and no dedicated fetch/search extension is listed in
your own recipe, try a plain shell command (e.g. `curl <url>`) before concluding
you have no way to retrieve it.

## Other builtin extensions (opt-in per agent, via `recipe_extensions`)

These are **not** enabled unless your own recipe's `extensions:` block lists them:

- `computercontroller` — web scraping (`web_scrape`: fetch a URL's content), file
  caching, PDF/DOCX/XLSX manipulation, and local automation scripts. The closest
  thing to a dedicated fetch tool; prefer it over ad hoc shell `curl` when it's
  available, since it handles content-type negotiation and caching for you.
- `summon` — load referenced recipes/skills into your own context, or delegate to
  a sub-recipe session (orchestrator only; Goose forbids nested delegation beyond
  one layer).
- `apps`, `skills`, `todo`, `analyze`, `memory`, `autovisualiser` — local,
  non-network tools for sandboxed HTML apps, skill discovery, task tracking, code
  structure analysis, durable memory, and data visualization respectively.

None of the builtin extensions include a general web-search tool (query text in,
ranked results out). `computercontroller`'s `web_scrape` requires a known URL. If a
task genuinely needs search rather than fetch, that requires a separate MCP
extension (e.g. a Brave/Tavily/DuckDuckGo search server) added via
`recipe_extensions`/`goose:mcp` in this team's brief — check whether one is
configured before assuming search is unavailable outright.

## General CLI competency (not Goose-specific)

See `references/cli-tool-discovery.reference.md` for the runtime-agnostic
methodology this file's `developer`/network guidance above is one instance of:
discovering what's actually installed, using `--help`/`man`, inspecting a program
as a last resort, and installing a genuinely missing tool. See
`references/skill-generation.reference.md` for what to do when a capability is
still out of reach after trying that.

## Context-bloat management (built into Goose, not something to prompt for)

Goose already auto-compacts a long-running conversation on its own — this is a real,
harness-level feature (`goose::context_mgmt`), not something an agent needs to
monitor or trigger itself. `/compact` is a genuine Goose slash command, and Goose
already calls it automatically once accumulated context crosses a configurable
fraction of the model's context window, summarizing rather than truncating so the
conversation's signal survives the compaction. Don't write agent instructions telling
a persona to "check context usage and call /compact" — the harness already does this
unconditionally, and an agent's own generated text isn't re-parsed as a slash command
by the harness, so such an instruction would be inert.

The one thing that IS configurable is the threshold: `GOOSE_AUTO_COMPACT_THRESHOLD`
(env var) / `autoCompactThreshold` (the same setting's name in Goose's ACP protocol,
used by IDE integrations like the VS Code extension) — a fraction, `(0, 1]`, e.g.
`0.9` for 90%. It is not exposed in the interactive `goose configure` wizard and has
no recipe-level equivalent (`.goose/recipes/*.yaml` has no settings-override block) —
it is set the same way as `GOOSE_MODE`/`GOOSE_DEBUG`, as a flat top-level key in that
Goose installation's own `~/.config/goose/config.yaml`. This project's generator has
no mechanism to set it on a downstream user's behalf — that file lives outside every
project directory this module writes to. A team that wants a specific threshold must
set it directly in their own Goose installation.
<!-- AGENTTEAMS:END content -->
