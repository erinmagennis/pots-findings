/* search.js: two independent search modes.
   KEYWORD: instant, zero dependency, works before/without the model. Default mode.
   SEMANTIC: real query embedding from the same MiniLM checkpoint used for the findings,
             cosine-ranked against the dequantized int8 shards. Degrades cleanly if the
             model or CDN is unavailable: keyword search never depends on it. */
import { DATA, getJSON, state, loadAllText, textOf, val } from './data.js';

/* ============ embedding shards ============ */
let EMB = null, embLoading = null;

export async function loadEmbeddings(onProgress){
  if(EMB) return EMB;
  if(embLoading) return embLoading;
  embLoading = (async ()=>{
    const man = await getJSON('emb/manifest.json');
    const qp  = await getJSON('emb/quant_params.json');
    const dims = man.dims, n = man.total_rows;
    const qmin = Float32Array.from(qp.qmin), scale = Float32Array.from(qp.scale);
    const M = new Float32Array(n*dims);
    let done = 0;
    for(const sh of man.shards){
      const r = await fetch(`${DATA}emb/${sh.file}`);
      if(!r.ok) throw new Error(`embedding shard ${sh.file} -> HTTP ${r.status}`);
      const q = new Uint8Array(await r.arrayBuffer());
      if(q.length !== sh.rows*dims) throw new Error(`shard ${sh.file} size mismatch`);
      for(let i=0;i<sh.rows;i++){
        const o=(sh.start+i)*dims, oi=i*dims;
        let ss=0;
        for(let d=0;d<dims;d++){ const v=q[oi+d]*scale[d]+qmin[d]; M[o+d]=v; ss+=v*v; }
        const inv = 1/Math.sqrt(ss);                       // dequant -> L2-normalize
        for(let d=0;d<dims;d++) M[o+d]*=inv;
      }
      done++; onProgress && onProgress(done, man.shards.length);
    }
    EMB = { M, dims, n };
    return EMB;
  })();
  try { return await embLoading; } catch(e){ embLoading=null; throw e; }
}
export function embeddingsReady(){ return !!EMB; }

/* ============ model worker bridge ============ */
let worker=null, modelState='idle', waiting=new Map(), seq=0, listeners=[];
export function modelStatus(){ return modelState; }
export function onModelStatus(fn){ listeners.push(fn); }
function setStatus(s, extra){ modelState=s; listeners.forEach(f=>f(s,extra)); }

export function initModel(){
  if(worker) return;
  try{
    worker = new Worker('./js/embed-worker.js', {type:'module'});
  }catch(e){
    setStatus('unavailable', 'This browser cannot start a module Web Worker.');
    return;
  }
  setStatus('loading');
  worker.onmessage = ev=>{
    const m = ev.data;
    if(m.type==='ready') setStatus('ready');
    else if(m.type==='progress') setStatus('loading', m);
    else if(m.type==='vec'){ const w=waiting.get(m.id); if(w){ waiting.delete(m.id); w.resolve(m.vec); } }
    else if(m.type==='error'){
      const w=waiting.get(m.id);
      if(w){ waiting.delete(m.id); w.reject(new Error(m.message)); }
      // a failed load is terminal for semantic mode, but must never break the page
      if(modelState!=='ready') setStatus('unavailable', m.message);
    }
  };
  worker.onerror = e=> setStatus('unavailable', e.message||'worker error');
  worker.postMessage({type:'init'});
}

export function embedQuery(text){
  return new Promise((resolve,reject)=>{
    if(!worker) return reject(new Error('model not initialized'));
    if(modelState==='unavailable') return reject(new Error('semantic search unavailable'));
    const id = ++seq;
    waiting.set(id,{resolve,reject});
    worker.postMessage({type:'embed', id, text});
    setTimeout(()=>{ if(waiting.has(id)){ waiting.delete(id); reject(new Error('embedding timed out')); } }, 120000);
  });
}

/** cosine rank a query vector over an allowed row set (already-filtered rows) */
export function rankByVector(qvec, allowed, topK=200){
  if(!EMB) throw new Error('embeddings not loaded');
  const {M,dims} = EMB;
  const q = Float32Array.from(qvec);
  let ss=0; for(let d=0;d<dims;d++) ss+=q[d]*q[d];
  if(ss>0){ const inv=1/Math.sqrt(ss); for(let d=0;d<dims;d++) q[d]*=inv; }
  const heap=[];
  const push=(row,s)=>{
    if(heap.length<topK){ heap.push([row,s]); if(heap.length===topK) heap.sort((a,b)=>a[1]-b[1]); }
    else if(s>heap[0][1]){ heap[0]=[row,s]; let i=0;              // sift down
      for(;;){ const l=2*i+1,r=l+1; let m=i;
        if(l<topK&&heap[l][1]<heap[m][1])m=l; if(r<topK&&heap[r][1]<heap[m][1])m=r;
        if(m===i)break; const t=heap[i];heap[i]=heap[m];heap[m]=t;i=m; } }
  };
  for(const row of allowed){
    const o=row*dims; let s=0;
    for(let d=0;d<dims;d++) s+=M[o+d]*q[d];
    push(row,s);
  }
  return heap.sort((a,b)=>b[1]-a[1]);
}

/* ============ keyword search ============ */
let textReady=false;
export async function prepareKeyword(onProgress){
  if(textReady) return;
  await loadAllText(onProgress);
  textReady=true;
}
export function keywordReady(){ return textReady; }

function tokens(qs){ return qs.toLowerCase().split(/[^a-z0-9%+./-]+/).filter(t=>t.length>1); }

/** substring/token match over finding_text + canonical entity + ORIGINAL entity string + condition.
    Including the original string matters: rows whose entity is grouped under a different display name
    must stay findable by the string the paper used. */
export function keywordSearch(query, allowed, topK=200){
  const ql = query.toLowerCase().trim();
  if(!ql) return [];
  const toks = tokens(ql), phrase = ql.length>2;
  const out=[];
  for(const row of allowed){
    const t = (textOf(row)||'').toLowerCase();
    const e = (val('e',row)||'').toLowerCase();
    const es = (val('es_str',row)||'').toLowerCase();
    const c = (val('c',row)||'').toLowerCase();
    const hay = t+' \u0001'+e+' \u0001'+es+' \u0001'+c;
    let score=0;
    if(phrase && hay.includes(ql)) score += 10 + (t.includes(ql)?4:0) + (e===ql?8:0);
    let hit=0;
    for(const tk of toks){
      if(hay.includes(tk)){ hit++; score += 1;
        if(e.includes(tk)) score+=1.5; else if(es.includes(tk)) score+=1.2;
        if(t.startsWith(tk)) score+=.5; }
    }
    if(!score) continue;
    if(hit<toks.length && !(phrase && hay.includes(ql))) score *= hit/toks.length;   // partial-match penalty
    out.push([row,score]);
  }
  out.sort((a,b)=> b[1]-a[1] || a[0]-b[0]);
  return out.slice(0,topK);
}
