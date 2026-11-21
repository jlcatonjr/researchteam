// Bibliography explorer: period -> person -> bio and attributes -> sources -> source detail.
//
// A dependency-free ES module. It displays one explorer file (CONTRACT.md, section 2) written by
// scripts/build_bibliography_explorer.py and holds no knowledge of any study.
//
//   import { mount } from "./explorer.js";
//   const explorer = mount(element, data, { onNavigate, labels, headingLevel, initial });
//   explorer.show({ view: "person", id: "some-id" });
//   explorer.destroy();
//
// Targets: { view: "periods" } | { view: "period", id } | { view: "person", id }
//          | { view: "source", id, person? }   (person: the person the source was opened from)
//
// Every string from the data is inserted as a text node. This file never parses markup from the data
// and never touches the URL; a link is made only for an http(s) address.

const SCHEMA = "researchteam.bibliography-explorer";
const SCHEMA_MAJOR = "1";

export const DEFAULT_LABELS = {
  breadcrumb: "Explorer path",
  periods: "Periods",
  persons: "people",
  person: "person",
  filter: "Find by name",
  sort: "Sort by",
  sortName: "Name",
  sortYear: "Year",
  shown: (n, total) => (n === total ? `${total} shown` : `${n} of ${total} shown`),
  noMatch: "No name matches.",
  nothingEstablished: "Nothing established",
  noYear: "no year",
  before: (y) => `before ${y + 1}`,
  from: (y) => `${y} on`,
  period: "Period",
  yearBasis: "Year from",
  aliases: "Also known as",
  bio: "Brief bio",
  noBio: "No bio yet.",
  unsourced: "unsourced",
  basis: "Basis",
  authoredBy: "Written by",
  verification: "Verification",
  attributes: "Attributes",
  noAttributes: "No attributes recorded.",
  established: "Established",
  notEstablished: "Not established",
  evidence: (n) => `Evidence (${n})`,
  tier: "Tier",
  source: "Source",
  citedAs: "Cited as",
  locator: "Where",
  quote: "Quoted",
  consulted: "Page consulted",
  access: "Access",
  via: "Reported via",
  evidenceBasis: "Basis",
  reporter: "Reported by",
  evidenceNote: "Note",
  audit: "Audit trail",
  supports: "Supports",
  codes: "Coded attributes",
  advisory: "Advisory",
  sourcesAbout: "Sources used for this entry",
  noSourcesAbout: "No sources recorded.",
  worksBy: "Works by or attributed to this entry",
  noWorksBy: "No works recorded.",
  citation: "Citation",
  originBibliography: "From the project bibliography. Chicago-style entry rendered from its fields.",
  originEvidenceCitation: "Not in the project bibliography. Citation shown as recorded.",
  originWorkTitle: "Uncatalogued work. Title shown as recorded.",
  summary: "Summary",
  noSummary: "No summary yet.",
  summaryBy: "Written by",
  summaryBasis: "What was read",
  summaryRead: "Read at",
  caveats: "Caveats",
  details: "Details",
  type: "Type",
  links: "Links",
  note: "Note on provenance",
  sourceAttributes: "Other attributes",
  linkedPersons: "Linked entries",
  noLinkedPersons: "Not linked to any entry.",
  relationBy: "By",
  relationAbout: "About",
  fields: {
    title: "Title", authors: "Authors", editors: "Editors", year: "Year", month: "Month",
    journal: "Journal", booktitle: "In", publisher: "Publisher", address: "Place", volume: "Volume",
    number: "Number", series: "Series", pages: "Pages", school: "School",
    howpublished: "Published as", doi: "DOI", isbn: "ISBN", issn: "ISSN", url: "URL", date: "Date",
    locator: "Where",
  },
};

const FIELD_ORDER = ["title", "authors", "editors", "year", "month", "date", "journal", "booktitle",
  "volume", "number", "series", "pages", "publisher", "address", "school", "howpublished", "locator",
  "doi", "isbn", "issn"];

