import { loadMeta, loadPapers, loadFacets, loadEntities, getJSON, state, fmt, esc, paperByPmid, val, applyFilters, paperCount } from './data.js';
import { mount, sortTable, flagPills } from './ui.js';
import { condLabel, themeLabel, srcLabel, MINOR_LABEL_MAX } from './labels.js';

await loadMeta(); await loadPapers(); await loadFacets(); await loadEntities();
mount('discover');
const C=state.meta.counts;
document.querySelector('#dtabs').insertAdjacentHTML('beforebegin', `<div class="statgrid findings-summary">
  <a class="stat" href="#assoc"><div class="v">${fmt(C.assoc_significant_total)}</div><div class="k">significant comparisons</div><div class="kv">top ${fmt(C.associations)} listed</div></a>
  <a class="stat" href="#contra"><div class="v">${fmt(C.contradictions_total)}</div><div class="k">contradictions</div><div class="kv">top ${fmt(C.contradictions)} listed</div></a>
  <a class="stat" href="#under"><div class="v">${fmt(C.understudied_total)}</div><div class="k">understudied signals</div><div class="kv">top ${fmt(C.understudied)} listed</div></a>
  <a class="stat" href="#nulls"><div class="v">${fmt(C.nulls)}</div><div class="k">null or failed findings</div></a>
</div>`);

// overview bars follow the default exclusion: findings from retracted papers and correction notices are left out
const facetRows = applyFilters(state.facets,{});
const EXCL_NOTE = 'Papers flagged as retracted or as correction notices are left out.';
const tally = field => { const map=new Map(); facetRows.forEach(row=>{ const value=val(field,row); if(value) map.set(value,(map.get(value)||0)+1); }); return [...map].sort((a,b)=>b[1]-a[1]); };
const pct = (n,d) => d ? `${(n/d*100).toFixed(1)}%` : '0%';
const barRows = (items, denominator, linkFor=()=>null, limit=8, show=x=>x) => items.slice(0,limit).map(([label,n])=>`<div class="overview-bar"><div class="overview-bar-head"><span>${linkFor(label)||esc(show(label))}</span><b>${fmt(n)} <small>${pct(n,denominator)}</small></b></div><div class="overview-track"><i style="width:${Math.max(2,n/items[0][1]*100)}%"></i></div></div>`).join('');

