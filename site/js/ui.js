/* ui.js: shared chrome: framing banner, nav, result cards, citation lines. */
import { state, esc, fmt, val, origEntity, textOf, detailOf, paper, DIRCLASS, flagsOf, EXCLUDE_TOGGLE_LABEL, setIncludeFlagged } from './data.js';
import { condLabel } from './labels.js';

export const PAGES = [
  ['search','Search'],['discover','Signals'],['connections','Connections'],
  ['builder','Analyze'],['about','About'],['chat','Ask']
];

function contextPopover(){
  const c = state.meta.counts;
  return `<details class="context-details"><summary>Scope &amp; safety</summary><div class="context-popover">
    <p><b>Scope.</b> ${fmt(c.findings)} findings extracted from ${fmt(c.papers)} papers (${c.year_min}–${c.year_max}) across POTS, dysautonomia and ${c.conditions} related condition literatures. Every finding carries a verbatim quote and a link to its paper. Ontology identifiers were verified at their authorities (v1.2); whether each finding states what its paper found has not yet been checked by a human reader. Absence of a signal is not evidence of absence. <a href="about#limits">Verification status</a>.</p>
    <p><b>Not medical advice.</b> Machine-extracted research information, not clinical guidance. No diagnostic or treatment recommendations. Talk to a qualified clinician about any personal health decision.</p>
    <p><b>Automated extraction has errors.</b> Co-occurrence is not causation; thin evidence includes noise and single-lab artifacts. <a href="about#limits">Limitations</a>. Every finding links to its source. The credit belongs to the original authors; please read their paper.</p>
  </div></details>`;
}

function railInner(){
  return `<b>${fmt(state.meta.counts.findings)} findings</b>${fmt(state.meta.counts.papers)} papers · version ${esc(state.meta.version)} ${contextPopover()}`;
}

export function header(active){
  const tabs = PAGES.map(([h,t])=>`<a href="${h}" class="${h===active?'active':''}">${t}</a>`).join('');
  return `<header class="site"><div class="wrap">
    <a class="brand" href="/" aria-label="POTS and Dysautonomia Literature Project home"><span class="mark" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><b></b></span><span class="brand-lockup"><span>POTS &amp; Dysautonomia</span><span>Literature Project</span><small>Research findings, source papers, and connections</small></span></a>
    <button class="mobile-nav-toggle" id="mobileNavToggle" type="button" aria-expanded="false" aria-controls="primaryNav"><span aria-hidden="true">☰</span><span class="sr-only">Menu</span></button>
    <nav class="nav-pill" id="primaryNav" aria-label="Primary navigation">${tabs}</nav>
    <div class="header-rail">${railInner()}</div>
  </div></header>`;
}

export function footer(){
  const m=state.meta;
  return `<div class="quiet-support"><div class="wrap"><strong>Grow the map</strong> Help make this public research index easier to extend, check, and reuse. <a href="about#connect">Collaborate with the project</a>.</div></div>
  <footer class="site"><div class="wrap"><span class="brand-footer">POTS &amp; Dysautonomia Findings</span><span>pots-findings ${esc(m.version)} · ${fmt(m.counts.findings)} findings / ${fmt(m.counts.papers)} papers · data generated ${esc(m.generated_utc)} · <a href="about">Scope, methods and limitations</a>.</span></div></footer>`;
}

/* The header is written into each page's HTML so it paints before any data loads.
   mount() only fills the counts rail; wireChrome() runs as soon as chrome.js loads. */
let wired=false;
export function wireChrome(){
  if(wired) return; wired=true;
  const navToggle = document.getElementById('mobileNavToggle');
  const primaryNav = document.getElementById('primaryNav');
  navToggle?.addEventListener('click', () => {
    const open = navToggle.getAttribute('aria-expanded') === 'true';
    navToggle.setAttribute('aria-expanded', String(!open));
    primaryNav?.toggleAttribute('data-open', !open);
  });
}

export function mount(active){
  document.getElementById('framing-slot')?.remove();
  const slot=document.getElementById('header-slot');
  if(slot) slot.outerHTML = header(active);
  else { const rail=document.querySelector('header.site .header-rail'); if(rail && state.meta) rail.innerHTML = railInner(); }
  const f=document.getElementById('footer-slot'); if(f) f.outerHTML = footer();
  wireChrome();
}

