import { loadMeta, loadFacets, loadPapers, loadEntities, state, applyFilters, paperCount,
         fmt, esc, val } from './data.js';
import { mount, entityCoverageNote } from './ui.js';

await loadMeta(); await loadFacets(); await loadPapers(); await loadEntities();
mount('charts');
const C=state.meta.counts, F=state.facets;

document.getElementById('stats').innerHTML=[
  [fmt(C.findings),'findings'],[fmt(C.papers),'papers'],
  [fmt(C.canonical_entities),'canonical entities'],[fmt(C.entities_with_ontology),'with ontology ID'],
  [fmt(C.nulls),'null / failed results'],[fmt(C.contradictions_total),'contradictions']
].map(([v,k])=>`<div class="stat"><div class="v">${v}</div><div class="k">${k}</div></div>`).join('');

const PALETTE=['#9a5638','#397277','#71896f','#343735','#b97858','#5b8f91','#91a58d','#6d6a63'];
const tally=(rows,field)=>{ const m=new Map();
  for(const r of rows){ const v=val(field,r); if(!v||v==='\u2014') continue; m.set(v,(m.get(v)||0)+1); } return m; };

function chartBox(id,title,sub,note){
  return `<div class="chartbox"><h3>${title}</h3>
    ${sub?`<p class="kv">${sub}</p>`:''}${note||''}
    <div class="canvasholder"><canvas id="${id}"></canvas></div>
    <div style="margin-top:8px;display:flex;gap:8px"><button data-png="${id}">PNG</button>
      <button data-csv="${id}">CSV</button></div></div>`;
}
const CSVDATA={};

const all=Array.from({length:F.n},(_,i)=>i);
const boxes=[];

/* 1. findings by condition */
const condM=[...tally(all,'c')].sort((a,b)=>b[1]-a[1]);
boxes.push(chartBox('c1','Findings by condition',
  `Distinct papers per condition are shown in the tooltip. Condition labels can occur across several source
   literatures, so use the source-literature filter when you need extraction provenance.`));

/* 2. evidence tier composition */
const tierM=[...tally(all,'tr')].sort((a,b)=>b[1]-a[1]);
boxes.push(chartBox('c2','Evidence-tier composition',
  'Review/expert-opinion and case reports together outnumber RCTs and meta-analyses by a wide margin: weight findings accordingly.'));

/* 3. top entities by paper count */
const topEnt=[...state.entities].sort((a,b)=>b.np_-a.np_).slice(0,20);
boxes.push(chartBox('c3','Top 20 canonical entities by paper count',
  'Paper counts use one paper per PubMed record and include split-derived rows.',
  entityCoverageNote('this entity chart')));

/* 4. direction split for a chosen entity */
boxes.push(`<div class="chartbox"><h3>Direction split for one entity</h3>
  <div class="searchbar" style="margin-bottom:8px">
    <select id="entSel" style="flex:1 1 260px;padding:7px"></select></div>
  <div class="canvasholder"><canvas id="c4"></canvas></div>
  <div style="margin-top:8px;display:flex;gap:8px"><button data-png="c4">PNG</button>
    <button data-csv="c4">CSV</button></div></div>`);

/* 5. findings over time */
const yrM=new Map();
for(const r of all){ const y=F.cols.y[r]; if(y>0) yrM.set(y,(yrM.get(y)||0)+1); }
const yrs=[...yrM.keys()].sort();
boxes.push(chartBox('c5','Findings over time (publication year)',
  `Year is the source paper's publication year. ${state.meta.counts.findings? '':''}
   ${C.year_max} is a partial year. The shape reflects
   both real publication growth and what the query retrieved.`));

document.getElementById('charts').innerHTML=boxes.join('');

const condPapers=new Map(condM.map(([c])=>[c,paperCount(applyFilters(F,{c}))]));

new Chart(document.getElementById('c1'),{type:'bar',
  data:{labels:condM.map(x=>x[0]),datasets:[{label:'findings',data:condM.map(x=>x[1]),
    backgroundColor:'#9a5638'}]},
  options:{plugins:{legend:{display:false},tooltip:{callbacks:{
    afterLabel:i=>`${condPapers.get(condM[i.dataIndex][0])} distinct papers`}}},
    scales:{y:{beginAtZero:true}},maintainAspectRatio:false}});
CSVDATA.c1={cols:['condition','findings','papers'],
  rows:condM.map(([c,n])=>[c,n,condPapers.get(c)])};