// ---------------------------------------------------------------------------- DOM helpers
function h(tag, attrs, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "on") for (const [type, fn] of Object.entries(value)) node.addEventListener(type, fn);
    else node.setAttribute(key, value === true ? "" : String(value));
  }
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    node.append(typeof child === "object" ? child : document.createTextNode(String(child)));
  }
  return node;
}

function externalLink(url, text) {
  if (typeof url !== "string" || !/^https?:\/\//i.test(url)) return h("span", null, text || url);
  return h("a", { href: url, rel: "noopener noreferrer", target: "_blank" }, text || url);
}

function fold(text) {
  return String(text).normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
}

function nameOf(name) {
  if (name.literal) return name.literal;
  return [name.given, name.family, name.suffix].filter(Boolean).join(" ");
}

// ---------------------------------------------------------------------------- mount
export function mount(element, data, options = {}) {
  if (!element || typeof element.append !== "function") throw new Error("bibliography explorer: no element to mount in");
  if (!data || data.schema !== SCHEMA || String(data.schema_version).split(".")[0] !== SCHEMA_MAJOR) {
    throw new Error(`bibliography explorer: expected ${SCHEMA} version ${SCHEMA_MAJOR}.x`);
  }
  const L = { ...DEFAULT_LABELS, ...(options.labels || {}) };
  L.fields = { ...DEFAULT_LABELS.fields, ...((options.labels || {}).fields || {}) };
  const level = Math.min(Math.max(Number(options.headingLevel) || 2, 1), 4);
  const H = (offset, attrs, ...kids) => h(`h${Math.min(level + offset, 6)}`, attrs, ...kids);

  const byId = (list) => new Map(list.map((item) => [item.id, item]));
  const periods = byId(data.periods);
  const persons = byId(data.persons);
  const sources = byId(data.sources);
  const evidence = byId(data.evidence);
  const vocab = Object.fromEntries(Object.entries(data.vocab).map(([k, v]) => [k, byId(v)]));
  const label = (kind, id) => (vocab[kind].get(id) || { label: id }).label;
  const personsIn = new Map(data.periods.map((p) => [p.id, []]));
  for (const p of data.persons) personsIn.get(p.period.id).push(p);
  const linksOfPerson = new Map(data.persons.map((p) => [p.id, []]));
  const linksOfSource = new Map(data.sources.map((s) => [s.id, []]));
  for (const link of data.links) {
    linksOfPerson.get(link.person_id).push(link);
    linksOfSource.get(link.source_id).push(link);
  }
  const hasEstablished = (p) => p.attributes.some((a) => a.established);
  const citationText = (s) => s.citation.chicago || s.citation.as_recorded || s.id;

  const root = h("div", { class: "bibx" });
  const listState = new Map();          // period id -> { filter, sort }
  let current = null;
  element.append(root);

  // -------------------------------------------------------------------------- navigation
  function resolve(target) {
    const t = target || { view: "periods" };
    const maps = { period: periods, person: persons, source: sources };
    if (t.view === "periods") return { view: "periods" };
    if (!maps[t.view] || !maps[t.view].has(t.id)) {
      throw new Error(`bibliography explorer: unknown target ${JSON.stringify(t)}`);
    }
    const out = { view: t.view, id: t.id };
    if (t.view === "source" && t.person && persons.has(t.person)) out.person = t.person;
    return out;
  }

  function show(target, { notify = true, focus = true } = {}) {
    current = resolve(target);
    const views = { periods: periodsView, period: periodView, person: personView, source: sourceView };
    const body = views[current.view](current);
    root.replaceChildren(
      data.meta.notice ? h("p", { class: "bibx-notice", role: "note" }, data.meta.notice) : null,
      breadcrumb(current),
      body,
    );
    if (focus) {
      const heading = body.querySelector("[data-bibx-heading]");
      if (heading) heading.focus();
    }
    if (notify && typeof options.onNavigate === "function") options.onNavigate({ ...current });
  }

  const go = (target) => () => show(target);
  const navButton = (target, cls, ...kids) => h("button", { type: "button", class: cls, on: { click: go(target) } }, ...kids);

  function breadcrumb(t) {
    const trail = [[{ view: "periods" }, L.periods]];
    const personCrumb = (p) => {
      trail.push([{ view: "period", id: p.period.id }, periods.get(p.period.id).label]);
      trail.push([{ view: "person", id: p.id }, p.display_name]);
    };
    if (t.view === "period") trail.push([t, periods.get(t.id).label]);
    if (t.view === "person") personCrumb(persons.get(t.id));
    if (t.view === "source") {
      if (t.person) personCrumb(persons.get(t.person));
      trail.push([t, L.source]);
    }
    return h("nav", { class: "bibx-crumbs", "aria-label": L.breadcrumb }, h("ol", null, trail.map(([target, text], k) =>
      h("li", null, k === trail.length - 1
        ? h("span", { "aria-current": "page" }, text)
        : navButton(target, "bibx-link", text)))));
  }

  // -------------------------------------------------------------------------- shared pieces
  function periodRange(p) {
    if (!p.established) return "";
    if (p.start_year === null && p.end_year === null) return "";
    if (p.start_year === null) return L.before(p.end_year);
    if (p.end_year === null) return L.from(p.start_year);
    return `${p.start_year}–${p.end_year}`;
  }

  function badge(established) {
    return h("span", { class: `bibx-badge ${established ? "bibx-yes" : "bibx-no"}` },
      established ? L.established : L.notEstablished);
  }

  function row(term, ...value) {
    return [h("dt", null, term), h("dd", null, ...value)];
  }

  function evidenceItem(ev, { withSource = true, withValue = false, person } = {}) {
    const tier = vocab.tiers.get(ev.tier) || { label: ev.tier };
    const src = sources.get(ev.source_id);
    return h("li", { class: "bibx-evidence" },
      withValue ? h("p", { class: "bibx-evidence-value" }, `${label("attribute_kinds", ev.attribute_kind)}: ${ev.value}`) : null,
      h("dl", { class: "bibx-dl" },
        row(L.tier, h("span", { class: `bibx-badge ${tier.establishes ? "bibx-yes" : "bibx-no"}` }, tier.label),
          tier.description ? h("span", { class: "bibx-muted" }, ` ${tier.description}`) : null),
        withSource && src ? row(L.source, navButton({ view: "source", id: src.id, person }, "bibx-link bibx-cite", citationRuns(src))) : null,
        ev.cited_as ? row(L.citedAs, ev.cited_as) : null,
        ev.locator ? row(L.locator, ev.locator) : null,
        ev.quote ? row(L.quote, h("blockquote", null, ev.quote)) : null,
        ev.url ? row(L.consulted, externalLink(ev.url)) : null,
        ev.access ? row(L.access, label("access", ev.access)) : null,
        ev.via ? row(L.via, ev.via) : null,
        ev.basis ? row(L.evidenceBasis, ev.basis) : null,
        ev.reporter ? row(L.reporter, ev.reporter) : null,
        ev.note ? row(L.evidenceNote, ev.note) : null,
      ),
      ev.audit ? h("details", { class: "bibx-audit" }, h("summary", null, L.audit), h("p", null, ev.audit)) : null,
    );
  }

  function evidenceDetails(ids, opts) {
    const rows = (ids || []).map((id) => evidence.get(id)).filter(Boolean);
    if (!rows.length) return null;
    return h("details", { class: "bibx-details" },
      h("summary", null, L.evidence(rows.length)),
      h("ul", { class: "bibx-evidence-list" }, rows.map((ev) => evidenceItem(ev, opts))));
  }

  function citationRuns(src) {
    const runs = src.citation.chicago_runs;
    if (!runs) return citationText(src);
    return runs.map((run) => (run.italic ? h("i", null, run.text) : run.text));
  }

  function section(title, ...kids) {
    return h("section", { class: "bibx-section" }, H(1, null, title), ...kids);
  }

  // -------------------------------------------------------------------------- views
  function periodsView() {
    return h("div", { class: "bibx-view" },
      H(0, { tabindex: "-1", "data-bibx-heading": true }, data.meta.title),
      h("ul", { class: "bibx-list" }, data.periods.map((p) => {
        const n = personsIn.get(p.id).length;
        return h("li", null, navButton({ view: "period", id: p.id }, "bibx-rowbutton",
          h("span", { class: "bibx-row-main" }, p.label),
          h("span", { class: "bibx-row-meta" }, [periodRange(p), `${n} ${n === 1 ? L.person : L.persons}`].filter(Boolean).join(" · "))));
      })));
  }

  function periodView(t) {
    const p = periods.get(t.id);
    const all = personsIn.get(p.id);
    const state = listState.get(p.id) || { filter: "", sort: "name" };
    listState.set(p.id, state);
    const list = h("ul", { class: "bibx-list" });
    const count = h("p", { class: "bibx-muted", "aria-live": "polite" });
    const sortButtons = {};
    const sortName = (a) => a.sort_name || a.display_name;

    function fill() {
      const needle = fold(state.filter.trim());
      const shown = all.filter((x) => !needle
        || [x.display_name, ...(x.aliases || [])].some((s) => fold(s).includes(needle)));
      shown.sort((a, b) => {
        if (state.sort === "year") {
          const ya = a.period.year, yb = b.period.year;
          if (ya !== yb) return (ya === undefined) - (yb === undefined) || ya - yb;
        }
        return sortName(a).localeCompare(sortName(b));
      });
      count.textContent = L.shown(shown.length, all.length);
      for (const [key, button] of Object.entries(sortButtons)) button.setAttribute("aria-pressed", String(key === state.sort));
      list.replaceChildren(...(shown.length ? shown.map((x) => h("li", null,
        navButton({ view: "person", id: x.id }, "bibx-rowbutton",
          h("span", { class: "bibx-row-main" }, x.display_name),
          h("span", { class: "bibx-row-meta" },
            [label("person_kinds", x.kind), x.period.year === undefined ? L.noYear : String(x.period.year)].join(" · "),
            hasEstablished(x) ? null : h("span", { class: "bibx-badge bibx-no" }, L.nothingEstablished)))))
        : [h("li", { class: "bibx-muted" }, L.noMatch)]));
    }

    const inputId = `bibx-filter-${Math.random().toString(36).slice(2)}`;
    const sorter = (key, text) => (sortButtons[key] = h("button", { type: "button", class: "bibx-toggle",
      on: { click: () => { state.sort = key; fill(); } } }, text));
    const view = h("div", { class: "bibx-view" },
      H(0, { tabindex: "-1", "data-bibx-heading": true }, p.label,
        periodRange(p) ? h("span", { class: "bibx-muted" }, ` ${periodRange(p)}`) : null),
      h("div", { class: "bibx-controls" },
        h("label", { for: inputId }, L.filter),
        h("input", { id: inputId, type: "search", value: state.filter, autocomplete: "off",
          on: { input: (e) => { state.filter = e.target.value; fill(); } } }),
        h("span", { class: "bibx-sort", role: "group", "aria-label": L.sort },
          h("span", { "aria-hidden": "true" }, `${L.sort}: `), sorter("name", L.sortName), sorter("year", L.sortYear))),
      count, list);
    fill();
    return view;
  }

  function bioBlock(p) {
    const bio = p.bio;
    if (!bio) return section(L.bio, h("p", { class: "bibx-muted" }, L.noBio));
    const panelId = `bibx-clause-${Math.random().toString(36).slice(2)}`;
    const panel = h("div", { class: "bibx-clause-evidence", id: panelId });
    let open = null;
    const text = h("p", { class: "bibx-bio" });
    if (bio.clauses) {
      bio.clauses.forEach((clause, k) => {
        const ids = clause.evidence_ids || [];
        const button = ids.length ? h("button", { type: "button", class: "bibx-ref", "aria-expanded": "false",
          "aria-controls": panelId, "aria-label": `${k + 1}. ${L.evidence(ids.length)}`, on: { click: () => {
            const closing = open === button;
            if (open) open.setAttribute("aria-expanded", "false");
            open = closing ? null : button;
            if (open) open.setAttribute("aria-expanded", "true");
            panel.replaceChildren(...(closing ? [] : [h("ul", { class: "bibx-evidence-list" },
              ids.map((id) => evidence.get(id)).filter(Boolean).map((ev) => evidenceItem(ev, { withValue: true, person: p.id })))]));
          } } }, String(k + 1)) : h("span", { class: "bibx-badge bibx-no" }, L.unsourced);
        text.append(clause.text, button, " ");
      });
    } else {
      text.append(bio.text);
    }
    return section(L.bio, text, panel, h("dl", { class: "bibx-dl bibx-muted" },
      row(L.basis, bio.basis),
      bio.authored_by ? row(L.authoredBy, bio.authored_by) : null,
      row(L.verification, bio.verification_state)));
  }

  function personView(t) {
    const p = persons.get(t.id);
    const period = periods.get(p.period.id);
    const kinds = [...vocab.attribute_kinds.values()].sort((a, b) => a.order - b.order);
    const links = linksOfPerson.get(p.id);
    const about = links.filter((l) => l.relation === "about");
    const by = links.filter((l) => l.relation === "by");
    const sourceButton = (id) => navButton({ view: "source", id, person: p.id }, "bibx-link bibx-cite", citationRuns(sources.get(id)));

    return h("div", { class: "bibx-view" },
      H(0, { tabindex: "-1", "data-bibx-heading": true }, p.display_name),
      h("dl", { class: "bibx-dl" },
        row(L.type, label("person_kinds", p.kind)),
        row(L.period, navButton({ view: "period", id: period.id }, "bibx-link", period.label),
          p.period.year === undefined ? null : ` · ${p.period.year}`),
        p.period.year_basis ? row(L.yearBasis, p.period.year_basis) : null,
        p.aliases && p.aliases.length ? row(L.aliases, p.aliases.join("; ")) : null),
      bioBlock(p),
      section(L.attributes, p.attributes.length ? kinds.map((kind) => {
        const values = p.attributes.filter((a) => a.kind === kind.id);
        if (!values.length) return null;
        return h("div", { class: "bibx-kind" }, H(2, null, kind.label),
          h("ul", { class: "bibx-values" }, values.map((a) => h("li", null,
            h("span", { class: "bibx-value" }, a.value), " ", badge(a.established),
            evidenceDetails(a.evidence_ids, { person: p.id })))));
      }) : h("p", { class: "bibx-muted" }, L.noAttributes)),
      p.codes && p.codes.length ? section(L.codes, h("ul", { class: "bibx-values" }, p.codes.map((c) => h("li", null,
        h("span", { class: "bibx-code-label" }, `${c.label}: `), h("span", { class: "bibx-value" }, c.value_label), " ",
        badge(c.established), c.basis ? h("span", { class: "bibx-muted" }, ` ${L.basis}: ${c.basis}`) : null,
        evidenceDetails(c.evidence_ids, { withValue: true, person: p.id }))))) : null,
      (p.groups || []).map((g) => h("section", { class: `bibx-section bibx-group${g.advisory ? " bibx-advisory" : ""}` },
        H(1, null, g.title, g.advisory ? h("span", { class: "bibx-badge bibx-no" }, L.advisory) : null),
        g.caveat ? h("p", { class: "bibx-caveat" }, g.caveat) : null,
        h("dl", { class: "bibx-dl" }, g.rows.map((r) => row(r.label, r.value,
          r.note ? h("p", { class: "bibx-muted" }, r.note) : null,
          r.links && r.links.length ? h("ul", { class: "bibx-inline" }, r.links.map((l) => h("li", null, externalLink(l.url, l.label)))) : null,
          evidenceDetails(r.evidence_ids, { withValue: true, person: p.id })))))),
      section(L.sourcesAbout, about.length ? h("ul", { class: "bibx-sources" }, about.map((l) => h("li", null,
        sourceButton(l.source_id),
        h("p", { class: "bibx-muted" }, `${L.supports}: ${l.attribute_kinds.map((k) => label("attribute_kinds", k)).join(", ")}`))))
        : h("p", { class: "bibx-muted" }, L.noSourcesAbout)),
      section(L.worksBy, by.length ? h("ul", { class: "bibx-sources" }, by.map((l) => h("li", null,
        sourceButton(l.source_id),
        h("p", { class: "bibx-muted" }, [label("roles", l.role), l.basis ? `${L.basis}: ${l.basis}` : ""].filter(Boolean).join(" · ")))))
        : h("p", { class: "bibx-muted" }, L.noWorksBy)));
  }

  function sourceView(t) {
    const s = sources.get(t.id);
    const origin = { bibliography: L.originBibliography, "evidence-citation": L.originEvidenceCitation,
      "work-title": L.originWorkTitle }[s.origin] || s.origin;
    const links = linksOfSource.get(s.id);
    const f = s.fields || {};
    const fieldValue = (key) => (Array.isArray(f[key]) ? f[key].map(nameOf).join("; ") + (f[`${key}_et_al`] ? " et al." : "") : String(f[key]));
    const sm = s.summary;
    const personButton = (id) => navButton({ view: "person", id }, "bibx-link", persons.get(id).display_name);

    return h("div", { class: "bibx-view" },
      H(0, { tabindex: "-1", "data-bibx-heading": true }, L.citation),
      h("p", { class: "bibx-citation" }, citationRuns(s)),
      h("p", { class: "bibx-muted" }, origin),
      section(L.summary, sm ? [
        h("p", null, sm.text),
        h("dl", { class: "bibx-dl bibx-muted" },
          row(L.summaryBy, sm.deemed_by), row(L.summaryBasis, sm.basis),
          sm.read_url ? row(L.summaryRead, externalLink(sm.read_url)) : null,
          sm.caveats && sm.caveats.length ? row(L.caveats, h("ul", { class: "bibx-inline" }, sm.caveats.map((c) => h("li", null, c)))) : null,
          row(L.verification, sm.verification_state)),
      ] : h("p", { class: "bibx-muted" }, L.noSummary)),
      section(L.details, h("dl", { class: "bibx-dl" },
        s.type ? row(L.type, s.type) : null,
        FIELD_ORDER.filter((key) => f[key] !== undefined).map((key) => row(L.fields[key] || key, fieldValue(key))),
        s.links && s.links.length ? row(L.links, h("ul", { class: "bibx-inline" }, s.links.map((l) => h("li", null, `${l.label}: `, externalLink(l.url))))) : null,
        s.note ? row(L.note, s.note) : null)),
      s.attributes && s.attributes.length ? section(L.sourceAttributes,
        h("dl", { class: "bibx-dl" }, s.attributes.map((a) => row(a.label, a.value)))) : null,
      section(L.linkedPersons, links.length ? h("ul", { class: "bibx-sources" }, links.map((l) => h("li", null,
        h("span", { class: "bibx-badge" }, l.relation === "by" ? L.relationBy : L.relationAbout), " ",
        personButton(l.person_id),
        l.relation === "by"
          ? h("p", { class: "bibx-muted" }, [label("roles", l.role), l.basis ? `${L.basis}: ${l.basis}` : ""].filter(Boolean).join(" · "))
          : [h("p", { class: "bibx-muted" }, `${L.supports}: ${l.attribute_kinds.map((k) => label("attribute_kinds", k)).join(", ")}`),
            evidenceDetails(l.evidence_ids, { withSource: false, withValue: true })])))
        : h("p", { class: "bibx-muted" }, L.noLinkedPersons)));
  }

  show(options.initial, { notify: false, focus: false });
  return {
    show: (target) => show(target),
    destroy: () => { root.remove(); },
  };
}
