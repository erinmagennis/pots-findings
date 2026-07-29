import { loadMeta, loadPapers, getJSON, state, fmt, esc, paperByPmid } from './data.js';
import { mount, sortTable } from './ui.js';

await loadMeta(); await loadPapers();
mount('discover.html');
const C = state.meta.counts;

/* The parquet exports store list/dict columns as strings: pmids as "123,456" and
   evidence/tier/certainty profiles as JSON text. Normalize before rendering. */
const asList = v => v==null ? []
  : Array.isArray(v) ? v
  : typeof v==='string' ? (v.trim()===''? [] :
      (v.trim().startsWith('[') ? (()=>{ try{ const p=JSON.parse(v); return Array.isArray(p)?p:[]; }catch{ return []; } })()
                                : v.split(/[,;]\s*/).filter(Boolean)))
  : [];
const asObj = v => {
  if(v==null || v==='') return null;
  if(typeof v==='object') return v;
  if(typeof v==='string'){ try{ const p=JSON.parse(v); return (p&&typeof p==='object')?p:null; }catch{ return null; } }
  return null;
};

const pmidLinks = (v, cap=8) => { const arr=asList(v); return !arr.length ? '—' :
  arr.slice(0,cap).map(p=>`<a href="paper.html?pmid=${esc(p)}">${esc(p)}</a>`).join(' ')
  + (arr.length>cap?` <span class="kv">+${arr.length-cap} more</span>`:''); };

const prof = v => { const o=asObj(v);
  if(o) return Object.entries(o).map(([k,n])=>`${esc(k)}&nbsp;${n}`).join(' · ');
  const a=asList(v); return a.length? a.map(x=>esc(String(x))).join(', ') : ''; };

/** Render up to 3 supporting quotes for one side of a contradiction, each with its own
    citation, tier and year — so a reader can weigh the two sides without leaving the page. */
const evidenceList = (v, cap=3) => {
  const items=asList(v).slice(0,cap);
  if(!items.length) return '';
  return `<ul class="ev">${items.map(e=>{
    if(typeof e==='string') return `<li>${esc(e.slice(0,200))}</li>`;
    const pm=e.canonical_pmid||e.pmid, p=pm?paperByPmid(pm):null;
    const cite = p ? `${esc(p.first_author||'?')}${p.author_count>1?' et al.':''} ${p.year||''}`
                   : (pm?`pmid ${esc(pm)}`:'');
    const q=(e.quote||'').slice(0,200);
    return `<li>${q?`<span class="quote">“${esc(q)}”</span> `:''}
      ${pm?`<a href="paper.html?pmid=${esc(pm)}">${cite}</a>`:cite}
      ${e.evidence_tier?`<span class="tag">${esc(e.evidence_tier)}</span>`:''}
      ${e.certainty&&e.certainty!=='confirmed'?`<span class="tag lowconf">${esc(e.certainty)}</span>`:''}</li>`;
  }).join('')}</ul>`;
};

