/* connections-flow.js: the Flow view. Papers flow from all papers to topic region to body system to strength of claim
   (default) or POTS subtype. Bands count papers. A small Sankey layout, no library. */
import { S, esc, fmt, pct, passesAll, filtersActive, regionName, regionColor, splitHTML, SPLIT_RULE, barsHTML, topicHTML } from './connections-common.js';

const LAST = {ft:{key:'f', mask:'ftm', list:'ft', head:'Finding type', noun:'finding type'},
  ca:{key:'c', mask:'cam', list:'ca', head:'Strength of claim', noun:'claim type'},
  ps:{key:'p', mask:'psm', list:'ps', head:'POTS subtype', noun:'subtype'}};

const SVGNS = 'http://www.w3.org/2000/svg';
const SINK_LABEL = {s:'No system stated', c:'No claim type stated', p:'No subtype stated', f:'No finding type stated'};

export function createFlow(el){
  const F = S.flow, M = S.map, Pk = M.papers.k, N = M.n_papers;
  let last = 'ft', sel = null, graph = null, visible = false;
  const svg = el.svg;
  const bits = m => { const o = []; for(let i = 0; m; i++, m >>= 1) if(m & 1) o.push(i); return o; };
  const sysKeys = j => F.sysm[j] ? bits(F.sysm[j]).map(i => 's:' + F.sys[i][0]) : ['s:none'];
  const lastKeys = j => { const L = LAST[last], m = F[L.mask][j]; return m ? bits(m).map(i => L.key + ':' + F[L.list][i][0]) : [L.key + ':none']; };
  const isSink = id => id.endsWith(':none');
  const nSubtype = (() => { let n = 0; for(let j = 0; j < N; j++) if(F.psm[j]) n++; return n; })();
  function label(id){
    if(id === 'all') return 'All papers';
    if(id[0] === 'k') return regionName(+id.slice(1));
    const t = id[0], v = id.slice(2);
    if(v === 'none') return SINK_LABEL[t];
    const list = t === 's' ? F.sys : t === 'p' ? F.ps : t === 'f' ? F.ft : F.ca;
    const hit = list.find(x => x[0] === v); return hit ? hit[1] : v;
  }
  function inNode(j, id){
    if(id === 'all') return true;
    if(id[0] === 'k') return Pk[j] === +id.slice(1);
    if(id[0] === 's') return sysKeys(j).includes(id);
    return lastKeys(j).includes(id);
  }
  function shown(){
    const out = [];
    for(let j = 0; j < N; j++){ if(!passesAll(j)) continue; if(last === 'ps' && !F.psm[j]) continue; out.push(j); }
    return out;
  }
  const color = id => id === 'all' ? '#343735' : id[0] === 'k' ? regionColor(+id.slice(1)) : id[0] === 's' ? '#397277' : '#9a5638';

  /* ---------- layout ---------- */
  function layout(papers, W, H, showSink){
    const L = new Map(), uniq = new Map();
    const add = (a, b) => { const k = a + '>' + b; L.set(k, (L.get(k) || 0) + 1); };
    for(const j of papers){
      const k = 'k' + Pk[j]; add('all', k);
      const ss = sysKeys(j), ls = lastKeys(j).filter(l => showSink || !isSink(l));
      for(const s of ss){ add(k, s); for(const l of ls) add(s, l); }
      for(const id of ['all', k, ...ss, ...ls]) uniq.set(id, (uniq.get(id) || 0) + 1);
    }
    const nodes = new Map(), col = id => id === 'all' ? 0 : id[0] === 'k' ? 1 : id[0] === 's' ? 2 : 3;
    const node = id => nodes.get(id) || nodes.set(id, {id, col:col(id), vin:0, vout:0, ins:[], outs:[]}).get(id);
    const links = [];
    for(const [key, v] of L){
      const [a, b] = key.split('>'), s = node(a), t = node(b), l = {s, t, v};
      s.vout += v; t.vin += v; s.outs.push(l); t.ins.push(l); links.push(l);
    }
    const cols = [[], [], [], []];
    for(const n of nodes.values()){ n.v = Math.max(n.vin, n.vout); cols[n.col].push(n); }
    cols.forEach(c => c.sort((a, b) => isSink(a.id) - isSink(b.id) || b.v - a.v || (a.id < b.id ? -1 : 1)));
    const top = 34, bottom = 10, pad = H < 700 ? 5 : 7, nw = 10, right = Math.min(210, W * .26);
    const avail = H - top - bottom;
    const ky = Math.min(...cols.filter(c => c.length).map(c => (avail - (c.length - 1) * pad) / c.reduce((a, n) => a + n.v, 0)));
    const x = c => 8 + c * (W - right - 8 - nw) / 3;
    cols.forEach((c, ci) => {
      const h = c.reduce((a, n) => a + n.v * ky, 0) + (c.length - 1) * pad;
      let y = top + Math.max(0, (avail - h) / 2);
      for(const n of c){ n.x0 = x(ci); n.x1 = n.x0 + nw; n.y0 = y; n.y1 = y + Math.max(1, n.v * ky); y = n.y1 + pad; }
    });
    for(const l of links) l.w = l.v * ky;
    for(const n of nodes.values()){
      n.outs.sort((a, b) => a.t.y0 - b.t.y0); n.ins.sort((a, b) => a.s.y0 - b.s.y0);
      let y = n.y0; for(const l of n.outs){ l.y0 = y + l.w / 2; y += l.w; }
      y = n.y0; for(const l of n.ins){ l.y1 = y + l.w / 2; y += l.w; }
    }
    return {nodes:[...nodes.values()], links, uniq, papers, x, right};
  }
  const path = (l, w) => { const x0 = l.s.x1, x1 = l.t.x0, xm = (x0 + x1) / 2; return `M${x0},${l.y0}C${xm},${l.y0} ${xm},${l.y1} ${x1},${l.y1}`; };
  const mk = (tag, attrs, parent) => { const e = document.createElementNS(SVGNS, tag); for(const k in attrs) e.setAttribute(k, attrs[k]); if(parent) parent.append(e); return e; };

  function draw(){
    if(!visible) return;
    const W = Math.max(760, svg.clientWidth || 0), H = svg.clientHeight || 700;
    if(!svg.clientWidth) return;
    // keep keyboard focus on the same bar across redraws
    const focused = svg.contains(document.activeElement) ? document.activeElement.getAttribute('data-id') : null;
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`); svg.replaceChildren();
    const showSink = last === 'ca' && el.sink.checked;
    const papers = shown();
    graph = layout(papers, W, H, showSink);
    const heads = ['All papers', 'Topic region', 'Body system', LAST[last].head];
    heads.forEach((h, i) => { const t = mk('text', {class:'cx-colhead', x:graph.x(i), y:18}, svg); t.textContent = h; });
    if(!papers.length){ const t = mk('text', {x:W / 2, y:H / 2, 'text-anchor':'middle', class:'cx-empty'}, svg); t.textContent = 'No papers match these filters.'; renderNote(papers); return; }
    mk('defs', {}, svg).innerHTML = '<pattern id="cxHatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="5" height="5" fill="#f3efe9"/><line x1="0" y1="0" x2="0" y2="5" stroke="#d9d3ca" stroke-width="2"/></pattern>';
    const gl = mk('g', {class:'cx-links'}, svg);
    const tip = el.tip;
    for(const l of graph.links){
      const p = mk('path', {class:'cx-link', d:path(l), stroke:isSink(l.t.id) ? '#c9c3b8' : color(l.s.id === 'all' ? l.t.id : l.s.id), 'stroke-width':Math.max(1, l.w)}, gl);
      p.addEventListener('mousemove', e => {
        const src = graph.uniq.get(l.s.id) || 1;
        tip.innerHTML = `<b>${esc(label(l.s.id))}</b> to <b>${esc(label(l.t.id))}</b><span class="cx-sub"><span class="cx-num">${fmt(l.v)}</span> papers, ${pct(l.v, src)}% of the ${fmt(src)} papers in ${esc(label(l.s.id))}</span>`;
        tip.style.display = 'block';
        const box = el.wrap.parentElement.getBoundingClientRect();
        tip.style.left = Math.max(6, Math.min(e.clientX - box.left + 14, box.width - tip.offsetWidth - 6)) + 'px';
        tip.style.top = (e.clientY - box.top + 14) + 'px';
      });
      p.addEventListener('mouseleave', () => { tip.style.display = 'none'; });
    }
    if(sel && graph.nodes.some(n => n.id === sel)){
      const sub = new Map(), inc = k => sub.set(k, (sub.get(k) || 0) + 1);
      for(const j of papers){
        if(!inNode(j, sel)) continue;
        const k = 'k' + Pk[j], ss = sysKeys(j), ls = lastKeys(j).filter(x => showSink || !isSink(x));
        inc('all>' + k); for(const s of ss){ inc(k + '>' + s); for(const x of ls) inc(s + '>' + x); }
      }
      gl.classList.add('cx-dim');
      const gh = mk('g', {class:'cx-hl'}, svg);
      for(const l of graph.links){ const v = sub.get(l.s.id + '>' + l.t.id); if(v) mk('path', {d:path(l), 'stroke-width':Math.max(1, l.w * v / l.v)}, gh); }
    }
    const gn = mk('g', {class:'cx-nodes'}, svg);
    const lastY = {}, labelled = new Set();
    [...graph.nodes].sort((a, b) => a.y0 - b.y0).forEach(n => {
      const y = (n.y0 + n.y1) / 2;
      if(n.y1 - n.y0 < 6 && n.col !== 3) return;
      if(lastY[n.col] != null && y - lastY[n.col] < 13) return;
      lastY[n.col] = y; labelled.add(n.id);
    });
    for(const n of graph.nodes){
      const u = graph.uniq.get(n.id) || 0;
      const g = mk('g', {class:`cx-node${isSink(n.id) ? ' sink' : ''}${sel === n.id ? ' sel' : ''}`, tabindex:0, role:'button',
        'aria-label':`${label(n.id)}: ${fmt(u)} papers`, 'aria-pressed':String(sel === n.id), 'data-id':n.id}, gn);
      mk('rect', {x:n.x0, y:n.y0, width:n.x1 - n.x0, height:Math.max(1, n.y1 - n.y0), fill:isSink(n.id) ? 'url(#cxHatch)' : color(n.id)}, g);
      // a taller invisible target so thin bars are easy to hit
      mk('rect', {class:'cx-hit', x:n.x0 - 3, y:Math.min(n.y0, (n.y0 + n.y1) / 2 - 6), width:n.x1 - n.x0 + 6, height:Math.max(12, n.y1 - n.y0)}, g);
      mk('title', {}, g).textContent = `${label(n.id)}: ${fmt(u)} papers`;
      if(labelled.has(n.id)){
        const maxLen = n.col === 3 ? 30 : 34, t0 = label(n.id), t = t0.length > maxLen ? t0.slice(0, maxLen - 1) + '…' : t0;
        const tx = mk('text', {x:n.x1 + 6, y:(n.y0 + n.y1) / 2 + 4}, g);
        tx.textContent = t + ' '; const num = mk('tspan', {class:'cx-tnum'}, tx); num.textContent = fmt(u);
      }
      const go = () => { sel = sel === n.id ? null : n.id; draw(); renderPanel(); };
      g.addEventListener('click', go);
      g.addEventListener('keydown', e => { if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); go(); svg.querySelector(`[data-id="${CSS.escape(n.id)}"]`)?.focus({preventScroll:true}); } });
    }
    renderNote(papers);
    if(focused) svg.querySelector(`[data-id="${CSS.escape(focused)}"]`)?.focus({preventScroll:true});
  }

  function renderNote(papers){
    const small = F.small_members.map(([s, n]) => `${esc(s)} (${fmt(n)})`).join(', ');
    const act = filtersActive();
    let note;
    if(last === 'ps'){
      const other = F.ps_other.map(([, l, n]) => `${esc(l)} (${fmt(n)})`).join(', ');
      note = `<b>Only ${fmt(nSubtype)} of ${fmt(N)} papers name a POTS subtype</b> in any finding. This view follows those ${fmt(nSubtype)} papers only${act ? `, and ${fmt(papers.length)} of them match your filters` : ''}.` +
        (other ? ` Subtypes named by fewer than ${fmt(F.fold_min)} papers are grouped as Other subtypes: ${other}.` : '');
    } else if(last === 'ft'){
      const other = F.ft_other.map(([, l, n]) => `${esc(l)} (${fmt(n)})`).join(', ');
      note = `Finding type says what each finding is about: a mechanism or biomarker, a treatment, symptoms, diagnosis, or conditions that occur together. A paper with several kinds of finding sits in each band.` +
        (other ? ` Types found in fewer than ${fmt(F.fold_min)} papers are grouped as Other finding types: ${other}.` : '');
    } else {
      let none = 0; for(const j of papers) if(!F.cam[j]) none++;
      const other = F.ca_other.map(([, l, n]) => `${esc(l)} (${fmt(n)})`).join(', ');
      note = `Strength of claim is what each finding says about cause, not proof. ${fmt(papers.length - none)} of ${fmt(papers.length)} papers shown state a claim type. ` +
        (el.sink.checked ? `The hatched bar holds the ${fmt(none)} that do not.` : `The ${fmt(none)} that do not are hidden.`) +
        (other ? ` Other claim types: ${other}.` : '');
    }
    el.note.innerHTML = note;
    el.legend.innerHTML = `Bands count papers. A paper whose findings touch several body systems or ${LAST[last].noun}s sits in each of those bands, so later columns add up to more than the total. Smaller systems holds findings tagged ${small}.`;
  }

  /* ---------- panel ---------- */
  function overviewHTML(){
    const papers = graph ? graph.papers : shown();
    let h = `<p class="cx-kicker">Overview</p><h2>${fmt(papers.length)} papers</h2>`;
    if(last === 'ps'){
      const counts = F.ps.map(([v, l], i) => [l, papers.filter(j => (F.psm[j] >> i) & 1).length]);
      h += `<p>Most papers never say which POTS subtype they mean. Of the ${fmt(papers.length)} shown that do:</p>
        <ul class="cx-rlist">${counts.map(([l, n]) => `<li><span class="cx-sw" style="background:#9a5638"></span><span>${esc(l)}</span><span class="cx-num">${fmt(n)}</span></li>`).join('')}</ul>
        <p class="cx-sub">A paper can name more than one subtype.</p>`;
    } else if(last === 'ft'){
      const counts = F.ft.map(([v, l], i) => [l, papers.filter(j => (F.ftm[j] >> i) & 1).length]);
      h += `<p>What the findings in these papers are about. Papers per finding type:</p>
        <ul class="cx-rlist">${counts.map(([l, n]) => `<li><span class="cx-sw" style="background:#9a5638"></span><span>${esc(l)}</span><span class="cx-num">${fmt(n)}</span></li>`).join('')}</ul>
        <p class="cx-sub">A paper can have findings of more than one type.</p>`;
    } else {
      const ix = v => F.ca.findIndex(x => x[0] === v);
      const nc = (i) => i < 0 ? 0 : papers.filter(j => (F.cam[j] >> i) & 1).length;
      h += `<p><span class="cx-num">${fmt(nc(ix('correlational-only')))}</span> papers report a correlation and <span class="cx-num">${fmt(nc(ix('causal-claim')))}</span> make a causal claim somewhere in their findings. A claim is what a paper says, not proof.</p>`;
    }
    h += `<p class="cx-sub">Pick any bar to follow its papers through every column and see where they disagree. Hover a band for its count.</p>
      <h3>Biggest disagreements on the map</h3><p class="cx-sub">${SPLIT_RULE}</p>${M.top_splits.slice(0, 4).map(splitHTML).join('')}`;
    return h;
  }
  function nodeHTML(){
    const id = sel, info = F.info[id], u = graph ? graph.uniq.get(id) || 0 : 0, tot = graph ? graph.papers.length : 0;
    let h = `<p class="cx-kicker"><button type="button" class="cx-linkbtn" id="cxFlowBack">Back to overview</button></p><h2>${esc(label(id))}</h2>
      <p class="cx-sub"><span class="cx-num">${fmt(u)}</span> papers here, ${pct(u, tot)}% of the papers shown.</p>`;
    if(info){
      h += `<h3>Most studied in this band</h3>${barsHTML(info.top)}
        <p class="cx-sub">Counts are papers, from the ${fmt(info.nf)} findings in this band${filtersActive() ? ', using all papers, not your filters' : ''}.</p>
        <h3>Where papers disagree</h3>
        <p class="cx-sub">${info.ns ? `${fmt(info.ns)} direction flips among the papers in this band. ${SPLIT_RULE}` : 'No direction flips among the papers in this band.'}</p>
        ${info.splits.map(splitHTML).join('')}`;
    } else if(isSink(id)){
      h += `<p>These papers have no ${id[0] === 's' ? 'body system' : LAST[last].noun} recorded in any finding.</p>`;
    } else if(id === 'all'){
      h += `<p>Every paper shown. Pick a region, system or ${LAST[last].noun} bar to see what it holds.</p>`;
    }
    return h;
  }
  function renderPanel(){
    const pn = el.panel;
    let byRegion = null;
    if(S.qMatch){ const c = new Map(); for(const j of shown()) c.set(Pk[j], (c.get(Pk[j]) || 0) + 1); byRegion = [...c].sort((a, b) => b[1] - a[1]); }
    pn.innerHTML = topicHTML(byRegion) + (sel && graph && graph.nodes.some(n => n.id === sel) ? nodeHTML() : overviewHTML());
    pn.querySelectorAll('[data-k]').forEach(b => b.onclick = () => { sel = 'k' + b.dataset.k; draw(); renderPanel(); });
    const back = pn.querySelector('#cxFlowBack'); if(back) back.onclick = () => { sel = null; draw(); renderPanel(); };
  }

  function setLast(v){
    last = LAST[v] ? v : 'ft'; sel = null;
    el.lastBtns.forEach(b => { const on = b.dataset.last === last; b.classList.toggle('on', on); b.setAttribute('aria-pressed', String(on)); });
    el.sinkWrap.hidden = last !== 'ca';
    draw(); renderPanel();
  }
  el.lastBtns.forEach(b => b.onclick = () => { setLast(b.dataset.last); el.onLast && el.onLast(last); });
  el.sink.onchange = () => { draw(); renderPanel(); };
  new ResizeObserver(() => draw()).observe(svg);

  return {
    show(){ visible = true; draw(); renderPanel(); },
    hide(){ visible = false; el.tip.style.display = 'none'; },
    refresh(){ draw(); renderPanel(); },
    reset(){ sel = null; draw(); renderPanel(); },
    setLast, get last(){ return last; }
  };
}
