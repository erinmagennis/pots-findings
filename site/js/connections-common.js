/* connections-common.js: shared state, filters and panel pieces for the Connections page (Map and Flow). */
import { esc, fmt } from './data.js';
import { condLabel } from './labels.js';

export { esc, fmt };
export const PAL = ['#a7593e','#4d7b82','#8a6d2a','#6b7f4e','#7a5c8e','#b07a5a','#3f6f5f','#9b4a5c',
  '#5f7fa6','#a38b3c','#6f6a9a','#c0794a','#4e8a7a','#8c5a3c','#7d8f99','#a05f7f'];
export const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;
export const pct = (a, b) => b ? Math.round(100 * a / b) : 0;
/* visible entity name: same rule as signals_rules.display and displayName() in home-v2.js. Links keep the raw name. */
export const display = name => {
  const s = String(name ?? ''), first = s.split(' ')[0];
  if(!s || !/^[a-z]/.test(s) || /[A-Z0-9]/.test(first.slice(1))) return s;
  return s[0].toUpperCase() + s.slice(1);
};

/* shared page state: data plus the filters both views read */
export const S = {
  map: null, papers: null, ents: null, splits: null, flow: null,
  q: '', cond: '', y0: 0, y1: 9999, years: [],
  qMatch: null,          // Uint8Array per paper (1 = matches the search), null when no search
  qEnts: [],             // entity ids whose names match the search
  listeners: new Set()
};
export const onFilter = fn => S.listeners.add(fn);
export const emitFilter = () => S.listeners.forEach(fn => fn());
export const filtersActive = () => !!(S.q || S.cond || S.y0 > S.years[0] || S.y1 < S.years[S.years.length - 1]);

/** paper j passes the condition and year filters */
export function passes(j){
  const P = S.map.papers;
  if(S.cond){ const b = S.map.conds.indexOf(S.cond); if(b < 0 || !(P.cm[j] & (1 << b))) return false; }
  const y = P.year[j];
  if(y && (y < S.y0 || y > S.y1)) return false;
  return true;
}
/** paper j passes every filter, the search included */
export const passesAll = j => passes(j) && (!S.qMatch || S.qMatch[j] === 1);

/** recompute the search match set from titles and entity names (both lazily loaded) */
export function computeSearch(){
  const q = S.q.toLowerCase();
  if(!q){ S.qMatch = null; S.qEnts = []; return; }
  const n = S.map.n_papers, m = new Uint8Array(n);
  const E = S.ents, T = S.papers;
  S.qEnts = [];
  if(E){
    const hit = new Uint8Array(E.names.length);
    E.names.forEach((nm, i) => { if(nm.toLowerCase().includes(q)){ hit[i] = 1; S.qEnts.push(i); } });
    for(let j = 0; j < n; j++){ const ids = E.paper[j]; for(let t = 0; t < ids.length; t++) if(hit[ids[t]]){ m[j] = 1; break; } }
  }
  if(T) for(let j = 0; j < n; j++) if(!m[j] && T.title[j].toLowerCase().includes(q)) m[j] = 1;
  if(!T){ const pm = S.map.papers.pmid; for(let j = 0; j < n; j++) if(pm[j] === S.q) m[j] = 1; }
  S.qMatch = m;
}

export const regionName = (k, n = 2) => S.map.regions[k].label.slice(0, n).join(', ');
export const regionColor = k => PAL[k % PAL.length];

/* ---------- links ---------- */
const pmidIndex = new Map();
export function indexPmids(){ S.map.papers.pmid.forEach((p, j) => pmidIndex.set(p, j)); }
export const paperIdx = pm => pmidIndex.get(String(pm));
export function citeOf(pm){
  const j = paperIdx(pm);
  return (j != null && S.papers && S.papers.cite[j]) || `PMID ${pm}`;
}
export const paperHref = pm => `paper?pmid=${encodeURIComponent(pm)}`;
export const paperLink = (pm, label) => `<a href="${paperHref(pm)}">${esc(label || citeOf(pm))}</a>`;
export const entityHref = e => `entity?e=${encodeURIComponent(e)}`;
export const searchHref = (e, c) => `search?e=${encodeURIComponent(e)}${c ? `&c=${encodeURIComponent(c)}` : ''}`;

/* "Mast cells in MCAS"; general and multiple read as plain words */
export function inCond(c){
  if(c === 'general') return 'not tied to one condition';
  if(c === 'multiple') return 'across several conditions';
  return `in ${condLabel(c)}`;
}

