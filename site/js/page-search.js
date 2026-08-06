import { loadMeta, loadFacets, loadPapers, loadEntities, state, applyFilters, ensureRows,
         paperCount, paper, fmt, esc, FILTER_FIELDS } from './data.js';
import { mount, findingCard, selectOpts, autocomplete, qs, entityCoverageNote } from './ui.js';
import { initModel, modelStatus, onModelStatus, embedQuery, loadEmbeddings, embeddingsReady,
         rankByVector, prepareKeyword, keywordReady, keywordSearch } from './search.js';

const PAGE=25;
let mode='keyword', view='papers', rows=[], scored=null, page=0;

const FLABEL = {c:'Condition', d:'Direction', tr:'Evidence tier', ce:'Certainty', ft:'Finding type',
  ek:'Entity kind', mc:'Map confidence', e:'Canonical entity', st:'Study type',
  ca:'Causal/correlational', ps:'POTS subtype', ag:'Age group', cv:'COVID-associated', th:'Theme',
  ti:'Extraction tier', sl:'Source literature'};

await loadMeta(); await loadFacets(); await loadPapers(); await loadEntities();
mount('search.html');

/* ---- filters ---- */
const fEl = document.getElementById('filters');
fEl.innerHTML = FILTER_FIELDS.map(k=>{
  const vals = [...state.facets.dicts[k]].sort((a,b)=>String(a).localeCompare(String(b)));
  if(k==='e'){
    return `<div><label>${FLABEL[k]}</label><div class="autoc"><input type="text" id="fe"
      placeholder="any entity" autocomplete="off"></div></div>`;
  }
  return `<div><label>${FLABEL[k]}</label><select data-f="${k}">${selectOpts(vals,'')}</select></div>`;
}).join('');
autocomplete(document.getElementById('fe'), state.entities.map(e=>e.name), ()=>run());
const cov=document.createElement('div'); cov.innerHTML=entityCoverageNote('the canonical-entity filter');
document.getElementById('filters').after(cov);

function opts(){
  const o={};
  fEl.querySelectorAll('select[data-f]').forEach(s=>{ if(s.value) o[s.dataset.f]=s.value; });
  const fe=document.getElementById('fe').value.trim(); if(fe) o.e=fe;
  o.hasQuant=document.getElementById('fQuant').checked;
  o.nullOnly=document.getElementById('fNull').checked;
  o.excludeSplit=document.getElementById('fSplit').checked;
  o.y0=document.getElementById('y0').value; o.y1=document.getElementById('y1').value;
  return o;
}

/* ---- mode + model status ---- */
const msEl=document.getElementById('modeState');
function renderStatus(){
  const st=modelStatus();
  let s='';
  if(mode==='keyword'){
    s=`<span class="pill">Keyword mode</span> exact substring / token match over finding text, entity and
       condition. No model needed.`;
    if(st==='ready') s+=` Semantic search is ready: switch any time.`;
  } else {
    if(st==='ready') s=`<span class="pill">Semantic mode</span> real query embedding
        (all-MiniLM-L6-v2, the same model used for the findings): cosine ranking, not an approximation.`;
    else if(st==='loading') s=`<span class="spinner"></span> loading search model (~23&nbsp;MB, cached after
        first use)… <span class="pill grey">keyword search still works</span>`;
    else if(st==='unavailable') s=`<span class="pill err">Semantic search unavailable</span>
        the model could not be loaded (offline, blocked CDN, or unsupported browser).
        <b>Keyword search still works</b>: switch back to Keyword mode.`;
    else s=`<span class="pill grey">Semantic mode</span> starting model…`;
  }
  msEl.innerHTML = s;
}
onModelStatus((s,extra)=>{
  renderStatus();
  if(s==='unavailable' && mode==='semantic'){ /* keep keyword usable, do not throw */ }
  if(s==='loading' && extra && extra.pct) {
    msEl.innerHTML = `<span class="spinner"></span> loading search model: ${Math.round(extra.pct)}%
      <span class="pill grey">keyword search still works</span>`;
  }
});
function setMode(m){
  mode=m;
  document.getElementById('mKeyword').classList.toggle('on', m==='keyword');
  document.getElementById('mSemantic').classList.toggle('on', m==='semantic');
  renderStatus();
  if(m==='semantic'){ initModel(); loadEmbeddings().catch(e=>{
      msEl.innerHTML=`<span class="pill err">Embeddings failed to load</span> ${esc(e.message)}: keyword search still works.`; }); }
  run();
}
document.getElementById('mKeyword').onclick=()=>setMode('keyword');
document.getElementById('mSemantic').onclick=()=>setMode('semantic');

