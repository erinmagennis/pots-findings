import { condLabel, srcLabel } from './labels.js';
import { loadMeta, loadFacets, loadPapers, loadEntities, state, applyFilters, excludedIn, fmt, esc, val,
         FILTER_FIELDS } from './data.js';
import { mount, selectOpts, entityCoverageNote, flagToggle, wireFlagToggle } from './ui.js';

await loadMeta(); await loadFacets(); await loadPapers(); await loadEntities();
mount('analyze');
const F=state.facets;

const DIM = {c:'Condition', d:'Direction', tr:'Evidence tier', ce:'Certainty', ft:'Finding type',
  ek:'Entity kind', mc:'Identifier status', e:'Canonical entity', st:'Study type', y:'Year',
  ca:'Causal/correlational', an:'Anatomical system', ps:'POTS subtype', ag:'Age group',
  sx:'Sex/hormonal', th:'Theme', sr:'Source stream', es:'Evidence stratum', rt:'Relation type',
  cv:'COVID-associated', nc:'Null/positive class', ti:'Package (provenance)', sl:'Source literature'};

document.getElementById('xaxis').innerHTML=Object.entries(DIM)
  .map(([k,l])=>`<option value="${k}"${k==='c'?' selected':''}>${l}</option>`).join('');
document.getElementById('series').innerHTML='<option value="">None</option>'+
  Object.entries(DIM).map(([k,l])=>`<option value="${k}">${l}</option>`).join('');

document.getElementById('bfilters').innerHTML=FILTER_FIELDS.map(k=>{
  const vals=[...F.dicts[k]].sort((a,b)=>String(a).localeCompare(String(b)));
  return `<div><label>${DIM[k]||k}</label><select data-f="${k}">${selectOpts(vals,'','Any',k==='c'?condLabel:k==='sl'?srcLabel:undefined)}</select></div>`;
}).join('');
document.getElementById('flagToggleSlot').innerHTML=flagToggle('fFlagged');
wireFlagToggle('fFlagged', ()=>{ clearPreset(); draw(); });
document.getElementById('covnote').innerHTML=
  `<div id="cn"></div>`;

function opts(){
  const o={};
  document.querySelectorAll('#bfilters select[data-f]').forEach(s=>{ if(s.value) o[s.dataset.f]=s.value; });
  o.hasQuant=document.getElementById('fQuant').checked;
  o.nullOnly=document.getElementById('fNull').checked;
  o.excludeSplit=document.getElementById('fSplit').checked;
  o.y0=document.getElementById('y0').value; o.y1=document.getElementById('y1').value;
  return o;
}
// display name for a stored category value (condition and source-literature keys never show raw)
const lab=(field,v)=> field==='c'?condLabel(v) : field==='sl'?srcLabel(v) : String(v);
const getDim=(field,row)=> field==='y' ? (F.cols.y[row]||null) : val(field,row);

