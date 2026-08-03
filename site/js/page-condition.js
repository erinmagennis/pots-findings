import { loadMeta, loadFacets, loadPapers, state, applyFilters, ensureRows, paperCount, fmt, esc, val,
         } from './data.js';
import { mount, findingCard, qs } from './ui.js';

const PAGE=25; let page=0, rows=[];
await loadMeta(); await loadFacets(); await loadPapers();
mount('conditions.html');

const c=qs('c');
rows=applyFilters(state.facets,{c});
const sourceLiteratures=[...new Set(rows.map(r=>val('sl',r)).filter(Boolean))].sort();
const extractionTiers=[...new Set(rows.map(r=>val('ti',r)).filter(Boolean))].sort();

const tally=(f)=>{ const m={}; for(const r of rows){ const v=val(f,r); if(v&&v!=='\u2014') m[v]=(m[v]||0)+1; } return m; };

document.getElementById('head').innerHTML=`<div class="panel">
  <h1>${esc(c)} <span class="pill">tiers ${extractionTiers.map(esc).join(', ')}</span></h1>
  <div class="note plain"><b>This is a condition-label view across the current checkpoint.</b>
    Its ${fmt(rows.length)} findings come from ${sourceLiteratures.length} source literature${sourceLiteratures.length===1?'':'s'}:
    ${sourceLiteratures.map(x=>`<code>${esc(x)}</code>`).join(', ')}. A condition label and a source literature
    are not interchangeable. Tier 2 covers ${state.meta.counts.tier2_chunks_extracted} of
    ${state.meta.counts.tier2_chunks_total} chunks, so these are subset counts and absence is not evidence of absence.
    ${rows.length<50?'This label carries very few findings, so treat its counts as exploratory.':''}</div>
  <div class="statgrid">
    <div class="stat"><div class="v">${fmt(rows.length)}</div><div class="k">findings</div></div>
    <div class="stat"><div class="v">${fmt(paperCount(rows))}</div><div class="k">papers</div></div>
    <div class="stat"><div class="v">${fmt(Object.keys(tally('e')).length)}</div><div class="k">named entities</div></div>
  </div>
  <p><a href="index.html?c=${encodeURIComponent(c)}">Open in search →</a></p></div>`;

const box=(t,id)=>`<div class="chartbox"><h3>${t}</h3><div class="canvasholder" style="height:260px"><canvas id="${id}"></canvas></div></div>`;
document.getElementById('charts').innerHTML=box('Direction','cD')+box('Evidence tier','cT');
const mk=(id,obj,col)=>{const k=Object.keys(obj),v=k.map(x=>obj[x]);
  new Chart(document.getElementById(id),{type:'bar',data:{labels:k,datasets:[{data:v,backgroundColor:col}]},
  options:{indexAxis:'y',plugins:{legend:{display:false}},scales:{x:{beginAtZero:true}},maintainAspectRatio:false}});};
mk('cD',tally('d'),'#8a4b2a'); mk('cT',tally('tr'),'#2f5f7a');

async function render(){
  document.getElementById('count').innerHTML=`${fmt(rows.length)} findings`;
  const slice=rows.slice(page*PAGE,(page+1)*PAGE);
  await ensureRows(slice);
  document.getElementById('results').innerHTML=slice.map(r=>findingCard(r)).join('');
  const pages=Math.ceil(rows.length/PAGE);
  const pg=`<button ${page===0?'disabled':''} id="prev">‹ prev</button>
    <span>page ${page+1} / ${Math.max(pages,1)}</span>
    <button ${page>=pages-1?'disabled':''} id="next">next ›</button>`;
  document.getElementById('pager').innerHTML=pg; document.getElementById('pager2').innerHTML=pg;
  document.querySelectorAll('#prev').forEach(b=>b.onclick=()=>{page--;render();});
  document.querySelectorAll('#next').forEach(b=>b.onclick=()=>{page++;render();});
}
render();