/* ---- run ---- */
async function run(){
  const q=document.getElementById('q').value.trim();
  const allowed=applyFilters(state.facets, opts());
  page=0; scored=null;
  if(!q){ rows=allowed; return render(`${fmt(allowed.length)} findings match the filters`); }

  if(mode==='keyword'){
    document.getElementById('count').textContent='Loading finding text…';
    if(!keywordReady()) await prepareKeyword();
    scored=keywordSearch(q, allowed, 400);
    rows=scored.map(s=>s[0]);
    return render(`${fmt(rows.length)} keyword matches (of ${fmt(allowed.length)} filtered)`, true);
  }
  // semantic
  try{
    document.getElementById('count').innerHTML='<span class="spinner"></span> embedding query…';
    if(!embeddingsReady()) await loadEmbeddings((d,n)=>{
      document.getElementById('count').innerHTML=`<span class="spinner"></span> loading vectors ${d}/${n}…`; });
    const v=await embedQuery(q);
    scored=rankByVector(v, allowed, 300);
    rows=scored.map(s=>s[0]);
    render(`top ${fmt(rows.length)} semantic matches (of ${fmt(allowed.length)} filtered)`, true);
  }catch(e){
    document.getElementById('count').innerHTML =
      `<span class="pill err">Semantic search failed</span> ${esc(e.message)}: falling back to keyword.`;
    setMode('keyword');
  }
}

async function render(label, withScores=false){
  const c=document.getElementById('count');
  const paperRows=[...new Set(rows.map(row=>state.facets.cols.p[row]))];
  const displayRows=view==='papers' ? paperRows : rows;
  const np=paperCount(rows);
  c.innerHTML=view==='papers' ? `${label} · <b>${fmt(displayRows.length)}</b> papers` : `${label} · <b>${fmt(np)}</b> distinct papers`;
  const slice=displayRows.slice(page*PAGE,(page+1)*PAGE);
  if(view==='papers'){
    document.getElementById('results').innerHTML = slice.length
      ? slice.map(index=>paperCard(paper(index))).join('')
      : `<div class="panel">No papers match. Try fewer filters, or switch search mode.</div>`;
  } else {
    await ensureRows(slice);
    document.getElementById('results').innerHTML = slice.length
      ? slice.map((r,i)=>findingCard(r, withScores&&scored?{score:scored[page*PAGE+i][1]}:{})).join('')
      : `<div class="panel">No findings match. Try fewer filters, or switch search mode.</div>`;
  }
  const pages=Math.ceil(displayRows.length/PAGE);
  const pg=`<button ${page===0?'disabled':''} id="prev">‹ prev</button>
    <span>page ${page+1} / ${Math.max(pages,1)}</span>
    <button ${page>=pages-1?'disabled':''} id="next">next ›</button>`;
  document.getElementById('pager').innerHTML=pg; document.getElementById('pager2').innerHTML=pg;
  document.querySelectorAll('#prev').forEach(b=>b.onclick=()=>{page--;render(label,withScores);});
  document.querySelectorAll('#next').forEach(b=>b.onclick=()=>{page++;render(label,withScores);});
}

function paperCard(p){
  if(!p) return '';
  const source=p.doi_url||p.pubmed_url||p.pmc_url;
  const sourceLink=source?`<a href="${esc(source)}" target="_blank" rel="noopener">Read source</a>`:'';
  return `<div class="card paper-card"><p class="paper-title"><a href="paper.html?pmid=${esc(p.pmid)}">${esc(p.title||p.citation_short||'Untitled paper')}</a></p>
    <div class="paper-meta">${esc(p.first_author||'Unknown')}${p.author_count>1?' et al.':''} · ${esc(p.journal||'Unknown journal')} · ${esc(p.year||'Year unavailable')}</div>
    <div class="paper-actions"><span>${fmt(p.n_findings)} extracted findings</span>${sourceLink?` · ${sourceLink}`:''} · <a href="paper.html?pmid=${esc(p.pmid)}">View findings</a></div></div>`;
}

function setView(next){
  view=next;
  ['papers','findings'].forEach(name=>{
    const button=document.getElementById(`view${name[0].toUpperCase()+name.slice(1)}`);
    const active=name===view;
    button.classList.toggle('on',active); button.setAttribute('aria-selected',String(active));
  });
  page=0; run();
}

document.getElementById('go').onclick=run;
document.getElementById('viewPapers').onclick=()=>setView('papers');
document.getElementById('viewFindings').onclick=()=>setView('findings');
document.getElementById('q').addEventListener('keydown',e=>{ if(e.key==='Enter') run(); });
document.getElementById('clear').onclick=()=>{
  document.getElementById('q').value=''; document.getElementById('fe').value='';
  fEl.querySelectorAll('select').forEach(s=>s.value='');
  ['fQuant','fNull','fSplit'].forEach(i=>document.getElementById(i).checked=false);
  document.getElementById('y0').value=''; document.getElementById('y1').value=''; run();
};
fEl.addEventListener('change',run);
document.querySelectorAll('#fQuant,#fNull,#fSplit,#y0,#y1').forEach(e=>e.addEventListener('change',run));

/* deep links: ?q=, ?e=, ?c=, ?null=1 */
const pe=qs('e'), pc=qs('c'), pq=qs('q');
if(pe) document.getElementById('fe').value=pe;
if(pc){ const s=fEl.querySelector('select[data-f="c"]'); if(s) s.value=pc; }
if(qs('null')==='1') document.getElementById('fNull').checked=true;
if(pq) document.getElementById('q').value=pq;
renderStatus();
run();