/* ================= associations ================= */
async function viewAssoc(){
  const d=await getJSON('associations.json');
  const el=document.getElementById('view');
  el.innerHTML=`<div class="panel">
    <h2>Entity co-occurrence associations</h2>
    <p class="lede">Pairs of canonical entities appearing in the same paper more often than chance.
      ${fmt(C.assoc_significant)} of ${fmt(C.assoc_primary)} tested pairs are significant at BH-FDR q&lt;0.05.</p>
    <div class="note stop"><b>Co-occurrence is not causation</b>, and it is not even a claimed relationship —
      it only means two entities were discussed in the same paper. Many pairs are
      <b>reporting conventions</b>: measures that are always reported together (e.g. HRV sub-measures), or
      name-nested / surface-linked strings. Those are labelled below and excluded from the default view.</div>
    <div class="chks">
      <label><input type="checkbox" id="aCross" checked> cross-kind only (different entity kinds)</label>
      <label><input type="checkbox" id="aNoConv" checked> hide reporting-convention pairs</label>
      <label><input type="checkbox" id="aSig" checked> significant at q&lt;0.05 only</label>
    </div>
    <div class="rowmeta"><div id="aCount"></div><div><button id="aCsv">Download CSV</button></div></div>
    <div class="tblwrap"><table id="aTbl"><thead></thead><tbody></tbody></table></div></div>`;

  let sk='assoc_score', sd=-1;
  const COLS=[['entity_a','Entity A'],['entity_b','Entity B'],['n_papers_both','Papers both'],
    ['lift','Lift'],['jaccard','Jaccard'],['q_bh','q (BH)'],['n_conditions','Conds'],['flags','Flags'],['pmids','Papers']];
  const rowsNow=()=>d.rows.filter(r=>{
    if(document.getElementById('aCross').checked && !r.cross_kind) return false;
    if(document.getElementById('aNoConv').checked && r.reporting_convention) return false;
    if(document.getElementById('aSig').checked && !r.significant_fdr05) return false;
    return true;
  });
  function render(){
    const r=sortTable(rowsNow(), sk, sd);
    document.querySelector('#aTbl thead').innerHTML='<tr>'+COLS.map(([k,l])=>
      `<th data-k="${k}">${l}${k===sk?(sd<0?' ▾':' ▴'):''}</th>`).join('')+'</tr>';
    document.querySelector('#aTbl tbody').innerHTML=r.slice(0,400).map(x=>{
      const flags=[];
      if(x.trivial_component_link) flags.push('component-of');
      if(x.name_level_nested) flags.push('name-nested');
      if(x.surface_string_linked) flags.push('surface-linked');
      if(!x.cross_kind) flags.push('same-kind');
      return `<tr>
        <td><a href="entity.html?e=${encodeURIComponent(x.entity_a)}">${esc(x.entity_a)}</a>
            <div class="kv">${esc(x.entity_kind_a||'—')}${x.map_confidence_a&&x.map_confidence_a!=='high'?` <span class="tag lowconf">map ${esc(x.map_confidence_a)}</span>`:''}</div></td>
        <td><a href="entity.html?e=${encodeURIComponent(x.entity_b)}">${esc(x.entity_b)}</a>
            <div class="kv">${esc(x.entity_kind_b||'—')}${x.map_confidence_b&&x.map_confidence_b!=='high'?` <span class="tag lowconf">map ${esc(x.map_confidence_b)}</span>`:''}</div></td>
        <td class="num">${fmt(x.n_papers_both)}<div class="kv">exp ${(x.expected_papers_both||0).toFixed(1)}</div></td>
        <td class="num">${x.lift==null?'—':x.lift.toFixed(1)}</td>
        <td class="num">${x.jaccard==null?'—':x.jaccard.toFixed(3)}</td>
        <td class="num">${x.q_bh==null?'—':(x.q_bh<1e-4?x.q_bh.toExponential(1):x.q_bh.toFixed(4))}
            ${x.significant_fdr05?'':'<span class="pill grey">ns</span>'}</td>
        <td class="num">${x.n_conditions||'—'}</td>
        <td>${flags.length?flags.map(f=>`<span class="tag lowconf">${f}</span>`).join(' '):'<span class="tag tier">non-trivial</span>'}</td>
        <td>${pmidLinks(x.pmids,5)}</td></tr>`;
    }).join('');
    document.getElementById('aCount').innerHTML=`${fmt(r.length)} pairs shown${r.length>400?' (first 400)':''} ·
      ${fmt(d.n)} total in table`;
    document.querySelectorAll('#aTbl th[data-k]').forEach(th=>th.onclick=()=>{
      const k=th.dataset.k; if(k===sk) sd*=-1; else {sk=k; sd=(k==='entity_a'||k==='entity_b')?1:-1;} render();});
  }
  ['aCross','aNoConv','aSig'].forEach(i=>document.getElementById(i).onchange=render);
  document.getElementById('aCsv').onclick=()=>csv(rowsNow(),
    ['entity_a','entity_b','entity_kind_a','entity_kind_b','n_papers_both','expected_papers_both','lift',
     'jaccard','p_hypergeom','q_bh','significant_fdr05','cross_kind','reporting_convention','n_conditions'],
    'associations.csv');
  render();
}