new Chart(document.getElementById('c2'),{type:'bar',
  data:{labels:tierM.map(x=>x[0]),datasets:[{data:tierM.map(x=>x[1]),backgroundColor:'#397277'}]},
  options:{indexAxis:'y',plugins:{legend:{display:false}},scales:{x:{beginAtZero:true}},maintainAspectRatio:false}});
CSVDATA.c2={cols:['evidence_tier','findings'],rows:tierM};

new Chart(document.getElementById('c3'),{type:'bar',
  data:{labels:topEnt.map(e=>e.name),datasets:[
    {label:'papers',data:topEnt.map(e=>e.np_),backgroundColor:'#9a5638'},
    {label:'papers (direct only)',data:topEnt.map(e=>e.npd),backgroundColor:'#71896f'}]},
  options:{indexAxis:'y',scales:{x:{beginAtZero:true}},maintainAspectRatio:false}});
CSVDATA.c3={cols:['entity','kind','papers','papers_direct','findings'],
  rows:topEnt.map(e=>[e.name,e.kind,e.np_,e.npd,e.nf])};

const sel=document.getElementById('entSel');
sel.innerHTML=[...state.entities].sort((a,b)=>b.np_-a.np_).slice(0,300)
  .map(e=>`<option value="${esc(e.name)}">${esc(e.name)} (${e.np_} papers)</option>`).join('');
let c4=null;
function drawEnt(){
  // A select with no explicit selection reports '' in some engines; fall back to the first option
  // so the chart always renders rather than silently staying blank.
  const name = sel.value || sel.options[0]?.value;
  const e = name ? state.entityByName.get(name) : null;
  if(!e){ document.getElementById('c4').closest('.chartbox')
    .querySelector('.canvasholder').innerHTML='<p class="kv">Select an entity to see its direction split.</p>';
    return; }
  const k=Object.keys(e.dirs||{}), v=k.map(x=>e.dirs[x]);
  if(c4) c4.destroy();
  c4=new Chart(document.getElementById('c4'),{type:'doughnut',
    data:{labels:k,datasets:[{data:v,backgroundColor:PALETTE}]},
    options:{maintainAspectRatio:false,plugins:{title:{display:true,text:`${e.name}: ${e.nf} findings, ${e.np_} papers`}}}});
  CSVDATA.c4={cols:['entity','direction','findings'],rows:k.map((x,i)=>[e.name,x,v[i]])};
}
sel.onchange=drawEnt; drawEnt();

new Chart(document.getElementById('c5'),{type:'line',
  data:{labels:yrs,datasets:[{label:'findings',data:yrs.map(y=>yrM.get(y)),borderColor:'#9a5638',
    backgroundColor:'rgba(138,75,42,.12)',fill:true,tension:.25}]},
  options:{plugins:{legend:{display:false}},scales:{y:{beginAtZero:true}},maintainAspectRatio:false}});
CSVDATA.c5={cols:['year','findings'],rows:yrs.map(y=>[y,yrM.get(y)])};

document.addEventListener('click',e=>{
  const png=e.target.dataset?.png, cs=e.target.dataset?.csv;
  if(png){ const cv=document.getElementById(png); const a=document.createElement('a');
    a.href=cv.toDataURL('image/png'); a.download=`${png}.png`; a.click(); }
  if(cs){ const d=CSVDATA[cs]; if(!d) return;
    const q=v=>{const s=String(v==null?'':v); return /[",\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;};
    const M=state.meta, cc=M.counts;
    const head=[`# POTS and related-condition findings browser: chart data (${cs})`,
      `# generated ${M.generated_utc} | ${fmt(cc.findings)} findings from ${fmt(cc.papers)} papers`,
      `# papers counted per PubMed record (pmid) | canonical_entity covers ${cc.canonical_entity_pct}% of findings`,
      `# scope: pots-findings ${M.version} full corpus; identifiers verified at their authorities; scientific fidelity not yet human-checked`,
      `# absence of a finding is not evidence of absence`,
      `# NOT MEDICAL ADVICE. Machine-extracted research information; extraction errors possible.`];
    const body=[...head, d.cols.join(','),...d.rows.map(r=>r.map(q).join(','))].join('\n');
    const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([body],{type:'text/csv'}));
    a.download=`${cs}_data.csv`; a.click(); URL.revokeObjectURL(a.href); }
});