let chart=null, LAST=null;
function draw(){
  const xf=document.getElementById('xaxis').value, sf=document.getElementById('series').value,
        ym=document.getElementById('ymetric').value, ct=document.getElementById('ctype').value,
        topn=+document.getElementById('topn').value||15, sortby=document.getElementById('sortby').value;
  const rows=applyFilters(F,opts());

  // group -> series -> {findings, papers:Set, entities:Set}
  const G=new Map();
  for(const r of rows){
    const x=getDim(xf,r); if(x==null||x==='\u2014') continue;
    const s=sf? (getDim(sf,r)??'N/A') : '_';
    if(!G.has(x)) G.set(x,new Map());
    const m=G.get(x);
    if(!m.has(s)) m.set(s,{n:0,p:new Set(),e:new Set()});
    const cell=m.get(s); cell.n++; cell.p.add(F.cols.p[r]);
    const ce=val('e',r); if(ce) cell.e.add(ce);
  }
  const metric=cell=> ym==='findings'?cell.n : ym==='papers'?cell.p.size : ym==='entities'?cell.e.size : cell.n;
  // order categories
  let cats=[...G.keys()];
  const total=c=>[...G.get(c).values()].reduce((a,b)=>a+metric(b),0);
  if(sortby==='value') cats.sort((a,b)=>total(b)-total(a));
  else if(sortby==='label') cats.sort((a,b)=>String(a).localeCompare(String(b),undefined,{numeric:true}));
  else cats.sort((a,b)=> (typeof a==='number'&&typeof b==='number')? a-b : String(a).localeCompare(String(b),undefined,{numeric:true}));
  if(cats.length>topn && sortby==='value') cats=cats.slice(0,topn);
  else if(cats.length>topn) cats=cats.slice(0,topn);

  const seriesKeys = sf ? [...new Set(cats.flatMap(c=>[...G.get(c).keys()]))].sort() : ['_'];
const PALETTE=['#9a5638','#397277','#71896f','#343735','#b97858','#5b8f91','#91a58d','#6d6a63'];
  const grandTotal=cats.reduce((a,c)=>a+total(c),0);
  const datasets=seriesKeys.map((s,i)=>({
    label: sf? lab(sf,s):'value',
    data: cats.map(c=>{ const cell=G.get(c).get(s); if(!cell) return 0;
      const v=metric(cell); return ym==='pct'? +(100*v/(grandTotal||1)).toFixed(2) : v; }),
    backgroundColor: ct==='doughnut'? PALETTE : PALETTE[i%PALETTE.length],
    borderColor: PALETTE[i%PALETTE.length], fill: ct==='line'? false:true, tension:.25
  }));

  if(chart) chart.destroy();
  const type = ct==='stackedBar'||ct==='horizontalBar'?'bar':ct;
  chart=new Chart(document.getElementById('cv'),{
    type, data:{labels:cats.map(c=>lab(xf,c)),datasets},
    options:{maintainAspectRatio:false, indexAxis: ct==='horizontalBar'?'y':'x',
      plugins:{legend:{display: !!sf || ct==='doughnut'}},
      scales: ct==='doughnut'? {} : {
        x:{stacked:ct==='stackedBar'}, y:{stacked:ct==='stackedBar',beginAtZero:true,
        title:{display:true,text: ym==='pct'?'% of findings':ym==='papers'?'distinct papers':
          ym==='entities'?'distinct canonical entities':'findings'}}}}});

  const ylab={findings:'Findings',papers:'Distinct papers',pct:'% of findings',entities:'Distinct canonical entities'}[ym];
  document.getElementById('ctitle').textContent=`${ylab} by ${DIM[xf]}${sf?` split by ${DIM[sf]}`:''}`;
  const nf=Object.entries(opts()).filter(([k,v])=>v&&v!==''&&k!=='y0'&&k!=='y1').length;
  const hidden=state.includeFlagged?0:excludedIn(applyFilters(F,{...opts(),includeFlagged:true}));
  document.getElementById('csub').innerHTML=
    `${fmt(rows.length)} findings pass the current filters (${nf} active filter${nf===1?'':'s'}) ·
     ${fmt(cats.length)} categories shown${G.size>cats.length?` of ${fmt(G.size)}`:''}
     ${hidden?` · <span id="flagHidden">${fmt(hidden)} from retracted papers and correction notices left out</span>`:''}
     ${ym==='papers'?' · papers counted per PubMed record':''}
     ${(xf==='e'||sf==='e'||ym==='entities')?` · <b>canonical-entity based: covers ${state.meta.counts.canonical_entity_pct}% of findings</b>`:''}`;
  document.getElementById('cn').innerHTML=(xf==='e'||sf==='e'||ym==='entities')
    ? entityCoverageNote('this chart') : '';

  // table + CSV payload
  // a Total column only where it adds something and adds up: findings and % split by series (papers and entities can repeat across series)
  const withTotal = !!sf && (ym==='findings'||ym==='pct');
  const cols=[DIM[xf], ...(sf?seriesKeys.map(s=>lab(sf,s)):[ylab]), ...(withTotal?['Total']:[])];
  const trows=cats.map(c=>{
    const vals=seriesKeys.map(s=>{ const cell=G.get(c).get(s); if(!cell) return 0;
      const v=metric(cell); return ym==='pct'? +(100*v/(grandTotal||1)).toFixed(2):v; });
    const sum=vals.reduce((a,b)=>a+b,0);
    return [lab(xf,c),...vals, ...(withTotal?[ym==='pct'? +sum.toFixed(2) : sum]:[])];
  });
  document.querySelector('#dtbl thead').innerHTML='<tr>'+cols.map(c=>`<th>${esc(c)}</th>`).join('')+'</tr>';
  document.querySelector('#dtbl tbody').innerHTML=trows.map(r=>'<tr>'+r.map((v,i)=>
    i===0?`<td>${esc(v)}</td>`:`<td class="num">${typeof v==='number'?v.toLocaleString('en-US'):esc(v)}</td>`).join('')+'</tr>').join('');
  LAST={cols,rows:trows,meta:{x:DIM[xf],series:sf?DIM[sf]:'',metric:ylab,filters:JSON.stringify(opts())}};
}

