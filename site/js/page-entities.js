import { loadMeta, loadFacets, loadEntities, state, fmt, esc } from './data.js';
import { mount, sortTable, selectOpts, entityCoverageNote } from './ui.js';

await loadMeta(); await loadFacets(); await loadEntities();
mount('entities');
document.getElementById('covnote').innerHTML=entityCoverageNote('this entity list and every entity filter');

const kinds=[...new Set(state.entities.map(e=>e.kind).filter(Boolean))].sort();
document.getElementById('kind').innerHTML=selectOpts(kinds,'','Any entity kind');

let sortKey='np_', sortDir=-1;
const COLS=[['name','Entity',0],['kind','Kind',0],['np_','Papers',1],['nf','Findings',1],
  ['origs','Merged strings',1],['oid','Ontology ID',0],['mapc','Map conf.',0]];

function rowsNow(){
  const q=document.getElementById('q').value.toLowerCase().trim();
  const k=document.getElementById('kind').value, o=document.getElementById('onto').value,
        mc=document.getElementById('mapc').value;
  return state.entities.filter(e=>{
    if(q && !(e.name.toLowerCase().includes(q) || (e.origs||[]).some(s=>s.toLowerCase().includes(q)))) return false;
    if(k && e.kind!==k) return false;
    if(o==='y' && !e.oid) return false;
    if(o==='n' && e.oid) return false;
    if(mc && e.mapc!==mc) return false;
    return true;
  });
}
function render(){
  let r=rowsNow();
  r=sortTable(r.map(e=>({...e, origs:(e.origs||[]).length})), sortKey, sortDir);
  const max=Math.max(...r.map(x=>x.np_),1);
  document.getElementById('tbl').querySelector('thead').innerHTML='<tr>'+COLS.map(([k,l])=>
    `<th data-k="${k}">${l}${k===sortKey?(sortDir<0?' ▾':' ▴'):''}</th>`).join('')+'</tr>';
  document.getElementById('tbl').querySelector('tbody').innerHTML=r.slice(0,600).map(e=>{
    const full=state.entityByName.get(e.name);
    return `<tr>
      <td><a href="entity?e=${encodeURIComponent(e.name)}"><b>${esc(e.name)}</b></a></td>
      <td>${esc(e.kind||'N/A')}</td>
      <td class="num">${fmt(e.np_)} <span class="bar" style="width:${Math.round(46*e.np_/max)}px"></span></td>
      <td class="num">${fmt(e.nf)}</td>
      <td class="num" title="${esc((full.origs||[]).slice(0,12).join(' · '))}">${e.origs||''}</td>
      <td class="mono">${e.oid?esc(e.oid):'N/A'}${e.osrc?` <span class="pill grey">${esc(e.osrc.split('/')[0])}</span>`:''}</td>
      <td>${e.mapc?`<span class="tag${e.mapc!=='high'?' lowconf':''}">${esc(e.mapc)}</span>`:'N/A'}</td></tr>`;
  }).join('');
  document.getElementById('count').innerHTML=`${fmt(r.length)} entities${r.length>600?' (showing first 600)':''} ·
    ${fmt(r.filter(x=>x.oid).length)} with an ontology ID`;
  document.querySelectorAll('th[data-k]').forEach(th=>th.onclick=()=>{
    const k=th.dataset.k; if(k===sortKey) sortDir*=-1; else {sortKey=k; sortDir=(k==='name'||k==='kind'||k==='oid')?1:-1;}
    render();
  });
}
['q','kind','onto','mapc'].forEach(i=>document.getElementById(i).addEventListener('input',render));
render();