async function viewOverview(){
  const [associations, contradictions, understudied] = await Promise.all([getJSON('associations.json'),getJSON('contradictions.json'),getJSON('understudied.json')]);
  const years=tally('y').filter(([year])=>year!=='0').sort((a,b)=>Number(a[0])-Number(b[0]));
  const areas=tally('th');
  // stray one-off labels from extraction stay in the tables but off the overview bars
  const directions=tally('d').filter(([,n])=>n>=MINOR_LABEL_MAX);
  const nulls=tally('nc').filter(([,n])=>n>=MINOR_LABEL_MAX);
  const plain=x=>String(x).replace(/-/g,' ');
  const reach=new Map(), pcol=state.facets.cols.p;
  for(const r of facetRows){ const e=val('e',r); if(!e) continue; if(!reach.has(e)) reach.set(e,new Set()); reach.get(e).add(pcol[r]); }
  const entityRows=[...reach].map(([name,s])=>[name,s.size]).sort((a,b)=>b[1]-a[1]).slice(0,8);
  const nPapers=paperCount(facetRows);
  const entityLinks=barRows(entityRows, nPapers, label=>`<a href="entity?e=${encodeURIComponent(label)}">${esc(label)}</a>`);
  const maxYear=years.length?years[years.length-1][0]:'current';
  document.getElementById('view').innerHTML=`<section class="overview-grid" aria-label="Findings overview">
    <div class="overview-main">
      <div class="overview-section"><div class="section-kicker">01 · Literature growth</div><h2>Findings by publication year</h2><p class="kv">Denominator: ${fmt(facetRows.length)} finding rows. ${EXCL_NOTE} Year comes from the source paper. <a href="search">Search the underlying findings</a>.</p><div class="year-bars">${years.map(([year,n])=>`<div class="year-bar"><span>${esc(year)}</span><i style="height:${Math.max(4,n/years.reduce((m,x)=>Math.max(m,x[1]),0)*100)}%" title="${fmt(n)} findings"></i><b>${fmt(n)}</b></div>`).join('')}</div><p class="kv">${esc(maxYear)} is a partial year where applicable.</p></div>
      <div class="overview-section"><div class="section-kicker">02 · Research areas</div><h2>Most represented themes</h2><p class="kv">Denominator: ${fmt(facetRows.length)} finding rows with a theme label. Missing theme labels are excluded.</p>${barRows(areas, facetRows.length, ()=>null, 8, themeLabel)}</div>
      <div class="overview-section"><div class="section-kicker">03 · Direction and null results</div><h2>What the extracted rows report</h2><div class="overview-columns"><div><h3>Direction</h3><p class="kv">Denominator: ${fmt(directions.reduce((s,x)=>s+x[1],0))} labeled rows.</p>${barRows(directions, directions.reduce((s,x)=>s+x[1],0), ()=>null, 8, plain)}</div><div><h3>Null or failed result</h3><p class="kv">Denominator: ${fmt(nulls.reduce((s,x)=>s+x[1],0))} labeled rows.</p>${barRows(nulls, nulls.reduce((s,x)=>s+x[1],0), ()=>null, 8, plain)}</div></div></div>
    </div>
    <aside class="overview-side"><div class="overview-section"><div class="section-kicker">04 · Connected entities</div><h2>Highest paper reach</h2><p class="kv">Denominator: ${fmt(nPapers)} papers. Entity coverage is a subset of the findings.</p>${entityLinks}<a class="overview-link" href="connections">Open the connection map →</a></div>
      <div class="overview-section"><div class="section-kicker">05 · Review signals</div><h2>Current contradictions</h2><p class="overview-number">${fmt(state.meta.counts.contradictions_total)}</p><p class="kv">Rows with conflicting extracted directions or null-versus-positive results.</p><a class="overview-link" href="#contra">Review contradictions →</a><h3>Under-studied signals</h3><p class="overview-number">${fmt(C.understudied_total)}</p><p class="kv">Entity and condition signals with three or fewer papers.</p><a class="overview-link" href="#under">Review under-studied signals →</a></div>
      <div class="overview-section"><div class="section-kicker">06 · Read the record</div><h2>Complete tables</h2><p class="kv">Browse every row behind this overview, with links to source papers and entities.</p><a class="overview-link" href="#assoc">Comparisons →</a><a class="overview-link" href="#nulls">Null and failed →</a><a class="overview-link" href="papers">All papers →</a><a class="overview-link" href="entities">All entities →</a></div>
    </aside></section>`;
}

const asList=v=>v==null?[]:Array.isArray(v)?v:String(v).split(/[|,;]\s*/).filter(Boolean);
const pmidLinks=(v,cap=6)=>{const values=asList(v); return values.length
  ? values.slice(0,cap).map(p=>`<a href="paper?pmid=${esc(p)}">${esc(p)}</a>`).join(' ')
    +(values.length>cap?` <span class="kv">+${values.length-cap} more</span>`:'')
  :'N/A';};
const sourceList=v=>asList(v).map(x=>`<span class="tag">${esc(srcLabel(x))}</span>`).join(' ');