/* ---------- paper flags: compact pills, shared by every list of findings or papers ---------- */
const PILL = {   // flag -> [pill text, pill class, hover text]
  retracted: ['Retracted','err','This paper was retracted on PubMed. Its findings are left out of counts and charts by default.'],
  partially_retracted: ['Partially retracted','err','Part of this paper was retracted on PubMed. Its findings are left out of counts and charts by default.'],
  erratum_notice: ['Correction notice','err','This PubMed record is a correction notice for another paper. Its findings are left out of counts and charts by default.'],
  expression_of_concern: ['Expression of concern','warn','The journal published an expression of concern about this paper.'],
  preprint: ['Preprint','grey','A preprint: not peer reviewed when posted.'],
  preprint_with_published_version: ['Preprint','grey','A preprint. The published version is also in this dataset.']
};
export function flagPills(pmid){
  const seen = new Set(), out = [];
  for(const x of flagsOf(pmid)){
    const p = PILL[x.f]; if(!p || seen.has(p[0])) continue;
    seen.add(p[0]); out.push(`<span class="pill ${p[1]} flag-pill" title="${esc(p[2])}">${p[0]}</span>`);
  }
  return out.length ? `<span class="flag-pills">${out.join('')}</span>` : '';
}
/** the one visible switch for the default exclusion: flagToggle() writes it, wireFlagToggle() sets state.includeFlagged and calls onChange */
export function flagToggle(id){
  return `<label class="flag-toggle"><input type="checkbox" id="${id}"${state.includeFlagged?' checked':''}> ${EXCLUDE_TOGGLE_LABEL}</label>`;
}
export function wireFlagToggle(id, onChange){
  const el=document.getElementById(id); if(!el) return;
  el.checked=state.includeFlagged;
  el.addEventListener('change',()=>{ setIncludeFlagged(el.checked); onChange&&onChange(); });
}

