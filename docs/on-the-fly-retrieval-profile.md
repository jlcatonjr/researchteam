# On-the-Fly Retrieval — an optional web-grounded profile (NOT the corpus-of-record)

An **optional, separately-labelled** retrieval profile for products that need reputable grounding *at
answer time* — a conversational/interactive app that must ground a reply now, not from a pre-provisioned
corpus. It reuses the framework's provenance discipline but relaxes exactly one thing — the acquisition
ceiling — and it carries its own, weaker honesty label to say so out loud.

> This profile **runs counter to a stated design law** of the corpus-of-record path
> (`docs/literature-library-protocol.md`: acquisition is out-of-band, **never an audit-time fetch**). That
> law is correct and is **not** changed. This is a *different profile* for a *different job*, labelled so
> no one mistakes an answer-time fetch for the human-gated corpus.

## The honest ceiling (read first — binding; do not soften)

- **This is NOT the corpus-of-record.** It is retrieved at answer time from a curated allowlist. It is
  **navigation, not a proof; not peer-reviewed truth.** A retrieved source is a pointer to open and verify,
  never a citation that anchors a claim on its own.
- **"Reputable" = provenance-vetted by a curated allowlist, NOT a guarantee the content is correct.**
  Reputability tiers rank *where a source came from*, not whether what it says is true. Provenance is not
  correctness.
- **Honest empty is mandatory.** When nothing reputable is found, return **nothing** and fall back to the
  product's existing grounding — **never** mislabel a lower-tier hit as primary, and never fabricate a
  source to fill the gap. "Absence of a reputable candidate ≠ absence of a source."
- **Answer-time acquisition is the ONE relaxation.** Everything else — provenance records, hash integrity,
  navigation-not-evidence, ships-UNVERIFIED — is inherited unchanged from the corpus-of-record discipline.
  Do not let the relaxation leak into the corpus-of-record path.

## What the profile is

A per-answer pipeline: **fetch a few reputable sources now → provenance → chunk → dense-embed → query**,
all local, no cloud key. It is templated on the researchRepositories corpora (OrthodoxLLM draws only from an
*enumerated set* of reputable repositories — CCEL / newadvent / archive.org — **never an open crawl**); the
on-the-fly profile applies that same "enumerated reputable sources only" idea at answer time.

The reusable **core** of the researchteam pattern transfers unchanged: provenance-per-source, hash
integrity, dense retrieval as navigation-only, and the honesty ceiling. Only the **acquisition** step
differs (answer-time vs. human-gated out-of-band).

## Reputability: a curated domain allowlist + primary-source steering

Because there is no human-curated catalogue at answer time, reputability must be encoded:

- **Curated domain allowlist, tiered.** Every allowed domain maps to a `tier`:
  - `primary` — original / primary texts & document repositories (e.g. gutenberg.org, wikisource.org,
    archive.org, ccel.org, perseus.tufts.edu, documentcloud.org).
  - `authoritative` — expert-reviewed reference / scholarly / official (e.g. plato.stanford.edu,
    iep.utm.edu, britannica.com, *.gov / *.int official bodies, national libraries).
  - `reference` — general encyclopedic (e.g. wikipedia.org).
  - **A domain not on the allowlist is REFUSED** — never returned. (Subdomains of an allowed domain match.)
- **Primary-source steering.** Turn the topic into targeted `site:` searches against the *primary*
  repositories for that subject area (plus one allowlist-filtered general search as a backstop). Rank
  results **primary > authoritative > reference**; dedupe by URL.
- **Best-effort, honestly.** `site:` is honored per-domain by some search backends and not others; empty
  per-domain results are simply skipped. When the whole pass yields nothing allowlisted, return empty
  (the ceiling above).

## Provenance record — the framework contract **plus a `tier` field**

The on-the-fly profile keeps the framework provenance contract but **adds `tier`**, because — unlike the
corpus-of-record, whose `*.provenance.json` records `license` against a human-curated catalogue — an
answer-time fetch has no catalogue and must carry its own reputability tiering:

```json
{
  "slug": "...",
  "source_url": "https://<allowlisted-domain>/...",
  "sha256": "<hash of the retrieved bytes>",
  "retrieved_at": "<ISO-8601>",
  "license": "<if known>",
  "char_count": 0,
  "tier": "primary | authoritative | reference"
}
```

`tier` is **required** for this profile (the corpus-of-record's provenance record does not carry it); the
other fields match the existing `{slug, source_url, sha256, retrieved_at, license, char_count}` contract so
the two profiles' provenance stays reconcilable.

## Relation to the other surfaces

- It is **not** surface #4 (literature library, the human-gated corpus-of-record) and **not** surface #5
  (source corpus over a pre-provisioned `sources/` tree). It is an *answer-time* grounding profile that
  produces its own short-lived, per-answer index.
- It still obeys the **shared cross-surface ceiling** in `docs/retrieval-surfaces.md`: navigation over a
  local index, structure-not-truth, out-of-band human verification for any real claim.

## Reference implementation (working, but a curated allowlist ≠ a truth oracle)

LingoFriend `b6579ad` — `knowledge/reputable.py` (the allowlist + tiers + topic→primary-repo steering, with
a public `tier_of(url)` and an honest-empty `reputable_sources(...) → []`) and `knowledge/sources.py`
(fetch → `provenance{sha256, tier, url, retrieved_at}` → paragraph-chunk → dense-embed → per-account query,
all local, no cloud key). Caveat the reference hit and this profile must carry: `site:` search is
best-effort per-domain, and reputability is *provenance*, not correctness.

## Acceptance for this profile

Documented as a **first-class option** with its own ceiling, distinct from the corpus-of-record law — so a
downstream product can adopt it *instead of* reinventing it against the stated law, and no reader mistakes
an answer-time fetch for the human-gated corpus.
