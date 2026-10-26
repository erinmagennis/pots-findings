import { condLabel, sourceList, MINOR_LABEL_MAX } from './labels.js';
import { loadMeta, loadFacets, loadPapers, state, applyFilters, paperCount, fmt, esc, val } from './data.js';
import { mount } from './ui.js';

await loadMeta(); await loadFacets(); await loadPapers();
mount('conditions');

const conds = state.facets.dicts.c.filter(c=>c && c!=='\u2014');
const stats = conds.map(c=>{
  const rows=applyFilters(state.facets,{c});
  const literatures=[...new Set(rows.map(r=>val('sl',r)).filter(Boolean))].sort();
  const tiers=[...new Set(rows.map(r=>val('ti',r)).filter(Boolean))].sort();
  return {c, n:rows.length, papers:paperCount(rows), literatures, tiers};
}).sort((a,b)=>b.n-a.n);
const main = stats.filter(s=>s.n>=MINOR_LABEL_MAX), minor = stats.filter(s=>s.n<MINOR_LABEL_MAX);

document.getElementById('cards').innerHTML = main.slice(0,6).map(s=>
  `<div class="stat"><div class="v">${fmt(s.n)}</div><div class="k">${esc(condLabel(s.c))}</div>
   <div class="kv">${fmt(s.papers)} papers</div></div>`).join('');

document.getElementById('tbl').querySelector('thead').innerHTML=
  `<tr><th>Condition label</th><th>Findings</th><th>Papers</th><th>Source coverage</th></tr>`;
const rowHtml = s=>`<tr>
  <td><a href="condition?c=${encodeURIComponent(s.c)}"><b>${esc(condLabel(s.c))}</b></a></td>
  <td class="num">${fmt(s.n)}</td><td class="num">${fmt(s.papers)}</td>
  <td><span class="kv">${esc(sourceList(s.literatures))}</span></td>
  </tr>`;
document.getElementById('tbl').querySelector('tbody').innerHTML = main.map(rowHtml).join('');
if(minor.length){
  document.querySelector('#tbl').closest('.tblwrap').insertAdjacentHTML('afterend', `<div class="minor-labels">
    <h3>Labels with fewer than ${MINOR_LABEL_MAX} findings</h3>
    <p class="kv">These labels were assigned to very few findings. They are kept as extracted and are not merged into other groups.</p>
    <div class="tblwrap"><table><thead><tr><th>Condition label</th><th>Findings</th><th>Papers</th><th>Source coverage</th></tr></thead>
    <tbody>${minor.map(rowHtml).join('')}</tbody></table></div></div>`);
}

new Chart(document.getElementById('cChart'),{
  type:'bar',
  data:{labels:main.map(s=>condLabel(s.c)),datasets:[{label:'findings',data:main.map(s=>s.n),backgroundColor:'#9a5638'}]},
  options:{plugins:{legend:{display:false},tooltip:{callbacks:{
    afterLabel:i=>`${main[i.dataIndex].papers} distinct papers; ${main[i.dataIndex].literatures.length} source literatures`}}},
    scales:{y:{beginAtZero:true}}, maintainAspectRatio:false}});