/* ---------- citation line: prominent, always with a link ---------- */
export function citeLine(pi){
  const p = paper(pi);
  if(!p) return `<div class="cite">Citation unavailable</div>`;
  const url = p.doi_url || p.pubmed_url || p.pmc_url || '';
  const etal = p.author_count>1 ? ' et al.' : '';
  const label = `${esc(p.first_author||'Unknown')}${etal}`;
  const link = url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${label}</a>` : label;
  return `<div class="cite">${flagPills(p.pmid)}${link}: <span class="jr">${esc(p.journal||'N/A')}</span>
    ${p.year?`(${p.year})`:''}
    ${p.pubmed_url?` · <a href="${esc(p.pubmed_url)}" target="_blank" rel="noopener">PubMed</a>`:''}
    ${p.doi_url?` · <a href="${esc(p.doi_url)}" target="_blank" rel="noopener">DOI</a>`:''}
    ${p.is_open_access?` · <span class="pill grey">open access</span>`:''}
    <a href="paper?pmid=${esc(p.pmid)}" style="margin-left:6px">all findings from this paper →</a></div>`;
}

/** Reusable notice for any surface built on canonical_entity. Two different coverage numbers :
    they are not the same thing and must not be conflated. */
export function entityCoverageNote(context){
  const c = state.meta.counts;
  return `<div class="note"><b>Entity coverage: read before interpreting ${context}.</b>
    An entity (gene, protein, metabolite, drug, measure, cell type) is named on <b>${fmt(c.entity_string_rows)} of ${fmt(c.findings)} findings
    (${c.entity_string_pct}%)</b>, spanning ${fmt(c.papers_with_canonical_entity)} of ${fmt(c.papers)} papers. The other findings are symptom,
    phenotype, diagnostic or quality-of-life findings that name no entity by design. Named entities are grouped into ${fmt(c.canonical_entities)} entity pages:
    ${fmt(c.verified_id_rows)} findings (${c.verified_id_pct}% of all findings) are anchored to an identifier verified at its authority (HGNC, ChEBI, MeSH, UniProt, HPO, UBERON),
    and spelling variants merge under that identifier; the rest are grouped by name, so one concept can still appear under more than one spelling.
    <b>${context} therefore cover about ${c.entity_string_pct}% of findings, not the whole corpus</b>. Findings without an entity remain fully findable by
    keyword and semantic search.</div>`;
}

/** Result card. Shows canonical entity AND the original string when they differ, so merges are auditable. */
export function findingCard(row, opts={}){
  const t = textOf(row) || '(text not loaded)';
  const d = detailOf(row);
  const dir = val('d',row), ent = val('e',row), cond = val('c',row), tier = val('tr',row),
        cert = val('ce',row), ft = val('ft',row), ek = val('ek',row), mc = val('mc',row),
        yr = val('y',row) || state.facets.cols.y[row], nres = val('nc',row);
  const orig = origEntity(row);
  const dc = DIRCLASS(dir);
  const estr = val('es_str',row);
  const tags = [];
  if(ent) tags.push(`<a class="tag ent" href="entity?e=${encodeURIComponent(ent)}">${esc(ent)}</a>`);
  else if(estr) tags.push(`<span class="tag lowconf" title="This entity string was not canonicalized, so this finding does not appear in entity roll-ups or entity filters. It is still fully searchable by keyword.">${esc(estr)} · not canonicalized</span>`);
  if(dir && dir!=='not applicable') tags.push(`<span class="tag dir ${dc}">${esc(dir)}</span>`);
  if(cond) tags.push(`<a class="tag" href="condition?c=${encodeURIComponent(cond)}">${esc(condLabel(cond))}</a>`);
  if(tier) tags.push(`<span class="tag tier">${esc(tier)}</span>`);
  if(cert) tags.push(`<span class="tag">${esc(cert)}</span>`);
  if(ft) tags.push(`<span class="tag">${esc(ft)}</span>`);
  if(ek) tags.push(`<span class="tag">${esc(ek)}</span>`);
  if(nres && nres!=='positive-effect' && nres!=='not-applicable')
    tags.push(`<span class="tag lowconf">${esc(nres)}</span>`);
  if(mc==='low'||mc==='medium')
    tags.push(`<span class="tag lowconf" title="Entity mapping confidence: review before relying on the merge">map: ${esc(mc)}</span>`);
  if(state.facets.cols.sd[row]) tags.push(`<span class="tag" title="Derived by splitting a compound entity string">split-derived</span>`);

  const score = opts.score!=null ? `<span class="pill grey" title="cosine similarity">${opts.score.toFixed(3)}</span> ` : '';
  const quote = d.quote ? `<div class="quote">“${esc(d.quote)}”${d.sec?` <span class="pill grey">${esc(d.sec)}</span>`:''}</div>` : '';
  const quant = d.quant ? `<div class="srcline"><b>Quantitative:</b> ${esc(d.quant)}${d.eff?` · effect: ${esc(d.eff)}`:''}</div>` : '';
  const npart = d.npart ? `<div class="srcline"><b>n</b> = ${esc(d.npart)}${d.comp?` · vs ${esc(d.comp)}`:''}</div>` : '';
  const mergedNote = (orig && orig!==ent)
    ? `<div class="merged">Reported as <code>${esc(orig)}</code>, folded into canonical <code>${esc(ent)}</code></div>` : '';
  return `<div class="card d-${dc}">
    <p class="ftext">${score}${esc(t)}</p>
    <div class="tags">${tags.join('')}</div>
    ${mergedNote}${quant}${npart}${quote}
    ${citeLine(state.facets.cols.p[row])}
  </div>`;
}

export function selectOpts(values, sel, anyLabel='Any', labeler=v=>v){
  return `<option value="">${anyLabel}</option>` + values.filter(v=>v && v!=='\u2014')
    .map(v=>`<option value="${esc(v)}"${v===sel?' selected':''}>${esc(labeler(v))}</option>`).join('');
}

/** sortable table helper */
export function sortTable(rows, key, dir){
  const r=[...rows];
  r.sort((a,b)=>{
    let x=a[key], y=b[key];
    if(x==null)x=-Infinity; if(y==null)y=-Infinity;
    if(typeof x==='string'||typeof y==='string') return dir*String(x).localeCompare(String(y));
    return dir*(x-y);
  });
  return r;
}

export function autocomplete(input, items, onPick){
  const box = document.createElement('div'); box.className='acbox hidden';
  input.parentNode.appendChild(box);
  let sel=-1, cur=[];
  const close=()=>{ box.classList.add('hidden'); sel=-1; };
  input.addEventListener('input', ()=>{
    const q=input.value.toLowerCase().trim();
    if(q.length<2) return close();
    cur = items.filter(s=>s.toLowerCase().includes(q)).slice(0,12);
    if(!cur.length) return close();
    box.innerHTML = cur.map((s,i)=>`<div data-i="${i}">${esc(s)}</div>`).join('');
    box.classList.remove('hidden');
  });
  box.addEventListener('mousedown', e=>{
    const d=e.target.closest('div[data-i]'); if(!d) return;
    e.preventDefault(); input.value=cur[+d.dataset.i]; close(); onPick&&onPick(input.value);
  });
  input.addEventListener('keydown', e=>{
    if(box.classList.contains('hidden')) return;
    const ds=[...box.querySelectorAll('div')];
    if(e.key==='ArrowDown'||e.key==='ArrowUp'){
      e.preventDefault(); sel=(sel+(e.key==='ArrowDown'?1:-1)+ds.length)%ds.length;
      ds.forEach((d,i)=>d.classList.toggle('sel',i===sel));
    } else if(e.key==='Enter' && sel>=0){ e.preventDefault(); input.value=cur[sel]; close(); onPick&&onPick(input.value); }
    else if(e.key==='Escape') close();
  });
  input.addEventListener('blur', ()=>setTimeout(close,150));
}

export function qs(name){ return new URLSearchParams(location.search).get(name); }
