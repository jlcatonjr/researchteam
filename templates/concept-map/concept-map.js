// Concept map: who holds, affirms or denies which position, and how views developed.
//
// A dependency-free ES module. It displays one map file (CONTRACT.md, section 2) written by
// scripts/build_concept_map.py and holds no knowledge of any study. The layout comes from the file
// (Graphviz, run by the exporter); this module only draws it and reports what is clicked.
//
//   import { mount, membersByRelation } from "./concept-map.js";
//   const map = mount(element, data, { onSelect, labels, fit, initial });
//   map.select("node-id");      // or null to clear; returns false for an unknown id
//   map.destroy();
//
// onSelect(selection | null). selection = { node, kind, role, persons?, members?, related }:
//   role "actor": persons = the node's own persons; role "topic": members = the persons of every actor
//   node an edge joins to it, one per (person, relation), with the edges they come through.
//
// Every string from the data is inserted as a text node or an attribute value. This file never parses
// markup from the data, loads nothing and never touches the URL or storage.

const SCHEMA = "researchteam.concept-map";
const SCHEMA_MAJOR = "1";
const SVGNS = "http://www.w3.org/2000/svg";
const HEX = /^#[0-9A-Fa-f]{6}$/;

export const DEFAULT_LABELS = {
  map: "Concept map",
  fit: "Fit to width",
  actual: "Actual size",
  hint: "Click a writer or a position, or focus it and press Enter, to list who it ties to. Escape clears.",
  legend: "Legend",
  kinds: "Shapes",
  fills: "Fill",
  relations: "Lines",
  selected: (label) => `Selected: ${label}`,
  cleared: "Selection cleared.",
};

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = String(text);
  return e;
}

function svg(tag, attrs = {}, parent) {
  const e = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs)) if (v != null) e.setAttribute(k, String(v));
  if (parent) parent.appendChild(e);
  return e;
}

function lines(parent, textLines, x, y, size, cls) {
  const lh = size * 1.2;
  const y0 = y - ((textLines.length - 1) * lh) / 2;
  const t = svg("text", { x, y: y0, "font-size": size, "text-anchor": "middle", "dominant-baseline": "central", class: cls }, parent);
  textLines.forEach((s, i) => {
    const span = svg("tspan", { x, y: y0 + i * lh }, t);
    span.textContent = s;
  });
  return t;
}

function octagon(x, y, w, h, inset = 0) {
  const W = w / 2 - inset, H = h / 2 - inset, a = W * 0.4, b = H * 0.4;
  return [[-W + a, -H], [W - a, -H], [W, -H + b], [W, H - b], [W - a, H], [-W + a, H], [-W, H - b], [-W, -H + b]]
    .map(([dx, dy]) => `${(x + dx).toFixed(2)},${(y + dy).toFixed(2)}`).join(" ");
}

function stroke(rel) {
  return rel.stroke === "ink" ? "var(--cmap-ink)" : HEX.test(rel.stroke) ? rel.stroke : "var(--cmap-ink)";
}

/** How a tie reads from the side of the node that is not its tail: the relation's passive label. */
export function passive(rel) {
  return rel.passive_label || `${rel.label} (reverse)`;
}

/** Members of a topic node grouped by relation and direction, in vocabulary order:
 *  [{ relation, active, label, inferred, members }]. active: the members' nodes are the edges' tails
 *  ("affirms" this node); otherwise this node is the tail and the label is passive ("rebutted by this node"). */
export function membersByRelation(data, nodeId, { thisNode = "this node" } = {}) {
  const node = data.nodes.find((n) => n.id === nodeId);
  if (!node || !node.members) return [];
  const out = [];
  for (const r of data.vocab.relations) {
    for (const active of [true, false]) {
      const members = node.members.filter((m) => m.relation === r.id && m.active === active);
      if (members.length) out.push({ relation: r.id, active, inferred: !!r.inferred, members,
        label: active ? r.label : `${passive(r)} ${thisNode}` });
    }
  }
  return out;
}

