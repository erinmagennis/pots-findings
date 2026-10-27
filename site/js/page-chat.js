/* page-chat.js: questions answered by a language model from retrieved findings, using a key the VISITOR
   pastes. The key and saved chats stay in this browser's localStorage. The key is sent only to the chosen
   provider's own API. There is no server in this app to send anything to. */
import { loadMeta, loadFacets, loadPapers, loadEntities, state, applyFilters, ensureRows,
         textOf, detailOf, paper, val, fmt, esc } from './data.js';
import { mount, citeLine } from './ui.js';
import { initModel, modelStatus, onModelStatus, embedQuery, loadEmbeddings, embeddingsReady,
         rankByVector, prepareKeyword, keywordReady, keywordSearch } from './search.js';
import { trackAsk } from './analytics.js';

await loadMeta(); await loadFacets(); await loadPapers(); await loadEntities();
mount('chat');

/* ---------- providers ----------
   Every provider here accepts calls straight from a browser (checked 2026-10-26). All but Anthropic use the
   OpenAI chat format. `model` is only a fallback for when the provider's model list cannot be read. */
const PROVIDERS={
  anthropic:{ label:'Anthropic (Claude)', base:'https://api.anthropic.com/v1', kind:'anthropic', hint:'sk-ant-…',
    model:'claude-sonnet-5-5', prefer:[/sonnet/], keys:'https://console.anthropic.com/settings/keys' },
  openai:{ label:'OpenAI (ChatGPT)', base:'https://api.openai.com/v1', hint:'sk-…', model:'gpt-5.4-mini',
    prefer:[/^gpt-5[.\d]*-mini$/,/mini/], keys:'https://platform.openai.com/api-keys' },
  gemini:{ label:'Google Gemini', base:'https://generativelanguage.googleapis.com/v1beta/openai', hint:'AIza…',
    prefer:[/flash(?!.*(lite|image|tts|live))/], keys:'https://aistudio.google.com/apikey',
    note:'Has a free tier. Google may use free-tier questions to improve its models.' },
  openrouter:{ label:'OpenRouter (many models, one key)', base:'https://openrouter.ai/api/v1', hint:'sk-or-…',
    prefer:[/^anthropic\/claude-sonnet/,/sonnet/], keys:'https://openrouter.ai/keys',
    note:'One key reaches models from many companies, including some free ones.' },
  perplexity:{ label:'Perplexity', base:'https://api.perplexity.ai', hint:'pplx-…', model:'sonar',
    keys:'https://www.perplexity.ai/account/api/keys' },
  mistral:{ label:'Mistral', base:'https://api.mistral.ai/v1', prefer:[/mistral-medium-latest/,/small-latest/],
    keys:'https://console.mistral.ai/api-keys' },
  groq:{ label:'Groq', base:'https://api.groq.com/openai/v1', hint:'gsk_…', keys:'https://console.groq.com/keys',
    note:'Has a free tier.' },
  deepseek:{ label:'DeepSeek', base:'https://api.deepseek.com', hint:'sk-…', model:'deepseek-chat',
    prefer:[/deepseek-chat/], keys:'https://platform.deepseek.com/api_keys' },
  xai:{ label:'xAI (Grok)', base:'https://api.x.ai/v1', hint:'xai-…', keys:'https://console.x.ai' },
  together:{ label:'Together AI', base:'https://api.together.xyz/v1', keys:'https://api.together.ai/settings/api-keys' },
  fireworks:{ label:'Fireworks', base:'https://api.fireworks.ai/inference/v1', hint:'fw_…',
    keys:'https://app.fireworks.ai/settings/users/api-keys' },
  cerebras:{ label:'Cerebras', base:'https://api.cerebras.ai/v1', hint:'csk-…', keys:'https://cloud.cerebras.ai',
    note:'Has a free tier.' },
  huggingface:{ label:'Hugging Face', base:'https://router.huggingface.co/v1', hint:'hf_…',
    keys:'https://huggingface.co/settings/tokens' },
  cohere:{ label:'Cohere', base:'https://api.cohere.ai/compatibility/v1', keys:'https://dashboard.cohere.com/api-keys' },
  deepinfra:{ label:'DeepInfra', base:'https://api.deepinfra.com/v1/openai', keys:'https://deepinfra.com/dash/api_keys' },
  moonshot:{ label:'Moonshot (Kimi)', base:'https://api.moonshot.ai/v1', hint:'sk-…',
    keys:'https://platform.moonshot.ai/console/api-keys' },
  qwen:{ label:'Alibaba Qwen', base:'https://dashscope-intl.aliyuncs.com/compatible-mode/v1', hint:'sk-…',
    keys:'https://modelstudio.console.alibabacloud.com' },
  ai21:{ label:'AI21 (Jamba)', base:'https://api.ai21.com/studio/v1', keys:'https://studio.ai21.com/account/api-key' },
  nebius:{ label:'Nebius AI Studio', base:'https://api.studio.nebius.com/v1', keys:'https://studio.nebius.com' },
  novita:{ label:'Novita AI', base:'https://api.novita.ai/v3/openai', keys:'https://novita.ai/settings/key-management' },
  hyperbolic:{ label:'Hyperbolic', base:'https://api.hyperbolic.xyz/v1', keys:'https://app.hyperbolic.xyz/settings' },
  custom:{ label:'Other, or a model on your computer', base:'', custom:true,
    note:'Any service that uses the OpenAI chat format, such as Ollama or LM Studio. Paste its address below.' }
};
const POPULAR=['anthropic','openai','gemini','openrouter','perplexity'];
// key prefixes that belong to exactly one provider; used only to correct an obvious mismatch, in this browser
const PREFIXES=[[/^sk-ant-/,'anthropic'],[/^sk-or-/,'openrouter'],[/^gsk_/,'groq'],[/^AIza/,'gemini'],[/^pplx-/,'perplexity'],
  [/^xai-/,'xai'],[/^fw_/,'fireworks'],[/^csk-/,'cerebras'],[/^hf_/,'huggingface'],[/^sk-(proj|svcacct)-/,'openai']];
