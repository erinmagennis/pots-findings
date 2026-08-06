import { loadMeta, loadFacets, loadPapers, state, applyFilters, paperCount, fmt, esc, val } from './data.js';
import { mount } from './ui.js';

await loadMeta(); await loadFacets(); await loadPapers();
mount('conditions.html');

const conds = state.facets.dicts.c.filter(c=>c && c!=='\u2014');
const stats = conds.map(c=>{
  const rows=applyFilters(state.facets,{c});
  const literatures=[...new Set(rows.map(r=>val('sl',r)).filter(Boolean))].sort();
  const tiers=[...new Set(rows.map(r=>val('ti',r)).filter(Boolean))].sort();
  return {c, n:rows.length, papers:paperCount(rows), literatures, tiers};
}).sort((a,b)=>b.n-a.n);

document.getElementById('cards').innerHTML = stats.slice(0,6).map(s=>
  `<div class="stat"><div class="v">${fmt(s.n)}</div><div class="k">${esc(s.c)}</div>
   <div class="kv">${fmt(s.papers)} papers</div></div>`).join('');

document.getElementById('tbl').querySelector('thead').innerHTML=
  `<tr><th>Condition label</th><th>Findings</th><th>Papers</th><th>Source coverage</th></tr>`;
document.getElementById('tbl').querySelector('tbody').innerHTML=stats.map(s=>`<tr>
  <td><a href="condition.html?c=${encodeURIComponent(s.c)}"><b>${esc(s.c)}</b></a></td>
  <td class="num">${fmt(s.n)}</td><td class="num">${fmt(s.papers)}</td>
  <td><span class="tag tier">tier ${s.tiers.map(esc).join(', ')}</span>
    <span class="kv">${s.literatures.length} source literature${s.literatures.length===1?'':'s'}:
      ${s.literatures.slice(0,5).map(esc).join(', ')}${s.literatures.length>5?` +${s.literatures.length-5} more`:''}</span></td>
  </tr>`).join('');

new Chart(document.getElementById('cChart'),{
  type:'bar',
  data:{labels:stats.map(s=>s.c),datasets:[{label:'findings',data:stats.map(s=>s.n),backgroundColor:'#9a5638'}]},
  options:{plugins:{legend:{display:false},tooltip:{callbacks:{
    afterLabel:i=>`${stats[i.dataIndex].papers} distinct papers across ${stats[i.dataIndex].literatures.length} source literatures`}}},
    scales:{y:{beginAtZero:true}}, maintainAspectRatio:false}});
