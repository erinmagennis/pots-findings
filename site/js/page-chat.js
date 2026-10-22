/* page-chat.js: retrieval-augmented Q&A with a key the VISITOR pastes.
   The key is kept in localStorage on this device only and is sent to the model provider's own
   endpoint and nowhere else. There is no server in this app to send it to. */
import { loadMeta, loadFacets, loadPapers, loadEntities, state, applyFilters, ensureRows,
         textOf, detailOf, paper, val, fmt, esc } from './data.js';
import { mount, citeLine } from './ui.js';
import { initModel, modelStatus, onModelStatus, embedQuery, loadEmbeddings, embeddingsReady,
         rankByVector, prepareKeyword, keywordReady, keywordSearch } from './search.js';

await loadMeta(); await loadFacets(); await loadPapers(); await loadEntities();
mount('chat');

const LS_KEY='pots_browser_api_key', LS_PROV='pots_browser_provider';
const PROVIDERS={
  anthropic:{ label:'Anthropic (Claude)', url:'https://api.anthropic.com/v1/messages',
    keyHint:'sk-ant-…', model:'claude-sonnet-5',
    build:(sys,msgs,model)=>({
      headers:{'content-type':'application/json','x-api-key':getKey(),
               'anthropic-version':'2023-06-01','anthropic-dangerous-direct-browser-access':'true'},
      body:{model, max_tokens:1200, system:sys,
            messages:msgs.map(m=>({role:m.role,content:m.content}))} }),
    parse:j=> (j.content||[]).filter(c=>c.type==='text').map(c=>c.text).join('') },
  openai:{ label:'OpenAI', url:'https://api.openai.com/v1/chat/completions',
    keyHint:'sk-…', model:'gpt-4o-mini',
    build:(sys,msgs,model)=>({
      headers:{'content-type':'application/json','authorization':'Bearer '+getKey()},
      body:{model, max_tokens:1200, messages:[{role:'system',content:sys},...msgs]} }),
    parse:j=> j.choices?.[0]?.message?.content || '' }
};
const getKey=()=>localStorage.getItem(LS_KEY)||'';
const getProv=()=>localStorage.getItem(LS_PROV)||'anthropic';

/* ---------- key panel ---------- */
function renderKeyPanel(){
  const has=!!getKey(), prov=getProv();
  document.getElementById('keypanel').innerHTML = has
   ? `<div class="keyrow">
        <span class="pill">key stored on this device</span>
        <span class="kv">provider: <b>${esc(PROVIDERS[prov].label)}</b> · model:
          <input id="model" value="${esc(PROVIDERS[prov].model)}" style="width:230px"></span>
        <button id="clearkey">Clear key</button>
      </div>
      <div class="note plain">Your key is in this browser's <code>localStorage</code> only. It is sent
        directly to ${esc(new URL(PROVIDERS[prov].url).host)} and to no one else: this site has no backend.
        Clearing it removes it from this device.</div>`
   : `<h3>No API key set: everything except this chat panel already works</h3>
      <p class="lede">Search, filters, entity and paper pages, all five discovery tables, the preset charts and
        the chart builder need <b>no key at all</b>. A key is only needed to have a language model summarise
        retrieved findings in prose.</p>
      <p class="kv"><b>What is an API key?</b> A credential from an AI provider that lets software call their
        model and bills your account for the usage. You create one in the provider's console. Typical cost for
        a question here is well under a cent, but it is <b>your</b> account being charged.</p>
      <div class="keyrow">
        <select id="prov">${Object.entries(PROVIDERS).map(([k,v])=>
          `<option value="${k}"${k===prov?' selected':''}>${esc(v.label)}</option>`).join('')}</select>
        <input type="password" id="key" placeholder="${esc(PROVIDERS[prov].keyHint)}" autocomplete="off">
        <button class="primary" id="savekey">Save key on this device</button>
      </div>
      <div class="note"><b>Where your key goes.</b> It is stored only in this browser's
        <code>localStorage</code> and sent only to the provider's own API endpoint over HTTPS. It is never
        transmitted to this site's host, never logged, and no key is bundled in this app. Use a key with a
        spending limit, and clear it when you're done on a shared computer.</div>`;
  const sk=document.getElementById('savekey');
  if(sk) sk.onclick=()=>{
    const k=document.getElementById('key').value.trim();
    if(!k) return;
    localStorage.setItem(LS_KEY,k); localStorage.setItem(LS_PROV,document.getElementById('prov').value);
    renderKeyPanel();
  };
  const ck=document.getElementById('clearkey');
  if(ck) ck.onclick=()=>{ localStorage.removeItem(LS_KEY); renderKeyPanel(); };
  const pv=document.getElementById('prov');
  if(pv) pv.onchange=()=>{ localStorage.setItem(LS_PROV,pv.value); renderKeyPanel(); };
}
renderKeyPanel();