/* ================= under-studied ================= */
async function viewUnder(){
  const d=await getJSON('understudied.json');
  document.getElementById('view').innerHTML=`<div class="panel">
    <h2>Under-studied signals</h2>
    <p class="lede">${fmt(C.understudied)} candidate signals that look directionally consistent but rest on
      few papers — places where a replication attempt would be informative.</p>
    <div class="note stop"><b>Thin evidence includes noise and single-lab artifacts.</b> A high score here
      means "few papers, agreeing" — which is also what a spurious result looks like. Of the
      ${fmt(C.understudied)} rows, ${fmt(C.understudied_two_author_notcase)} have ≥2 independent last authors and are
      not case-report-only; ${fmt(C.understudied_qualifying)} of those also pass the headline-eligibility bar
      (the stricter default view below).</div>
    <div class="chks">
      <label><input type="checkbox" id="uInd" checked> ≥2 independent last authors</label>
      <label><input type="checkbox" id="uCase" checked> exclude case-report-only</label>
      <label><input type="checkbox" id="uHead" checked> headline-eligible only</label>
    </div>
    <div class="rowmeta"><div id="uCount"></div><div><button id="uCsv">Download CSV</button></div></div>
    <div class="tblwrap"><table id="uTbl"><thead></thead><tbody></tbody></table></div></div>`;
  let sk='replication_score', sd=-1;
  const COLS=[['canonical_entity','Entity'],['condition','Condition'],['direction','Direction'],
    ['n_papers','Papers'],['n_distinct_last_authors','Indep. labs'],['direction_agreement','Agreement'],
    ['best_tier','Best tier'],['max_year','Latest'],['replication_score','Score'],['pmids','Papers']];
  const rowsNow=()=>d.rows.filter(r=>{
    if(document.getElementById('uInd').checked && !(r.n_distinct_last_authors>=2)) return false;
    if(document.getElementById('uCase').checked && r.case_report_only) return false;
    if(document.getElementById('uHead').checked && !r.headline_eligible) return false;
    return true;
  });
  function render(){
    const r=sortTable(rowsNow(), sk, sd);
    document.querySelector('#uTbl thead').innerHTML='<tr>'+COLS.map(([k,l])=>
      `<th data-k="${k}">${l}${k===sk?(sd<0?' ▾':' ▴'):''}</th>`).join('')+'</tr>';
    document.querySelector('#uTbl tbody').innerHTML=r.slice(0,400).map(x=>`<tr>
      <td><a href="entity.html?e=${encodeURIComponent(x.canonical_entity)}">${esc(x.canonical_entity)}</a>
        <div class="kv">${esc(x.entity_kind||'—')}${x.map_confidence&&x.map_confidence!=='high'?` <span class="tag lowconf">map ${esc(x.map_confidence)}</span>`:''}</div></td>
      <td>${esc(x.condition||'—')}</td>
      <td><span class="tag dir ${x.direction==='elevated'?'up':x.direction==='depleted/reduced'?'down':''}">${esc(x.direction||'—')}</span>
        ${x.bidirectional_conflict?'<span class="tag lowconf">bidirectional</span>':''}</td>
      <td class="num">${fmt(x.n_papers)}${x.case_report_only?'<div class="kv">case-report only</div>':''}</td>
      <td class="num">${fmt(x.n_distinct_last_authors)}</td>
      <td class="num">${x.direction_agreement==null?'—':(100*x.direction_agreement).toFixed(0)+'%'}
        ${x.n_papers_disagreeing?`<div class="kv">${x.n_papers_disagreeing} disagree</div>`:''}</td>
      <td>${esc(x.best_tier||'—')}</td>
      <td class="num">${x.max_year||'—'}</td>
      <td class="num">${x.replication_score==null?'—':x.replication_score.toFixed(2)}
        ${x.is_thin?'<div class="kv">thin</div>':''}</td>
      <td>${pmidLinks(x.pmids,5)}</td></tr>`).join('');
    document.getElementById('uCount').innerHTML=`${fmt(r.length)} signals shown · ${fmt(d.n)} in table`;
    document.querySelectorAll('#uTbl th[data-k]').forEach(th=>th.onclick=()=>{
      const k=th.dataset.k; if(k===sk) sd*=-1; else {sk=k; sd=(k==='canonical_entity'||k==='condition')?1:-1;} render();});
  }
  ['uInd','uCase','uHead'].forEach(i=>document.getElementById(i).onchange=render);
  document.getElementById('uCsv').onclick=()=>csv(rowsNow(),
    ['canonical_entity','entity_kind','condition','direction','n_papers','n_distinct_last_authors',
     'direction_agreement','best_tier','max_year','replication_score','is_thin','case_report_only','headline_eligible'],
    'understudied_signals.csv');
  render();
}