const NOT_CHAT=/embed|tts|whisper|dall-e|image|audio|moderation|realtime|transcri|rerank|guard|computer-use|veo|imagen|davinci|babbage|aqa|learnlm|ocr/i;

const LS={ key:'pots_browser_api_key', prov:'pots_browser_provider', base:'pots_browser_base', model:p=>'pots_browser_model_'+p };
const ls={ get:k=>{ try{ return localStorage.getItem(k)||''; }catch{ return ''; } },
  set:(k,v)=>{ try{ localStorage.setItem(k,v); }catch{} }, del:k=>{ try{ localStorage.removeItem(k); }catch{} } };
const getKey=()=>ls.get(LS.key);
const getProv=()=>PROVIDERS[ls.get(LS.prov)]?ls.get(LS.prov):'anthropic';
const baseOf=id=>PROVIDERS[id].custom?ls.get(LS.base).replace(/\/+$/,''):PROVIDERS[id].base;
const ready=()=>!!getKey() || (getProv()==='custom' && !!ls.get(LS.base));
const hostOf=u=>{ try{ return new URL(u).host; }catch{ return 'that address'; } };

function headersFor(id, key){
  if(PROVIDERS[id].kind==='anthropic') return {'content-type':'application/json','x-api-key':key,
    'anthropic-version':'2023-06-01','anthropic-dangerous-direct-browser-access':'true'};
  return key ? {'content-type':'application/json','authorization':'Bearer '+key} : {'content-type':'application/json'};
}
function requestFor(id, sys, msgs, model){
  const P=PROVIDERS[id], key=getKey();
  if(P.kind==='anthropic') return { url:baseOf(id)+'/messages', headers:headersFor(id,key),
    body:{model, max_tokens:4096, system:sys, messages:msgs.map(m=>({role:m.role,content:m.content}))} };
  const body={model, messages:[{role:'system',content:sys},...msgs]};
  if(id==='openai') body.max_completion_tokens=4096; else body.max_tokens=4096;
  return { url:baseOf(id)+'/chat/completions', headers:headersFor(id,key), body };
}
const parseReply=(id,j)=> PROVIDERS[id].kind==='anthropic'
  ? (j.content||[]).filter(c=>c.type==='text').map(c=>c.text).join('')
  : (j.choices?.[0]?.message?.content || '');

// read the provider's own model list so people pick from real names; falls back to a text box
async function listModels(id){
  const url=baseOf(id)+'/models'+(PROVIDERS[id].kind==='anthropic'?'?limit=100':'');
  const res=await fetch(url,{headers:headersFor(id,getKey())});
  if(!res.ok) throw new Error(res.status);
  const j=await res.json();
  const ids=(j.data||j.models||[]).map(m=>m.id||m.name).filter(Boolean).map(String).filter(m=>!NOT_CHAT.test(m));
  return [...new Set(ids)];
}
function pickDefault(id, models){
  const saved=ls.get(LS.model(id));
  if(saved && models.includes(saved)) return saved;
  for(const re of PROVIDERS[id].prefer||[]){ const m=models.find(x=>re.test(x)); if(m) return m; }
  return models.includes(PROVIDERS[id].model) ? PROVIDERS[id].model : models[0];
}
const currentModel=()=>{ const el=document.getElementById('model'); return (el?.value||PROVIDERS[getProv()].model||'').trim(); };

