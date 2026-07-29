import { loadMeta, loadFacets, loadPapers, state, applyFilters, ensureRows, paperCount, fmt, esc, val,
         TIER1_CONDITIONS as TIER1 } from './data.js';
import { mount, findingCard, qs } from './ui.js';

const PAGE=25; let page=0, rows=[];
await loadMeta(); await loadFacets(); await loadPapers();
mount('conditions.html');

const c=qs('c');
rows=applyFilters(state.facets,{c});
const incid = !TIER1.has(c);
const n = state.meta.incidental[c];

const tally=(f)=>{ const m={}; for(const r of rows){ const v=val(f,r); if(v&&v!=='—') m[v]=(m[v]||0)+1; } return m; };

document.getElementById('head').innerHTML=`<div class="panel">
  <h1>${esc(c)} ${incid?'<span class="pill grey">incidental mentions only</span>':'<span class="pill">within Tier-1 scope</span>'}</h1>
  ${incid? `<div class="note stop"><b>This is not the ${esc(c)} literature.</b> Tier 1 extracted only
      POTS/dysautonomia papers. These ${fmt(rows.length)} findings come from
      ${n!=null?`${n} POTS/dysautonomia papers that mention ${esc(c)}`:`POTS/dysautonomia papers that mention ${esc(c)}`} —
      a biased, incidental sample. The actual ${esc(c)} literature sits in Tiers 2–4 and has
      <b>not yet been extracted</b>. Do not read these counts as a survey of ${esc(c)} research.</div>`
    : `<div class="note plain">This label sits <b>inside</b> the Tier-1 extraction scope: it was applied to
      papers the POTS/dysautonomia search retrieved, so it reflects the extracted corpus rather than
      incidental mentions. Still limited to ${fmt(state.meta.counts.tier1_chunks)} of
      ${fmt(state.meta.counts.corpus_chunks)} corpus chunks
      (${fmt(state.meta.counts.papers)} of ~${fmt(state.meta.counts.corpus_papers_total)} papers), and
      <b>${esc(c)}</b> is a label applied within POTS/dysautonomia papers — not a separately searched
      literature. ${rows.length<50?'This label carries very few findings, so treat its counts as anecdotal.':''}</div>`}
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
