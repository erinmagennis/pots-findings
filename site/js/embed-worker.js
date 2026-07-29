/* embed-worker.js — runs all-MiniLM-L6-v2 in a Web Worker via transformers.js.
   The findings were embedded with sentence-transformers/all-MiniLM-L6-v2; Xenova/all-MiniLM-L6-v2
   is the ONNX export of that same checkpoint, so query and document vectors share one space and
   cosine ranking is exact (not an approximation).
   Kept in a worker so the ~23MB model download and each encode never block the UI thread. */

let extractor = null, loading = null;

const CDN = 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.2.0';

async function init(){
  if(extractor) return extractor;
  if(loading) return loading;
  loading = (async ()=>{
    const { pipeline, env } = await import(CDN);
    env.useBrowserCache = true;     // model persists in IndexedDB/CacheStorage after first load
    env.allowLocalModels = false;
    extractor = await pipeline('feature-extraction','Xenova/all-MiniLM-L6-v2',{
      progress_callback: p => {
        if(p && p.status==='progress' && p.file && /onnx|\.bin$/.test(p.file)){
          self.postMessage({type:'progress', file:p.file, pct: p.progress||0, loaded:p.loaded, total:p.total});
        } else if(p && p.status){
          self.postMessage({type:'progress', file:p.file||'', status:p.status});
        }
      }
    });
    return extractor;
  })();
  try { return await loading; }
  catch(e){ loading = null; throw e; }
}

self.onmessage = async (ev)=>{
  const { type, id, text } = ev.data || {};
  try{
    if(type==='init'){
      await init();
      self.postMessage({type:'ready'});
    } else if(type==='embed'){
      const ex = await init();
      // pooling:'mean' + normalize:true reproduces the sentence-transformers default pipeline
      const out = await ex(text, { pooling:'mean', normalize:true });
      self.postMessage({type:'vec', id, vec: Array.from(out.data)});
    }
  }catch(e){
    self.postMessage({type:'error', id, message: String(e && e.message || e)});
  }
};