/* ---------- steps 1 and 2 ---------- */
const provOptions=sel=>{
  const opt=id=>`<option value="${id}"${id===sel?' selected':''}>${esc(PROVIDERS[id].label)}</option>`;
  const more=Object.keys(PROVIDERS).filter(id=>!POPULAR.includes(id)&&id!=='custom')
    .sort((a,b)=>PROVIDERS[a].label.localeCompare(PROVIDERS[b].label));
  return `<optgroup label="Most used">${POPULAR.map(opt).join('')}</optgroup>
    <optgroup label="More providers">${more.map(opt).join('')}</optgroup>
    <optgroup label="Other">${opt('custom')}</optgroup>`;
};
function renderKeyPanel(note=''){
  const id=getProv(), P=PROVIDERS[id];
  if(ready()){
    document.getElementById('keypanel').innerHTML=`<div class="ask-ready"><span class="ok" aria-hidden="true">✓</span>
      <span>Using <b>${esc(P.label)}</b>${P.custom?` at ${esc(hostOf(baseOf(id)))}`:''}</span>
      <label class="ask-model">Model <span id="modelslot"><span class="spinner"></span></span></label>
      <button id="clearkey" class="linkish">${getKey()?'Remove key':'Change'}</button></div>`;
    document.getElementById('clearkey').onclick=()=>{ ls.del(LS.key); if(P.custom) ls.del(LS.base); renderKeyPanel(); };
    fillModels(id);
  } else {
    document.getElementById('keypanel').innerHTML=`<div class="ask-steps">
      <section class="ask-step" aria-labelledby="stepGet">
        <h2 id="stepGet"><span class="step-n">1</span>Choose your AI provider</h2>
        <select id="prov" aria-label="AI provider">${provOptions(id)}</select>
        <p class="ask-sub">${P.custom?esc(P.note):`${P.note?esc(P.note)+' ':''}Each question usually costs a few cents or less, billed to your account.`}</p>
      </section>
      <section class="ask-step" aria-labelledby="stepPaste">
        <h2 id="stepPaste"><span class="step-n">2</span>Paste your key</h2>
        ${P.custom?`<input type="url" id="base" class="ask-input" placeholder="http://localhost:11434/v1" value="${esc(ls.get(LS.base))}" aria-label="Service address">`:''}
        <div class="keyrow">
          <input type="password" id="key" placeholder="${esc(P.custom?'Key, if the service needs one':(P.hint||'Paste your key'))}" autocomplete="off" aria-label="API key">
          <button class="primary" id="savekey">Save</button>
        </div>
        ${note?`<p class="ask-sub ask-flag">${esc(note)}</p>`:''}
        ${P.custom?'':`<p class="ask-sub">No key yet? <a href="${P.keys}" target="_blank" rel="noopener">Make one on the ${esc(P.label.replace(/ \(.*\)$/,''))} site</a>. It takes a minute. Set a spending limit there so you stay in control of the cost.</p>`}
        <details class="ask-more"><summary>Where does my key go?</summary>
          <p>It is kept in this browser only and sent only to ${P.custom?'the address you enter':esc(hostOf(P.base))} when you
            ask a question. This site has no server, so it never sees your key or your questions. Remove the key when
            you finish on a shared computer.</p></details>
      </section></div>`;
    const pv=document.getElementById('prov'), kin=document.getElementById('key');
    pv.onchange=()=>{ ls.set(LS.prov,pv.value); trackAsk('provider_selected',{provider:pv.value}); renderKeyPanel(); };
    const save=()=>{
      const k=kin.value.trim(), b=document.getElementById('base')?.value.trim();
      if(P.custom){ if(!b){ document.getElementById('base').focus(); return; } ls.set(LS.base,b); }
      else if(!k){ kin.focus(); return; }
      // an unmistakable prefix from another provider: switch to it rather than send the key to the wrong place
      const owner=PREFIXES.find(([re])=>re.test(k))?.[1];
      if(owner && owner!==id && !P.custom){ ls.set(LS.prov,owner); renderKeyPanel(`That looks like a ${PROVIDERS[owner].label} key, so we switched to ${PROVIDERS[owner].label}. Click Save to use it.`); document.getElementById('key').value=k; return; }
      if(k) ls.set(LS.key,k);
      trackAsk('key_saved',{provider:id});
      renderKeyPanel(); document.getElementById('msg').focus();
    };
    document.getElementById('savekey').onclick=save;
    kin.addEventListener('keydown',e=>{ if(e.key==='Enter') save(); });
  }
  document.querySelector('.ask-chat').classList.toggle('waiting',!ready());
}
async function fillModels(id){
  const slot=document.getElementById('modelslot'); if(!slot) return;
  let models=[];
  try{ models=await listModels(id); }catch{}
  if(!document.getElementById('modelslot')) return;
  if(models.length){
    const pick=pickDefault(id,models);
    slot.innerHTML=`<select id="model">${models.map(m=>`<option${m===pick?' selected':''}>${esc(m)}</option>`).join('')}</select>`;
  } else {
    slot.innerHTML=`<input id="model" value="${esc(ls.get(LS.model(id))||PROVIDERS[id].model||'')}" placeholder="model name">`;
  }
  document.getElementById('model').onchange=e=>ls.set(LS.model(id),e.target.value.trim());
}

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