/* ---------- retrieval ---------- */
const rstate=document.getElementById('rstate');
onModelStatus(s=>{
  if(document.getElementById('rmode').value!=='semantic') return;
  rstate.innerHTML = s==='ready'? '<span class="pill">semantic retrieval ready</span>'
    : s==='loading'? '<span class="spinner"></span> loading search model…'
    : s==='unavailable'? '<span class="pill err">semantic unavailable: using keyword</span>' : '';
});
document.getElementById('rmode').onchange=e=>{
  if(e.target.value==='semantic'){ initModel(); loadEmbeddings().catch(()=>{}); }
  else rstate.textContent='';
};

async function retrieve(q, n){
  const allowed=applyFilters(state.facets,{});
  let scored=[];
  const mode=document.getElementById('rmode').value;
  if(mode==='semantic' && modelStatus()!=='unavailable'){
    try{
      if(!embeddingsReady()) await loadEmbeddings();
      const v=await embedQuery(q);
      scored=rankByVector(v,allowed,n);
    }catch(e){ rstate.innerHTML='<span class="pill err">semantic failed: used keyword</span>'; }
  }
  if(!scored.length){
    if(!keywordReady()) await prepareKeyword();
    scored=keywordSearch(q,allowed,n);
  }
  const rows=scored.slice(0,n).map(s=>s[0]);
  await ensureRows(rows);
  return rows;
}

/* ---------- prompt ---------- */
function contextBlock(rows){
  return rows.map((r,i)=>{
    const d=detailOf(r), p=paper(state.facets.cols.p[r]);
    const etal=p&&p.author_count>1?' et al.':'';
    return `[F${i+1}] ${textOf(r)}
  entity: ${val('e',r)||val('es_str',r)||'N/A'}${val('e',r)?'':' (not canonicalized)'} | direction: ${val('d',r)||'N/A'} | condition: ${val('c',r)||'N/A'}
  evidence_tier: ${val('tr',r)||'N/A'} | certainty: ${val('ce',r)||'N/A'} | finding_type: ${val('ft',r)||'N/A'}${d.npart?` | n=${d.npart}`:''}
  ${d.quant?`quantitative: ${d.quant}\n  `:''}source: ${p?`${p.first_author||'?'}${etal}, ${p.journal||'?'} (${p.year||'?'}), pmid ${p.pmid}`:'unknown'}
  link: ${p?(p.doi_url||p.pubmed_url||''):''}`;
  }).join('\n\n');
}
const SYSTEM=`You answer questions about a database of machine-extracted findings from POTS, dysautonomia, and related-condition research papers.

HARD RULES:
1. Answer ONLY from the numbered findings provided in the user's message. If they do not contain the answer, say so plainly and suggest a different search. Never add facts from your own knowledge, and never fill gaps with plausible-sounding detail.
2. Cite every claim with the finding tags you used, like [F3] or [F1][F7]. A sentence with no tag is not allowed.
3. You are NOT giving medical advice. Do not recommend, dose, or rank treatments, and do not tell the user what to do about their health. Describe only what the papers reported. If the question asks what someone should take or do, say that this is a research-literature tool and refer them to a qualified clinician.
4. Respect the evidence. State the evidence tier and certainty where they matter, and prefer "one cohort study reported X" over "X is true". Flag when findings disagree, when a result is a null result, or when support is a single case report.
5. Scope: the database holds ${fmt(state.meta.counts.findings)} machine-extracted findings from ${fmt(state.meta.counts.papers)} papers (${state.meta.counts.year_min}–${state.meta.counts.year_max}) on POTS, dysautonomia and related conditions. It is not the whole literature, and the findings have not yet been checked by a human reader against their papers. Never treat the absence of a finding as evidence that a relationship is absent, and say when the retrieved findings are thin.
6. Distinguish a finding's condition label from its source literature when that distinction matters. Co-mention is not evidence of interaction, and shared biology is not the same claim as patient comorbidity.
7. Quote at most a dozen words verbatim from any finding. Summarize in your own words otherwise.
8. Be concise and concrete. No preamble about being an AI.`;

