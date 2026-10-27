import { loadMeta, loadFacets, loadPapers, state, fmt, esc, flagsOf } from './data.js';
import { mount, sortTable, qs, flagPills } from './ui.js';

const PAGE=60; let page=0, sortKey='n_findings', sortDir=-1;
await loadMeta(); await loadPapers();
mount('papers');

const P=state.papers, all=P.rows.map((r,i)=>{
  const o={_i:i}; for(const k in P.idx) o[k]=r[P.idx[k]]; return o;
});
// paper-flag filter: every flag that occurs, with its paper count from meta (?flag=retracted deep-links here)
const flagSel=document.getElementById('flag'), C=state.meta.counts;
flagSel.innerHTML+=Object.entries(state.flagLabels).filter(([k])=>C[`flag_${k}`]>0)
  .map(([k,l])=>`<option value="${esc(k)}">${esc(l)} (${fmt(C[`flag_${k}`])})</option>`).join('');
if(qs('flag')) flagSel.value=qs('flag');
const COLS=[['first_author','First author'],['title','Title'],['journal','Journal'],['year','Year'],
  ['n_findings','Findings'],['cited_by_count','Cited by']];

function rowsNow(){
  const q=document.getElementById('q').value.toLowerCase().trim();
  const oa=document.getElementById('oa').value, fl=flagSel.value;
  const y0=+document.getElementById('y0').value||0, y1=+document.getElementById('y1').value||9999;
  return all.filter(p=>{
    if(q && !((p.title||'').toLowerCase().includes(q) || (p.authors||'').toLowerCase().includes(q)
       || (p.journal||'').toLowerCase().includes(q))) return false;
    if(oa==='y' && !p.is_open_access) return false;
    if(fl && !flagsOf(p.pmid).some(x=>x.f===fl)) return false;
    if(p.year && (p.year<y0||p.year>y1)) return false;
    return true;
  });
}
function render(){
  const r=sortTable(rowsNow(), sortKey, sortDir);
  document.getElementById('tbl').querySelector('thead').innerHTML='<tr>'+COLS.map(([k,l])=>
    `<th data-k="${k}">${l}${k===sortKey?(sortDir<0?' ▾':' ▴'):''}</th>`).join('')+'</tr>';
  document.getElementById('tbl').querySelector('tbody').innerHTML=r.slice(page*PAGE,(page+1)*PAGE).map(p=>{
    const etal=p.author_count>1?' et al.':'';
    return `<tr>
      <td><a href="paper?pmid=${esc(p.pmid)}"><b>${esc(p.first_author||'N/A')}${etal}</b></a></td>
      <td>${flagPills(p.pmid)}${esc((p.title||'').slice(0,120))}${(p.title||'').length>120?'…':''}</td>
      <td class="jr">${esc(p.journal||'N/A')}</td>
      <td class="num">${p.year||'N/A'}</td>
      <td class="num">${fmt(p.n_findings)}</td>
      <td class="num">${fmt(p.cited_by_count)}</td></tr>`;
  }).join('');
  document.getElementById('count').innerHTML=`${fmt(r.length)} papers`;
  const pages=Math.ceil(r.length/PAGE);
  document.getElementById('pager').innerHTML=`<button ${page===0?'disabled':''} id="prev">‹ prev</button>
    <span>page ${page+1} / ${Math.max(pages,1)}</span>
    <button ${page>=pages-1?'disabled':''} id="next">next ›</button>`;
  const pv=document.getElementById('prev'), nx=document.getElementById('next');
  if(pv) pv.onclick=()=>{page--;render();}; if(nx) nx.onclick=()=>{page++;render();};
  document.querySelectorAll('th[data-k]').forEach(th=>th.onclick=()=>{
    const k=th.dataset.k; if(k===sortKey) sortDir*=-1;
    else {sortKey=k; sortDir=(k==='first_author'||k==='title'||k==='journal')?1:-1;} page=0; render();});
}
['q','oa','flag','y0','y1'].forEach(i=>document.getElementById(i).addEventListener('input',()=>{page=0;render();}));
render();