/* ================= contradictions ================= */
async function viewContra(){
  const d=await getJSON('contradictions.json');
  document.getElementById('view').innerHTML=`<div class="panel">
    <h2>Contradictions</h2>
    <p class="lede">${fmt(C.contradictions)} entity–condition pairs where the literature disagrees:
      ${fmt(C.contra_flip)} hard direction flips and ${fmt(C.contra_null_vs_pos)} null-versus-positive conflicts.
      Both sides are shown with their evidence tiers.</p>
    <div class="note stop"><b>${fmt(C.contra_umbrella)} of ${fmt(C.contradictions)} sit under umbrella condition
      labels</b> (e.g. "dysautonomia", "general") and may reflect <b>pooled distinct diseases rather than a
      replication failure</b> — two studies of different patient populations can both be right.
      ${fmt(C.contra_moderator)} have a visible moderator that may explain the split; it is shown when present.</div>
    <div class="chks">
      <label>Type <select id="kType"><option value="">any</option>
        <option value="hard-direction-flip">hard direction flip</option>
        <option value="null-vs-positive">null vs positive</option></select></label>
      <label><input type="checkbox" id="kMod"> has a visible moderator</label>
      <label><input type="checkbox" id="kNarrow"> exclude umbrella condition labels</label>
    </div>
    <div class="rowmeta"><div id="kCount"></div><div><button id="kCsv">Download CSV</button></div></div>
    <div id="kList"></div></div>`;
  const rowsNow=()=>d.rows.filter(r=>{
    const t=document.getElementById('kType').value;
    if(t && r.conflict_type!==t) return false;
    if(document.getElementById('kMod').checked && !r.has_visible_moderator) return false;
    if(document.getElementById('kNarrow').checked && r.broad_condition_flag) return false;
    return true;
  });
  function render(){
    const r=rowsNow();
    document.getElementById('kCount').innerHTML=`${fmt(r.length)} contradictions shown · ${fmt(d.n)} in table`;
    document.getElementById('kList').innerHTML=r.slice(0,120).map(x=>{
      const side=(L,dir,np,nf,tt,tp,cp,pm,ev)=>`<div class="side ${L}">
        <h4>Side ${L} — ${esc(dir||'—')}</h4>
        <div class="kv"><b>${fmt(np)}</b> papers · ${fmt(nf)} findings · top tier <b>${esc(tt||'—')}</b></div>
        <div class="kv">tiers: ${prof(tp)||'—'}</div><div class="kv">certainty: ${prof(cp)||'—'}</div>
        ${evidenceList(ev)}
        <div class="kv" style="margin-top:5px">papers: ${pmidLinks(pm,6)}</div></div>`;
      return `<div class="panel" style="padding:12px">
        <div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:baseline">
          <h3 style="margin:0"><a href="entity.html?e=${encodeURIComponent(x.canonical_entity)}">${esc(x.canonical_entity)}</a>
            <span class="kv">in ${esc(x.condition||'—')}</span></h3>
          <div>
            <span class="tag">${esc(x.conflict_type)}</span>
            ${x.broad_condition_flag?'<span class="tag lowconf" title="Umbrella label may pool distinct diseases">umbrella condition</span>':''}
            ${x.map_confidence_min&&x.map_confidence_min!=='high'?`<span class="tag lowconf">map ${esc(x.map_confidence_min)}</span>`:''}
            ${x.conflict_strength!=null?`<span class="pill grey">strength ${(+x.conflict_strength).toFixed(2)}</span>`:''}
          </div></div>
        <div class="sides">
          ${side('A',x.side_A_direction,x.n_papers_A,x.n_findings_A,x.top_tier_A,x.tier_profile_A,x.certainty_profile_A,x.pmids_A,x.evidence_A)}
          ${side('B',x.side_B_direction,x.n_papers_B,x.n_findings_B,x.top_tier_B,x.tier_profile_B,x.certainty_profile_B,x.pmids_B,x.evidence_B)}
        </div>
        ${x.has_visible_moderator?`<div class="note"><b>Possible moderator:</b>
          ${esc(String(x.moderator_detail || asList(x.moderator_candidates).join(', ')).slice(0,400))} —
          the two sides may be studying different subgroups rather than contradicting each other.</div>`:''}
        ${x.heterogeneity_caveat?`<div class="kv">${esc(String(x.heterogeneity_caveat).slice(0,300))}</div>`:''}
        ${x.n_papers_both_sides?`<div class="kv">${x.n_papers_both_sides} paper(s) report both directions.</div>`:''}
        ${x.scope_note?`<div class="kv">${esc(String(x.scope_note).slice(0,240))}</div>`:''}
      </div>`;
    }).join('') || '<div class="panel">No contradictions match these filters.</div>';
  }
  ['kType','kMod','kNarrow'].forEach(i=>document.getElementById(i).onchange=render);
  document.getElementById('kCsv').onclick=()=>csv(rowsNow(),
    ['canonical_entity','condition','conflict_type','broad_condition_flag','side_A_direction','n_papers_A',
     'top_tier_A','side_B_direction','n_papers_B','top_tier_B','has_visible_moderator','moderator_detail',
     'conflict_strength'],'contradictions.csv');
  render();
}