/* ---------- chat ---------- */
const log=document.getElementById('chatlog');
let history=[];
function greet(){
  log.innerHTML=`<div class="msg"><div class="who">about this panel</div><div class="body">Ask about what these
${fmt(state.meta.counts.findings)} findings report. Your question is used to retrieve the most relevant findings
locally, and only those findings: plus your question: are sent to the model. Answers cite the findings used
so you can open the source papers yourself.

This is research information, not medical advice.</div></div>`;
}
greet();

function add(role, body, used){
  const div=document.createElement('div');
  div.className='msg '+(role==='user'?'u':'');
  div.innerHTML=`<div class="who">${role==='user'?'you':'answer'}</div><div class="body">${esc(body)}</div>
    ${used?`<div class="used"><b>Findings used (open the papers: these are automated extractions):</b>
      <ol>${used.map((r,i)=>{
        const d=detailOf(r);
        return `<li><b>[F${i+1}]</b> ${esc(textOf(r))}
          ${d.quote?`<div class="quote" style="margin:4px 0">“${esc(d.quote)}”</div>`:''}
          ${citeLine(state.facets.cols.p[r])}</li>`;}).join('')}</ol></div>`:''}`;
  log.appendChild(div); log.scrollTop=log.scrollHeight;
  return div;
}

async function send(){
  const q=document.getElementById('msg').value.trim();
  if(!q) return;
  if(!getKey()){ add('assistant','No API key is set. Add one above, or use Search / Charts / Discover: those need no key.'); return; }
  document.getElementById('msg').value='';
  add('user',q);
  const pending=add('assistant','retrieving findings…');
  const n=+document.getElementById('ctxn').value||12;
  let rows=[];
  try{
    rows=await retrieve(q,n);
    if(!rows.length){
      pending.querySelector('.body').textContent='No findings matched that question. Try different wording, or browse the discovery tables.';
      return;
    }
    pending.querySelector('.body').innerHTML='<span class="spinner"></span> asking the model…';
    const prov=PROVIDERS[getProv()];
    const model=(document.getElementById('model')?.value||prov.model).trim();
    const userMsg=`Question: ${q}\n\nFindings retrieved from the database:\n\n${contextBlock(rows)}`;
    const msgs=[...history,{role:'user',content:userMsg}];
    const {headers,body}=prov.build(SYSTEM,msgs,model);
    const res=await fetch(prov.url,{method:'POST',headers,body:JSON.stringify(body)});
    if(!res.ok){
      let detail='';
      try{ const j=await res.json(); detail=j.error?.message||JSON.stringify(j).slice(0,300); }
      catch{ detail=await res.text().catch(()=>''); }
      throw new Error(`${res.status} ${res.statusText}: ${detail}`);
    }
    const j=await res.json();
    const text=prov.parse(j)||'(empty response)';
    pending.remove();
    add('assistant',text,rows);
    history.push({role:'user',content:userMsg},{role:'assistant',content:text});
    if(history.length>6) history=history.slice(-6);
  }catch(e){
    const msg=String(e.message||e);
    const hint = /Failed to fetch|NetworkError|CORS/i.test(msg)
      ? ` This is usually a browser/CORS or network problem, or a key the provider rejected before responding. Your key never leaves this device except to the provider: check it is valid and that the provider allows direct browser calls.`
      : /401|403/.test(msg) ? ' The provider rejected the key. Check it, or clear and re-enter it.'
      : /429/.test(msg) ? ' Rate-limited or out of quota on your account.' : '';
    pending.querySelector('.body').innerHTML=
      `<span class="pill err">request failed</span> ${esc(msg)}${hint}
       <br><br>Search, browse and charts are unaffected and still work without a key.`;
  }
}
document.getElementById('send').onclick=send;
document.getElementById('msg').addEventListener('keydown',e=>{ if(e.key==='Enter') send(); });
document.getElementById('reset').onclick=()=>{ history=[]; greet(); };