/* Presets: each one sets the builder's own controls, then redraws. Counts shown come from meta.json only. */
const topEntity=[...state.entities].sort((a,b)=>b.np_-a.np_)[0]?.name||'';
const PRESETS=[
  {id:'cond',label:'Findings by condition',x:'c',y:'findings',type:'bar',topn:60,sort:'value',
    note:'Condition labels can occur across several source literatures. Use the source literature filter when you need to know where a finding came from.'},
  {id:'tier',label:'Evidence tiers',x:'tr',y:'findings',type:'horizontalBar',topn:20,sort:'value',
    note:'Review and expert opinion plus case reports together outnumber RCTs and meta-analyses by a wide margin. Weigh findings with that in mind.'},
  {id:'ents',label:'Top 20 entities',x:'e',y:'papers',type:'horizontalBar',topn:20,sort:'value',
    note:'Paper counts use one paper per PubMed record and include split-derived rows.'},
  {id:'dir',label:'Direction split for one entity',x:'d',y:'findings',type:'doughnut',topn:15,sort:'value',filters:{e:topEntity},openFilters:true,
    note:'Showing the most-studied entity. Change the Canonical entity filter to pick another.'},
  {id:'year',label:'Findings over time',x:'y',y:'findings',type:'line',topn:60,sort:'natural',
    note:`Year is the source paper's publication year, and ${state.meta.counts.year_max} is a partial year. The shape reflects both real publication growth and what the search retrieved.`}
];
const presetRow=document.getElementById('presetRow'), presetNote=document.getElementById('presetNote');
presetRow.innerHTML=PRESETS.map(p=>`<button type="button" class="preset-pill" data-preset="${p.id}" aria-pressed="false">${esc(p.label)}</button>`).join('');
function clearPreset(){ presetRow.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed','false')); presetNote.textContent=''; }
function applyPreset(p){
  const set=(id,v)=>{ document.getElementById(id).value=v; };
  set('ctype',p.type); set('xaxis',p.x); set('ymetric',p.y); set('series',p.series||''); set('topn',p.topn); set('sortby',p.sort);
  document.querySelectorAll('#bfilters select[data-f]').forEach(s=>{ s.value=(p.filters&&p.filters[s.dataset.f])||''; });
  ['fQuant','fNull','fSplit'].forEach(id=>{ document.getElementById(id).checked=false; });
  set('y0',''); set('y1','');
  if(p.openFilters) document.querySelector('.analyze-filter-section').open=true;
  draw();
  presetRow.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.preset===p.id)));
  presetNote.textContent=p.note;
}
presetRow.addEventListener('click',e=>{ const b=e.target.closest('button[data-preset]'); if(b) applyPreset(PRESETS.find(p=>p.id===b.dataset.preset)); });

document.getElementById('draw').onclick=draw;
document.querySelectorAll('#ctype,#xaxis,#ymetric,#series,#topn,#sortby').forEach(e=>e.onchange=()=>{ clearPreset(); draw(); });
document.querySelectorAll('#bfilters select,#fQuant,#fNull,#fSplit,#y0,#y1').forEach(e=>e.addEventListener('change',()=>{ clearPreset(); draw(); }));

document.getElementById('png').onclick=()=>{
  const cv=document.getElementById('cv');
  // flatten onto white so the PNG isn't transparent
  const out=document.createElement('canvas'); out.width=cv.width; out.height=cv.height;
  const g=out.getContext('2d'); g.fillStyle='#fff'; g.fillRect(0,0,out.width,out.height); g.drawImage(cv,0,0);
  const a=document.createElement('a'); a.href=out.toDataURL('image/png'); a.download='chart.png'; a.click();
};
document.getElementById('csv').onclick=()=>{
  if(!LAST) return;
  const q=v=>{const s=String(v==null?'':v); return /[",\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;};
  const c=state.meta.counts;
  const head=[`# POTS and related-condition findings browser: chart data`,
    `# metric: ${LAST.meta.metric} by ${LAST.meta.x}${LAST.meta.series?` split by ${LAST.meta.series}`:''}`,
    `# filters: ${LAST.meta.filters}`,
    `# papers are counted per PubMed record (pmid)`,
    `# retracted papers and correction notices: ${state.includeFlagged?'included':'left out (default)'}`,
    `# scope: pots-findings ${state.meta.version} full corpus; identifiers verified at their authorities; scientific fidelity not yet human-checked`,
    `# absence of a finding is not evidence of absence`,
    `# canonical_entity covers ${c.canonical_entity_pct}% of findings; entity-based cuts exclude the rest`,
    `# NOT MEDICAL ADVICE - machine-extracted research information, extraction errors possible`];
  const body=[...head, LAST.cols.map(q).join(','), ...LAST.rows.map(r=>r.map(q).join(','))].join('\n');
  const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([body],{type:'text/csv'}));
  a.download='chart_data.csv'; a.click(); URL.revokeObjectURL(a.href);
};
draw();
