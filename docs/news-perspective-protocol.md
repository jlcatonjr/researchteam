# News as Perspective — an interpretive overlay on the on-the-fly retrieval profile

News reporting on a recent or ongoing event is a **contemporaneous account of perspective** — not
verified fact, and not the same epistemic class as a scholarly, encyclopedic, or official source.
Outlets are, at minimum, *as* engaged in shaping how an event is perceived as they are in
informing the public about it; treating a news claim with the same confidence as a citation from a
peer-reviewed source or an official record is a category error this protocol exists to prevent.

> This is **not a sixth retrieval surface** and **not a change to the corpus-of-record law**. It
> is an interpretive overlay on `docs/on-the-fly-retrieval-profile.md`'s existing reputability
> mechanism — news sources are found and tiered exactly as any other on-the-fly source (via the
> same curated allowlist, the same honest-empty discipline); this doc adds *how to read what a
> `type="news"` source says*, nothing structurally new to `docs/retrieval-surfaces.md`'s
> five-surface enumeration.

## The honest ceiling (read first — binding; do not soften)

- **A news source is a contemporaneous account, not a verified fact.** Reputability (the allowlist
  tier a source cleared) is provenance — *where the account came from* — never a guarantee the
  event happened exactly as characterized.
- **Multiple outlets covering the same event may frame it differently, and this protocol does not
  adjudicate between them.** It gives an account honest attribution and, where extractable, a
  publish date — it does not corroborate one outlet's account against another's, and does not
  claim to resolve disagreement between sources. Multi-outlet corroboration tracking is explicitly
  out of scope here — a project that needs it is building something larger than this protocol
  covers.
- **A factual report and a characterization are not the same epistemic weight.** "X happened" (a
  plain report of an event) and "X was widely seen as troubling" (an outlet's characterization of
  how something landed) deserve different handling — the second is further from verifiable fact
  and needs more hedging, not the same confidence as the first.
- **Never call an outlet's account neutral.** Every account comes from somewhere; name the outlet,
  don't launder its framing into unattributed prose. This directly reuses `@interpretation-
  advisor`'s existing scholarly-tradition discipline ("never call a survey neutral, always name the
  canon and exclusions") — the same discipline, applied to an outlet's account instead of a
  scholarly canon.

## The "Reported" / "Contested" ledger-status pair

An addition to `@technical-validator`'s existing claim-ledger convention (`CH-08/09/10`), for use
specifically when a claim's supporting evidence is `type="news"`:

- **`Reported (attributed, dated)`** — a plain factual claim a news source is the origin of (what
  happened), carried with its outlet name and, when extractable, its publish date. Not
  independently re-verified — reported, not confirmed.
- **`Contested (attributed)`** — a claim about how a source *characterized* something (an outlet's
  editorializing description of a person, event, or motive), distinct from a plain factual report
  and held to a *more* skeptical standard than `Reported` — a characterization is further from
  verifiable fact than a report of what happened.

Neither status claims proof. Both exist specifically so a claim ledger doesn't fold a news-sourced
claim into the same undifferentiated confidence bucket as a scholarly or official citation.

## "Recency drift" — a named `@adversarial` check

A standard addition to `@adversarial`'s toolkit, for any project whose sources include
`type="news"` items: **are dated, recent-event claims stated with their date and attribution, not
presented as timeless procedure or settled fact?** A claim that was accurate "as reported on
`<date>`" can read as evergreen once its date is dropped during drafting — this check exists to
catch exactly that drift before it ships.

## Provenance record — unchanged from the on-the-fly profile, `tier`/`type` already sufficient

This overlay adds no new field to the on-the-fly profile's provenance contract
(`docs/on-the-fly-retrieval-profile.md`'s `{slug, source_url, sha256, retrieved_at, license,
char_count, tier}`). `type="news"` (already part of the underlying allowlist's data model) is what
triggers this protocol's interpretive discipline; a project wanting a machine-readable publish
date on a provenance record can extract one via the reference implementation below, but this
protocol itself is about *how a project's own agents present a news-sourced claim*, not a new
required schema field.

## Proven precedent this formalizes

This protocol did not originate as framework prescription — it formalizes a pattern a downstream
researchteam consumer project independently built and proved useful under real deliverable
pressure: `researchRepositories/OrthodoxLLM`'s `election-within-the-orthodox-church` project.
That project's own interpretive map defined a source-tier discipline naming journalism as a
distinct, recency-scoped class ("Tier 3 — journalism / wikis: used for *recent events*... always
cross-checked and attributed. Never the sole support for a normative or historical-structural
claim"), used a confidence-ledger status pair for dated news claims distinct from "Well-evidenced"
(`Reported (attributed, dated)` for a plain factual report; `Contested / attributed` for an
outlet's characterization), and named a recurring adversarial-audit check for exactly the
recency-drift failure mode described above. That pattern existed in exactly one project, in
project-local prose only, un-propagated to any other project or to this framework's own docs —
this protocol is that formalization and generalization, not a new invention.

## Reference implementation

`agentteams.research.news` (merged `agentteams` PR #59, commit `e631cc9`, part of the same
`agentteams[research]` optional-dependency group this repo already depends on):
`is_news_source(source) -> bool` and `perspective_attribution(source, published_at) -> str` — the
shared attribution-string formatter this protocol's "Reported"/"Contested" framing is presented
through. A `PerspectiveKind` type alias (`"reported"` / `"contested"`) exports the same two-label
vocabulary this doc uses, so a consumer's own code and this doc's own prose stay in the same
terms. `agentteams.research.search.extract_published_date(html)` (best-effort, regex-based —
JSON-LD `datePublished`/`dateCreated`, `article:published_time` meta, `date`/`pubdate` meta, a bare
`<time datetime>` tag — never fabricates, honest `None` on no match) is what a consumer calls to
get the date this protocol's `Reported (attributed, dated)` status names; a caller wanting both a
page's text and its date in one fetch has `fetch_text_and_date(url)`, additive alongside the
existing `fetch_text(url)` (identical behavior, unchanged signature).

**Precision on what's real:** `agentteams.research.news` does not itself decide whether a given
claim is `"reported"` or `"contested"` — that judgment needs the claim's own text, which the
module never sees. It supplies the vocabulary and the attribution/date-extraction primitives; the
classification judgment is made by whatever agent or pipeline is producing the claim (for a
researchteam project, this is where `@technical-validator`'s claim-ledger convention and
`@adversarial`'s "Recency drift" check, both described above, actually apply the distinction).

## Acceptance for this protocol

Documented as an interpretive overlay with its own honest ceiling and a proven, cited precedent —
so a project consuming reputable news sources has a formalized "Reported"/"Contested" vocabulary
and a named recency-drift check to apply, rather than either treating a news claim as equivalent
to a scholarly citation or re-inventing the OrthodoxLLM pattern locally, unaware it already exists.