/* ---------- chat ----------
   Chats are saved in this browser only (localStorage), unless the visitor turns saving off. Saved: the
   questions, the answers and which findings were used. Never the key. */
const log=document.getElementById('chatlog');
const CHATS='pots_ask_chats', SAVE='pots_ask_save', MAX_CHATS=30;
const saving=()=>ls.get(SAVE)!=='0';
const loadChats=()=>{ try{ return JSON.parse(ls.get(CHATS)||'[]'); }catch{ return []; } };
const storeChats=list=>ls.set(CHATS,JSON.stringify(list.slice(0,MAX_CHATS)));
const newChat=()=>({id:Date.now().toString(36), at:new Date().toISOString(), title:'', turns:[], history:[]});
let cur=newChat();

const EXAMPLES=['What is reported about norepinephrine in POTS?','Which findings disagree about mast cells?',
  'What did studies find about small fiber neuropathy?'];
function greet(){
  log.innerHTML=`<div class="ask-empty"><p>Try one of these</p>${EXAMPLES.map(q=>
    `<button class="ask-eg" type="button">${esc(q)}</button>`).join('')}</div>`;
  log.querySelectorAll('.ask-eg').forEach(b=>b.onclick=()=>{
    document.getElementById('msg').value=b.textContent; if(ready()) send(); else document.getElementById('key')?.focus();
  });
}

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

function persist(){
  if(!saving() || !cur.turns.length) return;
  const list=loadChats().filter(c=>c.id!==cur.id);
  list.unshift(cur); storeChats(list); renderChats();
}
async function openChat(id){
  const c=loadChats().find(x=>x.id===id); if(!c) return;
  cur=c; log.innerHTML='';
  await ensureRows(c.turns.flatMap(t=>t.rows||[]));
  c.turns.forEach(t=>{ add('user',t.q); add('assistant',t.a,t.rows); });
  renderChats();
}
function renderChats(){
  const box=document.getElementById('chats'), list=loadChats();
  box.innerHTML=`<div class="ask-chats-head"><h2>Your chats</h2>
      <label class="ask-toggle"><input type="checkbox" id="saveChats"${saving()?' checked':''}> Save chats on this device</label></div>
    ${list.length?`<ul class="ask-chatlist">${list.map(c=>`<li class="${c.id===cur.id?'on':''}">
        <button class="linkish ask-open" data-id="${c.id}">${esc(c.title||'Untitled chat')}</button>
        <span class="kv">${new Date(c.at).toLocaleDateString()} · ${c.turns.length} question${c.turns.length===1?'':'s'}</span>
        <button class="linkish ask-del" data-id="${c.id}" aria-label="Delete this chat">Delete</button></li>`).join('')}</ul>
      <button class="linkish" id="delAll">Delete all chats</button>`
    :`<p class="kv">${saving()?'Your chats will appear here. They stay in this browser and are never sent to this site.':'Saving is off. Chats disappear when you leave the page.'}</p>`}`;
  box.querySelectorAll('.ask-open').forEach(b=>b.onclick=()=>openChat(b.dataset.id));
  box.querySelectorAll('.ask-del').forEach(b=>b.onclick=()=>{
    storeChats(loadChats().filter(c=>c.id!==b.dataset.id));
    if(cur.id===b.dataset.id){ cur=newChat(); greet(); }
    renderChats();
  });
  const da=document.getElementById('delAll');
  if(da) da.onclick=()=>{ ls.del(CHATS); cur=newChat(); greet(); renderChats(); };
  document.getElementById('saveChats').onchange=e=>{
    ls.set(SAVE,e.target.checked?'1':'0');
    if(e.target.checked) persist(); else ls.del(CHATS);
    renderChats();
  };
}

