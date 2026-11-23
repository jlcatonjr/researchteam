// Component test for concept-map.js in Node, with a minimal DOM shim (no browser, no dependencies).
// It checks what does not need layout: what is drawn, selection by click and keyboard, the payload
// given to onSelect, Escape, select() from code, the schema guard and that text from the data is
// never parsed as markup. Run: node templates/concept-map/tests/component.test.mjs [map-file.json]
// (default: the example's map file). Layout and appearance are checked in a browser, by hand.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));

class ClassList {
  constructor(el) { this.el = el; }
  _get() { return new Set((this.el.attrs.class || "").split(/\s+/).filter(Boolean)); }
  _set(s) { this.el.attrs.class = [...s].join(" "); }
  add(...c) { const s = this._get(); c.forEach((x) => s.add(x)); this._set(s); }
  remove(...c) { const s = this._get(); c.forEach((x) => s.delete(x)); this._set(s); }
  contains(c) { return this._get().has(c); }
  toggle(c, on) { const s = this._get(); const v = on === undefined ? !s.has(c) : !!on; v ? s.add(c) : s.delete(c); this._set(s); return v; }
}
class Node_ {
  constructor(tag, ns) { this.tagName = tag; this.ns = ns; this.attrs = {}; this.children = []; this.parentNode = null; this.listeners = {}; this._text = ""; this.style = { setProperty() {} }; this.classList = new ClassList(this); }
  get className() { return this.attrs.class || ""; }
  set className(v) { this.attrs.class = v; }
  get type() { return this.attrs.type; }
  set type(v) { this.attrs.type = v; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; }
  hasAttribute(k) { return k in this.attrs; }
  removeAttribute(k) { delete this.attrs[k]; }
  appendChild(c) { c.parentNode = this; this.children.push(c); return c; }
  append(...cs) { cs.forEach((c) => this.appendChild(c)); }
  remove() { if (this.parentNode) this.parentNode.children = this.parentNode.children.filter((c) => c !== this); this.parentNode = null; }
  set textContent(v) { this.children = []; this._text = String(v); }
  get textContent() { return this._text + this.children.map((c) => c.textContent).join(""); }
  addEventListener(t, f) { (this.listeners[t] ||= []).push(f); }
  removeEventListener(t, f) { this.listeners[t] = (this.listeners[t] || []).filter((x) => x !== f); }
  dispatch(type, ev = {}) {
    const e = { type, target: this, key: ev.key, repeat: false, preventDefault() {}, ...ev };
    for (let n = this; n; n = n.parentNode) for (const f of n.listeners[type] || []) f(e);
  }
  closest(sel) { const cls = sel.replace(/^\./, ""); for (let n = this; n; n = n.parentNode) if (n.classList.contains(cls)) return n; return null; }
  contains(o) { for (let n = o; n; n = n.parentNode) if (n === this) return true; return false; }
  all(pred, out = []) { for (const c of this.children) { if (pred(c)) out.push(c); c.all(pred, out); } return out; }
  focus() {}
  get innerHTML() { throw new Error("innerHTML must not be used"); }
  set innerHTML(v) { throw new Error("innerHTML must not be used"); }
}
globalThis.document = {
  createElement: (t) => new Node_(t, "html"),
  createElementNS: (ns, t) => new Node_(t, ns),
  createTextNode: (t) => { const n = new Node_("#text", "text"); n._text = String(t); return n; },
};

const { mount, membersByRelation, DEFAULT_LABELS } = await import(path.join(here, "..", "concept-map.js"));
const file = process.argv[2] || path.join(here, "..", "example", "map-data.json");
const data = JSON.parse(readFileSync(file, "utf8"));
let failures = 0;
const ok = (cond, msg) => { console.log(`${cond ? "PASS" : "FAIL"} ${msg}`); if (!cond) failures++; };

const host = new Node_("div", "html");
const seen = [];
const map = mount(host, data, { onSelect: (s) => seen.push(s) });
const nodes = host.all((n) => n.classList.contains("cmap-node"));
const edges = host.all((n) => n.classList.contains("cmap-edge"));
ok(nodes.length === data.nodes.length, `draws every node (${nodes.length})`);
ok(edges.length === data.edges.length, `draws every edge (${edges.length})`);
ok(nodes.every((n) => n.getAttribute("role") === "button" && n.getAttribute("tabindex") === "0"), "every node is a focusable button");
ok(nodes.every((n) => n.getAttribute("aria-label")), "every node has an accessible name");

const topic = data.nodes.find((n) => n.members && n.members.length);
const actor = data.nodes.find((n) => n.persons && n.persons.length);
const el = (id) => nodes.find((n) => n.getAttribute("data-id") === id);
// click a label inside the node, as a user would
el(topic.id).children.find((c) => c.tagName === "text").dispatch("click");
let s = seen.at(-1);
ok(s && s.node.id === topic.id && s.role === "topic", "clicking a topic reports it");
ok(Array.isArray(s.members) && s.members.length === topic.members.length, "a topic's payload carries its members");
ok(el(topic.id).getAttribute("aria-pressed") === "true", "the selected node is aria-pressed");
const groups = membersByRelation(data, topic.id);
ok(groups.reduce((a, g) => a + g.members.length, 0) === topic.members.length, "membersByRelation keeps every member once");
const order = data.vocab.relations.map((r) => r.id);
ok(groups.every((g, i) => i === 0 || order.indexOf(groups[i - 1].relation) < order.indexOf(g.relation)
  || (groups[i - 1].relation === g.relation && groups[i - 1].active && !g.active)), "groups follow the vocabulary order, active before passive");
ok(groups.every((g) => g.members.every((m) => m.active === g.active)), "a group holds one direction only");
const on = edges.filter((e) => e.classList.contains("cmap-on")).length;
ok(on === data.edges.filter((e) => e.from === topic.id || e.to === topic.id).length, "incident edges are highlighted");

el(actor.id).dispatch("keydown", { key: "Enter" });
s = seen.at(-1);
ok(s && s.node.id === actor.id && s.role === "actor" && s.persons.length === actor.persons.length, "Enter on an actor reports its persons");
ok(el(topic.id).getAttribute("aria-pressed") === "false", "selecting another node releases the first");

el(actor.id).dispatch("click");
ok(seen.at(-1) === null, "clicking the selected node again clears");
el(actor.id).dispatch("click");
el(actor.id).dispatch("keydown", { key: "Escape" });
ok(seen.at(-1) === null, "Escape clears");

ok(map.select(topic.id) === true && seen.at(-1).node.id === topic.id, "select(id) from code selects and reports");
ok(map.select("no-such-node") === false, "select() refuses an unknown id");
ok(map.select(null) === true && seen.at(-1) === null, "select(null) clears");

// data text is shown as text, never parsed
const evil = structuredClone(data);
evil.nodes[0].label_lines = ["<img src=x onerror=alert(1)>"];
const h2 = new Node_("div", "html");
mount(h2, evil, {});
const spans = h2.all((n) => n.tagName === "tspan").map((n) => n._text);
ok(spans.includes("<img src=x onerror=alert(1)>") && !h2.all((n) => n.tagName === "img").length, "markup in a label stays text");

let threw = false;
try { mount(new Node_("div", "html"), { ...data, schema: "something-else" }, {}); } catch { threw = true; }
ok(threw, "a file of another schema is refused");
ok(typeof DEFAULT_LABELS.hint === "string", "labels are exported for hosts to override");
map.destroy();
ok(host.children.length === 0, "destroy() removes the component");
console.log(failures ? `${failures} failure(s)` : "all passed");
process.exit(failures ? 1 : 0);
