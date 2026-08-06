import { loadMeta, loadFacets, loadPapers, loadEntities, state, applyFilters, ensureRows,
         paperCount, fmt, esc, val } from './data.js';
import { mount, findingCard, qs } from './ui.js';

const PAGE=25; let page=0, rows=[];
await loadMeta(); await loadFacets(); await loadPapers(); await loadEntities();
mount('entities.html');

const name=qs('e');
const e=state.entityByName.get(name);
if(!e){
  document.getElementById('head').innerHTML=`<div class="panel"><h1>Entity not found</h1>
    <p>No canonical entity named <code>${esc(name)}</code>. <a href="entities.html">Browse all entities →</a></p></div>`;
} else {
  rows=applyFilters(state.facets,{e:name});
  const ont = e.oid
    ? `<span class="mono">${esc(e.oid)}</span> <span class="pill grey">${esc(e.osrc||'')}</span>${e.olabel?`: ${esc(e.olabel)}`:''}`
    : `<span class="pill grey">no ontology ID</span>`;
  document.getElementById('head').innerHTML=`<div class="panel">
    <h1>${esc(e.name)} ${e.kind?`<span class="pill">${esc(e.kind)}</span>`:''}</h1>
    <p class="kv">Ontology: ${ont} · Entity-mapping confidence:
      <b>${esc(e.mapc||'N/A')}</b>${e.mapc&&e.mapc!=='high'?' <span class="tag lowconf">review this merge before relying on it</span>':''}</p>
    <div class="statgrid" style="margin-top:10px">
      <div class="stat"><div class="v">${fmt(e.np_)}</div><div class="k">papers</div></div>
      <div class="stat"><div class="v">${fmt(e.npd)}</div><div class="k">papers (direct)</div></div>
      <div class="stat"><div class="v">${fmt(e.nf)}</div><div class="k">findings</div></div>
      <div class="stat"><div class="v">${fmt((e.origs||[]).length)}</div><div class="k">merged strings</div></div>
      <div class="stat"><div class="v">${fmt(Object.keys(e.conds||{}).length)}</div><div class="k">conditions</div></div>
    </div>
    <p class="kv" style="margin-top:8px"><b>papers</b> counts distinct canonical papers including
      split-derived rows; <b>papers (direct)</b> excludes rows created by splitting a compound entity string.</p>
    <p><a href="search.html?e=${encodeURIComponent(e.name)}">Open in search with filters →</a></p>
  </div>`;

  const origs=(e.origs||[]);
  document.getElementById('audit').innerHTML=`<h3>Auditability: original strings folded into this canonical</h3>
    ${origs.length? `<p class="kv">These ${origs.length} raw extraction strings were merged into
      <code>${esc(e.name)}</code>. If any of them does not belong, this canonical is over-merged.</p>
      <div class="tags">${origs.map(o=>`<span class="tag">${esc(o)}</span>`).join('')}</div>`
      : `<p class="kv">No variant strings were merged: the extracted string matched the canonical name directly.</p>`}`;

  const bar=(title,obj,id)=>`<div class="chartbox"><h3>${title}</h3>
    <div class="canvasholder" style="height:250px"><canvas id="${id}"></canvas></div></div>`;
  document.getElementById('charts').innerHTML=bar('Direction breakdown',e.dirs,'cDir')+bar('Evidence tiers',e.tiers,'cTier');
  const mk=(id,obj,color)=>{
    const k=Object.keys(obj||{}), v=k.map(x=>obj[x]);
    new Chart(document.getElementById(id),{type:'bar',data:{labels:k,datasets:[{data:v,backgroundColor:color}]},
      options:{indexAxis:'y',plugins:{legend:{display:false}},scales:{x:{beginAtZero:true,ticks:{precision:0}}},
        maintainAspectRatio:false}});
  };
  mk('cDir',e.dirs,'#9a5638'); mk('cTier',e.tiers,'#397277');
  render();
}

async function render(){
  document.getElementById('count').innerHTML=`${fmt(rows.length)} findings · <b>${fmt(paperCount(rows))}</b> distinct papers`;
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