/* ================= nulls ================= */
async function viewNulls(){
  const d=await getJSON('null_results.json');
  document.getElementById('view').innerHTML=`<div class="panel">
    <h2>Null and failed results</h2>
    <p class="lede">${fmt(C.nulls)} findings that reported <b>no effect</b>, a failed replication, or an
      abandoned approach: ${fmt(C.nulls_biomarker)} biomarker/mechanism nulls, ${fmt(C.nulls_treatment)} treatment
      failures (${fmt(C.nulls_treatment_rct)} at RCT or meta-analysis tier) and ${fmt(C.nulls_diagnostic)} diagnostic nulls.
      Negative results are usually invisible; this view makes them searchable.</p>
    <div class="note">A null result is not proof of absence — it can reflect small samples, wrong dose,
      or a heterogeneous cohort. Check the paper.</div>
    <div class="searchbar" style="margin-top:10px">
      <input type="text" id="nQ" placeholder="filter by entity, title or treatment…" style="flex:1 1 280px">
      <select id="nClass"><option value="">Any class</option></select>
      <select id="nTier"><option value="">Any tier</option></select>
      <select id="nCond"><option value="">Any condition</option></select>
    </div>
    <div class="rowmeta"><div id="nCount"></div><div><button id="nCsv">Download CSV</button></div></div>
    <div class="tblwrap"><table id="nTbl"><thead></thead><tbody></tbody></table></div>
    <div class="rowmeta"><div></div><div class="pager" id="nPager"></div></div></div>`;
  const uniq=(k)=>[...new Set(d.rows.map(r=>r[k]).filter(Boolean))].sort();
  document.getElementById('nClass').innerHTML+=uniq('null_class').map(v=>`<option>${esc(v)}</option>`).join('');
  document.getElementById('nTier').innerHTML+=uniq('evidence_tier').map(v=>`<option>${esc(v)}</option>`).join('');
  document.getElementById('nCond').innerHTML+=uniq('condition').map(v=>`<option>${esc(v)}</option>`).join('');
  let page=0, sk='year', sd=-1;
  const PAGE=40;
  const COLS=[['canonical_entity','Entity'],['null_class','Class'],['condition','Condition'],
    ['evidence_tier','Tier'],['n_participants','n'],['year','Year'],['first_author','Source']];
  const rowsNow=()=>{
    const q=document.getElementById('nQ').value.toLowerCase().trim();
    const c=document.getElementById('nClass').value, t=document.getElementById('nTier').value,
          cd=document.getElementById('nCond').value;
    return d.rows.filter(r=>{
      if(c && r.null_class!==c) return false;
      if(t && r.evidence_tier!==t) return false;
      if(cd && r.condition!==cd) return false;
      if(q && !((r.canonical_entity||'')+' '+(r.entity||'')+' '+(r.title||'')+' '+(r.treatment_class||''))
              .toLowerCase().includes(q)) return false;
      return true;
    });
  };
  function render(){
    const r=sortTable(rowsNow(), sk, sd);
    document.querySelector('#nTbl thead').innerHTML='<tr>'+COLS.map(([k,l])=>
      `<th data-k="${k}">${l}${k===sk?(sd<0?' ▾':' ▴'):''}</th>`).join('')+'<th>Quote &amp; citation</th></tr>';
    document.querySelector('#nTbl tbody').innerHTML=r.slice(page*PAGE,(page+1)*PAGE).map(x=>{
      const url=x.doi_url||x.pubmed_url||'';
      return `<tr>
        <td>${x.canonical_entity?`<a href="entity.html?e=${encodeURIComponent(x.canonical_entity)}">${esc(x.canonical_entity)}</a>`:esc(x.entity||'—')}
          ${x.map_confidence&&x.map_confidence!=='high'?`<div class="kv"><span class="tag lowconf">map ${esc(x.map_confidence)}</span></div>`:''}</td>
        <td><span class="tag">${esc(x.null_class||'—')}</span>
          ${x.negative_strength?`<div class="kv">${esc(x.negative_strength)}</div>`:''}</td>
        <td>${esc(x.condition||'—')}</td>
        <td><span class="tag tier">${esc(x.evidence_tier||'—')}</span></td>
        <td class="num">${x.n_participants||'—'}</td>
        <td class="num">${x.year||'—'}</td>
        <td>${url?`<a href="${esc(url)}" target="_blank" rel="noopener">${esc(x.first_author||'—')}</a>`:esc(x.first_author||'—')}
          <div class="kv jr">${esc((x.journal||'').slice(0,42))}</div>
          <a class="kv" href="paper.html?pmid=${esc(x.canonical_pmid)}">findings →</a></td>
        <td style="max-width:360px">${x.provenance_quote_trunc?`<div class="quote" style="margin:0">“${esc(x.provenance_quote_trunc)}”</div>`:''}
          <div class="kv">${esc(x.citation_short||'')}</div></td></tr>`;
    }).join('');
    document.getElementById('nCount').innerHTML=`${fmt(r.length)} null/failed results shown · ${fmt(d.n)} in table`;
    const pages=Math.ceil(r.length/PAGE);
    document.getElementById('nPager').innerHTML=`<button ${page===0?'disabled':''} id="np">‹ prev</button>
      <span>page ${page+1} / ${Math.max(pages,1)}</span><button ${page>=pages-1?'disabled':''} id="nn">next ›</button>`;
    const p=document.getElementById('np'), n=document.getElementById('nn');
    if(p) p.onclick=()=>{page--;render();}; if(n) n.onclick=()=>{page++;render();};
    document.querySelectorAll('#nTbl th[data-k]').forEach(th=>th.onclick=()=>{
      const k=th.dataset.k; if(k===sk) sd*=-1; else {sk=k; sd=-1;} page=0; render();});
  }
  ['nQ','nClass','nTier','nCond'].forEach(i=>document.getElementById(i).addEventListener('input',()=>{page=0;render();}));
  document.getElementById('nCsv').onclick=()=>csv(rowsNow(),
    ['canonical_pmid','canonical_entity','null_class','condition','finding_type','treatment_class',
     'evidence_tier','certainty','study_type','n_participants','year','first_author','journal','doi_url'],
    'null_results.csv');
  render();
}

