// Home page: POTS constellation (POTS in the middle, conditions around it sized by papers, POTS-specific topics
// between them) and the "What stands out" band. Data: data/home_map.json and data/home_stand.json, both written by
// site_tools/build_home_data.py from the site data on every rebuild. Counts leave out exclude-flagged papers.
import { condLabel } from './labels.js';

const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const fmt = n => Number(n).toLocaleString('en-US');
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const NS = 'http://www.w3.org/2000/svg';
function el(tag, attrs = {}, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
const getJSON = p => fetch(p).then(r => { if (!r.ok) throw new Error(p + ' ' + r.status); return r.json(); });
// Visible entity name: first letter capitalised unless it already starts with a capital or digit, or its first word looks
// like a gene or symbol (a capital or digit after the first letter: IL-6, mRNA). Links keep the raw name.
// Same rule as display() in site_tools/build_start_here.py and site_tools/signals_rules.py.
const displayName = name => {
  const s = String(name ?? ''), first = s.split(' ')[0];
  if (!s || !/^[a-z]/.test(s) || /[A-Z0-9]/.test(first.slice(1))) return s;
  return s[0].toUpperCase() + s.slice(1);
};
const DIRW = { elevated: 'higher', 'depleted/reduced': 'lower', 'no significant difference': 'no different' };

function tallyHTML(t) {
  if (!t) return '';
  return `<span class="tally">${esc(displayName(t.e))} in ${esc(condLabel(t.c))}: <span class="u">▲ ${fmt(t.up)} higher</span> <span class="d">▼ ${fmt(t.dn)} lower</span> <span class="n">${fmt(t.nu)} no difference</span></span>`;
}

// ---------- page shell: mobile menu and search ----------
function shell() {
  const t = document.getElementById('mobileNavToggle'), nav = document.getElementById('primaryNav');
  t?.addEventListener('click', () => {
    const open = t.getAttribute('aria-expanded') === 'true';
    t.setAttribute('aria-expanded', String(!open));
    nav?.toggleAttribute('data-open', !open);
  });
  document.getElementById('searchForm')?.addEventListener('submit', e => {
    e.preventDefault();
    const q = document.getElementById('curiosityInput').value.trim();
    location.href = 'search' + (q ? '?q=' + encodeURIComponent(q) : '');
  });
}

// ---------- What stands out ----------
function stand(s) {
  const host = document.getElementById('stand'); if (!host) return;
  const c = s.cex, n = s.nex, u = s.uex;
  const side = (k, d) => `${fmt(k)} ${k === 1 ? 'paper reports' : 'papers report'} it ${DIRW[d] || esc(d)}`;
  host.innerHTML = `
    <h2>What stands out</h2>
    <div class="stand-grid">
      <a class="stand-card" href="discover#contra"><p class="k">Where studies disagree</p><p class="v">${fmt(s.contra_total)}</p>
        <p class="ex">For example, <b>${esc(displayName(c.e))}</b> in ${esc(condLabel(c.c))}: ${side(c.a, c.da)}, ${side(c.b, c.db)}.</p><span class="more">See the disagreements</span></a>
      <a class="stand-card" href="discover#nulls"><p class="k">Tested and found nothing</p><p class="v">${fmt(s.nulls)}</p>
        <p class="ex">For example, a ${esc(n.year)} ${esc(condLabel(n.c))} study of <b>${esc(displayName(n.e))}</b>: “${esc(n.q)}”</p><span class="more">See the null results</span></a>
      <a class="stand-card" href="discover#under"><p class="k">Barely studied</p><p class="v">${fmt(s.under_total)}</p>
        <p class="ex">For example, <b>${esc(displayName(u.e))}</b> and ${esc(condLabel(u.c))}: ${fmt(u.n)} papers so far, ${fmt(u.nf)} findings.</p><span class="more">See what needs more work</span></a>
    </div>`;
}

// ---------- tooltip inside the stage, clamped to its box ----------
function makeTip(container) {
  const tip = document.createElement('div'); tip.className = 'tip'; container.appendChild(tip);
  return {
    el: tip,
    show(html, x, y, live) {
      tip.innerHTML = html; tip.classList.add('on'); tip.classList.toggle('live', !!live);
      const W = container.clientWidth, H = container.clientHeight, w = tip.offsetWidth, h = tip.offsetHeight;
      let lx = x + 16, ly = y + 14;
      if (lx + w > W - 8) lx = x - w - 16;
      if (lx < 8) lx = Math.max(8, Math.min(W - w - 8, x - w / 2));
      if (ly + h > H - 8) ly = y - h - 14;
      if (ly < 8) ly = 8;
      tip.style.left = lx + 'px'; tip.style.top = ly + 'px';
    },
    hide() { tip.classList.remove('on', 'live'); }
  };
}

// Pointer drift: nodes near the cursor lean toward it, eased at .16 per frame. strength 0 = fixed.
function drift(target, nodes, onFrame, width) {
  const m = new Map(nodes.map(n => [n.id, { x: 0, y: 0, tx: 0, ty: 0 }]));
  let frame = 0;
  const step = () => {
    let moving = false;
    m.forEach(s => { const dx = s.tx - s.x, dy = s.ty - s.y; s.x += dx * .16; s.y += dy * .16; if (Math.abs(dx) > .1 || Math.abs(dy) > .1) moving = true; });
    onFrame(m);
    frame = moving ? requestAnimationFrame(step) : 0;
  };
  const kick = () => { if (!frame) frame = requestAnimationFrame(step); };
  const move = ev => {
    if (ev.pointerType === 'touch') return;
    const b = target.getBoundingClientRect(); const px = ev.clientX - b.left, py = ev.clientY - b.top;
    const reach = Math.min(260, Math.max(180, width * .24));
    nodes.forEach(n => {
      const s = m.get(n.id); if (!n.strength) { s.tx = 0; s.ty = 0; return; }
      const dx = px - n.x, dy = py - n.y; const inf = Math.max(0, 1 - Math.hypot(dx, dy) / reach);
      s.tx = dx * .035 * inf * n.strength; s.ty = dy * .035 * inf * n.strength;
    });
    kick();
  };
  const leave = () => { m.forEach(s => { s.tx = 0; s.ty = 0; }); kick(); };
  if (!reduceMotion) { target.addEventListener('pointermove', move); target.addEventListener('pointerleave', leave); }
  onFrame(m);
  return { m, stop() { target.removeEventListener('pointermove', move); target.removeEventListener('pointerleave', leave); cancelAnimationFrame(frame); } };
}

// Card box relative to the stage, or null when the card does not sit over the graph (phones).
function cardBox(stage) {
  const c = document.querySelector('.hero-info'); if (!c || getComputedStyle(c.parentElement).position !== 'absolute') return null;
  const a = c.getBoundingClientRect(), b = stage.getBoundingClientRect();
  const box = { left: a.left - b.left - 12, right: a.right - b.left + 12, top: a.top - b.top - 12, bottom: a.bottom - b.top + 12 };
  if (box.bottom < 0 || box.top > b.height || box.right < 0) return null;
  return box;
}

// Labels placed in priority order; the first free candidate wins. Optional labels with no free spot get
// class is-crowded (hidden until their node is hovered or pinned).
function placeLabels(items, W, H, card, dots = []) {
  const pad = 5, placed = [];
  const hit = (a, b) => a.x < b.x + b.w + pad && a.x + a.w + pad > b.x && a.y < b.y + b.h + pad && a.y + a.h + pad > b.y;
  const inCard = b => card && b.x < card.right && b.x + b.w > card.left && b.y < card.bottom && b.y + b.h > card.top;
  items.forEach(it => {
    const t = it.text; t.classList.remove('is-crowded');
    const r = it.r || 4;
    const cands = it.cands || [['start', r + 5, 4], ['end', -r - 5, 4], ['middle', 0, -r - 6], ['middle', 0, r + 13], ['start', r + 5, -9], ['end', -r - 5, -9], ['start', r + 5, 16], ['end', -r - 5, 16]];
    for (const [anchor, dx, dy] of cands) {
      t.setAttribute('text-anchor', anchor); t.setAttribute('x', it.x + dx); t.setAttribute('y', it.y + dy);
      const bb = t.getBBox(); const box = { x: bb.x, y: bb.y, w: bb.width, h: bb.height };
      const inside = box.x >= 4 && box.x + box.w <= W - 4 && box.y >= 4 && box.y + box.h <= H - 4;
      if (inside && !inCard(box) && !placed.some(o => hit(box, o)) && !dots.some(o => o.id !== it.n.id && hit(box, o))) { it.place = [anchor, dx, dy]; it.box = box; placed.push(box); return; }
    }
    it.place = cands[0];
    t.setAttribute('text-anchor', cands[0][0]); t.setAttribute('x', it.x + cands[0][1]); t.setAttribute('y', it.y + cands[0][2]);
    const bb = t.getBBox(); it.box = { x: bb.x, y: bb.y, w: bb.width, h: bb.height };
    if (it.optional) t.classList.add('is-crowded'); else placed.push(it.box);
  });
}

// ---------- the "i" popover, written from the rules the data was built with ----------
function infoText(D) {
  const R = D.rules;
  const times = R.lift === 2 ? 'twice' : `${R.lift} times`;
  const hidden = D.hidden.slice(0, 4).map(h => h[0]);
  return `Each condition is sized by the number of papers that report findings for it. Its line to POTS is thicker when more papers report findings for both. `
    + `The topics in between are the ones most specific to POTS: named in at least ${R.floor} POTS papers and at least ${times} as common in POTS papers as in all papers. The top ${R.top_specific} are shown. `
    + (hidden.length ? `Left out because nearly every study measures them: ${hidden.join(', ')} and similar. ` : '')
    + `Topics in lighter italic are bridges: for each condition, up to ${R.bridges_per_cond} topics it shares most with POTS. `
    + `A ring marks a measured topic (a body measure, gene or protein, or cell type, or a chemical where no more than ${Math.round(R.treatment_share_max * 100)}% of its POTS findings come from treatment studies) where some POTS papers report it higher and some lower. Drugs and treatments get no ring, but their tooltips still show the counts. Dotted lines join the ${R.pairs_drawn} pairs of conditions that share the most topics. `
    + `Hover or tap a condition to see the topics it shares with POTS on its line. Retracted papers and correction notices are left out.`;
}

// ---------- constellation ----------
function constellation(D) {
  const stage = document.getElementById('stage'), host = document.getElementById('graph');
  const status = document.getElementById('graphStatus');
  const tip = makeTip(stage);
  const DEFAULT = 'Hover or tap a dot to see its neighborhood. Tap it again, or tap empty space, to let go.';
  status.textContent = DEFAULT;
  const pop = document.getElementById('infoPop'); if (pop) pop.textContent = infoText(D);
  const list = document.getElementById('condList');
  if (list) list.innerHTML = D.conds.map(c => `<li><a href="condition?c=${encodeURIComponent(c.c)}">${esc(condLabel(c.c))}: ${fmt(c.n)} papers, ${fmt(c.both)} also report POTS findings</a></li>`).join('');

  // Ring order: start with the largest condition, then always the unplaced one sharing most with the last.
  const ccAll = D.cc;
  const ccScore = (a, b) => (ccAll.find(r => (r.a === a && r.b === b) || (r.a === b && r.b === a)) || { s: 0 }).s;
  const ring = [D.conds[0].c]; const rest = new Set(D.conds.slice(1).map(c => c.c));
  while (rest.size) { const last = ring[ring.length - 1]; let best = null; rest.forEach(c => { if (!best || ccScore(last, c) > ccScore(last, best)) best = c; }); ring.push(best); rest.delete(best); }
  const CC = D.cc.slice(0, D.rules.pairs_drawn);

  let W = 0, H, cx, cy, N, L, LL = [], items, motion, pinned = null, drawn = false;
  const linkFor = n => n.kind === 'cond' ? [`condition?c=${encodeURIComponent(n.id)}`, `See all ${n.label} findings`]
    : n.kind === 'core' ? ['condition?c=POTS', 'See all POTS findings']
    : [`entity?e=${encodeURIComponent(n.t.ent)}`, `See findings for ${n.label}`];

  function layout() {
    host.innerHTML = '';
    motion?.stop();
    stage.style.height = '';
    W = stage.clientWidth; H = stage.clientHeight;
    const card = cardBox(stage), mobile = !card;
    // phones: the stage is cut to the drawing's own height, so there is no empty band above or below the map
    if (mobile) { H = Math.round(2 * W * .34 * 1.15 + 92); stage.style.height = H + 'px'; }
    cx = mobile ? W / 2 : Math.max(card.right + (W - card.right) * .5, W * .6); cy = H * (mobile ? .5 : .47);
    const R = mobile ? Math.min(W * .34, H * .4) : Math.min(H * .37, (W - card.right) / 2 - 90);
    const maxC = Math.max(...D.conds.map(c => c.n)), maxT = Math.max(...D.topics.map(t => t.np)), maxB = Math.max(...D.conds.map(c => c.both));
    const sy = mobile ? 1.15 : 1;
    N = new Map();
    N.set('POTS', { id: 'POTS', kind: 'core', x: cx, y: cy, r: 9, label: 'POTS', strength: 0 });
    const ang = {};
    ring.forEach((c, i) => {
      const a = -Math.PI / 2 + i * 2 * Math.PI / ring.length; ang[c] = a;
      const d = D.conds.find(x => x.c === c);
      N.set(c, { id: c, kind: 'cond', x: cx + R * Math.cos(a), y: cy + R * Math.sin(a) * sy, r: 3 + 8 * Math.sqrt(d.n / maxC), label: condLabel(c), d, strength: 7 });
    });
    // topics: desired angle = weighted mean of linked conditions, then spread apart on two inner radii
    const T = D.topics.map((t, i) => {
      let sx = 0, syy = 0; t.links.forEach(([c, n]) => { if (ang[c] == null) return; sx += Math.cos(ang[c]) * n; syy += Math.sin(ang[c]) * n; });
      const a = t.links.length ? Math.atan2(syy, sx) : Math.PI * (.15 + i * .07);
      return { t, a };
    }).sort((p, q) => p.a - q.a);
    const sep = 2 * Math.PI / T.length * .9;
    for (let it = 0; it < 200; it++) for (let i = 0; i < T.length; i++) {
      const p = T[i], q = T[(i + 1) % T.length]; let d = q.a - p.a; if (i === T.length - 1) d += 2 * Math.PI;
      if (d < sep) { const m = (sep - d) / 2; p.a -= m; q.a += m; }
    }
    T.forEach((p, i) => {
      const rr = R * (i % 2 ? .62 : .44), t = p.t;
      N.set('t:' + t.e, { id: 't:' + t.e, kind: 'topic', x: cx + rr * Math.cos(p.a), y: cy + rr * Math.sin(p.a) * sy, r: 2.5 + 4.5 * Math.sqrt(t.np / maxT), label: displayName(t.e), t, strength: 12 });
    });
    L = [];
    D.conds.forEach(c => L.push({ a: 'POTS', b: c.c, kind: 'spoke', w: .6 + 1.8 * c.both / maxB, bend: 0 }));
    D.topics.forEach(t => {
      L.push({ a: 'POTS', b: 't:' + t.e, kind: 'tp', w: t.kind === 'bridge' ? .5 : .7, bend: 0, bridge: t.kind === 'bridge' });
      t.links.forEach(([c]) => { if (N.has(c)) L.push({ a: 't:' + t.e, b: c, kind: 'tc', w: .6, bend: 10 }); });
    });
    CC.forEach(r => L.push({ a: r.a, b: r.b, kind: 'cc', w: .6 + r.s * .35, bend: -R * .28, r }));

    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, 'aria-hidden': 'true' }); host.appendChild(svg);
    const gL = el('g', {}, svg), gN = el('g', {}, svg), gT = el('g', {}, svg);
    L.forEach(l => {
      l.el = el('path', { class: 'lk', fill: 'none', stroke: '#8fa39c', 'stroke-width': l.w.toFixed(2), opacity: l.kind === 'cc' ? .28 : l.kind === 'tc' ? .22 : .42, 'stroke-dasharray': l.kind === 'cc' ? '2 4' : l.bridge ? '1 3' : '' }, gL);
      if (l.kind === 'cc') {
        l.hit = el('path', { class: 'cc-hit', fill: 'none', stroke: 'transparent', 'stroke-width': 10 }, gL);
        l.hit.addEventListener('pointerenter', e => { if (e.pointerType !== 'touch') showCC(l, e); });
        l.hit.addEventListener('pointerleave', () => { if (!pinned) unfocus(); });
      }
    });
    N.forEach(n => {
      if (n.kind === 'topic' && n.t.disagree) n.ring = el('circle', { cx: n.x, cy: n.y, r: n.r + 4, fill: 'none', stroke: 'var(--home-rust)', 'stroke-width': 1, class: 'pulse' }, gN);
      n.c = el('circle', { class: 'dot', cx: n.x, cy: n.y, r: n.r, fill: n.kind === 'core' ? 'var(--home-rust)' : n.kind === 'cond' ? '#90b2aa' : n.t.kind === 'bridge' ? '#e2e9e6' : '#c8d8d1', stroke: '#fcfcfa', 'stroke-width': 2 }, gN);
      n.hit = el('circle', { class: 'node-hit', cx: n.x, cy: n.y, r: Math.max(n.r + 6, 12), fill: 'transparent' }, gN);
      n.text = el('text', { class: 'nl ' + n.kind + (n.kind === 'topic' && n.t.kind === 'bridge' ? ' bridge' : '') }, gT); n.text.textContent = n.label;
      n.hit.addEventListener('pointerenter', e => { if (e.pointerType !== 'touch') show(n.id, e); });
      n.hit.addEventListener('pointerleave', e => { if (e.pointerType !== 'touch' && !pinned) unfocus(); });
      n.hit.addEventListener('click', e => { e.stopPropagation(); toggle(n.id, e); });
    });
    const rank = n => n.kind === 'core' ? 0 : n.kind === 'cond' ? 1 : 2;
    items = [...N.values()].sort((a, b) => rank(a) - rank(b) || (b.kind === 'topic' ? b.t.np - a.t.np : b.r - a.r)).map(n => {
      const out = n.kind === 'cond' ? Math.sign(n.x - cx) : 0;
      const cands = n.kind === 'core' ? [['middle', 0, -16], ['middle', 0, 26]]
        : n.kind === 'cond' ? (out >= 0 ? [['start', n.r + 6, 4], ['middle', 0, -n.r - 6], ['middle', 0, n.r + 14], ['end', -n.r - 6, 4]] : [['end', -n.r - 6, 4], ['middle', 0, -n.r - 6], ['middle', 0, n.r + 14], ['start', n.r + 6, 4]])
        : undefined;
      return { text: n.text, x: n.x, y: n.y, r: n.r, optional: n.kind === 'topic', n, cands };
    });
    // dots are obstacles too, so a topic label never sits on another node's dot (it hides until hover instead)
    placeLabels(items, W, H, card, [...N.values()].map(n => ({ id: n.id, x: n.x - n.r - 1, y: n.y - n.r - 1, w: 2 * n.r + 2, h: 2 * n.r + 2 })));
    // line labels: shared topics on spokes and condition pairs, shown only on hover or pin
    LL = [];
    L.forEach(l => {
      let txt = '';
      if (l.kind === 'spoke') txt = (D.conds.find(c => c.c === l.b).shared || []).slice(0, 2).map(s => displayName(s[0])).join(' · ');
      if (l.kind === 'cc') txt = l.r.shared.slice(0, 2).map(s => displayName(s[0])).join(' · ');
      if (!txt) return;
      const t = el('text', { class: 'll', 'text-anchor': 'middle' }, gT); t.textContent = txt; l.lab = t; t.style.opacity = 0; LL.push(l);
    });
    motion = drift(stage, [...N.values()], frame, W);
    // lines draw in once, spokes first, then topic lines, then condition pairs
    if (!drawn && !reduceMotion) {
      const order = { spoke: 0, tp: 1, tc: 2, cc: 3 }; const seq = [...L].sort((a, b) => order[a.kind] - order[b.kind]);
      seq.forEach((l, i) => {
        const len = l.el.getTotalLength(); l.el.style.strokeDasharray = `${len} ${len}`; l.el.style.strokeDashoffset = len;
        l.el.getBoundingClientRect();
        const delay = 200 + i * 28;
        l.el.style.transition = `stroke-dashoffset 1.3s cubic-bezier(.3,.6,.2,1) ${delay}ms`; l.el.style.strokeDashoffset = 0;
        setTimeout(() => { l.el.style.transition = ''; l.el.style.strokeDasharray = ''; l.el.style.strokeDashoffset = ''; }, delay + 14 * 100);
      });
    }
    drawn = true;
    pinned = null; unfocus();
  }
  const overlap = (b, o) => b.x < o.x + o.width + 2 && b.x + b.width + 2 > o.x && b.y < o.y + o.height + 2 && b.y + b.height + 2 > o.y;
  function placeLineLabel(l) {
    // try a few spots along the line, keep the first that clears every visible label
    const t = l.lab, path = l.el, len = path.getTotalLength();
    const boxes = [...host.querySelectorAll('svg text')].filter(x => x !== t && (x.classList.contains('ll') ? x.style.opacity === '1' : parseFloat(getComputedStyle(x).opacity) > .3)).map(x => x.getBBox());
    for (const f of [.5, .62, .38, .72, .28]) {
      for (const dy of [-5, 12]) {
        const p = path.getPointAtLength(len * f); t.setAttribute('x', p.x); t.setAttribute('y', p.y + dy);
        const b = t.getBBox();
        const inside = b.x > 4 && b.x + b.width < W - 4 && b.y > 4 && b.y + b.height < H - 4;
        if (inside && !boxes.some(o => overlap(b, o))) { l.labAt = [f, dy]; return true; }
      }
    }
    l.labAt = null; return false;
  }
  function showLineLabels(list) {
    LL.forEach(l => { l.lab.style.opacity = 0; l.labAt = null; });
    list.forEach(l => { if (l.lab && placeLineLabel(l)) l.lab.style.opacity = 1; });
  }
  function curve(l, m) {
    const A = N.get(l.a), B = N.get(l.b), oa = m.get(l.a), ob = m.get(l.b);
    const x1 = A.x + oa.x, y1 = A.y + oa.y, x2 = B.x + ob.x, y2 = B.y + ob.y;
    if (!l.bend) return `M ${x1} ${y1} L ${x2} ${y2}`;
    const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
    const dx = mx - cx, dy = my - cy; const d = Math.hypot(dx, dy) || 1;
    return `M ${x1} ${y1} Q ${mx - dx / d * l.bend} ${my - dy / d * l.bend} ${x2} ${y2}`;
  }
  function frame(m) {
    N.forEach(n => {
      const o = m.get(n.id); const x = n.x + o.x, y = n.y + o.y;
      n.c.setAttribute('cx', x); n.c.setAttribute('cy', y); n.hit.setAttribute('cx', x); n.hit.setAttribute('cy', y);
      if (n.ring) { n.ring.setAttribute('cx', x); n.ring.setAttribute('cy', y); }
    });
    items.forEach(it => { const o = m.get(it.n.id); it.text.setAttribute('x', it.x + it.place[1] + o.x); it.text.setAttribute('y', it.y + it.place[2] + o.y); });
    bump(m);
    L.forEach(l => { const d = curve(l, m); l.el.setAttribute('d', d); if (l.hit) l.hit.setAttribute('d', d); });
    const live = LL.filter(l => l.labAt);
    if (live.length) {
      const others = [...host.querySelectorAll('svg text.nl')].filter(x => parseFloat(getComputedStyle(x).opacity) > .3).map(x => x.getBBox());
      live.forEach(l => {
        const len = l.el.getTotalLength(), p = l.el.getPointAtLength(len * l.labAt[0]); l.lab.setAttribute('x', p.x); l.lab.setAttribute('y', p.y + l.labAt[1]);
        if (others.some(o => overlap(l.lab.getBBox(), o))) l.lab.style.opacity = placeLineLabel(l) ? 1 : 0;
      });
    }
  }
  // Drift moves nodes by different amounts, so two labels placed apart can slide into each other. Each frame, a label
  // that now overlaps a label kept before it (focused node first, then POTS, conditions, topics by papers) hides.
  let focusId = null;
  function bump(m) {
    const kept = [], pad = 2;
    const order = focusId ? [...items.filter(it => it.n.id === focusId), ...items.filter(it => it.n.id !== focusId)] : items;
    order.forEach(it => {
      const t = it.text;
      // skip labels that are hidden (crowded) or dimmed behind a focused neighborhood
      const lit = !focusId || t.classList.contains('hot');
      if (!it.box || !lit || (t.classList.contains('is-crowded') && !t.classList.contains('hot'))) { t.classList.remove('is-bumped'); return; }
      const o = m.get(it.n.id), b = { x: it.box.x + o.x, y: it.box.y + o.y, w: it.box.w, h: it.box.h };
      const clash = kept.some(k => b.x < k.x + k.w + pad && b.x + b.w + pad > k.x && b.y < k.y + k.h + pad && b.y + b.h + pad > k.y);
      t.classList.toggle('is-bumped', clash && it.n.id !== focusId);
      if (!clash || it.n.id === focusId) kept.push(b);
    });
  }
  function hood(id) {
    const s = new Set([id]);
    L.forEach(l => { if (l.kind === 'cc' && id !== l.a && id !== l.b) return; if (l.a === id) s.add(l.b); if (l.b === id) s.add(l.a); });
    return s;
  }
  function paint(set, linkTest) {
    N.forEach(n => {
      const on = !set || set.has(n.id);
      n.c.style.opacity = on ? 1 : .15; if (n.ring) n.ring.style.opacity = on ? '' : 0;
      const crowded = n.text.classList.contains('is-crowded');
      n.text.style.opacity = on ? (set && crowded ? 1 : '') : (crowded ? 0 : .12);
      n.text.classList.toggle('hot', !!set && on);
    });
    L.forEach(l => {
      const hot = set && linkTest(l);
      l.el.style.opacity = !set ? '' : hot ? .9 : .06;
      l.el.setAttribute('stroke', hot ? '#4d7b82' : '#8fa39c');
      l.el.setAttribute('stroke-width', (hot ? Math.max(l.w, 1.3) : l.w).toFixed(2));
    });
  }
  function pos(e, n) {
    if (e && e.clientX != null && (e.clientX || e.clientY)) { const b = stage.getBoundingClientRect(); return [e.clientX - b.left, e.clientY - b.top]; }
    const o = motion.m.get(n.id); return [n.x + o.x, n.y + o.y];
  }
  function show(id, e) {
    if (pinned && pinned !== id) return;
    const n = N.get(id); focusId = id;
    // a topic is defined by POTS papers, so POTS and its line to the topic always stay lit with the topic
    if (n.kind === 'core') paint(null); else { const s = hood(id); if (n.kind === 'topic') s.add('POTS'); paint(s, l => (l.a === id || l.b === id)); }
    bump(motion.m);
    showLineLabels(n.kind === 'cond' ? LL.filter(l => (l.kind === 'spoke' && l.b === id) || (l.kind === 'cc' && (l.a === id || l.b === id))) : []);
    let h;
    if (n.kind === 'core') {
      const spec = D.topics.filter(t => t.kind === 'specific').slice(0, 4).map(t => esc(displayName(t.e))).join(', ');
      const near = [...D.conds].sort((a, b) => b.both - a.both).slice(0, 3).map(c => `${esc(condLabel(c.c))} <span class="m">${fmt(c.both)}</span>`).join(', ');
      h = `<b>POTS</b><br><span class="m">${fmt(D.pots.n)} papers report POTS findings.</span><span class="k">Most specific to POTS</span>${spec}<span class="k">Most often studied with</span>${near}`;
    } else if (n.kind === 'cond') {
      const d = n.d;
      h = `<b>${esc(n.label)}</b><br><span class="m">${fmt(d.n)} papers. ${fmt(d.both)} of them also report POTS findings.</span>`;
      if (d.shared.length) h += `<span class="k">Shared with POTS</span>${d.shared.map(s => `${esc(displayName(s[0]))} <span class="m">${fmt(s[1])} POTS, ${fmt(s[2])} here</span>`).join('<br>')}`;
      if (d.split) h += `<span class="k">Where papers split</span>${tallyHTML(d.split)}`;
    } else {
      const t = n.t, lift = t.lift;
      const rel = lift >= 1.5 ? `${lift.toFixed(1)} times as common in POTS papers as in all papers` : lift >= .8 ? 'About as common in POTS papers as in all papers' : 'Less common in POTS papers than in all papers. It links POTS to other conditions';
      h = `<b>${esc(n.label)}</b><br><span class="m">${fmt(t.np)} POTS papers. ${rel}.</span>`;
      const tt = t.tally;
      h += `<span class="k">In POTS papers</span>` + (tt.up + tt.dn + tt.nu ? tallyHTML(tt) : '<span class="m">No higher or lower results outside treatment studies.</span>');
      if (t.links.length) h += `<span class="k">Also studied in</span>${t.links.map(([c, k]) => `${esc(condLabel(c))} <span class="m">${fmt(k)}</span>`).join(', ')}`;
    }
    const isPin = pinned === id;
    const [href, txt] = linkFor(n);
    if (isPin) h += `<a class="go" href="${href}">${esc(txt)} →</a>`;
    const [x, y] = pos(e, n); tip.show(h, x, y, isPin);
    const count = n.kind === 'topic' ? `${fmt(n.t.np)} POTS papers` : n.kind === 'cond' ? `${fmt(n.d.n)} papers` : `${fmt(D.pots.n)} papers`;
    status.innerHTML = `${esc(n.label)}: ${count}. ${isPin ? `<a href="${href}">${esc(txt)}</a>` : 'Tap or click to pin it and get a link.'}`;
  }
  function showCC(l, e) {
    if (pinned) return;
    paint(new Set([l.a, l.b]), x => x === l);
    showLineLabels([l]);
    const r = l.r; const [x, y] = pos(e, N.get(l.a));
    tip.show(`<b>${esc(condLabel(r.a))} and ${esc(condLabel(r.b))}</b><br><span class="m">${fmt(r.both)} papers report findings for both.</span><span class="k">Topics they share</span>${r.shared.map(s => `${esc(displayName(s[0]))} <span class="m">${fmt(s[1])} and ${fmt(s[2])} papers</span>`).join('<br>')}`, x, y);
  }
  function toggle(id, e) {
    if (pinned === id) { pinned = null; unfocus(); return; }
    pinned = null; pinned = id; show(id, e); stage.dataset.pinned = id;
  }
  function unfocus() { focusId = null; paint(null); if (motion) bump(motion.m); tip.hide(); status.textContent = DEFAULT; delete stage.dataset.pinned; showLineLabels([]); }
  function reset() { pinned = null; unfocus(); }
  // Clicking or tapping anywhere off a dot lets go of the pin, so any other dot can be picked next.
  document.addEventListener('click', e => {
    if (!pinned) return;
    if (e.target.closest('.node-hit, .tip a, .graph-status a')) return;
    reset();
  });
  addEventListener('keydown', e => { if (e.key === 'Escape') reset(); });
  layout();
  let rt, lastW = stage.clientWidth;
  addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(() => { if (stage.clientWidth !== lastW) { lastW = stage.clientWidth; layout(); } }, 150); });
  // test hooks for the page checks
  window.__home = { node: id => { const b = stage.getBoundingClientRect(), n = N.get(id), o = motion.m.get(id); return [b.left + n.x + o.x, b.top + n.y + o.y]; }, pinned: () => pinned, ids: () => [...N.keys()] };
}

async function init() {
  shell();
  getJSON('data/home_stand.json').then(stand).catch(() => {});
  try { constellation(await getJSON('data/home_map.json')); }
  catch (err) { const s = document.getElementById('graphStatus'); if (s) s.textContent = 'The map could not load right now. Try the full search instead.'; }
}
init();