export function mount(host, data, options = {}) {
  if (!data || data.schema !== SCHEMA || String(data.schema_version || "").split(".")[0] !== SCHEMA_MAJOR) {
    throw new Error(`concept-map: expected a ${SCHEMA} file, major version ${SCHEMA_MAJOR}`);
  }
  const L = { ...DEFAULT_LABELS, ...(options.labels || {}) };
  const onSelect = typeof options.onSelect === "function" ? options.onSelect : () => {};
  const kinds = new Map(data.vocab.node_kinds.map((k) => [k.id, k]));
  const fills = new Map(data.vocab.fills.map((f) => [f.id, f]));
  const rels = new Map(data.vocab.relations.map((r) => [r.id, r]));
  const font = data.meta.font || { family: "Helvetica", node_size: 9, edge_size: 7.5, band_size: 10 };

  const root = el("div", "cmap");
  root.style.setProperty("--cmap-font", `${font.family}, Helvetica, Arial, sans-serif`);
  if (data.meta.notice) root.appendChild(el("p", "cmap-notice", data.meta.notice));
  const bar = el("div", "cmap-bar");
  const hint = el("p", "cmap-hint", L.hint);
  const fitBtn = el("button", "cmap-fit");
  fitBtn.type = "button";
  bar.append(hint, fitBtn);
  root.appendChild(bar);
  const status = el("p", "cmap-sr");
  status.setAttribute("role", "status");
  status.setAttribute("aria-live", "polite");
  root.appendChild(status);

  const scroll = el("div", "cmap-scroll");
  const { width: W, height: H } = data.canvas;
  const S = svg("svg", { viewBox: `0 0 ${W} ${H}`, role: "group", "aria-label": `${L.map}: ${data.meta.title}`, class: "cmap-svg" });
  scroll.appendChild(S);
  root.appendChild(scroll);

  // bands
  const gB = svg("g", { class: "cmap-bands" }, S);
  for (const b of data.bands || []) if (b.x != null) lines(gB, String(b.label).split("\n"), b.x, b.y, font.band_size, "cmap-band");

  // edges
  const gE = svg("g", { class: "cmap-edges" }, S);
  const edgeEls = new Map();
  for (const e of data.edges) {
    const r = rels.get(e.relation);
    const col = stroke(r);
    const width = (r.width || 1) + (e.emphasis || 0);
    const g = svg("g", { class: "cmap-edge", "data-relation": e.relation }, gE);
    const p = e.path || [];
    if (p.length) {
      let d = `M${p[0][0]},${p[0][1]}`;
      for (let i = 1; i + 2 < p.length; i += 3) d += ` C${p[i][0]},${p[i][1]} ${p[i + 1][0]},${p[i + 1][1]} ${p[i + 2][0]},${p[i + 2][1]}`;
      const path = svg("path", { d, fill: "none", stroke: col, "stroke-width": width }, g);
      if (r.style === "dotted") path.setAttribute("stroke-dasharray", "1.5 3");
      if (r.style === "dashed") path.setAttribute("stroke-dasharray", "5 3");
      const last = p[p.length - 1];
      if (e.tip) {
        const [tx, ty] = e.tip, dx = tx - last[0], dy = ty - last[1], len = Math.hypot(dx, dy) || 1;
        const nx = -dy / len, ny = dx / len, hw = 3.5 + width / 2;
        if ((r.head || "normal") === "tee") {
          svg("line", { x1: last[0], y1: last[1], x2: tx, y2: ty, stroke: col, "stroke-width": width }, g);
          svg("line", { x1: tx + nx * (hw + 1.5), y1: ty + ny * (hw + 1.5), x2: tx - nx * (hw + 1.5), y2: ty - ny * (hw + 1.5), stroke: col, "stroke-width": width + 0.5 }, g);
        } else if ((r.head || "normal") === "normal") {
          svg("polygon", { points: `${tx},${ty} ${last[0] + nx * hw},${last[1] + ny * hw} ${last[0] - nx * hw},${last[1] - ny * hw}`, fill: col, stroke: col }, g);
        }
      }
    }
    if (e.label_lines && e.label_at) lines(g, e.label_lines, e.label_at[0], e.label_at[1], font.edge_size, "cmap-edge-label");
    const t = svg("title", {}, g);
    t.textContent = `${e.from} → ${e.to}: ${r.label}${e.label_lines ? ` (${e.label_lines.join(" ")})` : ""}`;
    edgeEls.set(e.id, g);
  }

  // nodes
  const gN = svg("g", { class: "cmap-nodes" }, S);
  const nodeEls = new Map();
  for (const n of data.nodes) {
    const k = kinds.get(n.kind), f = fills.get(n.fill);
    const fill = f && HEX.test(f.color) ? f.color : "#ffffff";
    const g = svg("g", { class: `cmap-node cmap-${k.role}`, tabindex: 0, role: "button", "aria-pressed": "false", "data-id": n.id }, gN);
    g.setAttribute("aria-label", `${k.label}: ${n.label_lines.join(" ")}`);
    const sw = 1 + (n.emphasis || 0);
    const { x, y, w, h } = n;
    if (k.shape === "ellipse") svg("ellipse", { cx: x, cy: y, rx: w / 2, ry: h / 2, fill, class: "cmap-shape", "stroke-width": sw }, g);
    else if (k.shape === "octagon") {
      svg("polygon", { points: octagon(x, y, w, h), fill, class: "cmap-shape", "stroke-width": sw }, g);
      svg("polygon", { points: octagon(x, y, w, h, 4), fill: "none", class: "cmap-shape-inner" }, g);
    } else svg("rect", { x: x - w / 2, y: y - h / 2, width: w, height: h, rx: 6, fill, class: "cmap-shape", "stroke-width": sw }, g);
    lines(g, n.label_lines, x, y, font.node_size, "cmap-node-label");
    const t = svg("title", {}, g);
    t.textContent = n.label_lines.join(" ");
    nodeEls.set(n.id, g);
  }

  // legend
  const leg = el("div", "cmap-legend");
  leg.appendChild(el("p", "cmap-legend-title", L.legend));
  const row = (title, items) => {
    const d = el("div", "cmap-legend-row");
    d.appendChild(el("span", "cmap-legend-label", title));
    const ul = el("ul", "cmap-legend-items");
    for (const it of items) ul.appendChild(it);
    d.appendChild(ul);
    leg.appendChild(d);
  };
  row(L.fills, data.vocab.fills.filter((f) => f.legend !== false).map((f) => {
    const li = el("li");
    const sw = el("span", "cmap-swatch");
    if (HEX.test(f.color)) sw.style.background = f.color;
    li.append(sw, document.createTextNode(f.label));
    return li;
  }));
  row(L.relations, data.vocab.relations.map((r) => {
    const li = el("li");
    const s = svg("svg", { width: 28, height: 10, class: "cmap-legend-line", "aria-hidden": "true" });
    const ln = svg("line", { x1: 1, y1: 5, x2: 25, y2: 5, stroke: stroke(r), "stroke-width": r.width || 1 }, s);
    if (r.style === "dotted") ln.setAttribute("stroke-dasharray", "1.5 3");
    if (r.style === "dashed") ln.setAttribute("stroke-dasharray", "5 3");
    if ((r.head || "normal") === "tee") svg("line", { x1: 25, y1: 1, x2: 25, y2: 9, stroke: stroke(r), "stroke-width": 1.5 }, s);
    else if ((r.head || "normal") === "normal") svg("polygon", { points: "27,5 21,2 21,8", fill: stroke(r) }, s);
    li.append(s, document.createTextNode(r.description ? `${r.label} (${r.description})` : r.label));
    return li;
  }));
  row(L.kinds, data.vocab.node_kinds.map((k) => el("li", null, `${k.label}: ${k.shape}`)));
  if (data.meta.legend_note) leg.appendChild(el("p", "cmap-legend-note", data.meta.legend_note));
  root.appendChild(leg);
  host.appendChild(root);

  // fit / actual size
  let fit = options.fit !== false;
  const applyFit = () => {
    S.setAttribute("width", fit ? "100%" : String(W));
    S.setAttribute("height", fit ? "" : String(H));
    if (fit) S.removeAttribute("height");
    fitBtn.textContent = fit ? L.actual : L.fit;
    fitBtn.setAttribute("aria-pressed", String(!fit));
  };
  fitBtn.addEventListener("click", () => { fit = !fit; applyFit(); });
  applyFit();

  // selection
  const byId = new Map(data.nodes.map((n) => [n.id, n]));
  let selected = null;
  const paint = () => {
    const near = new Set(), on = new Set();
    if (selected) {
      for (const e of data.edges) if (e.from === selected || e.to === selected) { on.add(e.id); near.add(e.from); near.add(e.to); }
    }
    root.classList.toggle("cmap-has-selection", !!selected);
    for (const [id, g] of nodeEls) {
      g.classList.toggle("cmap-selected", id === selected);
      g.classList.toggle("cmap-near", near.has(id) && id !== selected);
      g.setAttribute("aria-pressed", String(id === selected));
    }
    for (const [id, g] of edgeEls) g.classList.toggle("cmap-on", on.has(id));
  };
  const payload = (n) => {
    const k = kinds.get(n.kind);
    const p = { node: n, kind: k, role: k.role, related: n.related || [] };
    if (k.role === "actor") p.persons = n.persons || [];
    else p.members = n.members || [];
    return p;
  };
  const set = (id) => {
    selected = id;
    paint();
    const n = id ? byId.get(id) : null;
    status.textContent = n ? L.selected(n.label_lines.join(" ")) : L.cleared;
    onSelect(n ? payload(n) : null);
  };
  const toggle = (id) => set(selected === id ? null : id);
  const onClick = (ev) => {
    const g = ev.target.closest && ev.target.closest(".cmap-node");
    if (g && S.contains(g)) toggle(g.getAttribute("data-id"));
  };
  const onKey = (ev) => {
    if (ev.key === "Escape" && selected) { set(null); return; }
    const g = ev.target.closest && ev.target.closest(".cmap-node");
    if (g && (ev.key === "Enter" || ev.key === " ")) { ev.preventDefault(); if (!ev.repeat) toggle(g.getAttribute("data-id")); }
  };
  S.addEventListener("click", onClick);
  root.addEventListener("keydown", onKey);
  if (options.initial && byId.has(options.initial)) { selected = options.initial; paint(); }

  return {
    el: root,
    get selected() { return selected; },
    select(id) {
      if (id == null) { if (selected) set(null); return true; }
      if (!byId.has(String(id))) return false;
      set(String(id));
      nodeEls.get(String(id)).focus?.({ preventScroll: false });
      return true;
    },
    destroy() {
      S.removeEventListener("click", onClick);
      root.removeEventListener("keydown", onKey);
      root.remove();
    },
  };
}
