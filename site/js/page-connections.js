/* page-connections.js: the Connections page. Two views of the same papers: Map (paper landscape) and Flow
   (papers from topic region to body system to strength of claim or POTS subtype). The view lives in the URL hash
   (#map, #flow, #flow/subtype) so links can point straight at it. Data: site_tools/build_connections_data.py. */
import { loadMeta, getJSON, state } from './data.js';
import { mount as mountChrome } from './ui.js';
import { condLabel } from './labels.js';
import { S, esc, fmt, emitFilter, onFilter, computeSearch, indexPmids, regionName, countShown, filtersActive } from './connections-common.js';
import { createMap } from './connections-map.js';
import { createFlow } from './connections-flow.js';

const $ = id => document.getElementById(id);
const status = $('cxStatus');
await loadMeta();
mountChrome('connections');

const [map, flow] = await Promise.all([getJSON('conn_map.json'), getJSON('conn_flow.json')]);
S.map = map; S.flow = flow; S.meta = state.meta;
indexPmids();
S.years = [...new Set(map.papers.year.filter(Boolean))].sort((a, b) => a - b);
S.y0 = S.years[0]; S.y1 = S.years[S.years.length - 1];

/* ---------- copy that depends on the data ---------- */
const COPY = {
  map: {title:'A map of what the papers are about',
    lede:`Each dot is one of ${fmt(map.n_papers)} papers, placed by what its findings say. Papers close together report on similar things. Pick a region to see what it covers, how it links to other regions, and where its papers disagree.`},
  flow: {title:'Follow the papers from topic to finding',
    lede:`Start with all ${fmt(map.n_papers)} papers on the left. Follow them into topic regions, then the body systems their findings touch, then what kind of finding they report. Pick any bar to see what it holds and where its papers disagree.`}
};
$('cxCaveat').textContent = 'Findings were extracted by a language model and not checked by a person. Sitting close together means similar topics, not a proven link. Retracted papers and correction notices are left out.';
$('cxLegend').innerHTML = `<span><b>${fmt(map.regions.length)} regions</b>, found by grouping papers with similar findings.</span><span>Region names are the topics that set each region apart.</span><span>Zoom in for smaller groups, then single papers.</span>`;

/* ---------- filters ---------- */
const condSel = $('cxCond'), y0 = $('cxY0'), y1 = $('cxY1'), qIn = $('cxQ');
map.conds.forEach(c => condSel.insertAdjacentHTML('beforeend', `<option value="${esc(c)}">${esc(condLabel(c))}</option>`));
S.years.forEach(y => { y0.insertAdjacentHTML('beforeend', `<option>${y}</option>`); y1.insertAdjacentHTML('beforeend', `<option>${y}</option>`); });
y0.value = S.y0; y1.value = S.y1;
let qt;
qIn.addEventListener('input', () => { clearTimeout(qt); qt = setTimeout(() => { const v = qIn.value.trim(); S.q = v.length >= 2 ? v : ''; computeSearch(); emitFilter(); }, 200); });
condSel.onchange = () => { S.cond = condSel.value; emitFilter(); };
y0.onchange = () => { S.y0 = +y0.value; if(S.y0 > S.y1){ S.y1 = S.y0; y1.value = S.y1; } emitFilter(); };
y1.onchange = () => { S.y1 = +y1.value; if(S.y1 < S.y0){ S.y0 = S.y1; y0.value = S.y0; } emitFilter(); };
$('cxReset').onclick = () => {
  S.q = ''; S.cond = ''; S.y0 = S.years[0]; S.y1 = S.years[S.years.length - 1];
  qIn.value = ''; condSel.value = ''; y0.value = S.y0; y1.value = S.y1;
  computeSearch(); views[view].reset(); emitFilter();
};