/** one disagreement: entity in condition, higher / lower / no difference paper counts, example papers */
export function splitHTML(s){
  const ex = [];
  if(s.pu && s.pu[0]) ex.push(`<span class="up">Higher:</span> ${paperLink(s.pu[0])}`);
  if(s.pd && s.pd[0]) ex.push(`<span class="dn">Lower:</span> ${paperLink(s.pd[0])}`);
  if(s.pn && s.pn[0] && s.nu) ex.push(`<span class="nu">No difference:</span> ${paperLink(s.pn[0])}`);
  return `<div class="cx-split">
    <div class="cx-split-head"><a class="cx-ent" href="${searchHref(s.e, s.c)}" title="See every finding on ${esc(display(s.e))} ${esc(inCond(s.c))}">${esc(display(s.e))}</a> <span class="cx-sub">${esc(inCond(s.c))}</span></div>
    <div class="cx-dirs"><span class="up"><span aria-hidden="true">&#9650;</span> ${fmt(s.up)} higher</span><span class="dn"><span aria-hidden="true">&#9660;</span> ${fmt(s.dn)} lower</span><span class="nu">${fmt(s.nu)} no difference</span></div>
    <div class="cx-ex">${ex.join('<br>')}</div></div>`;
}
export const SPLIT_RULE = 'Papers that compared people with the condition to people without it found the same thing higher in some and lower in others. Changes after a treatment are not counted. Counts are papers, with the same rule as Signals and the home page.';

/** "most studied" bar list: [[entity, papers], ...] */
export function barsHTML(top){
  const max = top[0] ? top[0][1] : 1;
  return `<ul class="cx-bars">${top.map(([e, n]) => `<li><a href="${entityHref(e)}">${esc(display(e))}</a><span class="cx-num">${fmt(n)}</span><span class="cx-bar" aria-hidden="true"><i style="width:${(100 * n / max).toFixed(1)}%"></i></span></li>`).join('')}</ul>`;
}

/** topic block for a search that matches entity names: where it sits and where papers disagree about it */
export function topicHTML(byRegion, onRegionAttr = true){
  if(!S.q) return '';
  const E = S.ents;
  const names = E ? S.qEnts.slice().sort((a, b) => E.np[b] - E.np[a]).slice(0, 6) : [];
  const nMatch = S.qMatch ? countShown(j => S.qMatch[j] === 1) : 0;
  const qs = S.q.toLowerCase();
  const splits = S.splits ? S.splits.splits.filter(s => s.e.toLowerCase().includes(qs)).slice(0, 6) : [];
  const nSplits = S.splits ? S.splits.splits.filter(s => s.e.toLowerCase().includes(qs)).length : 0;
  let h = `<p class="cx-kicker">Your search</p><h2>&ldquo;${esc(S.q)}&rdquo;</h2>
    <p class="cx-sub"><span class="cx-num">${fmt(nMatch)}</span> papers shown have it in the title or in an extracted finding.</p>`;
  if(names.length) h += `<p class="cx-sub">Matching topics: ${names.map(i => `<a class="cx-chip" href="${entityHref(E.names[i])}">${esc(display(E.names[i]))} <span class="cx-num">${fmt(E.np[i])}</span></a>`).join(' ')}</p>`;
  if(byRegion && byRegion.length){
    h += `<h3>Where these papers sit</h3><ul class="cx-rlist">${byRegion.slice(0, 5).map(([k, n]) => `<li><span class="cx-sw" style="background:${regionColor(k)}"></span>${onRegionAttr ? `<button type="button" class="cx-linkbtn" data-k="${k}">${esc(regionName(k))}</button>` : esc(regionName(k))}<span class="cx-num">${fmt(n)}</span></li>`).join('')}</ul>`;
  }
  if(S.splits){
    h += `<h3>Where papers disagree about it</h3>`;
    h += nSplits ? `<p class="cx-sub">${fmt(nSplits)} disagreements name a matching topic. Biggest first. These counts use all papers, not your filters.</p>${splits.map(splitHTML).join('')}`
      : `<p class="cx-sub">No disagreements found for a matching topic.</p>`;
  }
  return `<div class="cx-topic">${h}</div>`;
}

/** label for the whole-map total of direction flips, so it is not read as the Signals total of every conflict */
export function flipTotalText(n){
  const c = S.meta && S.meta.counts, nvp = c && c.contra_null_vs_pos_total;
  return `${fmt(n)} direction flips across the whole map.` + (nvp != null ? ` Signals counts the same flips, plus ${fmt(nvp)} conflicts between an effect and no difference.` : '');
}

export function countShown(extra){
  let n = 0; const N = S.map.n_papers;
  for(let j = 0; j < N; j++) if(passes(j) && (!extra || extra(j))) n++;
  return n;
}
