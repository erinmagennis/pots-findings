/* connections-map.js: the Map view. Each dot is a paper placed by its findings (UMAP of mean finding embeddings),
   coloured by topic region. Labels follow the zoom: regions first, then sub-regions, then single papers. */
import { S, esc, fmt, pct, passes, passesAll, filtersActive, regionName, regionColor, reducedMotion,
  paperHref, paperLink, entityHref, splitHTML, SPLIT_RULE, barsHTML, topicHTML, countShown, display, flipTotalText } from './connections-common.js';
import { condLabel } from './labels.js';

const FT = {'mechanism/biomarker':'mechanisms and biomarkers','biomarker/mechanism':'mechanisms and biomarkers','treatment/intervention':'treatments',
  'symptom-burden':'symptom burden','comorbidity':'co-occurring conditions','diagnostic/screening':'diagnosis and screening'};
const AN = {neuro:'nervous system',immune:'immune',autonomic:'autonomic',vascular:'blood vessels',GI:'gut',endocrine:'hormones',
  musculoskeletal:'muscle and bone','connective-tissue':'connective tissue',other:'other systems'};
// zoom levels where more labels appear
const LOD_SUB = 1.8, LOD_PAPER = 4.5, K_MIN = 0.8, K_MAX = 40;

export function createMap(el){
  const cv = el.canvas, ctx = cv.getContext('2d');
  const M = S.map, P = M.papers, N = M.n_papers, Q = M.meta.q;
  let W = 0, H = 0, base = {s:1, ox:0, oy:0}, T = {k:1, x:0, y:0};
  let bx = new Float32Array(N), by = new Float32Array(N);
  let sel = null, hover = null, boxes = [], anim = null, visible = false;
  const font = getComputedStyle(document.body).fontFamily;
  const css = getComputedStyle(document.documentElement);
  const INK = css.getPropertyValue('--ink').trim() || '#242321', LINE = css.getPropertyValue('--line').trim() || '#ded9cf';
  const MUTED = css.getPropertyValue('--muted').trim() || '#716d65';

  // papers grouped by region, so colours are set once per region when drawing
  const byK = M.regions.map(() => []);
  for(let j = 0; j < N; j++) byK[P.k[j]].push(j);
  // hit-test grid in data space
  const G = 64, cell = (Q + 1) / G, grid = new Map();
  for(let j = 0; j < N; j++){ const key = Math.floor(P.x[j] / cell) * G + Math.floor(P.y[j] / cell); (grid.get(key) || grid.set(key, []).get(key)).push(j); }

  const SX = j => T.x + T.k * bx[j], SY = j => T.y + T.k * by[j];
  const sxq = x => T.x + T.k * (base.ox + base.s * x), syq = y => T.y + T.k * (base.oy + base.s * y);

  function resize(){
    const r = cv.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
    if(!r.width) return;
    const oldW = W, oldH = H;
    W = r.width; H = r.height; cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const pad = W < 600 ? 18 : 34, s = Math.min((W - 2 * pad) / Q, (H - 2 * pad) / Q);
    base = {s, ox:(W - s * Q) / 2, oy:(H - s * Q) / 2};
    for(let j = 0; j < N; j++){ bx[j] = base.ox + s * P.x[j]; by[j] = base.oy + s * P.y[j]; }
    if(oldW && (oldW !== W || oldH !== H)) T = {k:T.k, x:T.x + (W - oldW) / 2, y:T.y + (H - oldH) / 2};
    draw();
  }

  /* ---------- drawing ---------- */
  function roundRect(x, y, w, h, r){ ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
  const hit = (b, x0, y0, x1, y1) => x0 < b.x1 && x1 > b.x0 && y0 < b.y1 && y1 > b.y0;
  function place(x0, y0, x1, y1){
    if(x0 < 0 || x1 > W || y0 < 0 || y1 > H) return false;
    for(const b of boxes) if(hit(b, x0 - 2, y0 - 1, x1 + 2, y1 + 1)) return false;
    return true;
  }
  function pill(txt, x, y, opts){
    ctx.font = `${opts.weight || 500} ${opts.size}px ${font}`;
    const w = ctx.measureText(txt).width + 2 * opts.padX, h = opts.size + 2 * opts.padY;
    if(x + w / 2 < 0 || x - w / 2 > W || y < 0 || y > H) return null;
    x = Math.max(w / 2 + 4, Math.min(W - w / 2 - 4, x));
    const x0 = x - w / 2, y0 = y - h / 2;
    if(!place(x0, y0, x0 + w, y0 + h)) return null;
    ctx.globalAlpha = opts.alpha ?? .94;
    ctx.fillStyle = '#fffdf9'; ctx.strokeStyle = opts.stroke || LINE; ctx.lineWidth = opts.lineWidth || 1;
    roundRect(x0, y0, w, h, h / 2); ctx.fill(); ctx.stroke();
    ctx.fillStyle = opts.color || INK; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(txt, x, y + .5); ctx.globalAlpha = 1;
    const b = {x0, y0, x1:x0 + w, y1:y0 + h, ...opts.data}; boxes.push(b); return b;
  }
  function cut(s, n){ return s.length > n ? s.slice(0, n - 1).trimEnd() + '…' : s; }

  function draw(){
    if(!W) return;
    ctx.clearRect(0, 0, W, H);
    const r = Math.max(1.6, Math.min(5, 1.5 * Math.sqrt(T.k) + .3));
    const searching = !!S.qMatch;
    const on = j => passes(j) && (sel == null || P.k[j] === sel) && (!searching || S.qMatch[j] === 1);
    const inView = j => { const x = SX(j), y = SY(j); return x > -6 && x < W + 6 && y > -6 && y < H + 6; };
    ctx.fillStyle = '#e2ded5';
    const q = r * .55;
    for(let j = 0; j < N; j++){ if(on(j) || !inView(j)) continue; ctx.fillRect(SX(j) - q, SY(j) - q, 2 * q, 2 * q); }
    ctx.globalAlpha = .78;
    for(let k = 0; k < byK.length; k++){
      ctx.fillStyle = regionColor(k); ctx.beginPath();
      for(const j of byK[k]){ if(!on(j) || !inView(j)) continue; const x = SX(j), y = SY(j); ctx.moveTo(x + r, y); ctx.arc(x, y, r, 0, 6.2832); }
      ctx.fill();
    }
    ctx.globalAlpha = 1;
    if(searching){
      ctx.strokeStyle = '#fffdf9'; ctx.lineWidth = 1.2;
      for(let j = 0; j < N; j++){ if(!on(j) || !inView(j)) continue; ctx.fillStyle = regionColor(P.k[j]); ctx.beginPath(); ctx.arc(SX(j), SY(j), r + 1.3, 0, 6.2832); ctx.fill(); ctx.stroke(); }
    }
    if(hover != null){ ctx.strokeStyle = INK; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(SX(hover), SY(hover), r + 4, 0, 6.2832); ctx.stroke(); }
    drawLabels(r, on);
  }

  function drawLabels(r, on){
    boxes = [];
    const small = W < 600, k = T.k;
    // keep labels clear of the zoom buttons and the hint
    for(const n of el.reserve || []){ const r = n.getBoundingClientRect(), c = cv.getBoundingClientRect(); if(r.width) boxes.push({x0:r.left - c.left, x1:r.right - c.left, y0:r.top - c.top, y1:r.bottom - c.top}); }
    const regions = [...M.regions].sort((a, b) => (b.id === sel) - (a.id === sel) || b.n - a.n);
    const regionPill = (c, size) => {
      const words = small && k < 1.4 ? c.label.slice(0, 1) : c.label.slice(0, 2);
      const dim = sel != null && sel !== c.id;
      return pill(cut(words.join(', '), 44), sxq(c.cx), syq(c.cy), {size, padX:8, padY:4, weight:sel === c.id ? 650 : 550,
        alpha:dim ? .45 : .95, stroke:sel === c.id ? regionColor(c.id) : LINE, color:sel === c.id ? regionColor(c.id) : INK, data:{region:c.id}});
    };
    if(k < LOD_SUB){
      for(const c of regions) regionPill(c, small ? 11 : 12.5);
      return;
    }
    // level 2: sub-regions, biggest first, inside the selected region first
    const subs = M.subs.map((s, i) => ({...s, i})).sort((a, b) => ((b.k === sel) - (a.k === sel)) || b.n - a.n);
    if(sel != null) regionPill(M.regions[sel], small ? 11 : 12);
    for(const s of subs){
      if(!s.label.length) continue;
      const dim = sel != null && sel !== s.k;
      pill(cut(s.label.join(', '), 40), sxq(s.cx), syq(s.cy), {size:small ? 10.5 : 11.5, padX:7, padY:3, weight:500,
        alpha:dim ? .4 : .93, stroke:regionColor(s.k), color:INK, data:{sub:s.i, region:s.k}});
    }
    for(const c of regions) if(c.id !== sel) regionPill(c, small ? 10.5 : 11.5);
    // level 3: a few single papers, most cited in view first; the hovered paper always gets its title
    if(!S.papers) return;
    const T2 = S.papers, size = small ? 10 : 11, maxLen = k > 10 ? 60 : 44, gap = small ? 14 : 18;
    ctx.font = `400 ${size}px ${font}`; ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    const label = (j, force) => {
      const txt = cut(T2.title[j] || T2.cite[j], maxLen), w = ctx.measureText(txt).width;
      let x = SX(j) + r + 4; const y = SY(j);
      if(force && x + w > W - 4) x = Math.max(4, SX(j) - r - 4 - w);
      const bx0 = x - gap / 2, bx1 = x + w + gap / 2, by0 = y - size - gap / 2, by1 = y + size + gap / 2;
      if(!force && !place(bx0, by0, bx1, by1)) return false;
      if(force && (x < 0 || x + w > W)) return false;
      ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(255,253,249,.94)'; ctx.lineJoin = 'round';
      ctx.strokeText(txt, x, y); ctx.fillStyle = INK; ctx.fillText(txt, x, y);
      boxes.push({x0:bx0, y0:by0, x1:bx1, y1:by1, paper:j}); return true;
    };
    if(hover != null) label(hover, true);
    if(k < LOD_PAPER) return;
    const cand = [];
    for(let j = 0; j < N; j++){ if(!on(j) || j === hover) continue; const x = SX(j), y = SY(j); if(x > 0 && x < W && y > 0 && y < H) cand.push(j); }
    cand.sort((a, b) => T2.rank[a] - T2.rank[b]);
    const limit = small ? 6 : 12;
    let n = 0;
    for(const j of cand){ if(n >= limit) break; if(label(j, false)) n++; }
    ctx.fillStyle = MUTED;
  }

  /* ---------- view transform ---------- */
  function stopAnim(){ if(anim){ cancelAnimationFrame(anim); anim = null; goal = null; } }
  function setT(t){ T = {k:Math.max(K_MIN, Math.min(K_MAX, t.k)), x:t.x, y:t.y}; cv.dataset.zoom = T.k.toFixed(2); draw(); }
  let goal = null;   // where a running animation is heading, so quick repeated zooms add up
  function animateTo(t, ms = 450){
    if(anim) cancelAnimationFrame(anim);
    goal = t;
    if(reducedMotion()){ setT(t); goal = null; return; }
    const a = {...T}, t0 = performance.now();
    const step = now => {
      const u = Math.min(1, (now - t0) / ms), e = u < .5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
      // interpolate the scale geometrically so zooming feels even
      const k = a.k * Math.pow(t.k / a.k, e);
      setT({k, x:a.x + (t.x - a.x) * e, y:a.y + (t.y - a.y) * e});
      if(u < 1) anim = requestAnimationFrame(step); else { anim = null; goal = null; }
    };
    anim = requestAnimationFrame(step);
  }
  function zoomAt(f, mx = W / 2, my = H / 2, animate = false){
    const from = animate && anim && goal ? goal : T;
    const k = Math.max(K_MIN, Math.min(K_MAX, from.k * f)), g = k / from.k;
    const t = {k, x:mx - (mx - from.x) * g, y:my - (my - from.y) * g};
    animate ? animateTo(t, 280) : setT(t);
  }
  const fit = () => animateTo({k:1, x:0, y:0});
  function zoomToBox(idx, fill = .8, kMax = 6){
    if(!idx.length) return;
    const xs = idx.map(j => bx[j]).sort((a, b) => a - b), ys = idx.map(j => by[j]).sort((a, b) => a - b);
    const qn = (a, f) => a[Math.floor(f * (a.length - 1))];
    const x0 = qn(xs, .03), x1 = qn(xs, .97), y0 = qn(ys, .03), y1 = qn(ys, .97);
    const k = Math.max(1, Math.min(kMax, fill / Math.max((x1 - x0) / W, (y1 - y0) / H, 1e-3)));
    animateTo({k, x:W / 2 - k * (x0 + x1) / 2, y:H / 2 - k * (y0 + y1) / 2}, 600);
  }

  /* ---------- picking ---------- */
  function nearest(mx, my, radPx, filter){
    const dx = ((mx - T.x) / T.k - base.ox) / base.s, dy = ((my - T.y) / T.k - base.oy) / base.s;
    const rad = radPx / (base.s * T.k), c0 = Math.floor((dx - rad) / cell), c1 = Math.floor((dx + rad) / cell);
    const r0 = Math.floor((dy - rad) / cell), r1 = Math.floor((dy + rad) / cell);
    let best = null, bd = rad * rad;
    for(let cx = c0; cx <= c1; cx++) for(let cy = r0; cy <= r1; cy++){
      const L = grid.get(cx * G + cy); if(!L) continue;
      for(const j of L){ if(!filter(j)) continue; const d = (P.x[j] - dx) ** 2 + (P.y[j] - dy) ** 2; if(d <= bd){ bd = d; best = j; } }
    }
    return best;
  }
  const dotOn = j => passesAll(j) && (sel == null || P.k[j] === sel);
  function pick(mx, my){
    for(let i = boxes.length - 1; i >= 0; i--){ const b = boxes[i]; if(b.region == null && b.paper == null) continue; if(mx >= b.x0 && mx <= b.x1 && my >= b.y0 && my <= b.y1) return b; }
    const j = nearest(mx, my, 7, dotOn);
    if(j != null) return {paper:j};
    return null;
  }

  /* ---------- tooltip ---------- */
  function showTip(h, mx, my){
    const tip = el.tip;
    if(!h){ tip.style.display = 'none'; return; }
    let html;
    if(h.paper != null){
      const j = h.paper, T2 = S.papers;
      html = `<b>${esc(T2 ? T2.title[j] : 'PMID ' + P.pmid[j])}</b><span class="cx-sub">${esc(T2 ? T2.cite[j] : '')}</span><span class="cx-sub">${esc(regionName(P.k[j]))}. Click to open the paper.</span>`;
    } else if(h.sub != null){
      const s = M.subs[h.sub];
      html = `<b>${esc(s.label.join(', '))}</b><span class="cx-sub">${fmt(s.n)} papers, part of ${esc(regionName(s.k))}. Click to zoom in.</span>`;
    } else {
      const c = M.regions[h.region];
      html = `<b>${esc(regionName(c.id, 3))}</b><span class="cx-sub">${fmt(c.n)} papers. Click to explore this region.</span>`;
    }
    tip.innerHTML = html; tip.style.display = 'block';
    const tw = tip.offsetWidth, th = tip.offsetHeight;
    tip.style.left = Math.max(6, Math.min(mx + 14, W - tw - 6)) + 'px';
    tip.style.top = (my + 16 + th > H ? Math.max(6, my - th - 12) : my + 16) + 'px';
  }

  function activate(h){
    if(!h){ return; }
    if(h.paper != null){ location.href = paperHref(P.pmid[h.paper]); return; }
    if(h.sub != null){ selectRegion(M.subs[h.sub].k, false); const idx = []; for(let j = 0; j < N; j++) if(P.s[j] === h.sub) idx.push(j); zoomToBox(idx, .7, 14); return; }
    selectRegion(h.region, true);
  }

  /* ---------- pointer, wheel, keys ---------- */
  const pts = new Map(); let drag = null, pinch = null, moved = 0;
  const local = e => { const r = cv.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
  cv.addEventListener('pointerdown', e => {
    stopAnim(); cv.setPointerCapture(e.pointerId); pts.set(e.pointerId, local(e)); moved = 0;
    if(pts.size === 1){ const [x, y] = local(e); drag = {x, y, t:{...T}}; }
    if(pts.size === 2){ const [a, b] = [...pts.values()]; pinch = {d:Math.hypot(a[0] - b[0], a[1] - b[1]), t:{...T}, m:[(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]}; drag = null; }
    cv.classList.add('dragging');
  });
  cv.addEventListener('pointermove', e => {
    const [mx, my] = local(e);
    if(pts.has(e.pointerId)) pts.set(e.pointerId, [mx, my]);
    if(pinch && pts.size === 2){
      const [a, b] = [...pts.values()], d = Math.hypot(a[0] - b[0], a[1] - b[1]);
      const k = Math.max(K_MIN, Math.min(K_MAX, pinch.t.k * d / pinch.d)), g = k / pinch.t.k, m = pinch.m;
      const c = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
      setT({k, x:c[0] - (m[0] - pinch.t.x) * g, y:c[1] - (m[1] - pinch.t.y) * g}); moved += 10; return;
    }
    if(drag){
      moved = Math.max(moved, Math.hypot(mx - drag.x, my - drag.y));
      if(moved > 3){ setT({k:T.k, x:drag.t.x + mx - drag.x, y:drag.t.y + my - drag.y}); el.tip.style.display = 'none'; return; }
    }
    if(e.pointerType === 'mouse'){
      const h = pick(mx, my), hv = h && h.paper != null ? h.paper : null;
      cv.style.cursor = h ? 'pointer' : '';
      if(hv !== hover){ hover = hv; draw(); }
      showTip(h, mx, my);
    }
  });
  const end = e => {
    const [mx, my] = local(e), wasClick = drag && moved <= 3 && pts.size === 1;
    pts.delete(e.pointerId); if(pts.size < 2) pinch = null;
    if(!pts.size){ drag = null; cv.classList.remove('dragging'); }
    if(wasClick && e.type === 'pointerup'){
      const h = pick(mx, my);
      if(h) activate(h);
      else { const j = nearest(mx, my, 26, passesAll); if(j != null) selectRegion(P.k[j], false); }
    }
  };
  cv.addEventListener('pointerup', end); cv.addEventListener('pointercancel', end);
  cv.addEventListener('pointerleave', () => { if(hover != null){ hover = null; draw(); } el.tip.style.display = 'none'; });
  cv.addEventListener('wheel', e => {
    e.preventDefault(); stopAnim();
    const [mx, my] = local(e), dy = e.deltaMode === 1 ? e.deltaY * 16 : e.deltaY;
    zoomAt(Math.exp(-dy * (e.ctrlKey ? .01 : .0018)), mx, my);
  }, {passive:false});
  cv.addEventListener('dblclick', e => { const [mx, my] = local(e); zoomAt(2, mx, my, true); });
  cv.addEventListener('keydown', e => {
    const step = 60, map = {ArrowLeft:[step, 0], ArrowRight:[-step, 0], ArrowUp:[0, step], ArrowDown:[0, -step]};
    if(map[e.key]){ e.preventDefault(); setT({k:T.k, x:T.x + map[e.key][0], y:T.y + map[e.key][1]}); }
    else if(e.key === '+' || e.key === '='){ e.preventDefault(); zoomAt(1.6, W / 2, H / 2, true); }
    else if(e.key === '-' || e.key === '_'){ e.preventDefault(); zoomAt(1 / 1.6, W / 2, H / 2, true); }
    else if(e.key === '0'){ e.preventDefault(); fit(); }
    else if(e.key === 'Escape' && sel != null){ e.preventDefault(); clearRegion(); }
  });
  el.zin.onclick = () => zoomAt(1.6, W / 2, H / 2, true);
  el.zout.onclick = () => zoomAt(1 / 1.6, W / 2, H / 2, true);
  el.fit.onclick = fit;
  new ResizeObserver(() => { if(visible) resize(); }).observe(cv);

  /* ---------- panel ---------- */
  function shownIn(k){ let n = 0; for(const j of byK[k]) if(passesAll(j)) n++; return n; }
  function searchByRegion(){
    if(!S.qMatch) return null;
    const c = new Map(); for(let j = 0; j < N; j++) if(S.qMatch[j] && passes(j)) c.set(P.k[j], (c.get(P.k[j]) || 0) + 1);
    return [...c].sort((a, b) => b[1] - a[1]);
  }
  function overviewHTML(){
    const act = filtersActive();
    return `<p class="cx-kicker">Overview</p>
      <h2>${fmt(M.regions.length)} regions of research</h2>
      <p class="cx-sub">Grouped from ${fmt(M.n_findings)} findings in ${fmt(M.n_papers)} papers. Pick a region on the map or in this list.</p>
      <ul class="cx-rlist">${M.regions.map(c => `<li><span class="cx-sw" style="background:${regionColor(c.id)}"></span><button type="button" class="cx-linkbtn" data-k="${c.id}">${esc(regionName(c.id))}</button><span class="cx-num">${act ? `${fmt(shownIn(c.id))} of ` : ''}${fmt(c.n)}</span></li>`).join('')}</ul>
      <h3>Biggest possible splits on the map</h3>
      <p class="cx-sub">${SPLIT_RULE} ${flipTotalText(M.n_splits)}</p>
      ${M.top_splits.slice(0, 5).map(splitHTML).join('')}`;
  }
  function regionHTML(){
    const c = M.regions[sel], act = filtersActive();
    const named = c.conds.filter(([k]) => k !== 'general' && k !== 'multiple');
    const condTxt = named.length ? `Most papers here study ${esc(condLabel(named[0][0]))} (${pct(named[0][1], c.n)}%)` + (named[1] ? ` and ${esc(condLabel(named[1][0]))} (${pct(named[1][1], c.n)}%)` : '') + '.' : 'Papers here are not tied to one condition.';
    const ftTxt = c.fts.length ? ` Their findings are mostly about ${esc(FT[c.fts[0][0]] || c.fts[0][0])} (${Math.round(c.fts[0][1] * 100)}%)` + (c.fts[1] ? `, then ${esc(FT[c.fts[1][0]] || c.fts[1][0])} (${Math.round(c.fts[1][1] * 100)}%)` : '') + '.' : '';
    const anTxt = c.an.length ? ` Body systems named most: ${c.an.slice(0, 3).map(a => esc(AN[a[0]] || a[0])).join(', ')}.` : '';
    const subs = M.subs.map((s, i) => ({...s, i})).filter(s => s.k === sel && s.label.length).sort((a, b) => b.n - a.n);
    return `<p class="cx-kicker"><span class="cx-sw" style="background:${regionColor(c.id)}"></span> Region ${c.id + 1} of ${M.regions.length} · <button type="button" class="cx-linkbtn" id="cxBack">All regions</button></p>
      <h2>${esc(regionName(c.id, 3))}</h2>
      <p class="cx-sub"><span class="cx-num">${fmt(c.n)}</span> papers, <span class="cx-num">${fmt(c.nf)}</span> findings${act ? `. <span class="cx-num">${fmt(shownIn(c.id))}</span> match your filters` : ''}</p>
      <h3>What this region is about</h3>
      <p>${condTxt}${ftTxt}${anTxt}</p>
      <p class="cx-sub">What sets it apart from the rest of the map:</p>
      <p>${c.dist.map(([e, n]) => `<a class="cx-chip" href="${entityHref(e)}">${esc(display(e))} <span class="cx-num">${fmt(n)}</span></a>`).join(' ')}</p>
      ${subs.length ? `<p class="cx-sub">Smaller groups inside it (zoom in to see them):</p><p>${subs.map(s => `<button type="button" class="cx-chip" data-sub="${s.i}">${esc(s.label.join(', '))} <span class="cx-num">${fmt(s.n)}</span></button>`).join(' ')}</p>` : ''}
      <h3>Most studied here</h3>${barsHTML(c.top)}
      <p class="cx-sub">Counts are papers in this region.</p>
      <h3>How it connects to other regions</h3>
      ${c.rel.map(r => `<div class="cx-rel"><span class="cx-sw" style="background:${regionColor(r.j)}"></span><button type="button" class="cx-linkbtn" data-k="${r.j}">${esc(regionName(r.j))}</button><div class="cx-sub">Both study ${r.shared.map(([e, a, b]) => `${esc(display(e))} <span class="cx-num">(${fmt(a)} here, ${fmt(b)} there)</span>`).join(', ')}</div></div>`).join('')}
      <h3>Possible splits</h3>
      <p class="cx-sub">${c.ns ? `${fmt(c.ns)} direction flips among this region's papers. The counts below cover only this region's papers, so they can be smaller than on the whole map. The biggest:` : 'No direction flips among this region\'s papers.'}</p>
      ${c.splits.slice(0, 5).map(splitHTML).join('')}
      <h3>No-effect results</h3>
      <p><span class="cx-num">${fmt(c.nullf)}</span> findings in <span class="cx-num">${fmt(c.nullp)}</span> papers report no effect or a failed replication.${named[0] ? ` <a href="search?null=1&c=${encodeURIComponent(named[0][0])}">See no-effect results for ${esc(condLabel(named[0][0]))}</a>` : ''}</p>
      ${act ? `<p class="cx-sub">Lists in this panel use all papers in the region, not your filters.</p>` : ''}`;
  }
  function renderPanel(){
    const pn = el.panel;
    pn.innerHTML = topicHTML(searchByRegion()) + (sel == null ? overviewHTML() : regionHTML());
    pn.querySelectorAll('[data-k]').forEach(b => b.onclick = () => selectRegion(+b.dataset.k, true));
    pn.querySelectorAll('[data-sub]').forEach(b => b.onclick = () => activate({sub:+b.dataset.sub}));
    const back = pn.querySelector('#cxBack'); if(back) back.onclick = clearRegion;
  }
  function selectRegion(k, zoom){
    sel = k; renderPanel(); draw();
    if(zoom) zoomToBox(byK[k]);
    if(window.matchMedia('(max-width: 900px)').matches && zoom) el.panel.scrollIntoView({behavior:reducedMotion() ? 'auto' : 'smooth', block:'start'});
  }
  function clearRegion(){ sel = null; renderPanel(); fit(); }

  return {
    show(){ visible = true; resize(); renderPanel(); },
    hide(){ visible = false; el.tip.style.display = 'none'; },
    refresh(){ renderPanel(); draw(); },
    reset(){ sel = null; renderPanel(); fit(); },
    redraw: draw,
    searchByRegion, selectRegion,
    get zoom(){ return T.k; }
  };
}
