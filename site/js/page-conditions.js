import { loadMeta, loadFacets, loadPapers, state, applyFilters, paperCount, fmt, esc, val,
         TIER1_CONDITIONS as TIER1 } from './data.js';
import { mount } from './ui.js';

await loadMeta(); await loadFacets(); await loadPapers();
mount('conditions.html');

const INCID = state.meta.incidental;

const conds = state.facets.dicts.c.filter(c=>c && c!=='—');
const stats = conds.map(c=>{
  const rows=applyFilters(state.facets,{c});
  return {c, n:rows.length, papers:paperCount(rows), rows};
}).sort((a,b)=>b.n-a.n);

document.getElementById('cards').innerHTML = stats.slice(0,6).map(s=>
  `<div class="stat"><div class="v">${fmt(s.n)}</div><div class="k">${esc(s.c)}</div>
   <div class="kv">${fmt(s.papers)} papers</div></div>`).join('');

document.getElementById('tbl').querySelector('thead').innerHTML=
  `<tr><th>Condition</th><th>Findings</th><th>Papers</th><th>Coverage in Tier 1</th></tr>`;
document.getElementById('tbl').querySelector('tbody').innerHTML=stats.map(s=>{
  const incidental = !TIER1.has(s.c);
  const note = incidental
    ? `<span class="tag lowconf">incidental mentions only</span> ${INCID[s.c]!=null?`— ${INCID[s.c]} POTS/dysautonomia papers mention it; its own literature is not extracted`:'— its own literature is not extracted'}`
    : `<span class="tag tier">within Tier-1 extraction scope</span>`;
  return `<tr><td><a href="condition.html?c=${encodeURIComponent(s.c)}"><b>${esc(s.c)}</b></a></td>
    <td class="num">${fmt(s.n)}</td><td class="num">${fmt(s.papers)}</td><td>${note}</td></tr>`;
}).join('');

new Chart(document.getElementById('cChart'),{
  type:'bar',
  data:{labels:stats.map(s=>s.c),
        datasets:[{label:'findings',data:stats.map(s=>s.n),
          backgroundColor:stats.map(s=>TIER1.has(s.c)?'#8a4b2a':'#c9b08f')}]},
  options:{plugins:{legend:{display:false},
    tooltip:{callbacks:{afterLabel:(i)=>TIER1.has(stats[i.dataIndex].c)?'within Tier-1 extraction scope':'incidental mentions inside POTS/dysautonomia papers only'}}},
    scales:{y:{beginAtZero:true}}, maintainAspectRatio:false}});