// plain-text copy of the open chat, with each finding's citation and link
function download(){
  if(!cur.turns.length) return;
  const cite=r=>{ const p=paper(state.facets.cols.p[r]); if(!p) return 'citation unavailable';
    return `${p.first_author||'Unknown'}${p.author_count>1?' et al.':''}, ${p.journal||'N/A'}${p.year?` (${p.year})`:''}. ${p.doi_url||p.pubmed_url||''}`.trim(); };
  const out=[`# ${cur.title||'Chat'}`, '', `From ${location.origin}/chat on ${new Date(cur.at).toLocaleString()}.`,
    'Research information, not medical advice. Answers come from automated extractions; check the cited papers.', ''];
  cur.turns.forEach((t,i)=>{
    out.push(`## Question ${i+1}`, '', t.q, '', '### Answer', '', t.a, '', '### Findings used', '');
    (t.rows||[]).forEach((r,j)=>out.push(`${j+1}. [F${j+1}] ${textOf(r)}`, `   ${cite(r)}`));
    out.push('');
  });
  const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([out.join('\n')],{type:'text/markdown'}));
  a.download=`pots-chat-${cur.at.slice(0,10)}.md`; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),1000);
}

async function send(){
  const q=document.getElementById('msg').value.trim();
  if(!q) return;
  if(!ready()){ document.getElementById('key')?.focus(); add('assistant','Add a key in step 2 first. Search, Signals and Analyze work without one.'); return; }
  document.getElementById('msg').value='';
  log.querySelector('.ask-empty')?.remove();
  add('user',q);
  const pending=add('assistant','retrieving findings…');
  const n=+document.getElementById('ctxn').value||12;
  const id=getProv();
  trackAsk('question_sent',{provider:id});
  let rows=[];
  try{
    rows=await retrieve(q,n);
    if(!rows.length){
      pending.querySelector('.body').textContent='No findings matched that question. Try different wording, or browse the discovery tables.';
      return;
    }
    pending.querySelector('.body').innerHTML='<span class="spinner"></span> asking the model…';
    const userMsg=`Question: ${q}\n\nFindings retrieved from the database:\n\n${contextBlock(rows)}`;
    const {url,headers,body}=requestFor(id,SYSTEM,[...cur.history,{role:'user',content:userMsg}],currentModel());
    const res=await fetch(url,{method:'POST',headers,body:JSON.stringify(body)});
    if(!res.ok){
      let detail='';
      try{ const j=await res.json(); detail=j.error?.message||JSON.stringify(j).slice(0,300); }
      catch{ detail=await res.text().catch(()=>''); }
      throw new Error(`${res.status} ${res.statusText}: ${detail}`);
    }
    const j=await res.json();
    const text=parseReply(id,j)||(j.stop_reason==='max_tokens'||j.choices?.[0]?.finish_reason==='length'
      ? '(the model used its whole output budget before answering; try a shorter question or fewer findings)' : '(empty response)');
    pending.remove();
    add('assistant',text,rows);
    cur.history.push({role:'user',content:userMsg},{role:'assistant',content:text});
    if(cur.history.length>6) cur.history=cur.history.slice(-6);
    if(!cur.title) cur.title=q.length>70?q.slice(0,67)+'…':q;
    cur.turns.push({q,a:text,rows});
    persist();
  }catch(e){
    const msg=String(e.message||e);
    const hint = /Failed to fetch|NetworkError|CORS/i.test(msg)
      ? ` This is usually a network problem, or a key the provider rejected before answering. Check the key, and for a service on your computer, check it allows requests from this site.`
      : /401|403/.test(msg) ? ' The provider rejected the key. Check it, or remove it and paste it again.'
      : /404/.test(msg) ? ' The provider did not recognise the model. Pick another model above.'
      : /429/.test(msg) ? ' Rate-limited or out of credit on your account.' : '';
    pending.querySelector('.body').innerHTML=
      `<span class="pill err">request failed</span> ${esc(msg)}${hint}
       <br><br>Search, Signals and Analyze still work without a key.`;
  }
}
document.getElementById('send').onclick=send;
document.getElementById('msg').addEventListener('keydown',e=>{ if(e.key==='Enter') send(); });
document.getElementById('newchat').onclick=()=>{ cur=newChat(); greet(); renderChats(); };
document.getElementById('download').onclick=download;
renderKeyPanel();
greet();
renderChats();