export function csv(rows,cols,name){
  const quote=v=>{if(v==null)return '';const s=String(v);return /[",\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;};
  const head=[
    `# POTS and related-condition findings browser: ${name}`,
    `# generated ${state.meta.generated_utc} | ${fmt(C.findings)} findings from ${fmt(C.papers)} papers`,
    `# papers flagged as retracted or as correction notices are left out of this table`,
    `# scope: pots-findings ${state.meta.version} full corpus; identifiers verified at their authorities; scientific fidelity not yet human-checked`,
    `# absence of a finding is not evidence of absence`,
    `# automated extraction can contain errors; co-mention is not interaction or causation`,
    `# not medical advice; cite and read the original papers`
  ];
  const body=[...head,cols.join(','),...rows.map(r=>cols.map(c=>quote(r[c])).join(','))].join('\n');
  const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([body],{type:'text/csv'})); a.download=name; a.click();
  URL.revokeObjectURL(a.href);
}

async function viewAssoc(){
  const d=await getJSON('associations.json');
  document.getElementById('view').innerHTML=`<div class="panel">
    <h2>Entity co-mentions</h2>
    <p class="lede">${fmt(C.associations_total)} entity pairs occur in at least three of the same papers; the ${fmt(d.n)} strongest are listed. ${fmt(C.assoc_significant_total)}
      pass the supplied BH-FDR q&lt;0.05 threshold. ${EXCL_NOTE}</p>
    <div class="note stop"><b>Co-mention is not interaction or causation.</b> A pair can arise from common
      reporting practices, nested terminology, or a paper discussing separate topics.</div>
    <div class="chks"><label><input type="checkbox" id="aCross" checked> cross-kind only</label>
      <label><input type="checkbox" id="aSig" checked> q&lt;0.05 only</label></div>
    <div class="rowmeta"><div id="aCount"></div><button id="aCsv">Download CSV</button></div>
    <div class="tblwrap"><table id="aTbl"><thead></thead><tbody></tbody></table></div></div>`;
  let key='assoc_score_recomputed',direction=-1;
  const rowsNow=()=>d.rows.filter(r=>(!document.getElementById('aCross').checked||r.cross_kind)
    &&(!document.getElementById('aSig').checked||r.significant_fdr05));
  const columns=[['entity_a','Entity A'],['entity_b','Entity B'],['n_papers_both','Papers together'],
    ['lift','Lift'],['jaccard','Jaccard'],['q_bh','q (BH)'],['n_conditions','Conditions'],['pmids','Papers']];
  function render(){
    const values=sortTable(rowsNow(),key,direction);
    document.querySelector('#aTbl thead').innerHTML='<tr>'+columns.map(([k,l])=>
      `<th data-k="${k}">${l}${k===key?(direction<0?' ▾':' ▴'):''}</th>`).join('')+'</tr>';
    document.querySelector('#aTbl tbody').innerHTML=values.slice(0,400).map(r=>`<tr>
      <td><a href="entity?e=${encodeURIComponent(r.entity_a)}">${esc(r.entity_a)}</a><div class="kv">${esc(r.entity_kind_a||'')}</div></td>
      <td><a href="entity?e=${encodeURIComponent(r.entity_b)}">${esc(r.entity_b)}</a><div class="kv">${esc(r.entity_kind_b||'')}</div></td>
      <td class="num">${fmt(r.n_papers_both)}<div class="kv">expected ${Number(r.expected_papers_both||0).toFixed(1)}</div></td>
      <td class="num">${r.lift==null?'N/A':Number(r.lift).toFixed(1)}</td>
      <td class="num">${r.jaccard==null?'N/A':Number(r.jaccard).toFixed(3)}</td>
      <td class="num">${r.q_bh==null?'N/A':Number(r.q_bh).toExponential(2)}</td>
      <td class="num">${fmt(r.n_conditions)}</td><td>${pmidLinks(r.pmids)}</td></tr>`).join('');
    document.getElementById('aCount').textContent=`${fmt(values.length)} pairs shown${values.length>400?' (first 400)':''}`;
    document.querySelectorAll('#aTbl th[data-k]').forEach(th=>th.onclick=()=>{
      const next=th.dataset.k;if(next===key)direction*=-1;else{key=next;direction=next.startsWith('entity_')?1:-1;}render();});
  }
  ['aCross','aSig'].forEach(id=>document.getElementById(id).onchange=render);
  document.getElementById('aCsv').onclick=()=>csv(rowsNow(),[
    'entity_a','entity_b','entity_kind_a','entity_kind_b','n_papers_both','expected_papers_both',
    'lift','jaccard','q_bh','significant_fdr05','cross_kind','n_conditions','pmids'],'associations.csv');
  render();
}

async function viewUnder(opt){
  const d=await getJSON('understudied.json');
  document.getElementById('view').innerHTML=`<div class="panel">
    <h2>Under-studied signals</h2>
    <p class="lede">${fmt(C.understudied_total)} entity and condition signals with three or fewer papers and at least two findings; the ${fmt(d.n)} with the most findings are listed for possible replication work. ${EXCL_NOTE}</p>
    <div class="note stop"><b>Thin evidence can be noise.</b> This table does not establish independent-lab
      replication. It reports the fields present in the current combined analysis and should be used to find
      candidates for closer review.</div>
    <div class="chks"><label><input type="checkbox" id="uThin" checked> thin signals only</label>
      <label><input type="checkbox" id="uTwo" checked> at least 2 papers</label>
      <label><input type="checkbox" id="uCase" checked> exclude case-report-only</label></div>
    <div class="rowmeta"><div id="uCount"></div><button id="uCsv">Download CSV</button></div>
    <div class="tblwrap"><table id="uTbl"><thead></thead><tbody></tbody></table></div></div>`;
  let key='replication_score',direction=-1;
  const rowsNow=()=>d.rows.filter(r=>(!document.getElementById('uThin').checked||r.is_thin)
    &&(!document.getElementById('uTwo').checked||r.n_papers>=2)
    &&(!document.getElementById('uCase').checked||!r.case_report_only));
  const columns=[['canonical_entity','Entity'],['condition','Condition'],['direction','Direction'],
    ['n_papers','Papers'],['n_findings','Findings'],['best_tier','Best tier'],['max_year','Latest'],
    ['replication_score','Score'],['source_literatures','Source literatures'],['pmids','Papers']];
  function render(){
    const values=sortTable(rowsNow(),key,direction);
    document.querySelector('#uTbl thead').innerHTML='<tr>'+columns.map(([k,l])=>
      `<th data-k="${k}">${l}${k===key?(direction<0?' ▾':' ▴'):''}</th>`).join('')+'</tr>';
    document.querySelector('#uTbl tbody').innerHTML=values.slice(0,400).map(r=>`<tr>
      <td><a href="entity?e=${encodeURIComponent(r.canonical_entity)}">${esc(r.canonical_entity)}</a><div class="kv">${esc(r.entity_kind||'')}</div></td>
      <td>${esc(condLabel(r.condition)||'N/A')}</td><td>${esc(r.direction||'N/A')}</td>
      <td class="num">${fmt(r.n_papers)}</td><td class="num">${fmt(r.n_findings)}</td>
      <td>${esc(r.best_tier||'N/A')}</td><td class="num">${r.max_year||'N/A'}</td>
      <td class="num">${r.replication_score==null?'N/A':Number(r.replication_score).toFixed(2)}</td>
      <td>${sourceList(r.source_literatures)}</td><td>${pmidLinks(r.pmids)}</td></tr>`).join('');
    document.getElementById('uCount').textContent=`${fmt(values.length)} signals shown${values.length>400?' (first 400)':''}`;
    document.querySelectorAll('#uTbl th[data-k]').forEach(th=>th.onclick=()=>{const next=th.dataset.k;
      if(next===key)direction*=-1;else{key=next;direction=next==='canonical_entity'?1:-1;}render();});
  }
  if(opt==='all') ['uThin','uTwo','uCase'].forEach(id=>{document.getElementById(id).checked=false;});  // discover#under?all: every listed row
  ['uThin','uTwo','uCase'].forEach(id=>document.getElementById(id).onchange=render);
  document.getElementById('uCsv').onclick=()=>csv(rowsNow(),columns.map(x=>x[0]),'understudied_signals.csv');
  render();
}

async function viewContra(){
  const d=await getJSON('contradictions.json');
  document.getElementById('view').innerHTML=`<div class="panel">
    <h2>Contradictions</h2>
    <p class="lede">${fmt(C.contradictions_total)} entity and condition pairs with conflicting directions (the ${fmt(d.n)} strongest are listed):
      ${fmt(C.contra_flip_total)} direction flips and ${fmt(C.contra_null_vs_pos_total)} null-versus-positive conflicts. ${EXCL_NOTE}</p>
    <p class="kv">A disagreement means papers found the same thing higher in some and lower in others, or an effect in some and none in others. Only results the model tagged as a comparison between groups count, such as people with and without the condition, or two patient groups. Results tagged as a change after a treatment are left out. No person has checked these tags.</p>
    <div class="note stop">Different populations, methods, or source literatures can produce different results.
      A row here flags disagreement for review; it does not prove that either paper is wrong.</div>
    <div class="chks"><label>Type <select id="kType"><option value="">any</option>
      <option value="direction-flip">direction flip</option><option value="null-vs-positive">null vs positive</option>
      </select></label><label><input type="checkbox" id="kMulti"> multiple source literatures only</label></div>
    <div class="rowmeta"><div id="kCount"></div><button id="kCsv">Download CSV</button></div><div id="kList"></div></div>`;
  const rowsNow=()=>d.rows.filter(r=>(!document.getElementById('kType').value||r.conflict_type===document.getElementById('kType').value)
    &&(!document.getElementById('kMulti').checked||asList(r.source_literatures).length>1));
  function render(){
    const values=rowsNow(); document.getElementById('kCount').textContent=`${fmt(values.length)} contradictions shown`;
    document.getElementById('kList').innerHTML=values.slice(0,150).map(r=>`<div class="panel" style="padding:12px">
      <h3><a href="entity?e=${encodeURIComponent(r.canonical_entity)}">${esc(r.canonical_entity)}</a>
        <span class="kv">in ${esc(condLabel(r.condition)||'N/A')}</span></h3>
      <div>${sourceList(r.source_literatures)} <span class="pill grey">${esc(r.conflict_type)}</span></div>
      <div class="sides"><div class="side A"><h4>Side A: ${esc(r.side_A_direction||'N/A')}</h4>
        <div class="kv">${fmt(r.n_papers_A)} papers, ${fmt(r.n_findings_A)} findings, best tier ${esc(r.top_tier_A||'N/A')}</div>
        <div class="kv">${pmidLinks(r.pmids_A,8)}</div></div>
      <div class="side B"><h4>Side B: ${esc(r.side_B_direction||'N/A')}</h4>
        <div class="kv">${fmt(r.n_papers_B)} papers, ${fmt(r.n_findings_B)} findings, best tier ${esc(r.top_tier_B||'N/A')}</div>
        <div class="kv">${pmidLinks(r.pmids_B,8)}</div></div></div>
      ${r.n_papers_both_sides?`<div class="kv">${r.n_papers_both_sides} paper(s) report both directions.</div>`:''}
      </div>`).join('')||'<div class="panel">No contradictions match.</div>';
  }
  ['kType','kMulti'].forEach(id=>document.getElementById(id).onchange=render);
  document.getElementById('kCsv').onclick=()=>csv(rowsNow(),[
    'canonical_entity','condition','conflict_type','side_A_direction','n_papers_A','pmids_A',
    'side_B_direction','n_papers_B','pmids_B','source_literatures','conflict_strength'],'contradictions.csv');
  render();
}

async function viewNulls(){
  // index + column-oriented shards (newest papers first): render from the first shard, load the rest in the background
  const idx=await getJSON('null_results.json');
  const toObj=row=>Object.fromEntries(idx.fields.map((k,i)=>[k,row[i]]));
  const d={n:idx.n, rows:[]}; let loaded=0;
  const addShard=sh=>{ d.rows.push(...sh.rows.map(toObj)); loaded++; };
  if(idx.shards.length) addShard(await getJSON(idx.shards[0].file));
  document.getElementById('view').innerHTML=`<div class="panel"><h2>Null and failed results</h2>
    <p class="lede">${fmt(d.n)} findings classified as biomarker, treatment, or diagnostic nulls. ${EXCL_NOTE}</p>
    <div class="note">A null result is not proof of absence or ineffectiveness. Check the sample, dose,
      comparator, and source paper.</div>
    <div class="searchbar"><input id="nQ" placeholder="filter by entity, paper title, or treatment">
      <select id="nClass"><option value="">Any class</option></select>
      <select id="nTier"><option value="">Any evidence tier</option></select></div>
    <div class="rowmeta"><div id="nCount"></div><button id="nCsv">Download CSV</button></div>
    <div class="tblwrap"><table id="nTbl"><thead><tr><th>Entity</th><th>Class</th><th>Condition</th>
      <th>Evidence</th><th>Year</th><th>Source</th><th>Excerpt</th></tr></thead><tbody></tbody></table></div>
    <div class="pager" id="nPager"></div></div>`;
  const unique=k=>[...new Set(d.rows.map(r=>r[k]).filter(Boolean))].sort();
  const fillSelect=(id,k,anyLabel)=>{ const el=document.getElementById(id), keep=el.value;
    el.innerHTML=`<option value="">${anyLabel}</option>`+unique(k).map(v=>`<option${v===keep?' selected':''}>${esc(v)}</option>`).join(''); };
  fillSelect('nClass','null_class','Any class'); fillSelect('nTier','evidence_tier','Any evidence tier');
  let page=0; const PAGE=40;
  const rowsNow=()=>{const q=document.getElementById('nQ').value.toLowerCase().trim();
    const cls=document.getElementById('nClass').value,tier=document.getElementById('nTier').value;
    return d.rows.filter(r=>{const p=paperByPmid(r.canonical_pmid);
      return (!cls||r.null_class===cls)&&(!tier||r.evidence_tier===tier)
        &&(!q||`${r.canonical_entity||''} ${r.entity||''} ${r.treatment_class||''} ${p?.title||''}`.toLowerCase().includes(q));});};
  function render(){const values=sortTable(rowsNow(),'year',-1),slice=values.slice(page*PAGE,(page+1)*PAGE);
    document.querySelector('#nTbl tbody').innerHTML=slice.map(r=>{const p=paperByPmid(r.canonical_pmid),url=p&&(p.doi_url||p.pubmed_url||p.pmc_url);
      return `<tr><td>${r.canonical_entity?`<a href="entity?e=${encodeURIComponent(r.canonical_entity)}">${esc(r.canonical_entity)}</a>`:esc(r.entity||'N/A')}</td>
      <td>${esc(r.null_class||'N/A')}</td><td>${esc(condLabel(r.condition)||'N/A')}</td><td>${esc(r.evidence_tier||'N/A')}</td>
      <td class="num">${r.year||'N/A'}</td><td>${flagPills(r.canonical_pmid)}${url?`<a href="${esc(url)}" target="_blank" rel="noopener">${esc(p.first_author||'Source paper')}</a>`:'Source paper'}
        <div class="kv">${esc((p?.journal||'').slice(0,50))}</div><a class="kv" href="paper?pmid=${esc(r.canonical_pmid)}">all findings</a></td>
      <td>${r.provenance_quote_trunc?`<div class="quote">“${esc(r.provenance_quote_trunc)}”</div>`:''}</td></tr>`;}).join('');
    document.getElementById('nCount').textContent=`${fmt(values.length)} results`+(loaded<idx.shards.length?` (loading: ${fmt(d.rows.length)} of ${fmt(d.n)} rows so far)`:'');
    const pages=Math.ceil(values.length/PAGE);document.getElementById('nPager').innerHTML=`<button id="np" ${page===0?'disabled':''}>prev</button>
      <span>page ${page+1} / ${Math.max(pages,1)}</span><button id="nn" ${page>=pages-1?'disabled':''}>next</button>`;
    document.getElementById('np').onclick=()=>{page--;render();};document.getElementById('nn').onclick=()=>{page++;render();};}
  ['nQ','nClass','nTier'].forEach(id=>document.getElementById(id).addEventListener('input',()=>{page=0;render();}));
  document.getElementById('nCsv').onclick=()=>csv(rowsNow(),[
    'canonical_pmid','tier','source_literature','canonical_entity','entity','null_class','condition',
    'finding_type','treatment_class','evidence_tier','certainty','study_type','n_participants','year',
    'provenance_quote_trunc'],'null_results.csv'); render();
  for(const sh of idx.shards.slice(1)){
    if(!document.getElementById('nTbl')) return;                 // user left the tab
    addShard(await getJSON(sh.file));
    await new Promise(r=>setTimeout(r,0));                       // let the page breathe between shards
    if(document.getElementById('nTbl')) render();
  }
  if(document.getElementById('nTbl')){ fillSelect('nClass','null_class','Any class'); fillSelect('nTier','evidence_tier','Any evidence tier'); render(); }
}

async function viewConv(){
  const d=await getJSON('convergence.json');
  document.getElementById('view').innerHTML=`<div class="panel"><h2>Shared biology across literatures</h2>
    <p class="lede">${fmt(d.n)} canonical entities reported in a consistent direction across source literatures. ${EXCL_NOTE}</p>
    <div class="note stop"><b>Shared biology is not a comorbidity claim.</b> This view identifies repeated entity
      signals across extracted literatures. It does not show that the conditions co-occur in the same patients.</div>
    <div class="chks"><label><input type="checkbox" id="vFour" checked> at least 4 source literatures</label>
      <label><input type="checkbox" id="vCross"> present in both tiers</label></div>
    <div class="rowmeta"><div id="vCount"></div><button id="vCsv">Download CSV</button></div>
    <div class="tblwrap"><table id="vTbl"><thead></thead><tbody></tbody></table></div></div>`;
  let key='n_source_literatures',direction=-1;
  const rowsNow=()=>d.rows.filter(r=>(!document.getElementById('vFour').checked||r.n_source_literatures>=4)
    &&(!document.getElementById('vCross').checked||r.cross_tier));
  const columns=[['canonical_entity','Entity'],['concordant_direction','Direction'],
    ['n_source_literatures','Literatures'],['n_conditions','Conditions'],['n_papers','Papers'],
    ['n_findings','Findings'],['best_tier','Best evidence'],['tiers','Tiers'],['source_literatures','Sources']];
  function render(){const values=sortTable(rowsNow(),key,direction);
    document.querySelector('#vTbl thead').innerHTML='<tr>'+columns.map(([k,l])=>`<th data-k="${k}">${l}</th>`).join('')+'</tr>';
    document.querySelector('#vTbl tbody').innerHTML=values.slice(0,400).map(r=>`<tr>
      <td><a href="entity?e=${encodeURIComponent(r.canonical_entity)}">${esc(r.canonical_entity)}</a><div class="kv">${esc(r.entity_kind||'')}</div></td>
      <td>${esc(r.concordant_direction||'N/A')}</td><td class="num">${fmt(r.n_source_literatures)}</td>
      <td class="num">${fmt(r.n_conditions)}</td><td class="num">${fmt(r.n_papers)}</td><td class="num">${fmt(r.n_findings)}</td>
      <td>${esc(r.best_tier||'N/A')}</td><td>${sourceList(r.tiers)}</td><td>${sourceList(r.source_literatures)}</td></tr>`).join('');
    document.getElementById('vCount').textContent=`${fmt(values.length)} rows shown${values.length>400?' (first 400)':''}`;
    document.querySelectorAll('#vTbl th[data-k]').forEach(th=>th.onclick=()=>{const next=th.dataset.k;if(next===key)direction*=-1;else{key=next;direction=-1;}render();});}
  ['vFour','vCross'].forEach(id=>document.getElementById(id).onchange=render);
  document.getElementById('vCsv').onclick=()=>csv(rowsNow(),columns.map(x=>x[0]),'convergence.csv'); render();
}

const VIEWS={overview:viewOverview,assoc:viewAssoc,under:viewUnder,contra:viewContra,nulls:viewNulls,conv:viewConv};
function go(){const [key,opt]=(location.hash||'#overview').slice(1).split('?'),fn=VIEWS[key]||viewOverview;
  document.querySelectorAll('#dtabs a').forEach(a=>a.classList.toggle('on',a.getAttribute('href')==='#'+key));
  document.getElementById('view').innerHTML='<div class="panel"><span class="spinner"></span> loading...</div>';fn(opt);}
window.addEventListener('hashchange',go);go();
