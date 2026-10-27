/* data.js: shared loader/state for the combined findings browser.
   No framework, no build step. Everything is fetched from ./data/ as static files. */
export const DATA = './data/';
const _cache = {};

export async function getJSON(path){
  if(_cache[path]) return _cache[path];
  _cache[path] = (async ()=>{
    const r = await fetch(DATA + path);
    if(!r.ok) throw new Error(`fetch ${path} -> HTTP ${r.status}`);
    return r.json();
  })();
  return _cache[path];
}

export const state = { facets:null, meta:null, papers:null, entities:null, text:{}, detail:{},
  flags:{}, flagLabels:{}, excludePaper:null, includeFlagged:false };

export async function loadMeta(){ state.meta = state.meta || await getJSON('meta.json'); return state.meta; }

/** Facet layer: dictionary-encoded columns for every finding. Filters and charts need only this. */
export async function loadFacets(){
  if(state.facets) return state.facets;
  const f = await getJSON('findings_facets.json');
  f.inv = {};                                  // value -> code, for fast filtering
  for(const k in f.dicts){
    f.inv[k] = new Map(f.dicts[k].map((v,i)=>[v,i]));
  }
  state.facets = f;
  return f;
}

export async function loadPapers(){
  if(state.papers) return state.papers;
  const p = await getJSON('papers.json');
  const idx = {}; p.fields.forEach((n,i)=> idx[n]=i);
  state.papers = { rows:p.rows, idx, get:(i)=>p.rows[i] };
  // pmid -> row position, so views holding a bare pmid (discovery tables, deep links) can resolve a citation
  state.pmidIndex = new Map();
  const pi = idx.pmid;
  p.rows.forEach((r,i)=> state.pmidIndex.set(String(r[pi]), i));
  await loadFlags();
  return state.papers;
}

/* ---- paper flags (retractions, correction notices, preprints, linked records) ----
   paper_flags.json: {flags:{pmid:[{f,l,lp,li,lt,n,u}]}, labels:{flag:label}}. u = recommended use:
   'exclude' papers are left out of default counts, charts and searches (applyFilters) unless
   state.includeFlagged (or opts.includeFlagged) is set. A missing file must never break a page. */
export const EXCLUDE_TOGGLE_LABEL = 'Include retracted papers and correction notices';
export async function loadFlags(){
  try{
    const d = await getJSON('paper_flags.json');
    state.flags = d.flags || {}; state.flagLabels = d.labels || {};
  }catch(e){ state.flags = {}; state.flagLabels = {}; }
  if(state.papers){
    const ex = new Uint8Array(state.papers.rows.length);
    for(const pm in state.flags){
      if(!state.flags[pm].some(x=>x.u==='exclude')) continue;
      const i = state.pmidIndex.get(String(pm)); if(i!=null) ex[i] = 1;
    }
    state.excludePaper = ex;
  }
  return state.flags;
}
export function flagsOf(pmid){ return (pmid!=null && state.flags[String(pmid)]) || []; }
export function isExcludedPmid(pmid){ return flagsOf(pmid).some(x=>x.u==='exclude'); }
/** pmids carrying any of the given flag names, in papers.json order */
export function pmidsWithFlag(names){
  const want = new Set(names), out = [];
  for(const pm in state.flags) if(state.flags[pm].some(x=>want.has(x.f))) out.push(pm);
  return out.sort((a,b)=>(state.pmidIndex?.get(a)??0)-(state.pmidIndex?.get(b)??0));
}
/** number of finding rows left out by the default exclusion within a row set filtered with includeFlagged */
export function excludedIn(rows){
  const ex = state.excludePaper, p = state.facets.cols.p; if(!ex) return 0;
  let n=0; for(const r of rows) if(ex[p[r]]) n++; return n;
}
/** Look up a full paper record by pmid string. Returns null when the pmid is not in the canonical index. */
export function paperByPmid(pmid){
  if(pmid==null || !state.pmidIndex) return null;
  const i = state.pmidIndex.get(String(pmid));
  return i==null ? null : paper(i);
}
export function paper(i){
  const P = state.papers; if(!P || i==null) return null;
  const r = P.rows[i]; if(!r) return null;
  const o = {}; for(const k in P.idx) o[k] = r[P.idx[k]];
  return o;
}

export async function loadEntities(){
  if(state.entities) return state.entities;
  const e = await getJSON('entities.json');
  state.entities = e.entities;
  state.entityByName = new Map(e.entities.map(x=>[x.name,x]));
  return state.entities;
}