/* ================= convergence ================= */
async function viewConv(){
  const d=await getJSON('convergence.json');
  document.getElementById('view').innerHTML=`<div class="panel">
    <h2>Cross-condition convergence <span class="pill grey">Tier-1 scoped</span></h2>
    <p class="lede">${fmt(C.convergence)} entities reported in a consistent direction across more than one
      condition label. ${fmt(C.convergence_nonpots)} pass the ≥2-non-POTS-condition bar and
      ${fmt(C.convergence_headline)} are headline-eligible.</p>
    <div class="note stop"><b>This is the view most likely to be misread.</b> The "other conditions" here are
      <b>incidental mentions inside POTS/dysautonomia papers</b> — not those conditions' own literature, which
      has not been extracted. A row saying an entity converges across POTS and ME/CFS means POTS papers said so.
      Real cross-condition convergence cannot be established until Tiers 2–4 are extracted.</div>
    <div class="chks">
      <label><input type="checkbox" id="vBar" checked> passes ≥2-non-POTS bar</label>
      <label><input type="checkbox" id="vHead"> headline-eligible only</label>
      <label><input type="checkbox" id="vUncontested"> hide contested</label>
    </div>
    <div class="rowmeta"><div id="vCount"></div><div><button id="vCsv">Download CSV</button></div></div>
    <div class="tblwrap"><table id="vTbl"><thead></thead><tbody></tbody></table></div></div>`;
  let sk='score_multicondition', sd=-1;
  const COLS=[['canonical_entity','Entity'],['concordant_direction','Direction'],['n_conditions','Conds'],
    ['n_papers','Papers'],['n_papers_pots_dysautonomia','POTS/dys papers'],['n_papers_other_condition','Other-cond papers'],
    ['best_tier','Best tier'],['frac_confirmed','Confirmed'],['score_multicondition','Score']];
  const rowsNow=()=>d.rows.filter(r=>{
    if(document.getElementById('vBar').checked && !r.passes_nonpots_bar) return false;
    if(document.getElementById('vHead').checked && !r.headline_eligible) return false;
    if(document.getElementById('vUncontested').checked && r.is_contested) return false;
    return true;
  });
  function render(){
    const r=sortTable(rowsNow(), sk, sd);
    document.querySelector('#vTbl thead').innerHTML='<tr>'+COLS.map(([k,l])=>
      `<th data-k="${k}">${l}${k===sk?(sd<0?' ▾':' ▴'):''}</th>`).join('')+'<th>Conditions</th><th>Papers</th></tr>';
    document.querySelector('#vTbl tbody').innerHTML=r.slice(0,300).map(x=>`<tr>
      <td><a href="entity.html?e=${encodeURIComponent(x.canonical_entity)}">${esc(x.canonical_entity)}</a>
        <div class="kv">${esc(x.entity_kind||'—')}</div></td>
      <td><span class="tag dir ${x.concordant_direction==='elevated'?'up':x.concordant_direction==='depleted/reduced'?'down':''}">${esc(x.concordant_direction||'—')}</span>
        ${x.is_contested?'<div class="kv"><span class="tag lowconf">contested</span></div>':''}</td>
      <td class="num">${fmt(x.n_conditions)}</td><td class="num">${fmt(x.n_papers)}</td>
      <td class="num">${fmt(x.n_papers_pots_dysautonomia)}</td>
      <td class="num">${fmt(x.n_papers_other_condition)}</td>
      <td>${esc(x.best_tier||'—')}</td>
      <td class="num">${x.frac_confirmed==null?'—':(100*x.frac_confirmed).toFixed(0)+'%'}</td>
      <td class="num">${x.score_multicondition==null?'—':(+x.score_multicondition).toFixed(2)}</td>
      <td class="kv">${(()=>{
        const sup=asObj(x.per_condition_support), pc=sup&&sup.papers?sup.papers:null;
        const cs=asList(x.conditions);
        if(!cs.length) return '—';
        return cs.map(c=>`${esc(c)}${pc&&pc[c]!=null?`&nbsp;(${pc[c]})`:''}`).join(', ');
      })()}</td>
      <td>${pmidLinks(x.pmids,5)}</td></tr>`).join('');
    document.getElementById('vCount').innerHTML=`${fmt(r.length)} rows shown · ${fmt(d.n)} in table`;
    document.querySelectorAll('#vTbl th[data-k]').forEach(th=>th.onclick=()=>{
      const k=th.dataset.k; if(k===sk) sd*=-1; else {sk=k; sd=(k==='canonical_entity')?1:-1;} render();});
  }
  ['vBar','vHead','vUncontested'].forEach(i=>document.getElementById(i).onchange=render);
  document.getElementById('vCsv').onclick=()=>csv(rowsNow(),
    ['canonical_entity','entity_kind','concordant_direction','n_conditions','n_papers',
     'n_papers_pots_dysautonomia','n_papers_other_condition','best_tier','frac_confirmed',
     'passes_nonpots_bar','headline_eligible','is_contested','score_multicondition'],'convergence.csv');
  render();
}