/* ---------- views ---------- */
const mapView = createMap({canvas:$('cxMap'), panel:$('mapPanel'), tip:$('cxTip'), zin:$('cxZin'), zout:$('cxZout'), fit:$('cxFit'), reserve:[document.querySelector('.cx-mapbtns'), $('cxHint')]});
const flowView = createFlow({svg:$('cxFlow'), wrap:$('cxFlowWrap'), panel:$('flowPanel'), tip:$('cxFlowTip'), note:$('cxFlowNote'), legend:$('cxFlowLegend'),
  sink:$('cxSink'), sinkWrap:$('cxSinkWrap'), lastBtns:[...document.querySelectorAll('[data-last]')], onLast:() => writeHash()});
const views = {map:mapView, flow:flowView};
let view = 'map';

function writeHash(){
  const h = view === 'flow' ? ({ps:'#flow/subtype', ca:'#flow/claim'}[flowView.last] || '#flow') : '#map';
  if(location.hash !== h) history.replaceState(null, '', h);
}
function readHash(){
  const h = location.hash.replace('#', '');
  return {view:h.startsWith('flow') ? 'flow' : 'map', last:{'flow/subtype':'ps', 'flow/claim':'ca'}[h] || 'ft'};
}
function setView(v, fromHash){
  view = v;
  document.querySelectorAll('[data-view]').forEach(b => { const on = b.dataset.view === v; b.classList.toggle('on', on); b.setAttribute('aria-pressed', String(on)); });
  $('mapStage').hidden = v !== 'map'; $('flowStage').hidden = v !== 'flow';
  $('cxTitle').textContent = COPY[v].title; $('cxLede').textContent = COPY[v].lede;
  (v === 'map' ? flowView : mapView).hide();
  views[v].show();
  renderStatus();
  if(!fromHash) writeHash();
}
document.querySelectorAll('[data-view]').forEach(b => b.onclick = () => setView(b.dataset.view));
window.addEventListener('hashchange', () => { const h = readHash(); if(h.view === 'flow' && h.last !== flowView.last) flowView.setLast(h.last); if(h.view !== view) setView(h.view, true); });

function renderStatus(){
  const shown = countShown(), total = map.n_papers;
  let msg = filtersActive() ? `${fmt(shown)} of ${fmt(total)} papers match your filters.`
    : view === 'map' ? `${fmt(total)} papers on the map.` : `${fmt(total)} papers in the flow.`;
  if(S.q){
    if(!S.papers || !S.ents) msg = `Loading paper titles and topics to search…`;
    else {
      const by = mapView.searchByRegion() || [], n = by.reduce((a, r) => a + r[1], 0);
      msg = `${fmt(n)} papers mention &ldquo;${esc(S.q)}&rdquo;${S.cond || S.y0 > S.years[0] || S.y1 < S.years[S.years.length - 1] ? ' within your filters' : ''}. ` +
        (by.length ? 'Most sit in ' + by.slice(0, 3).map(([k, c]) => `<button type="button" class="cx-linkbtn" data-sk="${k}">${esc(regionName(k))}</button> (${fmt(c)})`).join(', ') + '.' : '');
      if(view === 'flow' && n) msg += ' The flow follows only these papers.';
    }
  }
  status.innerHTML = msg;
  status.querySelectorAll('[data-sk]').forEach(b => b.onclick = () => { if(view !== 'map') setView('map'); mapView.selectRegion(+b.dataset.sk, true); });
}
onFilter(() => { views[view].refresh(); renderStatus(); });

const h0 = readHash();
if(h0.last !== 'ft') flowView.setLast(h0.last);
setView(h0.view, true);

/* ---------- lazy data: titles and citations, topic names, every disagreement ---------- */
Promise.all([getJSON('conn_papers.json'), getJSON('conn_ents.json'), getJSON('conn_splits.json')]).then(([p, e, s]) => {
  S.papers = p; S.ents = e; S.splits = s;
  if(S.q) computeSearch();
  views[view].refresh(); renderStatus();
}).catch(err => { console.warn('Connections: optional data failed to load', err); });