/* ---- lazy per-shard text and detail ---- */
export function shardOf(row){ return Math.floor(row / state.facets.shard_rows); }
export async function loadTextShard(s){
  if(state.text[s]) return state.text[s];
  const d = await getJSON(`text_${String(s).padStart(2,'0')}.json`);
  state.text[s] = d; return d;
}
export async function loadDetailShard(s){
  if(state.detail[s]) return state.detail[s];
  const d = await getJSON(`detail_${String(s).padStart(2,'0')}.json`);
  state.detail[s] = d; return d;
}
/** Ensure text+detail are present for a set of row ids (used before rendering a page of cards). */
export async function ensureRows(rows, withDetail=true){
  const sh = new Set(rows.map(shardOf));
  const jobs = [];
  for(const s of sh){ jobs.push(loadTextShard(s)); if(withDetail) jobs.push(loadDetailShard(s)); }
  await Promise.all(jobs);
}
export function textOf(row){
  const s = shardOf(row), d = state.text[s];
  return d ? d.t[row - d.start] : null;
}
export function detailOf(row){
  const s = shardOf(row), d = state.detail[s];
  if(!d) return {};
  const i = row - d.start, o = {};
  for(const k in d) if(k!=='start' && k!=='end') o[k] = d[k][i];
  return o;
}
/** Load ALL text shards: needed for keyword search over finding_text. */
export async function loadAllText(onProgress){
  const n = state.facets.n_shards; let done=0;
  await Promise.all(Array.from({length:n},(_,s)=>loadTextShard(s).then(()=>{ done++; onProgress&&onProgress(done,n); })));
}

/* ---- facet accessors ---- */
/** Read a facet value. Returns null for absent values: dictionary-encoded columns store missing
    data as the placeholder "\u2014" (or "" for the entity-string column), and both must read as null so
    callers can use a plain truthiness test without rendering a phantom missing-value entity chip. */
export function val(field, row){
  const f = state.facets, c = f.cols[field];
  if(!c) return null;
  const d = f.dicts[field];
  const v = d ? d[c[row]] : c[row];
  if(v==='\u2014' || v==='') return null;
  return v;
}
export function code(field, v){ return state.facets.inv[field]?.get(v); }
export function origEntity(row){ return state.facets.orig_entity[String(row)] || null; }

/* Legacy Tier 1 condition grouping. New combined views should use the ti and sl facets to
   distinguish extraction tier and source literature instead of inferring scope from condition. */
export const TIER1_CONDITIONS = new Set(['POTS','dysautonomia','orthostatic_hypotension','general',
  'multiple','long_COVID','small_fiber_neuropathy']);
export const inTier1Scope = c => TIER1_CONDITIONS.has(c);

export const DIRCLASS = v =>
  v==='elevated' ? 'up' :
  v==='depleted/reduced' ? 'down' :
  v==='no significant difference' ? 'null' :
  (v||'').startsWith('dysregulated') ? 'dys' : '';

export function esc(s){
  return String(s==null?'':s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
export function fmt(n){ return (n==null||isNaN(n)) ? 'N/A' : Number(n).toLocaleString('en-US'); }

/* ---- filtering over the facet layer ---- */
export const FILTER_FIELDS = ['sl','c','d','tr','ce','ft','ek','mc','e','st','ca','ps','ag','cv','th'];

export function applyFilters(f, opts){
  const F = state.facets, n = F.n, out = [];
  const codes = {};
  for(const k of FILTER_FIELDS){
    if(opts[k]!=null && opts[k]!==''){
      const c = code(k, opts[k]);
      if(c===undefined) return [];       // value not in dictionary -> no rows
      codes[k]=c;
    }
  }
  const y0 = opts.y0? +opts.y0 : null, y1 = opts.y1? +opts.y1 : null;
  const yr = F.cols.y, q = F.cols.q, sd = F.cols.sd, nc = F.cols.nc, pc = F.cols.p;
  const excludePaper = (opts.includeFlagged || state.includeFlagged) ? null : state.excludePaper;
  const nullCode = F.inv.nc.get('null-no-effect'), failCode = F.inv.nc.get('failed-to-replicate'),
        abanCode = F.inv.nc.get('tried-and-abandoned');
  for(let i=0;i<n;i++){
    let ok = true;
    for(const k in codes){ if(F.cols[k][i]!==codes[k]){ ok=false; break; } }
    if(!ok) continue;
    if(excludePaper && excludePaper[pc[i]]) continue;   // retracted papers and correction notices, unless included
    if(y0 && (yr[i]<y0 || yr[i]===0)) continue;
    if(y1 && (yr[i]>y1 || yr[i]===0)) continue;
    if(opts.hasQuant && !q[i]) continue;
    if(opts.excludeSplit && sd[i]) continue;
    if(opts.nullOnly){
      const v = nc[i];
      if(v!==nullCode && v!==failCode && v!==abanCode) continue;
    }
    out.push(i);
  }
  return out;
}

/** distinct papers (PubMed records) among a row set (the project counting rule) */
export function paperCount(rows){
  const F = state.facets, s = new Set();
  for(const r of rows) s.add(F.cols.p[r]);
  return s.size;
}