/* csv download helper — every export carries the scope + limitations header, so a downloaded
   file cannot be read out of context. */
export function csv(rows, cols, name){
  const q=v=>{ if(v==null) return ''; const s=String(v); return /[",\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s; };
  const M=state.meta, c=M.counts;
  const head=[
    `# POTS/dysautonomia Tier-1 findings browser - ${name}`,
    `# generated ${M.generated_utc} | ${fmt(c.findings)} findings from ${fmt(c.papers)} papers`,
    `# papers counted on canonical_pmid (after 8 validated duplicate merges of 9 groups examined)`,
    `# SCOPE: Tier 1 extracted the POTS/dysautonomia literature only - ${fmt(c.papers)} of`,
    `#   ~${fmt(c.corpus_papers_total)} corpus papers (${c.tier1_chunks} of ${c.corpus_chunks} chunks).`,
    `#   Incidental mentions ONLY (own literature NOT extracted, Tiers 2-4): ${Object.keys(M.incidental).join(', ')}`,
    `# canonical_entity is present on ${c.canonical_entity_pct}% of findings; entity roll-ups exclude the rest`,
    `# LIMITS: automated extraction has errors; co-occurrence is not causation; thin evidence`,
    `#   includes noise and single-lab artifacts; ${fmt(c.contra_umbrella)} of ${fmt(c.contradictions)} contradictions`,
    `#   sit under umbrella condition labels and may pool distinct diseases.`,
    `# NOT MEDICAL ADVICE. Machine-extracted research information. Cite the original papers.`];
  const body=[...head, cols.join(','), ...rows.map(r=>cols.map(c=>q(r[c])).join(','))].join('\n');
  const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([body],{type:'text/csv'}));
  a.download=name; a.click(); URL.revokeObjectURL(a.href);
}

const VIEWS={assoc:viewAssoc,under:viewUnder,contra:viewContra,nulls:viewNulls,conv:viewConv};
function go(){
  const h=(location.hash||'#assoc').slice(1);
  const fn=VIEWS[h]||viewAssoc;
  document.querySelectorAll('#dtabs a').forEach(a=>a.classList.toggle('on',a.getAttribute('href')==='#'+h));
  document.getElementById('view').innerHTML='<div class="panel"><span class="spinner"></span> loading…</div>';
  fn();
}
window.addEventListener('hashchange',go);
go();
